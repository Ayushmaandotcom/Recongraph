from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

SAME_TAX_IDENTITY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("tax.same_tax_identity"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

VALID_REGIME_ALIGNMENT_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("tax.valid_regime_alignment"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

GROSS_NET_CONSISTENCY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("tax.gross_net_consistency"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
