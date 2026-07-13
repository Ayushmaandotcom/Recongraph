import pytest
from datetime import date
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.hypotheses import Hypothesis, EligibilityStatus
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceEvidencePolicy, ReferenceCorpusProfile
from recongraph.matching.scoring import SignalName
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY

@pytest.fixture
def empty_reference_context():
    return ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(
            reference_count=3,
            normalized_reference_frequency={"inv1": 1, "inv2": 1, "inv3": 1},
            numeric_token_document_frequency={"1": 1, "2": 1, "3": 1}
        ),
        policy=ReferenceEvidencePolicy()
    )

def test_evaluator_case_1(empty_reference_context):
    # P1 (100k) -> G1 (100k)
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    builder = CandidateGraphBuilder()
    u1, u2 = build_purchase_urn("p1"), build_gst_urn("g1")
    builder.add_node(u1, p1)
    builder.add_node(u2, g1)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2]),
        proposed_edges=frozenset([frozenset([u1, u2])])
    )
    
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(),
        ReferenceEvidenceProvider(empty_reference_context)
    ]
    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    result = evaluator.evaluate(builder.build(), hypothesis)
    
    assert result.eligibility == EligibilityStatus.ELIGIBLE
    assert result.score > 0.8  # Strong match
    assert len(result.violations) == 0

def test_evaluator_case_2(empty_reference_context):
    # P1 (100k) -> G1 (50k), G2 (50k)
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=50.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g2 = GSTRecord(record_id="g2", amount=50.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    builder = CandidateGraphBuilder()
    u1, u2, u3 = build_purchase_urn("p1"), build_gst_urn("g1"), build_gst_urn("g2")
    builder.add_node(u1, p1)
    builder.add_node(u2, g1)
    builder.add_node(u3, g2)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2, u3]),
        proposed_edges=frozenset([frozenset([u1, u2]), frozenset([u1, u3])])
    )
    
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(),
        ReferenceEvidenceProvider(empty_reference_context)
    ]
    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    result = evaluator.evaluate(builder.build(), hypothesis)
    
    assert result.eligibility == EligibilityStatus.ELIGIBLE
    assert result.supporting_evidence["signals"][SignalName.AMOUNT] == 1.0
    assert result.score > 0.7

def test_evaluator_case_3(empty_reference_context):
    # P1 (100k) -> G1 (40k), G2 (40k) (Incorrect sum)
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV2", vendor_name="B", tax_identity="TAX2")
    g1 = GSTRecord(record_id="g1", amount=40.0, record_date=date(2023,1,1), reference="INV2", vendor_name="B", tax_identity="TAX2")
    g2 = GSTRecord(record_id="g2", amount=40.0, record_date=date(2023,1,1), reference="INV2", vendor_name="B", tax_identity="TAX2")
    
    builder = CandidateGraphBuilder()
    u1, u2, u3 = build_purchase_urn("p1"), build_gst_urn("g1"), build_gst_urn("g2")
    builder.add_node(u1, p1)
    builder.add_node(u2, g1)
    builder.add_node(u3, g2)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2, u3]),
        proposed_edges=frozenset([frozenset([u1, u2]), frozenset([u1, u3])])
    )
    
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(),
        ReferenceEvidenceProvider(empty_reference_context)
    ]
    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    result = evaluator.evaluate(builder.build(), hypothesis)
    
    assert result.supporting_evidence["signals"][SignalName.AMOUNT] < 1.0
    assert result.score < 0.9

def test_evaluator_case_4(empty_reference_context):
    # P1 -> G1 (Semantic contradiction: date > max_days)
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV3", vendor_name="C", tax_identity="TAX3")
    g1 = GSTRecord(record_id="g1", amount=100.0, record_date=date(2024,1,1), reference="INV3", vendor_name="C", tax_identity="TAX3")
    
    builder = CandidateGraphBuilder()
    u1, u2 = build_purchase_urn("p1"), build_gst_urn("g1")
    builder.add_node(u1, p1)
    builder.add_node(u2, g1)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2]),
        proposed_edges=frozenset([frozenset([u1, u2])])
    )
    
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(),
        ReferenceEvidenceProvider(empty_reference_context)
    ]
    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    result = evaluator.evaluate(builder.build(), hypothesis)
    
    assert result.eligibility == EligibilityStatus.INELIGIBLE
    assert "TEMPORAL_MAX_DAYS_EXCEEDED" in result.violations
