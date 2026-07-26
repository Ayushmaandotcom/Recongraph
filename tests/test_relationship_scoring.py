import pytest

from recongraph.matching.scoring import (
    RelationshipPolicy,
    RelationshipScore,
    SignalName,
    calculate_relationship_score,
)


def test_signal_name_values_are_stable() -> None:
    assert SignalName.ENTITY == "entity"
    assert SignalName.REFERENCE == "reference"
    assert SignalName.AMOUNT == "amount"
    assert SignalName.TEMPORAL == "temporal"
    assert SignalName.TAX_IDENTITY == "tax_identity"


def test_relationship_score_preserves_explanation_fields() -> None:
    result = RelationshipScore(
        score=0.375,
        base_score=0.75,
        coverage=1.0,
    )

    assert result.score == 0.375
    assert result.base_score == 0.75
    assert result.coverage == 1.0


def test_relationship_score_is_immutable() -> None:
    result = RelationshipScore(
        score=1.0,
        base_score=1.0,
        coverage=1.0,
    )

    with pytest.raises(AttributeError):
        result.score = 0.5  # type: ignore[misc]


def test_relationship_policy_rejects_empty_weights() -> None:
    with pytest.raises(
        ValueError,
        match="at least one signal weight",
    ):
        RelationshipPolicy(weights={})


@pytest.mark.parametrize(
    "invalid_weight",
    [
        0.0,
        -0.1,
        float("nan"),
        float("inf"),
    ],
)
def test_relationship_policy_rejects_non_positive_weights(
    invalid_weight: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        RelationshipPolicy(
            weights={
                SignalName.AMOUNT: invalid_weight,
            }
        )


@pytest.fixture
def purchase_to_gst_policy() -> RelationshipPolicy:
    return RelationshipPolicy(
        weights={
            SignalName.ENTITY: 0.20,
            SignalName.REFERENCE: 0.20,
            SignalName.AMOUNT: 0.25,
            SignalName.TEMPORAL: 0.10,
            SignalName.TAX_IDENTITY: 0.25,
        }
    )


def test_calculate_relationship_score_for_complete_strong_evidence(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    result = calculate_relationship_score(
        signals={
            SignalName.ENTITY: 0.90,
            SignalName.REFERENCE: 0.80,
            SignalName.AMOUNT: 1.00,
            SignalName.TEMPORAL: 0.70,
            SignalName.TAX_IDENTITY: 1.00,
        },
        policy=purchase_to_gst_policy,
    )

    assert result.score == pytest.approx(0.91)
    assert result.base_score == pytest.approx(0.91)
    assert result.coverage == pytest.approx(1.0)


def test_calculate_relationship_score_renormalizes_missing_evidence(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    result = calculate_relationship_score(
        signals={
            SignalName.ENTITY: 0.90,
            SignalName.REFERENCE: 0.80,
            SignalName.AMOUNT: 1.00,
            SignalName.TEMPORAL: 0.70,
            SignalName.TAX_IDENTITY: None,
        },
        policy=purchase_to_gst_policy,
    )

    assert result.score == pytest.approx(0.88)
    assert result.base_score == pytest.approx(0.88)
    assert result.coverage == pytest.approx(0.75)


def test_calculate_relationship_score_preserves_low_coverage(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    result = calculate_relationship_score(
        signals={
            SignalName.ENTITY: 1.00,
            SignalName.REFERENCE: None,
            SignalName.AMOUNT: None,
            SignalName.TEMPORAL: None,
            SignalName.TAX_IDENTITY: None,
        },
        policy=purchase_to_gst_policy,
    )

    assert result.score == pytest.approx(1.0)
    assert result.base_score == pytest.approx(1.0)
    assert result.coverage == pytest.approx(0.20)


def test_calculate_relationship_score_preserves_unknown_when_all_evidence_missing(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    result = calculate_relationship_score(
        signals={
            SignalName.ENTITY: None,
            SignalName.REFERENCE: None,
            SignalName.AMOUNT: None,
            SignalName.TEMPORAL: None,
            SignalName.TAX_IDENTITY: None,
        },
        policy=purchase_to_gst_policy,
    )

    assert result.score is None
    assert result.base_score is None
    assert result.coverage == pytest.approx(0.0)


def test_calculate_relationship_score_rejects_missing_policy_signal(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    with pytest.raises(
        ValueError,
        match="exactly match policy signals",
    ):
        calculate_relationship_score(
            signals={
                SignalName.ENTITY: 1.0,
                SignalName.REFERENCE: 1.0,
                SignalName.AMOUNT: 1.0,
                SignalName.TEMPORAL: 1.0,
            },
            policy=purchase_to_gst_policy,
        )


def test_calculate_relationship_score_rejects_unconfigured_signal() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.AMOUNT: 1.0,
        }
    )

    with pytest.raises(
        ValueError,
        match="exactly match policy signals",
    ):
        calculate_relationship_score(
            signals={
                SignalName.AMOUNT: 1.0,
                SignalName.ENTITY: 1.0,
            },
            policy=policy,
        )


@pytest.mark.parametrize(
    "invalid_score",
    [
        -0.1,
        1.1,
        float("nan"),
        float("inf"),
    ],
)
def test_calculate_relationship_score_rejects_invalid_signal_scores(
    invalid_score: float,
) -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.AMOUNT: 1.0,
        }
    )

    with pytest.raises(
        ValueError,
        match="finite and between 0.0 and 1.0",
    ):
        calculate_relationship_score(
            signals={
                SignalName.AMOUNT: invalid_score,
            },
            policy=policy,
        )


def test_calculate_relationship_score_allows_zero_signal_score() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.AMOUNT: 1.0,
        }
    )

    result = calculate_relationship_score(
        signals={
            SignalName.AMOUNT: 0.0,
        },
        policy=policy,
    )

    assert result.score == pytest.approx(0.0)
    assert result.base_score == pytest.approx(0.0)
    assert result.coverage == pytest.approx(1.0)
