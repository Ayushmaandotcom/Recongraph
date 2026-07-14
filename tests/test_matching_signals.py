from datetime import date
import pytest

from recongraph.matching.signals import (
    entity_score,
    tax_identity_score,
    temporal_score,
)





def test_tax_identity_score_returns_one_for_matching_identities() -> None:
    score = tax_identity_score(
        "07ABCDE1234F1Z5",
        "07abcde1234f1z5",
    )

    assert score == 1.0


def test_tax_identity_score_returns_zero_for_conflicting_identities() -> None:
    score = tax_identity_score(
        "07ABCDE1234F1Z5",
        "09WXYZA7890B1Z4",
    )

    assert score == 0.0


def test_tax_identity_score_returns_none_when_identity_is_missing() -> None:
    score = tax_identity_score(
        "07ABCDE1234F1Z5",
        None,
    )

    assert score is None


def test_tax_identity_score_returns_none_when_both_identities_are_missing() -> None:
    assert tax_identity_score(None, None) is None


def test_tax_identity_score_treats_blank_identity_as_unknown() -> None:
    assert tax_identity_score("", "   ") is None


def test_temporal_score_returns_one_for_same_date() -> None:
    score = temporal_score(
        date(2026, 6, 12),
        date(2026, 6, 12),
        max_days=7,
    )

    assert score == 1.0


def test_temporal_score_decays_with_date_distance() -> None:
    score = temporal_score(
        date(2026, 6, 12),
        date(2026, 6, 13),
        max_days=7,
    )

    assert score == pytest.approx(6 / 7)


def test_temporal_score_is_direction_agnostic() -> None:
    forward_score = temporal_score(
        date(2026, 6, 12),
        date(2026, 6, 15),
        max_days=7,
    )
    backward_score = temporal_score(
        date(2026, 6, 15),
        date(2026, 6, 12),
        max_days=7,
    )

    assert forward_score == backward_score


def test_temporal_score_returns_zero_at_window_boundary() -> None:
    score = temporal_score(
        date(2026, 6, 12),
        date(2026, 6, 19),
        max_days=7,
    )

    assert score == 0.0


def test_temporal_score_returns_zero_beyond_window() -> None:
    score = temporal_score(
        date(2026, 6, 12),
        date(2026, 7, 12),
        max_days=7,
    )

    assert score == 0.0


def test_temporal_score_rejects_non_positive_window() -> None:
    with pytest.raises(
        ValueError,
        match="max_days must be greater than zero",
    ):
        temporal_score(
            date(2026, 6, 12),
            date(2026, 6, 13),
            max_days=0,
        )


