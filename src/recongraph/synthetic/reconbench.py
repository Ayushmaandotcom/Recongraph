import random
from decimal import Decimal
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.decision import DecisionAction
from recongraph.synthetic.models import ScenarioSpecification, ExpectedOutcome, Difficulty
from recongraph.graph.candidate import build_purchase_urn, build_gst_urn
from recongraph.synthetic.operators import AmountMutationOperator, VendorMutationOperator, ReferenceMutationOperator

def generate_reconbench_dataset(size: int, seed: int = 42) -> list[ScenarioSpecification]:
    """Generates a reproducible, diverse dataset for benchmarking ReconGraph."""
    rng = random.Random(seed)
    scenarios = []

    for i in range(size):
        base_amt = Decimal(str(round(rng.uniform(10.0, 10000.0), 2)))
        base_date = date(2023, rng.randint(1, 12), rng.randint(1, 28))
        base_ref = f"INV-{rng.randint(1000, 99999)}-{i}"
        base_vendor = f"Vendor Corp {rng.randint(1, 100)}"
        base_tax = f"TAX{rng.randint(100000, 999999)}"
        
        p = PurchaseRecord(record_id=f"p_bench_{i}", amount=base_amt, record_date=base_date, reference=base_ref, vendor_name=base_vendor, tax_identity=base_tax)
        g = GSTRecord(record_id=f"g_bench_{i}", amount=base_amt, record_date=base_date, reference=base_ref, vendor_name=base_vendor, tax_identity=base_tax)
        
        p_urn = build_purchase_urn(p.record_id)
        g_urn = build_gst_urn(g.record_id)
        
        # Decide scenario type
        scenario_type = rng.choices(
            ["EXACT", "OCR_NOISE", "TAX_CONFLICT", "AMOUNT_DISCREPANCY", "ALIAS"],
            weights=[0.4, 0.2, 0.1, 0.1, 0.2],
            k=1
        )[0]
        
        from typing import Any
        gst_mutations: list[tuple[int, Any]] = []
        expected_decision = DecisionAction.AUTO_MATCH
        
        if scenario_type == "OCR_NOISE":
            # Hyphen missing or 0->O
            noisy_ref = base_ref.replace("-", "") if rng.random() > 0.5 else base_ref.replace("0", "O")
            gst_mutations.append((0, ReferenceMutationOperator(noisy_ref)))
        elif scenario_type == "TAX_CONFLICT":
            gst_mutations.append((0, VendorMutationOperator("Completely Unrelated Inc")))
            expected_decision = DecisionAction.REVIEW_WEAK
        elif scenario_type == "AMOUNT_DISCREPANCY":
            mutated_amt = base_amt - Decimal("1.0")
            gst_mutations.append((0, AmountMutationOperator(mutated_amt)))
            expected_decision = DecisionAction.REVIEW_WEAK
        elif scenario_type == "ALIAS":
            gst_mutations.append((0, VendorMutationOperator(f"{base_vendor} Pvt Ltd")))
            
        scenarios.append(ScenarioSpecification(
            scenario_id=f"BENCH-{i:05d}",
            difficulty=Difficulty.MEDIUM,
            base_purchases=(p,),
            base_gsts=(g,),
            purchase_mutations=(),
            gst_mutations=tuple(gst_mutations),
            expected_outcome=ExpectedOutcome(
                expected_decision=expected_decision,
                expected_component_urns=frozenset({p_urn, g_urn}),
                expected_hypothesis_edges=frozenset({frozenset({p_urn, g_urn})})
            )
        ))
        
    return scenarios
