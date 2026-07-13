# Observation Identity vs Value Equality

## Semantic Boundary
In ReconGraph, there is a strict semantic distinction between "same value" and "same observation." 

**Value equality** asserts that two raw data payloads are mathematically or lexically equivalent (e.g. `100 == 100`, or `"ABC" == "ABC"`). 

**Observation identity** asserts that two values were observed at the *exact same structural slot* (e.g. `purchase:P1/vendor_name`) under the *exact same occurrence/revision*.

### Why it matters
If Purchase P1 has an amount of 100, and GST G1 has an amount of 100, their values are equal. However, their observation identities are distinct because they reside in different slots (`P1.amount` vs `G1.amount`). 

Treating them as the "same observation" would destroy the graph's ability to reason about pairwise reconciliation. 

### Same Source, Different Occurrences
Likewise, if a human corrects a typo on an invoice:
* T0: `P1.vendor_name = "ABC PVT LTO"`
* T1: `P1.vendor_name = "ABC PVT LTD"`

These are observations on the *same slot*, but their values (and potentially their `ObservationState`) differ, leading to different `ObservationIdentity` fingerprints. Future lineage metadata will distinguish *why* the revision occurred, but the kernel guarantees that the original misread and the human correction do not collide in identity.

### Summary
* Same value, different slot -> Different Observation Identity
* Same slot, different value -> Different Observation Identity
* Same slot, same value, same state -> Same Observation Identity (Deterministic Reconstruction)
