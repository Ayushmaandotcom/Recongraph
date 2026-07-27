import struct
import hashlib
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from .identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest, canonical_encode
from .scopes import Proposition
from .authority import AuthorityDescriptor
from .payloads import TypedPayloadEnvelope


class AssertionPolarity(str, Enum):
    SUPPORT = "support"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceAncestryRef:
    """
    Identity proven eligible as assertion ancestry.
    Must be an occurrence, not a semantic fact identity alone.
    """
    identity: KernelIdentityRef

    def __post_init__(self):
        allowed_domains = {
            "recongraph.observation_occurrence",
            "recongraph.derivation_occurrence"
        }
        if self.identity.domain.value not in allowed_domains:
            raise ValueError(f"Identity domain '{self.identity.domain.value}' is not eligible as evidence ancestry.")


def _canonicalize_magnitude(value: float) -> str:
    """
    Magnitude identity uses the exact IEEE-754 binary64 bit representation of the finite Python float, packed as hex.
    -0.0 is explicitly canonicalized to positive 0.0.
    """
    if not isinstance(value, float):
        raise TypeError("Magnitude must be a float.")
    import math
    if not math.isfinite(value):
        raise ValueError("Non-finite magnitudes are rejected.")
    
    # Python's struct.pack('>d', float) gives IEEE-754 binary64
    if value == 0.0:
        value = 0.0  # Coerce -0.0 to 0.0
    
    if value <= 0.0 or value > 1.0:
        raise ValueError("Magnitude must be in range (0.0, 1.0]")
        
    packed = struct.pack('>d', value)
    return f"binary64:{packed.hex()}"


@dataclass(frozen=True, slots=True, order=True)
class EvidenceAssertionIdentity:
    """
    Canonical content-addressed identity of an EvidenceAssertion.
    """
    digest: str


@dataclass(frozen=True, slots=True)
class EvidenceAssertion:
    """
    An atomic claim evaluated over evidence.
    Has exactly one proposition, one polarity, strictly positive finite magnitude,
    one descriptive authority basis, and exactly one valid semantic ancestry root.
    """
    proposition: Proposition
    polarity: AssertionPolarity
    magnitude: float
    authority: AuthorityDescriptor
    ancestry: EvidenceAncestryRef
    payload: Optional[TypedPayloadEnvelope] = None
    identity: EvidenceAssertionIdentity | None = None

    def __post_init__(self):
        # We compute identity and use object.__setattr__ because the dataclass is frozen.
        canon_mag = _canonicalize_magnitude(self.magnitude)
        
        payload_dict = {
            "schema": "recongraph.evidence_assertion.v1",
            "proposition": {
                "claim_id": self.proposition.claim.claim_id.value,
                "claim_semantic_version": self.proposition.claim.semantic_version.value,
                "subject": self.proposition.subject.to_dict()
            },
            "polarity": self.polarity.value,
            "magnitude": canon_mag,
            "authority": self.authority.basis.value,
            "ancestry": self.ancestry.identity.digest.value
        }
        
        if self.payload:
            payload_dict["payload"] = {
                "type_id": self.payload.type_id,
                "semantic_version": self.payload.semantic_version,
                "payload_fingerprint": hashlib.sha256(self.payload.payload.canonicalize()).hexdigest()
            }
            
        canonical_bytes = canonical_encode(payload_dict)
        domain_separated_bytes = b"recongraph:evidence_assertion:v1\x00" + canonical_bytes
        digest_hex = hashlib.sha256(domain_separated_bytes).hexdigest()
        
        computed_identity = EvidenceAssertionIdentity(f"sha256:{digest_hex}")
        
        # Prevent caller from providing an identity mismatch
        if self.identity is not None and self.identity != computed_identity:
            raise ValueError("Provided identity mismatch.")
            
        if self.identity is None:
            object.__setattr__(self, 'identity', computed_identity)


class EvidenceInterpretationState(str, Enum):
    INTERPRETED = "interpreted"
    MISSING_INPUT = "missing_input"
    INSUFFICIENT_INPUT = "insufficient_input"
    UNINTERPRETABLE_INPUT = "uninterpretable_input"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class EvidenceInterpretationResult:
    """
    Deterministic transport envelope describing one provider interpretation attempt.
    """
    state: EvidenceInterpretationState
    assertions: tuple[EvidenceAssertion, ...]

    def __post_init__(self):
        if self.state != EvidenceInterpretationState.INTERPRETED:
            if len(self.assertions) > 0:
                raise ValueError(f"Interpretation result in state '{self.state.value}' must have empty assertions.")
                
        # Validate uniqueness and order
        if len(self.assertions) > 0:
            canonically_ordered = tuple(sorted(self.assertions, key=lambda a: a.identity.digest))
            if self.assertions != canonically_ordered:
                # To fail EA064 reversed assertion emission order canonicalized: 
                # "reversed input order yields equal result"
                # wait, if they have to pass as identical if passed out of order, we should sort them in post_init.
                # Since the dataclass is frozen, we do this:
                object.__setattr__(self, 'assertions', canonically_ordered)

            # Check for duplicates
            digests = [a.identity.digest for a in self.assertions] # after sorting
            if len(set(digests)) != len(digests):
                raise ValueError("Duplicate assertion identities inside one interpretation result are forbidden.")
