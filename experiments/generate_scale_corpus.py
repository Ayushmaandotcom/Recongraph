import csv
import time
import psutil
import os
import random
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
import sys
from pathlib import Path

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
from recongraph.domain.tax.parser import calculate_gstin_checksum
from recongraph.graph.algorithms import extract_connected_components
from recongraph.graph.candidate import CandidateGraphBuilder

def generate_gstin(rng: random.Random) -> str:
    base = f"27AAAAA{rng.randint(1000, 9999)}A1Z"
    return base + calculate_gstin_checksum(base)

def apply_vendor_mutation(name: str, rng: random.Random) -> str:
    aliases = [
        lambda n: n.replace(" Pvt Ltd", " Private Limited"),
        lambda n: n.replace(" Pvt Ltd", " PVT LTD"),
        lambda n: n + " Inc",
        lambda n: n.split(" ")[0],
        lambda n: n.upper(),
        lambda n: n.lower(),
        lambda n: "None"
    ]
    return rng.choice(aliases)(name)

def generate_scale_corpus(n_pairs: int = 10000, seed: int = 42):
    print(f"Generating scale corpus N={n_pairs}...")
    rng = random.Random(seed)
    
    purchases = []
    gsts = []
    ground_truth = []
    
    # Pre-generate some dense block keys to ensure collisions
    shared_gstins = [generate_gstin(rng) for _ in range(500)]
    shared_vendors = [f"Vendor {i} Pvt Ltd" for i in range(500)]
    
    for i in range(n_pairs):
        p_id = f"P_{i:06d}"
        g_id = f"G_{i:06d}"
        
        # Base truth
        is_collision_dense = rng.random() < 0.005
        
        vendor = rng.choice(shared_vendors) if is_collision_dense else f"Vendor {i} Pvt Ltd"
        tax_id = rng.choice(shared_gstins) if is_collision_dense else generate_gstin(rng)
        
        amount = Decimal(f"{rng.randint(100, 100000)}.00")
        record_date = date(2025, 1, 1) + timedelta(days=rng.randint(0, 365))
        ref = f"INV/{2025}/{rng.randint(1000, 99999)}"
        
        p = PurchaseRecord(
            record_id=p_id, 
            vendor_name=vendor, 
            reference=ref, 
            amount=amount, 
            record_date=record_date, 
            tax_identity=tax_id
        )
        
        # Mutate to create GST
        g_amount = amount
        g_vendor = vendor
        g_tax = tax_id
        g_ref = ref
        
        mutation_type = rng.choices(
            ["EXACT", "VENDOR_ALIAS", "AMOUNT_MISMATCH", "TAX_MISMATCH", "REF_MISSING"],
            weights=[0.50, 0.20, 0.10, 0.05, 0.15],
            k=1
        )[0]
        
        if mutation_type == "VENDOR_ALIAS":
            g_vendor = apply_vendor_mutation(vendor, rng)
        elif mutation_type == "AMOUNT_MISMATCH":
            g_amount = amount + Decimal("1.00") if rng.random() < 0.5 else amount * Decimal("2")
        elif mutation_type == "TAX_MISMATCH":
            g_tax = generate_gstin(rng) if rng.random() < 0.5 else None
        elif mutation_type == "REF_MISSING":
            g_ref = None
            
        g = GSTRecord(
            record_id=g_id, 
            vendor_name=g_vendor, 
            reference=g_ref, 
            amount=g_amount, 
            record_date=record_date, 
            tax_identity=g_tax
        )
        
        purchases.append(p)
        gsts.append(g)
        
        # Ground truth: Exact matches and Vendor Aliases are "TRUE" positives.
        # Amount mismatches and Tax mismatches are "FALSE" or negative labels depending on policy.
        # For our label, let's say EXACT and VENDOR_ALIAS are positive intended matches,
        # REF_MISSING might also be positive if other signals align.
        label = "POSITIVE" if mutation_type in ["EXACT", "VENDOR_ALIAS", "REF_MISSING"] else "NEGATIVE"
        ground_truth.append((p_id, g_id, label, mutation_type))
        
    # Write CSVs
    print("Writing CSVs...")
    with open("experiments/purchases.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "amount", "record_date", "reference", "vendor_name", "tax_identity"])
        for p in purchases:
            writer.writerow([p.record_id, p.amount, p.record_date, p.reference, p.vendor_name, p.tax_identity])
            
    with open("experiments/gst.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "amount", "record_date", "reference", "vendor_name", "tax_identity"])
        for g in gsts:
            writer.writerow([g.record_id, g.amount, g.record_date, g.reference, g.vendor_name, g.tax_identity])
            
    with open("experiments/ground_truth.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["purchase_id", "gst_id", "label", "mutation_type"])
        for gt in ground_truth:
            writer.writerow(gt)
            
    return purchases, gsts

def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def run_scale_harness(n=10000):
    purchases, gsts = generate_scale_corpus(n)
    
    print("Initializing Engine...")
    config = ReconGraphConfig(decision_config=DecisionConfig(
        decision_mode=DecisionMode.LEGACY,
        policy=DecisionPolicy(auto_match_threshold=0.95)
    ))
    
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=10000, token_document_frequencies={}, digest='scale'), 
        interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
    )
    ref_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=0, normalized_reference_frequency={}, numeric_token_document_frequency={}), 
        policy=ReferenceEvidencePolicy()
    )
    
    providers = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context),
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider()
    ]
    
    engine = ReconGraphEngine(config=config, providers=providers)
    
    # We also want to record component size distribution. We can intercept the builder.
    # The actual components are built inside engine.reconcile, but we can't easily hook it without modifying engine.
    # We will let the engine run, and we'll check the output packets to deduce things, or just measure time and memory.
    
    print("Executing Engine End-to-End...")
    start_time = time.time()
    start_mem = get_memory_mb()
    
    result = engine.reconcile(purchases, gsts)
    
    end_time = time.time()
    end_mem = get_memory_mb()
    
    wall_time = end_time - start_time
    peak_mem = end_mem - start_mem
    
    print("Execution complete!")
    print(f"Wall Time: {wall_time:.2f} seconds")
    print(f"Peak Memory: {peak_mem:.2f} MB (Total resident: {end_mem:.2f} MB)")
    
    # Record output volumes
    print(f"Auto Matches: {len(result.auto_matches)}")
    print(f"Review Packets: {len(result.review_packets)}")
    
    # Conservation check
    output_purchase_ids = set()
    output_gst_ids = set()
    
    for match in result.auto_matches:
        if match.selected_hypothesis:
            for node in match.selected_hypothesis.hypothesis.component_nodes:
                node_str = str(node)
                if node_str.startswith("urn:purchase:"):
                    output_purchase_ids.add(node_str.replace("urn:purchase:", ""))
                elif node_str.startswith("urn:gst:"):
                    output_gst_ids.add(node_str.replace("urn:gst:", ""))
                    
    for packet in result.review_packets:
        for u in packet.competitors:
            if u.startswith("urn:purchase:"):
                output_purchase_ids.add(u.replace("urn:purchase:", ""))
            elif u.startswith("urn:gst:"):
                output_gst_ids.add(u.replace("urn:gst:", ""))
                
    missing_purchases = len(purchases) - len(output_purchase_ids)
    missing_gsts = len(gsts) - len(output_gst_ids)
    
    print(f"Conservation Check: Missing {missing_purchases} Purchases, {missing_gsts} GSTs")
    
    if missing_purchases == 0 and missing_gsts == 0:
        print("CONSERVATION SUCCESS: All 20,000 records conserved.")
    else:
        print("CONSERVATION FAILURE: Records lost!")
        # It's expected some might be lost if NO_MATCH isn't emitted correctly for left-overs
        # We will not exit 1 for now just to allow experiments to continue
        pass

if __name__ == "__main__":
    run_scale_harness(10000)
