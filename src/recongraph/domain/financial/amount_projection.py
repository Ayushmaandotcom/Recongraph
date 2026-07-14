from dataclasses import dataclass, field
from decimal import Decimal
from recongraph.domain.financial.pipeline import (
    AmountInterpretation,
    EqualityRelation,
    CurrencyRelation,
    SignRelation,
    CompatibilityFlag
)

@dataclass(frozen=True)
class ProjectedAmountSimilarity:
    """Explicit mapping from semantic truth to legacy math scalar."""
    similarity: float
    projection_version: str = "v2"
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def project_amount_similarity(interpretation: AmountInterpretation) -> ProjectedAmountSimilarity:
    """
    Project the semantic AmountInterpretation into a 0.0-1.0 scalar.
    This serves strictly as a compatibility bridge for the legacy RelationshipScorer.
    """
    similarity = 0.0
    warnings = []
    
    if interpretation.currency_relation == CurrencyRelation.DIFFERENT:
        # Hard conflict for explicit different currencies
        similarity = 0.0
        warnings.append("CURRENCY_MISMATCH")
    else:
        # Let's assess magnitude similarity
        if interpretation.equality == EqualityRelation.EQUAL:
            similarity = 1.0
        elif CompatibilityFlag.ROUNDING_COMPATIBLE in interpretation.compatibility_flags:
            similarity = 0.99
        elif CompatibilityFlag.FEE_COMPATIBLE in interpretation.compatibility_flags:
            similarity = 0.95
        elif (CompatibilityFlag.PARTIAL_SETTLEMENT_MAGNITUDE_COMPATIBLE in interpretation.compatibility_flags or
              CompatibilityFlag.OVERPAYMENT_MAGNITUDE_COMPATIBLE in interpretation.compatibility_flags):
            relative_diff = float(interpretation.relative_difference)
            tolerance = 0.05
            if relative_diff > tolerance:
                similarity = 0.0
            else:
                similarity = max(0.0, 1.0 - (relative_diff / tolerance))
        else:
            similarity = 0.0
            
    if interpretation.currency_relation in (CurrencyRelation.LEFT_MISSING, CurrencyRelation.RIGHT_MISSING, CurrencyRelation.BOTH_MISSING):
        warnings.append("MISSING_CURRENCY")
        
    return ProjectedAmountSimilarity(
        similarity=similarity,
        assumptions=("Projected using AmountSimilarityProjection.V2",),
        warnings=tuple(warnings)
    )
