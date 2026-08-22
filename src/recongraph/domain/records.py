from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from recongraph.domain.document.layout import DocumentLayoutArtifact, OcrConfidenceReport
    from recongraph.domain.reliability import ReliabilityEnvelope

@dataclass(frozen=True)
class PurchaseRecord:
    """Represent purchase-side financial evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: Decimal
    record_date: date
    tax_identity: str | None
    description: str | None = None
    filing_period: str | None = None
    net_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    currency: str = "USD"
    sign: int = 1
    layout_artifact: "Optional['DocumentLayoutArtifact']" = None
    ocr_confidence_report: "Optional['OcrConfidenceReport']" = None
    reliability_envelope: "Optional['ReliabilityEnvelope']" = None
    place_of_supply: str | None = None
    is_reverse_charge: bool | None = None
    document_type: str | None = None
    is_return: bool | None = None
    amendment_type: str | None = None
    fiscal_year: str | None = None
    company_gstin: str | None = None
    taxable_value: Decimal | None = None
    cgst: Decimal | None = None
    sgst: Decimal | None = None
    igst: Decimal | None = None
    cess: Decimal | None = None
    irn_number: str | None = None
    irn_source: str | None = None
    classification: str | None = None
    def __post_init__(self):
        for field in ("amount", "net_amount", "tax_amount", "tax_rate",
                      "taxable_value", "cgst", "sgst", "igst", "cess"):
            val = getattr(self, field, None)
            if val is not None and isinstance(val, float):
                raise TypeError(f"Financial field '{field}' must be initialized as Decimal, not float.")

@dataclass(frozen=True)
class GSTRecord:
    """Represent GST-side financial evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: Decimal
    record_date: date
    tax_identity: str | None
    description: str | None = None
    filing_period: str | None = None
    net_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    currency: str = "USD"
    sign: int = -1
    layout_artifact: "Optional['DocumentLayoutArtifact']" = None
    ocr_confidence_report: "Optional['OcrConfidenceReport']" = None
    reliability_envelope: "Optional['ReliabilityEnvelope']" = None
    place_of_supply: str | None = None
    is_reverse_charge: bool | None = None
    document_type: str | None = None
    is_return: bool | None = None
    amendment_type: str | None = None
    fiscal_year: str | None = None
    company_gstin: str | None = None
    taxable_value: Decimal | None = None
    cgst: Decimal | None = None
    sgst: Decimal | None = None
    igst: Decimal | None = None
    cess: Decimal | None = None
    irn_number: str | None = None
    irn_source: str | None = None
    classification: str | None = None
    def __post_init__(self):
        for field in ("amount", "net_amount", "tax_amount", "tax_rate",
                      "taxable_value", "cgst", "sgst", "igst", "cess"):
            val = getattr(self, field, None)
            if val is not None and isinstance(val, float):
                raise TypeError(f"Financial field '{field}' must be initialized as Decimal, not float.")

@dataclass(frozen=True)
class InvoiceRecord:
    """Represent invoice-side financial evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: Decimal
    record_date: date
    tax_identity: str | None
    description: str | None = None
    filing_period: str | None = None
    net_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    currency: str = "USD"
    sign: int = 1
    def __post_init__(self):
        for field in ("amount", "net_amount", "tax_amount", "tax_rate"):
            val = getattr(self, field, None)
            if val is not None and isinstance(val, float):
                raise TypeError(f"Financial field '{field}' must be initialized as Decimal, not float.")

@dataclass(frozen=True)
class BankRecord:
    """Represent bank-side financial settlement evidence."""

    record_id: str

    vendor_name: str | None
    reference: str | None
    amount: Decimal
    record_date: date
    description: str | None = None
    currency: str = "USD"
    sign: int = -1
    def __post_init__(self):
        for field in ("amount",):
            val = getattr(self, field, None)
            if val is not None and isinstance(val, float):
                raise TypeError(f"Financial field '{field}' must be initialized as Decimal, not float.")
