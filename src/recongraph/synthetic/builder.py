from typing import Sequence
from recongraph.synthetic.models import ScenarioSpecification, SyntheticDataset
from recongraph.domain.records import PurchaseRecord, GSTRecord

class DatasetBuilder:
    """Builds materialized datasets securely from declarative ScenarioSpecifications."""

    def build_from_specs(self, specs: Sequence[ScenarioSpecification], dataset_id: str) -> SyntheticDataset:
        purchases: list[PurchaseRecord] = []
        gsts: list[GSTRecord] = []
        outcomes = []
        
        for spec in specs:
            # Materialize purchases
            for i, p in enumerate(spec.base_purchases):
                mutated_p = p
                # Apply mutations mapped to this index
                for mut_idx, op in spec.purchase_mutations:
                    if mut_idx == i:
                        mutated_p = op.apply(mutated_p)
                purchases.append(mutated_p)
                
            # Materialize gsts
            for i, g in enumerate(spec.base_gsts):
                mutated_g = g
                for mut_idx, op in spec.gst_mutations:
                    if mut_idx == i:
                        mutated_g = op.apply(mutated_g)
                gsts.append(mutated_g)
                
            outcomes.append(spec.expected_outcome)
            
        return SyntheticDataset(
            dataset_id=dataset_id,
            purchases=tuple(purchases),
            gsts=tuple(gsts),
            expected_outcomes=tuple(outcomes)
        )
