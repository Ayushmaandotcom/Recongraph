# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-27

### Added
- **Core Engine**: Fully deterministic `ReconGraphEngine` for reconciling $N:M$ relationships between `PurchaseRecord` and `GSTRecord` instances.
- **Evidence Graph**: Automated generation of Bipartite Candidate Graphs grouping identical entities using configurable `tax_identity` blockers.
- **Semantic Propagation**: Support for canonical mappings across Tax, Temporal, Financial, and Reference domains.
- **Universal Reliability Framework**: Replaces opaque similarity scores by wrapping parsed fields in a `ReliabilityEnvelope`. Allows any observation source (OCR, LLMs, barcodes, manual entry) to declare its uncertainty declaratively.
- **Explainability Layer**: Extracts cryptographically stable `DecisionTrace`s into human-readable `ExplanationArtifact`s for auditing and compliance.
- **Review Protocol**: `ReviewPacketBuilder` for capturing sparse/conflicting data, including direct highlighting for OCR extraction errors.

### Changed
- Refactored `HypothesisEvaluator` into an orchestration-only layer that delegates mathematically descriptive signal attenuation to the `DecisionPolicy`.

### Deprecated
- `OcrConfidenceReport` and `adapter.py` mapping functions are deprecated and will be removed in `v1.1.0`. All parser pipelines should emit `ReliabilityEnvelope` directly.
