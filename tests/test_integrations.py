import sys
import hmac
import hashlib
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "recongraph-api"))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from recongraph.integrations.sap_connector import SAPConnector
from app.webhooks import router, WEBHOOK_SECRET

from recongraph.compliance.integrations.gst_portal import (
    StubGSTPortalClient,
    inward_supply_batch_to_records,
)
from recongraph.compliance.integrations.nic import StubNicClient


# ---------------------------------------------------------------------------
# SAP connector + webhook HMAC integration tests (Phase 8)
# ---------------------------------------------------------------------------

# Setup a dummy app to test the router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_sap_connector():
    connector = SAPConnector(base_url="mock_url", api_key="mock_key")
    records = connector.fetch_ap_invoices("2026-01-01")

    assert len(records) == 1
    assert records[0]["record_id"] == "SAP_5100000001"
    assert records[0]["tax_amount"] == 2700.00
    assert records[0]["total_amount"] == 17700.00


def test_webhook_valid_hmac():
    payload = {
        "tenant_id": "tenant_1",
        "source_system": "SAP",
        "invoices": [{"invoice_id": "123"}],
    }

    body_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(WEBHOOK_SECRET, body_bytes, hashlib.sha256).hexdigest()

    response = client.post(
        "/webhooks/erp/sync",
        content=body_bytes,
        headers={
            "x-hub-signature": signature,
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_webhook_invalid_hmac():
    payload = {
        "tenant_id": "tenant_1",
        "source_system": "SAP",
        "invoices": [{"invoice_id": "123"}],
    }

    response = client.post(
        "/webhooks/erp/sync",
        json=payload,
        headers={"x-hub-signature": "fake_signature_123"},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GST portal + NIC integration scaffold tests (F1, F7)
# ---------------------------------------------------------------------------

def test_stub_portal_downloads_batch() -> None:
    portal = StubGSTPortalClient()
    batch = portal.download_gstr_2b("29ABCDE1234F1Z5", "042024")
    assert batch.return_type == "GSTR2B"
    assert batch.return_period == "042024"
    assert len(batch.items) == 1
    assert batch.items[0].supplier_gstin == "29ABCDE1234F1Z5"


def test_batch_converts_to_gst_records() -> None:
    portal = StubGSTPortalClient()
    batch = portal.download_gstr_2a("29ABCDE1234F1Z5", "042024")
    records = inward_supply_batch_to_records(batch)
    assert len(records) == 1
    r = records[0]
    assert r.reference == "INV-STUB-001"
    assert r.classification == "B2B"
    assert r.filing_period == "042024"


def test_stub_gstin_verification() -> None:
    portal = StubGSTPortalClient()
    status = portal.verify_gstin("29ABCDE1234F1Z5")
    assert status.valid is True
    assert status.status == "Active"


def test_stub_nic_e_invoice() -> None:
    nic = StubNicClient()
    resp = nic.generate_e_invoice({"doc_num": "INV-001"})
    assert resp.irn.startswith("IRN-STUB")


def test_stub_nic_e_waybill() -> None:
    nic = StubNicClient()
    resp = nic.generate_e_waybill({})
    assert resp.eway_bill_no.startswith("EWB-STUB")


def test_stub_nic_cancel() -> None:
    nic = StubNicClient()
    result = nic.cancel_e_invoice("IRN-STUB-001", "Duplicate")
    assert result["status"] == "CANCELLED"
