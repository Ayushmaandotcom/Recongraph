# Scope Kind Construction Decision

## Context
When constructing an evidence scope (now called `PropositionSubject`), the kernel needs to know the formal `ScopeKind` (e.g. `RECORD_PAIR`, `GROUP_PAIR`). Should the kernel infer this from the cardinality of the provided subjects, or should the caller explicitly provide it?

## Decision
**The caller must explicitly provide the `ScopeKind` during construction.**

## Rationale
Semantic intent should not be guessed from cardinality. If a caller provides exactly one subject on the left and one on the right, cardinality alone cannot distinguish between:
* A `RECORD_PAIR` representing a 1:1 match.
* A `GROUP_PAIR` representing a group reconciliation that currently happens to contain only a single record on each side.

By forcing explicit `ScopeKind` construction (e.g., `PropositionSubject.create(claim, ScopeKind.GROUP_PAIR, left, right)`), the kernel avoids silently misclassifying the evidence and strictly validates whether the provided subjects satisfy the invariant rules for that explicit kind.
