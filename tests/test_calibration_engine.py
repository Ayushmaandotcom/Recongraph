from recongraph.graph.calibration import CalibrationCurve, CalibrationPolicy, CalibrationEngine
from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
from recongraph.contrib.kernel.claims import ClaimDescriptor, ClaimId, ClaimSemanticVersion, ClaimSymmetry
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.graph.dempster_shafer import MassFunction

def make_test_assertion(claim_id: str, basis: str) -> EvidenceAssertion:
    dummy_claim = ClaimDescriptor(
        claim_id=ClaimId(claim_id),
        semantic_version=ClaimSemanticVersion(1),
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds=frozenset([ScopeKind.RECORD_PAIR])
    )
    dummy_subject = SubjectRef("urn:dummy")
    
    mock_ancestry = EvidenceAncestryRef(
        identity=KernelIdentityRef(
            domain=IdentityDomainId("recongraph.observation_occurrence"),
            schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
            digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
        )
    )
    
    return EvidenceAssertion(
        authority=AuthorityDescriptor(basis=AuthorityBasisId(basis)),
        polarity=AssertionPolarity.SUPPORT,
        magnitude=1.0,
        proposition=Proposition.create(
            claim=dummy_claim,
            kind=ScopeKind.RECORD_PAIR,
            left=[dummy_subject],
            right=[dummy_subject]
        ),
        ancestry=mock_ancestry
    )

def test_calibration_curve_interpolation():
    curve = CalibrationCurve(((0.0, 0.0), (0.5, 0.2), (1.0, 0.99)))
    
    assert curve.interpolate(0.0) == 0.0
    assert curve.interpolate(0.25) == 0.1
    assert curve.interpolate(0.5) == 0.2
    assert curve.interpolate(0.75) == 0.595
    assert curve.interpolate(1.0) == 0.99
    
    # Out of bounds
    assert curve.interpolate(-0.5) == 0.0
    assert curve.interpolate(1.5) == 0.99

def test_calibration_engine_with_policy():
    policy = CalibrationPolicy(
        curves={
            ("tax.same_legal_entity", "TAX"): CalibrationCurve(((0.0, 0.0), (1.0, 0.95))),
        },
        default_curve=CalibrationCurve(((0.0, 0.0), (1.0, 0.5)))
    )
    engine = CalibrationEngine(policy)
    
    # 1. Test known curve
    known_assertion = make_test_assertion("tax.same_legal_entity", "TAX")
    import pytest
    mass = engine.calibrate(known_assertion)
    assert mass.match == 0.95
    assert mass.uncertainty == pytest.approx(0.05)
    
    # 2. Test default curve fallback
    unknown_assertion = make_test_assertion("financial.conservation", "FINANCIAL")
    mass2 = engine.calibrate(unknown_assertion)
    assert mass2.match == 0.5
    assert mass2.uncertainty == 0.5
