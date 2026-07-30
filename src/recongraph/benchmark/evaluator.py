from typing import Sequence
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, brier_score_loss # type: ignore

from recongraph.graph.decision import DecisionAction
from recongraph.engine import ReconciliationResult
from recongraph.synthetic.models import ExpectedOutcome
from recongraph.benchmark.models import QualityStatistics

def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error (ECE)."""
    bins = np.linspace(0., 1., n_bins + 1)
    binids = np.digitize(y_prob, bins) - 1
    
    ece = 0.0
    total = len(y_prob)
    
    for i in range(n_bins):
        bin_mask = (binids == i)
        bin_total = np.sum(bin_mask)
        if bin_total > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_total / total) * np.abs(bin_acc - bin_conf)
            
    return float(ece)

def evaluate_results(results: Sequence[tuple[ReconciliationResult, ExpectedOutcome]]) -> QualityStatistics:
    """Computes advanced benchmarking metrics via scikit-learn."""
    y_true = []
    y_pred = []
    y_prob = []
    
    human_agreements = 0
    total = len(results)

    for result, expected in results:
        # Determine actual ground truth action
        is_true_match = (expected.expected_decision == DecisionAction.AUTO_MATCH)
        y_true.append(1 if is_true_match else 0)
        
        # Determine engine prediction and confidence
        has_auto_match = len(result.auto_matches) > 0
        y_pred.append(1 if has_auto_match else 0)
        
        # Confidence is max coverage of auto_matches, or 0.0
        confidence = 0.0
        if has_auto_match:
            confidence = max(d.selected_hypothesis.coverage if d.selected_hypothesis else 0.0 for d in result.auto_matches)
        elif len(result.review_packets) > 0:
            # We can use the top review competitor as probability if not match
            confidence = max((p.competitors[0].coverage if p.competitors else 0.0 for p in result.review_packets), default=0.0)
            
        y_prob.append(confidence)
        
        # Human agreement: Does engine's top action match expected action exactly?
        # If engine AUTO_MATCHES when expected is AUTO_MATCH
        # Or if engine REVIEWS when expected is NOT AUTO_MATCH
        if has_auto_match and is_true_match:
            human_agreements += 1
        elif not has_auto_match and not is_true_match:
            human_agreements += 1
            
    if not results:
        return QualityStatistics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    y_true_np = np.array(y_true)
    y_pred_np = np.array(y_pred)
    y_prob_np = np.array(y_prob)
    
    # scikit-learn metrics
    prec = float(precision_score(y_true_np, y_pred_np, zero_division=0.0))
    rec = float(recall_score(y_true_np, y_pred_np, zero_division=0.0))
    f1 = float(f1_score(y_true_np, y_pred_np, zero_division=0.0))
    brier = float(brier_score_loss(y_true_np, y_prob_np))
    ece = calculate_ece(y_true_np, y_prob_np)
    
    human_agreement_rate = human_agreements / total if total > 0 else 0.0
    
    return QualityStatistics(
        precision=prec,
        recall=rec,
        f1_score=f1,
        brier_score=brier,
        expected_calibration_error=ece,
        human_agreement_rate=human_agreement_rate
    )
