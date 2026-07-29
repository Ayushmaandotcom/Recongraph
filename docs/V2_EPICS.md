# ReconGraph V2: Research Platform Epics

With the successful certification and release of **ReconGraph v1.0.0**, the project transitions from building core features to evolving a research-grade reasoning platform. 

Before diving into these epics, V2 will begin with an **Architecture Freeze Milestone** to explicitly declare stable contracts for:
- Claim semantics & Scope semantics
- Evidence assertion model
- Identity and provenance model
- Plugin interfaces
- Serialization contracts
- Backward-compatibility expectations

Once the foundation is frozen, the following epics define the V2 roadmap:

## Epic 1: Evidence Kernel Migration
*The first engineering priority of V2.*
Replace every remaining scalar evidence output with typed assertions. Every new subsystem (vendor identity, semantic evidence, temporal reasoning, tax reasoning) must emit the exact same language:
`Observation` → `Interpretation` → `EvidenceAssertion` → `Fusion` → `Decision`.

## Epic 2: Vendor Identity Pipeline
Evolve vendor matching from fuzzy names to true legal identity, incorporating corporate hierarchy, parent companies, GST registrations, PAN extraction, and registry evidence.

## Epic 3: Semantic Evidence Engine
Move beyond embeddings to typed semantic observations: business purpose, procurement intent, expense class, and service category assertions.

## Epic 4: Correlation-Aware Evidence Fusion
Transition from simple linear scalar addition to principled evidence-combination frameworks (e.g., belief theory, Bayesian networks) that question and model the true independence of signals.

## Epic 5: Calibration Framework
Evolve the engine's output from arbitrary confidence scores (`score = 0.95`) to true calibrated probabilities (`P(correct match) = 0.95`).
