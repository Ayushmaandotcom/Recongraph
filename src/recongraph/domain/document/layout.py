from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Tuple


class DocumentRegion(Enum):
    HEADER = auto()
    FOOTER = auto()
    TOTALS_BLOCK = auto()
    SIGNATURE = auto()
    TABLE_ROW = auto()
    VENDOR_DETAILS = auto()


@dataclass(frozen=True)
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float
    page_num: int

    def overlaps(self, other: "BoundingBox") -> bool:
        if self.page_num != other.page_num:
            return False
        return not (self.x1 < other.x0 or self.x0 > other.x1 or self.y1 < other.y0 or self.y0 > other.y1)

    def contains(self, other: "BoundingBox") -> bool:
        if self.page_num != other.page_num:
            return False
        return (self.x0 <= other.x0 and self.x1 >= other.x1 and
                self.y0 <= other.y0 and self.y1 >= other.y1)


@dataclass(frozen=True)
class DocumentBlock:
    region_type: DocumentRegion
    box: BoundingBox
    text: Optional[str] = None
    confidence: float = 1.0


@dataclass(frozen=True)
class DocumentLayoutArtifact:
    """Represents the structural map of a document."""
    blocks: tuple[DocumentBlock, ...]

    def get_blocks_by_region(self, region: DocumentRegion) -> List[DocumentBlock]:
        return [b for b in self.blocks if b.region_type == region]


# ---------------------------------------------------------------------------
# Stage 8G: Token-level OCR Provenance
# ---------------------------------------------------------------------------

class OcrConfidenceLevel(Enum):
    """Semantic classification of an OCR confidence score."""
    HIGH = "high"         # >= 0.90 — reliably extracted
    MEDIUM = "medium"     # 0.70–0.90 — usable, but note
    LOW = "low"           # 0.50–0.70 — flag for human review
    UNREADABLE = "unreadable"  # < 0.50 — do not trust

    @classmethod
    def from_score(cls, score: float) -> "OcrConfidenceLevel":
        if score >= 0.90:
            return cls.HIGH
        elif score >= 0.70:
            return cls.MEDIUM
        elif score >= 0.50:
            return cls.LOW
        else:
            return cls.UNREADABLE


@dataclass(frozen=True)
class TokenProvenance:
    """
    Tracks the physical origin and OCR reliability of a single extracted token.

    Attributes:
        text:        The raw extracted text from the OCR engine.
        confidence:  OCR engine confidence in [0, 1]. 1.0 = certain.
        box:         Bounding box on the page (None if unknown).
        ocr_engine:  Identifier of the OCR backend that produced the token.
        normalized:  The downstream-normalised value (e.g. "1000.00" from "1,000.00").
    """
    text: str
    confidence: float
    box: Optional[BoundingBox] = None
    ocr_engine: str = "unknown"
    normalized: Optional[str] = None

    @property
    def level(self) -> OcrConfidenceLevel:
        return OcrConfidenceLevel.from_score(self.confidence)

    @property
    def is_trustworthy(self) -> bool:
        """True if confidence is HIGH or MEDIUM."""
        return self.confidence >= 0.70

    def attenuated_weight(self) -> float:
        """
        Returns a multiplier [0, 1] to apply to a downstream evidence score.
        HIGH → 1.0, MEDIUM → 0.85, LOW → 0.60, UNREADABLE → 0.0
        """
        mapping = {
            OcrConfidenceLevel.HIGH: 1.0,
            OcrConfidenceLevel.MEDIUM: 0.85,
            OcrConfidenceLevel.LOW: 0.60,
            OcrConfidenceLevel.UNREADABLE: 0.0,
        }
        return mapping[self.level]


@dataclass(frozen=True)
class OcrConfidenceReport:
    """
    Aggregated provenance map for all structured fields on a single record.

    Keys are field names (e.g. "amount", "record_date", "vendor_name", "reference").
    Values are the corresponding TokenProvenance objects.
    """
    provenances: Dict[str, TokenProvenance]

    def get(self, field_name: str) -> Optional[TokenProvenance]:
        return self.provenances.get(field_name)

    def lowest_confidence_fields(self, threshold: float = 0.70) -> List[Tuple[str, TokenProvenance]]:
        """Return all (field, provenance) pairs where confidence < threshold."""
        return [
            (name, prov)
            for name, prov in self.provenances.items()
            if prov.confidence < threshold
        ]

    def aggregate_confidence(self) -> float:
        """Geometric mean of all confidence scores; 1.0 if no provenances."""
        if not self.provenances:
            return 1.0
        product = 1.0
        for prov in self.provenances.values():
            product *= prov.confidence
        return product ** (1.0 / len(self.provenances))

    @classmethod
    def empty(cls) -> "OcrConfidenceReport":
        return cls(provenances={})
