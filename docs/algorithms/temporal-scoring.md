# Temporal Scoring

## Baseline

ReconGraph's baseline temporal compatibility signal uses linear decay over the absolute number of days between two financial evidence records.

For a configured maximum temporal window `w` and absolute day difference `d`:

`score = max(0, 1 - d / w)`

The score is `1.0` when two records share the same date and decays linearly to `0.0` at the configured temporal-window boundary.

## Relationship-Specific Windows

The temporal scoring function does not define a universal financial date window.

The expected temporal distance between financial records depends on the relationship being evaluated.

For example, a purchase-register entry and a GST record may be expected to occur relatively close together, while an invoice and its associated bank payment may legitimately be separated by a longer payment term.

Relationship-level scoring policy should therefore provide the temporal window used by the primitive temporal scoring function.

## Current Limitation: Direction-Agnostic Scoring

The baseline implementation uses absolute date distance.

As a result, a record occurring three days before another record receives the same temporal score as a record occurring three days after it.

This is acceptable for the initial purchase-to-GST reconciliation baseline but may be inappropriate for directional financial relationships.

Future relationship policies may use asymmetric temporal windows or directional temporal scoring.

For example, invoice-to-payment relationships may allow a larger window after an invoice date than before it.

## Design Principle

Temporal compatibility and temporal relationship policy are separate concerns.

The signal function calculates compatibility for a provided window.

The relationship policy determines which window and temporal assumptions are appropriate for the financial relationship being evaluated.
