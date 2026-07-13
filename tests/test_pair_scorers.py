from datetime import date

import pytest

from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.matching.pair_scorers import (
    PURCHASE_TO_GST_MAX_DAYS,
    PURCHASE_TO_GST_POLICY,
    PairScoringResult,
    score_purchase_to_gst,
)
from recongraph.matching.scoring import RelationshipScore, SignalName
from recongraph.matching.purchase_gst_semantics import SemanticFinding


def test_purchase_record_preserves_financial_fields() -> None:
    record = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity="07ABCDE1234F1Z5",
    )

    assert record.vendor_name == "ABC Steel Private Limited"
    assert record.reference == "INV-1042"
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 12)
    assert record.tax_identity == "07ABCDE1234F1Z5"


def test_gst_record_preserves_financial_fields() -> None:
    record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=118000.0,
        record_date=date(2026, 6, 13),
        tax_identity="07ABCDE1234F1Z5",
    )

    assert record.vendor_name == "ABC STEELS PVT. LTD."
    assert record.reference == "AB/1042"
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 13)
    assert record.tax_identity == "07ABCDE1234F1Z5"


def test_purchase_to_gst_policy_uses_expected_weights() -> None:
    assert PURCHASE_TO_GST_POLICY.weights == {
        SignalName.ENTITY: 0.20,
        SignalName.REFERENCE: 0.20,
        SignalName.AMOUNT: 0.25,
        SignalName.TEMPORAL: 0.10,
        SignalName.TAX_IDENTITY: 0.25,
    }


def test_purchase_to_gst_policy_penalizes_tax_identity_contradiction() -> None:
    assert (
        PURCHASE_TO_GST_POLICY.contradiction_penalties[
            SignalName.TAX_IDENTITY
        ]
        == 0.50
    )


def test_purchase_to_gst_temporal_window_is_seven_days() -> None:
    assert PURCHASE_TO_GST_MAX_DAYS == 7


def test_pair_scoring_result_preserves_signal_explanation() -> None:
    relationship = RelationshipScore(
        score=0.94571,
        base_score=0.94571,
        coverage=1.0,
        contradiction_penalty=1.0,
        active_contradictions=(),
    )

    result = PairScoringResult(
        signals={
            SignalName.ENTITY: 1.0,
            SignalName.REFERENCE: 0.8,
            SignalName.AMOUNT: 1.0,
            SignalName.TEMPORAL: 0.8571,
            SignalName.TAX_IDENTITY: 1.0,
        },
        semantic_findings=(),
        relationship=relationship,
    )

    assert result.signals[SignalName.ENTITY] == 1.0
    assert result.signals[SignalName.REFERENCE] == 0.8
    assert result.semantic_findings == ()
    assert result.relationship == relationship


def test_pair_scoring_result_is_immutable() -> None:
    result = PairScoringResult(
        signals={},
        semantic_findings=(),
        relationship=RelationshipScore(
            score=None,
            base_score=None,
            coverage=0.0,
            contradiction_penalty=1.0,
            active_contradictions=(),
        ),
    )

    with pytest.raises(AttributeError):
        result.relationship = RelationshipScore(
            score=1.0,
            base_score=1.0,
            coverage=1.0,
            contradiction_penalty=1.0,
            active_contradictions=(),
        )


def test_score_purchase_to_gst_scores_controlled_positive_pair() -> None:
    purchase = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity="07ABCDE1234F1Z5",
    )

    gst_record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=118000.0,
        record_date=date(2026, 6, 13),
        tax_identity="07ABCDE1234F1Z5",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.signals[SignalName.ENTITY] == pytest.approx(1.0)
    assert result.signals[SignalName.REFERENCE] == pytest.approx(0.8)
    assert result.signals[SignalName.AMOUNT] == pytest.approx(1.0)
    assert result.signals[SignalName.TEMPORAL] == pytest.approx(
        1.0 - (1.0 / 7.0)
    )
    assert result.signals[SignalName.TAX_IDENTITY] == pytest.approx(
        1.0
    )

    assert result.semantic_findings == ()

    assert result.relationship.score == pytest.approx(
        0.9457142857142857
    )
    assert result.relationship.base_score == pytest.approx(
        0.9457142857142857
    )
    assert result.relationship.coverage == pytest.approx(1.0)
    assert result.relationship.contradiction_penalty == pytest.approx(
        1.0
    )
    assert result.relationship.active_contradictions == ()


def test_score_purchase_to_gst_exposes_severe_amount_conflict() -> None:
    purchase = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity="07ABCDE1234F1Z5",
    )

    gst_record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=236000.0,
        record_date=date(2026, 6, 13),
        tax_identity="07ABCDE1234F1Z5",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.semantic_findings == (
        SemanticFinding.SEVERE_AMOUNT_CONFLICT,
    )
    
    assert result.relationship.score == pytest.approx(
        0.6957142857142857
    )


def test_score_purchase_to_gst_exposes_tax_identity_conflict() -> None:
    purchase = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity="07ABCDE1234F1Z5",
    )

    gst_record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=118000.0,
        record_date=date(2026, 6, 13),
        tax_identity="27ZZZZZ9999Z9Z9",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.semantic_findings == (
        SemanticFinding.TAX_IDENTITY_CONFLICT,
    )
    
    assert result.relationship.score == pytest.approx(
        0.34785714285714286
    )


def test_score_purchase_to_gst_exposes_distinct_event_identity_evidence() -> None:
    purchase = PurchaseRecord(
        vendor_name="CloudLedger Software Private Limited",
        reference="CL-JUN-2026",
        amount=25000.0,
        record_date=date(2026, 6, 5),
        tax_identity="07CLOUD1234A1Z1",
    )

    gst_record = GSTRecord(
        vendor_name="CLOUDLEDGER SOFTWARE PVT LTD",
        reference="CL-JUL-2026",
        amount=25000.0,
        record_date=date(2026, 7, 5),
        tax_identity="07CLOUD1234A1Z1",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.semantic_findings == (
        SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,
    )
    
    assert result.relationship.score == pytest.approx(
        0.7000
    )


def test_score_purchase_to_gst_preserves_missing_tax_evidence() -> None:
    purchase = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity=None,
    )

    gst_record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=118000.0,
        record_date=date(2026, 6, 13),
        tax_identity="07ABCDE1234F1Z5",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.signals[SignalName.TAX_IDENTITY] is None
    assert result.semantic_findings == ()
    assert result.relationship.coverage == pytest.approx(0.75)
    assert result.relationship.contradiction_penalty == pytest.approx(
        1.0
    )
    assert result.relationship.active_contradictions == ()
    assert result.relationship.base_score == pytest.approx(
        0.9276190476190477
    )
    assert result.relationship.score == pytest.approx(
        0.9276190476190477
    )


def test_score_purchase_to_gst_applies_tax_contradiction() -> None:
    purchase = PurchaseRecord(
        vendor_name="ABC Steel Private Limited",
        reference="INV-1042",
        amount=118000.0,
        record_date=date(2026, 6, 12),
        tax_identity="07ABCDE1234F1Z5",
    )

    gst_record = GSTRecord(
        vendor_name="ABC STEELS PVT. LTD.",
        reference="AB/1042",
        amount=118000.0,
        record_date=date(2026, 6, 13),
        tax_identity="27ZZZZZ9999Z9Z9",
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.signals[SignalName.TAX_IDENTITY] == pytest.approx(
        0.0
    )
    assert result.relationship.coverage == pytest.approx(1.0)
    assert result.relationship.contradiction_penalty == pytest.approx(
        0.5
    )
    assert result.relationship.active_contradictions == (
        SignalName.TAX_IDENTITY,
    )
    assert result.relationship.base_score == pytest.approx(
        0.6957142857142857
    )
    assert result.relationship.score == pytest.approx(
        0.34785714285714286
    )


def test_score_purchase_to_gst_uses_purchase_to_gst_temporal_window() -> None:
    purchase = PurchaseRecord(
        vendor_name="Vendor",
        reference="INV-1",
        amount=1000.0,
        record_date=date(2026, 6, 1),
        tax_identity=None,
    )

    gst_record = GSTRecord(
        vendor_name="Vendor",
        reference="INV-1",
        amount=1000.0,
        record_date=date(2026, 6, 8),
        tax_identity=None,
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert result.signals[SignalName.TEMPORAL] == pytest.approx(0.0)


def test_score_purchase_to_gst_returns_pair_scoring_result() -> None:
    purchase = PurchaseRecord(
        vendor_name="Vendor",
        reference="INV-1",
        amount=1000.0,
        record_date=date(2026, 6, 1),
        tax_identity=None,
    )

    gst_record = GSTRecord(
        vendor_name="Vendor",
        reference="INV-1",
        amount=1000.0,
        record_date=date(2026, 6, 1),
        tax_identity=None,
    )

    result = score_purchase_to_gst(
        purchase=purchase,
        gst_record=gst_record,
    )

    assert isinstance(result, PairScoringResult)
    assert set(result.signals) == set(PURCHASE_TO_GST_POLICY.weights)

