import pytest
import unicodedata
from recongraph.contrib.kernel.identity import canonical_encode


def test_ce001_mapping_key_insertion_order_invariant():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert canonical_encode(d1) == canonical_encode(d2)


def test_ce002_nfc_nfd_payload_string_canonicalize_identically():
    nfc_str = unicodedata.normalize("NFC", "é")
    nfd_str = unicodedata.normalize("NFD", "é")
    assert canonical_encode(nfc_str) == canonical_encode(nfd_str)


def test_ce003_ascii_identifier_unicode_rejected_for_keys():
    # canonical_encode validates keys as machine keys (ASCII)
    with pytest.raises(ValueError, match="Machine keys must be ASCII"):
        canonical_encode({"संगठन_नाम": "abc"})


def test_ce004_signed_int64_min_accepted():
    min_int64 = -9223372036854775808
    assert canonical_encode(min_int64)


def test_ce005_signed_int64_max_accepted():
    max_int64 = 9223372036854775807
    assert canonical_encode(max_int64)


def test_ce006_below_int64_rejected():
    with pytest.raises(ValueError, match="Integer out of int64 bounds"):
        canonical_encode(-9223372036854775809)


def test_ce007_above_int64_rejected():
    with pytest.raises(ValueError, match="Integer out of int64 bounds"):
        canonical_encode(9223372036854775808)


def test_ce008_float_rejected():
    with pytest.raises(ValueError, match="Floats are forbidden"):
        canonical_encode(1.0)


def test_ce009_nan_rejected_indirectly_as_float():
    with pytest.raises(ValueError, match="Floats are forbidden"):
        canonical_encode(float("nan"))


def test_ce010_negative_zero_rejected():
    with pytest.raises(ValueError, match="Floats are forbidden"):
        canonical_encode(-0.0)


def test_ce011_array_order_changes_identity():
    assert canonical_encode([1, 2]) != canonical_encode([2, 1])


def test_ce012_nested_mapping_canonical():
    d1 = {"x": {"a": 1, "b": 2}, "y": 3}
    d2 = {"y": 3, "x": {"b": 2, "a": 1}}
    assert canonical_encode(d1) == canonical_encode(d2)


def test_ce013_non_string_mapping_key_rejected():
    with pytest.raises(ValueError, match="Dict keys must be strings"):
        canonical_encode({1: "a"})


def test_ce014_non_ascii_schema_key_rejected():
    with pytest.raises(ValueError, match="Machine keys must be ASCII"):
        canonical_encode({"दावा": "value"})


def test_ce015_custom_python_object_rejected():
    class Dummy:
        pass
    with pytest.raises(ValueError, match="is forbidden in canonical semantic encoding"):
        canonical_encode(Dummy())
