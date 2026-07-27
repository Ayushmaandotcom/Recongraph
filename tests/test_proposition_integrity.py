import pytest
from recongraph.contrib.kernel.scopes import ScopeKind, SubjectRef, PropositionSubject, Proposition
from recongraph.contrib.kernel.claims import CoreClaims, ClaimDescriptor, ClaimSymmetry


def test_pi001_same_claim_and_version_accepted():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject.create(
        claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")]
    )
    prop = Proposition(claim, subject)
    assert prop.claim == claim
    assert prop.subject == subject


def test_pi002_different_claim_id_rejected():
    claim1 = CoreClaims.SAME_LEGAL_ENTITY
    claim2 = CoreClaims.SAME_GST_REGISTRATION
    subject = PropositionSubject.create(
        claim1, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")]
    )
    with pytest.raises(ValueError, match="Proposition construction rejected: claim mismatch"):
        Proposition(claim2, subject)


def test_pi003_same_claim_id_different_semantic_version_rejected():
    claim1 = CoreClaims.SAME_LEGAL_ENTITY
    claim2 = ClaimDescriptor(
        claim_id=claim1.claim_id.value,
        semantic_version=2,
        symmetry=claim1.symmetry,
        allowed_scope_kinds=claim1.allowed_scope_kinds
    )
    subject = PropositionSubject.create(
        claim1, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")]
    )
    with pytest.raises(ValueError, match="Proposition construction rejected: claim semantic version mismatch"):
        Proposition(claim2, subject)


def test_pi004_symmetric_proposition_reversal_remains_equal():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    s1, s2 = SubjectRef("urn:1"), SubjectRef("urn:2")
    p1 = Proposition.create(claim, ScopeKind.RECORD_PAIR, left=[s1], right=[s2])
    p2 = Proposition.create(claim, ScopeKind.RECORD_PAIR, left=[s2], right=[s1])
    assert p1 == p2


def test_pi005_directional_proposition_reversal_remains_distinct():
    # We need a directional claim. Let's make a dummy one since core ones are symmetric.
    claim = ClaimDescriptor(
        claim_id="identity.parent_of",
        semantic_version=1,
        symmetry=ClaimSymmetry.DIRECTIONAL,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )
    s1, s2 = SubjectRef("urn:1"), SubjectRef("urn:2")
    p1 = Proposition.create(claim, ScopeKind.RECORD_PAIR, left=[s1], right=[s2])
    p2 = Proposition.create(claim, ScopeKind.RECORD_PAIR, left=[s2], right=[s1])
    assert p1 != p2


def test_pi006_unknown_plugin_claim_proposition_accepted():
    claim = ClaimDescriptor(
        claim_id="plugin.foo",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )
    p = Proposition.create(claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")])
    assert p.claim == claim


def test_pi007_unknown_plugin_claim_cross_version_mismatch_rejected():
    claim1 = ClaimDescriptor(
        claim_id="plugin.foo",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )
    claim2 = ClaimDescriptor(
        claim_id="plugin.foo",
        semantic_version=2,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )
    subject = PropositionSubject.create(
        claim1, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")]
    )
    with pytest.raises(ValueError):
        Proposition(claim2, subject)


def test_pi008_direct_proposition_constructor_cannot_bypass_compatibility_validation():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject(
        claim_id="identity.some_other_claim",
        claim_semantic_version=1,
        kind=ScopeKind.RECORD_PAIR,
        left=(SubjectRef("urn:1"),),
        right=(SubjectRef("urn:2"),)
    )
    with pytest.raises(ValueError, match="Proposition construction rejected: claim mismatch"):
        Proposition(claim, subject)
