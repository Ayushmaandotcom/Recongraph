# Vendor Entity Similarity

## Problem

Financial records may represent the same vendor using different legal suffixes, abbreviations, punctuation, and minor token variations.

Examples include:

* `ABC Steel Private Limited` and `ABC STEELS PVT. LTD.`
* `Shree Balaji Enterprises` and `SHREE BALAJI ENT.`

Exact raw-string equality is therefore insufficient for vendor entity comparison.

## Baseline Metric Experiment

ReconGraph evaluated the following RapidFuzz similarity metrics against a small controlled set of assumed positive and adversarial negative vendor-name pairs:

* `ratio`
* `partial_ratio`
* `token_sort_ratio`
* `token_set_ratio`
* `WRatio`

The experiment compared the minimum score among positive pairs with the maximum score among negative pairs.

The separation gap is defined as:

`minimum positive score - maximum negative score`

A positive separation gap indicates that, for the controlled experiment, every positive pair scored above every negative pair.

## Initial Result

Before domain-specific token canonicalization, none of the evaluated metrics produced a clean positive separation gap.

| Metric | Minimum Positive | Maximum Negative | Separation Gap |
|--------|------------------|------------------|----------------|
| ratio | 80.00 | 83.33 | -3.33 |
| partial_ratio | 97.67 | 100.00 | -2.33 |
| token_sort_ratio | 80.00 | 83.33 | -3.33 |
| token_set_ratio | 85.71 | 100.00 | -14.29 |
| WRatio | 90.00 | 90.00 | 0.00 |

The strongest initial separation gap was `0.00`, produced by `WRatio`. No evaluated metric placed every assumed positive pair strictly above every adversarial negative pair.

The comparison indicates that the baseline problem was not solved merely by selecting a more aggressive fuzzy scorer. Improving the vendor-name representation produced a larger separation improvement while preserving a simpler scoring metric.

`token_set_ratio` was particularly vulnerable to subset-style hard negatives, where a shorter vendor name was fully contained in a longer but assumed-distinct vendor name.

This demonstrates that generic fuzzy similarity should not be interpreted directly as entity identity.

## Domain Canonicalization

The baseline vendor normalizer explicitly canonicalizes a small set of observed representation variants.

Examples include:

* `ent` to `enterprises`
* `steels` to `steel`
* `components` to `component`
* `solutions` to `solution`
* `supplies` to `supply`

These rules are explicit baseline hypotheses derived from controlled reconciliation examples.

They are not intended to represent a universal English stemming system or a complete vendor alias dictionary.

## Post-Canonicalization Result

After explicit canonicalization of the observed vendor-name representation variants, the experiment produced the following separation gaps:

| Metric | Minimum Positive | Maximum Negative | Separation Gap |
|--------|------------------|------------------|----------------|
| ratio | 100.00 | 73.91 | 26.09 |
| partial_ratio | 100.00 | 100.00 | 0.00 |
| token_sort_ratio | 100.00 | 73.91 | 26.09 |
| token_set_ratio | 100.00 | 100.00 | 0.00 |
| WRatio | 100.00 | 90.00 | 10.00 |

`ratio` and `token_sort_ratio` produced the strongest observed separation gap of `26.09`.

ReconGraph selects `ratio` as the baseline vendor entity similarity metric.

The normalized vendor representation already preserves meaningful token order while removing known legal suffixes and canonicalizing observed token variants. Under the controlled experiment, `ratio` achieved the same separation as `token_sort_ratio` while using a simpler full-string similarity interpretation.

The baseline entity signal converts the RapidFuzz 0–100 similarity scale into ReconGraph's 0–1 signal scale by dividing the similarity score by 100.

This conversion is a numeric rescaling only.

An entity score of `0.90` means the selected normalized-string metric produced a similarity score of 90/100. It does not mean there is a calibrated 90% probability that the records refer to the same legal entity.

## Current Limitation

The controlled experiment is intentionally small and does not establish production-grade entity-resolution accuracy.

The negative labels are adversarial experiment assumptions rather than verified legal-entity ground truth.

Future evaluation should use a larger labelled vendor-pair dataset with verified entity identities and should measure false-positive and false-negative behaviour at candidate decision thresholds.

## Design Principle

Vendor-name normalization should remove known representation noise before similarity scoring.

A fuzzy string similarity score measures textual resemblance. It must not be interpreted as a calibrated probability that two records refer to the same legal entity.
