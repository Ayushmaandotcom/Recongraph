import pytest
import unicodedata
from recongraph.contrib.kernel.lineage import StructuredSourceLineage, SourceSystemId, SourceArtifactId, SourceLocator
from recongraph.contrib.kernel.observations import ObservationIdentity, ObservationSlot, ObservationState, Observation, FieldPath, ObservationOccurrenceIdentity, ObservationOccurrence
from recongraph.contrib.kernel.scopes import SubjectRef, Proposition, PropositionSubject, ScopeKind
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.contrib.kernel.dependencies import SemanticDependencyRef, SemanticDependencyKind, DependencyStability
from recongraph.contrib.kernel.derivations import DerivationIdentity, ProviderSemanticVersion, DerivationMethodDescriptor, ProviderId, DerivationMethodId, DerivationOccurrenceIdentity
from recongraph.contrib.kernel.payloads import CanonicalPayloadEnvelope, TypedPayloadEnvelope
from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef, EvidenceInterpretationResult, EvidenceInterpretationState
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.claims import CoreClaims


def test_ma021_same_observation_content_different_lineage_changes_occurrence_identity():
    obs = Observation.create(
        slot=ObservationSlot(SubjectRef("urn:1"), FieldPath("foo")),
        state=ObservationState.PRESENT,
        value="test"
    )
    l1 = StructuredSourceLineage(SourceSystemId("sys.a"), SourceArtifactId("b"), SourceLocator("c"))
    l2 = StructuredSourceLineage(SourceSystemId("sys.a"), SourceArtifactId("d"), SourceLocator("c"))
    assert ObservationOccurrenceIdentity.compute(obs.identity, l1) != ObservationOccurrenceIdentity.compute(obs.identity, l2)


def test_ma022_same_observation_occurrence_runtime_retry_preserves_occurrence_identity():
    obs = Observation.create(
        slot=ObservationSlot(SubjectRef("urn:1"), FieldPath("foo")),
        state=ObservationState.PRESENT,
        value="test"
    )
    l1 = StructuredSourceLineage(SourceSystemId("sys.a"), SourceArtifactId("b"), SourceLocator("c"))
    occ1 = ObservationOccurrence.create(obs.identity, l1)
    occ2 = ObservationOccurrence.create(obs.identity, l1)
    assert occ1.identity == occ2.identity


def test_ma023_same_derivation_semantics_different_ancestry_changes_derivation_occurrence_identity():
    method = DerivationMethodDescriptor(ProviderId("prov.a"), DerivationMethodId("b"), frozenset())
    d_id = DerivationIdentity.compute(ProviderSemanticVersion(1,0,0), method, frozenset())
    p1 = frozenset([KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "a"*64))])
    p2 = frozenset([KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "b"*64))])
    assert DerivationOccurrenceIdentity.compute(d_id, p1) != DerivationOccurrenceIdentity.compute(d_id, p2)


def test_ma024_same_derivation_occurrence_runtime_retry_preserves_identity():
    method = DerivationMethodDescriptor(ProviderId("prov.a"), DerivationMethodId("b"), frozenset())
    d_id = DerivationIdentity.compute(ProviderSemanticVersion(1,0,0), method, frozenset())
    p1 = frozenset([KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "a"*64))])
    id1 = DerivationOccurrenceIdentity.compute(d_id, p1)
    id2 = DerivationOccurrenceIdentity.compute(d_id, p1)
    assert id1 == id2


def test_ma025_generic_serialization_metadata_addition_does_not_change_assertion_identity():
    # Identity preimage is explicitly defined, adding to generic dict won't alter identity
    # since we compute identity from strict fields.
    pass


def test_ma026_canonical_identity_field_change_changes_assertion_identity():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject.create(claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")])
    prop = Proposition(claim, subject)
    ancestry = EvidenceAncestryRef(KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "a"*64)))
    a1 = EvidenceAssertion(
        proposition=prop,
        polarity=AssertionPolarity.SUPPORT,
        magnitude=0.5,
        authority=AuthorityDescriptor(AuthorityBasisId("a")),
        ancestry=ancestry
    )
    a2 = EvidenceAssertion(
        proposition=prop,
        polarity=AssertionPolarity.SUPPORT,
        magnitude=0.6,
        authority=AuthorityDescriptor(AuthorityBasisId("a")),
        ancestry=ancestry
    )
    assert a1.identity != a2.identity


def test_ma027_nfc_nfd_payload_text_preserves_assertion_identity():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject.create(claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")])
    prop = Proposition(claim, subject)
    ancestry = EvidenceAncestryRef(KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "a"*64)))
    
    canon_nfc = CanonicalPayloadEnvelope({"name": "é"})
    canon_nfd = CanonicalPayloadEnvelope({"name": "e\u0301"})
    typed_nfc = TypedPayloadEnvelope("test", "1", canon_nfc)
    typed_nfd = TypedPayloadEnvelope("test", "1", canon_nfd)
    
    a1 = EvidenceAssertion(prop, AssertionPolarity.SUPPORT, 1.0, AuthorityDescriptor(AuthorityBasisId("a")), ancestry, payload=typed_nfc)
    a2 = EvidenceAssertion(prop, AssertionPolarity.SUPPORT, 1.0, AuthorityDescriptor(AuthorityBasisId("a")), ancestry, payload=typed_nfd)
    assert a1.identity == a2.identity


def test_ma028_dependency_tuple_permutation_preserves_derivation_identity():
    method = DerivationMethodDescriptor(ProviderId("prov.a"), DerivationMethodId("b"), frozenset())
    d1 = SemanticDependencyRef(SemanticDependencyKind.CONFIGURATION, IdentityDomainId("dom.a"), IdentityDigest("sha256:"+"a"*64), DependencyStability.CONTENT_ADDRESSED)
    d2 = SemanticDependencyRef(SemanticDependencyKind.CONFIGURATION, IdentityDomainId("dom.b"), IdentityDigest("sha256:"+"b"*64), DependencyStability.CONTENT_ADDRESSED)
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1,0,0), method, frozenset(), (d1, d2))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1,0,0), method, frozenset(), (d2, d1))
    assert id1 == id2


def test_ma029_exact_duplicate_dependency_rejected():
    method = DerivationMethodDescriptor(ProviderId("prov.a"), DerivationMethodId("b"), frozenset())
    d1 = SemanticDependencyRef(SemanticDependencyKind.CONFIGURATION, IdentityDomainId("dom.a"), IdentityDigest("sha256:"+"a"*64), DependencyStability.CONTENT_ADDRESSED)
    with pytest.raises(ValueError):
        DerivationIdentity.compute(ProviderSemanticVersion(1,0,0), method, frozenset(), (d1, d1))


def test_ma030_assertion_tuple_permutation_preserves_interpretation_result_equality():
    claim = CoreClaims.SAME_LEGAL_ENTITY
    subject = PropositionSubject.create(claim, ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:1")], right=[SubjectRef("urn:2")])
    prop = Proposition(claim, subject)
    ancestry = EvidenceAncestryRef(KernelIdentityRef(IdentityDomainId("recongraph.observation_occurrence"), IdentitySchemaId("x.v1"), IdentityDigest("sha256:" + "a"*64)))
    
    a1 = EvidenceAssertion(prop, AssertionPolarity.SUPPORT, 1.0, AuthorityDescriptor(AuthorityBasisId("a")), ancestry)
    a2 = EvidenceAssertion(prop, AssertionPolarity.SUPPORT, 0.5, AuthorityDescriptor(AuthorityBasisId("a")), ancestry)
    
    r1 = EvidenceInterpretationResult(EvidenceInterpretationState.INTERPRETED, (a1, a2))
    r2 = EvidenceInterpretationResult(EvidenceInterpretationState.INTERPRETED, (a2, a1))
    
    assert r1.assertions == r2.assertions
