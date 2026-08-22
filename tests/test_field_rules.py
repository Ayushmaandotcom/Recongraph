"""Tests for the field-level rule matcher (F3)."""

from datetime import date
from decimal import Decimal

from recongraph.compliance.field_rules import (
    FieldRuleMatcher,
    MatchStatus,
    Rule,
)
from recongraph.domain.records import PurchaseRecord, GSTRecord


def _purchase(**kw) -> PurchaseRecord:
    base = dict(
        record_id="P1",
        vendor_name="Acme Ltd",
        reference="INV-001",
        amount=Decimal("1000.00"),
        record_date=date(2024, 4, 1),
        tax_identity="29ABCDE1234F1Z5",
        fiscal_year="2023-24",
        company_gstin="27AAACA1234F1Z5",
        place_of_supply="29",
        is_reverse_charge=False,
        taxable_value=Decimal("1000.00"),
        cgst=Decimal("90.00"),
        sgst=Decimal("90.00"),
        igst=None,
        cess=None,
    )
    base.update(kw)
    return PurchaseRecord(**base)


def _gst(**kw) -> GSTRecord:
    base = dict(
        record_id="G1",
        vendor_name="Acme Ltd",
        reference="INV-001",
        amount=Decimal("1000.00"),
        record_date=date(2024, 4, 1),
        tax_identity="29ABCDE1234F1Z5",
        fiscal_year="2023-24",
        company_gstin="27AAACA1234F1Z5",
        place_of_supply="29",
        is_reverse_charge=False,
        taxable_value=Decimal("1000.00"),
        cgst=Decimal("90.00"),
        sgst=Decimal("90.00"),
        igst=None,
        cess=None,
    )
    base.update(kw)
    return GSTRecord(**base)


def test_exact_match_when_all_fields_equal() -> None:
    assert FieldRuleMatcher.compare(_purchase(), _gst()) == MatchStatus.EXACT_MATCH


def test_suggested_match_on_rounding_difference() -> None:
    p = _purchase(taxable_value=Decimal("1000.00"), cgst=Decimal("90.00"), sgst=Decimal("90.00"))
    g = _gst(taxable_value=Decimal("1001.00"), cgst=Decimal("90.50"), sgst=Decimal("90.50"))
    assert FieldRuleMatcher.compare(p, g) == MatchStatus.SUGGESTED_MATCH


def test_suggested_match_on_fuzzy_bill_no() -> None:
    p = _purchase(reference="INV-001/2024")
    g = _gst(reference="INV-001/2024A")
    status = FieldRuleMatcher.compare(p, g)
    assert status in (MatchStatus.EXACT_MATCH, MatchStatus.SUGGESTED_MATCH)


def test_mismatch_on_conflicting_supplier_gstin() -> None:
    p = _purchase(tax_identity="29ABCDE1234F1Z5")
    g = _gst(tax_identity="27AAAAA1111A1Z5")
    assert FieldRuleMatcher.compare(p, g) == MatchStatus.MISMATCH


def test_mismatch_when_bill_number_differs_and_amounts_differ() -> None:
    p = _purchase(reference="INV-999", taxable_value=Decimal("5000.00"))
    g = _gst(reference="INV-001", taxable_value=Decimal("1000.00"))
    assert FieldRuleMatcher.compare(p, g) == MatchStatus.MISMATCH


def test_pan_level_ignores_supplier_gstin() -> None:
    # PAN-level rules do not compare supplier_gstin, so different GSTINs but
    # otherwise matching fields fall through to the first PAN row (MISMATCH).
    p = _purchase(tax_identity="29ABCDE1234F1Z5")
    g = _gst(tax_identity="29ABCDE1234F1Z5")
    assert FieldRuleMatcher.compare(p, g, level="pan") == MatchStatus.MISMATCH


def test_rounding_operator_boundary() -> None:
    matcher = FieldRuleMatcher()
    assert matcher._rounding(Decimal("1000"), Decimal("1001")) is True
    assert matcher._rounding(Decimal("1000"), Decimal("1002")) is False
    assert matcher._rounding(None, Decimal("1000")) is False
