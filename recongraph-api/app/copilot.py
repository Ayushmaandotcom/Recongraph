"""Enterprise GST Copilot API — the intelligence layer of ReconGraph.

Routes queries through:
  QueryRouter → Hybrid RAG / ReconGraph Tools → Context Builder → Response Generator

Features:
  - Hybrid retrieval (vector + BM25 + reranking)
  - Query classification (SIMPLE / GST_KNOWLEDGE / RECONCILIATION / COMPLEX)
  - Retrieval confidence scoring with abstention
  - Structured citations with document metadata
  - Tenant-scoped access to reconciliation data
  - Full audit logging
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from recongraph.learning.rag import get_rag_pipeline
from recongraph.learning.query_router import classify_query, QueryType
from recongraph.learning.confidence import compute_confidence, should_abstain
from recongraph.learning.context_builder import build_context
from recongraph.learning.llm_provider import get_llm_provider, StructuredResponse
from recongraph.learning.copilot_tools import (
    get_decision_trace, get_invoice_details, get_run_summary, get_supplier_history
)
from recongraph.learning.copilot_audit import (
    CopilotAuditLog, log_copilot_request, generate_request_id
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


# --- Request / Response Models ---

class ConversationMessage(BaseModel):
    role: str  # "user" or "copilot"
    content: str

class CopilotQuery(BaseModel):
    query: str
    run_id: Optional[str] = None
    packet_id: Optional[str] = None
    conversation_history: Optional[List[ConversationMessage]] = None

class StructuredCitation(BaseModel):
    document_id: str = ""
    section: str = ""
    source: str = ""
    text: str = ""
    effective_date: str = ""
    document_type: str = ""

class ConfidenceResponse(BaseModel):
    level: str
    overall: float
    retrieval_score: float = 0.0
    source_authority: str = ""

class CopilotResponse(BaseModel):
    answer: str
    citations: List[StructuredCitation]
    confidence: ConfidenceResponse
    abstained: bool
    query_type: str
    request_id: str


# --- Endpoint ---

@router.post("/ask", response_model=CopilotResponse)
async def ask_copilot(query: CopilotQuery):
    request_id = generate_request_id()
    audit = CopilotAuditLog(request_id=request_id, query=query.query)

    try:
        t_start = time.time()

        # 1. Classify the query
        has_recon_context = bool(query.run_id or query.packet_id)
        query_type = classify_query(query.query, has_recon_context=has_recon_context)
        audit.query_type = query_type.value

        # 2. Handle SIMPLE queries
        if query_type == QueryType.SIMPLE:
            answer = _handle_simple_query(query)
            audit.answer_length = len(answer)
            log_copilot_request(audit)
            return CopilotResponse(
                answer=answer,
                citations=[],
                confidence=ConfidenceResponse(level="HIGH", overall=1.0),
                abstained=False,
                query_type=query_type.value,
                request_id=request_id,
            )

        # 3. Retrieve GST knowledge (for GST_KNOWLEDGE, RECONCILIATION, COMPLEX)
        t_retrieval = time.time()
        pipeline = get_rag_pipeline()

        try:
            results = pipeline.search_hybrid(query.query, limit=5)
            reranker_used = True
        except (AttributeError, Exception):
            # Fallback to basic search if hybrid isn't available
            results = pipeline.search(query.query, limit=5)
            reranker_used = False

        audit.retrieval_latency_ms = (time.time() - t_retrieval) * 1000
        audit.retrieved_document_ids = [
            r.get("metadata", {}).get("document_id", "") for r in results
        ]
        audit.retrieval_scores = [r.get("score", 0.0) for r in results]

        # 4. Compute confidence
        confidence = compute_confidence(results, reranker_used=reranker_used)
        audit.confidence_level = confidence.level
        abstained = should_abstain(confidence)
        audit.abstained = abstained

        # 5. Gather reconciliation context (for RECONCILIATION and COMPLEX)
        recon_context = None
        supplier_context = None

        if query_type in (QueryType.RECONCILIATION, QueryType.COMPLEX):
            if query.run_id and query.packet_id:
                recon_context = get_decision_trace(query.run_id, query.packet_id)
            elif query.run_id:
                recon_context = get_run_summary(query.run_id)

            # Extract GSTIN from recon context for supplier intelligence
            if recon_context and not recon_context.get("error"):
                gstins = set()
                for side in ["purchases", "gsts"]:
                    for r in recon_context.get(side, []):
                        gstin = r.get("tax_identity")
                        if gstin:
                            gstins.add(gstin)
                if gstins:
                    supplier_context = get_supplier_history(list(gstins)[0])

        # 6. Build context and generate response
        conversation_history = None
        if query.conversation_history:
            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in query.conversation_history[-5:]
            ]

        prompt_context = build_context(
            query=query.query,
            retrieved_documents=results,
            recon_context=recon_context,
            supplier_context=supplier_context,
            conversation_history=conversation_history,
        )

        llm = get_llm_provider("gemini")
        
        if abstained:
            answer = (
                "I don't have sufficient authoritative information to answer this "
                "question confidently. Please consult the official GST portal or a "
                "qualified tax professional for guidance on this specific matter."
            )
        else:
            structured_resp = llm.generate_structured(
                prompt=prompt_context,
                response_model=StructuredResponse,
                temperature=0.1
            )
            answer = structured_resp.answer

        # 7. Build structured citations
        citations = []
        for r in results:
            meta = r.get("metadata", {})
            citations.append(StructuredCitation(
                document_id=meta.get("document_id", ""),
                section=meta.get("section", ""),
                source=meta.get("source", ""),
                text=r.get("text", "")[:500],  # Truncate for response size
                effective_date=meta.get("effective_from", ""),
                document_type=meta.get("document_type", ""),
            ))

        audit.citation_count = len(citations)
        audit.answer_length = len(answer)
        audit.llm_latency_ms = (time.time() - t_start) * 1000 - audit.retrieval_latency_ms

        log_copilot_request(audit)

        return CopilotResponse(
            answer=answer,
            citations=citations,
            confidence=ConfidenceResponse(
                level=confidence.level,
                overall=round(confidence.overall, 4),
                retrieval_score=round(confidence.retrieval_score, 4),
                source_authority=confidence.source_authority,
            ),
            abstained=abstained,
            query_type=query_type.value,
            request_id=request_id,
        )

    except Exception as e:
        audit.error = str(e)
        log_copilot_request(audit)
        raise HTTPException(status_code=500, detail=f"Copilot error: {str(e)}")


def _handle_simple_query(query: CopilotQuery) -> str:
    """Handle simple deterministic queries without RAG or LLM."""
    q = query.query.lower().strip()

    if query.run_id:
        summary = get_run_summary(query.run_id)
        if not summary.get("error"):
            if "how many" in q and ("invoice" in q or "record" in q):
                return f"This run processed {summary.get('total_packets', 0)} total packets."
            if "match" in q and "rate" in q:
                return f"Auto-match rate: {summary.get('auto_match_rate', 'N/A')}"
            # Generic summary
            return (
                f"Run summary: {summary.get('auto_matches', 0)} auto-matches, "
                f"{summary.get('review_packets', 0)} review packets, "
                f"engine version {summary.get('engine_version', 'N/A')}."
            )

    return "I can help with that! Please provide a run ID for specific data queries, or ask me about GST rules and reconciliation concepts."
