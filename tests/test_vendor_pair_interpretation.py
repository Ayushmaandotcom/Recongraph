import pytest
from recongraph.domain.vendor.observation import VendorNameObservation
from recongraph.domain.vendor.parser import DeterministicVendorParser
from recongraph.domain.vendor.artifact import build_vendor_observation_artifact
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.domain.vendor.interpretation import VendorPairInterpreter
from recongraph.domain.vendor.factors import (
    GSTRegistrationRelationState, PANRelationState, PANEvidenceDependence,
    LexicalRelationState, LegalFormRelationState, CorpusDistinctivenessState
)

@pytest.fixture
def default_context():
    profile = VendorCorpusProfile(
        corpus_size=1000,
        token_document_frequencies={"ENTERPRISES": 500, "TRADERS": 300, "RARECORP": 5},
        digest="sha256:corpus123"
    )
    return VendorIdentityContext(
        corpus_profile=profile,
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )

def parse_and_wrap(text):
    obs = DeterministicVendorParser.parse(text)
    art = build_vendor_observation_artifact(obs)
    return obs, art.identity

def test_semantic_symmetry(default_context):
    left, left_id = parse_and_wrap(None) # Missing
    right, right_id = parse_and_wrap("ABC PVT LTD")
    
    interp_ab = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    interp_ba = VendorPairInterpreter.interpret(right, right_id, left, left_id, default_context)
    
    # Check that LEFT_MISSING in A->B becomes RIGHT_MISSING in B->A
    assert interp_ab.gst_registration_relation.state == GSTRegistrationRelationState.BOTH_MISSING
    assert interp_ab.legal_form_relation.state == LegalFormRelationState.LEFT_MISSING
    assert interp_ba.legal_form_relation.state == LegalFormRelationState.RIGHT_MISSING
    
    # Check lexical inversion if applicable, here both missing because left is missing core
    assert interp_ab.lexical_relation.state == LexicalRelationState.BOTH_MISSING

def test_gstin_and_pan_dependence(default_context):
    gstin1 = "07ABCDE1234F1Z2"
    gstin2 = "09ABCDE1234F1ZY"
    
    left, left_id = parse_and_wrap(gstin1)
    right, right_id = parse_and_wrap(gstin2)
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    
    # GSTINs are valid and different
    assert interp.gst_registration_relation.state == GSTRegistrationRelationState.VALID_AND_DIFFERENT
    
    # PANs are the same! (ABCDE1234F)
    assert interp.pan_relation.state == PANRelationState.VALID_AND_EQUAL
    
    # Because GSTINs differ, they are INDEPENDENT PAN observations
    assert interp.pan_relation.dependence == PANEvidenceDependence.INDEPENDENT
    
    # Now test same GSTIN -> SAME_SOURCE_DERIVATION
    left2, left2_id = parse_and_wrap(gstin1)
    right2, right2_id = parse_and_wrap(gstin1)
    
    interp2 = VendorPairInterpreter.interpret(left2, left2_id, right2, right2_id, default_context)
    assert interp2.gst_registration_relation.state == GSTRegistrationRelationState.VALID_AND_EQUAL
    assert interp2.pan_relation.state == PANRelationState.VALID_AND_EQUAL
    assert interp2.pan_relation.dependence == PANEvidenceDependence.SAME_SOURCE_DERIVATION

def test_missingness_non_contradiction(default_context):
    # A missing legal form vs present legal form should NOT create INCOMPATIBLE
    left, left_id = parse_and_wrap("ABC ENTERPRISES") # no legal form
    right, right_id = parse_and_wrap("ABC ENTERPRISES PVT LTD") # PRIVATE_LIMITED
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    
    assert interp.legal_form_relation.state == LegalFormRelationState.LEFT_MISSING
    assert interp.lexical_relation.state == LexicalRelationState.EXACT_NORMALIZED_CORE_EQUALITY

def test_short_string_fuzzy_rejection(default_context):
    left, left_id = parse_and_wrap("ABC")
    right, right_id = parse_and_wrap("ABD")
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    
    # Even though ratio is high (0.66), minimum length is 6, so it must return DIFFERENT, not FUZZY
    assert interp.lexical_relation.state == LexicalRelationState.DIFFERENT
    
def test_corpus_distinctiveness(default_context):
    # RARECORP has DF 5/1000 = 0.005 <= 0.01 threshold -> DISTINCTIVE
    left, left_id = parse_and_wrap("RARECORP PVT LTD")
    right, right_id = parse_and_wrap("RARECORP")
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    assert interp.corpus_distinctiveness.state == CorpusDistinctivenessState.DISTINCTIVE_SUPPORT
    
    # TRADERS has DF 300/1000 = 0.3 > 0.01 threshold -> ATTENUATED
    left2, left2_id = parse_and_wrap("XYZ TRADERS")
    right2, right2_id = parse_and_wrap("ABC TRADERS")

    interp2 = VendorPairInterpreter.interpret(left2, left2_id, right2, right2_id, default_context)
    # They share "TRADERS"
    assert interp2.corpus_distinctiveness.state == CorpusDistinctivenessState.ATTENUATED_SUPPORT
    assert interp2.lexical_relation.state == LexicalRelationState.DIFFERENT

def test_context_determinism(default_context):
    # Changing context identity properties changes context identity
    c1 = VendorIdentityContext(
        corpus_profile=None,
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )
    
    c2 = VendorIdentityContext(
        corpus_profile=None,
        interpreter_policy_version="1.1.0", # changed
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )
    
    assert c1.identity.digest != c2.identity.digest
