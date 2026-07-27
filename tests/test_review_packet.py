from recongraph.matching.scoring import ScoringEvidence
from decimal import Decimal
import pytest
from datetime import date
from recongraph.graph.review import ReviewPacketBuilder, ReviewOutcome
from recongraph.graph.decision import ReconciliationDecision, DecisionAction
from recongraph.graph.explainability import DecisionExplanation, EvidenceSummary
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.hypotheses import EvaluatedHypothesis, Hypothesis, EligibilityStatus

def test_auto_match_skip():
    decision = ReconciliationDecision(
        action=DecisionAction.AUTO_MATCH,
        selected_hypothesis=None,
        competitors=(),
        rationale="Clear winner"
    )
    explanation = DecisionExplanation(
        action=DecisionAction.AUTO_MATCH,
        policy_rationale="Clear winner",
        positive_reasons=(),
        limiting_factors=(),
        ambiguity_context=None,
        evidence_summary=None
    )
    
    builder = ReviewPacketBuilder()
    packet = builder.build(decision, explanation, CandidateGraphBuilder().build())
    assert packet is None

def test_checklist_generation_ambiguous():
    from recongraph.graph.fusion_explainability import ExplanationArtifact
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_AMBIGUOUS,
        selected_hypothesis=None,
        competitors=(),
        rationale="Close scores"
    )
    
    explanation = ExplanationArtifact(
        trace_id="test",
        executive_summary={"decision": DecisionAction.REVIEW_AMBIGUOUS.value},
        domain_summaries={},
        technical_details={},
        audit_nodes={}
    )

    builder = ReviewPacketBuilder()
    packet = builder.build(decision, explanation, CandidateGraphBuilder().build())
    
    assert packet is not None
    assert "Disambiguate competing hypotheses manually" in packet.checklist

def test_checklist_generation_limits():
    from recongraph.graph.fusion_explainability import ExplanationArtifact
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_WEAK,
        selected_hypothesis=None,
        competitors=(),
        rationale="Weak score"
    )
    
    explanation = ExplanationArtifact(
        trace_id="test",
        executive_summary={"decision": DecisionAction.REVIEW_WEAK.value},
        domain_summaries={},
        technical_details={"contradicted": ["TAX_NODE", "FINANCIAL_NODE"]},
        audit_nodes={}
    )

    builder = ReviewPacketBuilder()
    packet = builder.build(decision, explanation, CandidateGraphBuilder().build())
    
    assert packet is not None
    assert "Verify GST tax filing manually" in packet.checklist
    assert "Verify exact invoice amounts and potential split payments" in packet.checklist

def test_packet_materialization():
    p1 = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    graph_builder = CandidateGraphBuilder()
    u1, u2 = build_purchase_urn("p1"), build_gst_urn("g1")
    graph_builder.add_node(u1, p1)
    graph_builder.add_node(u2, g1)
    graph = graph_builder.build()
    
    h = EvaluatedHypothesis(
        hypothesis=Hypothesis(
            component_nodes=frozenset([u1, u2]), 
            proposed_edges=frozenset([frozenset([u1, u2])])
        ),
        score=0.9,
            coverage=1.0,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence=ScoringEvidence(),
        violations=frozenset()
    )
    
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_WEAK,
        selected_hypothesis=h,
        competitors=(),
        rationale="Sub threshold"
    )
    
    builder = ReviewPacketBuilder()
    packet = builder.build(decision, None, graph)
    
    assert packet.packet_id == "RP-00001"
    assert len(packet.purchases) == 1
    assert packet.purchases[0].record_id == "p1"
    assert len(packet.gsts) == 1
    assert packet.gsts[0].record_id == "g1"
