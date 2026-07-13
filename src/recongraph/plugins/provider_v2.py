from typing import Protocol, TypeVar, Generic, Iterable, Sequence, Any
from dataclasses import dataclass, field
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker

T_Extraction = TypeVar('T_Extraction')
T_Interpretation = TypeVar('T_Interpretation')

@dataclass(frozen=True)
class EvidenceContributionV2(Generic[T_Interpretation]):
    """
    Represents a single plugin's interpretation of a hypothesis.
    Unlike V1, this explicitly carries the domain-specific interpretation payload
    to allow for advanced Evidence Fusion algorithms in the Decision Engine.
    """
    provider_name: str
    score: float | None # 0.0 to 1.0, or None if abstaining/N/A
    violations: frozenset[str] = frozenset()
    metadata: dict = field(default_factory=dict)
    interpretation: T_Interpretation | None = None

class EvidencePipeline(Protocol[T_Extraction, T_Interpretation]):
    """
    A strictly typed pipeline enforcing the extraction, interpretation,
    and contribution boundaries for a specific evidence domain.
    """
    
    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> T_Extraction:
        """
        Extract raw observations from the records.
        Must not make comparisons or decisions.
        """
        ...
        
    def interpret(self, extraction: T_Extraction) -> T_Interpretation:
        """
        Compare and enrich the extracted observations.
        Produces a semantic interpretation of the evidence.
        """
        ...
        
    def contribute(self, interpretation: T_Interpretation) -> EvidenceContributionV2[T_Interpretation]:
        """
        Project the interpretation into a normalized score and violations
        for the engine to fuse.
        """
        ...

class EvidenceProviderV2(Protocol):
    """
    The outer boundary for an Evidence Provider.
    Manages candidate blocking logic and provides the strict Evidence Pipeline for evaluation.
    """
    def get_name(self) -> str:
        ...
        
    def get_blockers(self) -> Iterable[Blocker]:
        ...
        
    def get_pipeline(self) -> EvidencePipeline[Any, Any]:
        ...
