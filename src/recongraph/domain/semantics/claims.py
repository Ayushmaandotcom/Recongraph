from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

# Latent Semantic Business Assertions
SAME_BUSINESS_PURPOSE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("identity.same_business_purpose"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

SAME_PRODUCT_CATEGORY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("identity.same_product_category"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

SAME_SERVICE_CATEGORY_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("identity.same_service_category"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
