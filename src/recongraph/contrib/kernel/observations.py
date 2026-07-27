import re
import json
import hashlib
from enum import Enum
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from .scopes import SubjectRef


class ObservationState(str, Enum):
    PRESENT = "present"
    MISSING = "missing"
    INVALID = "invalid"


class InterpretationState(str, Enum):
    INTERPRETED = "interpreted"
    UNINTERPRETABLE = "uninterpretable"


@dataclass(frozen=True, order=True)
class FieldPath:
    """
    Semantic value object for field paths.
    Validates against grammar: <segment>(.<segment>)* where segment is [a-z][a-z0-9_]*
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid FieldPath format: '{self.value}'")

    def __str__(self) -> str:
        return self.value

    def to_dict(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class ObservationSlot:
    """
    Identifies the semantic source slot where a fact belongs, independent of its value occurrence.
    """
    subject: SubjectRef
    field: FieldPath

    def to_dict(self) -> dict:
        return {
            "subject": self.subject.to_dict(),
            "field": self.field.to_dict()
        }


@dataclass(frozen=True)
class ObservationFingerprint:
    """
    Opaque deterministic fingerprint representing the typed value state occurrence.
    This replaces temporal revision numbers.
    """
    digest: str

    def to_dict(self) -> str:
        return self.digest


@dataclass(frozen=True)
class ObservationIdentity:
    """
    Deterministic identity for an observation occurrence.
    Composed of the slot (where) and the fingerprint (what typed state).
    """
    slot: ObservationSlot
    fingerprint: ObservationFingerprint

    def to_dict(self) -> dict:
        return {
            "slot": self.slot.to_dict(),
            "fingerprint": self.fingerprint.to_dict()
        }

    def to_kernel_identity_ref(self) -> 'KernelIdentityRef':
        from .identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.observation_identity"),
            schema=IdentitySchemaId("recongraph.observation_identity.v1"),
            # K3 fingerprint digest did not have the sha256: prefix, we add it for KernelIdentityRef 
            digest=IdentityDigest(f"sha256:{self.fingerprint.digest}")
        )


def _canonicalize_value(value: Any) -> tuple[str, Any]:
    """
    Produces a canonical (type_tag, raw_value) for observation values.
    """
    if value is None:
        return "none", None
    elif isinstance(value, bool):
        return "bool", value
    elif isinstance(value, int):
        return "int", value
    elif isinstance(value, float):
        import math
        if not math.isfinite(value):
            raise ValueError("Non-finite floats are not supported for observations.")
        # float repr is relatively stable in modern python, but forcing a standard string representation prevents JSON weirdness
        return "float", repr(value)
    elif isinstance(value, Decimal):
        # Preserves precision scale (e.g. 1.0 vs 1.00)
        return "decimal", str(value)
    elif isinstance(value, str):
        return "str", value
    elif isinstance(value, datetime):
        return "datetime", value.isoformat()
    elif isinstance(value, date):
        return "date", value.isoformat()
    else:
        raise TypeError(f"Unsupported observation value type: {type(value)}")


@dataclass(frozen=True)
class Observation:
    """
    Minimal immutable envelope for an observed fact occurrence.
    Use Observation.create() to guarantee identity consistency.
    """
    identity: ObservationIdentity
    state: ObservationState
    value: Any

    def __post_init__(self):
        # Validate state/value contract
        if self.state == ObservationState.MISSING:
            if self.value is not None:
                raise ValueError("MISSING observation must have a None value.")
        else:
            if self.value is None:
                raise ValueError(f"{self.state.value.upper()} observation cannot have a None value.")

        # Re-derive fingerprint to guarantee identity consistency
        expected_fingerprint = self._compute_fingerprint(self.state, self.value)
        if self.identity.fingerprint != expected_fingerprint:
            raise ValueError("Observation identity fingerprint is inconsistent with state and value.")

    @staticmethod
    def _compute_fingerprint(state: ObservationState, value: Any) -> ObservationFingerprint:
        type_tag, canonical_val = _canonicalize_value(value)
        envelope = {
            "schema_version": 1,
            "state": state.value,
            "type": type_tag,
            "value": canonical_val
        }
        envelope_bytes = json.dumps(envelope, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(envelope_bytes).hexdigest()
        return ObservationFingerprint(digest)

    @classmethod
    def create(
        cls,
        slot: ObservationSlot,
        state: ObservationState,
        value: Any
    ) -> 'Observation':
        fingerprint = cls._compute_fingerprint(state, value)
        identity = ObservationIdentity(slot=slot, fingerprint=fingerprint)
        return cls(identity=identity, state=state, value=value)

    def to_dict(self) -> dict:
        """
        Dumps the full sensitive observation containing raw source values.
        """
        type_tag, canonical_val = _canonicalize_value(self.value)
        return {
            "identity": self.identity.to_dict(),
            "state": self.state.value,
            "value": {
                "type": type_tag,
                "value": canonical_val
            }
        }


from .lineage import StructuredSourceLineage
from .identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest

@dataclass(frozen=True, slots=True, order=True)
class ObservationOccurrenceIdentity:
    """
    Deterministic identity for an observation occurrence.
    H(observation_identity_ref, source_lineage_canonical_identity).
    """
    digest: str

    @classmethod
    def compute(
        cls,
        observation_identity: ObservationIdentity,
        lineage: StructuredSourceLineage
    ) -> 'ObservationOccurrenceIdentity':
        
        payload = {
            "schema": "recongraph.observation_occurrence_identity.v1",
            "observation_identity": observation_identity.to_kernel_identity_ref().digest.value,
            "lineage": hashlib.sha256(lineage.canonicalize_for_serialization()).hexdigest()
        }
        
        canonical_bytes = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")

        domain_separated_bytes = b"recongraph:observation-occurrence:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        return cls(f"sha256:{digest_hex}")

    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.observation_occurrence"),
            schema=IdentitySchemaId("recongraph.observation_occurrence_identity.v1"),
            digest=IdentityDigest(self.digest)
        )


@dataclass(frozen=True, slots=True, order=True)
class ObservationOccurrence:
    """
    Binds an observation fact (what content state exists) to a source occurrence (where it came from).
    """
    observation_identity: ObservationIdentity
    lineage: StructuredSourceLineage
    identity: ObservationOccurrenceIdentity

    @classmethod
    def create(
        cls,
        observation_identity: ObservationIdentity,
        lineage: StructuredSourceLineage
    ) -> 'ObservationOccurrence':
        identity = ObservationOccurrenceIdentity.compute(observation_identity, lineage)
        return cls(observation_identity=observation_identity, lineage=lineage, identity=identity)
