# Core Claim Catalog V1

This document is normative for claim semantics in ReconGraph v0.1.

## `identity.same_legal_entity`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`, `GROUP_PAIR`
* **Meaning:** The scoped subjects refer to exactly the same legal entity (e.g. shared PAN in India).
* **Non-meaning:** Does not assert financial reconciliation. Does not merely assert that the vendor names look similar.

## `identity.same_gst_registration`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`, `GROUP_PAIR`
* **Meaning:** The scoped subjects share the exact same GST registration identity.
* **Non-meaning:** Does not assert complete legal entity equivalence (a legal entity can have multiple GSTINs).

## `identity.lexical_name_similarity`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`
* **Meaning:** The vendor names on the scoped subjects are lexically similar.
* **Non-meaning:** Does not assert legal entity identity.

## `identity.legal_form_compatibility`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`
* **Meaning:** The legal forms (e.g., PVT LTD vs INC) extracted from the subjects are compatible.
* **Non-meaning:** Does not assert identity, merely non-contradiction of structure.

## `financial.amount_conservation`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`, `GROUP_PAIR`
* **Meaning:** The total monetary amounts on the left side equal the total on the right side.
* **Non-meaning:** Does not assert identity.

## `financial.currency_compatibility`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`, `GROUP_PAIR`
* **Meaning:** All subjects in the scope transact in the same currency or represent a valid exchange pair.

## `reference.structural_compatibility`
* **Version:** 1
* **Symmetry:** SYMMETRIC
* **Allowed Scopes:** `RECORD_PAIR`, `GROUP_PAIR`
* **Meaning:** Reference fields (like invoice numbers) structurally align or overlap.

## `document.reference_is_parseable`
* **Version:** 1
* **Symmetry:** SYMMETRIC  (Unary scopes don't really have symmetry, but technically order-insensitive)
* **Allowed Scopes:** `RECORD`
* **Meaning:** The reference field contains parseable structured data.

*(Note: `document.supersedes` is omitted from production core claims as it was merely a directional example in research.)*
