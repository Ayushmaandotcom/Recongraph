from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PurchaseRecord:
    """Represent purchase-side financial evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: float
    record_date: date
    tax_identity: str | None
    net_amount: float | None = None
    tax_amount: float | None = None
    tax_rate: float | None = None
    currency: str = "USD"
    sign: int = 1


@dataclass(frozen=True)
class GSTRecord:
    """Represent GST-side financial evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: float
    record_date: date
    tax_identity: str | None
    net_amount: float | None = None
    tax_amount: float | None = None
    tax_rate: float | None = None
    currency: str = "USD"
    sign: int = -1
