from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

SAME_ECONOMIC_ENTITY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("vendor.same_economic_entity"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

SAME_LEGAL_ENTITY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("vendor.same_legal_entity"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

SHARED_TAX_REGISTRATION_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("vendor.shared_tax_registration"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

ALIAS_MATCH_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("vendor.alias_match"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
