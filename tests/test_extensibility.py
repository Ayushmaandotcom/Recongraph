import pytest
from decimal import Decimal
from datetime import date
from collections.abc import Iterable

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.reliability import (
    ReliabilityEnvelope,
    FieldReliability,
    ReliabilityProfile,
    ExtractionQuality,
    ParserQuality,
    Completeness,
    VerificationState,
    ConfidenceProvenance,
    ReliabilityReason
)
from recongraph.domain.document.layout import BoundingBox
from recongraph.graph.hypotheses import EvaluatedHypothesis, Hypothesis
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.review import ReviewPacketBuilder, _collect_ocr_data_from_records

# 1. Extensibility Test: Implement a completely new observation source (Barcode)
def test_barcode_extensibility():
    """
    Simulates a Barcode decoding source contributing to the reliability envelope,
    proving the framework can handle new sources without core modifications.
    """
    # Simulate a barcode that extracted the reference number perfectly
    barcode_profile = ReliabilityProfile(
        extraction_quality=ExtractionQuality.AUTHORITATIVE,
        parser_quality=ParserQuality.CANONICAL,
        completeness=Completeness.PRESENT,
        verification_state=VerificationState.UNVERIFIED,
        confidence_provenance=ConfidenceProvenance.ENGINE_REPORTED,
        reasons=(ReliabilityReason.OCR_HIGH_CONFIDENCE,), # Note: In a real system, we'd add BARCODE_SCANNED to ReliabilityReason
        source_id="qr_decoder_v1",
        audit_metadata={"barcode_type": "QR", "confidence": 1.0}
    )
    
    envelope = ReliabilityEnvelope(
        profiles=(
            FieldReliability(field_name="reference", profile=barcode_profile),
        )
    )
    
    p = PurchaseRecord(
        record_id="p1", vendor_name="Vendor", reference="INV-123", 
        amount=Decimal("100"), record_date=date(2023, 1, 1),
        tax_identity="T1",
        reliability_envelope=envelope
    )
    
    # We just ensure it doesn't crash the review process or evaluator, and is preserved.
    assert p.reliability_envelope is not None
    
    boxes, warnings = _collect_ocr_data_from_records([p], [])
    assert len(boxes) == 0
    assert len(warnings) == 0

# 2. Purity Test: Ensure review.py correctly extracts low-confidence boxes/warnings
def test_review_packet_extracts_reliability_warnings():
    box = BoundingBox(x0=10, y0=20, x1=30, y1=40, page_num=1)
    
    low_confidence_profile = ReliabilityProfile(
        extraction_quality=ExtractionQuality.LOW,
        parser_quality=ParserQuality.CANONICAL,
        completeness=Completeness.PRESENT,
        verification_state=VerificationState.UNVERIFIED,
        confidence_provenance=ConfidenceProvenance.ENGINE_REPORTED,
        reasons=(ReliabilityReason.OCR_LOW_CONFIDENCE,),
        source_id="tesseract",
        audit_metadata={"confidence": 0.6, "box": box}
    )
    
    envelope = ReliabilityEnvelope(
        profiles=(
            FieldReliability(field_name="amount", profile=low_confidence_profile),
        )
    )
    
    p = PurchaseRecord(
        record_id="p2", vendor_name="Vendor", reference="INV-456", 
        amount=Decimal("100"), record_date=date(2023, 1, 1),
        tax_identity="T1",
        reliability_envelope=envelope
    )
    g = GSTRecord(
        record_id="g1", vendor_name="Vendor", reference="INV-456", 
        amount=Decimal("100"), record_date=date(2023, 1, 1),
        tax_identity="T1"
    )
    
    builder = CandidateGraphBuilder()
    u1, u2 = build_purchase_urn(p.record_id), build_gst_urn(g.record_id)
    builder.add_node(u1, p)
    builder.add_node(u2, g)
    
    hypothesis = Hypothesis(
        component_nodes=frozenset([u1, u2]),
        proposed_edges=frozenset([frozenset([u1, u2])])
    )
    
    eval_hyp = EvaluatedHypothesis(
        hypothesis=hypothesis, score=0.8, coverage=1.0, 
        eligibility=None, supporting_evidence={}, violations=frozenset()
    )
    
    # The review.py system should extract the box directly from the record envelope
    from recongraph.graph.decision import ReconciliationDecision, DecisionAction
    decision = ReconciliationDecision(
        action=DecisionAction.REVIEW_AMBIGUOUS,
        selected_hypothesis=eval_hyp,
        competitors=(),
        rationale="test"
    )
    
    review_builder = ReviewPacketBuilder()
    packet = review_builder.build(decision, None, builder.build())
    
    assert packet is not None
    assert len(packet.highlight_regions) == 1
    assert packet.highlight_regions[0] == box
    
    assert "OCR_AMOUNT_WARNING" in packet.ocr_warnings
    assert "OCR_AMOUNT_WARNING" in packet.checklist
