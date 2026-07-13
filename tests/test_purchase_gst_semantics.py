import pytest

from recongraph.matching.purchase_gst_semantics import (
    EligibilityResult,
    OneToOneEligibility,
    SemanticFinding,
    ONE_TO_ONE_BLOCKING_FINDINGS,
    analyze_purchase_gst_semantics,
    evaluate_purchase_gst_one_to_one_eligibility,
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
    [SignalName.ENTITY, SignalName.REFERENCE, SignalName.AMOUNT, SignalName.TEMPORAL, SignalName.TAX_IDENTITY],
)
def test_analyze_purchase_gst_semantics_rejects_missing_evidence_keys(
    missing_signal: SignalName,
):
    evidence = complete_evidence()
    del evidence[missing_signal]

    with pytest.raises(KeyError):
        analyze_purchase_gst_semantics(evidence)


# Eligibility tests
def test_one_to_one_eligibility_is_eligible_without_findings():
    result = evaluate_purchase_gst_one_to_one_eligibility(())

    assert result == EligibilityResult(
        status=OneToOneEligibility.ELIGIBLE,
        blocking_findings=(),
    )


def test_severe_amount_conflict_blocks_one_to_one_eligibility():
    result = evaluate_purchase_gst_one_to_one_eligibility(
        (
            SemanticFinding.SEVERE_AMOUNT_CONFLICT,
        )
    )

    assert result == EligibilityResult(
        status=OneToOneEligibility.INELIGIBLE,
        blocking_findings=(
            SemanticFinding.SEVERE_AMOUNT_CONFLICT,
        ),
    )


def test_tax_identity_conflict_blocks_one_to_one_eligibility():
    result = evaluate_purchase_gst_one_to_one_eligibility(
        (
            SemanticFinding.TAX_IDENTITY_CONFLICT,
        )
    )

    assert result == EligibilityResult(
        status=OneToOneEligibility.INELIGIBLE,
        blocking_findings=(
            SemanticFinding.TAX_IDENTITY_CONFLICT,
        ),
    )


def test_distinct_event_identity_evidence_blocks_one_to_one_eligibility():
    result = evaluate_purchase_gst_one_to_one_eligibility(
        (
            SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,
        )
    )

    assert result == EligibilityResult(
        status=OneToOneEligibility.INELIGIBLE,
        blocking_findings=(
            SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,
        ),
    )


def test_one_to_one_eligibility_preserves_multiple_blocking_findings():
    findings = (
        SemanticFinding.TAX_IDENTITY_CONFLICT,
        SemanticFinding.SEVERE_AMOUNT_CONFLICT,
    )

    result = evaluate_purchase_gst_one_to_one_eligibility(
        findings
    )

    assert result == EligibilityResult(
        status=OneToOneEligibility.INELIGIBLE,
        blocking_findings=findings,
    )


def test_one_to_one_blocking_findings_are_explicit():
    assert ONE_TO_ONE_BLOCKING_FINDINGS == frozenset(
        {
            SemanticFinding.SEVERE_AMOUNT_CONFLICT,
            SemanticFinding.TAX_IDENTITY_CONFLICT,
            SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,
        }
    )


def test_one_to_one_eligibility_deduplicates_blocking_findings():
    result = evaluate_purchase_gst_one_to_one_eligibility(
        (
            SemanticFinding.SEVERE_AMOUNT_CONFLICT,
            SemanticFinding.SEVERE_AMOUNT_CONFLICT,
        )
    )

    assert result.blocking_findings == (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT,
    )


def test_eligibility_result_rejects_eligible_status_with_blocking_findings():
    with pytest.raises(ValueError):
        EligibilityResult(
            status=OneToOneEligibility.ELIGIBLE,
            blocking_findings=(
                SemanticFinding.SEVERE_AMOUNT_CONFLICT,
            ),
        )


def test_eligibility_result_rejects_ineligible_status_without_blocking_findings():
    with pytest.raises(ValueError):
        EligibilityResult(
            status=OneToOneEligibility.INELIGIBLE,
            blocking_findings=(),
        )
