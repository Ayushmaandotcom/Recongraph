import pytest
from recongraph.domain.tax.parser import DeterministicTaxParser, ParsedTaxIdentifierArtifact, TaxNormalizationEvent, TaxNormalizationTransformation
from recongraph.domain.tax.observation import TaxIdentifierObservation, TaxObservationState, TaxIdentifierCandidateType


# === ARTIFACT IDENTITY CONTRACT ===

def test_aid_001_repeated_parse_identical():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert a == b

def test_aid_002_different_raw_different_artifact():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse(" 07abcde1234f1z2 ")
    assert a != b
    assert a.gstin_candidate == b.gstin_candidate

def test_aid_003_raw_provenance_preserved():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse(" 07abcde1234f1z5 ")
    assert a.observation.raw_value == "07ABCDE1234F1Z2"
    assert b.observation.raw_value == " 07abcde1234f1z5 "

def test_aid_004_normalization_events_whitespace():
    art = DeterministicTaxParser.parse(" 07ABCDE1234F1Z2 ")
    strip_events = [e for e in art.normalization_events if e.transformation_type == TaxNormalizationTransformation.WHITESPACE_STRIP]
    assert len(strip_events) >= 1
    assert strip_events[0].before_value != strip_events[0].after_value

def test_aid_005_normalization_events_case():
    art = DeterministicTaxParser.parse("07abcde1234f1z5")
    case_events = [e for e in art.normalization_events if e.transformation_type == TaxNormalizationTransformation.CASE_NORMALIZATION]
    assert len(case_events) >= 1

def test_aid_006_no_normalization_for_canonical_input():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert len(art.normalization_events) == 0

def test_aid_007_context_independence():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert a == b

def test_aid_008_no_projection_fields():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, 'similarity')
    assert not hasattr(art, 'projection')
    assert not hasattr(art, 'pair_relation')

def test_aid_009_no_pair_conclusion():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, 'is_match')
    assert not hasattr(art, 'is_same_entity')
    assert not hasattr(art, 'is_same_registration')

def test_aid_010_no_legal_entity_claim():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, 'legal_entity')
    assert not hasattr(art, 'same_legal_entity')

def test_aid_011_no_transaction_claim():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert not hasattr(art, 'transaction_id')
    assert not hasattr(art, 'same_transaction')

def test_aid_012_hash_determinism():
    a = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    b = DeterministicTaxParser.parse("07ABCDE1234F1Z2")
    assert hash(a) == hash(b)

def test_aid_013_source_field_preserved():
    art = DeterministicTaxParser.parse("07ABCDE1234F1Z2", field_id="vendor_name")
    assert art.observation.source_field_identity == "vendor_name"
    art2 = DeterministicTaxParser.parse("07ABCDE1234F1Z2", field_id="tax_identity")
    assert art2.observation.source_field_identity == "tax_identity"
    assert art != art2
