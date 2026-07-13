# Observation Content vs Occurrence Identity

## The Distinction
In ReconGraph, K3 identifies **epistemic content state**. Temporal source occurrence identity belongs to structured lineage or future persistence/event infrastructure.

Consider the following timeline of a single source slot:
* **T0:** slot S contains "ABC"
* **T1:** slot S contains "XYZ"
* **T2:** slot S contains "ABC" (e.g. human reverted to the original value)

Because K3 `ObservationFingerprint` is a deterministic hash of the typed value state, we mathematically guarantee:

`ObservationIdentity(T0) == ObservationIdentity(T2)`
`ObservationIdentity(T0) != ObservationIdentity(T1)`

These are not three different revision identities. They are:
* Content state A
* Content state B
* Content state A

The future lineage/event layer (K4) or a persistence layer (Stage 7) may distinguish the *event* T0 from the *event* T2, but the semantic kernel correctly recognizes that the *content* is structurally identical.
