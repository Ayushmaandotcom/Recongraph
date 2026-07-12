from datetime import date

from recongraph.normalization.text import (
    extract_numeric_reference_tokens,
    normalize_reference,
    normalize_tax_identity,
)


def _is_year_like_token(token: str) -> bool:
    """Return whether a numeric token resembles a calendar year."""
    if len(token) != 4:
        return False

    year = int(token)

    return 1900 <= year <= 2100


def amount_score(
    amount_a: float,
    amount_b: float,
    tolerance: float = 0.01,
) -> float:
    """Calculate scale-aware compatibility between two monetary amounts."""
    if tolerance <= 0:
        raise ValueError("tolerance must be greater than zero")

    maximum_amount = max(abs(amount_a), abs(amount_b))

    if maximum_amount == 0:
        return 1.0

    relative_difference = (
        abs(amount_a - amount_b) / maximum_amount
    )

    return max(
        0.0,
        1.0 - (relative_difference / tolerance),
    )


def tax_identity_score(
    tax_identity_a: str | None,
    tax_identity_b: str | None,
) -> float | None:
    """Compare tax identities while preserving unknown evidence states."""
    if tax_identity_a is None or tax_identity_b is None:
        return None

    normalized_a = normalize_tax_identity(tax_identity_a)
    normalized_b = normalize_tax_identity(tax_identity_b)

    if not normalized_a or not normalized_b:
        return None

    if normalized_a == normalized_b:
        return 1.0

    return 0.0


def temporal_score(
    date_a: date,
    date_b: date,
    max_days: int,
) -> float:
    """Calculate temporal compatibility within an expected date window."""
    if max_days <= 0:
        raise ValueError("max_days must be greater than zero")

    day_difference = abs((date_a - date_b).days)

    return max(
        0.0,
        1.0 - (day_difference / max_days),
    )


def reference_score(
    reference_a: str | None,
    reference_b: str | None,
    min_numeric_token_length: int = 3,
    shared_numeric_score: float = 0.8,
) -> float | None:
    """Calculate compatibility between financial references."""
    if min_numeric_token_length <= 0:
        raise ValueError(
            "min_numeric_token_length must be greater than zero"
        )

    if not 0.0 <= shared_numeric_score <= 1.0:
        raise ValueError(
            "shared_numeric_score must be between zero and one"
        )

    if reference_a is None or reference_b is None:
        return None

    normalized_a = normalize_reference(reference_a)
    normalized_b = normalize_reference(reference_b)

    if not normalized_a or not normalized_b:
        return None

    if normalized_a == normalized_b:
        return 1.0

    numeric_tokens_a = extract_numeric_reference_tokens(
        reference_a,
        min_length=min_numeric_token_length,
    )
    numeric_tokens_b = extract_numeric_reference_tokens(
        reference_b,
        min_length=min_numeric_token_length,
    )

    numeric_tokens_a = {
        token
        for token in numeric_tokens_a
        if not _is_year_like_token(token)
    }
    numeric_tokens_b = {
        token
        for token in numeric_tokens_b
        if not _is_year_like_token(token)
    }

    shared_numeric_tokens = numeric_tokens_a & numeric_tokens_b

    if shared_numeric_tokens:
        return shared_numeric_score

    return 0.0
