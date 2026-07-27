from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from datetime import datetime, timezone
import hashlib
from recongraph.contrib.kernel.identity import canonical_encode
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recongraph.graph.decision import ReconciliationDecision
    from recongraph.graph.hypotheses import EvaluatedHypothesis

class TraceStage(StrEnum):
    CANDIDATE_GENERATION = "candidate_generation"
    GRAPH_BUILDING = "graph_building"
    COMPONENT_EXTRACTION = "component_extraction"
    HYPOTHESIS_SEARCH = "hypothesis_search"
    HYPOTHESIS_EVALUATION = "hypothesis_evaluation"
    DECISION_EVALUATION = "decision_evaluation"
    EXPLANATION_GENERATION = "explanation_generation"

@dataclass(frozen=True)
class TraceEvent:
    """An explicit, chronological record of a single action in the reconciliation pipeline."""
    timestamp: datetime
    stage: TraceStage
    payload: Any  # E.g., CandidateEdge, CandidateGraph, Hypothesis, EvaluatedHypothesis, ReconciliationDecision

def canonicalize_score(score: float | None) -> int | None:
    if score is None:
        return None
    # Reject NaN and Infinity
    if score != score or score == float('inf') or score == float('-inf'):
        raise ValueError("Scores must be finite real numbers.")
    return int(round(score * 10000))

def _map_evaluated_hypothesis(h: 'EvaluatedHypothesis') -> dict[str, Any]:
    proposed_edges_list = [sorted(list(edge)) for edge in h.hypothesis.proposed_edges]
    proposed_edges_list.sort()
    
    base_score = None
    if h.supporting_evidence.relationship is not None:
        rel = h.supporting_evidence.relationship
        if hasattr(rel, "base_score"):
            base_score = rel.base_score
    
    return {
        "hypothesis_identity": proposed_edges_list,
        "eligibility": h.eligibility.value,
        "semantic_findings": sorted(list(h.violations)),
        "base_score": canonicalize_score(base_score),
        "coverage": canonicalize_score(h.coverage),
        "relationship_score": canonicalize_score(h.score),
        "provider_projection_identities": sorted(list(h.supporting_evidence.metadata.keys()))
    }

@dataclass(frozen=True)
class DecisionTrace:
    """The immutable historical record of an entire reconciliation execution."""
    trace_id: str
    engine_version: str
    config_hash: str
    events: tuple[TraceEvent, ...]
    
    def to_json(self) -> str:
        import json
        from recongraph.serialization import ReconEncoder
        return json.dumps(self, cls=ReconEncoder)

    @classmethod
    def compute_identity(cls, engine_version: str, config_hash: str, component_nodes: frozenset[str], decision: 'ReconciliationDecision | None' = None) -> str:
        """
        Computes a deterministic, canonical identity for a reconciliation trace.
        Follows the K6 domain-separated hashing philosophy.
        """
        payload: dict[str, Any] = {
            "schema": "recongraph.decision_trace_identity.v1",
            "engine_version": engine_version,
            "config_hash": config_hash,
            "component_nodes": sorted(list(component_nodes))
        }
        
        if decision is not None:
            payload["decision"] = decision.action.value
            if decision.selected_hypothesis:
                payload["selected_hypothesis"] = _map_evaluated_hypothesis(decision.selected_hypothesis)
            else:
                payload["selected_hypothesis"] = None

        canonical_bytes = canonical_encode(payload)
        domain_separated_bytes = b"recongraph:decision_trace:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        return f"sha256:{digest_hex}"
    
    def get_events_for_stage(self, stage: TraceStage) -> tuple[TraceEvent, ...]:
        return tuple(e for e in self.events if e.stage == stage)
        
    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "engine_version": self.engine_version,
            "config_hash": self.config_hash,
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "stage": e.stage.value,
                    "payload": repr(e.payload) # Placeholder for robust serialization
                }
                for e in self.events
            ]
        }


