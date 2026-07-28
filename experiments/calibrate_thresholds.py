import csv
import json
import sys
import time
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode, DecisionPolicy
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider,
    VendorEvidenceProvider,
    ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def load_data():
    purchases = []
    gsts = []
    ground_truth = {}
    
    with open("experiments/purchases.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            purchases.append(PurchaseRecord(
                record_id=row["record_id"],
                amount=Decimal(row["amount"]),
                record_date=datetime.strptime(row["record_date"], "%Y-%m-%d").date(),
                reference=row["reference"] if row["reference"] != "" else None,
                vendor_name=row["vendor_name"],
                tax_identity=row["tax_identity"] if row["tax_identity"] != "" else None
            ))
            
    with open("experiments/gst.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gsts.append(GSTRecord(
                record_id=row["record_id"],
                amount=Decimal(row["amount"]),
                record_date=datetime.strptime(row["record_date"], "%Y-%m-%d").date(),
                reference=row["reference"] if row["reference"] != "" else None,
                vendor_name=row["vendor_name"],
                tax_identity=row["tax_identity"] if row["tax_identity"] != "" else None
            ))
            
    with open("experiments/ground_truth.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ground_truth[(row["purchase_id"], row["gst_id"])] = row["label"]
            
    return purchases, gsts, ground_truth

def run_calibration():
    print("Loading data...")
    purchases, gsts, ground_truth = load_data()
    
    # Use a small sample for the sweep to avoid massive delays
    sample_size = 500
    purchases = purchases[:sample_size]
    # Filter GSTs to only those that might match the sampled purchases or just a sample
    gst_set = {g_id for (p_id, g_id) in ground_truth.keys() if p_id in [p.record_id for p in purchases]}
    gsts = [g for g in gsts if g.record_id in gst_set]
    
    print(f"Sampled {len(purchases)} purchases and {len(gsts)} GST records for sweep.")
    
    thresholds = [0.85, 0.90, 0.95, 0.99]
    temporal_windows = [3, 7, 14, 21]
    
    results = []
    
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=10000, token_document_frequencies={}, digest='scale'), 
        interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
    )
    ref_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=0, normalized_reference_frequency={}, numeric_token_document_frequency={}), 
        policy=ReferenceEvidencePolicy()
    )
    
    for threshold in thresholds:
        for t_window in temporal_windows:
            print(f"Testing threshold={threshold}, temporal_window={t_window}")
            
            config = ReconGraphConfig(decision_config=DecisionConfig(
                decision_mode=DecisionMode.LEGACY,
                policy=DecisionPolicy(auto_match_threshold=threshold)
            ))
            
            providers = [
                VendorEvidenceProvider(vendor_context),
                ReferenceEvidenceProvider(ref_context),
                FinancialEvidenceProvider(),
                TemporalEvidenceProvider(),
                TaxEvidenceProvider()
            ]
            
            engine = ReconGraphEngine(config=config, providers=providers)
            
            t0 = time.time()
            result = engine.reconcile(purchases, gsts)
            duration = time.time() - t0
            
            # Compute metrics
            true_positives = 0
            false_positives = 0
            false_negatives = 0
            
            # Ground truth positives for the sample
            actual_positives = {pair for pair, label in ground_truth.items() 
                                if label == "POSITIVE" and pair[0] in [p.record_id for p in purchases]}
            
            predicted_positives = set()
            for match in result.auto_matches:
                if match.selected_hypothesis:
                    p_ids = [n for n in match.selected_hypothesis.hypothesis.component_nodes if str(n).startswith("urn:recongraph:purchase:")]
                    g_ids = [n for n in match.selected_hypothesis.hypothesis.component_nodes if str(n).startswith("urn:recongraph:gst:")]
                    for p in p_ids:
                        for g in g_ids:
                            predicted_positives.add((str(p).replace("urn:recongraph:purchase:", ""), str(g).replace("urn:recongraph:gst:", "")))
                            
            for pair in predicted_positives:
                if pair in actual_positives:
                    true_positives += 1
                else:
                    false_positives += 1
                    
            false_negatives = len(actual_positives) - true_positives
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            print(f"  auto_matches: {len(result.auto_matches)}, review_packets: {len(result.review_packets)}")
            print(f"  predicted: {len(predicted_positives)}, actual: {len(actual_positives)}")
            print(f"  P: {precision:.4f}, R: {recall:.4f}, F1: {f1:.4f} (took {duration:.2f}s)")
            results.append({
                "threshold": threshold,
                "temporal_window": t_window,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "duration": duration,
                "true_positives": true_positives,
                "false_positives": false_positives,
                "false_negatives": false_negatives
            })
            
    # Save results
    with open("experiments/calibration_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Calibration sweep complete. Results saved to experiments/calibration_results.json")

if __name__ == "__main__":
    run_calibration()
