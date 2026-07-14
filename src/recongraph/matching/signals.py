from datetime import date

from rapidfuzz import fuzz

from recongraph.normalization.text import (
    normalize_tax_identity,
    normalize_vendor_name,
)


def _is_year_like_token(token: str) -> bool:
    """Return whether a numeric token resembles a calendar year."""
    if len(token) != 4:
        return False

    year = int(token)

    return 1900 <= year <= 2100


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




def entity_score(
    entity_a: str | None,
    entity_b: str | None,
) -> float | None:
    """Calculate normalized textual similarity between vendor entities."""
    if entity_a is None or entity_b is None:
        return None

    normalized_a = normalize_vendor_name(entity_a)
    normalized_b = normalize_vendor_name(entity_b)

    if not normalized_a or not normalized_b:
        return None

    similarity = fuzz.ratio(
        normalized_a,
        normalized_b,
    )

    return similarity / 100.0
