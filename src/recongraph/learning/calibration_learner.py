from dataclasses import dataclass
from typing import Iterable, Any

from recongraph.learning.protocols import LearningAgent, LearnedInsight
from recongraph.graph.review import ReviewPacket, ReviewOutcome
from recongraph.graph.decision import DecisionAction

@dataclass(frozen=True)
class CalibrationInsight(LearnedInsight):
    """Insight indicating empirical mismatch with the current calibration curve."""
    claim_id: str
    empirical_accuracy: float
    current_prediction: float
    sample_size: int

class CalibrationLearner(LearningAgent):
    """
    Observes manual approvals/rejections and computes running empirical accuracy 
    for specific assertions. If an assertion is systematically wrong, emits a CalibrationInsight.
    """
    
    def __init__(self, sample_threshold: int = 5):
        self.sample_threshold = sample_threshold
        # map (claim_id, bucket) -> [is_match: bool]
        self._history: dict[tuple[str, int], list[bool]] = {}
        
    def get_name(self) -> str:
        return "calibration_learner"
        
    def observe(self, packet: ReviewPacket, outcome: ReviewOutcome) -> None:
        if outcome.final_action not in ("APPROVED", "REJECTED"):
            return
            
        is_match = outcome.final_action == "APPROVED"
        
        if not packet.competitors:
            return
            
        primary_hypothesis = packet.competitors[0]
        
        for assertion in primary_hypothesis.supporting_evidence.assertions:
            claim_id = assertion.proposition.claim.claim_id.value
            # bucket magnitude into deciles for tracking
            bucket = int(assertion.magnitude * 10)
            
            key = (claim_id, bucket)
            if key not in self._history:
                self._history[key] = []
            self._history[key].append(is_match)
            
    def get_insights(self) -> Iterable[LearnedInsight]:
        insights = []
        for (claim_id, bucket), matches in list(self._history.items()):
            if len(matches) >= self.sample_threshold:
                empirical_accuracy = sum(matches) / len(matches)
                current_prediction = bucket / 10.0 + 0.05 # midpoint
                
                # If off by more than 0.2 (20%), emit insight
                if abs(empirical_accuracy - current_prediction) > 0.2:
                    insights.append(
                        CalibrationInsight(
                            agent_id=self.get_name(),
                            claim_id=claim_id,
                            empirical_accuracy=empirical_accuracy,
                            current_prediction=current_prediction,
                            sample_size=len(matches),
                            metadata={"bucket": bucket}
                        )
                    )
                # clear history after emitting
                del self._history[(claim_id, bucket)]
                
        return insights
