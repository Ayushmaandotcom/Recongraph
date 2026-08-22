"""Tests for the Indian tax-identifier taxonomy (F6).

Patterns ported from India Compliance; see NOTICE.
"""

from recongraph.domain.tax.taxonomy import (
    GstinCategory,
    classify_gstin_category,
    validate_invoice_number,
    validate_pan,
    validate_pincode,
)


def test_registered_regular_gstin() -> None:
    # 29 = state, PAN block, 'Z' position, valid-looking check digit
    assert classify_gstin_category("29ABCDE1234F1Z5") == GstinCategory.REGISTERED


def test_composition_and_sez_share_registered() -> None:
    # Composition/SEZ use the same REGISTERED pattern, so they classify as REGISTERED
    assert classify_gstin_category("29ABCDE1234F1Z5") == GstinCategory.REGISTERED


def test_tax_deductor_gstin() -> None:
    # position 14 is 'D' → Tax Deductor
    assert classify_gstin_category("27AABCT1234F1DZ") == GstinCategory.TAX_DEDUCTOR


def test_tax_collector_gstin() -> None:
    # position 14 is 'C' → Tax Collector
    assert classify_gstin_category("29ABCDE1234F1CZ") == GstinCategory.TAX_COLLECTOR


def test_uin_holder_gstin() -> None:
    # UNBODY pattern: 4 digits + 3 letters + 5 digits + U/O + N + alphanumeric
    assert classify_gstin_category("1234ABC12345UN0") == GstinCategory.UIN_HOLDERS


def test_overseas_nri_gstin() -> None:
    # NRI_ID: 4 digits + 3 letters + 5 digits + NR + alnum
    assert classify_gstin_category("1234ABC12345NR0") == GstinCategory.OVERSEAS


def test_unknown_gstin_returns_none() -> None:
    assert classify_gstin_category("not-a-gstin") is None
    assert classify_gstin_category(None) is None
    assert classify_gstin_category("") is None


def test_classification_is_case_and_space_insensitive() -> None:
    assert classify_gstin_category("  29abcde1234f1z5  ") == GstinCategory.REGISTERED


def test_validate_pan() -> None:
    assert validate_pan("ABCDE1234F") is True
    assert validate_pan("abcde1234f") is True
    assert validate_pan("ABCDE1234") is False
    assert validate_pan("") is False
    assert validate_pan(None) is False


def test_validate_pincode() -> None:
    assert validate_pincode("110001") is True
    assert validate_pincode("000000") is False  # first digit cannot be 0
    assert validate_pincode("12345") is False
    assert validate_pincode("") is False


def test_validate_invoice_number() -> None:
    assert validate_invoice_number("INV-001/2024") is True
    assert validate_invoice_number("A") is True
    assert validate_invoice_number("") is False
    assert validate_invoice_number(None) is False
    # 17 characters exceeds the 16-char maximum
    assert validate_invoice_number("INVOICE-NUMBER-01") is False
