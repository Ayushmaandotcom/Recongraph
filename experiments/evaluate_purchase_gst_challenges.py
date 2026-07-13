import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.matching.pair_scorers import score_purchase_to_gst
from recongraph.matching.scoring import SignalName


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHALLENGE_DIR = PROJECT_ROOT / "datasets" / "challenge"

PURCHASES_PATH = CHALLENGE_DIR / "purchase_register_v1.csv"
GST_RECORDS_PATH = CHALLENGE_DIR / "gst_records_v1.csv"
PAIR_LABELS_PATH = CHALLENGE_DIR / "pair_labels_v1.csv"
CASES_PATH = CHALLENGE_DIR / "challenge_cases_v1.csv"

# Diagnostic threshold for challenge inspection only.
# This is not a calibrated production decision threshold.
CHALLENGE_CONCERN_SCORE = 0.60


@dataclass(frozen=True)
class ChallengePair:
    case_id: str
    purchase_record_id: str
    gst_record_id: str
    expected_label: str


@dataclass(frozen=True)
class ChallengeResult:
    case_id: str
    purchase_record_id: str
    gst_record_id: str
    expected_label: str
    score: float | None
    coverage: float
    entity_score: float | None
    reference_score: float | None
    amount_score: float | None
    temporal_score: float | None
    tax_identity_score: float | None
    semantic_findings: tuple[str, ...]


def optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def load_purchases(path: Path) -> dict[str, PurchaseRecord]:
    purchases: dict[str, PurchaseRecord] = {}

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            purchases[row["record_id"]] = PurchaseRecord(
                vendor_name=optional_text(row["vendor_name"]),
                reference=optional_text(row["invoice_number"]),
                amount=float(row["amount"]),
                record_date=date.fromisoformat(row["invoice_date"]),
                tax_identity=optional_text(row["gstin"]),
            )

    return purchases


def load_gst_records(path: Path) -> dict[str, GSTRecord]:
    gst_records: dict[str, GSTRecord] = {}

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            gst_records[row["record_id"]] = GSTRecord(
                vendor_name=optional_text(row["supplier_name"]),
                reference=optional_text(row["invoice_number"]),
                amount=float(row["amount"]),
                record_date=date.fromisoformat(row["invoice_date"]),
                tax_identity=optional_text(row["gstin"]),
            )

    return gst_records


def load_challenge_pairs(path: Path) -> list[ChallengePair]:
    pairs: list[ChallengePair] = []

    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            pairs.append(
                ChallengePair(
                    case_id=row["case_id"],
                    purchase_record_id=row["purchase_record_id"],
                    gst_record_id=row["gst_record_id"],
                    expected_label=row["expected_label"],
                )
            )

    return pairs


def evaluate_challenges(
    purchases: dict[str, PurchaseRecord],
    gst_records: dict[str, GSTRecord],
    challenge_pairs: list[ChallengePair],
) -> list[ChallengeResult]:
    results: list[ChallengeResult] = []

    for challenge_pair in challenge_pairs:
        purchase = purchases[challenge_pair.purchase_record_id]
        gst_record = gst_records[challenge_pair.gst_record_id]

        pair_result = score_purchase_to_gst(
            purchase=purchase,
            gst_record=gst_record,
        )

        signals = pair_result.signals

        findings = tuple(finding.value for finding in pair_result.semantic_findings)

        results.append(
            ChallengeResult(
                case_id=challenge_pair.case_id,
                purchase_record_id=challenge_pair.purchase_record_id,
                gst_record_id=challenge_pair.gst_record_id,
                expected_label=challenge_pair.expected_label,
                score=pair_result.relationship.score,
                coverage=pair_result.relationship.coverage,
                entity_score=signals[SignalName.ENTITY],
                reference_score=signals[SignalName.REFERENCE],
                amount_score=signals[SignalName.AMOUNT],
                temporal_score=signals[SignalName.TEMPORAL],
                tax_identity_score=signals[SignalName.TAX_IDENTITY],
                semantic_findings=findings,
            )
        )

    return results


def format_score(score: float | None) -> str:
    if score is None:
        return "None"

    return f"{score:.4f}"


def format_findings(findings: tuple[str, ...]) -> str:
    if not findings:
        return "-"
    return ",".join(findings)


def print_score_table(results: list[ChallengeResult]) -> None:
    print(
        f"{'Case':<7} "
        f"{'Pair':<14} "
        f"{'Label':<17} "
        f"{'Score':>7}  "
        f"{'Entity':>7}  "
        f"{'Ref':>7}  "
        f"{'Amount':>7}  "
        f"{'Time':>7}  "
        f"{'Tax':>7}  "
        f"{'Findings'}"
    )
    print("-" * 115)

    for r in results:
        pair_str = f"{r.purchase_record_id}-{r.gst_record_id}"
        print(
            f"{r.case_id:<7} "
            f"{pair_str:<14} "
            f"{r.expected_label:<17} "
            f"{format_score(r.score):>7}  "
            f"{format_score(r.entity_score):>7}  "
            f"{format_score(r.reference_score):>7}  "
            f"{format_score(r.amount_score):>7}  "
            f"{format_score(r.temporal_score):>7}  "
            f"{format_score(r.tax_identity_score):>7}  "
            f"{format_findings(r.semantic_findings)}"
        )


def print_baseline_concerns(results: list[ChallengeResult]) -> None:
    print("\nBaseline concerns")
    print("-" * 17)
    
    for r in results:
        pair_str = f"{r.purchase_record_id}-{r.gst_record_id}"
        
        if r.expected_label == "group_component":
            print(f"{r.case_id} requires group-level evaluation; pair score shown diagnostically.")
            continue
            
        if r.expected_label == "negative" and r.score is not None and r.score >= CHALLENGE_CONCERN_SCORE:
            print(f"{r.case_id} {pair_str} score={r.score:.4f}")


def main() -> None:
    purchases = load_purchases(PURCHASES_PATH)
    gst_records = load_gst_records(GST_RECORDS_PATH)
    challenge_pairs = load_challenge_pairs(PAIR_LABELS_PATH)

    results = evaluate_challenges(
        purchases=purchases,
        gst_records=gst_records,
        challenge_pairs=challenge_pairs,
    )

    print_score_table(results)
    print_baseline_concerns(results)


if __name__ == "__main__":
    main()
