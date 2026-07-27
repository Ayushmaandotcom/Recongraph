import pytest
from recongraph.contrib.kernel.identity import IdentityDomainId, IdentityDigest
from recongraph.contrib.kernel.dependencies import SemanticDependencyRef, SemanticDependencyKind, DependencyStability
from recongraph.contrib.kernel.derivations import DerivationIdentity, ProviderSemanticVersion, DerivationMethodDescriptor, ProviderId, DerivationMethodId


def _dummy_method():
    return DerivationMethodDescriptor(
        provider_id=ProviderId("recongraph.dummy"),
        method_id=DerivationMethodId("test"),
        commutative_roles=frozenset()
    )


def test_sd001_content_addressed_config_dependency():
    dep = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "c" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    assert dep.stability == DependencyStability.CONTENT_ADDRESSED


def test_sd002_immutable_model_version_dependency():
    dep = SemanticDependencyRef(
        kind=SemanticDependencyKind.MODEL_ARTIFACT,
        namespace=IdentityDomainId("recongraph.model.vendor_encoder"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.IMMUTABLE_VERSION,
        semantic_version="1.2.3"
    )
    assert dep.stability == DependencyStability.IMMUTABLE_VERSION


def test_sd003_mutable_registry_alias():
    dep = SemanticDependencyRef(
        kind=SemanticDependencyKind.REGISTRY_SNAPSHOT,
        namespace=IdentityDomainId("recongraph.registry.gst"),
        identity=IdentityDigest("sha256:" + "0" * 64), # identity hash of the string "latest" etc. But we must use IdentityDigest format
        stability=DependencyStability.MUTABLE_REFERENCE
    )
    assert dep.stability == DependencyStability.MUTABLE_REFERENCE


def test_sd004_same_namespace_different_content_digest_changes_identity():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "b" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1,))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d2,))
    assert id1 != id2


def test_sd005_same_identity_different_kind_changes_identity():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.RULESET,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1,))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d2,))
    assert id1 != id2


def test_sd006_dependency_order_permutation_invariant():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.MODEL_ARTIFACT,
        namespace=IdentityDomainId("recongraph.model"),
        identity=IdentityDigest("sha256:" + "b" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1, d2))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d2, d1))
    assert id1 == id2


def test_sd007_duplicate_identical_dependency_rejected():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    with pytest.raises(ValueError, match="Duplicate identical semantic dependencies are rejected"):
        DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1, d1))


def test_sd008_same_dependency_identity_in_two_distinct_namespaces_preserved():
    # If the digest is the same but namespaces differ, they are distinct dependencies
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config.1"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config.2"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    # this shouldn't raise duplicate error because they are distinct objects
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1, d2))
    assert id1


def test_sd009_mutable_dependency_remains_representable():
    d = SemanticDependencyRef(
        kind=SemanticDependencyKind.REGISTRY_SNAPSHOT,
        namespace=IdentityDomainId("recongraph.registry"),
        identity=IdentityDigest("sha256:" + "0" * 64),
        stability=DependencyStability.MUTABLE_REFERENCE
    )
    assert DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d,))


def test_sd010_mutable_dependency_does_not_masquerade_as_reproducible_snapshot():
    # It must be explicit that it's mutable
    d = SemanticDependencyRef(
        kind=SemanticDependencyKind.REGISTRY_SNAPSHOT,
        namespace=IdentityDomainId("recongraph.registry"),
        identity=IdentityDigest("sha256:" + "0" * 64),
        stability=DependencyStability.MUTABLE_REFERENCE
    )
    assert d.stability == DependencyStability.MUTABLE_REFERENCE


def test_sd011_dependency_kind_change_changes_identity():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.CONFIGURATION,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.RULESET,
        namespace=IdentityDomainId("recongraph.config"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.CONTENT_ADDRESSED
    )
    assert d1 != d2
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1,))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d2,))
    assert id1 != id2


def test_sd012_semantic_version_change_changes_identity():
    d1 = SemanticDependencyRef(
        kind=SemanticDependencyKind.MODEL_ARTIFACT,
        namespace=IdentityDomainId("recongraph.model"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.IMMUTABLE_VERSION,
        semantic_version="1.0.0"
    )
    d2 = SemanticDependencyRef(
        kind=SemanticDependencyKind.MODEL_ARTIFACT,
        namespace=IdentityDomainId("recongraph.model"),
        identity=IdentityDigest("sha256:" + "a" * 64),
        stability=DependencyStability.IMMUTABLE_VERSION,
        semantic_version="1.0.1"
    )
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d1,))
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), _dummy_method(), frozenset(), (d2,))
    assert id1 != id2
