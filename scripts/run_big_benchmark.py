import csv
import time
import json
from pathlib import Path
from decimal import Decimal
from datetime import date
from typing import List

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine, ReconGraphConfig
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider,
    VendorEvidenceProvider, ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext
from recongraph.matching.reference_evidence import build_reference_corpus_profile, ReferenceEvidenceContext, ReferenceEvidencePolicy

class BenchmarkRunner:
    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        
    def load_data(self):
        pr_list = []
        gst_list = []
        labels = []
        with open(self.dataset_path, "r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                pr_amt = row.get("pr_amount")
                gst_amt = row.get("gst_amount")
                pr_amt = pr_amt if pr_amt not in (None, "") else "0"
                gst_amt = gst_amt if gst_amt not in (None, "") else "0"
                
                pr = PurchaseRecord(
                    record_id=row["packet_id"] + "_PR",
                    vendor_name=row["pr_vendor"],
                    reference=row["pr_ref"],
                    amount=Decimal(pr_amt),
                    record_date=date.fromisoformat(row.get("pr_date") or "2000-01-01"),
                    tax_identity=row["pr_gstin"]
                )
                gst = GSTRecord(
                    record_id=row["packet_id"] + "_GST",
                    vendor_name=row["gst_vendor"],
                    reference=row["gst_ref"],
                    amount=Decimal(gst_amt),
                    record_date=date.fromisoformat(row.get("gst_date") or "2000-01-01"),
                    tax_identity=row["gst_gstin"]
                )
                pr_list.append(pr)
                gst_list.append(gst)
                labels.append(row["label"])
        return pr_list, gst_list, labels

    def evaluate(self, name: str, results: list, labels: list, time_taken: float):
        # Flatten engine results by packet_id
        # In this mock benchmark, each row is an independent pair (P, G)
        
        # Calculate metrics
        tp = fp = tn = fn = 0
        auto_matches = 0
        reviews = 0
        
        for res_dict, label in zip(results, labels):
            ai_prov = res_dict.get("ai_provenance") or {}
            decision = ai_prov.get("decision", "NO_MATCH")
            if not decision or decision == "UNKNOWN":
                decision = res_dict.get("decision", "NO_MATCH")
                
            is_true_match = label in ("EXACT_MATCH", "FUZZY_MATCH")
            
            if decision == "AUTO_MATCH":
                auto_matches += 1
                if is_true_match:
                    tp += 1
                else:
                    fp += 1
            elif decision in ("REVIEW", "REVIEW_AMBIGUOUS", "REVIEW_WEAK"):
                reviews += 1
                # In AI+HITL, reviews are successfully resolved
                if "HITL" in name:
                    if is_true_match:
                        tp += 1
                    else:
                        tn += 1
            else:
                if is_true_match:
                    fn += 1
                else:
                    tn += 1
                    
        total = len(labels)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"--- {name} ---")
        print(f"Total processed: {total}")
        print(f"Time Taken: {time_taken:.2f}s ({(time_taken/total)*1000:.2f}ms/invoice)")
        print(f"Auto-match rate: {(auto_matches/total)*100:.1f}%")
        print(f"Review rate: {(reviews/total)*100:.1f}%")
        print(f"False-match rate (FPR): {(fp/total)*100:.2f}%")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}\n")
        
        return {
            "name": name,
            "precision": precision, "recall": recall, "f1": f1,
            "auto_rate": auto_matches/total, "review_rate": reviews/total,
            "false_match_rate": fp/total
        }

    def run(self):
        pr_list, gst_list, labels = self.load_data()
        
        # Build shared engine context
        corpus = build_reference_corpus_profile([r.reference for r in pr_list + gst_list if r.reference])
        ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
        vendor_ctx = VendorIdentityContext(corpus_profile=None)
        providers = [
            FinancialEvidenceProvider(), TemporalEvidenceProvider(), TaxEvidenceProvider(),
            VendorEvidenceProvider(vendor_ctx), ReferenceEvidenceProvider(ref_ctx),
        ]
        
        config = ReconGraphConfig()
        
        print("Starting Benchmark on 2500 Synthetic Test Cases...\n")
        
        # Benchmark A: Deterministic
        print("Running Benchmark A (Deterministic)...")
        t0 = time.time()
        # To simulate deterministic, we disable ML filter override. We'll just run it normally
        # but intercept the output to look only at `decision` (ignoring ai_provenance override)
        engine = ReconGraphEngine(config, providers)
        
        det_results = []
        ai_results = []
        for i in range(len(pr_list)):
            p = pr_list[i]
            g = gst_list[i]
            
            # 1. Force candidate edge for benchmark evaluation
            from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
            from recongraph.graph.algorithms import extract_connected_components
            from recongraph.graph.search import HypothesisSearcher
            from recongraph.graph.evaluator import HypothesisEvaluator
            from recongraph.graph.decision import DecisionEngine, DecisionAction
            
            graph_builder = CandidateGraphBuilder()
            graph_builder.add_node(build_purchase_urn(p.record_id), p)
            graph_builder.add_node(build_gst_urn(g.record_id), g)
            # Force edge to simulate blocking phase success
            graph_builder.add_candidate_edge(build_purchase_urn(p.record_id), build_gst_urn(g.record_id), {"forced": "true"})
            graph = graph_builder.build()
            
            # Manually run the engine evaluation flow for this forced component
            comp = list(extract_connected_components(graph))[0]
            searcher = HypothesisSearcher()
            evaluator = HypothesisEvaluator(providers, config.decision_config.relationship_policy)
            decision_engine = DecisionEngine(config.decision_config.policy)
            
            hypotheses = searcher.search(comp)
            evaluated = [evaluator.evaluate(graph, h) for h in hypotheses]
            decision = decision_engine.decide(evaluated)
            
            # Now run engine's AI layer manually to get the provenance
            ml_confidence = engine.ml_filter.predict_confidence(p, g, {"pr_node_degree": 1, "gst_node_degree": 1, "component_size": 2, "candidate_count": 1})
            
            # Apply deterministic baseline
            det_decision = decision.action.name
            
            # Apply Phase 9 AI thresholds
            if 0.70 <= ml_confidence < 0.95:
                ai_decision = "REVIEW"
            elif ml_confidence < 0.70:
                ai_decision = "REJECT"
            else:
                ai_decision = "AUTO_MATCH"
                
            det_results.append({"decision": det_decision})
            ai_results.append({"ai_provenance": {"decision": ai_decision, "confidence": ml_confidence}})
            
        t1 = time.time()
        self.evaluate("Benchmark A (Deterministic)", det_results, labels, t1 - t0)
        
        # Benchmark B: AI (Uses ML predictions without human resolution)
        print("Running Benchmark B (AI only)...")
        self.evaluate("Benchmark B (AI Mode)", ai_results, labels, t1 - t0)
        
        # Benchmark C: AI + HITL
        print("Running Benchmark C (AI + Human-In-The-Loop)...")
        self.evaluate("Benchmark C (AI + HITL)", ai_results, labels, t1 - t0)

if __name__ == "__main__":
    runner = BenchmarkRunner(Path("datasets/ai_production/master_dataset.csv"))
    runner.run()
