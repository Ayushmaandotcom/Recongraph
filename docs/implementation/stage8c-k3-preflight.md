# Stage 8C K3 Preflight Audit

## K1/K2 Closure Review

### Public Construction APIs
* **ClaimId:** `ClaimId(value: str)`
* **ClaimSemanticVersion:** `ClaimSemanticVersion(value: int)`
* **ClaimDescriptor:** `ClaimDescriptor(claim_id, semantic_version, symmetry, allowed_scope_kinds)`
* **ClaimSymmetry:** `ClaimSymmetry.SYMMETRIC` / `ClaimSymmetry.DIRECTIONAL`
* **ScopeKind:** `ScopeKind.RECORD`, `ScopeKind.RECORD_PAIR`, `ScopeKind.GROUP`, `ScopeKind.GROUP_PAIR`, `ScopeKind.HYPOTHESIS`, `ScopeKind.COMPONENT`
* **SubjectRef:** `SubjectRef(urn: str)`
* **PropositionSubject:** `PropositionSubject.create(claim_descriptor, kind, left, right)`

### Current Conventions
* **K1/K2 package location:** `src/recongraph/domain/claims.py` and `src/recongraph/domain/scopes.py`
* **Current domain primitive dependency direction:** Bottom-up. Primitives depend only on standard library.
* **Current serialization convention:** Explicit `.to_dict()` methods on domain objects returning simple Python dicts/primitives.
* **Current validation style:** `__post_init__` within `dataclass(frozen=True)` or explicit static factory methods like `create()`.
* **Current custom exception style:** Raising built-in `ValueError` or `TypeError` with structured error codes (e.g. "SC-001 Violation: ...").
* **Current immutable collection style:** Built-in `frozenset` and `tuple`.
* **Current stable URN representation:** String URNs inside `SubjectRef(urn=...)`.
* **Current record identity representation:** Handled by graph builder, domain only knows URNs.

### K3 Architecture
* **Recommended K3 module location:** `src/recongraph/domain/observations.py`
* **Expected import dependencies:** 
  - `src/recongraph/domain/scopes.py` (for `SubjectRef`)
* **Expected import-cycle risks:** Low. Observations depend on SubjectRef but not on semantic Claims or Scopes. Claims and Scopes do not need to import Observations. The dependency graph remains clean.
