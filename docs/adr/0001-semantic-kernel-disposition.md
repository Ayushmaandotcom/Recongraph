# ADR 0001: Disposition of the Semantic Kernel in V1

## Status
Accepted

## Context
During the evolution of ReconGraph, an extensive "Semantic Kernel" (found in `src/recongraph/contrib/kernel/`) was developed to provide an ontology-driven, strongly-typed epistemological framework for expressing identity, assertions, observations, and claims across financial records. 

However, as the graph engine evolved to support the V1 scale requirements (10,000 x 10,000 records dynamically evaluated), it became evident that materializing the full Semantic Kernel ontology for every pairwise comparison introduced unacceptable computational and memory overhead. The core traversal and evaluation logic (`HypothesisSearcher` and `HypothesisEvaluator`) needed to operate in under a millisecond per candidate. 

## Decision
1. **Delegation to Pluggable Providers**: The core `ReconGraphEngine` relies entirely on a flat, fast `EvidenceProvider` protocol. The core engine is mathematically ignorant of the Semantic Kernel.
2. **Quarantine of Kernel**: The Semantic Kernel remains in `src/recongraph/contrib/kernel/` but is **not** on the hot path for V1 automated reconciliation.
3. **Future Extension**: The Kernel is reserved for human-in-the-loop explanation generation (Stage 9) or batch offline analytics where the strict epistemological proof of *why* an edge exists is necessary, but it will not be materialized during the `reconcile` tight loop.
4. **V1 Types**: We rely on primitive sets (`frozenset[SemanticFinding]`), floats (`score`, `coverage`), and string URNs for graph resolution in V1, achieving a >1000x speedup compared to deep object instantiation.

## Consequences
- **Positive**: The engine can process a 10,000 x 10,000 matrix with 5% collisions in < 50 minutes (and sparse real-world data in seconds). Memory usage is capped.
- **Negative**: The `ReconciliationDecision` lacks the deep "Claim vs Observation" metaphysical trace out of the box, relying instead on a flatter `DecisionTrace` event log and basic `EvidenceSummary`.
- **Mitigation**: Explanations can be reconstructed lazily by passing the matched record IDs back into a Kernel-aware explainer component when a user clicks "Why did this match?" in the UI.
