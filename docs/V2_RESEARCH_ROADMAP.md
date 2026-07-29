# ReconGraph: V2 Research Roadmap & Vision

This document outlines the strategic transition of ReconGraph from a V1 deterministic production engine into a research-grade platform. The focus shifts from feature construction to evolving the core evidence pipeline: **Observation → Interpretation → Assertion → Fusion → Decision**.

## The Real Reasoning Pipeline
ReconGraph V1 replaced the traditional "Fuzzy Matching → Threshold" approach with a true deterministic reasoning pipeline:

```text
ERP Data & GST Data
        ▼
Observation Layer
        ▼
Evidence Layer
        ▼
Interpretation Layer
        ▼
Graph Construction
        ▼
Connected Components
        ▼
Hypothesis Search
        ▼
Hypothesis Evaluation
        ▼
Decision Engine
        ▼
Explanation Builder
        ▼
Decision Trace
        ▼
Human Review & Feedback
```

## The 10 Phases of ReconGraph Research

### Phase 1: Vendor Identity
Moving beyond fuzzy names to true legal identity:
- Corporate hierarchy and parent companies.
- GST registrations and PAN extraction.
- Registry evidence and authority reasoning.

### Phase 2: Semantic Evidence
Moving beyond embeddings to typed semantic observations:
- Business purpose and procurement intent.
- Expense class and service category.
- Semantic assertions.

### Phase 3: Evidence Fusion
Addressing evidence independence and principled combination:
- Belief theory.
- Bayesian networks.
- Correlation-aware evidence fusion.

### Phase 4: Calibration
Moving from absolute scores to probabilities:
- From `score = 0.95` to `P(correct match) = 0.95`.

### Phase 5: Learning
Feedback loops without compromising deterministic reasoning:
- Human Review → Feedback → Calibration → Benchmark → Synthetic Generator → Regression Tests.

### Phase 6: Multi-modal Observations
Expanding the input space:
- Invoice PDFs, Images, Tables.
- Handwriting, Logos, QR codes, Signatures.

### Phase 7: Knowledge Graph
Building a complete business event graph:
- Supplier → Purchase Orders → Invoices → Payments → GST → Contracts → Shipments → Bank → Emails → Approvals.

### Phase 8: Distributed Reasoning
Scaling from thousands to millions of records.

### Phase 9: Self-evaluation
Answering "How confident am I that I'm correct?" proactively before human intervention.

### Phase 10: Research Publications
Publishable themes embedded in the architecture:
1. Graph-based deterministic financial reconciliation.
2. Evidence-centric reconciliation architecture.
3. Explainable reconciliation using semantic evidence assertions.
4. Benchmarking framework for financial reconciliation systems.
5. Synthetic adversarial datasets for reconciliation.
6. Evidence lineage and provenance for deterministic AI.
7. Correlation-aware evidence fusion.
8. Calibration of deterministic reconciliation confidence.

## Immediate Priorities (Next 6 Months)

1. **Replace every remaining scalar evidence output with typed assertions:** Finish the transition (started with K6) so every evidence source speaks the same semantic language.
2. **Formalize the Evidence Kernel:** Treat it as the heart of ReconGraph. Future evidence providers plug into it without changing core reasoning.
3. **Build a true evaluation lab:** Track precision, recall, calibration, latency, ambiguity rates, evidence conflicts, and regression across versions (beyond pass/fail).
4. **Add observability:** Include pipeline visualizations, evidence graphs, timing breakdowns, and decision provenance.
5. **Expand production readiness:** Persistence, version migrations, distributed execution, incremental corpus updates, multi-tenant support, and operational monitoring.

## Design Philosophy Constraint
Every new subsystem MUST satisfy at least one of these criteria; otherwise, it belongs in an experiment, not the production engine:
- Increases correctness.
- Increases explainability.
- Increases scalability.
- Increases reproducibility.
- Enables future research cleanly.
