# Observation Serialization Sensitivity

## Context
When an `Observation` is serialized to JSON (or Python dictionaries), it must emit two distinct levels of data: structural identity and full typed value occurrences.

### `ObservationIdentity.to_dict()`
This serialization produces a safe structural identity representation (the slot and the fingerprint hash). It is safe to use in operational telemetry, graph topology logging, and unencrypted deduplication traces, as it does not leak raw PII or exact raw strings (though it is susceptible to dictionary attacks for low-entropy enums/values).

### `Observation.to_dict()`
This serialization includes the raw typed value (e.g. `{"type": "str", "value": "ABC PRIVATE LIMITED"}`). **This representation is highly sensitive.** It contains raw source data which may include PANs, GSTINs, and proprietary vendor names. 

Observation serialization containing raw source data must not be treated as sanitized telemetry. Any system (like Stage 7 Traces) that persists `Observation.to_dict()` must treat the resulting artifact as a secure data asset with appropriate access controls and encryption at rest.

*(Note: In the future, a `to_trace_dict(redaction_policy)` may be introduced to sanitize values for lower-security traces, but v0.1 does not implement this).*
