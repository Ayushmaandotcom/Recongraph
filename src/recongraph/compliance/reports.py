"""Report builders and CSV export (F5).

Produces accountant-ready summaries from a ``ReconciliationResult`` (accepted
as its JSON-dict form): match summary, supplier summary, and invoice detail.

The shapes mirror India Compliance's Excel sheets (match summary, supplier
data, invoice data) but emit CSV via the standard library.
"""

import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Sequence


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _sum(values: Iterable[Any]) -> Decimal:
    total = Decimal("0")
    for value in values:
        dec = _as_decimal(value)
        if dec is not None:
            total += dec
    return total


def _records_of(result: dict, side: str, packet: dict) -> list[dict]:
    return [r for r in packet.get(side, []) or [] if isinstance(r, dict)]


def _field(record: dict, *keys: str) -> Any:
    for key in keys:
        if record.get(key) not in (None, ""):
            return record[key]
    return None


def _gstin(record: dict) -> Any:
    return _field(record, "tax_identity", "gstin", "supplier_gstin")


def _vendor(record: dict) -> Any:
    return _field(record, "vendor_name", "supplier_name")


def _reference(record: dict) -> Any:
    return _field(record, "reference", "bill_no", "invoice_number")


def _amount(record: dict) -> Any:
    return _field(record, "amount")


def _taxable_value(record: dict) -> Any:
    return _field(record, "taxable_value", "amount")


def _total_tax(record: dict) -> Decimal:
    return _sum((record.get(k) for k in ("cgst", "sgst", "igst", "cess")))


def _fmt(value: Any) -> str:
    """Format a Decimal/str as a clean string with trailing zeros stripped."""
    dec = _as_decimal(value)
    if dec is None:
        return "0"
    text = format(dec, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


# ---------------------------------------------------------------------------
# Match summary
# ---------------------------------------------------------------------------

MATCH_SUMMARY_COLUMNS = (
    "match_status",
    "inward_supply_count",
    "purchase_count",
    "taxable_value_difference",
    "tax_difference",
    "action_taken",
)


def build_match_summary(result: dict) -> list[dict]:
    """Aggregate counts and amount differences by match status / action."""
    buckets: dict[str, dict[str, Any]] = {}

    def bucket(key: str) -> dict[str, Any]:
        return buckets.setdefault(key, {
            "match_status": key,
            "inward_supply_count": 0,
            "purchase_count": 0,
            "taxable_value_difference": Decimal("0"),
            "tax_difference": Decimal("0"),
            "action_taken": 0,
        })

    for match in result.get("auto_matches") or []:
        key = str(match.get("action") or "auto_match")
        row = bucket(key)
        row["action_taken"] += 1

    for packet in result.get("review_packets") or []:
        key = str(packet.get("action") or "review")
        row = bucket(key)
        purchases = _records_of(result, "purchases", packet)
        gsts = _records_of(result, "gsts", packet)
        row["inward_supply_count"] += len(gsts)
        row["purchase_count"] += len(purchases)
        p_taxable = _sum((_taxable_value(r) for r in purchases))
        g_taxable = _sum((_taxable_value(r) for r in gsts))
        row["taxable_value_difference"] += g_taxable - p_taxable
        p_tax = _sum((_total_tax(r) for r in purchases))
        g_tax = _sum((_total_tax(r) for r in gsts))
        row["tax_difference"] += g_tax - p_tax

    rows = list(buckets.values())
    for row in rows:
        row["taxable_value_difference"] = _fmt(row["taxable_value_difference"])
        row["tax_difference"] = _fmt(row["tax_difference"])
    return rows


# ---------------------------------------------------------------------------
# Supplier summary
# ---------------------------------------------------------------------------

SUPPLIER_COLUMNS = (
    "supplier_name",
    "supplier_gstin",
    "inward_supply_count",
    "purchase_count",
    "taxable_value_difference",
    "tax_difference",
    "action_taken",
)


def build_supplier_summary(result: dict) -> list[dict]:
    """Aggregate per-supplier counts and differences across all packets."""
    buckets: dict[str, dict[str, Any]] = {}

    def bucket(supplier: dict | None) -> dict[str, Any]:
        name = _vendor(supplier) if supplier else None
        gstin = _gstin(supplier) if supplier else None
        key = f"{gstin or ''}|{name or ''}"
        return buckets.setdefault(key, {
            "supplier_name": name,
            "supplier_gstin": gstin,
            "inward_supply_count": 0,
            "purchase_count": 0,
            "taxable_value_difference": Decimal("0"),
            "tax_difference": Decimal("0"),
            "action_taken": 0,
        })

    for packet in result.get("review_packets") or []:
        purchases = _records_of(result, "purchases", packet)
        gsts = _records_of(result, "gsts", packet)
        for p in purchases:
            row = bucket(p)
            row["purchase_count"] += 1
            row["action_taken"] += 1
            row["taxable_value_difference"] -= _sum((_taxable_value(p),))
            row["tax_difference"] -= _total_tax(p)
        for g in gsts:
            row = bucket(g)
            row["inward_supply_count"] += 1
            row["taxable_value_difference"] += _sum((_taxable_value(g),))
            row["tax_difference"] += _total_tax(g)

    rows = list(buckets.values())
    for row in rows:
        row["taxable_value_difference"] = _fmt(row["taxable_value_difference"])
        row["tax_difference"] = _fmt(row["tax_difference"])
    return rows


# ---------------------------------------------------------------------------
# Invoice detail
# ---------------------------------------------------------------------------

INVOICE_COLUMNS = (
    "match_status",
    "supplier_name",
    "supplier_gstin",
    "inward_supply_bill_no",
    "inward_supply_bill_date",
    "inward_supply_taxable_value",
    "inward_supply_cgst",
    "inward_supply_sgst",
    "inward_supply_igst",
    "inward_supply_cess",
    "purchase_bill_no",
    "purchase_bill_date",
    "purchase_taxable_value",
    "purchase_cgst",
    "purchase_sgst",
    "purchase_igst",
    "purchase_cess",
)


def _date_str(record: dict) -> Any:
    return _field(record, "record_date", "bill_date", "invoice_date")


def build_invoice_detail(result: dict) -> list[dict]:
    """Side-by-side purchase vs inward-supply detail rows."""
    rows: list[dict] = []

    def emit(match_status: str, purchase: dict | None, gst: dict | None) -> None:
        rows.append({
            "match_status": match_status,
            "supplier_name": _vendor(purchase) if purchase else (_vendor(gst) if gst else None),
            "supplier_gstin": _gstin(purchase) if purchase else (_gstin(gst) if gst else None),
            "inward_supply_bill_no": _reference(gst) if gst else None,
            "inward_supply_bill_date": _date_str(gst) if gst else None,
            "inward_supply_taxable_value": _taxable_value(gst) if gst else None,
            "inward_supply_cgst": gst.get("cgst") if gst else None,
            "inward_supply_sgst": gst.get("sgst") if gst else None,
            "inward_supply_igst": gst.get("igst") if gst else None,
            "inward_supply_cess": gst.get("cess") if gst else None,
            "purchase_bill_no": _reference(purchase) if purchase else None,
            "purchase_bill_date": _date_str(purchase) if purchase else None,
            "purchase_taxable_value": _taxable_value(purchase) if purchase else None,
            "purchase_cgst": purchase.get("cgst") if purchase else None,
            "purchase_sgst": purchase.get("sgst") if purchase else None,
            "purchase_igst": purchase.get("igst") if purchase else None,
            "purchase_cess": purchase.get("cess") if purchase else None,
        })

    for match in result.get("auto_matches") or []:
        # auto-match entries in the flat dict carry only hypothesis data, not
        # raw records; skip detail rows for them.
        continue

    for packet in result.get("review_packets") or []:
        status = str(packet.get("action") or "review")
        purchases = _records_of(result, "purchases", packet)
        gsts = _records_of(result, "gsts", packet)
        n = max(len(purchases), len(gsts), 1)
        for i in range(n):
            emit(status, purchases[i] if i < len(purchases) else None,
                 gsts[i] if i < len(gsts) else None)

    return rows


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

REPORTS = {
    "match_summary": (build_match_summary, MATCH_SUMMARY_COLUMNS),
    "supplier": (build_supplier_summary, SUPPLIER_COLUMNS),
    "invoice": (build_invoice_detail, INVOICE_COLUMNS),
}


def _get_report(report: str) -> tuple[Any, tuple[str, ...]]:
    if report not in REPORTS:
        raise ValueError(f"Unknown report '{report}'. Choose from {sorted(REPORTS)}")
    return REPORTS[report]


def build_report(result: dict, report: str) -> list[dict]:
    builder, _ = _get_report(report)
    return builder(result)


def export_csv(result: dict, report: str) -> str:
    """Render a report as CSV text."""
    builder, columns = _get_report(report)
    rows = builder(result)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(columns), extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def export_report(result: dict, report: str, fmt: str = "csv") -> bytes:
    """Return report bytes in the requested format (``csv`` or ``xlsx``)."""
    if fmt == "csv":
        return export_csv(result, report).encode("utf-8")
    if fmt == "xlsx":
        return _export_xlsx(result, report)
    raise ValueError(f"Unsupported format '{fmt}'")


def _export_xlsx(result: dict, report: str) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise RuntimeError(
            "openpyxl is required for xlsx export. Install with "
            "`pip install recongraph[export]`."
        ) from exc

    builder, columns = _get_report(report)
    rows = builder(result)
    wb = Workbook()
    ws = wb.active
    ws.title = report
    ws.append(list(columns))
    for row in rows:
        ws.append([row.get(col) for col in columns])

    import io as _io
    buf = _io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
