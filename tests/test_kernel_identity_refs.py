import pytest
from recongraph.contrib.kernel.identity import (
    IdentityDomainId, IdentitySchemaId, IdentityDigest, KernelIdentityRef
)


def test_iv001_valid_core_domain():
    assert IdentityDomainId("recongraph.observation")


def test_iv002_valid_plugin_domain():
    assert IdentityDomainId("plugin.acme.bank_account")


def test_iv003_empty_domain_rejected():
    with pytest.raises(ValueError):
        IdentityDomainId("")


def test_iv004_whitespace_rejected():
    with pytest.raises(ValueError):
        IdentityDomainId(" recongraph.observation ")


def test_iv005_uppercase_normalization_forbidden_rejected():
    with pytest.raises(ValueError):
        IdentityDomainId("Recongraph.Observation")


def test_iv006_unicode_identifier_rejected():
    with pytest.raises(ValueError):
        IdentityDomainId("दावा.समान_कानूनी_इकाई")


def test_iv007_malformed_digest_rejected():
    with pytest.raises(ValueError):
        IdentityDigest("sha256:xyz")


def test_iv008_unsupported_digest_algorithm_rejected():
    with pytest.raises(ValueError):
        # We only support sha256 right now per the regex + checks
        IdentityDigest("sha1:a9993e364706816aba3e25717850c26c9cd0d89d")


def test_iv009_sha256_wrong_length_rejected():
    with pytest.raises(ValueError):
        IdentityDigest("sha256:a9993e364706816aba3e25717850c26c9cd0d89d")


def test_iv010_uppercase_hex_rejected():
    with pytest.raises(ValueError):
        IdentityDigest("sha256:" + "A" * 64)


def test_iv011_digest_equality_deterministic():
    d1 = IdentityDigest("sha256:" + "a" * 64)
    d2 = IdentityDigest("sha256:" + "a" * 64)
    assert d1 == d2


def test_iv012_domain_participates_in_ref_equality():
    d = IdentityDigest("sha256:" + "a" * 64)
    s = IdentitySchemaId("recongraph.v1")
    r1 = KernelIdentityRef(IdentityDomainId("domain.a"), s, d)
    r2 = KernelIdentityRef(IdentityDomainId("domain.b"), s, d)
    assert r1 != r2


def test_iv013_schema_participates_in_ref_equality():
    d = IdentityDigest("sha256:" + "a" * 64)
    dom = IdentityDomainId("recongraph.v1")
    r1 = KernelIdentityRef(dom, IdentitySchemaId("schema.a"), d)
    r2 = KernelIdentityRef(dom, IdentitySchemaId("schema.b"), d)
    assert r1 != r2
