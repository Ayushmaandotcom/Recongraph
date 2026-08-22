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
import logging
from typing import Dict, Any

logger = logging.getLogger("recongraph-api")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s')

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

from contextvars import ContextVar
request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

logger.addFilter(RequestIdFilter())

from fastapi import Request

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    request_id_var.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

# In-memory store for runs (keyed by UUID)
# In a real system, this would be a database (PostgreSQL/Redis)
_runs_store: Dict[str, dict] = {}

# Setup SQLite for HITL Feedback
def init_db():
    conn = sqlite3.connect('hitl_feedback.db')
    c = conn.cursor()
    
    # Check if we need to migrate from v1 (unstructured) to v2 (normalized)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_v2'")
    v2_exists = c.fetchone() is not None
    
    if not v2_exists:
        c.execute('''
            CREATE TABLE feedback_v2
            (review_id INTEGER PRIMARY KEY AUTOINCREMENT,
             packet_id TEXT,
             purchase_record_id TEXT,
             gst_record_id TEXT,
             deterministic_decision TEXT,
             deterministic_score REAL,
             deterministic_coverage REAL,
             ml_score REAL,
             calibrated_ml_probability REAL,
             graph_features TEXT,
             evidence_features TEXT,
             final_human_decision TEXT,
             reviewer_action TEXT,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
             engine_version TEXT,
             model_version TEXT,
             config_hash TEXT,
             explanation_version TEXT,
             rag_context_identifiers TEXT,
             legacy_payload TEXT)
        ''')
        
        # Migrate old data if v1 exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
        v1_exists = c.fetchone() is not None
        
        if v1_exists:
            c.execute("SELECT packet_id, action, timestamp, payload FROM feedback")
            rows = c.fetchall()
            for row in rows:
                packet_id, action, timestamp, payload = row
                try:
                    payload_dict = json.loads(payload)
                except Exception:
                    payload_dict = {}
                c.execute('''
                    INSERT INTO feedback_v2 
                    (packet_id, reviewer_action, timestamp, legacy_payload) 
                    VALUES (?, ?, ?, ?)
                ''', (packet_id, action, timestamp, payload))
            
            # Rename old table as backup
            c.execute("ALTER TABLE feedback RENAME TO feedback_v1_backup")
            
    conn.commit()
    conn.close()

init_db()

class FeedbackRequest(BaseModel):
    packet_id: str
    action: str
    purchase_record_id: str = ""
    gst_record_id: str = ""
    deterministic_decision: str = ""
    deterministic_score: float = 0.0
    deterministic_coverage: float = 0.0
    ml_score: float = 0.0
    calibrated_ml_probability: float = 0.0
    graph_features: dict = {}
    evidence_features: dict = {}
    engine_version: str = ""
    model_version: str = ""
    config_hash: str = ""
    explanation_version: str = ""
    rag_context_identifiers: list = []
    payload: dict = {} # Legacy compat

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

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/ready")
async def readiness_check():
    # In a real scenario, ping the database and models
    return {"status": "ready"}

@app.get("/version")
async def version_check():
    from recongraph.engine import ReconGraphEngine
    return {"version": ReconGraphEngine.VERSION}

@app.post("/reconcile", response_model=RunResponse)
async def reconcile(
    purchases: UploadFile = File(...),
    gsts: UploadFile = File(...)
):
    MAX_CSV_SIZE = 10 * 1024 * 1024 # 10 MB limit for security (7Q)
    
    try:
        logger.info(f"Received reconciliation request. Purchases: {purchases.filename}, GSTs: {gsts.filename}")
        p_content_bytes = await purchases.read()
        if len(p_content_bytes) > MAX_CSV_SIZE:
            raise HTTPException(status_code=413, detail="Purchases CSV exceeds 10MB limit.")
            
        g_content_bytes = await gsts.read()
        if len(g_content_bytes) > MAX_CSV_SIZE:
            raise HTTPException(status_code=413, detail="GSTs CSV exceeds 10MB limit.")
            
        p_content = p_content_bytes.decode("utf-8")
        g_content = g_content_bytes.decode("utf-8")
        
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
            """INSERT INTO feedback_v2 
               (packet_id, purchase_record_id, gst_record_id, deterministic_decision, 
                deterministic_score, deterministic_coverage, ml_score, calibrated_ml_probability,
                graph_features, evidence_features, final_human_decision, reviewer_action,
                engine_version, model_version, config_hash, explanation_version, rag_context_identifiers, legacy_payload) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                feedback.packet_id,
                feedback.purchase_record_id,
                feedback.gst_record_id,
                feedback.deterministic_decision,
                feedback.deterministic_score,
                feedback.deterministic_coverage,
                feedback.ml_score,
                feedback.calibrated_ml_probability,
                json.dumps(feedback.graph_features),
                json.dumps(feedback.evidence_features),
                feedback.action, # final_human_decision
                feedback.action, # reviewer_action
                feedback.engine_version,
                feedback.model_version,
                feedback.config_hash,
                feedback.explanation_version,
                json.dumps(feedback.rag_context_identifiers),
                json.dumps(feedback.payload)
            )
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
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
