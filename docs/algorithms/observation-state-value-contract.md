# Observation State/Value Contract

This document defines the strict legality matrix for combining an `ObservationState` with a value (whether None or non-None) in ReconGraph v0.1.

| ObservationState | None Allowed | Non-None Allowed | Meaning |
|---|---|---|---|
| `PRESENT` | NO | YES | The field is present and contains a concrete source value. `PRESENT` + `None` is ambiguous and explicitly rejected. (If the value is missing, the state must be `MISSING`). |
| `MISSING` | YES | NO | The field is absent from the source. A missing observation should not simultaneously carry a source value. |
| `INVALID` | NO | YES | The field is present but violates structural/schema contracts (e.g. malformed data). The raw value is preserved for explainability. `INVALID` + `None` is rejected because there is no raw invalid value to preserve. |

*(Note: Explicit strings like "UNKNOWN" or "MISSING" in the source data are treated as `PRESENT` with a non-None string value; interpretation logic later decides if they hold semantic meaning).*
