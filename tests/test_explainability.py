import pytest
from decimal import Decimal
from recongraph.graph.hypotheses import EvaluatedHypothesis, Hypothesis, EligibilityStatus
from recongraph.graph.decision import ReconciliationDecision, DecisionAction
from recongraph.matching.scoring import SignalName
from recongraph.graph.explainability import ExplanationBuilder
from recongraph.domain.financial.pipeline import AmountInterpretation, AmountRelationship
from recongraph.domain.financial.amount_projection import ProjectedAmountSimilarity

def mock_amount_meta(rel: AmountRelationship, sim: float, notes=None):
    interp = AmountInterpretation(
        relationship=rel,
        amount_a=Decimal("100"), amount_b=Decimal("100"),
        absolute_difference=Decimal("0"), relative_difference=Decimal("0"), residual=Decimal("0"),
        currency_status="USD", comparison_basis="Gross", notes=notes or ()
    )
    proj = ProjectedAmountSimilarity(sim)
    return {"interpretation": interp, "projection": proj}

def test_explain_no_match():
    decision = ReconciliationDecision(
        action=DecisionAction.NO_MATCH,
        selected_hypothesis=None,
        competitors=(),
        rationale="No mathematically eligible hypotheses generated."
    )
    builder = ExplanationBuilder()
    explanation = builder.build(decision)
    
    assert explanation.action == DecisionAction.NO_MATCH
    assert "No mathematically eligible" in explanation.limiting_factors[0]
    assert explanation.evidence_summary is None

def test_explain_auto_match():
    h = EvaluatedHypothesis(
        hypothesis=Hypothesis(frozenset(), frozenset()),
        score=0.99,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence={
            "signals": {
                SignalName.AMOUNT: 1.0,
                SignalName.REFERENCE: 0.95,
                SignalName.TEMPORAL: 1.0,
                SignalName.ENTITY: 0.9,
                SignalName.TAX_IDENTITY: 1.0
            },
            "metadata": {
                SignalName.AMOUNT: mock_amount_meta(AmountRelationship.EXACT_MATCH, 1.0, ("Amounts match perfectly.",))
            }
        },
        violations=frozenset()
    )
    decision = ReconciliationDecision(
        action=DecisionAction.AUTO_MATCH,
        selected_hypothesis=h,
        competitors=(),
        rationale="Cleared threshold."
    )
    
    builder = ExplanationBuilder()
    explanation = builder.build(decision)
    
    assert explanation.action == DecisionAction.AUTO_MATCH
    assert any("Amounts match perfectly" in r for r in explanation.positive_reasons)
    assert any("Strong reference match" in r for r in explanation.positive_reasons)
    assert len(explanation.limiting_factors) == 0
    assert explanation.evidence_summary.amount_projection.similarity == 1.0

def test_explain_review_ambiguous():
    h1 = EvaluatedHypothesis(
        hypothesis=Hypothesis(frozenset(), frozenset()),
        score=0.95,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence={"signals": {SignalName.AMOUNT: 1.0}, "metadata": {SignalName.AMOUNT: mock_amount_meta(AmountRelationship.EXACT_MATCH, 1.0)}},
        violations=frozenset()
    )
    h2 = EvaluatedHypothesis(
        hypothesis=Hypothesis(frozenset(), frozenset()),
        score=0.94,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence={"signals": {SignalName.AMOUNT: 1.0}, "metadata": {SignalName.AMOUNT: mock_amount_meta(AmountRelationship.EXACT_MATCH, 1.0)}},
        violations=frozenset()
    )
    
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_AMBIGUOUS,
        selected_hypothesis=None,
        competitors=(h1, h2),
        rationale="Within ambiguity margin."
    )
    
    builder = ExplanationBuilder()
    explanation = builder.build(decision)
    
    assert explanation.action == DecisionAction.REVIEW_AMBIGUOUS
    assert "Competitor was only 0.010 points behind." in explanation.ambiguity_context
    assert explanation.evidence_summary.amount_projection.similarity == 1.0

def test_explain_limiting_factors():
    h = EvaluatedHypothesis(
        hypothesis=Hypothesis(frozenset(), frozenset()),
        score=0.5,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence={
            "signals": {
                SignalName.TEMPORAL: 0.3,
                SignalName.REFERENCE: None
            },
            # No AMOUNT metadata provided to simulate missing amount evidence
        },
        violations=frozenset(["TAX_IDENTITY_CONFLICT"])
    )
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_WEAK,
        selected_hypothesis=h,
        competitors=(),
        rationale="Weak score."
    )
    
    builder = ExplanationBuilder()
    explanation = builder.build(decision)
    
    limits = explanation.limiting_factors
    assert any("Semantic violation: TAX_IDENTITY_CONFLICT" in l for l in limits)
    assert any("Amount evidence unavailable" in l for l in limits)
    assert any("Dates are far apart" in l for l in limits)
    assert any("No reference provided" in l for l in limits)
