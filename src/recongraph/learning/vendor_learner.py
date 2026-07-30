from dataclasses import dataclass
from typing import Iterable, Any

from recongraph.learning.protocols import LearningAgent, LearnedInsight
from recongraph.graph.review import ReviewPacket, ReviewOutcome
from recongraph.graph.decision import DecisionAction

@dataclass(frozen=True)
class AliasInsight(LearnedInsight):
    """Insight indicating two vendor names likely represent the same economic entity."""
    primary_name: str
    alias_name: str

class VendorAliasLearner(LearningAgent):
    """
    Observes manual approvals of ambiguous matches.
    If the human approves a match despite a low vendor identity score,
    it emits an AliasInsight so the alias can be added to the vendor graph.
    """
    
    def __init__(self, vendor_score_threshold: float = 0.5):
        self.vendor_score_threshold = vendor_score_threshold
        self._insights: list[AliasInsight] = []
        
    def get_name(self) -> str:
        return "vendor_alias_learner"
        
    def observe(self, packet: ReviewPacket, outcome: ReviewOutcome) -> None:
        if outcome.final_action != DecisionAction.AUTO_MATCH.value and outcome.final_action != "APPROVED":
            return
            
        if not packet.competitors:
            return
            
        # Check the primary competitor
        primary_hypothesis = packet.competitors[0]
        
        # Look for the vendor evidence
        for assertion in primary_hypothesis.supporting_evidence.assertions:
            if "vendor" in assertion.proposition.claim.claim_id.value:
                # If the human approved it but the model thought the vendor score was low,
                # they might be aliases.
                if assertion.magnitude < self.vendor_score_threshold:
                    p_name = " ".join(str(getattr(p, "vendor_name")) for p in packet.purchases if getattr(p, "vendor_name", None))
                    g_name = " ".join(str(getattr(g, "vendor_name")) for g in packet.gsts if getattr(g, "vendor_name", None))
                    if p_name and g_name and p_name != g_name:
                        self._insights.append(
                            AliasInsight(
                                agent_id=self.get_name(),
                                primary_name=g_name,
                                alias_name=p_name,
                                metadata={
                                    "original_vendor_score": assertion.magnitude,
                                    "reviewer_id": outcome.reviewer_id,
                                    "packet_id": packet.packet_id
                                }
                            )
                        )
                        
    def get_insights(self) -> Iterable[LearnedInsight]:
        insights = list(self._insights)
        self._insights.clear()
        return insights
