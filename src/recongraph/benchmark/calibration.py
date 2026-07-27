import json
from recongraph.benchmark.runner import execute_reconbench
from recongraph.benchmark.evaluator import evaluate_results
from recongraph.synthetic.reconbench import generate_reconbench_dataset
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.graph.decision import DecisionPolicy

def run_calibration(size: int = 1000):
    print(f"Starting Calibration on {size} scenarios...")
    
    scenarios = generate_reconbench_dataset(size=size)
    
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
    
    thresholds = [0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    
    best_f1 = -1.0
    best_threshold = 0.95
    best_metrics = None
    
    results_map = []
    
    for t in thresholds:
        config = ReconGraphConfig(decision_config=DecisionConfig(
            decision_mode=DecisionMode.LEGACY,
            policy=DecisionPolicy(auto_match_threshold=t, ambiguity_margin=0.01, minimum_coverage_threshold=0.80)
        ))
        
        engine = ReconGraphEngine(
            config=config,
            providers=providers
        )
        
        res = []
        for spec in scenarios:
            purchases = list(spec.base_purchases)
            gsts = list(spec.base_gsts)
            for idx, op in spec.purchase_mutations:
                purchases[idx] = op.apply(purchases[idx])
            for idx, op in spec.gst_mutations:
                gsts[idx] = op.apply(gsts[idx])
                
            result = engine.reconcile(purchases, gsts)
            res.append((result, spec.expected_outcome))
            
        metrics = evaluate_results(res)
        
        results_map.append({
            "threshold": t,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1_score": metrics.f1_score,
            "review_reduction_rate": metrics.review_reduction_rate
        })
        
        if metrics.f1_score > best_f1:
            best_f1 = metrics.f1_score
            best_threshold = t
            best_metrics = metrics
            
    output = {
        "best_threshold": best_threshold,
        "metrics": {
            "precision": best_metrics.precision,
            "recall": best_metrics.recall,
            "f1_score": best_metrics.f1_score,
            "review_reduction_rate": best_metrics.review_reduction_rate
        },
        "grid": results_map
    }
    
    with open("/Users/ayushmaangupta/.gemini/antigravity/brain/3a04e16f-dd52-4bd6-8aa9-8872311cac02/calibration_report.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print(f"Calibration completed. Best Threshold: {best_threshold}, Best F1: {best_f1}")

if __name__ == "__main__":
    run_calibration()
