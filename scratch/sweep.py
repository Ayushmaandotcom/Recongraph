import sys
from collections import defaultdict
from recongraph.synthetic.reconbench import generate_reconbench_dataset, ADVERSARIAL_TYPES, NOISY_POSITIVE_TYPES
from recongraph.benchmark.runner import execute_reconbench
from recongraph.config import DecisionConfig, ReconGraphConfig
from recongraph.graph.decision import DecisionPolicy, DecisionAction
from recongraph.engine import ReconGraphEngine
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from typing import Any, cast

def _build_engine(threshold):
    config = ReconGraphConfig(
        decision_config=DecisionConfig(policy=DecisionPolicy(auto_match_threshold=threshold, minimum_coverage_threshold=0.80))
    )
    corpus_profile = ReferenceCorpusProfile(reference_count=1, normalized_reference_frequency={'dummy': 1}, numeric_token_document_frequency={})
    ref_context = ReferenceEvidenceContext(corpus_profile, ReferenceEvidencePolicy())
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85
    )
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context)
    ]
    return ReconGraphEngine(config, providers)

print("Generating dataset...")
scenarios = generate_reconbench_dataset(500, seed=42)
print(f"Generated {len(scenarios)} scenarios.")

thresholds = [0.85, 0.90, 0.95, 0.99]
results = {}

for threshold in thresholds:
    engine = _build_engine(threshold)
    
    metrics = {
        "EXACT": {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "Total": 0},
        "NOISY_POSITIVE": {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "Total": 0},
        "ADVERSARIAL": {"TP": 0, "FP": 0, "FN": 0, "TN": 0, "Total": 0},
    }
    
    for spec in scenarios:
        scenario_type = spec.scenario_id.split("-")[1]
        if scenario_type == "EXACT":
            bucket = "EXACT"
        elif scenario_type in NOISY_POSITIVE_TYPES:
            bucket = "NOISY_POSITIVE"
        elif scenario_type in ADVERSARIAL_TYPES:
            bucket = "ADVERSARIAL"
        else:
            continue
            
        metrics[bucket]["Total"] += 1
        
        purchases = list(spec.base_purchases)
        gsts = list(spec.base_gsts)
        for idx, op in spec.purchase_mutations:
            op_any = cast(Any, op)
            purchases[idx] = op_any.apply(purchases[idx])
        for idx, op in spec.gst_mutations:
            op_any = cast(Any, op)
            gsts[idx] = op_any.apply(gsts[idx])
            
        result = engine.reconcile(purchases, gsts)
        
        actual = DecisionAction.AUTO_MATCH if result.auto_matches else DecisionAction.REVIEW_WEAK # Simplification
        expected = spec.expected_outcome.expected_decision
        
        is_positive = (actual == DecisionAction.AUTO_MATCH)
        expected_positive = (expected == DecisionAction.AUTO_MATCH)
        
        if is_positive and expected_positive:
            metrics[bucket]["TP"] += 1
        elif is_positive and not expected_positive:
            metrics[bucket]["FP"] += 1
        elif not is_positive and expected_positive:
            metrics[bucket]["FN"] += 1
        else:
            metrics[bucket]["TN"] += 1
            
    results[threshold] = metrics
    print(f"\nThreshold: {threshold}")
    for b, m in metrics.items():
        if m["Total"] > 0:
            recall = m["TP"] / (m["TP"] + m["FN"]) if (m["TP"] + m["FN"]) > 0 else 0
            fp = m["FP"]
            print(f"  {b:15s} | Recall: {recall:.4f} | FP: {fp}")
