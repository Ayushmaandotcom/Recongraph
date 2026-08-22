"""ITC (Input Tax Credit) availability and claim-period logic.

Ported from India Compliance's `gst_india/utils/itc_claim.py` and the GST
Inward Supply model, Resilient Tech, GPL v3. See NOTICE.

A matched inward supply becomes eligible for ITC in a specific GSTR-3B claim
period. The claim period is derived from the filing period of the purchase /
match date, honoring the GST rule that ITC can only be availed once the
supplier has filed their return (post-GSTR-2B availability).
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


class ItcAvailability(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"
    INELIGIBLE = "Ineligible"
    UNKNOWN = "Unknown"


@dataclass(frozen=True)
class ItcClaim:
    """The ITC claim-period decision attached to a matched supply."""

    availability: ItcAvailability
    claim_period: str | None
    reason_unavailable: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "itc_availability": self.availability.value,
            "itc_claim_period": self.claim_period,
            "reason_itc_unavailability": self.reason_unavailable,
        }


def _format_period(year: int, month: int) -> str:
    return f"{month:02d}-{year}"


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def set_itc_claim_period_on_match(
    match_date: date,
    *,
    filing_period: str | None = None,
    available: bool = True,
    reason_unavailable: str | None = None,
) -> ItcClaim:
    """Compute the ITC claim period for a matched purchase.

    The claim period is the month following the match date (ITC is availed in
    the next return period after the supply is confirmed). When a
    ``filing_period`` (e.g. "042024") is provided it is honored directly.
    """
    if not available:
        return ItcClaim(
            availability=ItcAvailability.UNAVAILABLE,
            claim_period=None,
            reason_unavailable=reason_unavailable,
        )

    if filing_period:
        return ItcClaim(
            availability=ItcAvailability.AVAILABLE,
            claim_period=filing_period,
        )

    year, month = _next_month(match_date.year, match_date.month)
    return ItcClaim(
        availability=ItcAvailability.AVAILABLE,
        claim_period=_format_period(year, month),
    )
