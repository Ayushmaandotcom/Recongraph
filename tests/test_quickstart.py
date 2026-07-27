from datetime import date
from decimal import Decimal
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    VendorEvidenceProvider,
    ReferenceEvidenceProvider,
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def test_readme_quick_start():
    # 1. Setup Providers
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'),
        interpreter_policy_version='1.0.0',
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )
    reference_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(
            reference_count=1, 
            normalized_reference_frequency={"inv2026a": 1}, 
            numeric_token_document_frequency={"2026": 1}
        ),
        policy=ReferenceEvidencePolicy()
    )
    providers = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(reference_context),
        FinancialEvidenceProvider(tolerance=0.05),
        TemporalEvidenceProvider(max_days=7),
        TaxEvidenceProvider()
    ]

    # 2. Initialize Engine (Using FUSION mode as it replaces shadow)
    config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION))
    engine = ReconGraphEngine(config=config, providers=providers)

    # 3. Define Evidence (Fixing Decimal arguments to ensure they are strings to avoid float inaccuracies)
    purchase = PurchaseRecord(
        record_id="P-001",
        vendor_name="TechCorp Private Limited",
        reference="INV-2026-A",
        amount=Decimal("15000.00"),
        record_date=date(2026, 1, 15),
        tax_identity="07ABCDE1234F1Z2"
    )

    gst = GSTRecord(
        record_id="G-001",
        vendor_name="TECHCORP PVT LTD",
        reference="2026-A",
        amount=Decimal("15000.00"),
        record_date=date(2026, 1, 16),
        tax_identity="07ABCDE1234F1Z2"
    )

    # 4. Evaluate Match
    result = engine.reconcile([purchase], [gst])

    if result.auto_matches:
        print(f"Action: {result.auto_matches[0].action.value}")
    elif result.review_packets:
        packet = result.review_packets[0]
        print(f"Action: {packet.action.value}")
        if packet.explanation:
            print(f"Explanation: {packet.explanation.executive_summary['decision']}")
            
    assert len(result.auto_matches) == 1 or len(result.review_packets) == 2
