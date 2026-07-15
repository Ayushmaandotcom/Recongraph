from datetime import date
import pytest
from decimal import Decimal
from recongraph.domain.financial.pipeline import AmountInterpretation, EqualityRelation, MagnitudeRelation, CurrencyRelation, SignRelation, CompatibilityFlag
from recongraph.domain.financial.amount_projection import ProjectedAmountSimilarity
from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile

def _get_vendor_context():
    return VendorIdentityContext(corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'), interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01)
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_MAX_DAYS, PURCHASE_TO_GST_POLICY, PairScoringResult, score_purchase_to_gst
from recongraph.matching.scoring import RelationshipScore, SignalName
from recongraph.matching.purchase_gst_semantics import SemanticFinding, OneToOneEligibility, EligibilityResult
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceEvidencePolicy, ReferenceCorpusProfile, ReferenceEvidenceInterpretation, ReferenceEvidenceContribution, ReferenceEvidenceKind

def _default_context() -> ReferenceEvidenceContext:
    prof = ReferenceCorpusProfile(reference_count=1000, normalized_reference_frequency={'dummy': 998, 'inv1042': 2}, numeric_token_document_frequency={'2026': 100, '1042': 2})
    return ReferenceEvidenceContext(profile=prof, policy=ReferenceEvidencePolicy())

def test_purchase_record_preserves_financial_fields() -> None:
    record = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    assert record.vendor_name == 'ABC Steel Private Limited'
    assert record.reference == 'INV-1042'
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 12)
    assert record.tax_identity == '07ABCDE1234F1Z5'

def test_gst_record_preserves_financial_fields() -> None:
    record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='07ABCDE1234F1Z5')
    assert record.vendor_name == 'ABC STEELS PVT. LTD.'
    assert record.reference == 'AB/1042'
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 13)
    assert record.tax_identity == '07ABCDE1234F1Z5'

def test_purchase_to_gst_policy_uses_expected_weights() -> None:
    assert PURCHASE_TO_GST_POLICY.weights == {SignalName.ENTITY: 0.2, SignalName.REFERENCE: 0.2, SignalName.AMOUNT: 0.25, SignalName.TEMPORAL: 0.1, SignalName.TAX_IDENTITY: 0.25}

def test_purchase_gst_policy_uses_pure_compatibility() -> None:
    assert PURCHASE_TO_GST_POLICY.contradiction_penalties == {}

def test_purchase_to_gst_temporal_window_is_seven_days() -> None:
    assert PURCHASE_TO_GST_MAX_DAYS == 7

def test_pair_scoring_result_preserves_signal_explanation() -> None:
    relationship = RelationshipScore(score=0.94571, base_score=0.94571, coverage=1.0, contradiction_penalty=1.0, active_contradictions=())
    from recongraph.matching.reference_evidence import ReferenceEvidenceInterpretation
    result = PairScoringResult(signals={SignalName.ENTITY: 0.9, SignalName.REFERENCE: 0.5, SignalName.AMOUNT: 1.0, SignalName.TEMPORAL: 0.5, SignalName.TAX_IDENTITY: 0.0}, semantic_findings=(SemanticFinding.TAX_IDENTITY_CONFLICT,), eligibility=EligibilityResult(status=OneToOneEligibility.INELIGIBLE, blocking_findings=(SemanticFinding.TAX_IDENTITY_CONFLICT,)), relationship=RelationshipScore(score=0.5, base_score=0.6, coverage=1.0, contradiction_penalty=0.5, active_contradictions=(SignalName.TAX_IDENTITY,)), reference_interpretation=ReferenceEvidenceInterpretation(score=0.5, statistical_coverage=1.0, contributions=(ReferenceEvidenceContribution(evidence_kind=ReferenceEvidenceKind.SHARED_NUMERIC_TOKEN, identity_value='12345', positive_evidence=0.5, evidential_weight=0.8, statistics_available=True),)), amount_interpretation=AmountInterpretation(equality=EqualityRelation.UNEQUAL, magnitude_relation=MagnitudeRelation.EQUAL, currency_relation=CurrencyRelation.DIFFERENT, sign_relation=SignRelation.SAME_POSITIVE, amount_a=Decimal('118000.0'), amount_b=Decimal('118000.0'), absolute_difference=Decimal('0.0'), relative_difference=Decimal('0.0'), residual=Decimal('0.0')), amount_projection=ProjectedAmountSimilarity(1.0), vendor_interpretation=None, vendor_projection=None)
    assert result.signals[SignalName.ENTITY] == 0.9
    assert result.signals[SignalName.REFERENCE] == 0.5
    assert result.semantic_findings == (SemanticFinding.TAX_IDENTITY_CONFLICT,)
    assert result.relationship.score == 0.5

def test_pair_scoring_result_is_immutable() -> None:
    result = PairScoringResult(signals={}, semantic_findings=(), eligibility=EligibilityResult(status=OneToOneEligibility.ELIGIBLE, blocking_findings=()), relationship=RelationshipScore(score=None, base_score=None, coverage=0.0, contradiction_penalty=1.0, active_contradictions=()), reference_interpretation=ReferenceEvidenceInterpretation(0.0, 0.0, ()), amount_interpretation=AmountInterpretation(equality=EqualityRelation.EQUAL, magnitude_relation=MagnitudeRelation.EQUAL, currency_relation=CurrencyRelation.SAME, sign_relation=SignRelation.SAME_POSITIVE, amount_a=Decimal('100'), amount_b=Decimal('100'), absolute_difference=Decimal('0'), relative_difference=Decimal('0'), residual=Decimal('0'), comparison_basis='Gross'), amount_projection=ProjectedAmountSimilarity(1.0), vendor_interpretation=None, vendor_projection=None)
    with pytest.raises(AttributeError):
        result.relationship = RelationshipScore(score=1.0, base_score=1.0, coverage=1.0, contradiction_penalty=1.0, active_contradictions=())

def test_score_purchase_to_gst_scores_controlled_positive_pair() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='07ABCDE1234F1Z5')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.signals[SignalName.ENTITY] == pytest.approx(0.947, rel=0.01)
    assert result.signals[SignalName.REFERENCE] == pytest.approx(0.5)
    assert result.signals[SignalName.AMOUNT] == pytest.approx(1.0)
    assert result.signals[SignalName.TEMPORAL] == pytest.approx(1.0 - 1.0 / 7.0)
    assert result.signals[SignalName.TAX_IDENTITY] == pytest.approx(1.0)
    assert result.semantic_findings == ()
    assert result.eligibility.status is OneToOneEligibility.ELIGIBLE
    assert result.eligibility.blocking_findings == ()
    assert result.relationship.score == pytest.approx(0.875, rel=0.01)
    assert result.relationship.base_score == pytest.approx(0.875, rel=0.01)
    assert result.relationship.coverage == pytest.approx(1.0)
    assert result.relationship.contradiction_penalty == pytest.approx(1.0)
    assert result.relationship.active_contradictions == ()

def test_score_purchase_to_gst_exposes_severe_amount_conflict() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='INV-1042', amount=Decimal('236000.0'), record_date=date(2026, 6, 13), tax_identity='07ABCDE1234F1Z5')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.semantic_findings == (SemanticFinding.SEVERE_AMOUNT_CONFLICT,)
    assert result.eligibility.status is OneToOneEligibility.INELIGIBLE
    assert result.eligibility.blocking_findings == (SemanticFinding.SEVERE_AMOUNT_CONFLICT,)
    assert result.relationship.score == pytest.approx(0.725, rel=0.01)

def test_score_purchase_to_gst_exposes_tax_identity_conflict() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='27ZZZZZ9999Z9Z9')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.semantic_findings == (SemanticFinding.TAX_IDENTITY_CONFLICT,)
    assert result.eligibility.status is OneToOneEligibility.INELIGIBLE
    assert result.eligibility.blocking_findings == (SemanticFinding.TAX_IDENTITY_CONFLICT,)
    assert result.relationship.score == pytest.approx(0.625, rel=0.01)

def test_score_purchase_to_gst_exposes_distinct_event_identity_evidence() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='CloudLedger Software Private Limited', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1Z1')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='CLOUDLEDGER SOFTWARE PVT LTD', reference='CL-JUL-456', amount=Decimal('25000.0'), record_date=date(2026, 7, 5), tax_identity='07CLOUD1234A1Z1')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.semantic_findings == (SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,)
    assert result.eligibility.status is OneToOneEligibility.INELIGIBLE
    assert result.eligibility.blocking_findings == (SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,)
    assert result.relationship.score == pytest.approx(0.7)

def test_score_purchase_to_gst_preserves_missing_tax_evidence() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity=None)
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='07ABCDE1234F1Z5')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.signals[SignalName.TAX_IDENTITY] is None
    assert result.semantic_findings == ()
    assert result.relationship.coverage == pytest.approx(0.75)
    assert result.relationship.contradiction_penalty == pytest.approx(1.0)
    assert result.relationship.active_contradictions == ()
    assert result.relationship.base_score == pytest.approx(0.834, rel=0.01)
    assert result.relationship.score == pytest.approx(0.834, rel=0.01)

def test_score_purchase_to_gst_applies_tax_contradiction() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='27ZZZZZ9999Z9Z9')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.signals[SignalName.TAX_IDENTITY] == pytest.approx(0.0)
    assert result.relationship.coverage == pytest.approx(1.0)
    assert result.relationship.contradiction_penalty == pytest.approx(1.0)
    assert result.relationship.active_contradictions == ()
    assert result.relationship.base_score == pytest.approx(0.625, rel=0.01)
    assert result.relationship.score == pytest.approx(0.625, rel=0.01)

def test_score_purchase_to_gst_uses_purchase_to_gst_temporal_window() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='Vendor', reference='INV-1', amount=Decimal('1000.0'), record_date=date(2026, 6, 1), tax_identity=None)
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='Vendor', reference='INV-1', amount=Decimal('1000.0'), record_date=date(2026, 6, 8), tax_identity=None)
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.signals[SignalName.TEMPORAL] == pytest.approx(0.0)

def test_score_purchase_to_gst_returns_pair_scoring_result() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='Vendor', reference='INV-1', amount=Decimal('1000.0'), record_date=date(2026, 6, 1), tax_identity=None)
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='Vendor', reference='INV-1', amount=Decimal('1000.0'), record_date=date(2026, 6, 1), tax_identity=None)
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert isinstance(result, PairScoringResult)
    assert set(result.signals) == set(PURCHASE_TO_GST_POLICY.weights)

def test_low_compatibility_pair_can_remain_one_to_one_eligible() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC', reference='INV-1', amount=Decimal('100.0'), record_date=date(2026, 6, 1), tax_identity=None)
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='XYZ', reference='INV-999', amount=Decimal('500.0'), record_date=date(2026, 6, 1), tax_identity=None)
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.relationship.score < 0.5
    assert result.eligibility.status is OneToOneEligibility.ELIGIBLE
    assert result.eligibility.blocking_findings == ()

def test_high_compatibility_pair_can_be_ineligible() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='CloudLedger Software Private Limited', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1Z1')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='CLOUDLEDGER SOFTWARE PVT LTD', reference='CL-JUL-456', amount=Decimal('25000.0'), record_date=date(2026, 7, 5), tax_identity='07CLOUD1234A1Z1')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.relationship.score >= 0.7
    assert result.eligibility.status is OneToOneEligibility.INELIGIBLE
    assert result.eligibility.blocking_findings == (SemanticFinding.DISTINCT_EVENT_IDENTITY_EVIDENCE,)

def test_purchase_gst_tax_conflict_does_not_apply_compatibility_penalty() -> None:
    purchase = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    gst_record = GSTRecord(record_id='dummy_g', vendor_name='ABC Steel Private Limited', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='29XYZAB5678C1Z2')
    result = score_purchase_to_gst(purchase=purchase, gst_record=gst_record, reference_context=_default_context(), vendor_context=_get_vendor_context())
    assert result.relationship.base_score == pytest.approx(0.636, rel=0.01)
    assert result.relationship.score == pytest.approx(0.636, rel=0.01)
    assert result.relationship.contradiction_penalty == 1.0
    assert result.relationship.active_contradictions == ()
    assert result.eligibility.status is OneToOneEligibility.INELIGIBLE
    assert result.eligibility.blocking_findings == (SemanticFinding.TAX_IDENTITY_CONFLICT,)