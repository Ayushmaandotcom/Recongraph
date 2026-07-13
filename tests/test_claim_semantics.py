import pytest
from recongraph.domain.claims import ClaimId, ClaimSemanticVersion, ClaimSymmetry, ClaimDescriptor
from recongraph.domain.scopes import ScopeKind

def test_claim_id_accepts_valid_namespaced_identifier():
    assert ClaimId("identity.same_legal_entity").value == "identity.same_legal_entity"

def test_claim_id_rejects_missing_namespace():
    with pytest.raises(ValueError):
        ClaimId("same_legal_entity")

def test_claim_id_rejects_uppercase():
    with pytest.raises(ValueError):
        ClaimId("Identity.SameLegalEntity")

def test_claim_id_rejects_hyphen():
    with pytest.raises(ValueError):
        ClaimId("identity.same-entity")

def test_claim_id_rejects_empty_segment():
    with pytest.raises(ValueError):
        ClaimId("identity..same")
    with pytest.raises(ValueError):
        ClaimId(".identity")

def test_claim_id_is_hashable():
    c1 = ClaimId("a.b")
    c2 = ClaimId("a.b")
    assert hash(c1) == hash(c2)

def test_claim_id_equality_is_value_based():
    assert ClaimId("a.b") == ClaimId("a.b")
    assert ClaimId("a.b") != ClaimId("a.c")

def test_claim_id_does_not_normalize_input():
    with pytest.raises(ValueError):
        ClaimId(" Identity.Same ")

def test_claim_id_round_trip_string():
    assert str(ClaimId("a.b")) == "a.b"

def test_claim_semantic_version_equality():
    assert ClaimSemanticVersion(1) == ClaimSemanticVersion(1)
    assert ClaimSemanticVersion(1) != ClaimSemanticVersion(2)

def test_claim_semantic_version_rejects_zero():
    with pytest.raises(ValueError):
        ClaimSemanticVersion(0)

def test_claim_semantic_version_rejects_negative():
    with pytest.raises(ValueError):
        ClaimSemanticVersion(-1)

def test_claim_semantic_version_rejects_bool():
    with pytest.raises(TypeError):
        ClaimSemanticVersion(True) # type: ignore

def test_claim_symmetry_values_are_stable():
    assert ClaimSymmetry.SYMMETRIC.value == "symmetric"
    assert ClaimSymmetry.DIRECTIONAL.value == "directional"

def test_claim_descriptor_requires_allowed_scope():
    with pytest.raises(ValueError):
        ClaimDescriptor(
            claim_id="a.b",
            semantic_version=1,
            symmetry=ClaimSymmetry.SYMMETRIC,
            allowed_scope_kinds=[]
        )

def test_claim_descriptor_freezes_allowed_scope_kinds():
    scopes = {ScopeKind.RECORD_PAIR}
    descriptor = ClaimDescriptor(
        claim_id="a.b",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds=scopes
    )
    assert isinstance(descriptor.allowed_scope_kinds, frozenset)

def test_same_claim_id_different_semantic_versions_are_distinct():
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    d2 = ClaimDescriptor("a.b", 2, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    assert d1 != d2
    assert hash(d1) != hash(d2)

def test_descriptor_does_not_depend_on_provider():
    # Attempting to set provider on the frozen dataclass fails
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    with pytest.raises(AttributeError):
        d1.provider_id = "test" # type: ignore

def test_descriptor_allows_declared_scope_kind():
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    assert d1.validates_scope_kind(ScopeKind.RECORD_PAIR) is True

def test_descriptor_rejects_undeclared_scope_kind():
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    assert d1.validates_scope_kind(ScopeKind.GROUP_PAIR) is False

def test_descriptor_is_hashable():
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    d2 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    assert hash(d1) == hash(d2)

def test_plugin_claim_can_be_described_without_core_enum_change():
    # Just construct a plugin ClaimDescriptor dynamically without modifying core lists.
    plugin_claim = ClaimDescriptor(
        claim_id="custom.bank_account_match",
        semantic_version=1,
        symmetry=ClaimSymmetry.SYMMETRIC,
        allowed_scope_kinds={ScopeKind.RECORD_PAIR}
    )
    assert plugin_claim.claim_id.value == "custom.bank_account_match"

def test_claim_descriptor_serialization_is_explicit():
    d1 = ClaimDescriptor("a.b", 1, ClaimSymmetry.SYMMETRIC, {ScopeKind.RECORD_PAIR})
    data = d1.to_dict()
    assert data["claim_id"] == "a.b"
    assert data["semantic_version"] == 1
    assert data["symmetry"] == "symmetric"
    assert data["allowed_scope_kinds"] == ["record_pair"]
