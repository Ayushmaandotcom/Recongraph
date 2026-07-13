import re
from dataclasses import dataclass
from typing import Optional
import json

from .observations import ObservationIdentity


@dataclass(frozen=True, order=True)
class SourceSystemId:
    """
    Identifies the semantic source system (e.g. 'erp.sap', 'document.invoice').
    Must be a namespaced grammar: <namespace>.<system>
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid SourceSystemId format: '{self.value}'. Must be namespaced like 'erp.sap'.")

    def to_dict(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class SourceNodeRef:
    """
    Opaque extensible coordinates for a source artifact (record, document, page, block, etc).
    """
    kind: str
    ref: str

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "ref": self.ref
        }


@dataclass(frozen=True, order=True)
class SourceVersionRef:
    """
    Literal opaque source version identity.
    """
    value: str

    def to_dict(self) -> str:
        return self.value


@dataclass(frozen=True)
class StructuredSourceLineage:
    """
    Minimal immutable lineage coordinates answering where a fact came from.
    """
    source_system: SourceSystemId
    source_node: SourceNodeRef
    source_version: Optional[SourceVersionRef] = None

    def to_dict(self) -> dict:
        return {
            "source_system": self.source_system.to_dict(),
            "source_node": self.source_node.to_dict(),
            "source_version": self.source_version.to_dict() if self.source_version else None
        }


@dataclass(frozen=True)
class ObservationProvenance:
    """
    Relational wrapper attaching lineage to a specific observation content state.
    """
    observation_identity: ObservationIdentity
    lineage: StructuredSourceLineage

    def to_dict(self) -> dict:
        return {
            "observation_identity": self.observation_identity.to_dict(),
            "lineage": self.lineage.to_dict()
        }
