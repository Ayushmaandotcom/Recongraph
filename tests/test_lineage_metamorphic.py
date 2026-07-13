import pytest

from recongraph.domain.lineage import (
    SourceSystemId,
    SourceNodeRef,
    SourceVersionRef,
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
def base_lineage():
    return StructuredSourceLineage(
        source_system=SourceSystemId("erp.sap"),
        source_node=SourceNodeRef("record", "DOC123"),
        source_version=SourceVersionRef("v1")
    )


def test_kdm_001_source_system_distinction(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=SourceSystemId("document.invoice"),
        source_node=base_lineage.source_node,
        source_version=base_lineage.source_version
    )
    assert base_lineage != l2


def test_kdm_002_artifact_distinction(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=SourceNodeRef("record", "DOC999"),
        source_version=base_lineage.source_version
    )
    assert base_lineage != l2


def test_kdm_003_version_distinction(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=SourceVersionRef("v2")
    )
    assert base_lineage != l2


def test_kdm_004_version_absence_distinction(base_lineage):
    l_none = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=None
    )
    l_unknown = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=SourceVersionRef("unknown")
    )
    assert l_none != l_unknown


def test_kdm_005_observation_identity_independence():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    
    l1 = StructuredSourceLineage(SourceSystemId("erp.sap"), SourceNodeRef("record", "1"), None)
    l2 = StructuredSourceLineage(SourceSystemId("erp.oracle"), SourceNodeRef("record", "2"), None)
    
    p1 = ObservationProvenance(obs, l1)
    p2 = ObservationProvenance(obs, l2)
    
    # Lineage differs, but observation identity remains shared
    assert p1.lineage != p2.lineage
    assert p1.observation_identity == p2.observation_identity


def test_kdm_007_provider_distinction():
    obs = Observation.create(ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor")), ObservationState.PRESENT, "ABC").identity
    inputs = DerivationInputSet(frozenset([DerivationInputBinding("only", obs)]))
    
    m1 = DerivationMethodDescriptor(ProviderId("vendor.identity"), DerivationMethodId("extract"), DerivationInputMode.UNORDERED)
    m2 = DerivationMethodDescriptor(ProviderId("plugin.custom"), DerivationMethodId("extract"), DerivationInputMode.UNORDERED)
    
    d1 = DerivationMetadata.create(ProviderSemanticVersion(1), m1, inputs)
    d2 = DerivationMetadata.create(ProviderSemanticVersion(1), m2, inputs)
    
    assert d1.identity != d2.identity


def test_kdm_011_input_state_distinction():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs_present = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    obs_invalid = Observation.create(slot, ObservationState.INVALID, "ABC").identity
    
    assert obs_present != obs_invalid
    
    m1 = DerivationMethodDescriptor(ProviderId("vendor.identity"), DerivationMethodId("extract"), DerivationInputMode.UNORDERED)
    
    d1 = DerivationMetadata.create(ProviderSemanticVersion(1), m1, DerivationInputSet(frozenset([DerivationInputBinding("only", obs_present)])))
    d2 = DerivationMetadata.create(ProviderSemanticVersion(1), m1, DerivationInputSet(frozenset([DerivationInputBinding("only", obs_invalid)])))
    
    assert d1.identity != d2.identity


def test_kdm_021_input_role_distinction():
    obs1 = Observation.create(ObservationSlot(SubjectRef("urn:1"), FieldPath("amount")), ObservationState.PRESENT, "100").identity
    obs2 = Observation.create(ObservationSlot(SubjectRef("urn:2"), FieldPath("amount")), ObservationState.PRESENT, "50").identity
    
    m1 = DerivationMethodDescriptor(ProviderId("financial.conservation"), DerivationMethodId("subtract"), DerivationInputMode.ORDERED)
    
    d1 = DerivationMetadata.create(
        ProviderSemanticVersion(1), m1,
        DerivationInputSet(frozenset([
            DerivationInputBinding("minuend", obs1),
            DerivationInputBinding("subtrahend", obs2)
        ]))
    )
    
    d2 = DerivationMetadata.create(
        ProviderSemanticVersion(1), m1,
        DerivationInputSet(frozenset([
            DerivationInputBinding("subtrahend", obs1),
            DerivationInputBinding("minuend", obs2)
        ]))
    )
    
    assert d1.identity != d2.identity
