import pytest
from decimal import Decimal
from recongraph.domain.vendor.observation import VendorNameObservation, VendorObservationState
from recongraph.domain.vendor.parser import DeterministicVendorParser
from recongraph.domain.tax.parser import ParsedTaxIdentifierArtifact
from recongraph.domain.tax.observation import TaxIdentifierObservation, TaxObservationState as TaxState, TaxIdentifierCandidateType
from recongraph.domain.vendor.artifact import build_vendor_observation_artifact
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.domain.vendor.interpretation import VendorPairInterpreter
from recongraph.domain.vendor.policy import VendorProjectionPolicyV1

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

def test_missingness_safety(default_context):
    left, left_id = parse_and_wrap(None)
    right, right_id = parse_and_wrap(None)
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    proj = VendorProjectionPolicyV1.project(interp)
    
    # Missingness does NOT cap or contradict. It just returns None similarity.
    assert proj.similarity is None
    assert "lexical_relation" in proj.missing_factors
    assert "legal_form_relation" in proj.missing_factors
    assert not proj.contradiction_markers

def test_pan_conflict_capping_072_problem(default_context):
    left_obs = VendorNameObservation(
        raw_name="RARECORP",
        observation_state=VendorObservationState.PRESENT,
        canonical_core_text="RARECORP",
        organization_tokens=("RARECORP",),
        legal_form_category=None,
        recognized_designators=(),
        token_spans=(),
        normalization_events=(),
        tax_artifact=ParsedTaxIdentifierArtifact(
            observation=TaxIdentifierObservation("AAAAA1111A", "vendor_name", TaxIdentifierCandidateType.PAN, TaxState.PRESENT),
            gstin_candidate=None,
            gstin_valid=None,
            pan_candidate="AAAAA1111A",
            pan_valid=True,
            pan_derived_from_gstin=False,
            normalization_events=()
        )
    )
    left_id = build_vendor_observation_artifact(left_obs).identity
    
    right_obs = VendorNameObservation(
        raw_name="RARECORP",
        observation_state=VendorObservationState.PRESENT,
        canonical_core_text="RARECORP",
        organization_tokens=("RARECORP",),
        legal_form_category=None,
        recognized_designators=(),
        token_spans=(),
        normalization_events=(),
        tax_artifact=ParsedTaxIdentifierArtifact(
            observation=TaxIdentifierObservation("BBBBB2222B", "vendor_name", TaxIdentifierCandidateType.PAN, TaxState.PRESENT),
            gstin_candidate=None,
            gstin_valid=None,
            pan_candidate="BBBBB2222B",
            pan_valid=True,
            pan_derived_from_gstin=False,
            normalization_events=()
        )
    )
    right_id = build_vendor_observation_artifact(right_obs).identity
    
    interp = VendorPairInterpreter.interpret(left_obs, left_id, right_obs, right_id, default_context)
    proj = VendorProjectionPolicyV1.project(interp)
    
    assert "PAN_IDENTIFIER_CONFLICT" in proj.contradiction_markers
    assert proj.similarity == 0.40

def test_identical_exact_common_token_attenuation(default_context):
    left, left_id = parse_and_wrap("XYZ TRADERS")
    right, right_id = parse_and_wrap("ABC TRADERS")
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    proj = VendorProjectionPolicyV1.project(interp)
    
    assert "corpus_distinctiveness" in proj.considered_factors
    
    # If the only token is TRADERS, exact equality should not be capped by attenuation
    left2, left2_id = parse_and_wrap("TRADERS")
    right2, right2_id = parse_and_wrap("TRADERS")
    interp2 = VendorPairInterpreter.interpret(left2, left2_id, right2, right2_id, default_context)
    proj2 = VendorProjectionPolicyV1.project(interp2)
    
    assert proj2.similarity == 0.85

def test_same_source_derivation_logged(default_context):
    left, left_id = parse_and_wrap("07ABCDE1234F1Z2")
    right, right_id = parse_and_wrap("07ABCDE1234F1Z2")
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    proj = VendorProjectionPolicyV1.project(interp)
    
    assert "TAX_EVIDENCE_GROUP" in proj.dependence_groups

def test_projection_identity_determinism(default_context):
    left, left_id = parse_and_wrap("RARECORP")
    right, right_id = parse_and_wrap("RARECORP")
    
    interp = VendorPairInterpreter.interpret(left, left_id, right, right_id, default_context)
    proj1 = VendorProjectionPolicyV1.project(interp)
    proj2 = VendorProjectionPolicyV1.project(interp)
    
    assert proj1.identity_digest == proj2.identity_digest
