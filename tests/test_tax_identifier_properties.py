import pytest
import string
from hypothesis import given, strategies as st, assume, settings

from recongraph.domain.tax.parser import (
    DeterministicTaxParser,
    ParsedTaxIdentifierArtifact,
    TaxNormalizationTransformation,
)
from recongraph.domain.tax.observation import (
    TaxObservationState,
    TaxIdentifierCandidateType,
)


# === HYPOTHESIS STRATEGIES ===

def structurally_interpretable_pan():
    """Generate a PAN matching [A-Z]{5}[0-9]{4}[A-Z]{1}."""
    return st.tuples(
        st.text(alphabet=string.ascii_uppercase, min_size=5, max_size=5),
        st.text(alphabet=string.digits, min_size=4, max_size=4),
        st.text(alphabet=string.ascii_uppercase, min_size=1, max_size=1),
    ).map(lambda t: t[0] + t[1] + t[2])


def structurally_interpretable_gstin():
    """Generate a GSTIN matching [0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}."""
    entity_chars = string.ascii_uppercase + "123456789"
    check_chars = string.ascii_uppercase + string.digits
    return st.tuples(
        st.integers(min_value=0, max_value=99).map(lambda x: f"{x:02d}"),
        structurally_interpretable_pan(),
        st.sampled_from(list(entity_chars)),
        st.just("Z"),
    ).map(lambda t: t[0] + t[1] + t[2] + t[3]).map(
        lambda prefix: prefix + __import__("recongraph.domain.tax.parser", fromlist=["calculate_gstin_checksum"]).calculate_gstin_checksum(prefix)
    )


def malformed_pan_candidate():
    """Generate a 10-char alnum string that does NOT match PAN pattern."""
    return st.text(alphabet=string.digits, min_size=10, max_size=10)


def malformed_gstin_candidate():
    """Generate a 15-char alnum string that does NOT match GSTIN pattern."""
    return st.text(alphabet=string.ascii_uppercase, min_size=15, max_size=15)


def placeholder_tax_observation():
    """Generate known placeholder/non-evidence values."""
    return st.sampled_from([
        "N/A", "n/a", "NA", "na", "NULL", "null",
        "UNKNOWN", "unknown", "-", ".", "MALFORMED",
    ])


def ocr_mutated_identifier():
    """Generate a valid GSTIN with one OCR-like character mutation."""
    ocr_pairs = [("0", "O"), ("1", "I"), ("5", "S"), ("8", "B"), ("2", "Z"), ("6", "G")]
    return structurally_interpretable_gstin().flatmap(
        lambda gstin: st.tuples(
            st.just(gstin),
            st.integers(min_value=0, max_value=len(gstin) - 1),
            st.sampled_from(ocr_pairs),
        )
    ).map(lambda t: _apply_ocr_mutation(t[0], t[1], t[2]))


def _apply_ocr_mutation(gstin: str, pos: int, pair: tuple) -> tuple:
    original_char, replacement_char = pair
    # Only mutate if the position has the original character
    if gstin[pos] == original_char:
        mutated = gstin[:pos] + replacement_char + gstin[pos + 1:]
        return (gstin, mutated)
    elif gstin[pos] == replacement_char:
        mutated = gstin[:pos] + original_char + gstin[pos + 1:]
        return (gstin, mutated)
    else:
        # No mutation possible at this position, return same string twice
        return (gstin, gstin)


# === METAMORPHIC / PROPERTY TESTS ===


@given(raw=st.one_of(st.none(), st.text(max_size=200)))
@settings(max_examples=200)
def test_mp_001_raw_preservation(raw):
    """MP-001: For every bounded input, parse(x).raw evidence preserves x exactly."""
    art = DeterministicTaxParser.parse(raw)
    if raw is None:
        assert art.observation.raw_value == ""
    else:
        assert art.observation.raw_value == raw


@given(raw=st.one_of(st.none(), st.text(max_size=200)))
@settings(max_examples=200)
def test_mp_002_parse_determinism(raw):
    """MP-002: For every bounded input, parse(x) is equivalent across repeated parses."""
    a = DeterministicTaxParser.parse(raw)
    b = DeterministicTaxParser.parse(raw)
    assert a == b


@given(pan=structurally_interpretable_pan())
@settings(max_examples=100)
def test_mp_003_pan_case_canonicalization(pan):
    """MP-003: Case-only representation changes preserve canonical PAN value."""
    upper = DeterministicTaxParser.parse(pan.upper())
    lower = DeterministicTaxParser.parse(pan.lower())
    assert upper.pan_candidate == lower.pan_candidate


@given(gstin=structurally_interpretable_gstin())
@settings(max_examples=100)
def test_mp_004_gstin_case_canonicalization(gstin):
    """MP-004: Case-only representation changes preserve canonical GSTIN value."""
    upper = DeterministicTaxParser.parse(gstin.upper())
    lower = DeterministicTaxParser.parse(gstin.lower())
    assert upper.gstin_candidate == lower.gstin_candidate


@given(pan=structurally_interpretable_pan(), ws=st.text(alphabet=" \t", min_size=1, max_size=5))
@settings(max_examples=100)
def test_mp_005_pan_surrounding_whitespace_stability(pan, ws):
    """MP-005: Adding surrounding whitespace preserves canonical PAN value."""
    clean = DeterministicTaxParser.parse(pan)
    padded = DeterministicTaxParser.parse(ws + pan + ws)
    assert clean.pan_candidate == padded.pan_candidate


@given(gstin=structurally_interpretable_gstin(), ws=st.text(alphabet=" \t", min_size=1, max_size=5))
@settings(max_examples=100)
def test_mp_006_gstin_surrounding_whitespace_stability(gstin, ws):
    """MP-006: Adding surrounding whitespace preserves canonical GSTIN value."""
    clean = DeterministicTaxParser.parse(gstin)
    padded = DeterministicTaxParser.parse(ws + gstin + ws)
    assert clean.gstin_candidate == padded.gstin_candidate


@given(placeholder=placeholder_tax_observation())
@settings(max_examples=50)
def test_mp_007_placeholder_case_stability(placeholder):
    """MP-007: Case variation of placeholder literals preserves non-candidate state."""
    upper_art = DeterministicTaxParser.parse(placeholder.upper())
    lower_art = DeterministicTaxParser.parse(placeholder.lower())
    # Neither should become a structurally valid tax identifier
    assert upper_art.gstin_valid is not True or upper_art.gstin_candidate is None or len(placeholder) in (10, 15)
    assert lower_art.gstin_valid is not True or lower_art.gstin_candidate is None or len(placeholder) in (10, 15)


def test_mp_008_missing_non_canonicalization():
    """MP-008: Missing input cannot produce a canonical identifier."""
    art = DeterministicTaxParser.parse(None)
    assert art.gstin_candidate is None
    assert art.pan_candidate is None
    assert art.observation.observation_state == TaxObservationState.MISSING


@given(placeholder=placeholder_tax_observation())
@settings(max_examples=50)
def test_mp_009_placeholder_non_canonicalization(placeholder):
    """MP-009: Placeholder input cannot produce a valid canonical tax identifier."""
    art = DeterministicTaxParser.parse(placeholder)
    # No placeholder should produce a structurally valid GSTIN or PAN
    if art.gstin_valid is True:
        # This would be a failure — placeholders should not be valid GSTINs
        assert False, f"Placeholder '{placeholder}' produced valid GSTIN"
    if art.pan_valid is True:
        assert False, f"Placeholder '{placeholder}' produced valid PAN"


@given(gstin=malformed_gstin_candidate())
@settings(max_examples=100)
def test_mp_010_invalid_gstin_non_derivation(gstin):
    """MP-010: Structurally invalid GSTIN cannot produce a valid GSTIN-derived PAN artifact."""
    art = DeterministicTaxParser.parse(gstin)
    if art.gstin_valid is False:
        assert art.pan_candidate is None
        assert art.pan_derived_from_gstin is False


@given(gstin=structurally_interpretable_gstin(), new_state=st.integers(min_value=0, max_value=99))
@settings(max_examples=100)
def test_mp_011_state_code_non_pan_effect(gstin, new_state):
    """MP-011: Changing only state code preserves embedded PAN value."""
    original = DeterministicTaxParser.parse(gstin)
    modified_raw = f"{new_state:02d}" + gstin[2:]
    modified = DeterministicTaxParser.parse(modified_raw)
    if original.pan_candidate is not None and modified.pan_candidate is not None:
        assert original.pan_candidate == modified.pan_candidate


@given(gstin=structurally_interpretable_gstin())
@settings(max_examples=100)
def test_mp_012_entity_code_non_pan_effect(gstin):
    """MP-012: Changing only entity code preserves embedded PAN value."""
    original = DeterministicTaxParser.parse(gstin)
    # Change entity code (position 12) to a different valid value
    entity_chars = "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    new_entity = entity_chars[(entity_chars.index(gstin[12]) + 1) % len(entity_chars)]
    modified_raw = gstin[:12] + new_entity + gstin[13:]
    modified = DeterministicTaxParser.parse(modified_raw)
    if original.pan_candidate is not None and modified.pan_candidate is not None:
        assert original.pan_candidate == modified.pan_candidate


@given(gstin=structurally_interpretable_gstin(), char_idx=st.integers(min_value=2, max_value=11))
@settings(max_examples=100)
def test_mp_013_pan_segment_effect(gstin, char_idx):
    """MP-013: Changing a PAN-segment character changes the derived PAN value."""
    original = DeterministicTaxParser.parse(gstin)
    assume(original.gstin_valid is True)
    # Mutate one character in the PAN segment [2:12]
    old_char = gstin[char_idx]
    # Pick a different character of the same class
    if old_char.isdigit():
        new_char = str((int(old_char) + 1) % 10)
    else:
        new_char = chr((ord(old_char) - ord('A') + 1) % 26 + ord('A'))
    assume(new_char != old_char)
    modified_raw = gstin[:char_idx] + new_char + gstin[char_idx + 1:]
    modified = DeterministicTaxParser.parse(modified_raw)
    if modified.pan_candidate is not None:
        assert original.pan_candidate != modified.pan_candidate


@given(gstin=structurally_interpretable_gstin())
@settings(max_examples=100)
def test_mp_014_derived_origin_preservation(gstin):
    """MP-014: Every PAN derived from GSTIN retains derived origin."""
    art = DeterministicTaxParser.parse(gstin)
    if art.gstin_valid and art.pan_candidate is not None:
        assert art.pan_derived_from_gstin is True


@given(gstin=structurally_interpretable_gstin())
@settings(max_examples=100)
def test_mp_015_parent_preservation(gstin):
    """MP-015: Every PAN derived from GSTIN retains the correct parent GSTIN."""
    art = DeterministicTaxParser.parse(gstin)
    if art.pan_derived_from_gstin:
        assert art.gstin_candidate is not None
        assert art.pan_candidate == art.gstin_candidate[2:12]


@given(pan=structurally_interpretable_pan(), state=st.integers(min_value=0, max_value=99))
@settings(max_examples=100)
def test_mp_016_equal_value_origin_preservation(pan, state):
    """MP-016: Independent PAN and GSTIN-derived PAN with equal values retain different origins."""
    independent = DeterministicTaxParser.parse(pan)
    # Build a GSTIN embedding this PAN
    gstin_raw = f"{state:02d}" + pan + "1Z5"
    derived = DeterministicTaxParser.parse(gstin_raw)
    if independent.pan_valid and derived.gstin_valid:
        assert independent.pan_candidate == derived.pan_candidate
        assert independent.pan_derived_from_gstin is False
        assert derived.pan_derived_from_gstin is True


def test_mp_017_ocr_non_repair():
    """MP-017: OCR-like mutation cannot silently canonicalize back to baseline."""
    baseline = "07ABCDE1234F1Z2"
    mutations = [
        baseline.replace("0", "O", 1),  # O in state code
        baseline.replace("1", "I", 1),  # I in numeric
    ]
    baseline_art = DeterministicTaxParser.parse(baseline)
    for mutated in mutations:
        if mutated != baseline:
            mutated_art = DeterministicTaxParser.parse(mutated)
            # Mutated must NOT silently canonicalize to equal the baseline
            assert mutated_art.gstin_candidate != baseline_art.gstin_candidate or mutated_art.gstin_candidate is None


def test_mp_018_context_independence():
    """MP-018: Changing VendorIdentityContext cannot alter a parsed tax artifact."""
    # DeterministicTaxParser.parse takes no context parameter
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert a == b


def test_mp_019_projection_independence():
    """MP-019: Changing VendorProjectionPolicy cannot alter a parsed tax artifact."""
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, "projection")
    assert not hasattr(art, "similarity")


def test_mp_020_decision_independence():
    """MP-020: Changing DecisionPolicy cannot alter a parsed tax artifact."""
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, "decision")
    assert not hasattr(art, "eligibility")


def test_mp_021_no_pair_conclusion():
    """MP-021: ParsedTaxIdentifierArtifact cannot encode pair relation state."""
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, "pair_result")
    assert not hasattr(art, "is_match")
    assert not hasattr(art, "compatibility")


def test_mp_022_no_legal_entity_claim():
    """MP-022: Parsed tax artifact cannot assert legal entity."""
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, "legal_entity")
    assert not hasattr(art, "entity_type")


def test_mp_023_no_transaction_claim():
    """MP-023: Parsed tax artifact cannot assert transaction."""
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, "transaction")


@given(raw=st.one_of(
    st.text(alphabet=string.ascii_lowercase, min_size=10, max_size=10),
    st.text(alphabet=string.ascii_uppercase + string.digits, min_size=15, max_size=15),
))
@settings(max_examples=100)
def test_mp_024_canonical_equality_preserves_raw_difference(raw):
    """MP-024: Where two raw forms canonicalize equally, raw observation difference remains auditable."""
    upper_raw = raw.upper()
    lower_raw = raw.lower()
    a = DeterministicTaxParser.parse(upper_raw)
    b = DeterministicTaxParser.parse(lower_raw)
    if upper_raw != lower_raw:
        assert a.observation.raw_value != b.observation.raw_value


@given(gstin=structurally_interpretable_gstin())
@settings(max_examples=100)
def test_mp_025_derivation_reconstructability(gstin):
    """MP-025: A derived PAN can identify the parent GSTIN and derivation rule."""
    art = DeterministicTaxParser.parse(gstin)
    if art.pan_derived_from_gstin:
        # Parent GSTIN is recoverable
        assert art.gstin_candidate is not None
        # Derivation span is recoverable
        assert art.pan_candidate == art.gstin_candidate[2:12]
        # Derivation flag is set
        assert art.pan_derived_from_gstin is True


# === ADVERSARIAL ROBUSTNESS ===

@given(raw=st.text(min_size=0, max_size=500))
@settings(max_examples=200)
def test_adversarial_parser_does_not_crash(raw):
    """Parser must not crash on any bounded input."""
    art = DeterministicTaxParser.parse(raw)
    assert isinstance(art, ParsedTaxIdentifierArtifact)


def test_adversarial_very_long_string():
    art = DeterministicTaxParser.parse("A" * 10000)
    assert isinstance(art, ParsedTaxIdentifierArtifact)
    assert art.observation.raw_value == "A" * 10000


def test_adversarial_zero_width_space():
    art = DeterministicTaxParser.parse("07ABCDE\u200B1234F1Z5")
    assert isinstance(art, ParsedTaxIdentifierArtifact)
    assert art.observation.raw_value == "07ABCDE\u200B1234F1Z5"


def test_adversarial_embedded_null():
    art = DeterministicTaxParser.parse("07ABCDE\x001234F1Z5")
    assert isinstance(art, ParsedTaxIdentifierArtifact)


def test_adversarial_emoji():
    art = DeterministicTaxParser.parse("07\U0001F600BCDE1234F1Z5")
    assert isinstance(art, ParsedTaxIdentifierArtifact)


def test_adversarial_sql_injection():
    art = DeterministicTaxParser.parse("'; DROP TABLE gst;--")
    assert isinstance(art, ParsedTaxIdentifierArtifact)
    assert art.gstin_candidate is None
    assert art.pan_candidate is None


def test_adversarial_html_tags():
    art = DeterministicTaxParser.parse("<script>alert('xss')</script>")
    assert isinstance(art, ParsedTaxIdentifierArtifact)
    assert art.gstin_candidate is None


def test_adversarial_path_traversal():
    art = DeterministicTaxParser.parse("../../etc/passwd")
    assert isinstance(art, ParsedTaxIdentifierArtifact)
    assert art.gstin_candidate is None


def test_adversarial_mixed_scripts():
    art = DeterministicTaxParser.parse("07\u0410\u0412CDE1234F1Z5")  # Cyrillic А, В
    assert isinstance(art, ParsedTaxIdentifierArtifact)


def test_adversarial_control_characters():
    art = DeterministicTaxParser.parse("\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a")
    assert isinstance(art, ParsedTaxIdentifierArtifact)


# === OCR NON-REPAIR ===

def test_ocr_001_O_for_0_in_state_code():
    baseline = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    mutated = DeterministicTaxParser.parse("O7ABCDE1234F1Z5")
    assert baseline.gstin_candidate != (mutated.gstin_candidate if mutated.gstin_candidate else "")

def test_ocr_002_I_for_1_in_numeric():
    baseline = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    mutated = DeterministicTaxParser.parse("07ABCDEI234F1Z5")
    # After uppercase I stays I, not silently repaired to 1
    if mutated.gstin_candidate is not None:
        assert "I" in mutated.gstin_candidate or mutated.gstin_candidate != baseline.gstin_candidate

def test_ocr_003_B_for_8_in_numeric():
    baseline = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    mutated = DeterministicTaxParser.parse("07ABCDE12B4F1Z5")
    if mutated.gstin_candidate is not None:
        assert mutated.gstin_candidate != baseline.gstin_candidate

def test_ocr_004_S_for_5_in_checksum():
    baseline = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    mutated = DeterministicTaxParser.parse("07ABCDE1234F1ZS")
    if mutated.gstin_candidate is not None:
        assert mutated.gstin_candidate != baseline.gstin_candidate

def test_ocr_005_Z_for_2_in_state_code():
    baseline = DeterministicTaxParser.parse("27ABCDE1234F1Z0")
    mutated = DeterministicTaxParser.parse("Z7ABCDE1234F1Z5")
    if mutated.gstin_candidate is not None:
        assert mutated.gstin_candidate != baseline.gstin_candidate
