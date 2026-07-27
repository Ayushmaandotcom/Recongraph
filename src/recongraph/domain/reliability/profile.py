import hashlib
from dataclasses import dataclass, field
from typing import Optional, Any
from recongraph.contrib.kernel.identity import canonical_encode

from .dimensions import ExtractionQuality, ParserQuality, Completeness, VerificationState, ConfidenceProvenance
from .reasons import ReliabilityReason

@dataclass(frozen=True, slots=True)
class ReliabilityProfile:
    """
    Immutable, deterministic, structured description of observation quality.
    
    Attached at the observation boundary — never at the assertion or
    fusion boundary. This is NOT semantic evidence.
    """
    extraction_quality: ExtractionQuality
    parser_quality: ParserQuality
    completeness: Completeness
    verification_state: VerificationState
    confidence_provenance: ConfidenceProvenance
    reasons: tuple[ReliabilityReason, ...]  # Canonically sorted, deduplicated
    source_id: str  # e.g., "tesseract.v5", "sap.api.v2", "manual.clerk_007"
    schema_version: int = 1
    
    # Audit metadata does NOT participate in identity hashing.
    # Used to carry raw floats (e.g. OCR confidence=0.87) or BoundingBox highlights.
    audit_metadata: dict[str, Any] = field(default_factory=dict, hash=False, compare=False)

    def __post_init__(self):
        # Enforce canonical sorting for reasons
        object.__setattr__(self, 'reasons', tuple(sorted(set(self.reasons), key=lambda r: r.value)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "extraction_quality": self.extraction_quality.value,
            "parser_quality": self.parser_quality.value,
            "completeness": self.completeness.value,
            "verification_state": self.verification_state.value,
            "confidence_provenance": self.confidence_provenance.value,
            "reasons": [r.value for r in self.reasons],
            "source_id": self.source_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], audit_metadata: Optional[dict[str, Any]] = None) -> "ReliabilityProfile":
        return cls(
            extraction_quality=ExtractionQuality(data["extraction_quality"]),
            parser_quality=ParserQuality(data["parser_quality"]),
            completeness=Completeness(data["completeness"]),
            verification_state=VerificationState(data["verification_state"]),
            confidence_provenance=ConfidenceProvenance(data["confidence_provenance"]),
            reasons=tuple(ReliabilityReason(r) for r in data["reasons"]),
            source_id=data["source_id"],
            schema_version=data.get("schema_version", 1),
            audit_metadata=audit_metadata or {}
        )

    def canonical_digest(self) -> str:
        """SHA-256 digest of the canonical JSON representation."""
        payload = self.to_dict()
        canonical_bytes = canonical_encode(payload)
        domain_separated = b"recongraph:reliability_profile:v1\x00" + canonical_bytes
        return f"sha256:{hashlib.sha256(domain_separated).hexdigest()}"


@dataclass(frozen=True, slots=True, order=True)
class FieldReliability:
    """Binds a ReliabilityProfile to a specific field on a record."""
    field_name: str
    profile: ReliabilityProfile


@dataclass(frozen=True, slots=True)
class ReliabilityEnvelope:
    """
    Per-record reliability metadata, keyed by field name.
    Replaces OcrConfidenceReport as a universal contract.
    """
    profiles: tuple[FieldReliability, ...]

    def __post_init__(self):
        object.__setattr__(self, 'profiles', tuple(sorted(self.profiles, key=lambda f: f.field_name)))

    def get(self, field_name: str) -> Optional[ReliabilityProfile]:
        for fr in self.profiles:
            if fr.field_name == field_name:
                return fr.profile
        return None
