# Financial Relationship Score

## Purpose

ReconGraph combines multiple primitive compatibility signals to estimate the strength of a relationship between financial evidence records.

The Financial Relationship Score is a compatibility score. It is not a calibrated probability that two records represent the same financial event.

## Primitive Signals

The purchase-to-GST baseline uses five primitive signals:

* entity compatibility
* reference compatibility
* amount compatibility
* temporal compatibility
* tax identity compatibility

Each available signal produces a score between 0.0 and 1.0.

An unavailable signal is represented as `None`.

Unavailable evidence is distinct from contradictory evidence.

## Purchase-to-GST Baseline Weights

| Signal | Weight |
|--------|--------|
| Entity | 0.20 |
| Reference | 0.20 |
| Amount | 0.25 |
| Temporal | 0.10 |
| Tax identity | 0.25 |

The weights are explicit baseline policy hypotheses.

They are not learned parameters and should not be interpreted as statistically optimal feature importance values.

## Base Compatibility Score

Only available signals participate in the base compatibility calculation.

For the set of available signals A:

`base_score = sum(weight_i * score_i) / sum(weight_i)`

for all i in A.

This available-weight renormalization prevents missing evidence from being treated as either a mismatch or a perfect match.

A signal with score 0.0 is available evidence and remains in the weighted denominator.

A signal with value `None` is unavailable and is excluded from both the weighted numerator and the available-weight denominator.

## Evidence Coverage

Evidence coverage measures how much of the relationship policy's expected weighted evidence is available.

`coverage = available_weight / total_configured_weight`

Coverage is maintained separately from compatibility.

A pair may have high compatibility among available signals while still having low evidence coverage.

For example, two records with only perfectly matching vendor evidence may have a base compatibility score of 1.0 but coverage of only 0.20 under the purchase-to-GST baseline policy.

Future decision policy should consider both relationship score and evidence coverage.

## Contradiction Penalty

The purchase-to-GST v0.1 policy treats an explicit tax identity mismatch as contradictory evidence.

When the tax identity signal is available and equals 0.0, the baseline applies a contradiction penalty multiplier of 0.50.

`final_score = base_score * contradiction_penalty`

When no configured contradiction is present, the multiplier is 1.0.

The tax identity mismatch influences the result in two ways:

1. Its 0.0 score contributes no positive compatibility while remaining in the weighted denominator.
2. The explicit contradiction additionally activates the relationship-level penalty.

This strong treatment is deliberate in the v0.1 purchase-to-GST policy and should be evaluated against labelled reconciliation pairs.

## Missing Evidence

Missing evidence does not activate a contradiction penalty.

For example, a missing tax identity produces an unavailable tax signal and reduces evidence coverage.

It does not behave like an explicit tax identity mismatch.

## Current Limitations

The baseline weights and contradiction penalty are manually specified policy hypotheses.

They have not been trained or calibrated against a production reconciliation dataset.

The current model assumes signal contributions are combined linearly before contradiction treatment.

Interactions between signals are represented only through explicit contradiction rules.

Future evaluation may compare the deterministic baseline against learned pairwise models using the primitive signal vector as input features.

## Design Principle

Primitive signals measure individual forms of compatibility.

Relationship policy determines signal importance and contradiction treatment.

Compatibility and evidence coverage are separate dimensions.

A high relationship score with low coverage must not be interpreted the same way as a high relationship score supported by complete evidence.
