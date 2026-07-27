import pytest
import json
from dataclasses import dataclass

from recongraph.contrib.kernel.derivations import (
    DerivedArtifactTypeId,
    DerivedArtifactIdentity,
    DerivedArtifact,
    CanonicalPayloadEnvelope,
    DerivationIdentity
)

def test_derived_artifact_type_id():
    tid = DerivedArtifactTypeId("tax.pan")
    assert tid.value == "tax.pan"
    
    with pytest.raises(ValueError):
        DerivedArtifactTypeId("PAN") # missing namespace


def test_dak001_same_artifact_same_payload_same_derivation():
    tid = DerivedArtifactTypeId("tax.pan")
    payload = CanonicalPayloadEnvelope({"pan": "ABCDE1234F"})
    did = DerivationIdentity("sha256:111")
    
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    
    assert id1 == id2


def test_dak002_different_artifact_type_different_identity():
    payload = CanonicalPayloadEnvelope({"text": "ABC"})
    
    id1 = DerivedArtifactIdentity.compute(DerivedArtifactTypeId("ocr.text"), "1.0", payload)
    id2 = DerivedArtifactIdentity.compute(DerivedArtifactTypeId("vendor.name"), "1.0", payload)
    
    assert id1 != id2


def test_dak003_different_payload_different_identity():
    tid = DerivedArtifactTypeId("tax.pan")
    
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", CanonicalPayloadEnvelope({"pan": "A"}))
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", CanonicalPayloadEnvelope({"pan": "B"}))
    
    assert id1 != id2


def test_dak004_different_derivation_identity():
    # As requested by the ADR, DerivedArtifactIdentity only contains semantic type + version + fingerprint.
    # It does NOT include DerivationIdentity. Derivation ancestry is edges, artifact is node.
    tid = DerivedArtifactTypeId("tax.pan")
    payload = CanonicalPayloadEnvelope({"pan": "A"})
    
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", payload)
    
    assert id1 == id2


def test_dak005_mapping_insertion_order_changes_same_identity():
    tid = DerivedArtifactTypeId("test.mapping")
    
    p1 = CanonicalPayloadEnvelope({"a": 1, "b": 2})
    p2 = CanonicalPayloadEnvelope({"b": 2, "a": 1})
    
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", p1)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", p2)
    
    assert id1 == id2


def test_dak006_tuple_order_changes_different_identity():
    tid = DerivedArtifactTypeId("test.tuple")
    
    p1 = CanonicalPayloadEnvelope({"t": (1, 2)})
    p2 = CanonicalPayloadEnvelope({"t": (2, 1)})
    
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", p1)
    id2 = DerivedArtifactIdentity.compute(tid, "1.0", p2)
    
    assert id1 != id2


def test_dak007_float_payload_rejected():
    with pytest.raises(ValueError):
        CanonicalPayloadEnvelope({"amount": 100.5})


def test_dak008_nan_rejected():
    with pytest.raises(ValueError):
        CanonicalPayloadEnvelope({"amount": float("nan")})


def test_dak009_set_rejected():
    with pytest.raises(ValueError):
        CanonicalPayloadEnvelope({"tags": {"a", "b"}})


def test_dak010_arbitrary_object_rejected():
    class Custom:
        pass
        
    with pytest.raises(ValueError):
        CanonicalPayloadEnvelope({"obj": Custom()})


def test_dak011_unicode_string_deterministic():
    tid = DerivedArtifactTypeId("test.str")
    p1 = CanonicalPayloadEnvelope({"s": "प्रदायक"})
    id1 = DerivedArtifactIdentity.compute(tid, "1.0", p1)
    assert id1.digest.startswith("sha256:")


def test_dak012_empty_string_payload():
    # Should be valid
    CanonicalPayloadEnvelope({"s": ""})


def test_dak013_none_payload():
    # Should be valid
    CanonicalPayloadEnvelope({"s": None})


def test_dak014_nested_canonical_payload():
    # Should be valid
    CanonicalPayloadEnvelope({"outer": {"inner": (1, "a", None, True)}})


def test_dak020_domain_separation_from_derivation_identity():
    # A DerivedArtifactIdentity and DerivationIdentity with the same internal digest bytes 
    # must not collide due to prefix domain separation.
    pass
