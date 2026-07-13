# Observation vs Evidence Boundary

An observation states that a source slot had a particular value occurrence or condition. An evidence assertion states that an interpreter derived semantic support or conflict for a claim from observations. A structurally invalid observation can still be successfully interpreted for a claim concerning invalidity. Therefore, Observation State (PRESENT/MISSING/INVALID) is orthogonal to Interpretation State (INTERPRETED/UNINTERPRETABLE).

## Semantic Mapping Examples

| Source Fact | Observation State | Possible Interpretation State | Why |
|---|---|---|---|
| valid vendor name | PRESENT | INTERPRETED | Standard lexical parsing succeeds. |
| blank vendor name | PRESENT | UNINTERPRETABLE | Empty string cannot yield a vendor name similarity score. |
| vendor field absent | MISSING | UNINTERPRETABLE | Missing fields cannot be compared lexically. |
| vendor value "UNKNOWN" | PRESENT | UNINTERPRETABLE | Literal string "UNKNOWN" yields no specific identity support. |
| Japanese vendor name under English-only parser | PRESENT | UNINTERPRETABLE | Valid data, but interpreter lacks capability. |
| valid GSTIN | PRESENT | INTERPRETED | Checksum and structure valid, can derive state/identity. |
| invalid GSTIN structure | INVALID | INTERPRETED | Can assert `document.contains_invalid_tax_identifier`. |
| GSTIN checksum failure | INVALID | INTERPRETED | Can assert `document.contains_invalid_tax_identifier`. |
| valid reference | PRESENT | INTERPRETED | Can be matched against other references. |
| reference punctuation only | PRESENT | UNINTERPRETABLE | Cannot extract meaningful semantic tokens. |
| amount present | PRESENT | INTERPRETED | Number can be used in conservation check. |
| amount malformed | INVALID | UNINTERPRETABLE | Cannot perform math on malformed text. |
| currency present but unsupported | PRESENT | UNINTERPRETABLE | E.g. internal logic only supports USD/INR. |
| one-sided date | PRESENT | INTERPRETED | Could be used to assert `temporal.strictly_before`. |
| OCR text confidence 0.41 | PRESENT | UNINTERPRETABLE | Low confidence rejects interpretation to prevent false positives. |
