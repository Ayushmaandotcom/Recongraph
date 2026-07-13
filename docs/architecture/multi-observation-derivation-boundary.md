# Multi-Observation Derivation Boundary

## Context
Some semantic interpretations rely on multiple distinct observed fields from the same source document. For example, validating `financial.amount_conservation` might require interpreting three distinct source fields: `gross_amount`, `net_amount`, and `tax_amount`.

## Boundary Decision
**Observation identity identifies source fact occurrences (singular field slots). Derivation identity (K5) records which observations participated in a semantic interpretation.**

We explicitly reject the creation of `CompositeObservation`, `MultiFieldObservation`, or `ObservationGroup` within the K3 observation layer. 

By keeping observations atomic (1:1 with source field slots), we avoid building a redundant derivation DAG in the observation layer. When a provider interprets a complex claim, it will consume multiple atomic `Observation`s and list all of their `ObservationIdentity` references inside its future `DerivationMetadata`. This keeps the observation layer purely factual and leaves complex dependency mapping to the derivation engine.
