from collections.abc import Mapping
from enum import StrEnum

from recongraph.matching.scoring import SignalName


STRONG_REFERENCE_SCORE = 0.8
STRONG_ENTITY_SCORE = 0.9
STRONG_AMOUNT_SCORE = 0.9


class SemanticFinding(StrEnum):
    SEVERE_AMOUNT_CONFLICT = "severe_amount_conflict"
    TAX_IDENTITY_CONFLICT = "tax_identity_conflict"
    DISTINCT_EVENT_IDENTITY_EVIDENCE = (
        "distinct_event_identity_evidence"
    )


def analyze_purchase_gst_semantics(
    evidence: Mapping[SignalName, float | None],
) -> tuple[SemanticFinding, ...]:
    findings: list[SemanticFinding] = []

    entity = evidence[SignalName.ENTITY]
    reference = evidence[SignalName.REFERENCE]
    amount = evidence[SignalName.AMOUNT]
    temporal = evidence[SignalName.TEMPORAL]
    tax_identity = evidence[SignalName.TAX_IDENTITY]

    if (
        amount == 0.0
        and reference is not None
        and reference >= STRONG_REFERENCE_SCORE
        and tax_identity == 1.0
    ):
        findings.append(
            SemanticFinding.SEVERE_AMOUNT_CONFLICT
        )

    if tax_identity == 0.0:
        findings.append(
            SemanticFinding.TAX_IDENTITY_CONFLICT
        )

    if (
        entity is not None
        and entity >= STRONG_ENTITY_SCORE
        and reference == 0.0
        and amount is not None
        and amount >= STRONG_AMOUNT_SCORE
        and temporal == 0.0
        and tax_identity == 1.0
    ):
        findings.append(
            SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        )

    return tuple(findings)
