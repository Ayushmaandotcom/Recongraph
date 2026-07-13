# Stage 8C K3 Import Cycle Audit

## Modules Audited
* `src/recongraph/domain/observations.py`

## Internal ReconGraph Imports
* `src/recongraph/domain/observations.py`:
  - `recongraph.domain.scopes.SubjectRef`

## Results
* **Observation module imports claims:** no
* **Observation module imports scopes:** yes (only `SubjectRef`)
* **Observation module imports SubjectRef:** yes
* **Observation module imports plugins:** no
* **Observation module imports evaluator:** no
* **Observation module imports decision:** no
* **Observation module imports trace:** no

The dependency graph remains clean. The observation layer sits beside or slightly below the claim/scope layer, sharing only the formal subject identity wrapper (`SubjectRef`).
