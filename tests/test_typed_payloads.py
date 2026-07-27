import pytest
from recongraph.contrib.kernel.payloads import CanonicalPayloadEnvelope, TypedPayloadEnvelope
from recongraph.contrib.kernel.identity import canonical_encode


def test_tpe001_typed_payload_envelope():
    content = {"status": "active"}
    canon_env = CanonicalPayloadEnvelope(content)
    typed_env = TypedPayloadEnvelope(
        type_id="recongraph.payload.status.v1",
        semantic_version="1.0.0",
        payload=canon_env
    )
    
    assert typed_env.type_id == "recongraph.payload.status.v1"
    assert typed_env.semantic_version == "1.0.0"
    
    # Must serialize deterministically
    assert typed_env.canonicalize()


def test_ea065_nfc_nfd_typed_payload_equivalence():
    canon_nfc = CanonicalPayloadEnvelope({"name": "é"})
    canon_nfd = CanonicalPayloadEnvelope({"name": "e\u0301"})  # NFD e + acute
    
    typed_nfc = TypedPayloadEnvelope("test", "1", canon_nfc)
    typed_nfd = TypedPayloadEnvelope("test", "1", canon_nfd)
    
    assert typed_nfc.canonicalize() == typed_nfd.canonicalize()


def test_ea066_int64_overflow_payload_rejected():
    with pytest.raises(ValueError):
        canon = CanonicalPayloadEnvelope({"val": 9223372036854775808})
        canon.canonicalize()
