# Observation Revision Implementation Decision

## Context
An `ObservationSlot` (e.g. `purchase:P1/vendor_name`) identifies *where* a fact belongs. We must also identify *which value occurrence* was observed at that slot (e.g. "ABC PVT LTD" vs a later correction "ABC PRIVATE LIMITED"), yielding a unique `ObservationIdentity`. The identifier must be deterministic, distinguish duplicates, differentiate value types and missing/invalid states, avoid random UUIDs, and avoid embedding raw sensitive values directly.

## Evaluated Strategies

* **Revision A (Explicit Monotonic Revision Number):** e.g. `P1.vendor_name@1`. Rejected because K3 has no persistence layer to track monotonically increasing counters, breaking deterministic independent reconstruction.
* **Revision B (Value Fingerprint):** `slot + SHA-256(value)`. Rejected because it fails to distinguish different observation states (e.g. `PRESENT` "MISSING" vs `MISSING` state with no value), and normalizations change the identity.
* **Revision C (Explicit Revision Token Supplied by Ingestion):** Rejected because it pushes too much responsibility onto disparate plugins which may lack reliable source sequences.
* **Revision D (Structural Slot + Opaque Deterministic Fingerprint):** The fingerprint is derived from a canonical typed value envelope (schema version, state, type tag, canonical bytes). Raw values are excluded from the identifier string itself.
* **Revision E (Caller-Supplied Revision Ref):** Pushes identity semantics entirely out of the kernel.

## Decision
**Revision D (Structural Slot + Opaque Deterministic Fingerprint)** is selected.

We implement `ObservationFingerprint` (to correctly reflect content-based identity rather than temporal sequence). The fingerprint is a SHA-256 hash of a deterministic JSON serialization of a typed envelope containing:
- Observation schema version
- `ObservationState` (PRESENT, MISSING, INVALID)
- Canonical Type Tag (`str`, `int`, `float`, `none`, etc.)
- Canonical Value bytes

## Trade-offs & Properties Satisfied
1. **Deterministic reconstruction:** Yes. Independent ingestions of the exact same typed value state will yield the exact same fingerprint.
2. **Exact duplicate observation detectability:** Yes.
3. **Value occurrence distinction:** Yes. Changes in value change the fingerprint.
4. **Type distinction:** Yes. `1` (int) and `1.0` (float) have different type tags.
5. **State distinction:** Yes. `PRESENT` with value "ABC" has a different fingerprint than `INVALID` with value "ABC".
6. **No raw value in IDs:** Yes. The ID only contains a SHA-256 hex digest.
7. **No Python hash():** Yes. Uses stable crypto hash (`hashlib.sha256`), avoiding Python's randomized hash seeds.

**Caveat:** A plain SHA-256 digest is susceptible to dictionary attacks for low-entropy values (like currency codes or booleans). The fingerprint is a technical identity, not a cryptographic anonymization scheme. We explicitly accept this privacy trade-off for v0.1 as deterministic cross-environment trace replay requires the absence of runtime-specific secret keys (HMAC).
