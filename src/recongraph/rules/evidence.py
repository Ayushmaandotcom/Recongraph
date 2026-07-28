from typing import Sequence, Any, Mapping
from recongraph.plugins.provider import EvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.rules.models import RuleSet
from recongraph.rules.evaluator import RuleEvaluator
from recongraph.plugins.provider_v2 import EvidenceContributionV2

class RuleEvidenceProvider(EvidenceProvider):
    """
    Evidence Provider that evaluates business rules and emits 
    rule violations as evidence contributions.
    """
    
    def __init__(self, rule_sets: Mapping[str, RuleSet], tenant_id: str = "default"):
        self.rule_sets = rule_sets
        self.name = "rule_engine"
        self.tenant_id = tenant_id
        
    def get_name(self) -> str:
        return self.name
        
    def get_blockers(self) -> Sequence[Any]:
        return []
        
    def score_pair(self, purchase: PurchaseRecord, gst: GSTRecord) -> float:
        return 0.0

    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContributionV2[Any]:
        if self.tenant_id not in self.rule_sets:
            return EvidenceContributionV2(provider_name=self.name, score=1.0, metadata={})
            
        # Build context from records
        vendor_name_conflict = False
        for p in purchases:
            for g in gsts:
                if p.vendor_name != g.vendor_name:
                    vendor_name_conflict = True
                    break
                    
        context = {
            "amount_difference": 0.0,
            "vendor_name_conflict": vendor_name_conflict
        } 
        
        evaluator = RuleEvaluator(self.rule_sets[self.tenant_id])
        violations = evaluator.evaluate(context)
        
        # If there are BLOCK violations, we can score 0.0 or emit metadata
        has_blocks = any(v.severity == "BLOCK" for v in violations)
        score = 0.0 if has_blocks else 1.0
        
        metadata = {"violations": [v.rule_id for v in violations]}
        
        return EvidenceContributionV2(provider_name=self.name, score=score, metadata=metadata)

