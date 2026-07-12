from recongraph.normalization.text import (
    normalize_reference,
    normalize_vendor_name,
)


def test_normalize_reference_removes_formatting_differences() -> None:
    assert normalize_reference("AB/1042") == "ab1042"
    assert normalize_reference("AB-1042") == "ab1042"
    assert normalize_reference("AB 1042") == "ab1042"
    assert normalize_reference("ab1042") == "ab1042"


def test_normalize_vendor_name_removes_legal_suffixes() -> None:
    assert normalize_vendor_name("ABC STEELS PVT. LTD.") == "abc steels"
    assert (
        normalize_vendor_name("ABC Steels Private Limited")
        == "abc steels"
    )
    assert (
        normalize_vendor_name("Northstar Components Pvt Ltd")
        == "northstar components"
    )


def test_normalize_vendor_name_preserves_meaningful_tokens() -> None:
    assert (
        normalize_vendor_name("SHREE BALAJI ENT.")
        == "shree balaji ent"
    )
