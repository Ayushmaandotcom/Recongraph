from decimal import Decimal
import pytest
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.config import ReconGraphConfig
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, ReferenceEvidenceProvider, VendorEvidenceProvider, TaxEvidenceProvider
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.engine import ReconGraphEngine
from recongraph.graph.decision import DecisionAction
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile

def test_engine_reconcile():
    p1 = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")

    from recongraph.config import DecisionConfig, DecisionMode
    config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION))
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
    
    assert result.engine_version == ReconGraphEngine.VERSION
    assert len(result.auto_matches) == 1

def test_conservation_hole_auto_match_leftovers():
    # If p1 matches g1 perfectly, but p2 shares a blocking key and is left unmatched,
    # p2 MUST be returned as a REVIEW_INSUFFICIENT_EVIDENCE packet.
    p1 = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    # p2 shares tax identity with p1/g1, so it gets grouped into the same component.
    p2 = PurchaseRecord(record_id="p2", amount=Decimal("999.0"), record_date=date(2023,1,1), reference="INV2", vendor_name="B", tax_identity="TAX1")

    from recongraph.config import DecisionConfig
    from recongraph.graph.decision import DecisionPolicy
    config = ReconGraphConfig(decision_config=DecisionConfig(policy=DecisionPolicy(minimum_coverage_threshold=0.5)))
    context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=2, normalized_reference_frequency={"inv1": 1, "inv2": 1}, numeric_token_document_frequency={"1": 1, "2": 1}),
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
    result = engine.reconcile([p1, p2], [g1])
    
    # We expect p1 and g1 to AUTO_MATCH.
    assert len(result.auto_matches) == 1
    
    # We expect p2 to be conserved as a ReviewPacket because it is a leftover unmatched node
    assert len(result.review_packets) == 1
    leftover_packet = result.review_packets[0]
    assert leftover_packet.action == DecisionAction.NO_MATCH
    assert len(leftover_packet.purchases) == 1
    assert leftover_packet.purchases[0].record_id == "p2"
    assert len(leftover_packet.gsts) == 0
    trace = result.traces[0]
    
    assert trace.engine_version == ReconGraphEngine.VERSION
    assert trace.config_hash is not None
    # Assert serializability
    trace_dict = trace.to_dict()
    assert trace_dict["engine_version"] == engine.VERSION
