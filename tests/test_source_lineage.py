import pytest
import json
from dataclasses import dataclass

from recongraph.domain.lineage import (
    SourceSystemId,
    SourceArtifactId,
    SourceLocator
)


def test_sl001_valid_source_system():
    sid = SourceSystemId("sap.production")
    assert sid.value == "sap.production"
    
    assert SourceSystemId("document.upload_2024").value == "document.upload_2024"


def test_sl002_source_system_missing_namespace():
    with pytest.raises(ValueError):
        SourceSystemId("sap")


def test_sl003_uppercase_source_system():
    with pytest.raises(ValueError):
        SourceSystemId("SAP.production")


def test_sl004_whitespace_source_system():
    with pytest.raises(ValueError):
        SourceSystemId("sap. production")


def test_sl005_empty_artifact_id():
    with pytest.raises(ValueError):
        SourceArtifactId("")


def test_sl006_artifact_surrounding_whitespace():
    with pytest.raises(ValueError):
        SourceArtifactId("  DOC123  ")


def test_sl007_artifact_internal_structured_punctuation():
    # Should accept colons, dashes, etc. opaque coordinate
    aid = SourceArtifactId("purchase_invoice:874219@v1")
    assert aid.value == "purchase_invoice:874219@v1"


def test_sl008_artifact_case_preservation():
    aid1 = SourceArtifactId("DOC_123")
    aid2 = SourceArtifactId("doc_123")
    assert aid1 != aid2
    assert aid1.value == "DOC_123"


def test_sl009_empty_locator():
    with pytest.raises(ValueError):
        SourceLocator("")


def test_sl010_locator_surrounding_whitespace():
    with pytest.raises(ValueError):
        SourceLocator("  field:vendor  ")


def test_sl011_locator_internal_slash():
    loc = SourceLocator("page:2/bbox:100,200,500,260")
    assert loc.value == "page:2/bbox:100,200,500,260"


def test_sl012_locator_unicode_decision():
    # Locators might legitimately contain unicode fields if the adapter dictates it
    loc = SourceLocator("column:प्रदायक")
    assert loc.value == "column:प्रदायक"


def test_sl013_deterministic_equality():
    loc1 = SourceLocator("page:2")
    loc2 = SourceLocator("page:2")
    assert loc1 == loc2
    
    sys1 = SourceSystemId("gst.portal")
    sys2 = SourceSystemId("gst.portal")
    assert sys1 == sys2


def test_sl014_hash_stability_within_process_semantics():
    # Ensure they can be used in dicts/sets and rely on __hash__, but we will not mandate 
    # hash() to be stable cross-process in tests. Serialization provides absolute stability.
    s = {SourceSystemId("sap.production")}
    assert SourceSystemId("sap.production") in s


def test_sl015_different_typed_ids_never_compare_equal():
    assert SourceSystemId("sap.production") != SourceArtifactId("sap.production")


def test_sl016_timestamp_not_auto_generated():
    # If a SourceArtifactId generated timestamps automatically, two instances with the same value 
    # would not compare equal if generated milliseconds apart.
    aid1 = SourceArtifactId("file1")
    aid2 = SourceArtifactId("file1")
    assert aid1 == aid2


def test_sl017_artifact_does_not_infer_content_hash():
    # SourceArtifactId takes the coordinate literally. It does not parse or check file existence.
    aid = SourceArtifactId("sha256:abc")
    assert aid.value == "sha256:abc"
    assert not hasattr(aid, "hash_value")


def test_sl018_source_system_does_not_parse_provider_identity():
    # It must not be conflated with ProviderId from K5.
    # Even if grammar matches, they are strictly domain-separated types in Python.
    sys_id = SourceSystemId("recongraph.vendor")
    assert sys_id.value == "recongraph.vendor"


from recongraph.domain.observations import ObservationSlot, ObservationState, Observation, FieldPath
from recongraph.domain.scopes import SubjectRef
from recongraph.domain.lineage import StructuredSourceLineage, SourceVersionRef, ObservationOccurrence

def test_structured_source_lineage_serialization():
    sys = SourceSystemId("sap.production")
    art = SourceArtifactId("purchase_invoice:123")
    loc = SourceLocator("field:vendor_name")
    ver = SourceVersionRef("rowversion:1")
    
    lineage = StructuredSourceLineage(sys, art, loc, ver)
    
    # We must explicitly canonicalize to bytes
    canonical_bytes = lineage.canonicalize_for_serialization()
    assert isinstance(canonical_bytes, bytes)
    
    payload = json.loads(canonical_bytes.decode("utf-8"))
    assert payload["schema"] == "recongraph.source_lineage.v1"
    assert payload["source_system"] == "sap.production"
    assert payload["source_artifact"] == "purchase_invoice:123"
    assert payload["source_version"] == "rowversion:1"


def test_observation_occurrence_invariants():
    slot = ObservationSlot(SubjectRef("urn:1"), FieldPath("vendor"))
    obs1 = Observation.create(slot, ObservationState.PRESENT, "ABC").identity
    obs2 = Observation.create(slot, ObservationState.PRESENT, "XYZ").identity
    
    lin1 = StructuredSourceLineage(SourceSystemId("sys.a"), SourceArtifactId("1"), SourceLocator("L"))
    lin2 = StructuredSourceLineage(SourceSystemId("sys.b"), SourceArtifactId("2"), SourceLocator("L"))
    
    # 1. Same observation + same lineage = Equal
    occ1a = ObservationOccurrence(obs1, lin1)
    occ1b = ObservationOccurrence(obs1, lin1)
    assert occ1a == occ1b
    
    # 2. Same observation + different lineage = Distinct
    occ_diff_lin = ObservationOccurrence(obs1, lin2)
    assert occ1a != occ_diff_lin
    
    # 3. Different observation + same lineage = Distinct
    # This prevents the OCR semantic attack where OCR engine A and B read the same PDF bbox 
    # but produce different text. Their lineage is identical, but their epistemic content differs.
    occ_diff_obs = ObservationOccurrence(obs2, lin1)
    assert occ1a != occ_diff_obs
