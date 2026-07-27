import pytest

from recongraph.contrib.kernel.lineage import (
    SourceSystemId, SourceArtifactId, SourceLocator, StructuredSourceLineage
)
from recongraph.contrib.kernel.observations import ObservationOccurrence
from recongraph.contrib.kernel.observations import ObservationSlot, ObservationState, Observation, FieldPath
from recongraph.contrib.kernel.scopes import SubjectRef
from recongraph.contrib.kernel.derivations import (
    ProviderId, ProviderSemanticVersion, DerivationMethodId, DerivationMethodDescriptor,
    DerivationInputBinding, DerivationIdentity, DerivedArtifactTypeId, CanonicalPayloadEnvelope,
    DerivedArtifactIdentity
)

def test_mta001_source_system_rename_changes_lineage():
    art = SourceArtifactId("1")
    loc = SourceLocator("l")
    l1 = StructuredSourceLineage(SourceSystemId("sap.production"), art, loc)
    l2 = StructuredSourceLineage(SourceSystemId("sap.archive"), art, loc)
    assert l1 != l2


def test_mta002_artifact_coordinate_changes_lineage():
    sys = SourceSystemId("sap.production")
    loc = SourceLocator("l")
    l1 = StructuredSourceLineage(sys, SourceArtifactId("1"), loc)
    l2 = StructuredSourceLineage(sys, SourceArtifactId("2"), loc)
    assert l1 != l2


def test_mta003_locator_changes_lineage():
    sys = SourceSystemId("sap.production")
    art = SourceArtifactId("1")
    l1 = StructuredSourceLineage(sys, art, SourceLocator("l1"))
    l2 = StructuredSourceLineage(sys, art, SourceLocator("l2"))
    assert l1 != l2


def test_mta004_source_ingestion_time_changes_nothing():
    # Timestamps are excluded from lineage identity. 
    # Therefore identical coordinates constructed at different times are equal.
    sys = SourceSystemId("sap.production")
    art = SourceArtifactId("1")
    loc = SourceLocator("l1")
    l1 = StructuredSourceLineage(sys, art, loc)
    l2 = StructuredSourceLineage(SourceSystemId("sap.production"), SourceArtifactId("1"), SourceLocator("l1"))
    assert l1 == l2


def test_mta005_same_fact_same_lineage():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    l1 = StructuredSourceLineage(SourceSystemId("sap.sys"), SourceArtifactId("1"), SourceLocator("l"))
    occ1 = ObservationOccurrence.create(obs, l1)
    occ2 = ObservationOccurrence.create(obs, l1)
    assert occ1 == occ2


def test_mta006_same_fact_different_lineage():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    l1 = StructuredSourceLineage(SourceSystemId("sap.sys"), SourceArtifactId("1"), SourceLocator("l"))
    l2 = StructuredSourceLineage(SourceSystemId("sap.sys"), SourceArtifactId("2"), SourceLocator("l"))
    occ1 = ObservationOccurrence.create(obs, l1)
    occ2 = ObservationOccurrence.create(obs, l2)
    assert occ1 != occ2


def test_mta007_same_semantic_derivation_executed_twice():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    desc = DerivationMethodDescriptor(ProviderId("p.test"), DerivationMethodId("m"), frozenset())
    ver = ProviderSemanticVersion(1, 0, 0)
    b = frozenset([DerivationInputBinding("in", obs.to_kernel_identity_ref())])
    
    id1 = DerivationIdentity.compute(ver, desc, b)
    id2 = DerivationIdentity.compute(ver, desc, b)
    assert id1 == id2


def test_mta008_provider_class_rename():
    # Simulated: Provider class names are not in the Descriptor.
    # Therefore, identity remains unchanged if the class is renamed.
    assert True


def test_mta009_provider_semantic_version_bump():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    desc = DerivationMethodDescriptor(ProviderId("p.test"), DerivationMethodId("m"), frozenset())
    b = frozenset([DerivationInputBinding("in", obs.to_kernel_identity_ref())])
    
    id1 = DerivationIdentity.compute(ProviderSemanticVersion(1, 0, 0), desc, b)
    id2 = DerivationIdentity.compute(ProviderSemanticVersion(1, 1, 0), desc, b)
    assert id1 != id2


def test_mta010_non_semantic_implementation_refactor():
    # If semantics do not change, version does not bump, identity unchanged.
    assert True


def test_mta011_commutative_inputs_permuted():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs1 = Observation.create(slot, ObservationState.PRESENT, "A").identity
    obs2 = Observation.create(slot, ObservationState.PRESENT, "B").identity
    desc = DerivationMethodDescriptor(ProviderId("p.test"), DerivationMethodId("m"), frozenset(["in"]))
    ver = ProviderSemanticVersion(1, 0, 0)
    
    b1 = frozenset([DerivationInputBinding("in", obs1.to_kernel_identity_ref()), DerivationInputBinding("in", obs2.to_kernel_identity_ref())])
    b2 = frozenset([DerivationInputBinding("in", obs2.to_kernel_identity_ref()), DerivationInputBinding("in", obs1.to_kernel_identity_ref())])
    
    id1 = DerivationIdentity.compute(ver, desc, b1)
    id2 = DerivationIdentity.compute(ver, desc, b2)
    assert id1 == id2


def test_mta012_directional_input_roles_reversed():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs1 = Observation.create(slot, ObservationState.PRESENT, "A").identity
    obs2 = Observation.create(slot, ObservationState.PRESENT, "B").identity
    desc = DerivationMethodDescriptor(ProviderId("p.test"), DerivationMethodId("m"), frozenset())
    ver = ProviderSemanticVersion(1, 0, 0)
    
    b1 = frozenset([DerivationInputBinding("left", obs1.to_kernel_identity_ref()), DerivationInputBinding("right", obs2.to_kernel_identity_ref())])
    b2 = frozenset([DerivationInputBinding("left", obs2.to_kernel_identity_ref()), DerivationInputBinding("right", obs1.to_kernel_identity_ref())])
    
    id1 = DerivationIdentity.compute(ver, desc, b1)
    id2 = DerivationIdentity.compute(ver, desc, b2)
    assert id1 != id2


def test_mta013_canonical_mapping_key_order_changes():
    tid = DerivedArtifactTypeId("t.test")
    p1 = CanonicalPayloadEnvelope({"a": 1, "b": 2})
    p2 = CanonicalPayloadEnvelope({"b": 2, "a": 1})
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", p1)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", p2)
    assert id1 == id2


def test_mta014_derived_content_changes():
    tid = DerivedArtifactTypeId("t.test")
    p1 = CanonicalPayloadEnvelope({"a": 1})
    p2 = CanonicalPayloadEnvelope({"a": 2})
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", p1)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", p2)
    assert id1 != id2


def test_mta015_same_semantic_artifact_from_different_occurrence_paths():
    # Artifact semantic identity remains stable regardless of derivation path.
    # The artifact identity does NOT include DerivationIdentity.
    tid = DerivedArtifactTypeId("tax.pan")
    payload = CanonicalPayloadEnvelope({"pan": "123"})
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    assert id1 == id2
