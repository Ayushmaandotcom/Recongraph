import pytest

from recongraph.normalization.text import (
    extract_numeric_reference_tokens,
    normalize_reference,
    normalize_tax_identity,
    normalize_vendor_name,
)


def test_normalize_reference_removes_formatting_differences() -> None:
    assert normalize_reference("AB/1042") == "ab1042"
    assert normalize_reference("AB-1042") == "ab1042"
    assert normalize_reference("AB 1042") == "ab1042"
    assert normalize_reference("ab1042") == "ab1042"


def test_normalize_vendor_name_removes_legal_suffixes() -> None:
    assert normalize_vendor_name("ABC STEELS PVT. LTD.") == "abc steel"
    assert (
        normalize_vendor_name("ABC Steels Private Limited")
        == "abc steel"
    )
    assert (
        normalize_vendor_name("Northstar Components Pvt Ltd")
        == "northstar component"
    )


def test_normalize_vendor_name_preserves_unmapped_meaningful_tokens() -> None:
    assert (
        normalize_vendor_name("SHREE BALAJI FOODS")
        == "shree balaji foods"
    )


def test_normalize_vendor_name_canonicalizes_known_aliases() -> None:
    assert (
        normalize_vendor_name("SHREE BALAJI ENT.")
        == "shree balaji enterprises"
    )


def test_normalize_vendor_name_canonicalizes_known_token_variants() -> None:
    assert (
        normalize_vendor_name("ABC STEELS PVT. LTD.")
        == "abc steel"
    )
    assert (
        normalize_vendor_name("Northstar Components Pvt Ltd")
        == "northstar component"
    )
    assert (
        normalize_vendor_name("Metro Office Solutions")
        == "metro office solution"
    )
    assert (
        normalize_vendor_name("Apex Industrial Supplies")
        == "apex industrial supply"
    )


def test_normalize_tax_identity_standardizes_case_and_whitespace() -> None:
    assert (
        normalize_tax_identity(" 07abcde1234f1z5 ")
        == "07ABCDE1234F1Z5"
    )


def test_extract_numeric_reference_tokens_finds_significant_numbers() -> None:
    tokens = extract_numeric_reference_tokens(
        "INV-2026-1042"
    )

    assert tokens == {"2026", "1042"}


def test_extract_numeric_reference_tokens_ignores_short_numbers() -> None:
    tokens = extract_numeric_reference_tokens(
        "INV-22-A-1042"
    )

    assert tokens == {"1042"}


def test_extract_numeric_reference_tokens_rejects_non_positive_min_length() -> None:
    with pytest.raises(
        ValueError,
        match="min_length must be greater than zero",
    ):
        extract_numeric_reference_tokens(
            "INV-1042",
            min_length=0,
        )
