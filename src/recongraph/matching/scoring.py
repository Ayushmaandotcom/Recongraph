from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite


class SignalName:
    """Names of primitive compatibility signals."""

    ENTITY = "entity"
    REFERENCE = "reference"
    AMOUNT = "amount"
    TEMPORAL = "temporal"
    TAX_IDENTITY = "tax_identity"
    SEMANTICS = "semantics"


from recongraph.domain.reliability import AttenuationPolicy

@dataclass(frozen=True)
class RelationshipPolicy:
    """Define how a financial relationship interprets primitive signals."""

    weights: Mapping[str, float]
    attenuation_policy: AttenuationPolicy = field(
        default_factory=AttenuationPolicy.default
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


@dataclass(frozen=True)
class RelationshipScore:
    """Represent an explainable relationship scoring result."""

    score: float | None
    base_score: float | None
    coverage: float


def calculate_relationship_score(
    signals: Mapping[str, float | None],
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

    for signal_name, signal_score in signals.items():
        if signal_score is None:
            continue

        weight = policy.weights[signal_name]

        available_weight += weight
        weighted_numerator += weight * signal_score

    coverage = available_weight / total_weight

    if available_weight == 0.0:
        return RelationshipScore(
            score=None,
            base_score=None,
            coverage=coverage,
        )

    base_score = weighted_numerator / available_weight
    final_score = base_score

    return RelationshipScore(
        score=final_score,
        base_score=base_score,
        coverage=coverage,
    )

from typing import Any

@dataclass(frozen=True)
class ScoringEvidence:
    """Detailed evidence supporting an evaluated hypothesis."""
    signals: dict[str, float | None] = field(default_factory=dict)
    relationship: RelationshipScore | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    contributions: dict[str, Any] = field(default_factory=dict)

