import pytest
from recongraph.domain.tax.parser import DeterministicTaxParser, ParsedTaxIdentifierArtifact
from recongraph.domain.tax.observation import TaxObservationState, TaxIdentifierCandidateType


# === GSTIN -> PAN DERIVATION BOUNDARY ===

def test_der_001_valid_gstin_produces_pan():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.gstin_valid is True
    assert art.pan_candidate is not None
    assert art.pan_derived_from_gstin is True

def test_der_002_derived_pan_equals_embedded_segment():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_candidate == art.gstin_candidate[2:12]

def test_der_003_derived_pan_is_not_independent():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.pan_derived_from_gstin is True
    ind = DeterministicTaxParser.parse("ABCDE1234F")
    assert ind.pan_derived_from_gstin is False

def test_der_004_derived_pan_preserves_parent_gstin():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.gstin_candidate == "07ABCDE1234F1Z2"
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_derived_from_gstin is True

def test_der_005_derivation_flag_recorded():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.pan_derived_from_gstin is True

def test_der_006_derived_pan_source_span():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.gstin_candidate[2:12] == art.pan_candidate

def test_der_007_different_state_code_same_pan():
    art_07 = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    art_29 = DeterministicTaxParser.parse("29ABCDE1234F1ZW")
    assert art_07.pan_candidate == art_29.pan_candidate == "ABCDE1234F"

def test_der_008_different_entity_code_same_pan():
    art_1 = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    art_2 = DeterministicTaxParser.parse("07ABCDE1234F2Z1")
    assert art_1.pan_candidate == art_2.pan_candidate == "ABCDE1234F"

def test_der_009_changed_pan_segment_changes_derived_pan():
    art_a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    art_b = DeterministicTaxParser.parse("07BBBBB5678G1ZJ")
    assert art_a.pan_candidate != art_b.pan_candidate

def test_der_010_invalid_gstin_no_derived_pan():
    art = DeterministicTaxParser.parse("A7ABCDE1234F1Z5")
    assert art.gstin_valid is False
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_der_011_uninterpretable_no_derived_pan():
    art = DeterministicTaxParser.parse("07-ABCDE1234F1Z")
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_der_012_placeholder_no_derived_pan():
    art = DeterministicTaxParser.parse("N/A")
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_der_013_missing_no_derived_pan():
    art = DeterministicTaxParser.parse(None)
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_der_014_ocr_corrupted_gstin_no_silent_derivation():
    # O instead of 0 in state code
    art = DeterministicTaxParser.parse("O7ABCDE1234F1Z5")
    assert art.gstin_valid is False
    assert art.pan_candidate is None
    assert art.pan_derived_from_gstin is False

def test_der_015_repeated_parse_determinism():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert a.pan_candidate == b.pan_candidate
    assert a.pan_derived_from_gstin == b.pan_derived_from_gstin
    assert a.gstin_candidate == b.gstin_candidate
    assert a.gstin_valid == b.gstin_valid

def test_der_016_independent_vs_derived_origin_preserved():
    """Critical invariant: VALUE EQUALITY DOES NOT ERASE EVIDENCE ORIGIN."""
    independent = DeterministicTaxParser.parse("ABCDE1234F")
    derived = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert independent.pan_candidate == derived.pan_candidate == "ABCDE1234F"
    assert independent.pan_derived_from_gstin is False
    assert derived.pan_derived_from_gstin is True
    assert derived.gstin_candidate == "07ABCDE1234F1Z2"
    assert independent.gstin_candidate is None
