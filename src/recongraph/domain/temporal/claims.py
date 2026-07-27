from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.scopes import ScopeKind

SAME_FISCAL_PERIOD_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("temporal.same_fiscal_period"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.SYMMETRIC,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

VALID_LATE_FILING_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("temporal.valid_late_filing"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL, # Late filing implies directionality between purchase and GST
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
