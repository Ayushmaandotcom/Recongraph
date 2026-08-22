# ReconGraph AI Architecture

This document outlines the Phase 9/10 Production AI Architecture for ReconGraph, focusing on how we hardened the AI reconciliation engine for enterprise deployment.

## 1. LLM Abstraction & Structured Output (Stage 2 & 3)
We introduced an `LLMProvider` protocol (`src/recongraph/learning/llm_provider.py`) to abstract away the specific LLM implementation (e.g., Gemini, OpenAI, Anthropic). We use strict Pydantic schemas (`StructuredResponse`, `AnswerClaims`, `Citation`) to guarantee structured communication and prevent prompt injection or format drift.

## 2. Grounded Claim & Citation Architecture (Stage 4)
We implemented citation validation in `src/recongraph/learning/grounding.py`. This ensures every claim made by the AI maps back strictly to a document retrieved from the knowledge base, preventing hallucinations. Unverified citations are flagged, allowing the system to handle risk appropriately.

## 3. Knowledge-Base Provenance & Versioning (Stage 5)
In `src/recongraph/learning/knowledge_base.py`, we added document hashing and retrieval dates. This guarantees traceability: we know exactly which version of a GST rule or circular was used to justify a reconciliation decision.

## 4. Temporal Validation (Stage 6)
Rules change over time. We implemented temporal awareness (`test_temporal_rag.py`) so the AI retrieves the version of the rule active on the invoice date, avoiding retroactive application of new rules.

## 5. Retrieval Benchmarking (Stage 7-9)
We built an automated benchmark suite (`scripts/benchmark_retrieval.py` and `tests/data/rag_benchmark.json`) to continuously evaluate Recall@5 and Mean Reciprocal Rank (MRR@5) for GST queries, ensuring search quality remains high.

## 6. Confidence Calibration & Circuit Breaking (Stage 10, 13, 14)
We introduced explicit confidence states (HIGH, MEDIUM, LOW, INSUFFICIENT) and implemented a `CircuitBreaker` (`circuit_breaker.py`) to halt AI operations safely if external APIs (like the embedding model or LLM) begin failing continuously.

## 7. Tenant Isolation (Stage 11 & 12)
We updated `copilot_tools.py` to strictly validate `tenant_id` on all reconciliation tool calls. The AI operates within a sandboxed context and cannot access cross-tenant data.

## 8. Latency, Load Testing, and Cost Tracking (Stage 15 & 16)
We implemented a load testing script (`scripts/load_test_copilot.py`) and updated `CopilotAuditLog` to track token usage and estimated costs, providing complete financial observability for the AI pipeline.

## 9. Next Steps
- Production End-to-End Report
- Setup CI/CD for ongoing benchmark execution
