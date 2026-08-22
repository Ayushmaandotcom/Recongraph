"""Retrieval confidence scoring and abstention logic for the GST Copilot."""

from dataclasses import dataclass
from typing import List, Dict, Any


# Authority hierarchy: higher authority = more trustworthy
AUTHORITY_WEIGHTS = {
    "ACT": 1.0,
    "RULE": 0.9,
    "NOTIFICATION": 0.8,
    "CIRCULAR": 0.75,
    "GUIDANCE": 0.6,
    "PRECEDENT": 0.5,
    "INTERNAL": 0.4,
}

# Abstention threshold
ABSTENTION_THRESHOLD = 0.35


@dataclass
class RetrievalConfidence:
    """Composite confidence score for a Copilot retrieval + response."""

    retrieval_score: float      # avg vector/hybrid similarity (0-1)
    reranker_score: float       # cross-encoder relevance (0-1), 0 if no reranker
    source_authority: str       # highest authority level among sources
    source_recency: float       # 0-1 based on how recent the source is
    context_completeness: float  # fraction of query aspects covered (heuristic)
    overall: float              # weighted composite
    level: str                  # HIGH / MEDIUM / LOW / INSUFFICIENT

    def to_dict(self) -> dict:
        return {
            "retrieval_score": round(self.retrieval_score, 4),
            "reranker_score": round(self.reranker_score, 4),
            "source_authority": self.source_authority,
            "source_recency": round(self.source_recency, 4),
            "context_completeness": round(self.context_completeness, 4),
            "overall": round(self.overall, 4),
            "level": self.level,
        }


def _compute_recency_score(effective_from: str) -> float:
    """Score based on how recent the source is (1.0 = very recent, 0.0 = very old)."""
    from datetime import date

    if not effective_from:
        return 0.5  # unknown = neutral

    try:
        eff_date = date.fromisoformat(effective_from)
        days_old = (date.today() - eff_date).days
        if days_old < 0:
            return 1.0  # future-dated = very recent
        if days_old < 365:
            return 0.95
        if days_old < 730:
            return 0.85
        if days_old < 1825:  # 5 years
            return 0.7
        return 0.5
    except (ValueError, TypeError):
        return 0.5


def _compute_authority_score(document_type: str) -> float:
    """Score based on the authority level of the source document."""
    return AUTHORITY_WEIGHTS.get(document_type.upper(), 0.3)


def _classify_level(overall: float) -> str:
    """Map composite score to a human-readable confidence level."""
    if overall >= 0.75:
        return "HIGH"
    if overall >= 0.55:
        return "MEDIUM"
    if overall >= ABSTENTION_THRESHOLD:
        return "LOW"
    return "INSUFFICIENT"


def compute_confidence(
    retrieval_results: List[Dict[str, Any]],
    reranker_used: bool = False,
) -> RetrievalConfidence:
    """
    Compute a composite retrieval confidence from the search results.

    Each result dict should have:
      - 'score': float (vector or hybrid score)
      - 'reranker_score': float (optional)
      - 'metadata': dict with 'document_type', 'effective_from', 'source'
    """
    if not retrieval_results:
        return RetrievalConfidence(
            retrieval_score=0.0,
            reranker_score=0.0,
            source_authority="NONE",
            source_recency=0.0,
            context_completeness=0.0,
            overall=0.0,
            level="INSUFFICIENT",
        )

    # Retrieval score: average of top results
    retrieval_scores = [r.get("score", 0.0) for r in retrieval_results]
    avg_retrieval = sum(retrieval_scores) / len(retrieval_scores)

    # Reranker score: average of reranker scores if available
    if reranker_used:
        reranker_scores = [r.get("reranker_score", 0.0) for r in retrieval_results]
        avg_reranker = sum(reranker_scores) / len(reranker_scores) if reranker_scores else 0.0
    else:
        avg_reranker = 0.0

    # Source authority: take the highest
    authority_scores = []
    for r in retrieval_results:
        meta = r.get("metadata", {})
        doc_type = meta.get("document_type", "GUIDANCE")
        authority_scores.append(_compute_authority_score(doc_type))

    best_authority_score = max(authority_scores) if authority_scores else 0.3
    best_authority_type = "UNKNOWN"
    for r in retrieval_results:
        meta = r.get("metadata", {})
        doc_type = meta.get("document_type", "GUIDANCE")
        if _compute_authority_score(doc_type) == best_authority_score:
            best_authority_type = doc_type
            break

    # Source recency: average
    recency_scores = []
    for r in retrieval_results:
        meta = r.get("metadata", {})
        recency_scores.append(_compute_recency_score(meta.get("effective_from", "")))
    avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 0.5

    # Context completeness heuristic: based on number of unique sources
    unique_sources = set()
    for r in retrieval_results:
        meta = r.get("metadata", {})
        doc_id = meta.get("document_id", meta.get("section", ""))
        if doc_id:
            unique_sources.add(doc_id)
    completeness = min(len(unique_sources) / 3.0, 1.0)  # 3+ unique sources = full coverage

    # Weighted composite
    weights = {
        "retrieval": 0.30,
        "reranker": 0.25 if reranker_used else 0.0,
        "authority": 0.20,
        "recency": 0.10,
        "completeness": 0.15 if not reranker_used else 0.15,
    }
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        for k in weights:
            weights[k] /= total_weight

    overall = (
        weights["retrieval"] * avg_retrieval
        + weights["reranker"] * avg_reranker
        + weights["authority"] * best_authority_score
        + weights["recency"] * avg_recency
        + weights["completeness"] * completeness
    )

    level = _classify_level(overall)

    return RetrievalConfidence(
        retrieval_score=avg_retrieval,
        reranker_score=avg_reranker,
        source_authority=best_authority_type,
        source_recency=avg_recency,
        context_completeness=completeness,
        overall=overall,
        level=level,
    )


def should_abstain(confidence: RetrievalConfidence) -> bool:
    """Returns True if the Copilot should abstain from answering."""
    return confidence.overall < ABSTENTION_THRESHOLD
