import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum, auto

from recongraph.domain.tax.observation import (
    TaxIdentifierObservation,
    TaxObservationState,
    TaxIdentifierCandidateType
)

GSTIN_PATTERN = re.compile(r"^([0-9]{2})([A-Z]{5}[0-9]{4}[A-Z]{1})([1-9A-Z]{1})(Z)([0-9A-Z]{1})$")
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

def calculate_gstin_checksum(gstin_14: str) -> str:
    """Calculate the Mod36 checksum for a 14-character GSTIN prefix."""
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    factor = 1
    total_sum = 0
    for char in gstin_14:
        try:
            val = charset.index(char)
        except ValueError:
            return ""
        product = val * factor
        total_sum += (product // 36) + (product % 36)
        factor = 2 if factor == 1 else 1
    
    checksum_val = (36 - (total_sum % 36)) % 36
    return charset[checksum_val]

class TaxNormalizationTransformation(Enum):
    UNICODE_NORMALIZATION = auto()
    CASE_NORMALIZATION = auto()
    WHITESPACE_STRIP = auto()

@dataclass(frozen=True)
class TaxNormalizationEvent:
    transformation_type: TaxNormalizationTransformation
    before_value: str
    after_value: str
    rule_name: str

@dataclass(frozen=True)
class ParsedTaxIdentifierArtifact:
    """
    Deterministic extraction of structure from a tax identifier string.
    Does not interpret pairwise relationships.
    """
    observation: TaxIdentifierObservation
    
    gstin_candidate: Optional[str]
    gstin_valid: Optional[bool]
    
    pan_candidate: Optional[str]
    pan_valid: Optional[bool]
    
    pan_derived_from_gstin: bool
    
    normalization_events: Tuple[TaxNormalizationEvent, ...]

    def to_dict(self) -> dict:
        return {
            "observation": {
                "raw_value": self.observation.raw_value,
                "source_field_identity": self.observation.source_field_identity,
                "candidate_type": self.observation.candidate_type.name,
                "observation_state": self.observation.observation_state.name,
            },
            "gstin_candidate": self.gstin_candidate,
            "gstin_valid": self.gstin_valid,
            "pan_candidate": self.pan_candidate,
            "pan_valid": self.pan_valid,
            "pan_derived_from_gstin": self.pan_derived_from_gstin,
            "normalization_events": [
                {
                    "transformation_type": e.transformation_type.name,
                    "before_value": e.before_value,
                    "after_value": e.after_value,
                    "rule_name": e.rule_name,
                }
                for e in self.normalization_events
            ],
        }

class DeterministicTaxParser:
    """
    Context-independent parser for raw tax identifiers.
    Extracts structure and records normalization explicitly.
    """
    
    VERSION = "1.0.0"
    
    @classmethod
    def _create_observation(cls, raw: Optional[str], field_id: str) -> TaxIdentifierObservation:
        if raw is None:
            return TaxIdentifierObservation(
                raw_value="",
                source_field_identity=field_id,
                candidate_type=TaxIdentifierCandidateType.UNKNOWN,
                observation_state=TaxObservationState.MISSING
            )
            
        if not str(raw).strip():
            return TaxIdentifierObservation(
                raw_value=str(raw),
                source_field_identity=field_id,
                candidate_type=TaxIdentifierCandidateType.UNKNOWN,
                observation_state=TaxObservationState.EMPTY
            )
            
        # We classify purely by length of stripped string for candidate type
        stripped = str(raw).strip()
        candidate = TaxIdentifierCandidateType.UNKNOWN
        if len(stripped) == 15:
            candidate = TaxIdentifierCandidateType.GSTIN
        elif len(stripped) == 10:
            candidate = TaxIdentifierCandidateType.PAN
            
        return TaxIdentifierObservation(
            raw_value=str(raw),
            source_field_identity=field_id,
            candidate_type=candidate,
            observation_state=TaxObservationState.PRESENT
        )
    
    @classmethod
    def parse(cls, raw: Optional[str], field_id: str = "tax_identity") -> ParsedTaxIdentifierArtifact:
        obs = cls._create_observation(raw, field_id)
        
        if obs.observation_state in (TaxObservationState.MISSING, TaxObservationState.EMPTY):
            return ParsedTaxIdentifierArtifact(
                observation=obs,
                gstin_candidate=None,
                gstin_valid=None,
                pan_candidate=None,
                pan_valid=None,
                pan_derived_from_gstin=False,
                normalization_events=()
            )
            
        events: List[TaxNormalizationEvent] = []
        raw_str = str(raw)
        
        unicode_norm = unicodedata.normalize("NFKC", raw_str)
        if unicode_norm != raw_str:
            events.append(TaxNormalizationEvent(
                transformation_type=TaxNormalizationTransformation.UNICODE_NORMALIZATION,
                before_value=raw_str,
                after_value=unicode_norm,
                rule_name="NFKC"
            ))
            
        stripped = unicode_norm.strip()
        if stripped != unicode_norm:
            events.append(TaxNormalizationEvent(
                transformation_type=TaxNormalizationTransformation.WHITESPACE_STRIP,
                before_value=unicode_norm,
                after_value=stripped,
                rule_name="STRIP"
            ))
            
        upper_cased = stripped.upper()
        if upper_cased != stripped:
            events.append(TaxNormalizationEvent(
                transformation_type=TaxNormalizationTransformation.CASE_NORMALIZATION,
                before_value=stripped,
                after_value=upper_cased,
                rule_name="UPPER"
            ))
            
        final_str = upper_cased
        
        gstin_candidate = None
        gstin_valid = None
        pan_candidate = None
        pan_valid = None
        pan_derived = False
        
        if len(final_str) == 15 and final_str.isalnum():
            gstin_candidate = final_str
            gstin_valid = bool(GSTIN_PATTERN.match(final_str))
            if gstin_valid:
                expected_checksum = calculate_gstin_checksum(final_str[:14])
                gstin_valid = (expected_checksum == final_str[14])
            if gstin_valid:
                pan_candidate = final_str[2:12]
                pan_valid = True
                pan_derived = True
        elif len(final_str) == 10 and final_str.isalnum():
            pan_candidate = final_str
            pan_valid = bool(PAN_PATTERN.match(final_str))
            
        return ParsedTaxIdentifierArtifact(
            observation=obs,
            gstin_candidate=gstin_candidate,
            gstin_valid=gstin_valid,
            pan_candidate=pan_candidate,
            pan_valid=pan_valid,
            pan_derived_from_gstin=pan_derived,
            normalization_events=tuple(events)
        )
