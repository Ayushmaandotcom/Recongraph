from typing import Protocol, Iterable, Sequence
from dataclasses import dataclass, field
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker

@dataclass(frozen=True)
class EvidenceContribution:
    """Represents a single plugin's interpretation of a hypothesis."""
    provider_name: str
    score: float | None # 0.0 to 1.0, or None if abstaining/N/A
    violations: frozenset[str] = frozenset()
    metadata: dict = field(default_factory=dict)

class EvidenceProvider(Protocol):
    """
    An extensible plugin that defines how to block (for candidate generation)
    and evaluate (for hypothesis scoring) a specific dimension of evidence.
    """
    def get_name(self) -> str:
        ...
        
    def get_blockers(self) -> Iterable[Blocker]:
        ...
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        ...
