from dataclasses import dataclass, field
from decimal import Decimal
from recongraph.domain.financial.pipeline import AmountInterpretation, AmountRelationship

@dataclass(frozen=True)
class ProjectedAmountSimilarity:
    """Explicit mapping from semantic truth to legacy math scalar."""
    similarity: float
    projection_version: str = "v1"
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def project_amount_similarity(interpretation: AmountInterpretation) -> ProjectedAmountSimilarity:
    """
    Project the semantic AmountInterpretation into a 0.0-1.0 scalar.
    This serves strictly as a compatibility bridge for the legacy RelationshipScorer.
    """
    similarity = 0.0
    warnings = []
    
    if interpretation.relationship == AmountRelationship.EXACT_MATCH:
        similarity = 1.0
    elif interpretation.relationship == AmountRelationship.ROUNDING_MATCH:
        similarity = 0.99
    elif interpretation.relationship == AmountRelationship.FEE_DETECTED:
        similarity = 0.95
    elif interpretation.relationship in (AmountRelationship.PARTIAL_SETTLEMENT, AmountRelationship.OVERPAYMENT):
        # Scale-aware decay based on relative difference
        relative_diff = float(interpretation.relative_difference)
        
        # In V1, tolerance was typically 0.05.
        # It decayed from 1.0 to 0.0 within tolerance, and was 0.0 outside.
        # We will use 0.05 as the strict bound.
        tolerance = 0.05
        if relative_diff > tolerance:
            similarity = 0.0
        else:
            similarity = max(0.0, 1.0 - (relative_diff / tolerance))
            
    elif interpretation.relationship == AmountRelationship.CURRENCY_MISMATCH:
        similarity = 0.0
        warnings.append("CURRENCY_MISMATCH")
    else:
        similarity = 0.0
        
    return ProjectedAmountSimilarity(
        similarity=similarity,
        assumptions=("Projected using AmountSimilarityProjection.V1",),
        warnings=tuple(warnings)
    )
