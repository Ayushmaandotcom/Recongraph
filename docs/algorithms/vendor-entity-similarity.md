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

TODO: Record the second experiment results and selected baseline metric.

## Current Limitation

The controlled experiment is intentionally small and does not establish production-grade entity-resolution accuracy.

The negative labels are adversarial experiment assumptions rather than verified legal-entity ground truth.

Future evaluation should use a larger labelled vendor-pair dataset with verified entity identities and should measure false-positive and false-negative behaviour at candidate decision thresholds.

## Design Principle

Vendor-name normalization should remove known representation noise before similarity scoring.

A fuzzy string similarity score measures textual resemblance. It must not be interpreted as a calibrated probability that two records refer to the same legal entity.
