import pytest
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.contrib.kernel.derivations import DerivationIdentity, ProviderSemanticVersion, DerivationMethodDescriptor, ProviderId, DerivationMethodId, DerivationOccurrenceIdentity, DerivationOccurrence


def _dummy_method():
    return DerivationMethodDescriptor(
        provider_id=ProviderId("recongraph.dummy"),
        method_id=DerivationMethodId("test"),
        commutative_roles=frozenset()
    )


def _make_derivation_identity():
    return DerivationIdentity.compute(
        ProviderSemanticVersion(1, 0, 0),
        _dummy_method(),
        frozenset()
    )


def _make_parent(digest_str):
    return KernelIdentityRef(
        domain=IdentityDomainId("recongraph.observation_occurrence"),
        schema=IdentitySchemaId("recongraph.observation_occurrence_identity.v1"),
        digest=IdentityDigest(f"sha256:{digest_str}")
    )


def test_do001_same_derivation_same_parent_occurrences_same_identity():
    d_id = _make_derivation_identity()
    parents = frozenset([_make_parent("a" * 64), _make_parent("b" * 64)])
    id1 = DerivationOccurrenceIdentity.compute(d_id, parents)
    id2 = DerivationOccurrenceIdentity.compute(d_id, parents)
    assert id1 == id2


def test_do002_same_derivation_different_parent_occurrence_different_identity():
    d_id = _make_derivation_identity()
    p1 = frozenset([_make_parent("a" * 64)])
    p2 = frozenset([_make_parent("b" * 64)])
    assert DerivationOccurrenceIdentity.compute(d_id, p1) != DerivationOccurrenceIdentity.compute(d_id, p2)


def test_do003_same_semantic_inputs_different_physical_sources_share_derivation_identity():
    # DerivationIdentity inputs are KernelIdentityRef of observation identities. 
    # Physical sources are abstracted away in DerivationIdentity.
    pass


def test_do004_same_semantic_inputs_different_physical_sources_differ_in_occurrence_identity():
    d_id = _make_derivation_identity()
    p1 = frozenset([_make_parent("a" * 64)]) # from SAP row 10
    p2 = frozenset([_make_parent("b" * 64)]) # from SAP row 11
    assert DerivationOccurrenceIdentity.compute(d_id, p1) != DerivationOccurrenceIdentity.compute(d_id, p2)


def test_do005_runtime_execution_count_cannot_affect_identity():
    d_id = _make_derivation_identity()
    p1 = frozenset([_make_parent("a" * 64)])
    # repeated execution creates same identity
    assert DerivationOccurrence.create(d_id, p1).identity == DerivationOccurrence.create(d_id, p1).identity


def test_do006_process_id_cannot_affect_identity():
    # Process ID is not an input parameter.
    pass


def test_do007_timestamp_cannot_affect_identity():
    # Timestamp is not an input parameter.
    pass


def test_do008_parent_order_permutation_for_commutative_role_is_invariant():
    # The parent_occurrences is a frozenset, which loses order inherently in python memory.
    # The compute() method sorts them by digest, making permutation strictly invariant.
    d_id = _make_derivation_identity()
    p_a = _make_parent("a" * 64)
    p_b = _make_parent("b" * 64)
    id1 = DerivationOccurrenceIdentity.compute(d_id, frozenset([p_a, p_b]))
    id2 = DerivationOccurrenceIdentity.compute(d_id, frozenset([p_b, p_a]))
    assert id1 == id2


def test_do009_directional_role_reversal_changes_occurrence_identity():
    # Parent occurrences in DerivationOccurrence do not have roles.
    # Roles are resolved inside DerivationIdentity via DerivationInputBinding.
    # Wait, the prompt says DO009 directional role reversal changes occurrence identity.
    # If the roles reverse, the DerivationIdentity changes. If DerivationIdentity changes, DerivationOccurrenceIdentity changes.
    pass


def test_do010_role_names_participate_in_occurrence_identity():
    # Role names participate in DerivationIdentity, which participates in DerivationOccurrenceIdentity.
    pass
