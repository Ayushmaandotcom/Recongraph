import sys
import hmac
import hashlib
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "recongraph-api"))

from recongraph.integrations.sap_connector import SAPConnector
from fastapi.testclient import TestClient
from app.webhooks import router, WEBHOOK_SECRET
from fastapi import FastAPI

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
        "invoices": [{"invoice_id": "123"}]
    }
    
    body_bytes = json.dumps(payload).encode('utf-8')
    signature = hmac.new(WEBHOOK_SECRET, body_bytes, hashlib.sha256).hexdigest()
    
    response = client.post(
        "/webhooks/erp/sync", 
        content=body_bytes,
        headers={
            "x-hub-signature": signature,
            "Content-Type": "application/json"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_webhook_invalid_hmac():
    payload = {
        "tenant_id": "tenant_1",
        "source_system": "SAP",
        "invoices": [{"invoice_id": "123"}]
    }
    
    response = client.post(
        "/webhooks/erp/sync", 
        json=payload,
        headers={"x-hub-signature": "fake_signature_123"}
    )
    
    assert response.status_code == 403
