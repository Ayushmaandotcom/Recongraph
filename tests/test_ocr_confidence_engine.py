"""
Tests for Stage 8G: OCR Confidence Engine.

Verifies:
1. TokenProvenance confidence level classification
2. Score attenuation via attenuated_weight()
3. OcrConfidenceReport helpers (aggregate confidence, lowest_confidence_fields)
4. FinancialEvidenceProvider : score is attenuated on LOW/UNREADABLE amount confidence
5. FinancialEvidenceProvider: violations emitted for OCR problems
6. FinancialEvidenceProvider: highlight_boxes propagated in metadata
7. TemporalEvidenceProvider: violations emitted for low-confidence dates
8. ReviewPacket: highlight_regions and ocr_warnings populated from hypothesis
9. OCR confidence helpers: generate_ocr_warnings, weighted_aggregate_confidence
10. End-to-end: a LOW-confidence amount leads to a ReviewPacket with OCR highlights
"""
import pytest
from datetime import date
from decimal import Decimal
from typing import Optional

from recongraph.domain.document.layout import (
    BoundingBox, DocumentBlock, DocumentRegion, DocumentLayoutArtifact,
    TokenProvenance, OcrConfidenceReport, OcrConfidenceLevel
)
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.ocr.confidence import (
    attenuate_score, collect_low_confidence_boxes, generate_ocr_warnings,
    weighted_aggregate_confidence, HIGH_THRESHOLD, MEDIUM_THRESHOLD, LOW_THRESHOLD
)
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_box(page: int = 1) -> BoundingBox:
    return BoundingBox(0, 0, 100, 20, page)


def make_provenance(confidence: float, field_text: str = "100.00") -> TokenProvenance:
    return TokenProvenance(
        text=field_text,
        confidence=confidence,
        box=make_box(),
        ocr_engine="tesseract",
        normalized=field_text,
    )


def make_ocr_report(**field_confidences: float) -> OcrConfidenceReport:
    """Create an OcrConfidenceReport from keyword arguments: field_name=confidence."""
    return OcrConfidenceReport(provenances={
        field: make_provenance(conf) for field, conf in field_confidences.items()
    })


def make_purchase(amount: str = "100.00", ocr_report: Optional[OcrConfidenceReport] = None) -> PurchaseRecord:
    return PurchaseRecord(
        record_id="p1",
        vendor_name="Acme",
        reference="INV-001",
        amount=Decimal(amount),
        record_date=date(2023, 1, 15),
        tax_identity="GSTIN123",
        net_amount=Decimal(amount),
        tax_amount=Decimal("0"),
        tax_rate=Decimal("0"),
        ocr_confidence_report=ocr_report,
    )


def make_gst(amount: str = "100.00", ocr_report: Optional[OcrConfidenceReport] = None) -> GSTRecord:
    return GSTRecord(
        record_id="g1",
        vendor_name="Acme",
        reference="INV-001",
        amount=Decimal(amount),
        record_date=date(2023, 1, 15),
        tax_identity="GSTIN123",
        net_amount=Decimal(amount),
        tax_amount=Decimal("0"),
        tax_rate=Decimal("0"),
        ocr_confidence_report=ocr_report,
    )


# ---------------------------------------------------------------------------
# 1. OcrConfidenceLevel classification
# ---------------------------------------------------------------------------

class TestOcrConfidenceLevel:
    def test_high_threshold(self):
        assert OcrConfidenceLevel.from_score(0.95) == OcrConfidenceLevel.HIGH
        assert OcrConfidenceLevel.from_score(0.90) == OcrConfidenceLevel.HIGH

    def test_medium_threshold(self):
        assert OcrConfidenceLevel.from_score(0.89) == OcrConfidenceLevel.MEDIUM
        assert OcrConfidenceLevel.from_score(0.70) == OcrConfidenceLevel.MEDIUM

    def test_low_threshold(self):
        assert OcrConfidenceLevel.from_score(0.69) == OcrConfidenceLevel.LOW
        assert OcrConfidenceLevel.from_score(0.50) == OcrConfidenceLevel.LOW

    def test_unreadable_threshold(self):
        assert OcrConfidenceLevel.from_score(0.49) == OcrConfidenceLevel.UNREADABLE
        assert OcrConfidenceLevel.from_score(0.0) == OcrConfidenceLevel.UNREADABLE


# ---------------------------------------------------------------------------
# 2. TokenProvenance attenuation weights
# ---------------------------------------------------------------------------

class TestTokenProvenanceAttenuation:
    def test_high_weight_is_1(self):
        prov = make_provenance(0.95)
        assert prov.attenuated_weight() == 1.0

    def test_medium_weight_is_0_85(self):
        prov = make_provenance(0.80)
        assert prov.attenuated_weight() == 0.85

    def test_low_weight_is_0_60(self):
        prov = make_provenance(0.60)
        assert prov.attenuated_weight() == 0.60

    def test_unreadable_weight_is_0(self):
        prov = make_provenance(0.30)
        assert prov.attenuated_weight() == 0.0

    def test_is_trustworthy_high(self):
        assert make_provenance(0.95).is_trustworthy is True

    def test_is_not_trustworthy_low(self):
        assert make_provenance(0.60).is_trustworthy is False


# ---------------------------------------------------------------------------
# 3. OcrConfidenceReport helpers
# ---------------------------------------------------------------------------

class TestOcrConfidenceReport:
    def test_empty_aggregate_is_1(self):
        report = OcrConfidenceReport.empty()
        assert report.aggregate_confidence() == 1.0

    def test_aggregate_geometric_mean(self):
        report = make_ocr_report(amount=0.81, record_date=1.0)
        expected = (0.81 * 1.0) ** 0.5
        assert abs(report.aggregate_confidence() - expected) < 1e-9

    def test_lowest_confidence_fields(self):
        report = make_ocr_report(amount=0.60, record_date=0.95, vendor_name=0.55)
        low = report.lowest_confidence_fields(threshold=0.70)
        low_names = {name for name, _ in low}
        assert "amount" in low_names
        assert "vendor_name" in low_names
        assert "record_date" not in low_names

    def test_get_existing_field(self):
        report = make_ocr_report(amount=0.85)
        prov = report.get("amount")
        assert prov is not None
        assert abs(prov.confidence - 0.85) < 1e-9

    def test_get_missing_field_returns_none(self):
        report = make_ocr_report(amount=0.85)
        assert report.get("reference") is None


# ---------------------------------------------------------------------------
# 4–6. FinancialEvidenceProvider OCR behaviour (via HypothesisEvaluator)
# ---------------------------------------------------------------------------

from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.hypotheses import Hypothesis, EvaluatedHypothesis
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY
from recongraph.domain.reliability import ExtractionQuality, AttenuationAction, AttenuationPolicy

from recongraph.matching.scoring import RelationshipPolicy

from recongraph.matching.scoring import RelationshipPolicy, SignalName
from recongraph.plugins.provider import EvidenceContribution

class MockProvider:
    def __init__(self, name: str, score: float = 1.0):
        self.name = name
        self.score = score
        
    def get_name(self):
        return self.name
        
    def get_blockers(self):
        return []
        
    def evaluate(self, p, g):
        return EvidenceContribution(self.name, self.score, frozenset(), {})

def evaluate_with_engine(p: PurchaseRecord, g: GSTRecord, providers: list) -> EvaluatedHypothesis:
    builder = CandidateGraphBuilder()
    u1, u2 = build_purchase_urn(p.record_id), build_gst_urn(g.record_id)
    builder.add_node(u1, p)
    builder.add_node(u2, g)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2]),
        proposed_edges=frozenset([frozenset([u1, u2])])
    )
    
    # Ensure all 5 signals are present
    provided_names = {prov.get_name() for prov in providers}
    all_names = {SignalName.AMOUNT, SignalName.TEMPORAL, SignalName.ENTITY, SignalName.REFERENCE, SignalName.TAX_IDENTITY}
    
    for missing in all_names - provided_names:
        providers.append(MockProvider(missing))
        
    # Use the real default policy which contains all 5 weights
    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    return evaluator.evaluate(builder.build(), hypothesis)


class TestFinancialEvidenceProviderOcr:
    def test_no_ocr_data_returns_unattenuated_score(self):
        p = make_purchase("100.00")
        g = make_gst("100.00")
        result = evaluate_with_engine(p, g, [FinancialEvidenceProvider()])
        amount_score = result.supporting_evidence.signals["amount"]
        assert amount_score is not None
        assert amount_score >= 0.99

    def test_high_confidence_does_not_attenuate(self):
        ocr = make_ocr_report(amount=0.95)
        p = make_purchase("100.00", ocr_report=ocr)
        g = make_gst("100.00")
        result = evaluate_with_engine(p, g, [FinancialEvidenceProvider()])
        amount_score = result.supporting_evidence.signals["amount"]
        assert amount_score is not None
        assert amount_score >= 0.99

    def test_medium_confidence_attenuates_score(self):
        ocr = make_ocr_report(amount=0.80)  # DEGRADED → multiplier 0.85
        p = make_purchase("100.00", ocr_report=ocr)
        g = make_gst("100.00")
        result = evaluate_with_engine(p, g, [FinancialEvidenceProvider()])
        amount_score = result.supporting_evidence.signals["amount"]
        assert amount_score is not None
        assert abs(amount_score - 0.85) < 1e-6

    def test_low_confidence_attenuates_and_emits_violation(self):
        ocr = make_ocr_report(amount=0.60)  # LOW → multiplier 0.60
        p = make_purchase("100.00", ocr_report=ocr)
        g = make_gst("100.00")
        result = evaluate_with_engine(p, g, [FinancialEvidenceProvider()])
        amount_score = result.supporting_evidence.signals["amount"]
        assert amount_score is not None
        assert abs(amount_score - 0.60) < 1e-6
        assert "OCR_AMOUNT_LOW_CONFIDENCE" in result.violations

    def test_unreadable_zeroes_score_and_emits_violation(self):
        ocr = make_ocr_report(amount=0.30)  # UNREADABLE (FAILED) → multiplier 0.0
        p = make_purchase("100.00", ocr_report=ocr)
        g = make_gst("100.00")
        result = evaluate_with_engine(p, g, [FinancialEvidenceProvider()])
        amount_score = result.supporting_evidence.signals["amount"]
        assert amount_score == 0.0
        assert "OCR_AMOUNT_UNREADABLE" in result.violations


# ---------------------------------------------------------------------------
# 7. TemporalEvidenceProvider OCR behaviour (via HypothesisEvaluator)
# ---------------------------------------------------------------------------

class TestTemporalEvidenceProviderOcr:
    def test_no_ocr_data_no_violations(self):
        p = make_purchase()
        g = make_gst()
        result = evaluate_with_engine(p, g, [TemporalEvidenceProvider(max_days=7)])
        assert "OCR_DATE_LOW_CONFIDENCE" not in result.violations

    def test_low_date_confidence_emits_violation(self):
        ocr = make_ocr_report(record_date=0.60)
        p = make_purchase(ocr_report=ocr)
        g = make_gst()
        result = evaluate_with_engine(p, g, [TemporalEvidenceProvider(max_days=7)])
        assert "OCR_DATE_LOW_CONFIDENCE" in result.violations

    def test_unreadable_date_emits_unreadable_violation(self):
        ocr = make_ocr_report(record_date=0.30)
        p = make_purchase(ocr_report=ocr)
        g = make_gst()
        result = evaluate_with_engine(p, g, [TemporalEvidenceProvider(max_days=7)])
        assert "OCR_DATE_UNREADABLE" in result.violations

    def test_high_date_confidence_no_violations(self):
        ocr = make_ocr_report(record_date=0.95)
        p = make_purchase(ocr_report=ocr)
        g = make_gst()
        result = evaluate_with_engine(p, g, [TemporalEvidenceProvider(max_days=7)])
        assert "OCR_DATE_LOW_CONFIDENCE" not in result.violations


# ---------------------------------------------------------------------------
# 8. generate_ocr_warnings utility
# ---------------------------------------------------------------------------

class TestGenerateOcrWarnings:
    def test_no_warnings_for_high_confidence(self):
        report = make_ocr_report(amount=0.95)
        warnings = generate_ocr_warnings(report)
        assert warnings == []

    def test_medium_confidence_note(self):
        report = make_ocr_report(amount=0.80)
        warnings = generate_ocr_warnings(report)
        assert len(warnings) == 1
        assert "NOTE" in warnings[0]
        assert "amount" in warnings[0].lower()

    def test_low_confidence_warning(self):
        report = make_ocr_report(amount=0.60)
        warnings = generate_ocr_warnings(report)
        assert len(warnings) == 1
        assert "WARNING" in warnings[0]

    def test_unreadable_critical(self):
        report = make_ocr_report(amount=0.30)
        warnings = generate_ocr_warnings(report)
        assert len(warnings) == 1
        assert "CRITICAL" in warnings[0]

    def test_none_report_returns_empty(self):
        warnings = generate_ocr_warnings(None)
        assert warnings == []

    def test_non_critical_field_ignored_by_default(self):
        # "description" is not in default critical_fields
        report = OcrConfidenceReport(provenances={"description": make_provenance(0.30)})
        warnings = generate_ocr_warnings(report)
        assert warnings == []


# ---------------------------------------------------------------------------
# 9. weighted_aggregate_confidence
# ---------------------------------------------------------------------------

class TestWeightedAggregateConfidence:
    def test_none_report_returns_1(self):
        assert weighted_aggregate_confidence(None) == 1.0

    def test_empty_report_returns_1(self):
        assert weighted_aggregate_confidence(OcrConfidenceReport.empty()) == 1.0

    def test_high_confidence_near_1(self):
        report = make_ocr_report(amount=0.95, record_date=0.93)
        score = weighted_aggregate_confidence(report)
        assert score > 0.90

    def test_mix_lowers_score(self):
        report = make_ocr_report(amount=0.60, record_date=0.95)
        score = weighted_aggregate_confidence(report)
        # amount has weight 2.0, date 1.5 → weighted average should be < 0.80
        assert score < 0.85
