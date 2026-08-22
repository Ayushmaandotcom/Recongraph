"""GST Portal client scaffold (F1).

Defines the interface for downloading GSTR-2A/2B and verifying GSTINs against
the government portal, plus a deterministic stub for offline development and a
helper that maps downloaded inward-supply payloads into ReconGraph records.

Live integration (OTP login, session encryption, auth-token refresh) is out of
scope until GST Portal credentials are provided.
"""

from datetime import date
from decimal import Decimal
from typing import Protocol

from recongraph.compliance.integrations.models import (
    GstinStatus,
    InwardSupplyBatch,
    InwardSupplyItem,
)
from recongraph.domain.records import GSTRecord


class GSTPortalClient(Protocol):
    """Interface to the GST taxpayer/returns and public APIs."""

    def request_otp(self, gstin: str) -> str: ...

    def verify_otp(self, gstin: str, otp: str) -> str: ...

    def download_gstr_2a(self, gstin: str, period: str) -> InwardSupplyBatch: ...

    def download_gstr_2b(self, gstin: str, period: str) -> InwardSupplyBatch: ...

    def verify_gstin(self, gstin: str) -> GstinStatus: ...


class StubGSTPortalClient:
    """Deterministic, offline client returning fixed fixtures (no network)."""

    def request_otp(self, gstin: str) -> str:
        return "STUB-OTP"

    def verify_otp(self, gstin: str, otp: str) -> str:
        return "stub-session-token"

    def download_gstr_2a(self, gstin: str, period: str) -> InwardSupplyBatch:
        return InwardSupplyBatch(
            gstin=gstin,
            return_period=period,
            return_type="GSTR2A",
            items=[_stub_item()],
        )

    def download_gstr_2b(self, gstin: str, period: str) -> InwardSupplyBatch:
        return InwardSupplyBatch(
            gstin=gstin,
            return_period=period,
            return_type="GSTR2B",
            items=[_stub_item()],
        )

    def verify_gstin(self, gstin: str) -> GstinStatus:
        return GstinStatus(gstin=gstin, valid=True, status="Active")


def _stub_item() -> InwardSupplyItem:
    return InwardSupplyItem(
        bill_no="INV-STUB-001",
        bill_date=date(2024, 4, 1),
        supplier_gstin="29ABCDE1234F1Z5",
        supplier_name="Stub Supplier Pvt Ltd",
        taxable_value=Decimal("1000.00"),
        cgst=Decimal("90.00"),
        sgst=Decimal("90.00"),
        igst=None,
        cess=None,
        place_of_supply="29",
        is_reverse_charge=False,
        classification="B2B",
        irn_number=None,
        irn_source=None,
    )


def inward_supply_batch_to_records(batch: InwardSupplyBatch) -> list[GSTRecord]:
    """Convert a downloaded inward-supply batch into ReconGraph GSTRecords."""
    records: list[GSTRecord] = []
    for i, item in enumerate(batch.items):
        records.append(GSTRecord(
            record_id=f"{batch.return_period}-{batch.gstin}-{i}",
            vendor_name=item.supplier_name,
            reference=item.bill_no,
            amount=item.taxable_value or Decimal("0"),
            record_date=item.bill_date or date(2000, 1, 1),
            tax_identity=item.supplier_gstin,
            filing_period=batch.return_period,
            taxable_value=item.taxable_value,
            cgst=item.cgst,
            sgst=item.sgst,
            igst=item.igst,
            cess=item.cess,
            place_of_supply=item.place_of_supply,
            is_reverse_charge=item.is_reverse_charge,
            classification=item.classification,
            irn_number=item.irn_number,
            irn_source=item.irn_source,
        ))
    return records
