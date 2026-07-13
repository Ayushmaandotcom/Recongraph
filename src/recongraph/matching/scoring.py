from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite


class SignalName(StrEnum):
    """Names of primitive compatibility signals."""

    ENTITY = "entity"
    REFERENCE = "reference"
    AMOUNT = "amount"
    TEMPORAL = "temporal"
    TAX_IDENTITY = "tax_identity"


@dataclass(frozen=True)
class RelationshipPolicy:
    """Define how a financial relationship interprets primitive signals."""

    weights: Mapping[SignalName, float]
    contradiction_penalties: Mapping[SignalName, float] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.weights:
            raise ValueError(
                "Relationship policy requires at least one signal weight."
            )

        for weight in self.weights.values():
            if not isfinite(weight) or weight <= 0.0:
                raise ValueError(
                    "Signal weights must be finite and greater than zero."
                )

        for penalty in self.contradiction_penalties.values():
            if not isfinite(penalty) or not 0.0 <= penalty <= 1.0:
                raise ValueError(
                    "Contradiction penalties must be between "
                    "0.0 and 1.0."
                )

        for signal_name in self.contradiction_penalties:
            if signal_name not in self.weights:
                raise ValueError(
                    "A contradiction signal must also have "
                    "a configured weight."
                )


@dataclass(frozen=True)
class RelationshipScore:
    """Represent an explainable relationship scoring result."""

    score: float | None
    base_score: float | None
    coverage: float
    contradiction_penalty: float
    active_contradictions: tuple[SignalName, ...]


def calculate_relationship_score(
    signals: Mapping[SignalName, float | None],
    policy: RelationshipPolicy,
) -> RelationshipScore:
    """Aggregate primitive evidence under a relationship policy."""
    if set(signals) != set(policy.weights):
        raise ValueError(
            "Signal names must exactly match policy signals."
        )

    for score in signals.values():
        if score is None:
            continue

        if not isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError(
                "Signal scores must be finite and between "
                "0.0 and 1.0."
            )

    total_weight = sum(policy.weights.values())

    available_weight = 0.0
    weighted_numerator = 0.0

    for signal_name, score in signals.items():
        if score is None:
            continue

        weight = policy.weights[signal_name]

        available_weight += weight
        weighted_numerator += weight * score

    coverage = available_weight / total_weight

    active_contradictions = tuple(
        signal_name
        for signal_name in policy.contradiction_penalties
        if signals[signal_name] == 0.0
    )

    contradiction_penalty = 1.0

    for signal_name in active_contradictions:
        contradiction_penalty *= (
            policy.contradiction_penalties[signal_name]
        )

    if available_weight == 0.0:
        return RelationshipScore(
            score=None,
            base_score=None,
            coverage=coverage,
            contradiction_penalty=contradiction_penalty,
            active_contradictions=active_contradictions,
        )

    base_score = weighted_numerator / available_weight
    final_score = base_score * contradiction_penalty

    return RelationshipScore(
        score=final_score,
        base_score=base_score,
        coverage=coverage,
        contradiction_penalty=contradiction_penalty,
        active_contradictions=active_contradictions,
    )
