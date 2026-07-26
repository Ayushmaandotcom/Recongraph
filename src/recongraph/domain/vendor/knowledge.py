from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Set, Optional

class AliasRelation(Enum):
    KNOWN_ALIAS = auto()
    HISTORICAL_RENAME = auto()
    PARENT_SUBSIDIARY = auto()
    UNAFFILIATED = auto() # Explicitly known to be unrelated despite lexical similarity
    NO_KNOWLEDGE = auto()

@dataclass(frozen=True)
class KnowledgeBaseEntry:
    canonical_core: str
    relation: AliasRelation

class OrganizationalKnowledgeBase:
    """
    A deterministic, immutable knowledge base for resolving organizational identity.
    Maps a canonical vendor core string to known related entities.
    """
    def __init__(self, mappings: Optional[Dict[str, Set[KnowledgeBaseEntry]]] = None):
        # We store mappings symmetrically for O(1) lookups.
        # If A is a parent of B, then A -> (B, PARENT_SUBSIDIARY) and B -> (A, PARENT_SUBSIDIARY)
        self._mappings: Dict[str, Set[KnowledgeBaseEntry]] = mappings or {}

    @classmethod
    def empty(cls) -> "OrganizationalKnowledgeBase":
        return cls({})

    def get_relation(self, core_a: str, core_b: str) -> AliasRelation:
        """
        Determines the explicit known relationship between two normalized core strings.
        Returns NO_KNOWLEDGE if no relationship is defined.
        """
        if core_a == core_b:
            return AliasRelation.KNOWN_ALIAS
            
        entries = self._mappings.get(core_a, set())
        for entry in entries:
            if entry.canonical_core == core_b:
                return entry.relation
                
        return AliasRelation.NO_KNOWLEDGE

    def compute_digest(self) -> str:
        """
        Computes a deterministic hash of the knowledge base contents for trace identity.
        """
        import hashlib
        import json
        
        # Build a sorted dictionary of lists of dicts
        serializable = {}
        for key in sorted(self._mappings.keys()):
            sorted_entries = sorted(
                self._mappings[key], 
                key=lambda e: (e.canonical_core, e.relation.name)
            )
            serializable[key] = [
                {"canonical_core": e.canonical_core, "relation": e.relation.name}
                for e in sorted_entries
            ]
            
        canonical_bytes = json.dumps(
            serializable,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")
        
        return hashlib.sha256(canonical_bytes).hexdigest()
