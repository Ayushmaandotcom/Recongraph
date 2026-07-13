import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.matching.pair_scorers import score_purchase_to_gst


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PURCHASES_PATH = (
    PROJECT_ROOT / "datasets" / "raw" / "purchase_register.csv"
)

GST_RECORDS_PATH = (
    PROJECT_ROOT / "datasets" / "raw" / "gst_records.csv"
)

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "datasets"
    / "ground_truth"
    / "purchase_gst_matches.csv"
)


@dataclass(frozen=True)
class IdentifiedPurchase:
    record_id: str
    record: PurchaseRecord


@dataclass(frozen=True)
class IdentifiedGSTRecord:
    record_id: str
    record: GSTRecord


@dataclass(frozen=True)
class EvaluationRow:
    purchase_record_id: str
    gst_record_id: str
    relationship: str
    score: float | None
    coverage: float


def optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def load_purchases(path: Path) -> list[IdentifiedPurchase]:
    purchases: list[IdentifiedPurchase] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            purchases.append(
                IdentifiedPurchase(
                    record_id=row["record_id"],
                    record=PurchaseRecord(
                        vendor_name=optional_text(row["vendor_name"]),
                        reference=optional_text(row["invoice_number"]),
                        amount=float(row["amount"]),
                        record_date=date.fromisoformat(row["invoice_date"]),
                        tax_identity=optional_text(row["gstin"]),
                    ),
                )
            )

    return purchases


def load_gst_records(path: Path) -> list[IdentifiedGSTRecord]:
    gst_records: list[IdentifiedGSTRecord] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            gst_records.append(
                IdentifiedGSTRecord(
                    record_id=row["record_id"],
                    record=GSTRecord(
                        vendor_name=optional_text(row["supplier_name"]),
                        reference=optional_text(row["invoice_number"]),
                        amount=float(row["amount"]),
                        record_date=date.fromisoformat(row["invoice_date"]),
                        tax_identity=optional_text(row["gstin"]),
                    ),
                )
            )

    return gst_records


def load_positive_pairs(path: Path) -> set[tuple[str, str]]:
    positive_pairs: set[tuple[str, str]] = set()

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["relationship"] == "same_financial_event":
                positive_pairs.add(
                    (
                        row["purchase_record_id"],
                        row["gst_record_id"],
                    )
                )

    return positive_pairs


def evaluate_pairs(
    purchases: list[IdentifiedPurchase],
    gst_records: list[IdentifiedGSTRecord],
    positive_pairs: set[tuple[str, str]],
) -> list[EvaluationRow]:
    rows: list[EvaluationRow] = []

    for purchase in purchases:
        for gst_record in gst_records:
            result = score_purchase_to_gst(
                purchase=purchase.record,
                gst_record=gst_record.record,
            )

            pair = (
                purchase.record_id,
                gst_record.record_id,
            )

            relationship = (
                "positive"
                if pair in positive_pairs
                else "negative"
            )

            rows.append(
                EvaluationRow(
                    purchase_record_id=purchase.record_id,
                    gst_record_id=gst_record.record_id,
                    relationship=relationship,
                    score=result.relationship.score,
                    coverage=result.relationship.coverage,
                )
            )

    return rows


def sortable_score(row: EvaluationRow) -> float:
    if row.score is None:
        return -1.0

    return row.score


def print_score_table(rows: list[EvaluationRow]) -> None:
    print(
        f"{'Purchase':<10} "
        f"{'GST':<10} "
        f"{'Label':<10} "
        f"{'Score':>10} "
        f"{'Coverage':>10}"
    )

    print("-" * 56)

    for row in rows:
        score_text = (
            "None"
            if row.score is None
            else f"{row.score:.4f}"
        )

        print(
            f"{row.purchase_record_id:<10} "
            f"{row.gst_record_id:<10} "
            f"{row.relationship:<10} "
            f"{score_text:>10} "
            f"{row.coverage:>10.4f}"
        )


def calculate_separation(
    rows: list[EvaluationRow],
) -> tuple[float, float, float]:
    positive_scores = [
        row.score
        for row in rows
        if row.relationship == "positive"
        and row.score is not None
    ]

    negative_scores = [
        row.score
        for row in rows
        if row.relationship == "negative"
        and row.score is not None
    ]

    if not positive_scores or not negative_scores:
        raise ValueError(
            "Evaluation requires scored positive and negative pairs."
        )

    minimum_positive = min(positive_scores)
    maximum_negative = max(negative_scores)
    separation_gap = minimum_positive - maximum_negative

    return (
        minimum_positive,
        maximum_negative,
        separation_gap,
    )


def print_separation_summary(
    minimum_positive: float,
    maximum_negative: float,
    separation_gap: float,
) -> None:
    print()
    print("Separation summary")
    print("------------------")
    print(f"Minimum positive score: {minimum_positive:.4f}")
    print(f"Maximum negative score: {maximum_negative:.4f}")
    print(f"Separation gap: {separation_gap:.4f}")


def main() -> None:
    purchases = load_purchases(PURCHASES_PATH)
    gst_records = load_gst_records(GST_RECORDS_PATH)
    positive_pairs = load_positive_pairs(GROUND_TRUTH_PATH)

    rows = evaluate_pairs(
        purchases=purchases,
        gst_records=gst_records,
        positive_pairs=positive_pairs,
    )

    rows.sort(
        key=sortable_score,
        reverse=True,
    )

    print(f"Purchases loaded: {len(purchases)}")
    print(f"GST records loaded: {len(gst_records)}")
    print(f"Candidate pairs scored: {len(rows)}")
    print()

    print_score_table(rows)

    (
        minimum_positive,
        maximum_negative,
        separation_gap,
    ) = calculate_separation(rows)

    print_separation_summary(
        minimum_positive=minimum_positive,
        maximum_negative=maximum_negative,
        separation_gap=separation_gap,
    )


if __name__ == "__main__":
    main()
