import re
from dataclasses import dataclass
from enum import Enum
from .scopes import ScopeKind


class ClaimSymmetry(str, Enum):
    """
    Positive semantic vocabulary for claim directionality.
    """
    SYMMETRIC = "symmetric"
    DIRECTIONAL = "directional"


@dataclass(frozen=True)
class ClaimId:
    """
    Typed, immutable, validated claim identifier.
    Must follow the grammar <namespace>.<name> where segments are [a-z][a-z0-9_]*
    """
    value: str

    _PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")

    def __post_init__(self):
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid ClaimId format: '{self.value}'")

    def __str__(self) -> str:
        return self.value

    def to_dict(self) -> str:
        return self.value


@dataclass(frozen=True, order=True)
class ClaimSemanticVersion:
    """
    Strict semantic version for claims.
    Rejects booleans and values less than 1.
    """
    value: int

    def __post_init__(self):
        # bool is a subclass of int in Python, so isinstance(True, int) is True.
        # We must explicitly reject bool.
        if isinstance(self.value, bool):
            raise TypeError("Semantic version cannot be a boolean.")
        if not isinstance(self.value, int):
            raise TypeError("Semantic version must be an integer.")
        if self.value < 1:
            raise ValueError("Semantic version must be >= 1.")

    def __str__(self) -> str:
        return str(self.value)

    def to_dict(self) -> int:
        return self.value


@dataclass(frozen=True)
class ClaimDescriptor:
    """
    Immutable semantic descriptor for a claim family and version.
    Defines the structural invariants of the claim (symmetry, valid scopes)
    without knowing about providers or evaluation logic.
    """
    claim_id: ClaimId
    semantic_version: ClaimSemanticVersion
    symmetry: ClaimSymmetry
    allowed_scope_kinds: frozenset['ScopeKind']

    def __init__(
        self,
        claim_id: ClaimId | str,
        semantic_version: ClaimSemanticVersion | int,
        symmetry: ClaimSymmetry,
        allowed_scope_kinds: frozenset['ScopeKind'] | set['ScopeKind'] | list['ScopeKind']
    ):
        if isinstance(claim_id, str):
            claim_id = ClaimId(claim_id)
        if isinstance(semantic_version, int) and not isinstance(semantic_version, bool):
            semantic_version = ClaimSemanticVersion(semantic_version)

        frozen_scopes = frozenset(allowed_scope_kinds)
        if not frozen_scopes:
            raise ValueError("CD-001 Violation: Claim must have at least one allowed scope kind.")

        object.__setattr__(self, 'claim_id', claim_id)
        object.__setattr__(self, 'semantic_version', semantic_version)
        object.__setattr__(self, 'symmetry', symmetry)
        object.__setattr__(self, 'allowed_scope_kinds', frozen_scopes)

    def validates_scope_kind(self, scope_kind: 'ScopeKind') -> bool:
        """
        Validates whether this claim allows the given scope kind.
        """
        return scope_kind in self.allowed_scope_kinds

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id.to_dict(),
            "semantic_version": self.semantic_version.to_dict(),
            "symmetry": self.symmetry.value,
            "allowed_scope_kinds": sorted([sk.value for sk in self.allowed_scope_kinds])
        }

class ImmutableCatalog(type):
    def __setattr__(cls, name, value):
        raise AttributeError(f"Cannot modify immutable catalog {cls.__name__}")

class CoreClaims(metaclass=ImmutableCatalog):
    """
    Immutable catalog of core claim semantics for ReconGraph v0.1.
    """
    SAME_LEGAL_ENTITY = ClaimDescriptor(
        claim_id="identity.same_legal_entity",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

    SAME_GST_REGISTRATION = ClaimDescriptor(
        claim_id="identity.same_gst_registration",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

    LEXICAL_NAME_SIMILARITY = ClaimDescriptor(
        claim_id="identity.lexical_name_similarity",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )

    LEGAL_FORM_COMPATIBILITY = ClaimDescriptor(
        claim_id="identity.legal_form_compatibility",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )

    AMOUNT_CONSERVATION = ClaimDescriptor(
        claim_id="financial.amount_conservation",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

    CURRENCY_COMPATIBILITY = ClaimDescriptor(
        claim_id="financial.currency_compatibility",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

    STRUCTURAL_COMPATIBILITY = ClaimDescriptor(
        claim_id="reference.structural_compatibility",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR, ScopeKind.GROUP_PAIR}
    )

    REFERENCE_IS_PARSEABLE = ClaimDescriptor(
        claim_id="document.reference_is_parseable",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD}
    )
