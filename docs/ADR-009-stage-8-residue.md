# ADR-009: Stage 8 Residue & Suspension

**Status:** Accepted (2026-07-29)
**Context:** ReconGraph V1 Certification

## Context
During the pre-V1 development cycle, an ambitious architectural expansion known as "Stage 8" was initiated. This stage aimed to introduce deep document reasoning, OCR confidence modeling, and a highly granular semantic "Kernel" for evidence derivation (`contrib/kernel`). 

However, aligning this deep knowledge graph architecture with the deterministic, rule-based V1 baseline proved destabilizing. The V2 fusion engine built on these concepts broke core invariant properties (e.g., matching distinct legal entities by allowing high similarity scores to outvote hard tax identity contradictions). 

To secure the V1 release, the V2 fusion pipeline and Stage 8 architecture were reverted and suspended.

## Decision
1. **Suspension of Stage 8 Modules:** The following namespaces are officially designated as "Stage 8 Residue" and are **suspended** from use in the core V1 pipeline:
   - `src/recongraph/contrib/kernel`
   - `src/recongraph/domain/ocr`
   - `src/recongraph/domain/document`
   - `src/recongraph/domain/reliability`

2. **Provenance Boundary Rule:** The core `ReconGraphEngine.reconcile()` path and the matching/scoring logic **must not** import from the suspended modules. 
   - *Exception:* The `convert_ocr_report_to_envelope` adapter in `domain.reliability` and the `BoundingBox` class may be used *exclusively* for formatting `ReviewPacket` outputs (highlighting low-confidence zones for the human review UI). They must not influence the `DecisionPolicy` or scoring logic.

3. **Codebase Preservation:** The suspended modules will remain in the repository (not deleted) to preserve the research and domain modeling work for a potential V3 architecture, but they are strictly isolated from V1 execution paths.

4. **Future V1 Refinements (Policy Guardrails):**
   - **Legal Form Blocking:** `LEGAL_FORM_LEXICAL_DIFFERENCE` currently routes a pair to manual review (as a member of `ONE_TO_ONE_BLOCKING_FINDINGS`) even if the tax identity (GSTIN) is structurally valid and perfectly matching. Future refinement will conditionally downgrade this finding to a non-blocking warning when `gstin_valid=True`, as same-GSTIN + different legal suffix is overwhelmingly data noise rather than distinct legal entities. For now, the over-conservative routing is preserved.

## Consequences
- The engine guarantees V1 stability and deterministic 1:1 matching.
- The UI review queue can still surface OCR layout highlighting without the engine depending on the complex `contrib/kernel` derivations.
- Future maintainers must respect the import boundary: any attempt to wire `contrib/kernel` into `core_providers.py` or `pair_scorers.py` violates V1 certification.
