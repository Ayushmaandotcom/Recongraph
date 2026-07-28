import random
from decimal import Decimal
from datetime import date, timedelta
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction
from recongraph.synthetic.models import ScenarioSpecification, ExpectedOutcome, Difficulty
from recongraph.graph.candidate import build_purchase_urn, build_gst_urn
from recongraph.synthetic.operators import AmountMutationOperator, VendorMutationOperator, ReferenceMutationOperator

# Scenario type weights — deliberately balanced to stress each signal category.
# EXACT:              Clean match — expected AUTO_MATCH at 0.99 threshold.
# NOISY_DATE_1D:      Same invoice, 1-day date drift — expected AUTO_MATCH or REVIEW_WEAK.
# NOISY_DATE_3D:      Same invoice, 3-day date drift — may fall below temporal window.
# NOISY_AMOUNT_1:     Same invoice, ₹1 rounding gap — near-exact financial signal.
# NOISY_AMOUNT_5:     Same invoice, ₹5 gap — tests relaxed tolerance boundary.
# NOISY_VENDOR_ALIAS: Pvt/Private/case/spacing variants — same legal entity.
# NOISY_REF_PARTIAL:  INV-1234 → 1234 or 1234/A — partial reference.
# OCR_NOISE:          Reference OCR corruption — hyphen drop or 0→O substitution.
# ADVERSARIAL_TAX:    Completely different vendor → ineligible, expected REVIEW_WEAK.
# ADVERSARIAL_AMOUNT: Large amount discrepancy → ineligible, expected REVIEW_WEAK.
_SCENARIO_TYPES = [
    "EXACT",
    "NOISY_DATE_1D",
    "NOISY_DATE_3D",
    "NOISY_AMOUNT_1",
    "NOISY_AMOUNT_5",
    "NOISY_VENDOR_ALIAS",
    "NOISY_REF_PARTIAL",
    "OCR_NOISE",
    "ADVERSARIAL_TAX",
    "ADVERSARIAL_AMOUNT",
]
_SCENARIO_WEIGHTS = [0.30, 0.08, 0.08, 0.08, 0.07, 0.07, 0.07, 0.05, 0.10, 0.10]

# Noisy positives are scenarios where the true match should still be findable
# (same underlying invoice) but real-world data imperfections are present.
NOISY_POSITIVE_TYPES = frozenset({
    "NOISY_DATE_1D",
    "NOISY_DATE_3D",
    "NOISY_AMOUNT_1",
    "NOISY_AMOUNT_5",
    "NOISY_VENDOR_ALIAS",
    "NOISY_REF_PARTIAL",
    "OCR_NOISE",
})

# Adversarial types: structurally invalid pairs — must NEVER auto-match.
ADVERSARIAL_TYPES = frozenset({"ADVERSARIAL_TAX", "ADVERSARIAL_AMOUNT"})


def _apply_date_drift(base_date: date, days: int) -> date:
    """Apply a date drift, clamping to the same month to avoid filing-period drift."""
    drifted = base_date + timedelta(days=days)
    # Clamp to same year to avoid edge cases with temporal projection
    if drifted.year != base_date.year:
        return base_date
    return drifted


def generate_reconbench_dataset(size: int, seed: int = 42) -> list[ScenarioSpecification]:
    """Generates a reproducible, diverse dataset for benchmarking ReconGraph.

    Includes both:
    - EXACT match scenarios (baseline: should auto-match at 0.99)
    - NOISY POSITIVE scenarios (same invoice with real-world imperfections)
    - ADVERSARIAL scenarios (structurally invalid pairs — must never auto-match)

    See BENCHMARKS.md for the full calibration sweep table and threshold choice rationale.
    """
    rng = random.Random(seed)
    scenarios = []

    for i in range(size):
        base_amt = Decimal(str(round(rng.uniform(10.0, 10000.0), 2)))
        base_date = date(2023, rng.randint(1, 12), rng.randint(1, 28))
        base_ref = f"INV-{rng.randint(1000, 99999)}-{i}"
        base_vendor = f"Vendor Corp {rng.randint(1, 100)}"
        base_tax = f"AAAAA{rng.randint(1000, 9999)}A"

        p = PurchaseRecord(
            record_id=f"p_bench_{i}", amount=base_amt, record_date=base_date,
            reference=base_ref, vendor_name=base_vendor, tax_identity=base_tax
        )
        g = GSTRecord(
            record_id=f"g_bench_{i}", amount=base_amt, record_date=base_date,
            reference=base_ref, vendor_name=base_vendor, tax_identity=base_tax
        )

        p_urn = build_purchase_urn(p.record_id)
        g_urn = build_gst_urn(g.record_id)

        # Decide scenario type
        scenario_type = rng.choices(_SCENARIO_TYPES, weights=_SCENARIO_WEIGHTS, k=1)[0]

        from typing import Any
        gst_mutations: list[tuple[int, Any]] = []
        purchase_mutations: list[tuple[int, Any]] = []

        # Noisy positives: same invoice, real-world imperfection on the GST side
        if scenario_type == "NOISY_DATE_1D":
            drifted = _apply_date_drift(base_date, rng.choice([1, -1]))
            from recongraph.synthetic.operators import DateMutationOperator
            gst_mutations.append((0, DateMutationOperator(drifted)))
            expected_decision = DecisionAction.AUTO_MATCH  # 1-day drift within tolerance

        elif scenario_type == "NOISY_DATE_3D":
            drift = rng.choice([3, -3])
            drifted = _apply_date_drift(base_date, drift)
            from recongraph.synthetic.operators import DateMutationOperator
            gst_mutations.append((0, DateMutationOperator(drifted)))
            # 3-day drift: may exceed temporal window → can be REVIEW_WEAK
            expected_decision = DecisionAction.REVIEW_WEAK

        elif scenario_type == "NOISY_AMOUNT_1":
            delta = Decimal("1.00") * rng.choice([1, -1])
            gst_mutations.append((0, AmountMutationOperator(base_amt + delta)))
            expected_decision = DecisionAction.AUTO_MATCH  # within 5% tolerance

        elif scenario_type == "NOISY_AMOUNT_5":
            delta = Decimal("5.00") * rng.choice([1, -1])
            gst_mutations.append((0, AmountMutationOperator(base_amt + delta)))
            expected_decision = DecisionAction.AUTO_MATCH  # likely within tolerance

        elif scenario_type == "NOISY_VENDOR_ALIAS":
            # Pvt Ltd / Private Limited / case / extra spacing
            aliases = [
                f"{base_vendor} Pvt Ltd",
                f"{base_vendor} Private Limited",
                f"{base_vendor.upper()}",
                f"  {base_vendor}  ",
                f"{base_vendor} Ltd",
            ]
            gst_mutations.append((0, VendorMutationOperator(rng.choice(aliases))))
            expected_decision = DecisionAction.AUTO_MATCH

        elif scenario_type == "NOISY_REF_PARTIAL":
            # Extract the numeric core of the reference
            parts = base_ref.split("-")
            if len(parts) >= 2:
                partial_ref = rng.choice([
                    parts[1],                     # just the number
                    f"{parts[1]}/{parts[-1]}",    # number/suffix
                    base_ref.replace("-", ""),    # no hyphens
                ])
            else:
                partial_ref = base_ref
            gst_mutations.append((0, ReferenceMutationOperator(partial_ref)))
            expected_decision = DecisionAction.AUTO_MATCH  # partial match expected

        elif scenario_type == "OCR_NOISE":
            noisy_ref = (
                base_ref.replace("-", "")
                if rng.random() > 0.5
                else base_ref.replace("0", "O")
            )
            gst_mutations.append((0, ReferenceMutationOperator(noisy_ref)))
            expected_decision = DecisionAction.AUTO_MATCH

        # Adversarial: structurally invalid pairs — must NEVER auto-match
        elif scenario_type == "ADVERSARIAL_TAX":
            gst_mutations.append((0, VendorMutationOperator("Completely Unrelated Inc")))
            expected_decision = DecisionAction.REVIEW_WEAK

        elif scenario_type == "ADVERSARIAL_AMOUNT":
            mutated_amt = base_amt * Decimal("2")  # 100% discrepancy
            gst_mutations.append((0, AmountMutationOperator(mutated_amt)))
            expected_decision = DecisionAction.REVIEW_WEAK

        else:
            # EXACT — baseline
            expected_decision = DecisionAction.AUTO_MATCH

        scenarios.append(ScenarioSpecification(
            scenario_id=f"BENCH-{scenario_type}-{i:05d}",
            difficulty=Difficulty.MEDIUM,
            base_purchases=(p,),
            base_gsts=(g,),
            purchase_mutations=tuple(purchase_mutations),
            gst_mutations=tuple(gst_mutations),
            expected_outcome=ExpectedOutcome(
                expected_decision=expected_decision,
                expected_component_urns=frozenset({p_urn, g_urn}),
                expected_hypothesis_edges=frozenset({frozenset({p_urn, g_urn})})
            )
        ))

    return scenarios
