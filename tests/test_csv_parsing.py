"""Tests for the extended CSV parser (F3)."""

from decimal import Decimal

from recongraph.compliance.csv_parsing import parse_purchase_csv, parse_gst_csv


def test_minimal_columns_still_parse() -> None:
    csv = "record_id,vendor_name,amount,record_date,gstin\nP1,Acme,1000,2024-04-01,29ABCDE1234F1Z5\n"
    records = parse_purchase_csv(csv)
    assert len(records) == 1
    assert records[0].record_id == "P1"
    assert records[0].tax_identity == "29ABCDE1234F1Z5"
    assert records[0].place_of_supply is None


def test_extended_columns_parse() -> None:
    csv = (
        "record_id,vendor_name,amount,record_date,gstin,place_of_supply,"
        "is_reverse_charge,cgst,sgst,igst,cess,taxable_value,classification\n"
        "P1,Acme,1000,2024-04-01,29ABCDE1234F1Z5,29,false,90,90,,,1000,B2B\n"
    )
    records = parse_purchase_csv(csv)
    r = records[0]
    assert r.place_of_supply == "29"
    assert r.is_reverse_charge is False
    assert r.cgst == Decimal("90")
    assert r.taxable_value == Decimal("1000")
    assert r.igst is None
    assert r.classification == "B2B"


def test_reverse_charge_boolean_parsing() -> None:
    csv = "record_id,vendor_name,amount,record_date,is_reverse_charge\nP1,Acme,1000,2024-04-01,yes\n"
    assert parse_purchase_csv(csv)[0].is_reverse_charge is True
    csv = "record_id,vendor_name,amount,record_date,is_reverse_charge\nP1,Acme,1000,2024-04-01,no\n"
    assert parse_purchase_csv(csv)[0].is_reverse_charge is False


def test_gst_csv_uses_supplier_name() -> None:
    csv = "record_id,supplier_name,amount,record_date,gstin\nG1,Acme GST,500,2024-04-02,27AAAAA1111A1Z5\n"
    records = parse_gst_csv(csv)
    assert records[0].vendor_name == "Acme GST"
    assert records[0].sign == -1
