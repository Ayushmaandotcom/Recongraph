"""Tests for the IMS action model and ITC claim period (F4)."""

from datetime import date

from recongraph.compliance.ims import (
    ACTION_STATUS_MAP,
    ImsAction,
    ImsDecision,
    apply_action,
)
from recongraph.compliance.itc_claim import (
    ItcAvailability,
    set_itc_claim_period_on_match,
)


def test_action_status_map() -> None:
    assert ACTION_STATUS_MAP[ImsAction.ACCEPT] == "Reconciled"
    assert ACTION_STATUS_MAP[ImsAction.REJECT] == "Unreconciled"
    assert ACTION_STATUS_MAP[ImsAction.PENDING] == "Unreconciled"
    assert ACTION_STATUS_MAP[ImsAction.IGNORE] == "Ignored"
    assert ACTION_STATUS_MAP[ImsAction.NO_ACTION] == "Unreconciled"


def test_apply_action_accept() -> None:
    decision = apply_action("PKT1", "Accept", reviewer_id="u1", comments="ok")
    assert isinstance(decision, ImsDecision)
    assert decision.action == ImsAction.ACCEPT
    assert decision.status == "Reconciled"
    assert decision.is_resolved is True


def test_apply_action_unknown_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        apply_action("PKT1", "Bogus")


def test_action_round_trips_to_dict() -> None:
    decision = apply_action("PKT1", ImsAction.REJECT, reviewer_id="u1")
    d = decision.to_dict()
    assert d["packet_id"] == "PKT1"
    assert d["action"] == "Reject"
    assert d["status"] == "Unreconciled"
    assert d["reviewer_id"] == "u1"


def test_itc_claim_period_next_month() -> None:
    claim = set_itc_claim_period_on_match(date(2024, 4, 15))
    assert claim.availability == ItcAvailability.AVAILABLE
    assert claim.claim_period == "05-2024"


def test_itc_claim_period_rolls_year() -> None:
    claim = set_itc_claim_period_on_match(date(2024, 12, 31))
    assert claim.claim_period == "01-2025"


def test_itc_claim_period_honors_filing_period() -> None:
    claim = set_itc_claim_period_on_match(date(2024, 4, 15), filing_period="042024")
    assert claim.claim_period == "042024"


def test_itc_unavailable() -> None:
    claim = set_itc_claim_period_on_match(
        date(2024, 4, 15), available=False, reason_unavailable="Supplier not filed"
    )
    assert claim.availability == ItcAvailability.UNAVAILABLE
    assert claim.claim_period is None
    assert claim.reason_unavailable == "Supplier not filed"
