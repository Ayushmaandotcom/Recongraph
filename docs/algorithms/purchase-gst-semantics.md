# Purchase-to-GST Relationship Semantics

## Purpose

Explain why primitive compatibility signals are insufficient to identify
the same financial event and define relationship-specific evidence
patterns for Purchase ↔ GST reconciliation.

## Baseline limitation

The v0.1 baseline uses a weighted average of entity, reference, amount,
temporal, and tax-identity signals.

Weighted averaging is compensatory: strong signals can offset severe
disagreement in another signal.

Challenge Dataset v1 exposed cases where this behaviour conflicts with
financial-event identity.

## Design principle

Primitive signals measure evidence.

Relationship semantics interpret combinations of evidence.

Semantic findings identify evidence patterns but do not, by themselves,
define production match decisions.

## Semantic finding PG-001: Severe amount conflict

### Motivation

HN001 scored 0.6957 despite a 100% amount mismatch because entity,
reference, temporal, and tax-identity evidence remained strong.

### Evidence pattern

- amount score is 0.0
- reference evidence is strong
- tax identity agrees

### Interpretation

The records exhibit strong identity evidence while their monetary values
are fundamentally incompatible under the current 1:1 Purchase ↔ GST
hypothesis.

### Finding

`severe_amount_conflict`

### Open question

Should this finding apply a contradiction penalty, trigger a hard gate,
or route the pair to review?

## Semantic finding PG-002: Distinct event identity evidence

### Motivation

HN003 scored 0.7000 for separate monthly invoices because entity, amount,
and tax identity matched exactly.

### Evidence pattern

- entity evidence is strong
- amount evidence is strong
- tax identity agrees
- reference score is 0.0
- temporal score is 0.0

### Interpretation

The records appear to involve the same legal entity and transaction
shape, but reference and temporal evidence indicate distinct financial
events.

### Finding

`distinct_event_identity_evidence`

### Open question

Should this finding reduce compatibility or act as a non-compensatory
event-identity gate?

## Existing tax identity contradiction

The v0.1 policy already treats an explicit tax-identity mismatch as a
contradiction and applies a multiplicative penalty.

HN002 demonstrated that this mechanism suppresses a highly compatible
surface-level pair.

The semantic layer should expose this condition as:

`tax_identity_conflict`

The scoring consequence may initially remain in RelationshipPolicy.

## Out-of-scope findings

### Weak numeric reference collision

HN004 exposed a primitive reference-scoring issue. The semantic layer
should not repair incorrect primitive evidence.

### Group relationship required

HN005 exposed a relationship-cardinality limitation. Pair semantics
cannot prove a 1:N reconciliation hypothesis.

## Challenge traceability

| Finding | Challenge case | Failure category |
|---|---|---|
| severe_amount_conflict | HN001 | relationship semantics |
| tax_identity_conflict | HN002 | relationship semantics |
| distinct_event_identity_evidence | HN003 | relationship semantics |
| weak numeric reference collision | HN004 | primitive scoring |
| group relationship required | HN005 | relationship cardinality |

## Detection before consequence

Semantic findings are initially observational.

`analyze_purchase_gst_semantics()` detects evidence patterns and returns
structured findings without changing pair compatibility scores.

This separation allows the challenge dataset to validate semantic
detection independently from the later policy decision of whether a
finding should apply a penalty, trigger a gate, or route a pair to
review.

## Initial semantic thresholds

The v0.1 semantic detector uses:

- strong reference evidence: score >= 0.8
- strong entity evidence: score >= 0.9
- strong amount evidence: score >= 0.9

These thresholds are rule semantics, not calibrated probabilities.

The severe amount conflict currently requires an amount score exactly
equal to 0.0. This preserves the first challenge-derived rule without
introducing an untested near-zero threshold.
