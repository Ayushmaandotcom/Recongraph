"""NIC (IRP) e-invoice and e-waybill client scaffold (F7).

Defines the interface for the Invoice Registration Portal (IRP) and e-waybill
services, plus a deterministic stub. Live integration requires NIC encryption
credentials and is out of scope until a follow-up epic.
"""

from typing import Protocol

from recongraph.compliance.integrations.models import EwaybillResponse, IrnResponse


class NicClient(Protocol):
    """Interface to the NIC e-invoice (IRP) and e-waybill portals."""

    def generate_e_invoice(self, payload: dict) -> IrnResponse: ...

    def cancel_e_invoice(self, irn: str, reason: str) -> dict: ...

    def generate_e_waybill(self, payload: dict) -> EwaybillResponse: ...


class StubNicClient:
    """Deterministic, offline NIC stub (no network, no encryption)."""

    def generate_e_invoice(self, payload: dict) -> IrnResponse:
        irn = f"IRN-STUB-{payload.get('doc_num', '000000')}"
        return IrnResponse(irn=irn, ack_no="ACK-STUB", ack_date="2024-04-01")

    def cancel_e_invoice(self, irn: str, reason: str) -> dict:
        return {"irn": irn, "status": "CANCELLED", "reason": reason}

    def generate_e_waybill(self, payload: dict) -> EwaybillResponse:
        return EwaybillResponse(eway_bill_no="EWB-STUB-0000000001")
