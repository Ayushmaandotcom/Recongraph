from datetime import date
import pytest

from recongraph.matching.signals import (
    amount_score,
    reference_score,
    tax_identity_score,
    temporal_score,
)


def test_amount_score_returns_one_for_exact_match() -> None:
    assert amount_score(118000.0, 118000.0) == 1.0


def test_amount_score_is_scale_aware() -> None:
    small_scale_score = amount_score(
        2000.0,
        1000.0,
    )
    large_scale_score = amount_score(
        10_000_000.0,
        9_999_000.0,
    )

    assert small_scale_score == 0.0
    assert large_scale_score > small_scale_score


def test_amount_score_decays_within_tolerance() -> None:
    score = amount_score(
        100_000.0,
        99_500.0,
    )

    assert score == pytest.approx(0.5)


def test_amount_score_returns_zero_at_tolerance_boundary() -> None:
    score = amount_score(
        100_000.0,
        99_000.0,
    )

    assert score == 0.0


def test_amount_score_returns_zero_beyond_tolerance() -> None:
    score = amount_score(
        100_000.0,
        90_000.0,
    )

    assert score == 0.0


def test_amount_score_handles_two_zero_amounts() -> None:
    assert amount_score(0.0, 0.0) == 1.0


def test_amount_score_rejects_non_positive_tolerance() -> None:
    with pytest.raises(
        ValueError,
        match="tolerance must be greater than zero",
    ):
        amount_score(
            100_000.0,
            99_500.0,
            tolerance=0.0,
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


def test_reference_score_returns_one_for_normalized_exact_match() -> None:
    score = reference_score(
        "AB/1042",
        "AB-1042",
    )

    assert score == 1.0


def test_reference_score_uses_shared_significant_numeric_token() -> None:
    score = reference_score(
        "INV-1042",
        "AB/1042",
    )

    assert score == 0.8


def test_reference_score_returns_zero_without_shared_reference_evidence() -> None:
    score = reference_score(
        "INV-1042",
        "AB/8891",
    )

    assert score == 0.0


def test_reference_score_returns_none_for_missing_reference() -> None:
    assert reference_score("INV-1042", None) is None


def test_reference_score_returns_none_for_blank_references() -> None:
    assert reference_score("   ", "") is None


def test_reference_score_ignores_shared_year_like_tokens() -> None:
    score = reference_score(
        "INV-2026-1042",
        "AB-2026-8891",
    )

    assert score == 0.0


def test_reference_score_accepts_custom_shared_numeric_score() -> None:
    score = reference_score(
        "INV-1042",
        "AB/1042",
        shared_numeric_score=0.65,
    )

    assert score == 0.65


def test_reference_score_rejects_invalid_shared_numeric_score() -> None:
    with pytest.raises(
        ValueError,
        match="shared_numeric_score must be between zero and one",
    ):
        reference_score(
            "INV-1042",
            "AB/1042",
            shared_numeric_score=1.5,
        )


def test_reference_score_rejects_non_positive_token_length() -> None:
    with pytest.raises(
        ValueError,
        match="min_numeric_token_length must be greater than zero",
    ):
        reference_score(
            "INV-1042",
            "AB/1042",
            min_numeric_token_length=0,
        )
