import re
import json
import hashlib
from enum import Enum
from dataclasses import dataclass, field
from typing import FrozenSet, List

from .observations import ObservationIdentity


@dataclass(frozen=True, order=True)
class ProviderId:
    """
    Identifies a semantic producer (e.g. 'vendor.identity').
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid ProviderId format: '{self.value}'. Must be namespaced like 'vendor.identity'.")

    def to_dict(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class ProviderSemanticVersion:
    """
    Semantic version of a provider's interpretation procedure.
    Distinct from ClaimSemanticVersion.
    """
    value: int

    def __post_init__(self):
        if not isinstance(self.value, int) or self.value < 1:
            raise ValueError("ProviderSemanticVersion must be a positive integer.")

    def to_dict(self) -> int:
        return self.value


@dataclass(frozen=True, order=True)
class DerivationMethodId:
    """
    Provider-relative identifier for a semantic transformation method.
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid DerivationMethodId format: '{self.value}'. Must be like 'normalize_name'.")

    def to_dict(self) -> str:
        return self.value


class DerivationInputMode(str, Enum):
    ORDERED = "ordered"
    UNORDERED = "unordered"


@dataclass(frozen=True)
class DerivationMethodDescriptor:
    """
    Describes the identity and input semantics of a semantic derivation method.
    """
    provider_id: ProviderId
    method_id: DerivationMethodId
    input_mode: DerivationInputMode

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id.to_dict(),
            "method_id": self.method_id.to_dict(),
            "input_mode": self.input_mode.value
        }


@dataclass(frozen=True)
class DerivationInputBinding:
    """
    Binds an observation identity to a specific semantic role in a derivation.
    """
    role: str
    observation_identity: ObservationIdentity

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "observation_identity": self.observation_identity.to_dict()
        }


@dataclass(frozen=True)
class DerivationInputSet:
    """
    A collection of semantic input bindings for a derivation.
    """
    bindings: FrozenSet[DerivationInputBinding]
    
    def __post_init__(self):
        if not self.bindings:
            raise ValueError("DerivationInputSet must contain at least one input binding.")

    def canonicalize_for_serialization(self, input_mode: DerivationInputMode) -> List[dict]:
        """
        Canonicalizes bindings deterministically.
        If ordered, sorts by role (since roles enforce order). 
        If unordered, sorts by observation identity fingerprint to preserve canonical structure.
        """
        serialized = [b.to_dict() for b in self.bindings]
        if input_mode == DerivationInputMode.ORDERED:
            # Ordered mode relies on role strings dictating position (e.g. '0', '1' or 'left', 'right')
            # Lexicographical sort by role achieves deterministic order.
            serialized.sort(key=lambda x: x["role"])
        else:
            # Unordered mode: order by the actual observation content fingerprint
            serialized.sort(key=lambda x: (x["role"], x["observation_identity"]["fingerprint"]))
        return serialized


@dataclass(frozen=True)
class DerivationIdentity:
    """
    Deterministic fingerprint of a semantic derivation transformation.
    """
    digest: str

    def to_dict(self) -> str:
        return self.digest


@dataclass(frozen=True)
class DerivationMetadata:
    """
    Immutable derivation envelope identifying how semantic material was produced.
    """
    identity: DerivationIdentity
    provider_semantic_version: ProviderSemanticVersion
    method: DerivationMethodDescriptor
    inputs: DerivationInputSet

    def __post_init__(self):
        expected_fingerprint = self._compute_fingerprint(
            self.provider_semantic_version,
            self.method,
            self.inputs
        )
        if self.identity.digest != expected_fingerprint.digest:
            raise ValueError("Derivation identity fingerprint is inconsistent with derivation properties.")

    @staticmethod
    def _compute_fingerprint(
        version: ProviderSemanticVersion,
        method: DerivationMethodDescriptor,
        inputs: DerivationInputSet
    ) -> DerivationIdentity:
        envelope = {
            "schema_version": 1,
            "provider_semantic_version": version.to_dict(),
            "method": method.to_dict(),
            "inputs": inputs.canonicalize_for_serialization(method.input_mode)
        }
        envelope_bytes = json.dumps(envelope, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(envelope_bytes).hexdigest()
        return DerivationIdentity(digest)

    @classmethod
    def create(
        cls,
        provider_semantic_version: ProviderSemanticVersion,
        method: DerivationMethodDescriptor,
        inputs: DerivationInputSet
    ) -> 'DerivationMetadata':
        identity = cls._compute_fingerprint(provider_semantic_version, method, inputs)
        return cls(
            identity=identity,
            provider_semantic_version=provider_semantic_version,
            method=method,
            inputs=inputs
        )

    def to_dict(self) -> dict:
        return {
            "identity": self.identity.to_dict(),
            "provider_semantic_version": self.provider_semantic_version.to_dict(),
            "method": self.method.to_dict(),
            "inputs": self.inputs.canonicalize_for_serialization(self.method.input_mode)
        }

    def shared_observation_identities(self, other: 'DerivationMetadata') -> FrozenSet[ObservationIdentity]:
        """
        Pure structural helper for Stage 8J ancestry detection.
        Returns the intersection of observation identities consumed by both derivations.
        """
        my_obs = frozenset(b.observation_identity for b in self.inputs.bindings)
        other_obs = frozenset(b.observation_identity for b in other.inputs.bindings)
        return my_obs.intersection(other_obs)
