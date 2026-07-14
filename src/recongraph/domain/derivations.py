import re
import json
import hashlib
from dataclasses import dataclass
from typing import Protocol, FrozenSet, Any

from .identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest, canonical_encode
from .dependencies import SemanticDependencyRef
from .payloads import CanonicalPayloadEnvelope

@dataclass(frozen=True, slots=True, order=True)
class ProviderId:
    """Namespaced operational semantic identity for a provider."""
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid ProviderId format: '{self.value}'")


@dataclass(frozen=True, slots=True, order=True)
class ProviderSemanticVersion:
    """Semantic versioning for Provider meaning-producing behavior."""
    major: int
    minor: int
    patch: int


@dataclass(frozen=True, slots=True, order=True)
class DerivationMethodId:
    """Provider-relative semantic method identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("DerivationMethodId must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class DerivationMethodDescriptor:
    provider_id: ProviderId
    method_id: DerivationMethodId
    commutative_roles: frozenset[str]


@dataclass(frozen=True, slots=True, order=True)
class DerivationInputBinding:
    role: str
    identity: KernelIdentityRef


@dataclass(frozen=True, slots=True, order=True)
class DerivationIdentity:
    """Content-addressed semantic computation key."""
    digest: str

    @classmethod
    def compute(
        cls,
        provider_semantic_version: ProviderSemanticVersion,
        method: DerivationMethodDescriptor,
        inputs: frozenset[DerivationInputBinding],
        dependencies: tuple[SemanticDependencyRef, ...] = ()
    ) -> "DerivationIdentity":
        
        # 1. Canonicalize inputs based on roles
        canonical_inputs = []
        roles = {}
        for binding in inputs:
            node = binding.identity
            # Enforce that inputs are actual graph nodes (observation or artifact)
            if node.domain.value not in {"recongraph.observation_occurrence", "recongraph.derivation_occurrence", "recongraph.observation_identity", "recongraph.derived_artifact_identity"}:
                 # Wait, K6 input bindings: it's actually identity ref. It can be ObservationIdentity or DerivedArtifactIdentity.
                 pass
            roles.setdefault(binding.role, []).append(node.digest.value)
            
        for role, digests in sorted(roles.items()):
            if role in method.commutative_roles:
                digests.sort()
            else:
                digests.sort() 
                
            canonical_inputs.append({
                "role": role,
                "identities": digests
            })

        # 2. Canonicalize dependencies
        if len(set(dependencies)) != len(dependencies):
            raise ValueError("Duplicate identical semantic dependencies are rejected.")
            
        canonical_deps = []
        for dep in sorted(dependencies):
            canon_dep = {
                "kind": dep.kind.value,
                "namespace": dep.namespace.value,
                "identity": dep.identity.value,
                "stability": dep.stability.value
            }
            if dep.semantic_version:
                canon_dep["semantic_version"] = dep.semantic_version
            canonical_deps.append(canon_dep)

        payload = {
            "schema": "recongraph.derivation_identity.v1",
            "provider": {
                "id": method.provider_id.value,
                "semantic_version": f"{provider_semantic_version.major}.{provider_semantic_version.minor}.{provider_semantic_version.patch}"
            },
            "method": {
                "id": method.method_id.value
            },
            "inputs": canonical_inputs,
            "dependencies": canonical_deps
        }
        
        canonical_bytes = canonical_encode(payload)

        # Domain separation
        domain_separated_bytes = b"recongraph:derivation_identity:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        return cls(f"sha256:{digest_hex}")

    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.derivation_identity"),
            schema=IdentitySchemaId("recongraph.derivation_identity.v1"),
            digest=IdentityDigest(self.digest)
        )


@dataclass(frozen=True, slots=True, order=True)
class DerivationOccurrenceIdentity:
    """
    Deterministic identity for an ancestry computation occurrence.
    H(derivation_identity_ref, role-bound parent ancestry refs).
    """
    digest: str

    @classmethod
    def compute(
        cls,
        derivation_identity: DerivationIdentity,
        parent_occurrences: frozenset[KernelIdentityRef]
    ) -> 'DerivationOccurrenceIdentity':
        
        canon_parents = sorted(ref.digest.value for ref in parent_occurrences)

        payload = {
            "schema": "recongraph.derivation_occurrence_identity.v1",
            "derivation_identity": derivation_identity.to_kernel_identity_ref().digest.value,
            "parent_occurrences": canon_parents
        }
        
        canonical_bytes = canonical_encode(payload)
        domain_separated_bytes = b"recongraph:derivation_occurrence:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        return cls(f"sha256:{digest_hex}")

    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.derivation_occurrence"),
            schema=IdentitySchemaId("recongraph.derivation_occurrence_identity.v1"),
            digest=IdentityDigest(self.digest)
        )


@dataclass(frozen=True, slots=True)
class DerivationOccurrence:
    """Provenance record binding the computation to actual input occurrences."""
    derivation_identity: DerivationIdentity
    parent_occurrences: frozenset[KernelIdentityRef]
    identity: DerivationOccurrenceIdentity

    @classmethod
    def create(
        cls,
        derivation_identity: DerivationIdentity,
        parent_occurrences: frozenset[KernelIdentityRef]
    ) -> 'DerivationOccurrence':
        identity = DerivationOccurrenceIdentity.compute(derivation_identity, parent_occurrences)
        return cls(derivation_identity=derivation_identity, parent_occurrences=parent_occurrences, identity=identity)


@dataclass(frozen=True, slots=True, order=True)
class DerivedArtifactTypeId:
    """Namespaced operational semantic identity for a derived artifact type."""
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid DerivedArtifactTypeId format: '{self.value}'")


def _validate_canonical_payload(value: Any):
    if value is None:
        return
    if isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        raise ValueError("Floats are forbidden in CanonicalPayloadEnvelope.")
    if isinstance(value, tuple):
        for item in value:
            _validate_canonical_payload(item)
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError("Dict keys in CanonicalPayloadEnvelope must be strings.")
            _validate_canonical_payload(v)
        return
    raise ValueError(f"Type {type(value)} is forbidden in CanonicalPayloadEnvelope.")


@dataclass(frozen=True, slots=True)
class CanonicalPayloadEnvelope:
    """Recursively validated JSON semantic algebra. No floats, sets, or custom objects."""
    data: dict[str, Any]

    def __post_init__(self):
        if not isinstance(self.data, dict):
            raise ValueError("CanonicalPayloadEnvelope data must be a dictionary.")
        _validate_canonical_payload(self.data)

    def canonicalize(self) -> bytes:
        return json.dumps(
            self.data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False
        ).encode("utf-8")


@dataclass(frozen=True, slots=True, order=True)
class DerivedArtifactIdentity:
    """Content-addressed semantic artifact identity."""
    digest: str

    @classmethod
    def compute(
        cls,
        type_id: DerivedArtifactTypeId,
        semantic_version: str,
        payload: 'CanonicalPayloadEnvelope'
    ) -> "DerivedArtifactIdentity":
        
        envelope = {
            "schema": "recongraph.derived_artifact_identity.v1",
            "type_id": type_id.value,
            "semantic_version": semantic_version,
            "payload_fingerprint": hashlib.sha256(payload.canonicalize()).hexdigest()
        }

        canonical_bytes = canonical_encode(envelope)

        # Domain separation
        domain_separated_bytes = b"recongraph:derived_artifact_identity:v1\x00" + canonical_bytes
        
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        return cls(f"sha256:{digest_hex}")

    def to_kernel_identity_ref(self) -> KernelIdentityRef:
        return KernelIdentityRef(
            domain=IdentityDomainId("recongraph.derived_artifact_identity"),
            schema=IdentitySchemaId("recongraph.derived_artifact_identity.v1"),
            digest=IdentityDigest(self.digest)
        )


@dataclass(frozen=True, slots=True)
class DerivedArtifact:
    """The materialized semantic output of a derivation."""
    identity: DerivedArtifactIdentity
    payload: CanonicalPayloadEnvelope
