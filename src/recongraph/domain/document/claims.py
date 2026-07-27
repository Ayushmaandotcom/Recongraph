from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

HAS_VALID_SIGNATURE_REGION_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("document.has_valid_signature_region"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,  # Typically applies to one document at a time, but evaluated as support for the record pair
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

TOTALS_BLOCK_CONSISTENCY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("document.totals_block_consistency"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

HEADER_MATCH_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("document.header_match"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
