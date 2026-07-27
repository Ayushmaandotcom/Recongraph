from recongraph.matching.scoring import ScoringEvidence
import pytest
from recongraph.graph.hypotheses import EvaluatedHypothesis, Hypothesis, EligibilityStatus
from recongraph.graph.decision import DecisionEngine, DecisionPolicy, DecisionAction

def create_mock_hypothesis(score: float, eligibility: EligibilityStatus) -> EvaluatedHypothesis:
    # Minimal mock for testing decision logic independent of graph structure
    h = Hypothesis(frozenset(), frozenset())
    return EvaluatedHypothesis(
        hypothesis=h,
        score=score,
        coverage=1.0,
        eligibility=eligibility,
        supporting_evidence=ScoringEvidence(),
        violations=frozenset()
    )

def test_decision_case_1():
    # Case 1: One eligible hypothesis, no competitors -> AUTO_MATCH
    h1 = create_mock_hypothesis(0.98, EligibilityStatus.ELIGIBLE)
    
    engine = DecisionEngine(DecisionPolicy(auto_match_threshold=0.95))
    decision = engine.decide([h1])
    
    assert decision.action == DecisionAction.AUTO_MATCH
    assert decision.selected_hypothesis == h1
    assert len(decision.competitors) == 0

def test_decision_case_2():
    # Case 2: Two equally strong eligible hypotheses -> REVIEW_AMBIGUOUS
    h1 = create_mock_hypothesis(0.98, EligibilityStatus.ELIGIBLE)
    h2 = create_mock_hypothesis(0.97, EligibilityStatus.ELIGIBLE)
    
    engine = DecisionEngine(DecisionPolicy(auto_match_threshold=0.95, ambiguity_margin=0.05))
    decision = engine.decide([h1, h2])
    
    assert decision.action == DecisionAction.REVIEW_AMBIGUOUS
    assert decision.selected_hypothesis is None
    assert len(decision.competitors) == 2

def test_decision_case_3():
    # Case 3: Best hypothesis is eligible but weak -> REVIEW_WEAK
    h1 = create_mock_hypothesis(0.90, EligibilityStatus.ELIGIBLE)
    
    engine = DecisionEngine(DecisionPolicy(auto_match_threshold=0.95))
    decision = engine.decide([h1])
    
    assert decision.action == DecisionAction.REVIEW_WEAK
    assert decision.selected_hypothesis == h1
    assert len(decision.competitors) == 0

def test_decision_case_4():
    # Case 4: Every hypothesis violates constraint (INELIGIBLE) -> NO_MATCH
    h1 = create_mock_hypothesis(0.98, EligibilityStatus.INELIGIBLE)
    h2 = create_mock_hypothesis(0.95, EligibilityStatus.INELIGIBLE)
    
    engine = DecisionEngine()
    decision = engine.decide([h1, h2])
    
    assert decision.action == DecisionAction.NO_MATCH
    assert decision.selected_hypothesis is None
    assert len(decision.competitors) == 2

def test_decision_case_5():
    # Case 5: No hypotheses produced -> NO_MATCH
    engine = DecisionEngine()
    decision = engine.decide([])
    
    assert decision.action == DecisionAction.NO_MATCH
    assert decision.selected_hypothesis is None
    assert len(decision.competitors) == 0
