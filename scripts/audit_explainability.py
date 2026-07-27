import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    VendorEvidenceProvider, ReferenceEvidenceProvider, FinancialEvidenceProvider, AmountMultipleEvidenceProvider, AmountMultipleEvidenceProvider,
    TemporalEvidenceProvider, TaxEvidenceProvider
)
from recongraph.matching.scoring import SignalName
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

from recongraph.graph.decision import DecisionPolicy

def test_explainability():
    print("Running Phase G: Explainability Audit...")
    
    # Lower coverage threshold to 0.40 to force REVIEW_WEAK instead of NO_MATCH for a 0.50 score
    policy = DecisionPolicy(minimum_coverage_threshold=0.40)
    config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION, policy=policy))
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'), 
        interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
    )
    ref_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(
            reference_count=100, 
            normalized_reference_frequency={"inv999": 1, "other": 99}, 
            numeric_token_document_frequency={"999": 1, "000": 99}
        ), 
        policy=ReferenceEvidencePolicy()
    )
    
    providers = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context),
        FinancialEvidenceProvider(tolerance=0.05),
        TemporalEvidenceProvider(max_days=0),
        TaxEvidenceProvider()
    ]
    
    # We want a scenario where exactly ONE provider succeeds (Financial),
    # but Tax explicitly contradicts, and others fail, so we get exactly 1 Review packet.
    
    engine = ReconGraphEngine(config=config, providers=providers)
    
    purchase = PurchaseRecord(
        record_id="P-001",
        vendor_name="Determinism Test Pvt Ltd",
        reference="INV-999",
        amount=Decimal("15000.00"),
        record_date=date(2026, 1, 15),
        tax_identity="07ABCDE1234F1Z1"
    )
    
    gst = GSTRecord(
        record_id="G-001",
        vendor_name="COMPLETELY DIFFERENT CORP",
        reference="INV-888",
        amount=Decimal("15000.00"),
        record_date=date(2026, 1, 16),
        tax_identity="27XYZQR5678S1Z1"  # Different state code, different pan!
    )
    
    result = engine.reconcile([purchase], [gst])
    
    print(f"Auto matches: {len(result.auto_matches)}")
    print(f"Review packets: {len(result.review_packets)}")
    for trace in result.traces:
        print(trace)
        
    assert len(result.review_packets) == 1, "Expected exactly 1 review packet."
    packet = result.review_packets[0]
    
    if packet.explanation is None:
        raise RuntimeError("Explanation artifact is missing.")
        
    explanation = packet.explanation
    
    print(f"Decision Action: {explanation.executive_summary['decision']}")
    
    print(f"Domain summary keys: {list(explanation.domain_summaries.keys())}")
    
    # We might need to use the Enum value if it is an Enum
    tax_summary = explanation.domain_summaries.get(SignalName.TAX_IDENTITY) or explanation.domain_summaries.get("tax_identity")
    
    assert tax_summary is not None, "Tax summary is missing."
    print(f"Tax summary: {tax_summary}")
    assert "TAX_IDENTITY_CONFLICT" in tax_summary["violations"], "Explanation hallucinated tax support or missed contradiction."
    
    print("Explanation Audit: PASS (No hallucinations detected).")
    
if __name__ == "__main__":
    test_explainability()
