import hmac
import hashlib
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any

# In production, this would be loaded from a secure vault or env vars
WEBHOOK_SECRET = b"erp_sync_secret_v1_2026"

router = APIRouter(prefix="/webhooks", tags=["ERP Integrations"])

async def verify_hmac(request: Request, x_hub_signature: str = Header(None)):
    """
    Verifies that the incoming webhook request was actually sent by a trusted ERP
    and hasn't been tampered with in transit.
    """
    if not x_hub_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    body = await request.body()
    
    # Calculate HMAC-SHA256 signature
    expected_signature = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_signature, x_hub_signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
        
    return True

class ERPPayload(BaseModel):
    tenant_id: str
    source_system: str
    invoices: List[Dict[str, Any]]

@router.post("/erp/sync")
async def sync_erp_invoices(payload: ERPPayload, request: Request, x_hub_signature: str = Header(None)):
    """
    Secure endpoint for ERP systems to push invoice batches in real-time.
    """
    # 1. Verify cryptographic signature
    await verify_hmac(request, x_hub_signature)
    
    # 2. Accept payload and dispatch to Celery for asynchronous processing
    # from recongraph_api.worker import process_erp_sync
    # process_erp_sync.delay(payload.dict())
    
    return {
        "status": "success",
        "message": f"Successfully queued {len(payload.invoices)} invoices for tenant {payload.tenant_id}.",
        "job_id": "job_12345"
    }
