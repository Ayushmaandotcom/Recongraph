import pytest
import json
from dataclasses import dataclass

from recongraph.domain.derivations import (
    ProviderId,
    ProviderSemanticVersion,
    DerivationMethodId,
    DerivationMethodDescriptor,
    DerivationInputBinding,
    DerivationIdentity,
    DerivationExecution
)
from recongraph.domain.observations import ObservationSlot, ObservationState, Observation, FieldPath
from recongraph.domain.scopes import SubjectRef


def test_provider_id_validation():
    pid = ProviderId("recongraph.vendor")
    assert pid.value == "recongraph.vendor"
    
    with pytest.raises(ValueError):
        ProviderId("vendor") # missing namespace
        
    with pytest.raises(ValueError):
        ProviderId("recongraph..vendor")


def test_provider_semantic_version():
    ver = ProviderSemanticVersion(major=1, minor=2, patch=3)
    assert ver.major == 1
    assert ver.minor == 2
    assert ver.patch == 3


def test_derivation_method_id_not_globally_namespaced():
    # As decided, MethodId is provider-relative.
    # It must not duplicate the namespace. 
    mid = DerivationMethodId("normalize_name")
    assert mid.value == "normalize_name"


def test_di001_same_inputs_method_version_same_identity():
    # Setup
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    
    desc = DerivationMethodDescriptor(
        provider_id=ProviderId("vendor.identity"),
        method_id=DerivationMethodId("extract"),
        commutative_roles=frozenset()
    )
    
    bindings = frozenset([DerivationInputBinding("source", obs)])
    
    id1 = DerivationIdentity.compute(
        provider_semantic_version=ProviderSemanticVersion(1, 0, 0),
        method=desc,
        inputs=bindings
    )
    
    id2 = DerivationIdentity.compute(
        provider_semantic_version=ProviderSemanticVersion(1, 0, 0),
        method=desc,
        inputs=bindings
    )
    
    assert id1 == id2
    assert id1.digest.startswith("sha256:")


def test_di002_commutative_roles_canonicalize():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs1 = Observation.create(slot, ObservationState.PRESENT, "A").identity
    obs2 = Observation.create(slot, ObservationState.PRESENT, "B").identity
    
    desc = DerivationMethodDescriptor(
        provider_id=ProviderId("recongraph.financial"),
        method_id=DerivationMethodId("aggregate"),
        commutative_roles=frozenset(["amount"])
    )
    
    # Order 1
    b1 = frozenset([
        DerivationInputBinding("amount", obs1),
        DerivationInputBinding("amount", obs2)
    ])
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b1)
    
    # Order 2
    b2 = frozenset([
        DerivationInputBinding("amount", obs2),
        DerivationInputBinding("amount", obs1)
    ])
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b2)
    
    assert id1 == id2


def test_di003_directional_roles_distinct():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs1 = Observation.create(slot, ObservationState.PRESENT, "A").identity
    obs2 = Observation.create(slot, ObservationState.PRESENT, "B").identity
    
    desc = DerivationMethodDescriptor(
        provider_id=ProviderId("recongraph.financial"),
        method_id=DerivationMethodId("subtract"),
        commutative_roles=frozenset()
    )
    
    b1 = frozenset([
        DerivationInputBinding("left", obs1),
        DerivationInputBinding("right", obs2)
    ])
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b1)
    
    b2 = frozenset([
        DerivationInputBinding("left", obs2),
        DerivationInputBinding("right", obs1)
    ])
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b2)
    
    assert id1 != id2


def test_di005_semantic_version_bump_changes_identity():
    desc = DerivationMethodDescriptor(
        provider_id=ProviderId("vendor.identity"),
        method_id=DerivationMethodId("extract"),
        commutative_roles=frozenset()
    )
    b = frozenset([])
    
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b)
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 1, 0), desc, b)
    assert id1 != id2
