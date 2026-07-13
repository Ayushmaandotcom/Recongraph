# Observation Kernel Metamorphic Properties

The K3 Observation Kernel must mathematically satisfy the following metamorphic properties. Any violation signifies a broken identity model or a conflation of orthogonal concepts.

| Property | Transformation | Invariant | Reason |
|---|---|---|---|
| **KOM-001** (Slot Stability) | Change observed value for the same source field | `ObservationSlot` remains identical | Slot identifies *where* the fact exists, independent of *what* it is. |
| **KOM-002** (Revision Distinction) | Change observed value for the same source field | `ObservationIdentity` changes | Distinguishes different occurrences (e.g. human correction). |
| **KOM-003** (Exact Reconstruction) | Reconstruct the exact same observation independently | `ObservationIdentity` remains identical | Permits deterministic replay and deduplication. |
| **KOM-004** (Subject Distinction) | Change `SubjectRef` | Slot and Identity change | Prevents cross-record data collision. |
| **KOM-005** (Field Distinction) | Change `FieldPath` | Slot and Identity change | Prevents cross-field data collision. |
| **KOM-006** (State Distinction) | Change `PRESENT` to `INVALID` with same raw value | Identity changes | Context of extraction failure is fundamentally different from a valid parse. |
| **KOM-007** (Missing Determinism) | Reconstruct a `MISSING` state observation | Identity remains identical | Absence is a deterministic structural state. |
| **KOM-008** (Runtime Object Independence)| Provide semantically equal values from distinct memory addresses | Identity remains identical | Values, not Python object IDs, define occurrences. |
| **KOM-009** (Type Preservation) | Change `1` (int) to `1.0` (float) | Identity changes | Type-sensitive hashing preserves source representation semantics. |
| **KOM-010** (Interpretation Independence)| Change `InterpretationState` on a downstream assertion | Observation identity remains identical | Proves orthogonal separation of observation and interpretation. |
| **KOM-011** (Provider Independence) | Reconstruct under a new provider version | Observation identity remains identical | Observations precede providers. |
| **KOM-012** (Claim Independence) | Evaluate observation against a different claim | Observation identity remains identical | Observations precede claims. |
| **KOM-013** (Scope Independence) | Pass observation to a different `PropositionSubject` | Observation identity remains identical | Observations are atomic facts; scope is an assertion mapping. |
| **KOM-014** (Serialization Stability) | Serialize two structurally equal observations | Emitted JSON is byte-equivalent | Enables cross-language/environment replay. |
| **KOM-015** (Invalid Value Preservation) | Change an invalid source string to another invalid string | Identity changes | Invalid values still represent distinct source facts. |
| **KOM-016** (Empty String Handling) | Compare `None` to `""` | Identity changes | An empty string is a present string; None is an absence. |
| **KOM-017** (Whitespace Sensitivity) | Compare `"ABC"` to `" ABC "` | Identity changes | Unnormalized values preserve raw source fidelity. |
| **KOM-018** (Decimal Stability) | Provide identical precision `Decimal` | Identity remains identical | Numeric scaling is preserved if types are identical. |
| **KOM-019** (Boolean/Integer Distinction)| Compare `True` to `1` | Identity changes | Prevents accidental collision due to Python subclassing. |
| **KOM-020** (Missingness Value Check) | Attempt `MISSING` + `value="ABC"` | Raises exception | Missing state fundamentally contradicts value presence. |
