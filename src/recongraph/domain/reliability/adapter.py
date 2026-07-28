from typing import Any
from recongraph.domain.document.layout import OcrConfidenceReport
from .dimensions import ExtractionQuality, ParserQuality, Completeness, VerificationState, ConfidenceProvenance
from .reasons import ReliabilityReason
from .profile import ReliabilityProfile, FieldReliability, ReliabilityEnvelope

def convert_ocr_report_to_envelope(report: OcrConfidenceReport) -> ReliabilityEnvelope:
    """
    Phase 1 coexistence bridge: Converts legacy OcrConfidenceReport into a new ReliabilityEnvelope.
    """
    profiles = []
    
    # Check fields in the report: amount, date, vendor
    for field_name in ["amount", "record_date", "vendor_name"]:
        prov = report.get(field_name)
        if prov is None:
            continue
            
        score = prov.confidence
            
        if score >= 0.90:
            ext_quality = ExtractionQuality.HIGH
            reason = ReliabilityReason.OCR_HIGH_CONFIDENCE
        elif score >= 0.70:
            ext_quality = ExtractionQuality.DEGRADED
            reason = ReliabilityReason.OCR_MEDIUM_CONFIDENCE
        elif score >= 0.50:
            ext_quality = ExtractionQuality.LOW
            reason = ReliabilityReason.OCR_LOW_CONFIDENCE
        else:
            ext_quality = ExtractionQuality.FAILED
            reason = ReliabilityReason.OCR_UNREADABLE
            
        audit_metadata: dict[str, Any] = {"confidence": score}
        
        if prov.box:
            audit_metadata["box"] = prov.box

        profile = ReliabilityProfile(
            extraction_quality=ext_quality,
            parser_quality=ParserQuality.CANONICAL,  # Default for OCR
            completeness=Completeness.PRESENT,
            verification_state=VerificationState.UNVERIFIED,
            confidence_provenance=ConfidenceProvenance.ENGINE_REPORTED,
            reasons=(reason,),
            source_id=prov.ocr_engine or "legacy_ocr",
            audit_metadata=audit_metadata
        )
        
        profiles.append(FieldReliability(field_name=field_name, profile=profile))
        
    return ReliabilityEnvelope(profiles=tuple(profiles))
