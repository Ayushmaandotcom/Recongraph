import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True, order=True)
class SourceSystemId:
    """
    Identifies a logical source system namespace (e.g., 'sap.production', 'gst.portal').
    It does not identify specific files or rows.
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(
                f"Invalid SourceSystemId format: '{self.value}'. "
                "Must be lowercased, namespaced (e.g., 'sap.production'), and contain only a-z, 0-9, -, _"
            )


@dataclass(frozen=True, slots=True, order=True)
class SourceArtifactId:
    """
    SourceArtifactId is an opaque identifier within a SourceSystemId namespace. 
    It does not independently claim global uniqueness, immutability, or content identity.
    """
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("SourceArtifactId cannot be empty.")
        if self.value != self.value.strip():
            raise ValueError("SourceArtifactId cannot contain surrounding whitespace.")
        # Reject control characters (0x00-0x1F and 0x7F)
        if any(ord(c) < 32 or ord(c) == 127 for c in self.value):
            raise ValueError("SourceArtifactId cannot contain control characters.")


@dataclass(frozen=True, slots=True, order=True)
class SourceLocator:
    """
    Identifies the semantic or structural location inside an artifact (e.g., 'field:vendor_name').
    The kernel preserves the supplied canonical coordinate but does not parse it.
    """
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("SourceLocator cannot be empty.")
        if self.value != self.value.strip():
            raise ValueError("SourceLocator cannot contain surrounding whitespace.")


@dataclass(frozen=True, slots=True, order=True)
class SourceVersionRef:
    """
    Literal opaque source version identity. Acts as a state qualifier over the logical artifact.
    """
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("SourceVersionRef cannot be empty.")


@dataclass(frozen=True, slots=True, order=True)
class StructuredSourceLineage:
    """
    Minimal immutable lineage coordinates answering where a fact came from.
    Preserves exact temporal source occurrence identity.
    """
    source_system: SourceSystemId
    source_artifact: SourceArtifactId
    source_locator: SourceLocator
    source_version: SourceVersionRef | None = None

    def canonicalize_for_serialization(self) -> bytes:
        """
        Explicit canonical representation for identity hashing.
        Uses Canonical JSON bytes with sorted keys, explicit schema identifier, 
        UTF-8, and compact separators.
        """
        import json
        payload = {
            "schema": "recongraph.source_lineage.v1",
            "source_system": self.source_system.value,
            "source_artifact": self.source_artifact.value,
            "source_locator": self.source_locator.value,
            "source_version": self.source_version.value if self.source_version else None
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")
