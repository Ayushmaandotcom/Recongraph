# Architecture Decision Record (ADR) Index

This index tracks key architectural decisions and "negative decisions" (what we explicitly chose *not* to do) to prevent architectural regression during the V2 research phase. 

This establishes the **Architecture Freeze Milestone**, explicitly declaring stable contracts for the core engine.

## 1. Core V2 Semantic Contracts

### ADR-001: Separation of Observation, Interpretation, and Assertion
- **Context**: V1 originally collapsed evidence extraction and scoring into a single scalar float (`contrib.score`).
- **Decision**: ReconGraph strictly separates observations (immutable facts), interpretations (domain-specific meaning), and assertions (formalized claims). 
- **Negative Decision**: We will *never* introduce a provider that skips interpretation and directly emits a scalar score. LLM plugins must emit typed assertions, not raw similarity scores.

### ADR-002: Kernel Claims over Domain Silos
- **Context**: Every domain (tax, vendor, financial) needs to communicate evidence to the Fusion Engine.
- **Decision**: All plugins must emit `EvidenceAssertion` instances based on a shared vocabulary of `ClaimId`s defined in the V2 Evidence Kernel (e.g., `SAME_ECONOMIC_ENTITY`, `SAME_BUSINESS_PURPOSE`). 
- **Negative Decision**: The Fusion Engine will *not* contain domain-specific logic. It only understands kernel claims.

### ADR-003: Independence of Provenance and Identity
- **Context**: Tracing the origin of evidence is critical for explainability and adversarial evaluation.
- **Decision**: All observations and assertions must carry cryptographic Identity and Ancestry profiles (`KernelIdentityRef`, `EvidenceAncestryRef`). 
- **Negative Decision**: We will *never* flatten or discard provenance information for short-term performance gains.

### ADR-004: Evidence Fusion Replaces Linear Weighting
- **Context**: V1 used a primitive weighted sum (linear addition) for final decision making (`calculate_relationship_score`).
- **Decision**: The V2 Decision Engine will fuse evidence using principled probabilistic or structural models (e.g., Dempster-Shafer, Bayesian Belief Networks) that model the correlation and true independence of signals. 
- **Negative Decision**: We will *not* add "more weights" to fix false positives. We will address false positives by modeling signal dependence.

### ADR-005: Backward-Compatibility Guarantee
- **Context**: V1 users rely on the existing JSON serialization and `ReconGraphEngine.reconcile` API.
- **Decision**: V2 will introduce new capabilities (Shadow Mode, Fusion Engine) gracefully. The V1 pipeline structure and data dictionary schemas remain strictly backward-compatible unless deprecated over a full major version cycle.

## 2. Active ADRs

### ADR-006: Dempster-Shafer for Belief Fusion
- **Context**: V2 requires fusing multiple assertions (Support vs. Conflict) while properly accounting for the system's "Ignorance" (uncertainty) when evidence is sparse.
- **Decision**: Implemented the Dempster-Shafer Theory of Evidence (`MassFunction`) to manage Belief and Plausibility across mutually exclusive propositions (Match, No Match).
- **Negative Decision**: We will *not* use naive Bayesian networks for fusion because they require full prior probability distributions that we lack in zero-shot reconciliation scenarios.

### ADR-007: Semantic Propagation
- **Context**: Evidence assertions depend on each other. For example, a TAX match assertion is logically meaningless if the VENDOR identities strongly contradict.
- **Decision**: Implemented a `SemanticPropagator` that evaluates assertions topographically. It automatically prunes, propagates, or invalidates evidence dynamically based on upstream support or contradictions.
- **Negative Decision**: We will *never* place "if vendor match then score tax" rules inside the evidence providers. Providers simply emit what they observe, and the global graph handles semantic dependencies.

### ADR-008: Confidence Calibration (Stage 8K)
- **Context**: Different algorithms (e.g., lexical TF-IDF vs. embedding similarity) output raw magnitudes that are incomparable and do not reflect true empirical probabilities.
- **Decision**: Introduced the `CalibrationEngine` to perform offline calibration of precision curves per-provider and per-claim. This converts raw magnitudes into rigorously calibrated probability masses.
- **Negative Decision**: The Dempster-Shafer engine will *never* accept raw, uncalibrated similarity scores as inputs. All assertions must pass through calibration mapping to ensure uniform semantic meaning.

*To be expanded as Epic 6 and beyond are implemented.*
