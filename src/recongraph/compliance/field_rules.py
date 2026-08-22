"""Deterministic field-level reconciliation rules.

Ported from India Compliance's Purchase Reconciliation Tool
(`gst_india/doctype/purchase_reconciliation_tool/__init__.py`), Resilient Tech,
GPL v3. See NOTICE.

The original engine compares purchase records against GST inward supplies using
an ordered list of rule rows. Each row declares, per field, one of:

  - EXACT_MATCH         -> the two values must be equal
  - FUZZY_MATCH         -> bill number matched fuzzily
  - ROUNDING_DIFFERENCE -> numeric fields within +-1 (hardcoded)

The first rule whose declared fields all pass determines the match status. This
module reimplements that behavior as an optional, standalone matcher. It
complements — not replaces — ReconGraph's evidence-graph engine.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Callable, Sequence

from rapidfuzz import fuzz

from recongraph.domain.records import PurchaseRecord, GSTRecord


class Rule(Enum):
    EXACT_MATCH = "Exact Match"
    FUZZY_MATCH = "Fuzzy Match"
    ROUNDING_DIFFERENCE = "Rounding Difference"  # <= 1, hardcoded upstream


class MatchStatus(Enum):
    EXACT_MATCH = "Exact Match"
    SUGGESTED_MATCH = "Suggested Match"
    MISMATCH = "Mismatch"
    MANUAL_MATCH = "Manual Match"
    ONLY_IN_2A_2B = "Only in 2A/2B"
    ONLY_IN_BOOKS = "Only in Books"


# Each field extractor returns the (purchase-side, gst-side) values.
_FieldExtractor = Callable[[PurchaseRecord, GSTRecord], tuple[object, object]]


def _fy(record) -> str | None:
    if getattr(record, "fiscal_year", None):
        return str(record.fiscal_year)
    if getattr(record, "filing_period", None):
        return str(record.filing_period)[:4]
    return None


def _fiscal_year(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (_fy(p), _fy(g))


def _supplier_gstin(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.tax_identity, g.tax_identity)


def _company_gstin(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.company_gstin, g.company_gstin)


def _bill_no(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.reference, g.reference)


def _place_of_supply(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.place_of_supply, g.place_of_supply)


def _reverse_charge(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.is_reverse_charge, g.is_reverse_charge)


def _taxable_value(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.taxable_value if p.taxable_value is not None else p.amount,
            g.taxable_value if g.taxable_value is not None else g.amount)


def _cgst(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.cgst, g.cgst)


def _sgst(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.sgst, g.sgst)


def _igst(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.igst, g.igst)


def _cess(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    return (p.cess, g.cess)


def _total_gst(p: PurchaseRecord, g: GSTRecord) -> tuple[object, object]:
    # PAN-level comparison uses total GST in place of the CGST/SGST/IGST split.
    def total(cgst, sgst, igst):
        vals = [v for v in (cgst, sgst, igst) if isinstance(v, Decimal)]
        return sum(vals, Decimal("0")) if vals else None
    return (total(p.cgst, p.sgst, p.igst), total(g.cgst, g.sgst, g.igst))


FIELDS: dict[str, _FieldExtractor] = {
    "fiscal_year": _fiscal_year,
    "supplier_gstin": _supplier_gstin,
    "company_gstin": _company_gstin,
    "bill_no": _bill_no,
    "place_of_supply": _place_of_supply,
    "reverse_charge": _reverse_charge,
    "taxable_value": _taxable_value,
    "cgst": _cgst,
    "sgst": _sgst,
    "igst": _igst,
    "cess": _cess,
    "total_gst": _total_gst,
}


@dataclass(frozen=True)
class RuleRow:
    match_status: MatchStatus
    fields: dict[str, Rule]


# Ordered: first matching row wins. Mirrors India Compliance's GSTIN_RULES.
GSTIN_RULES: Sequence[RuleRow] = (
    RuleRow(MatchStatus.EXACT_MATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "company_gstin": Rule.EXACT_MATCH, "bill_no": Rule.EXACT_MATCH,
        "place_of_supply": Rule.EXACT_MATCH, "reverse_charge": Rule.EXACT_MATCH,
        "taxable_value": Rule.EXACT_MATCH, "cgst": Rule.EXACT_MATCH,
        "sgst": Rule.EXACT_MATCH, "igst": Rule.EXACT_MATCH, "cess": Rule.EXACT_MATCH,
    }),
    RuleRow(MatchStatus.SUGGESTED_MATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "company_gstin": Rule.EXACT_MATCH, "bill_no": Rule.FUZZY_MATCH,
        "place_of_supply": Rule.EXACT_MATCH, "reverse_charge": Rule.EXACT_MATCH,
        "taxable_value": Rule.EXACT_MATCH, "cgst": Rule.EXACT_MATCH,
        "sgst": Rule.EXACT_MATCH, "igst": Rule.EXACT_MATCH, "cess": Rule.EXACT_MATCH,
    }),
    RuleRow(MatchStatus.SUGGESTED_MATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "company_gstin": Rule.EXACT_MATCH, "bill_no": Rule.EXACT_MATCH,
        "place_of_supply": Rule.EXACT_MATCH, "reverse_charge": Rule.EXACT_MATCH,
        "taxable_value": Rule.ROUNDING_DIFFERENCE, "cgst": Rule.ROUNDING_DIFFERENCE,
        "sgst": Rule.ROUNDING_DIFFERENCE, "igst": Rule.ROUNDING_DIFFERENCE,
        "cess": Rule.ROUNDING_DIFFERENCE,
    }),
    RuleRow(MatchStatus.SUGGESTED_MATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "company_gstin": Rule.EXACT_MATCH, "bill_no": Rule.FUZZY_MATCH,
        "place_of_supply": Rule.EXACT_MATCH, "reverse_charge": Rule.EXACT_MATCH,
        "taxable_value": Rule.ROUNDING_DIFFERENCE, "cgst": Rule.ROUNDING_DIFFERENCE,
        "sgst": Rule.ROUNDING_DIFFERENCE, "igst": Rule.ROUNDING_DIFFERENCE,
        "cess": Rule.ROUNDING_DIFFERENCE,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "bill_no": Rule.EXACT_MATCH,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "bill_no": Rule.FUZZY_MATCH,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "supplier_gstin": Rule.EXACT_MATCH,
        "company_gstin": Rule.EXACT_MATCH, "place_of_supply": Rule.EXACT_MATCH,
        "reverse_charge": Rule.EXACT_MATCH, "taxable_value": Rule.ROUNDING_DIFFERENCE,
        "cgst": Rule.ROUNDING_DIFFERENCE, "sgst": Rule.ROUNDING_DIFFERENCE,
        "igst": Rule.ROUNDING_DIFFERENCE, "cess": Rule.ROUNDING_DIFFERENCE,
    }),
)

# PAN-level rules run on leftovers keyed by PAN, so supplier_gstin is omitted
# and total GST is compared instead of the CGST/SGST/IGST split.
PAN_RULES: Sequence[RuleRow] = (
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "company_gstin": Rule.EXACT_MATCH,
        "bill_no": Rule.EXACT_MATCH, "place_of_supply": Rule.EXACT_MATCH,
        "reverse_charge": Rule.EXACT_MATCH, "taxable_value": Rule.ROUNDING_DIFFERENCE,
        "total_gst": Rule.ROUNDING_DIFFERENCE, "cess": Rule.ROUNDING_DIFFERENCE,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "company_gstin": Rule.EXACT_MATCH,
        "bill_no": Rule.FUZZY_MATCH, "place_of_supply": Rule.EXACT_MATCH,
        "reverse_charge": Rule.EXACT_MATCH, "taxable_value": Rule.ROUNDING_DIFFERENCE,
        "total_gst": Rule.ROUNDING_DIFFERENCE, "cess": Rule.ROUNDING_DIFFERENCE,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "bill_no": Rule.FUZZY_MATCH,
    }),
    RuleRow(MatchStatus.MISMATCH, {
        "fiscal_year": Rule.EXACT_MATCH, "company_gstin": Rule.EXACT_MATCH,
        "place_of_supply": Rule.EXACT_MATCH, "reverse_charge": Rule.EXACT_MATCH,
        "taxable_value": Rule.ROUNDING_DIFFERENCE, "total_gst": Rule.ROUNDING_DIFFERENCE,
        "cess": Rule.ROUNDING_DIFFERENCE,
    }),
)


class FieldRuleMatcher:
    """Standalone pairwise field matcher implementing the ported rule tables."""

    #: Bill-number similarity threshold for FUZZY_MATCH (percent).
    FUZZY_THRESHOLD = 90

    def __init__(self, rules: Sequence[RuleRow] = GSTIN_RULES):
        self.rules = rules

    def match(self, purchase: PurchaseRecord, gst: GSTRecord) -> MatchStatus:
        for row in self.rules:
            if self._row_matches(row, purchase, gst):
                return row.match_status
        return MatchStatus.MISMATCH

    def _row_matches(self, row: RuleRow, purchase: PurchaseRecord, gst: GSTRecord) -> bool:
        for field_name, operator in row.fields.items():
            extractor = FIELDS.get(field_name)
            if extractor is None:
                continue
            left, right = extractor(purchase, gst)
            if not self._satisfies(left, right, operator):
                return False
        return True

    def _satisfies(self, left: object, right: object, operator: Rule) -> bool:
        if operator is Rule.EXACT_MATCH:
            # Both-absent is "equal" (e.g. neither document carries IGST).
            return _normalize(left) == _normalize(right)
        if operator is Rule.FUZZY_MATCH:
            return self._fuzzy(left, right)
        if operator is Rule.ROUNDING_DIFFERENCE:
            return self._rounding(left, right)
        return False

    @staticmethod
    def _fuzzy(left: object, right: object) -> bool:
        if not _values_present(left, right):
            return False
        return fuzz.ratio(str(left).upper(), str(right).upper()) >= FieldRuleMatcher.FUZZY_THRESHOLD

    @staticmethod
    def _rounding(left: object, right: object) -> bool:
        if left is None and right is None:
            return True
        if left is None or right is None:
            return False
        try:
            return abs(Decimal(str(left)) - Decimal(str(right))) <= Decimal("1")
        except Exception:
            return False

    @staticmethod
    def compare(purchase: PurchaseRecord, gst: GSTRecord, level: str = "gstin") -> MatchStatus:
        """Compare a single purchase record against a single GST record.

        ``level`` is one of ``"gstin"`` (default) or ``"pan"``.
        """
        rules = PAN_RULES if level == "pan" else GSTIN_RULES
        return FieldRuleMatcher(rules).match(purchase, gst)


def _values_present(left: object, right: object) -> bool:
    return left is not None and right is not None


def _normalize(value: object) -> object:
    if isinstance(value, str):
        return value.strip().upper()
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return value
    return value
