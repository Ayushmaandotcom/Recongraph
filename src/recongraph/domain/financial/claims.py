from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

SAME_AMOUNT_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("financial.same_amount"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

WITHIN_FEE_TOLERANCE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("financial.within_fee_tolerance"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

CURRENCY_CONSISTENCY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("financial.currency_consistency"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
