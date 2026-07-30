from dataclasses import dataclass
from typing import Mapping, Sequence, Any
from recongraph.graph.decision import DecisionAction

@dataclass(frozen=True, kw_only=True)
class ExplanationNode:
    """
    A foundational node in the explanation tree mapping to a structural fact.
    """
    node_id: str
    identity_hash: str
    dependencies: tuple[str, ...]
    human_readable: str | None = None

@dataclass(frozen=True, kw_only=True)
class ContributionExplanation(ExplanationNode):
    """Explains a single domain's contribution."""
    provider_name: str
    score: float | None
    interpretation_repr: str | None
    violations: frozenset[str]

@dataclass(frozen=True, kw_only=True)
class PropagationExplanation(ExplanationNode):
    """Explains the result of semantic propagation."""
    status: str
    derived_from: tuple[str, ...]

@dataclass(frozen=True, kw_only=True)
class FusionExplanation(ExplanationNode):
    """Explains the semantic fusion state."""
    independent_support: int
    derived_support: int
    contradictions: int
    missing_domains: tuple[str, ...]

@dataclass(frozen=True, kw_only=True)
class DecisionExplanation(ExplanationNode):
    """Explains the final deterministic decision."""
    action: DecisionAction
    rationale: str
    coverage: float

@dataclass(frozen=True, kw_only=True)
class TraceExplanation(ExplanationNode):
    """Roots the explanation to a verifiable execution trace."""
    engine_version: str
    config_hash: str

@dataclass(frozen=True, kw_only=True)
class ExplanationArtifact:
    """
    A strictly deterministic, fully serialized explanation spanning
    multiple levels of detail for a given reconciliation decision.
    """
    trace_id: str
    
    # Layer 1
    executive_summary: dict[str, Any]
    
    # Layer 2
    domain_summaries: dict[str, dict[str, Any]]
    
    # Layer 3
    technical_details: dict[str, Any]
    
    # Layer 4
    audit_nodes: dict[str, ExplanationNode]
