from dataclasses import dataclass
from typing import Sequence
from recongraph.graph.decision import DecisionAction
from recongraph.engine import ReconciliationResult
from recongraph.synthetic.models import ExpectedOutcome

@dataclass(frozen=True)
class EvaluationMetrics:
    total_scenarios: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    review_rate: float
    review_reduction_rate: float
    exact_match_rate: float
    ece_score: float

def evaluate_results(results: Sequence[tuple[ReconciliationResult, ExpectedOutcome]]) -> EvaluationMetrics:
    tp = 0
    fp = 0
    fn = 0
    total = len(results)
    reviews = 0
    exact_matches = 0

    for result, expected in results:
        if expected.expected_decision == DecisionAction.AUTO_MATCH:
            if len(result.auto_matches) > 0:
                tp += 1
                exact_matches += 1
            elif len(result.review_packets) > 0:
                fn += 1
                reviews += 1
            else:
                fn += 1
        else:
            if len(result.auto_matches) > 0:
                fp += 1
            elif len(result.review_packets) > 0:
                reviews += 1
                exact_matches += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    review_rate = reviews / total if total > 0 else 0.0
    review_reduction_rate = 1.0 - review_rate
    exact_match_rate = exact_matches / total if total > 0 else 0.0
    ece_score = 0.0 # Placeholder for Expected Calibration Error

    return EvaluationMetrics(
        total_scenarios=total,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        review_rate=review_rate,
        review_reduction_rate=review_reduction_rate,
        exact_match_rate=exact_match_rate,
        ece_score=ece_score
    )
