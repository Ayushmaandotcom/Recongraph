"""
K6 Claim Descriptors for the OCR Confidence Engine (Stage 8G).

These claims allow the evidence engine to express:
 - That a specific field was extracted with low OCR confidence (downgrade support).
 - That a field was completely unreadable (conflict on the underlying evidence).
"""

from recongraph.domain.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.domain.scopes import ScopeKind

# Emitted as SUPPORT when all key financial fields are >= HIGH confidence.
OCR_HIGH_CONFIDENCE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("ocr.field_high_confidence"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

# Emitted as SUPPORT (attenuated magnitude) when a field is MEDIUM confidence.
OCR_MEDIUM_CONFIDENCE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("ocr.field_medium_confidence"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

# Emitted as CONFLICT when a critical field (amount, date) is LOW confidence.
OCR_LOW_CONFIDENCE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("ocr.field_low_confidence"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)

# Emitted as CONFLICT when a field is completely UNREADABLE.
OCR_UNREADABLE_CLAIM = ClaimDescriptor(
    claim_id=ClaimId("ocr.field_unreadable"),
    semantic_version=ClaimSemanticVersion(1),
    symmetry=ClaimSymmetry.DIRECTIONAL,
    allowed_scope_kinds=frozenset({ScopeKind.RECORD_PAIR})
)
