import pytest

from recongraph.domain.lineage import (
    SourceSystemId,
    SourceNodeRef,
    SourceVersionRef,
    StructuredSourceLineage,
    ObservationProvenance
)
from recongraph.domain.observations import (
    ObservationSlot,
    ObservationState,
    ObservationIdentity,
    Observation,
    FieldPath
)
from recongraph.domain.scopes import SubjectRef


@pytest.fixture
def base_obs_identity():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    return Observation.create(slot, ObservationState.PRESENT, "ABC").identity


@pytest.fixture
def base_lineage():
    return StructuredSourceLineage(
        source_system=SourceSystemId("erp.sap"),
        source_node=SourceNodeRef("record", "DOC123"),
        source_version=SourceVersionRef("v1")
    )


def test_invalid_source_system_rejected():
    with pytest.raises(ValueError):
        SourceSystemId("sap")
    with pytest.raises(ValueError):
        SourceSystemId("erp")
    with pytest.raises(ValueError):
        SourceSystemId("erp-sap")


def test_ldup001_exact_source_reprocessing(base_lineage):
    l1 = base_lineage
    l2 = StructuredSourceLineage(
        source_system=SourceSystemId("erp.sap"),
        source_node=SourceNodeRef("record", "DOC123"),
        source_version=SourceVersionRef("v1")
    )
    assert l1 == l2


def test_ldup002_same_artifact_ref_different_system(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=SourceSystemId("document.invoice"),
        source_node=base_lineage.source_node,
        source_version=base_lineage.source_version
    )
    assert base_lineage != l2


def test_ldup003_same_system_different_artifact_ref(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=SourceNodeRef("record", "DOC999"),
        source_version=base_lineage.source_version
    )
    assert base_lineage != l2


def test_ldup004_same_artifact_different_version(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=SourceVersionRef("v2")
    )
    assert base_lineage != l2


def test_ldup005_same_observation_under_two_lineages(base_obs_identity, base_lineage):
    p1 = ObservationProvenance(base_obs_identity, base_lineage)
    
    l2 = StructuredSourceLineage(
        source_system=SourceSystemId("document.invoice"),
        source_node=SourceNodeRef("record", "INV1"),
        source_version=None
    )
    p2 = ObservationProvenance(base_obs_identity, l2)
    
    assert p1.observation_identity == p2.observation_identity
    assert p1.lineage != p2.lineage


def test_ldup006_different_observations_under_same_lineage(base_lineage, base_obs_identity):
    p1 = ObservationProvenance(base_obs_identity, base_lineage)
    
    slot2 = ObservationSlot(SubjectRef("urn:1"), FieldPath("amount"))
    obs2 = Observation.create(slot2, ObservationState.PRESENT, "100.0").identity
    p2 = ObservationProvenance(obs2, base_lineage)
    
    assert p1.observation_identity != p2.observation_identity
    assert p1.lineage == p2.lineage


def test_ldup007_source_version_unavailable(base_lineage):
    l1 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=None
    )
    assert l1 != base_lineage


def test_ldup008_literal_unknown_version_versus_none(base_lineage):
    l1 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=None
    )
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=base_lineage.source_node,
        source_version=SourceVersionRef("unknown")
    )
    assert l1 != l2


def test_ldup009_duplicate_source_file_under_new_artifact_ref(base_lineage):
    l2 = StructuredSourceLineage(
        source_system=base_lineage.source_system,
        source_node=SourceNodeRef("record", "DOC123_copy"),
        source_version=base_lineage.source_version
    )
    assert base_lineage != l2
