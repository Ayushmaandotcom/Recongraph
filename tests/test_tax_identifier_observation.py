import pytest
from recongraph.domain.tax.parser import DeterministicTaxParser, ParsedTaxIdentifierArtifact
from recongraph.domain.tax.observation import TaxIdentifierObservation, TaxObservationState, TaxIdentifierCandidateType


# === OBSERVATION STATE BOUNDARY CONFORMANCE ===

def test_obs_001_none_input():
    art = DeterministicTaxParser.parse(None)
    assert art.observation.observation_state == TaxObservationState.MISSING
    assert art.observation.raw_value == ""
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.gstin_candidate is None
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_obs_002_empty_string():
    art = DeterministicTaxParser.parse("")
    assert art.observation.observation_state == TaxObservationState.EMPTY
    assert art.observation.raw_value == ""
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.gstin_candidate is None
    assert art.pan_candidate is None

def test_obs_003_single_space():
    art = DeterministicTaxParser.parse(" ")
    assert art.observation.observation_state == TaxObservationState.EMPTY
    assert art.observation.raw_value == " "
    assert art.gstin_candidate is None
    assert art.pan_candidate is None

def test_obs_004_multiple_spaces():
    art = DeterministicTaxParser.parse("   ")
    assert art.observation.observation_state == TaxObservationState.EMPTY
    assert art.observation.raw_value == "   "

def test_obs_005_tab_only():
    art = DeterministicTaxParser.parse("\t")
    assert art.observation.observation_state == TaxObservationState.EMPTY
    assert art.observation.raw_value == "\t"

def test_obs_006_newline_only():
    art = DeterministicTaxParser.parse("\n")
    assert art.observation.observation_state == TaxObservationState.EMPTY
    assert art.observation.raw_value == "\n"

def test_obs_007_unknown_upper():
    art = DeterministicTaxParser.parse("UNKNOWN")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "UNKNOWN"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    # UNKNOWN is 7 chars, not 10 or 15 -> no structural candidate
    assert art.gstin_candidate is None
    assert art.pan_candidate is None

def test_obs_008_unknown_lower():
    art = DeterministicTaxParser.parse("unknown")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "unknown"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_009_unknown_mixed():
    art = DeterministicTaxParser.parse("Unknown")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "Unknown"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_010_na_slash():
    art = DeterministicTaxParser.parse("N/A")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "N/A"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.gstin_candidate is None
    assert art.pan_candidate is None

def test_obs_011_na_lower():
    art = DeterministicTaxParser.parse("n/a")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "n/a"

def test_obs_012_na_upper():
    art = DeterministicTaxParser.parse("NA")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "NA"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_013_na_lower_plain():
    art = DeterministicTaxParser.parse("na")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "na"

def test_obs_014_null_upper():
    art = DeterministicTaxParser.parse("NULL")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "NULL"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_015_null_lower():
    art = DeterministicTaxParser.parse("null")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "null"

def test_obs_016_hyphen():
    art = DeterministicTaxParser.parse("-")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "-"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_017_malformed():
    art = DeterministicTaxParser.parse("MALFORMED")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "MALFORMED"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    # Critical: MALFORMED must NOT become a structurally interpretable identifier
    assert art.gstin_candidate is None
    assert art.pan_candidate is None

def test_obs_018_random_prose():
    art = DeterministicTaxParser.parse("This is random text")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "This is random text"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN

def test_obs_019_pan_shaped():
    art = DeterministicTaxParser.parse("ABCDE1234F")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "ABCDE1234F"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.PAN
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_valid is True
    assert art.pan_derived_from_gstin is False
    assert art.gstin_candidate is None

def test_obs_020_gstin_shaped():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == "07ABCDE1234F1Z2"
    assert art.observation.candidate_type == TaxIdentifierCandidateType.GSTIN
    assert art.gstin_candidate == "07ABCDE1234F1Z2"
    assert art.gstin_valid is True
