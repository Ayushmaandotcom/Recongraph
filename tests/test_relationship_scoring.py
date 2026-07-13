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


def test_relationship_policy_defaults_to_no_contradiction_penalties() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.AMOUNT: 1.0,
        }
    )

    assert policy.contradiction_penalties == {}


def test_relationship_score_preserves_explanation_fields() -> None:
    result = RelationshipScore(
        score=0.375,
        base_score=0.75,
        coverage=1.0,
        contradiction_penalty=0.5,
        active_contradictions=(
            SignalName.TAX_IDENTITY,
        ),
    )

    assert result.score == 0.375
    assert result.base_score == 0.75
    assert result.coverage == 1.0
    assert result.contradiction_penalty == 0.5
    assert result.active_contradictions == (
        SignalName.TAX_IDENTITY,
    )


def test_relationship_score_is_immutable() -> None:
    result = RelationshipScore(
        score=1.0,
        base_score=1.0,
        coverage=1.0,
        contradiction_penalty=1.0,
        active_contradictions=(),
    )

    with pytest.raises(AttributeError):
        result.score = 0.5


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


@pytest.mark.parametrize(
    "invalid_penalty",
    [
        -0.1,
        1.1,
        float("nan"),
        float("inf"),
    ],
)
def test_relationship_policy_rejects_penalties_outside_unit_interval(
    invalid_penalty: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="between 0.0 and 1.0",
    ):
        RelationshipPolicy(
            weights={
                SignalName.TAX_IDENTITY: 1.0,
            },
            contradiction_penalties={
                SignalName.TAX_IDENTITY: invalid_penalty,
            },
        )


def test_relationship_policy_allows_hard_veto_penalty() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.TAX_IDENTITY: 1.0,
        },
        contradiction_penalties={
            SignalName.TAX_IDENTITY: 0.0,
        },
    )

    assert (
        policy.contradiction_penalties[SignalName.TAX_IDENTITY]
        == 0.0
    )


def test_relationship_policy_allows_neutral_penalty() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.TAX_IDENTITY: 1.0,
        },
        contradiction_penalties={
            SignalName.TAX_IDENTITY: 1.0,
        },
    )

    assert (
        policy.contradiction_penalties[SignalName.TAX_IDENTITY]
        == 1.0
    )


def test_relationship_policy_rejects_unweighted_contradiction_signal() -> None:
    with pytest.raises(
        ValueError,
        match="must also have a configured weight",
    ):
        RelationshipPolicy(
            weights={
                SignalName.AMOUNT: 1.0,
            },
            contradiction_penalties={
                SignalName.TAX_IDENTITY: 0.5,
            },
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
        },
        contradiction_penalties={
            SignalName.TAX_IDENTITY: 0.50,
        },
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
    assert result.contradiction_penalty == pytest.approx(1.0)
    assert result.active_contradictions == ()


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
    assert result.contradiction_penalty == pytest.approx(1.0)
    assert result.active_contradictions == ()


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
    assert result.contradiction_penalty == pytest.approx(1.0)
    assert result.active_contradictions == ()


def test_calculate_relationship_score_applies_tax_contradiction_penalty(
    purchase_to_gst_policy: RelationshipPolicy,
) -> None:
    result = calculate_relationship_score(
        signals={
            SignalName.ENTITY: 1.00,
            SignalName.REFERENCE: 1.00,
            SignalName.AMOUNT: 1.00,
            SignalName.TEMPORAL: 1.00,
            SignalName.TAX_IDENTITY: 0.00,
        },
        policy=purchase_to_gst_policy,
    )

    assert result.score == pytest.approx(0.375)
    assert result.base_score == pytest.approx(0.75)
    assert result.coverage == pytest.approx(1.0)
    assert result.contradiction_penalty == pytest.approx(0.50)
    assert result.active_contradictions == (
        SignalName.TAX_IDENTITY,
    )


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
    assert result.contradiction_penalty == pytest.approx(1.0)
    assert result.active_contradictions == ()


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


def test_calculate_relationship_score_multiplies_active_penalties() -> None:
    policy = RelationshipPolicy(
        weights={
            SignalName.AMOUNT: 0.5,
            SignalName.TAX_IDENTITY: 0.5,
        },
        contradiction_penalties={
            SignalName.AMOUNT: 0.8,
            SignalName.TAX_IDENTITY: 0.5,
        },
    )

    result = calculate_relationship_score(
        signals={
            SignalName.AMOUNT: 0.0,
            SignalName.TAX_IDENTITY: 0.0,
        },
        policy=policy,
    )

    assert result.base_score == pytest.approx(0.0)
    assert result.contradiction_penalty == pytest.approx(0.4)
    assert result.score == pytest.approx(0.0)
    assert result.active_contradictions == (
        SignalName.AMOUNT,
        SignalName.TAX_IDENTITY,
    )

