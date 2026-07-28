from enum import Enum
from dataclasses import dataclass, field
from .dimensions import ExtractionQuality

class AttenuationAction(str, Enum):
    NONE = "none"
    ATTENUATE = "attenuate"
    ZERO = "zero"
    ABSTAIN = "abstain"

@dataclass(frozen=True)
class AttenuationRule:
    signal_name: str           # The signal produced by a provider (e.g., "amount")
    field_name: str            # The field in the record to check (e.g., "amount", "record_date")
    extraction_quality: ExtractionQuality
    action: AttenuationAction
    weight: float = 1.0        # Multiplier when action is ATTENUATE
    violation: str | None = None  # Violation code to emit

@dataclass(frozen=True)
class AttenuationPolicy:
    rules: tuple[AttenuationRule, ...]

    def apply(self, signal_name: str, lowest_quality: ExtractionQuality | None) -> tuple[float, list[str]]:
        """
        Returns a weight multiplier (1.0 default) and a list of violation strings.
        If `lowest_quality` is None, applies no attenuation.
        """
        weight = 1.0
        violations: list[str] = []
        
        if lowest_quality is None:
            return weight, violations
            
        for rule in self.rules:
            if rule.signal_name == signal_name and rule.extraction_quality == lowest_quality:
                if rule.action == AttenuationAction.ZERO:
                    weight = 0.0
                elif rule.action == AttenuationAction.ATTENUATE:
                    weight *= rule.weight
                
                if rule.violation:
                    violations.append(rule.violation)
                    
        return weight, violations

    @classmethod
    def default(cls) -> "AttenuationPolicy":
        """
        Default Stage 9B policy mapping ExtractionQuality to signal attenuation.
        """
        return cls(
            rules=(
                # Financial Evidence (Amount)
                AttenuationRule(
                    signal_name="amount",
                    field_name="amount",
                    extraction_quality=ExtractionQuality.DEGRADED,
                    action=AttenuationAction.ATTENUATE,
                    weight=0.85,
                    violation="OCR_AMOUNT_DEGRADED"
                ),
                AttenuationRule(
                    signal_name="amount",
                    field_name="amount",
                    extraction_quality=ExtractionQuality.LOW,
                    action=AttenuationAction.ATTENUATE,
                    weight=0.60,
                    violation="OCR_AMOUNT_LOW_CONFIDENCE"
                ),
                AttenuationRule(
                    signal_name="amount",
                    field_name="amount",
                    extraction_quality=ExtractionQuality.FAILED,
                    action=AttenuationAction.ZERO,
                    violation="OCR_AMOUNT_UNREADABLE"
                ),
                
                # Temporal Evidence (Date)
                AttenuationRule(
                    signal_name="temporal",
                    field_name="record_date",
                    extraction_quality=ExtractionQuality.LOW,
                    action=AttenuationAction.NONE,
                    violation="OCR_DATE_LOW_CONFIDENCE"
                ),
                AttenuationRule(
                    signal_name="temporal",
                    field_name="record_date",
                    extraction_quality=ExtractionQuality.FAILED,
                    action=AttenuationAction.NONE,
                    violation="OCR_DATE_UNREADABLE"
                ),
            )
        )
