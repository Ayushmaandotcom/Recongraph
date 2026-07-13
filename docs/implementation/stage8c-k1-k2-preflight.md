# Stage 8C K1-K2 Preflight Audit

## Current Architecture State
* **Current node identity type:** `NodeID` is an alias for `str` in `src/recongraph/graph/candidate.py`.
* **Current URN construction location:** `build_purchase_urn(record_id: str)` and `build_gst_urn(record_id: str)` in `src/recongraph/graph/candidate.py`.
* **Current Hypothesis identity semantics:** Hypothesis identity is mostly driven by object instances or explicitly constructed edge sets, not stable semantic identifiers.
* **Existing evidence primitive locations:**
  - `src/recongraph/plugins/provider.py`, `src/recongraph/plugins/provider_v2.py`
  - `src/recongraph/plugins/core_providers.py`
  - `src/recongraph/domain/financial/pipeline.py` (has `EvaluatedFinancialEvidence`, `EvidenceContributionV2`)
* **Existing plugin protocol locations:** `src/recongraph/plugins/`
* **Likely import-cycle risks:** The new semantic claims and scopes must live in `src/recongraph/domain/` (e.g., `semantic.py` or `claims.py` / `scopes.py`). If `src/recongraph/domain/semantic.py` imports anything from `src/recongraph/plugins/` or `src/recongraph/graph/`, it will create cycles. `SubjectRef` might be tempted to import `PurchaseRecord`, which we must avoid.

## Implementation Placement
* **Recommended package location:** `src/recongraph/domain/semantic.py` (or `src/recongraph/domain/claims.py` and `src/recongraph/domain/scopes.py`). We will use:
  - `src/recongraph/domain/claims.py` (ClaimId, ClaimSemanticVersion, ClaimSymmetry, ClaimDescriptor)
  - `src/recongraph/domain/scopes.py` (ScopeKind, SubjectRef, PropositionSubject)
* **Files expected to be created:**
  - `src/recongraph/domain/claims.py`
  - `src/recongraph/domain/scopes.py`
  - `tests/test_claim_semantics.py`
  - `tests/test_evidence_scope.py`
  - `docs/architecture/core-claim-catalog-v1.md`
  - `docs/architecture/scope-kind-construction-decision.md`
  - `docs/architecture/unknown-claim-kernel-boundary.md`
* **Files expected to be modified:**
  - `docs/architecture/open-questions.md`

## Construction Decision
We will use `PropositionSubject` instead of `EvidenceScope` because it is conceptually cleaner as the arguments to the semantic predicate (the Claim). It will expose a factory `PropositionSubject.create(...)` to explicitly enforce claim-aware symmetric canonicalization during construction. SubjectRef will hold a simple `urn: str` rather than generic domain objects, maintaining strict boundary hygiene.
