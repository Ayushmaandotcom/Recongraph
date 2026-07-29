# ReconGraph: V2 Research Roadmap & Vision

> **ReconGraph does not ask "How similar are these records?" It asks "What independent evidence exists about the relationship between these records, how was that evidence produced, and what conclusions does it legitimately support?"**

### Core Design Principles for V2
Before writing the first line of V2 code, evaluate every proposed feature against one question: *Is this producing a new observation, a new interpretation, or is it prematurely making a decision?*

1. **Observations are facts; assertions are interpretations.**
2. **Every semantic conclusion must carry reproducible provenance.**
3. **Fusion is the only place where independent evidence becomes a decision.**

---

## Current State: ReconGraph V1 (Core)
ReconGraph V1 is the foundational production reconciliation engine. It successfully shifted the design philosophy from arbitrary fuzzy scoring to a true reasoning pipeline.

**Maturity Assessment:**
- Mathematical Core: 10/10
- Reference Evidence, Graph Engine, Decision Engine, Explainability: 10/10
- Benchmark Framework & Synthetic Evaluation: 10/10
- UI & Documentation: 9.5/10

## The ReconGraph Research Vision (Next 12–18 Months)

To evolve from a deterministic reconciliation engine into an **Evidence Reasoning Platform**, the roadmap is divided into 12 strategic tiers.

### Tier 1 — Core V2 (Highest Priority)
- **Typed assertions everywhere** (remove remaining scalar evidence)
- **Vendor Identity Pipeline**
- **Semantic Evidence Engine** (LLM/embeddings)
- **Evidence Fusion Engine**
- **Confidence Calibration**

### Tier 2 — Advanced AI/NLP
- **Semantic Business Purpose:** `Observation → Business Purpose → Assertion: same_business_purpose`.
- **Multilingual Support:** Embeddings, detection, and translation provenance (English, Hindi, German, etc.).
- **OCR Evidence:** PDF → OCR → Observation → Confidence → Assertion.
- **Document Layout Understanding:** Invoice number, vendor, taxes, stamps, QR codes.
- **Table Understanding:** Structured extraction with provenance.

### Tier 3 — Financial Intelligence
- **Tax Reasoning:** IGST, CGST, SGST, CESS, reverse charge, exemptions.
- **Currency Engine:** Exchange rates, forex, tolerance windows.
- **Temporal Reasoning:** Reason over timelines (Purchase Jan 10 → Invoice Jan 15 → Payment Feb 2).
- **Payment Intelligence:** Partial, split, advance payments, credit/debit notes.
- **Ledger Semantics:** Accounting behavior.

### Tier 4 — Graph Intelligence
- **Supplier Graph:** Supplier → Parent → Subsidiary → GST registrations → Branches.
- **Organization Graph:** Employees, vendors, banks, tax entities, contracts.
- **Event Graph:** Business events as first-class entities.

### Tier 5 — Learning
- **Calibration over Rules:** System learns calibration from human feedback without changing deterministic reasoning.
- **Ambiguity Measurement:** System measures ambiguity through reviewer disagreement.

### Tier 6 — Explainability++
- **Interactive Evidence Graph:** Decision → Evidence → Observations → Source → Artifacts (functioning like a debugger).

### Tier 7 — Knowledge Retrieval
- **Connected Ecosystem:** Vendor → GST Portal → MCA → Sanctions → Internal ERP → Contracts → Bank.

### Tier 8 — Performance
- **Scale:** Distributed execution, artifact caching, semantic cache, GPU embeddings, incremental graph updates.

### Tier 9 — Benchmarking
- **Real-World Benchmark:** Thousands of real invoices, ground truth, and leaderboards to compare ReconGraph against LLMs and commercial tools.

### Tier 10 — Enterprise Features
- **Operations:** RBAC, Audit logs, SaaS deployment, Multi-tenancy, Monitoring, Data retention.

### Tier 11 — Research Papers
- Evidence-Centric Financial Reconciliation
- Provenance-aware Evidence Assertions
- Deterministic Graph-based Reconciliation
- Synthetic Benchmark for Financial Reconciliation
- Correlation-aware Evidence Fusion
- Calibration of Financial Matching Systems
- Semantic Business Purpose Reasoning
- Knowledge Graphs for Financial Audit

### Tier 12 — "Dream Version"
```text
          ERP
           │
Purchase Orders & Vendor Master & GST Portal & Invoice PDFs
           │
   OCR Observations
           │
Semantic Evidence Engine & Vendor Identity Engine & Tax Identity Engine & Temporal Reasoning
           │
   Graph Construction
           │
    Evidence Fusion
           │
      Calibration
           │
       Decision
           │
 Interactive Explanation
           │
      Human Review
           │
 Continuous Benchmarking
```

## The Top 5 Immediate Milestones
Before expanding into the outer tiers, these 5 milestones form the bedrock of V2:
1. **Complete the migration to typed evidence assertions** so every provider speaks the same semantic language.
2. **Implement the Vendor Identity Pipeline** with legal-entity, GST, PAN, and organization-core reasoning.
3. **Build the Semantic Evidence Engine** where embeddings become observations and evidence—not decisions.
4. **Design a principled Evidence Fusion Engine** that combines independent assertions while accounting for correlation, instead of simple weighted scoring.
5. **Add confidence calibration and human feedback** so the system's reported confidence is empirically meaningful and improves over time.
