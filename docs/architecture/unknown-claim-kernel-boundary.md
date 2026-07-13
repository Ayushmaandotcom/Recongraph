# Unknown Claim Kernel Boundary

This document explicitly defines the boundaries for handling unknown plugin claims within the Evidence Semantic Kernel v0.1.

## Normative Rules

1. The semantic kernel can represent an unknown claim. (A plugin can instantiate a custom `ClaimDescriptor` and pass it to `PropositionSubject.create()`).
2. Representation does not imply fusion support. (Stage 8J cannot blindly mathematically fuse claims it does not explicitly understand).
3. Serialization does not imply semantic understanding. (Traces will faithfully serialize and deserialize the claim identifier and its structure, even if the core engine lacks the domain logic to evaluate it).
4. Namespacing does not imply trust. (A plugin claim `custom.bank_account_match` is isolated from the `CoreClaims` catalog).

By adhering to these boundaries, ReconGraph supports infinite plugin extensibility while protecting the mathematical integrity of the core fusion engine.
