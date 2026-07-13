import pytest

from recongraph.matching.purchase_gst_semantics import (
    SemanticFinding,
    analyze_purchase_gst_semantics,
)
from recongraph.matching.scoring import SignalName


def complete_evidence(
    *,
    entity: float | None = 1.0,
    reference: float | None = 1.0,
    amount: float | None = 1.0,
    temporal: float | None = 1.0,
    tax_identity: float | None = 1.0,
) -> dict[SignalName, float | None]:
    return {
        SignalName.ENTITY: entity,
        SignalName.REFERENCE: reference,
        SignalName.AMOUNT: amount,
        SignalName.TEMPORAL: temporal,
        SignalName.TAX_IDENTITY: tax_identity,
    }


def test_analyze_purchase_gst_semantics_returns_no_findings_for_clean_evidence():
    findings = analyze_purchase_gst_semantics(
        complete_evidence()
    )
    assert findings == ()


# PG-001: Severe Amount Conflict
def test_detects_severe_amount_conflict():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=0.8,
            amount=0.0,
            tax_identity=1.0,
        )
    )
    assert findings == (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT,
    )


def test_does_not_detect_severe_amount_conflict_when_amount_is_positive():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=0.8,
            amount=0.01,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT
        not in findings
    )


def test_does_not_detect_severe_amount_conflict_without_strong_reference_evidence():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=0.0,
            amount=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT
        not in findings
    )


def test_does_not_detect_severe_amount_conflict_when_reference_is_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=None,
            amount=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT
        not in findings
    )


def test_does_not_detect_severe_amount_conflict_when_tax_identity_conflicts():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=0.8,
            amount=0.0,
            tax_identity=0.0,
        )
    )
    assert (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT
        not in findings
    )


def test_does_not_detect_severe_amount_conflict_when_tax_identity_is_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            reference=0.8,
            amount=0.0,
            tax_identity=None,
        )
    )
    assert (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT
        not in findings
    )


# Tax Identity Conflict
def test_detects_tax_identity_conflict():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            tax_identity=0.0,
        )
    )
    assert findings == (
        SemanticFinding.TAX_IDENTITY_CONFLICT,
    )


def test_does_not_detect_tax_identity_conflict_when_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            tax_identity=None,
        )
    )
    assert (
        SemanticFinding.TAX_IDENTITY_CONFLICT
        not in findings
    )


def test_does_not_detect_tax_identity_conflict_when_tax_identity_agrees():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.TAX_IDENTITY_CONFLICT
        not in findings
    )


# PG-002: Distinct Event Identity Evidence
def test_detects_distinct_event_identity_evidence():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=1.0,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert findings == (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,
    )


def test_does_not_detect_distinct_event_identity_when_entity_is_weak():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=0.89,
            reference=0.0,
            amount=1.0,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_detects_distinct_event_identity_at_entity_threshold():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=0.9,
            reference=0.0,
            amount=1.0,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        in findings
    )


def test_does_not_detect_distinct_event_identity_when_amount_is_weak():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=0.89,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_detects_distinct_event_identity_at_amount_threshold():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=0.9,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        in findings
    )


def test_does_not_detect_distinct_event_identity_when_reference_has_positive_evidence():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.8,
            amount=1.0,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_does_not_detect_distinct_event_identity_when_reference_is_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=None,
            amount=1.0,
            temporal=0.0,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_does_not_detect_distinct_event_identity_when_temporal_is_positive():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=1.0,
            temporal=0.01,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_does_not_detect_distinct_event_identity_when_temporal_is_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=1.0,
            temporal=None,
            tax_identity=1.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_does_not_detect_distinct_event_identity_when_tax_identity_conflicts():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=1.0,
            temporal=0.0,
            tax_identity=0.0,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


def test_does_not_detect_distinct_event_identity_when_tax_identity_is_unknown():
    findings = analyze_purchase_gst_semantics(
        complete_evidence(
            entity=1.0,
            reference=0.0,
            amount=1.0,
            temporal=0.0,
            tax_identity=None,
        )
    )
    assert (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE
        not in findings
    )


# Missing Evidence Keys
@pytest.mark.parametrize(
    "missing_signal",
    list(SignalName),
)
def test_analyze_purchase_gst_semantics_rejects_missing_evidence_keys(
    missing_signal: SignalName,
):
    evidence = complete_evidence()
    del evidence[missing_signal]

    with pytest.raises(KeyError):
        analyze_purchase_gst_semantics(evidence)
