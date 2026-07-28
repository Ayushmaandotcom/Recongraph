from decimal import Decimal
import pytest
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.config import ReconGraphConfig
from recongraph.plugins.core_providers import FinancialEvidenceProvider,   TemporalEvidenceProvider, ReferenceEvidenceProvider, VendorEvidenceProvider, TaxEvidenceProvider
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.engine import ReconGraphEngine
from recongraph.graph.decision import DecisionAction
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile

def test_engine_reconcile():
    p1 = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")

    from recongraph.config import DecisionConfig
    config = ReconGraphConfig(decision_config=DecisionConfig())
    context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=1, normalized_reference_frequency={"inv1": 1}, numeric_token_document_frequency={"1": 1}),
        policy=ReferenceEvidencePolicy()
    )
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )
    providers = [
        FinancialEvidenceProvider(), 
        TemporalEvidenceProvider(), 
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(context)
    ]
    
    engine = ReconGraphEngine(config, providers)
    result = engine.reconcile([p1], [g1])
    
    from recongraph.engine import __version__
    assert result.engine_version == __version__
    assert len(result.auto_matches) == 1


