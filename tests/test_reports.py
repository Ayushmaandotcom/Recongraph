"""Tests for report builders and CSV export (F5)."""

import csv
import io

from recongraph.compliance.reports import (
    build_invoice_detail,
    build_match_summary,
    build_supplier_summary,
    export_csv,
    REPORTS,
)


def _result() -> dict:
    return {
        "auto_matches": [{"action": "AUTO_MATCH"}],
        "review_packets": [
            {
                "packet_id": "PKT1",
                "action": "review_weak",
                "purchases": [
                    {
                        "record_id": "P1",
                        "vendor_name": "Acme",
                        "tax_identity": "29ABCDE1234F1Z5",
                        "reference": "INV-1",
                        "amount": "1000.00",
                        "taxable_value": "1000.00",
                        "cgst": "90.00",
                        "sgst": "90.00",
                        "igst": None,
                        "cess": None,
                        "record_date": "2024-04-01",
                    }
                ],
                "gsts": [
                    {
                        "record_id": "G1",
                        "vendor_name": "Acme",
                        "tax_identity": "29ABCDE1234F1Z5",
                        "reference": "INV-1",
                        "amount": "1000.00",
                        "taxable_value": "1000.00",
                        "cgst": "90.00",
                        "sgst": "90.00",
                        "igst": None,
                        "cess": None,
                        "record_date": "2024-04-01",
                    }
                ],
            }
        ],
    }


def test_match_summary_counts() -> None:
    rows = build_match_summary(_result())
    by_status = {r["match_status"]: r for r in rows}
    assert by_status["AUTO_MATCH"]["action_taken"] == 1
    assert by_status["review_weak"]["purchase_count"] == 1
    assert by_status["review_weak"]["inward_supply_count"] == 1
    assert by_status["review_weak"]["tax_difference"] == "0"


def test_supplier_summary() -> None:
    rows = build_supplier_summary(_result())
    assert len(rows) == 1
    assert rows[0]["supplier_name"] == "Acme"
    assert rows[0]["purchase_count"] == 1
    assert rows[0]["inward_supply_count"] == 1


def test_invoice_detail_side_by_side() -> None:
    rows = build_invoice_detail(_result())
    assert len(rows) == 1
    assert rows[0]["purchase_bill_no"] == "INV-1"
    assert rows[0]["inward_supply_bill_no"] == "INV-1"
    assert rows[0]["purchase_cgst"] == "90.00"


def test_export_csv_has_header_and_rows() -> None:
    text = export_csv(_result(), "supplier")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert reader.fieldnames is not None
    assert "supplier_name" in reader.fieldnames
    assert len(rows) == 1


def test_unknown_report_raises() -> None:
    import pytest
    with pytest.raises(ValueError):
        export_csv(_result(), "nope")


def test_all_reports_registered() -> None:
    assert set(REPORTS) == {"match_summary", "supplier", "invoice"}
