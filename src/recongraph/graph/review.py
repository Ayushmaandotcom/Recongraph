from dataclasses import dataclass
from typing import Any
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction, ReconciliationDecision
from recongraph.graph.explainability import DecisionExplanation
from recongraph.graph.candidate import CandidateGraph
from recongraph.graph.hypotheses import EvaluatedHypothesis

@dataclass(frozen=True)
class ReviewOutcome:
    """The mutable workflow state owned by the human/AI reviewer."""
    reviewer_id: str
    final_action: str
    comments: str

@dataclass(frozen=True)
class ReviewPacket:
    """An immutable, curated workspace required for a human/AI to resolve a complex decision."""
    packet_id: str
    action: DecisionAction
    purchases: tuple[PurchaseRecord, ...]
    gsts: tuple[GSTRecord, ...]
    explanation: DecisionExplanation
    competitors: tuple[EvaluatedHypothesis, ...]
    checklist: tuple[str, ...]

class ReviewPacketBuilder:
    """Constructs ReviewPackets exclusively for non-automated decisions."""
    
    def __init__(self):
        self._counter = 0
        
    def _generate_checklist(self, explanation: DecisionExplanation) -> tuple[str, ...]:
        checklist = []
        limits = "".join(explanation.limiting_factors).lower()
        
        if "tax_identity_conflict" in limits:
            checklist.append("Verify GST tax filing manually")
        if "amounts differ" in limits or "severe_amount_conflict" in limits:
            checklist.append("Verify exact invoice amounts and potential split payments")
        if "dates are far apart" in limits:
            checklist.append("Verify transaction date against posting date")
        if explanation.action == DecisionAction.REVIEW_AMBIGUOUS:
            checklist.append("Disambiguate competing hypotheses manually")
            
        if not checklist:
            checklist.append("General manual review")
            
        return tuple(checklist)
        
    def build(
        self, 
        decision: ReconciliationDecision, 
        explanation: DecisionExplanation, 
        graph: CandidateGraph
    ) -> ReviewPacket | None:
        
        if decision.action == DecisionAction.AUTO_MATCH:
            return None
            
        self._counter += 1
        packet_id = f"RP-{self._counter:05d}"
        
        purchases = []
        gsts = []
        
        target_hypothesis = decision.selected_hypothesis
        if not target_hypothesis and decision.competitors:
            target_hypothesis = decision.competitors[0]
            
        if target_hypothesis:
            for urn in target_hypothesis.hypothesis.matched_nodes:
                if urn.startswith("urn:recongraph:purchase:"):
                    purchases.append(graph.nodes[urn])
                elif urn.startswith("urn:recongraph:gst:"):
                    gsts.append(graph.nodes[urn])
                    
        checklist = self._generate_checklist(explanation)
        
        curated_competitors = decision.competitors[:3]
        
        return ReviewPacket(
            packet_id=packet_id,
            action=decision.action,
            purchases=tuple(purchases),
            gsts=tuple(gsts),
            explanation=explanation,
            competitors=curated_competitors,
            checklist=checklist
        )
