import pytest

from recongraph.domain.lineage import (
    SourceSystemId,
    SourceNodeRef,
    StructuredSourceLineage,
    ObservationProvenance
)
from recongraph.domain.derivations import (
    ProviderId,
    ProviderSemanticVersion,
    DerivationMethodId,
    DerivationInputMode,
    DerivationMethodDescriptor,
    DerivationInputBinding,
    DerivationInputSet,
    DerivationMetadata
)
from recongraph.domain.observations import (
    ObservationSlot,
    ObservationState,
    Observation,
    FieldPath
)
from recongraph.domain.scopes import SubjectRef


@pytest.fixture
def obs1():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    return Observation.create(slot, ObservationState.PRESENT, "ABC").identity


@pytest.fixture
def obs2():
    slot = ObservationSlot(SubjectRef("urn:2"), FieldPath("vendor"))
    return Observation.create(slot, ObservationState.PRESENT, "XYZ").identity


@pytest.fixture
def base_method():
    return DerivationMethodDescriptor(
        provider_id=ProviderId("vendor.identity"),
        method_id=DerivationMethodId("compare_core"),
        input_mode=DerivationInputMode.UNORDERED
    )


@pytest.fixture
def base_inputs(obs1, obs2):
    b1 = DerivationInputBinding("left", obs1)
    b2 = DerivationInputBinding("right", obs2)
    return DerivationInputSet(frozenset([b1, b2]))


@pytest.fixture
def base_derivation(base_method, base_inputs):
    return DerivationMetadata.create(
        provider_semantic_version=ProviderSemanticVersion(1),
        method=base_method,
        inputs=base_inputs
    )


def test_ddup001_exact_reconstruction(base_derivation, base_method, base_inputs):
    d2 = DerivationMetadata.create(
        provider_semantic_version=ProviderSemanticVersion(1),
        method=base_method,
        inputs=base_inputs
    )
    assert base_derivation.identity == d2.identity


def test_ddup002_provider_changes(base_derivation, base_inputs):
    m2 = DerivationMethodDescriptor(
        provider_id=ProviderId("plugin.custom"),
        method_id=DerivationMethodId("compare_core"),
        input_mode=DerivationInputMode.UNORDERED
    )
    d2 = DerivationMetadata.create(ProviderSemanticVersion(1), m2, base_inputs)
    assert base_derivation.identity != d2.identity


def test_ddup003_semantic_version_changes(base_derivation, base_method, base_inputs):
    d2 = DerivationMetadata.create(
        provider_semantic_version=ProviderSemanticVersion(2),
        method=base_method,
        inputs=base_inputs
    )
    assert base_derivation.identity != d2.identity


def test_ddup007_unordered_input_reversal(base_derivation, base_method, obs1, obs2):
    # Reverse roles logically, but keep them structurally identical semantic inputs 
    # Actually, in role-bound architecture, changing the role changes the binding entirely.
    # What the test means is: if the set is constructed in reverse order of iteration.
    b1 = DerivationInputBinding("left", obs1)
    b2 = DerivationInputBinding("right", obs2)
    inputs_reversed = DerivationInputSet(frozenset([b2, b1]))
    d2 = DerivationMetadata.create(ProviderSemanticVersion(1), base_method, inputs_reversed)
    assert base_derivation.identity == d2.identity


def test_ddup016_role_bindings_swapped(base_derivation, base_method, obs1, obs2):
    b1 = DerivationInputBinding("right", obs1)
    b2 = DerivationInputBinding("left", obs2)
    inputs = DerivationInputSet(frozenset([b1, b2]))
    d2 = DerivationMetadata.create(ProviderSemanticVersion(1), base_method, inputs)
    assert base_derivation.identity != d2.identity


def test_ddup018_empty_input_derivation_fails(base_method):
    with pytest.raises(ValueError):
        DerivationInputSet(frozenset([]))


def test_shared_ancestry_query(base_method, obs1, obs2):
    d1 = DerivationMetadata.create(
        ProviderSemanticVersion(1),
        base_method,
        DerivationInputSet(frozenset([
            DerivationInputBinding("only", obs1)
        ]))
    )
    
    d2 = DerivationMetadata.create(
        ProviderSemanticVersion(1),
        base_method,
        DerivationInputSet(frozenset([
            DerivationInputBinding("left", obs1),
            DerivationInputBinding("right", obs2)
        ]))
    )
    
    d3 = DerivationMetadata.create(
        ProviderSemanticVersion(1),
        base_method,
        DerivationInputSet(frozenset([
            DerivationInputBinding("only", obs2)
        ]))
    )
    
    assert len(d1.shared_observation_identities(d2)) == 1
    assert list(d1.shared_observation_identities(d2))[0] == obs1
    
    assert len(d1.shared_observation_identities(d3)) == 0


def test_derivation_serialization_is_deterministic(base_derivation):
    import json
    s1 = json.dumps(base_derivation.to_dict(), sort_keys=True)
    
    d2 = DerivationMetadata.create(
        ProviderSemanticVersion(1),
        base_derivation.method,
        base_derivation.inputs
    )
    s2 = json.dumps(d2.to_dict(), sort_keys=True)
    
    assert s1 == s2
