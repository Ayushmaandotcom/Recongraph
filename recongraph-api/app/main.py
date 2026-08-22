from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import io
import csv
from decimal import Decimal
from datetime import date
import sqlite3
import json
from typing import Dict, Any

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider,
    VendorEvidenceProvider, ReferenceEvidenceProvider,
)
from recongraph.domain.vendor.context import VendorIdentityContext
from recongraph.matching.reference_evidence import (
    build_reference_corpus_profile, ReferenceEvidenceContext, ReferenceEvidencePolicy,
)

app = FastAPI(title="ReconGraph API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for runs (keyed by UUID)
# In a real system, this would be a database (PostgreSQL/Redis)
_runs_store: Dict[str, dict] = {}

# Setup SQLite for HITL Feedback
def init_db():
    conn = sqlite3.connect('hitl_feedback.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         packet_id TEXT,
         action TEXT,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
         payload TEXT)
    ''')
    conn.commit()
    conn.close()

init_db()

class FeedbackRequest(BaseModel):
    packet_id: str
    action: str
    payload: dict

class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str

def _parse_csv(content: str, is_purchase: bool) -> list:
    records = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        try:
            if is_purchase:
                record = PurchaseRecord(
                    record_id=row.get("record_id") or row.get("id", ""),
                    vendor_name=row.get("vendor_name") or row.get("supplier_name") or None,
                    reference=row.get("reference") or row.get("invoice_number") or None,
                    amount=Decimal(str(row.get("amount", "0"))),
                    record_date=date.fromisoformat(row.get("record_date") or row.get("invoice_date", "2000-01-01")),
                    tax_identity=row.get("gstin") or row.get("tax_identity") or None,
                )
            else:
                record = GSTRecord(
                    record_id=row.get("record_id") or row.get("id", ""),
                    vendor_name=row.get("supplier_name") or row.get("vendor_name") or None,
                    reference=row.get("reference") or row.get("invoice_number") or None,
                    amount=Decimal(str(row.get("amount", "0"))),
                    record_date=date.fromisoformat(row.get("record_date") or row.get("invoice_date", "2000-01-01")),
                    tax_identity=row.get("gstin") or row.get("tax_identity") or None,
                )
            records.append(record)
        except Exception as e:
            # Skip unparseable rows for now
            pass
    return records

@app.post("/reconcile", response_model=RunResponse)
async def reconcile(
    purchases: UploadFile = File(...),
    gsts: UploadFile = File(...)
):
    try:
        p_content = (await purchases.read()).decode("utf-8")
        g_content = (await gsts.read()).decode("utf-8")
        
        P = _parse_csv(p_content, True)
        G = _parse_csv(g_content, False)
        
        if not P or not G:
            raise HTTPException(status_code=400, detail="One or both CSV files were empty or unparseable.")
            
        corpus = build_reference_corpus_profile([r.reference for r in P + G]) # type: ignore
        ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
        vendor_ctx = VendorIdentityContext(corpus_profile=None)
        
        providers = [
            FinancialEvidenceProvider(),
            TemporalEvidenceProvider(),
            TaxEvidenceProvider(),
            VendorEvidenceProvider(vendor_ctx),
            ReferenceEvidenceProvider(ref_ctx),
        ]
        
        engine = ReconGraphEngine(config=ReconGraphConfig(), providers=providers)
        result = engine.reconcile(P, G)
        
        run_id = str(uuid.uuid4())
        _runs_store[run_id] = result.to_dict()
        
        return RunResponse(run_id=run_id, status="success", message="Reconciliation complete")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in _runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    return _runs_store[run_id]

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    try:
        conn = sqlite3.connect('hitl_feedback.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO feedback (packet_id, action, payload) VALUES (?, ?, ?)",
            (feedback.packet_id, feedback.action, json.dumps(feedback.payload))
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/demo")
async def get_demo():
    """Returns the challenge dataset result instantly."""
    from pathlib import Path
    
    # Check if we have pre-computed demo results
    demo_file = Path("demo_results.json")
    if demo_file.exists():
        import json
        with open(demo_file, "r") as f:
            return json.load(f)
            
    # Otherwise, fallback to computing it (if challenge dataset exists)
    import subprocess
    import sys
    
    challenge_dir = Path("../datasets/challenge")
    p_csv = challenge_dir / "purchase_register_v1.csv"
    g_csv = challenge_dir / "gst_records_v1.csv"
    
    if not p_csv.exists() or not g_csv.exists():
        raise HTTPException(status_code=404, detail="Demo dataset not found")
        
    with open(p_csv, "r") as f:
        p_content = f.read()
    with open(g_csv, "r") as f:
        g_content = f.read()
        
    P = _parse_csv(p_content, True)
    G = _parse_csv(g_content, False)
    
    corpus = build_reference_corpus_profile([r.reference for r in P + G]) # type: ignore
    ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
    vendor_ctx = VendorIdentityContext(corpus_profile=None)
    
    providers = [
        FinancialEvidenceProvider(), TemporalEvidenceProvider(), TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_ctx), ReferenceEvidenceProvider(ref_ctx),
    ]
    
    engine = ReconGraphEngine(config=ReconGraphConfig(), providers=providers)
    result = engine.reconcile(P, G)
    
    return result.to_dict()
