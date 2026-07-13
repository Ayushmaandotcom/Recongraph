# Observation Fingerprint Privacy Threat Analysis

## Threat Model
In ReconGraph v0.1, the `ObservationIdentity` relies on an `ObservationFingerprint` constructed from a deterministic SHA-256 digest of the typed observation envelope (schema version, state, type tag, value bytes).

An attacker who obtains an observation fingerprint could attempt to reverse it by hashing potential source values and comparing the digests. 

### Can observation fingerprints be dictionary attacked?
Yes. Because the digest is deterministic and unsalted, low-entropy values (like currency codes, booleans, dates, or common vendor names) can be trivially guessed and hashed by an attacker to confirm their presence in the system. High-entropy values (like exact invoice numbers or long random references) are more resistant but still technically susceptible.

### Are fingerprints anonymization?
**NO.** A fingerprint is a technical identity primitive for deterministic deduplication and trace replay. It is strictly not an encryption mechanism, not an anonymization scheme, and not a method of access control. 

### Should observation IDs be logged publicly?
No. Because they leak exact value equality and can be dictionary-attacked, observation identities should be treated as sensitive metadata and restricted to secure operational telemetry (e.g. secure audit logs), not exposed in public dashboards or unprotected environments.

### Does v0.1 require HMAC?
No. Introducing a keyed HMAC for the digest complicates deterministic cross-environment replay because the secret key becomes part of the identity. For v0.1, we accept the privacy trade-off of a plain digest in exchange for stable counterfactual re-evaluation across environments, provided the system treats the IDs themselves as sensitive.

### What must Stage 7 persistence eventually protect?
When observations are persisted to a database or object store (Stage 7), the persistence layer must protect the `ObservationIdentity` column with the same access controls and encryption-at-rest policies as the raw value payload itself.
