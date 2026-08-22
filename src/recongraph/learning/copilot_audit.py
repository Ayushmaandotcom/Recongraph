from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import logging
import uuid

logger = logging.getLogger('recongraph.copilot.audit')

@dataclass
class CopilotAuditLog:
    request_id: str
    tenant_id: str = ''
    user_id: str = ''
    query: str = ''
    query_type: str = ''  # SIMPLE, GST_KNOWLEDGE, RECONCILIATION, COMPLEX
    retrieval_latency_ms: float = 0.0
    retrieved_document_ids: list = field(default_factory=list)
    reranker_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    citation_count: int = 0
    retrieval_scores: list = field(default_factory=list)
    answer_length: int = 0
    abstained: bool = False
    confidence_level: str = ''
    error: str = ''
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def log_copilot_request(audit: CopilotAuditLog):
    """Write structured audit log entry."""
    logger.info(json.dumps(asdict(audit), default=str))

def generate_request_id() -> str:
    return str(uuid.uuid4())
