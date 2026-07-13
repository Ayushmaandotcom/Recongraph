from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PurchaseRecord:
    """Represent purchase-side financial evidence."""

    vendor_name: str | None
    reference: str | None
    amount: float
    record_date: date
    tax_identity: str | None


@dataclass(frozen=True)
class GSTRecord:
    """Represent GST-side financial evidence."""

    vendor_name: str | None
    reference: str | None
    amount: float
    record_date: date
    tax_identity: str | None
