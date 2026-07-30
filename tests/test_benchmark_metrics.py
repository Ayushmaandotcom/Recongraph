import pytest
import numpy as np
from recongraph.benchmark.evaluator import calculate_ece, evaluate_results
from recongraph.benchmark.models import QualityStatistics
from recongraph.synthetic.models import ExpectedOutcome
from recongraph.graph.decision import DecisionAction
from recongraph.engine import ReconciliationResult
from recongraph.graph.review import ReviewPacket, ReviewOutcome

def test_brier_score_and_f1():
    # Construct mock data
    class MockHypothesis:
        def __init__(self, coverage):
            self.coverage = coverage

    class MockDecision:
        def __init__(self, action, coverage):
            self.action = action
            self.selected_hypothesis = MockHypothesis(coverage)

    class MockPacket:
        def __init__(self, coverage):
            self.decision = MockDecision(DecisionAction.REVIEW_AMBIGUOUS, coverage)
            self.competitors = [MockHypothesis(coverage)]

    # 1. True match, engine confident auto match (TP)
    r1 = ReconciliationResult(
        auto_matches=[MockDecision(DecisionAction.AUTO_MATCH, 0.9)],
        review_packets=[],
        traces=[],
        engine_version="0.9.0"
    )
    e1 = ExpectedOutcome(expected_decision=DecisionAction.AUTO_MATCH, expected_component_urns=frozenset(), expected_hypothesis_edges=frozenset())
    
    # 2. True match, engine review (FN)
    r2 = ReconciliationResult(
        auto_matches=[],
        review_packets=[MockPacket(0.6)],
        traces=[],
        engine_version="0.9.0"
    )
    e2 = ExpectedOutcome(expected_decision=DecisionAction.AUTO_MATCH, expected_component_urns=frozenset(), expected_hypothesis_edges=frozenset())
    
    # 3. Not match, engine confident auto match (FP)
    r3 = ReconciliationResult(
        auto_matches=[MockDecision(DecisionAction.AUTO_MATCH, 0.8)],
        review_packets=[],
        traces=[],
        engine_version="0.9.0"
    )
    e3 = ExpectedOutcome(expected_decision=DecisionAction.REVIEW_AMBIGUOUS, expected_component_urns=frozenset(), expected_hypothesis_edges=frozenset())

    # 4. Not match, engine review (TN)
    r4 = ReconciliationResult(
        auto_matches=[],
        review_packets=[MockPacket(0.7)],
        traces=[],
        engine_version="0.9.0"
    )
    e4 = ExpectedOutcome(expected_decision=DecisionAction.REVIEW_AMBIGUOUS, expected_component_urns=frozenset(), expected_hypothesis_edges=frozenset())

    results = [(r1, e1), (r2, e2), (r3, e3), (r4, e4)]
    metrics = evaluate_results(results)

    # TP = 1 (r1), FP = 1 (r3), FN = 1 (r2), TN = 1 (r4)
    # Precision = 1 / (1 + 1) = 0.5
    # Recall = 1 / (1 + 1) = 0.5
    # F1 = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1_score == 0.5
    
    # Human Agreement: r1 matches (both AUTO), r4 matches (both not AUTO). 2/4 = 0.5
    assert metrics.human_agreement_rate == 0.5

    # Brier Score:
    # y_true = [1, 1, 0, 0]
    # y_prob = [0.9, 0.6, 0.8, 0.7]
    # diff = [-0.1, 0.4, -0.8, -0.7]
    # diff^2 = [0.01, 0.16, 0.64, 0.49]
    # Mean = (0.01 + 0.16 + 0.64 + 0.49) / 4 = 1.3 / 4 = 0.325
    assert pytest.approx(metrics.brier_score) == 0.325


def test_calculate_ece():
    y_true = np.array([1, 1, 0, 0, 1])
    y_prob = np.array([0.9, 0.85, 0.1, 0.2, 0.6])
    
    # Bins: [0, 0.5) [0.5, 1.0]
    # y_prob in bin 0: [0.1, 0.2] (Indices 2, 3)
    #   y_true in bin 0: [0, 0] => acc = 0.0, conf = 0.15
    # y_prob in bin 1: [0.9, 0.85, 0.6] (Indices 0, 1, 4)
    #   y_true in bin 1: [1, 1, 1] => acc = 1.0, conf = 2.35/3 = 0.7833...
    
    # ECE = (2/5) * |0.0 - 0.15| + (3/5) * |1.0 - 0.7833|
    # = 0.4 * 0.15 + 0.6 * 0.21666...
    # = 0.06 + 0.13 = 0.19
    ece = calculate_ece(y_true, y_prob, n_bins=2)
    assert pytest.approx(ece) == 0.19
