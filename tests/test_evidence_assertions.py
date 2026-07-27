import pytest
from recongraph.contrib.kernel.assertions import (
    EvidenceAssertion, EvidenceAssertionIdentity, EvidenceAncestryRef,
    AssertionPolarity, EvidenceInterpretationResult, EvidenceInterpretationState
)
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.scopes import Proposition, PropositionSubject, ScopeKind, SubjectRef
from recongraph.contrib.kernel.claims import CoreClaims


def _make_ancestry(domain="recongraph.observation_occurrence"):
    ref = KernelIdentityRef(
        domain=IdentityDomainId(domain),
        schema=IdentitySchemaId("test.v1"),
        digest=IdentityDigest("sha256:" + "a" * 64)
    )
    return EvidenceAncestryRef(identity=ref)


def _make_proposition():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject.create(
        claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")]
    )
    return Proposition(claim, subject)


def _make_assertion(magnitude=1.0, polarity=AssertionPolarity.SUPPORT, domain="recongraph.observation_occurrence"):
    return EvidenceAssertion(
        proposition=_make_proposition(),
        polarity=polarity,
        magnitude=magnitude,
        authority=AuthorityDescriptor(AuthorityBasisId("test")),
        ancestry=_make_ancestry(domain=domain)
    )


def test_ea015_magnitude_zero_rejected():
    with pytest.raises(ValueError, match="Magnitude must be in range"):
        _make_assertion(magnitude=0.0)


def test_ea051_direct_proposition_construction_with_mismatched_claim():
    pass # Tested in test_proposition_integrity


def test_ea052_same_claimid_different_semantic_version_proposition_mismatch():
    pass # Tested in test_proposition_integrity


def test_ea053_malformed_kernel_identity_ref_digest():
    pass # Tested in test_kernel_identity_refs


def test_ea054_valid_digest_but_invalid_identity_domain():
    # Attempting to use observation_identity as ancestry
    with pytest.raises(ValueError):
        _make_ancestry(domain="recongraph.observation_identity")


def test_ea055_observation_identity_used_as_assertion_ancestry():
    with pytest.raises(ValueError):
        _make_ancestry(domain="recongraph.observation_identity")


def test_ea056_derivation_identity_used_as_assertion_ancestry():
    with pytest.raises(ValueError):
        _make_ancestry(domain="recongraph.derivation_identity")


def test_ea057_derived_artifact_identity_used_as_assertion_ancestry():
    with pytest.raises(ValueError):
        _make_ancestry(domain="recongraph.derived_artifact_identity")


def test_ea063_exact_duplicate_assertion_inside_interpretation_rejected():
    a1 = _make_assertion()
    with pytest.raises(ValueError, match="Duplicate assertion identities"):
        EvidenceInterpretationResult(
            state=EvidenceInterpretationState.INTERPRETED,
            assertions=(a1, a1)
        )


def test_ea064_reversed_assertion_emission_order_canonicalized():
    a1 = _make_assertion(magnitude=1.0)
    a2 = _make_assertion(magnitude=0.8)
    
    r1 = EvidenceInterpretationResult(
        state=EvidenceInterpretationState.INTERPRETED,
        assertions=(a1, a2)
    )
    r2 = EvidenceInterpretationResult(
        state=EvidenceInterpretationState.INTERPRETED,
        assertions=(a2, a1)
    )
    assert r1.assertions == r2.assertions


def test_ea071_interpreted_empty_is_canonical_no_assertion_representation():
    r = EvidenceInterpretationResult(
        state=EvidenceInterpretationState.INTERPRETED,
        assertions=()
    )
    assert r.assertions == ()


def test_ea072_provider_cannot_encode_no_evidence_as_support_zero():
    with pytest.raises(ValueError):
        _make_assertion(magnitude=0.0, polarity=AssertionPolarity.SUPPORT)


def test_ea073_provider_cannot_encode_no_conflict_as_conflict_zero():
    with pytest.raises(ValueError):
        _make_assertion(magnitude=0.0, polarity=AssertionPolarity.CONFLICT)


def test_ac006_interpreted_empty_legal():
    EvidenceInterpretationResult(state=EvidenceInterpretationState.INTERPRETED, assertions=())


def test_ac007_missing_input_empty_legal():
    EvidenceInterpretationResult(state=EvidenceInterpretationState.MISSING_INPUT, assertions=())


def test_ac008_missing_input_non_empty_rejected():
    with pytest.raises(ValueError, match="must have empty assertions"):
        EvidenceInterpretationResult(
            state=EvidenceInterpretationState.MISSING_INPUT,
            assertions=(_make_assertion(),)
        )


def test_ac009_uninterpretable_non_empty_rejected():
    with pytest.raises(ValueError, match="must have empty assertions"):
        EvidenceInterpretationResult(
            state=EvidenceInterpretationState.UNINTERPRETABLE_INPUT,
            assertions=(_make_assertion(),)
        )


def test_ac010_not_applicable_non_empty_rejected():
    with pytest.raises(ValueError, match="must have empty assertions"):
        EvidenceInterpretationResult(
            state=EvidenceInterpretationState.NOT_APPLICABLE,
            assertions=(_make_assertion(),)
        )
