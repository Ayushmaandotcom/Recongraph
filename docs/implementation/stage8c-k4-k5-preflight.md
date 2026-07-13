# Stage 8C K4/K5 Preflight Audit

## K3 Closure Review

### Observation Module Location
* **Location:** `src/recongraph/domain/observations.py`

### Public APIs
* **Observation construction API:** `Observation.create(slot: ObservationSlot, state: ObservationState, value: Any)`
* **Observation identity composition:** `ObservationIdentity(slot: ObservationSlot, fingerprint: ObservationFingerprint)`
* **Observation fingerprint algorithm:** SHA-256 of JSON serialized canonical value envelope.
* **Observation schema version representation:** Explicit `"schema_version": 1` in the envelope dictionary.
* **Observation supported value types:** `str`, `int`, `float`, `Decimal`, `bool`, `date`, `datetime`, `None` (missing).
* **Observation serialization API:** `ObservationIdentity.to_dict()` for structural ID, `Observation.to_dict()` for sensitive full payload.
* **SubjectRef construction API:** `SubjectRef(urn: str)`

### External Primitives
* **Current semantic-version primitives:** `ClaimSemanticVersion(value: int)` (in `claims.py`)
* **Current provider version representation:** N/A (not yet represented in primitives)
* **Current engine version representation:** Currently handled by the broader application config/trace logic, not as a typed domain primitive.
* **Current trace engine_version representation:** Currently plain string/dict in trace schema.
* **Current config_hash representation:** Currently plain string in config module.

### K4/K5 Architecture Recommendations
* **Recommended K4 module location:** `src/recongraph/domain/lineage.py`
* **Recommended K5 module location:** `src/recongraph/domain/derivations.py`
* **Potential circular imports:** K4/K5 will need to import `ObservationIdentity` from `observations.py`. This is structurally clean. If we must attach Lineage to Observation, there is a risk of a circular dependency if `observations.py` needs to import `lineage.py`. We should use a wrapper object (like `SourcedObservation` or `ObservationProvenance`) living in `lineage.py` or a distinct attachment module.

## Mandatory Vocabulary Correction

`ObservationFingerprint` = **content-state fingerprint**

It is NOT:
* temporal revision number
* source event identity
* ingestion sequence
* historical occurrence identity

*Observation identity distinguishes typed observation content states.*
