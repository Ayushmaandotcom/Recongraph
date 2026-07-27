import pytest
from recongraph.domain.tax.parser import DeterministicTaxParser, ParsedTaxIdentifierArtifact, GSTIN_PATTERN, PAN_PATTERN
from recongraph.domain.tax.observation import TaxIdentifierObservation, TaxObservationState, TaxIdentifierCandidateType



# === GSTIN STRUCTURAL CONFORMANCE ===

def test_gst_001_accepted_gstin():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art.gstin_candidate == "07ABCDE1234F1Z2"
    assert art.gstin_valid is True
    assert art.observation.candidate_type == TaxIdentifierCandidateType.GSTIN

def test_gst_002_lowercase_gstin():
    art = DeterministicTaxParser.parse("07abcde1234f1z2")
    assert art.gstin_candidate == "07ABCDE1234F1Z2"
    assert art.gstin_valid is True

def test_gst_003_whitespace_gstin():
    art = DeterministicTaxParser.parse(" 07ABCDE1234F1Z2 ")
    assert art.gstin_candidate == "07ABCDE1234F1Z2"
    assert art.gstin_valid is True
    assert art.observation.raw_value == " 07ABCDE1234F1Z2 "  # raw preserved

def test_gst_004_14_char_not_gstin():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z")
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.gstin_candidate is None

def test_gst_005_16_char_not_gstin():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z25")
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.gstin_candidate is None

def test_gst_006_letter_in_state_code():
    art = DeterministicTaxParser.parse("A7ABCDE1234F1Z5")
    assert art.gstin_candidate == "A7ABCDE1234F1Z5"
    assert art.gstin_valid is False
    assert art.pan_candidate is None

def test_gst_007_digit_where_alpha_needed():
    art = DeterministicTaxParser.parse("071BCDE1234F1Z5")
    assert art.gstin_candidate == "071BCDE1234F1Z5"
    assert art.gstin_valid is False
    assert art.pan_candidate is None

def test_gst_008_alpha_in_pan_numeric():
    art = DeterministicTaxParser.parse("07ABCDEA234F1Z5")
    assert art.gstin_candidate == "07ABCDEA234F1Z5"
    assert art.gstin_valid is False
    assert art.pan_candidate is None

def test_gst_009_zero_entity_code():
    art = DeterministicTaxParser.parse("07ABCDE1234F0Z5")
    assert art.gstin_candidate == "07ABCDE1234F0Z5"
    assert art.gstin_valid is False
    assert art.pan_candidate is None

def test_gst_010_invalid_conventional_position():
    art = DeterministicTaxParser.parse("07ABCDE1234F1A5")
    assert art.gstin_candidate == "07ABCDE1234F1A5"
    assert art.gstin_valid is False

def test_gst_011_internal_whitespace():
    art = DeterministicTaxParser.parse("07 ABCDE1234F1Z5")
    assert art.gstin_candidate is None

def test_gst_012_embedded_hyphen():
    art = DeterministicTaxParser.parse("07-ABCDE1234F1Z5")
    assert art.gstin_candidate is None

def test_gst_013_embedded_slash():
    art = DeterministicTaxParser.parse("07/ABCDE1234F1Z5")
    assert art.gstin_candidate is None

def test_gst_014_embedded_newline():
    art = DeterministicTaxParser.parse("07ABCDE\n1234F1Z5")
    assert art.gstin_candidate is None

def test_gst_015_all_digits_15_char():
    art = DeterministicTaxParser.parse("012345678901234")
    assert art.gstin_candidate == "012345678901234"
    assert art.gstin_valid is False

def test_gst_016_all_alpha_15_char():
    art = DeterministicTaxParser.parse("ABCDEFGHIJKLMNO")
    assert art.gstin_candidate == "ABCDEFGHIJKLMNO"
    assert art.gstin_valid is False

def test_gst_017_unicode_homoglyph():
    # Cyrillic 'А' (U+0410) vs Latin 'A'
    cyrillic_a = "\u0410"
    art = DeterministicTaxParser.parse(f"07{cyrillic_a}BCDE1234F1Z5")
    # After NFKC normalization, Cyrillic А should remain Cyrillic А (not mapped to Latin A)
    # So the resulting string may not match GSTIN pattern
    assert art.observation.observation_state == TaxObservationState.PRESENT
    assert art.observation.raw_value == f"07{cyrillic_a}BCDE1234F1Z5"

def test_gst_018_valid_gstin_components():
    art = DeterministicTaxParser.parse("27BBBBB5678G2ZG")
    assert art.gstin_valid is True
    assert art.gstin_candidate == "27BBBBB5678G2ZG"
    assert art.pan_candidate == "BBBBB5678G"
    assert art.pan_derived_from_gstin is True

def test_gst_019_checksum_position_letter():
    # Checksum position (last char) can be [0-9A-Z]
    art_digit = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    art_letter = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert art_digit.gstin_valid is True
    assert art_letter.gstin_valid is True

def test_gst_020_special_chars_in_15_char():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z!")
    # Has '!' -> not alnum -> no gstin_candidate
    assert art.gstin_candidate is None


# === PAN STRUCTURAL CONFORMANCE ===

def test_pan_001_accepted_pan():
    art = DeterministicTaxParser.parse("ABCDE1234F")
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_valid is True
    assert art.pan_derived_from_gstin is False
    assert art.observation.candidate_type == TaxIdentifierCandidateType.PAN

def test_pan_002_lowercase_pan():
    art = DeterministicTaxParser.parse("abcde1234f")
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_valid is True

def test_pan_003_whitespace_pan():
    art = DeterministicTaxParser.parse(" ABCDE1234F ")
    assert art.pan_candidate == "ABCDE1234F"
    assert art.pan_valid is True
    assert art.observation.raw_value == " ABCDE1234F "

def test_pan_004_9_char_not_pan():
    art = DeterministicTaxParser.parse("ABCDE1234")
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.pan_candidate is None

def test_pan_005_11_char_not_pan():
    art = DeterministicTaxParser.parse("ABCDE1234FG")
    assert art.observation.candidate_type == TaxIdentifierCandidateType.UNKNOWN
    assert art.pan_candidate is None

def test_pan_006_digit_in_alpha_prefix():
    art = DeterministicTaxParser.parse("1BCDE1234F")
    assert art.pan_candidate == "1BCDE1234F"
    assert art.pan_valid is False

def test_pan_007_letter_in_numeric():
    art = DeterministicTaxParser.parse("ABCDEA234F")
    assert art.pan_candidate == "ABCDEA234F"
    assert art.pan_valid is False

def test_pan_008_digit_in_final_alpha():
    art = DeterministicTaxParser.parse("ABCDE12341")
    assert art.pan_candidate == "ABCDE12341"
    assert art.pan_valid is False

def test_pan_009_internal_whitespace():
    art = DeterministicTaxParser.parse("ABCDE 1234F")
    assert art.pan_candidate is None

def test_pan_010_hyphen():
    art = DeterministicTaxParser.parse("ABCDE-1234F")
    assert art.pan_candidate is None

def test_pan_011_slash():
    art = DeterministicTaxParser.parse("ABCDE/1234F")
    assert art.pan_candidate is None

def test_pan_012_newline():
    art = DeterministicTaxParser.parse("ABCDE\n1234F")
    assert art.pan_candidate is None

def test_pan_013_all_digits_10_char():
    art = DeterministicTaxParser.parse("0123456789")
    assert art.pan_candidate == "0123456789"
    assert art.pan_valid is False

def test_pan_014_all_alpha_10_char():
    art = DeterministicTaxParser.parse("ABCDEFGHIJ")
    assert art.pan_candidate == "ABCDEFGHIJ"
    assert art.pan_valid is False

def test_pan_015_malformed_with_special_char():
    art = DeterministicTaxParser.parse("MALFORMED!")
    assert art.pan_candidate is None

def test_pan_016_identical_parsed_twice():
    a = DeterministicTaxParser.parse("XYZXY6789Q")
    b = DeterministicTaxParser.parse("XYZXY6789Q")
    assert a.pan_candidate == b.pan_candidate
    assert a.pan_valid == b.pan_valid
    assert a.observation.raw_value == b.observation.raw_value

def test_pan_017_same_canonical_different_repr():
    a = DeterministicTaxParser.parse("abcde1234f")
    b = DeterministicTaxParser.parse(" ABCDE1234F ")
    assert a.pan_candidate == b.pan_candidate
    assert a.pan_valid == b.pan_valid
    assert a.observation.raw_value != b.observation.raw_value

def test_pan_018_unknown_string():
    art = DeterministicTaxParser.parse("UNKNOWN")
    assert art.pan_candidate is None

def test_pan_019_na_string():
    art = DeterministicTaxParser.parse("N/A")
    assert art.pan_candidate is None

def test_pan_020_malformed_string():
    art = DeterministicTaxParser.parse("MALFORMED")
    assert art.pan_candidate is None


# === LEGACY BOUNDARY CHARACTERIZATION ===
# These test KNOWN DEFECTS that must remain until T3.
# They are NOT correct behavior. They are architectural canaries.
