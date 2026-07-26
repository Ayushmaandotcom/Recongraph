"""
OCR Confidence helpers: scoring attenuation and warning generation.
These are pure functions — no side effects, fully deterministic.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from recongraph.domain.document.layout import OcrConfidenceReport, TokenProvenance, BoundingBox

# Confidence thresholds
HIGH_THRESHOLD = 0.90
MEDIUM_THRESHOLD = 0.70
LOW_THRESHOLD = 0.50

# Field importance weights for aggregate confidence
FIELD_IMPORTANCE: dict[str, float] = {
    "amount":      2.0,   # Critical — attenuation has the largest effect
    "record_date": 1.5,   # Important for temporal gating
    "vendor_name": 1.2,   # Moderate
    "reference":   1.0,   # Standard
    "tax_identity": 1.5,  # Important for GST matching
}


def attenuate_score(
    base_score: Optional[float],
    field_name: str,
    report: "Optional[OcrConfidenceReport]",
) -> Tuple[Optional[float], Optional["TokenProvenance"]]:
    """
    Attenuate a base evidence score based on OCR confidence for `field_name`.

    Returns:
        (attenuated_score, provenance_or_None)
        - attenuated_score: base_score * attenuated_weight, or base_score if no OCR data.
        - provenance: the TokenProvenance if one was found, else None.
    """
    if base_score is None or report is None:
        return base_score, None

    prov = report.get(field_name)
    if prov is None:
        return base_score, None

    weight = prov.attenuated_weight()
    return base_score * weight, prov


def collect_low_confidence_boxes(
    report: "Optional[OcrConfidenceReport]",
    threshold: float = MEDIUM_THRESHOLD,
) -> List["BoundingBox"]:
    """Return all bounding boxes from fields whose confidence < threshold."""
    if report is None:
        return []
    boxes = []
    for _field, prov in report.lowest_confidence_fields(threshold):
        if prov.box is not None:
            boxes.append(prov.box)
    return boxes


def generate_ocr_warnings(
    report: "Optional[OcrConfidenceReport]",
    critical_fields: Optional[List[str]] = None,
) -> List[str]:
    """
    Generate human-readable OCR warning strings for a ReviewPacket checklist.

    Args:
        report: OcrConfidenceReport for a single record.
        critical_fields: Fields to highlight specifically. Defaults to amount + date.
    """
    if report is None:
        return []

    if critical_fields is None:
        critical_fields = ["amount", "record_date", "vendor_name", "reference", "tax_identity"]

    warnings = []
    for field_name, prov in report.provenances.items():
        if field_name not in critical_fields:
            continue
        level_label = prov.level.value.upper()
        if prov.confidence < LOW_THRESHOLD:
            warnings.append(
                f"CRITICAL: OCR confidence for '{field_name}' is UNREADABLE "
                f"({prov.confidence:.0%}). Manual re-entry required."
            )
        elif prov.confidence < MEDIUM_THRESHOLD:
            warnings.append(
                f"WARNING: OCR confidence for '{field_name}' is LOW "
                f"({prov.confidence:.0%}). Verify against original document."
            )
        elif prov.confidence < HIGH_THRESHOLD:
            warnings.append(
                f"NOTE: OCR confidence for '{field_name}' is MEDIUM "
                f"({prov.confidence:.0%}). Consider spot-checking."
            )
    return warnings


def weighted_aggregate_confidence(
    report: "Optional[OcrConfidenceReport]",
) -> float:
    """
    Compute a weighted aggregate confidence score using FIELD_IMPORTANCE weights.
    Returns 1.0 if no report (no OCR data → assume full confidence).
    """
    if report is None or not report.provenances:
        return 1.0

    total_weight = 0.0
    weighted_sum = 0.0
    for field_name, prov in report.provenances.items():
        w = FIELD_IMPORTANCE.get(field_name, 1.0)
        total_weight += w
        weighted_sum += w * prov.confidence

    if total_weight == 0.0:
        return 1.0
    return weighted_sum / total_weight
