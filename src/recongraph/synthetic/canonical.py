from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction
from recongraph.synthetic.models import ScenarioSpecification, ExpectedOutcome, Difficulty
from recongraph.graph.candidate import build_purchase_urn, build_gst_urn
from recongraph.synthetic.operators import AmountMutationOperator

def get_hn001_exact_match() -> ScenarioSpecification:
    """Canonical Scenario HN001: 1:1 Exact Match (Easy)"""
    p = PurchaseRecord(record_id="p_hn001", amount=100.0, record_date=date(2023,1,1), reference="INV-HN001", vendor_name="Vendor A", tax_identity="TAX-A")
    g = GSTRecord(record_id="g_hn001", amount=100.0, record_date=date(2023,1,1), reference="INV-HN001", vendor_name="Vendor A", tax_identity="TAX-A")
    
    p_urn = build_purchase_urn(p.record_id)
    g_urn = build_gst_urn(g.record_id)
    
    return ScenarioSpecification(
        scenario_id="HN001",
        difficulty=Difficulty.EASY,
        base_purchases=(p,),
        base_gsts=(g,),
        purchase_mutations=(),
        gst_mutations=(),
        expected_outcome=ExpectedOutcome(
            expected_decision=DecisionAction.AUTO_MATCH,
            expected_component_urns=frozenset({p_urn, g_urn}),
            expected_hypothesis_edges=frozenset({frozenset({p_urn, g_urn})})
        )
    )

def get_hn004_rare_reference_overrides_amount() -> ScenarioSpecification:
    """Canonical Scenario HN004: Rare Reference Overrides Amount Discrepancy (Medium)"""
    p = PurchaseRecord(record_id="p_hn004", amount=100.0, record_date=date(2023,1,1), reference="UNIQUE-HN004", vendor_name="Vendor B", tax_identity="TAX-B")
    g = GSTRecord(record_id="g_hn004", amount=100.0, record_date=date(2023,1,1), reference="UNIQUE-HN004", vendor_name="Vendor B", tax_identity="TAX-B")
    
    p_urn = build_purchase_urn(p.record_id)
    g_urn = build_gst_urn(g.record_id)
    
    return ScenarioSpecification(
        scenario_id="HN004",
        difficulty=Difficulty.MEDIUM,
        base_purchases=(p,),
        base_gsts=(g,),
        purchase_mutations=(),
        gst_mutations=((0, AmountMutationOperator(99.0)),),
        expected_outcome=ExpectedOutcome(
            expected_decision=DecisionAction.REVIEW_WEAK,
            expected_component_urns=frozenset({p_urn, g_urn}),
            expected_hypothesis_edges=frozenset({frozenset({p_urn, g_urn})})
        )
    )
