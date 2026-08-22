from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
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

from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, get_current_user, require_admin, require_auditor
from datetime import timedelta

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Mock user database for Phase 8 demonstration
    if form_data.username == "admin" and form_data.password == "admin":
        role = "admin"
    elif form_data.username == "auditor" and form_data.password == "auditor":
        role = "auditor"
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    access_token_expires = timedelta(minutes=60*24)
    access_token = create_access_token(
        data={"sub": form_data.username, "role": role, "tenant_id": "tenant-001"},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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

def _run_reconciliation_task(run_id: str, p_content: str, g_content: str):
    try:
        _runs_store[run_id] = {"status": "processing", "message": "Parsing CSV and generating graphs"}
        P = _parse_csv(p_content, True)
        G = _parse_csv(g_content, False)
        
        if not P or not G:
            _runs_store[run_id] = {"status": "failed", "message": "One or both CSV files were empty or unparseable."}
            return
            
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
        
        _runs_store[run_id] = {"status": "processing", "message": "Engine running hypothesis search"}
        engine = ReconGraphEngine(config=ReconGraphConfig(), providers=providers)
        result = engine.reconcile(P, G)
        
        _runs_store[run_id] = {"status": "success", "result": result.to_dict()}
    except Exception as e:
        logger.error(f"Reconciliation task {run_id} failed: {e}")
        _runs_store[run_id] = {"status": "failed", "message": str(e)}

@app.post("/reconcile", response_model=RunResponse)
async def reconcile(
    purchases: UploadFile = File(...),
    gsts: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(require_auditor)
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
        
        run_id = str(uuid.uuid4())
        _runs_store[run_id] = {"status": "queued", "message": "Job queued for background processing"}
        
        if background_tasks:
            background_tasks.add_task(_run_reconciliation_task, run_id, p_content, g_content)
        else:
            # Fallback if somehow not provided
            _run_reconciliation_task(run_id, p_content, g_content)
        
        return RunResponse(run_id=run_id, status="queued", message="Job dispatched successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs/{run_id}")
async def get_run(run_id: str, current_user: dict = Depends(require_auditor)):
    if run_id not in _runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
    return _runs_store[run_id]

from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/export/{run_id}")
async def export_run_csv(run_id: str, current_user: dict = Depends(require_auditor)):
    if run_id not in _runs_store:
        raise HTTPException(status_code=404, detail="Run not found")
        
    run_data = _runs_store[run_id]
    if run_data.get("status") != "success":
        raise HTTPException(status_code=400, detail="Run not completed yet")
        
    result = run_data.get("result", {})
    packets = result.get("packets", [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Packet ID", "Decision", "Polarity", "Missing PR Count", "Missing GST Count", 
        "PR Total", "GST Total", "Champion Confidence", "Challenger Confidence",
        "AI Decision", "Reason Codes", "Dataset Version"
    ])
    
    # Write rows
    for p in packets:
        decision = p.get("decision", "UNKNOWN")
        polarity = p.get("polarity", "NONE")
        missing_pr = len(p.get("missing_evidence", {}).get("missing_in_pr", []))
        missing_gst = len(p.get("missing_evidence", {}).get("missing_in_gstr2b", []))
        
        pr_total = sum(float(r.get("amount", 0)) for r in p.get("purchase_records", []))
        gst_total = sum(float(r.get("amount", 0)) for r in p.get("gst_records", []))
        
        ai_prov = p.get("ai_provenance", {})
        champ_conf = ai_prov.get("confidence", 0)
        chall_conf = ai_prov.get("challenger_confidence", 0)
        ai_decision = ai_prov.get("decision", "UNKNOWN")
        
        reason_codes = []
        if champ_conf >= 0.95:
            reason_codes.append("HIGH_CONFIDENCE_MATCH")
        elif champ_conf < 0.70:
            reason_codes.append("LOW_CONFIDENCE_REJECT")
        else:
            reason_codes.append("AMBIGUOUS_SCORE_REVIEW")
            
        dataset_version = "v1-ai-prod"
        
        writer.writerow([
            p.get("packet_id"), decision, polarity, missing_pr, missing_gst,
            pr_total, gst_total, champ_conf, chall_conf,
            ai_decision, "|".join(reason_codes), dataset_version
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=recongraph_audit_{run_id}.csv"}
    )

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest, current_user: dict = Depends(require_auditor)):
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
