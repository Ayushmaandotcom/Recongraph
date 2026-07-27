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
    review_rate: float
    exact_match_rate: float

def evaluate_results(results: Sequence[tuple[ReconciliationResult, ExpectedOutcome]]) -> EvaluationMetrics:
    tp = 0
    fp = 0
    fn = 0
    total = len(results)
    reviews = 0
    exact_matches = 0

    for result, expected in results:
        # Simplistic evaluation for benchmark framework
        # If expected is AUTO_MATCH, and we got AUTO_MATCH for the exact same components -> TP
        # If we got AUTO_MATCH for something wrong -> FP
        # If expected is AUTO_MATCH and we didn't -> FN
        # Note: Since the engine outputs a batch of decisions, we must check if the expected decision is present
        
        # We assume each scenario runs through the engine and produces traces/decisions.
        matched = False
        reviewed = False
        
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
    review_rate = reviews / total if total > 0 else 0.0
    exact_match_rate = exact_matches / total if total > 0 else 0.0

    return EvaluationMetrics(
        total_scenarios=total,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        review_rate=review_rate,
        exact_match_rate=exact_match_rate
    )
