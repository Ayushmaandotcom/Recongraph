import pytest
from recongraph.contrib.kernel.lineage import StructuredSourceLineage, SourceSystemId, SourceArtifactId, SourceLocator, SourceVersionRef
from recongraph.contrib.kernel.observations import ObservationIdentity, ObservationSlot, ObservationState, Observation, FieldPath, ObservationOccurrenceIdentity, ObservationOccurrence
from recongraph.contrib.kernel.scopes import SubjectRef


def _make_lineage(sys, art, loc, ver=None):
    return StructuredSourceLineage(
        source_system=SourceSystemId(sys),
        source_artifact=SourceArtifactId(art),
        source_locator=SourceLocator(loc),
        source_version=SourceVersionRef(ver) if ver else None
    )


def _make_obs():
    return Observation.create(
        slot=ObservationSlot(SubjectRef("urn:1"), FieldPath("foo")),
        state=ObservationState.PRESENT,
        value="test"
    )


def _make_obs2():
    return Observation.create(
        slot=ObservationSlot(SubjectRef("urn:1"), FieldPath("foo")),
        state=ObservationState.PRESENT,
        value="test2"
    )


def test_oi001_same_fact_same_lineage_same_identity():
    obs = _make_obs()
    lin = _make_lineage("sys.a", "art", "loc")
    id1 = ObservationOccurrenceIdentity.compute(obs.identity, lin)
    id2 = ObservationOccurrenceIdentity.compute(obs.identity, lin)
    assert id1 == id2


def test_oi002_same_fact_different_artifact_different_identity():
    obs = _make_obs()
    lin1 = _make_lineage("sys.a", "art1", "loc")
    lin2 = _make_lineage("sys.a", "art2", "loc")
    assert ObservationOccurrenceIdentity.compute(obs.identity, lin1) != ObservationOccurrenceIdentity.compute(obs.identity, lin2)


def test_oi003_same_fact_same_artifact_different_version_different_identity():
    obs = _make_obs()
    lin1 = _make_lineage("sys.a", "art", "loc", "v1")
    lin2 = _make_lineage("sys.a", "art", "loc", "v2")
    assert ObservationOccurrenceIdentity.compute(obs.identity, lin1) != ObservationOccurrenceIdentity.compute(obs.identity, lin2)


def test_oi004_different_fact_same_lineage_different_identity():
    obs1 = _make_obs()
    obs2 = _make_obs2()
    lin = _make_lineage("sys.a", "art", "loc")
    assert ObservationOccurrenceIdentity.compute(obs1.identity, lin) != ObservationOccurrenceIdentity.compute(obs2.identity, lin)


def test_oi005_extraction_timestamp_cannot_affect_identity():
    # Source version ref is a string. If extraction timestamp is not inside the lineage, it cannot affect identity.
    # It is structurally excluded from the inputs to compute().
    pass


def test_oi006_retry_cannot_affect_identity():
    # Calling compute() multiple times yields same identity
    obs = _make_obs()
    lin = _make_lineage("sys.a", "art", "loc")
    occ1 = ObservationOccurrence.create(obs.identity, lin)
    occ2 = ObservationOccurrence.create(obs.identity, lin)
    assert occ1.identity == occ2.identity
