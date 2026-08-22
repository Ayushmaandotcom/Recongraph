"""Data-transfer objects for government-portal integrations (F1, F7)."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class InwardSupplyItem:
    """A single line from a GSTR-2A/2B inward supply."""

    bill_no: str | None
    bill_date: date | None
    supplier_gstin: str | None
    supplier_name: str | None
    taxable_value: Decimal | None
    cgst: Decimal | None
    sgst: Decimal | None
    igst: Decimal | None
    cess: Decimal | None
    place_of_supply: str | None
    is_reverse_charge: bool | None
    classification: str | None
    irn_number: str | None
    irn_source: str | None


@dataclass
class InwardSupplyBatch:
    """A downloaded return period's worth of inward supplies."""

    gstin: str
    return_period: str
    return_type: str  # "GSTR2A" | "GSTR2B"
    items: list[InwardSupplyItem] = field(default_factory=list)


@dataclass(frozen=True)
class GstinStatus:
    gstin: str
    valid: bool
    status: str | None = None  # "Active" | "Cancelled" | ...
    legal_name: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class IrnResponse:
    irn: str
    ack_no: str | None = None
    ack_date: str | None = None
    qr_code: str | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class EwaybillResponse:
    eway_bill_no: str
    valid_upto: str | None = None
    raw: dict[str, Any] | None = None
