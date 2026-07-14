from typing import Iterable, Sequence, Callable, TypeVar
from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker, ExactAmountBlocker, TaxIdentityBlocker, ReferenceTokenBlocker
from recongraph.matching.scoring import SignalName
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, compute_reference_interpretation
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline
from recongraph.matching.signals import tax_identity_score, entity_score, temporal_score
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_MAX_DAYS

T = TypeVar('T')

def _weakest_available(
    purchases: Sequence[PurchaseRecord],
    gsts: Sequence[GSTRecord],
    extractor: Callable[[PurchaseRecord | GSTRecord], T],
    scorer: Callable[[T, T], float | None]
) -> float | None:
    scores = []
    for p in purchases:
        p_val = extractor(p)
        for g in gsts:
            g_val = extractor(g)
            s = scorer(p_val, g_val)
            if s is not None:
                scores.append(s)
                
    if not scores:
        return None
    return min(scores)

class FinancialEvidenceProvider:
    def __init__(self, tolerance: float = 0.05):
        self.pipeline = FinancialEvidencePipeline(tolerance=tolerance)
        
    def get_name(self) -> str:
        return SignalName.AMOUNT
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [ExactAmountBlocker()]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        from recongraph.domain.financial.amount_projection import project_amount_similarity
        
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        projection = project_amount_similarity(interpretation)
        
        violations = set(projection.warnings)
        if interpretation.currency_status == "MISMATCH":
            violations.add("CURRENCY_MISMATCH")
        elif projection.similarity < 0.5 and interpretation.relationship not in ("EXACT_MATCH", "ROUNDING_MATCH", "FEE_DETECTED"):
            violations.add("SEVERE_AMOUNT_CONFLICT")
            
        return EvidenceContribution(
            provider_name=self.get_name(),
            score=projection.similarity,
            violations=frozenset(violations),
            metadata={
                "interpretation": interpretation,
                "projection": projection
            }
        )

class TemporalEvidenceProvider:
    def __init__(self, max_days: int = PURCHASE_TO_GST_MAX_DAYS):
        self.max_days = max_days
        
    def get_name(self) -> str:
        return SignalName.TEMPORAL
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        score = _weakest_available(
            purchases,
            gsts,
            lambda r: r.record_date,
            lambda d1, d2: temporal_score(d1, d2, self.max_days)
        )
        
        if score == 0.0:
            return EvidenceContribution(
                provider_name=self.get_name(),
                score=0.0,
                violations=frozenset(["TEMPORAL_MAX_DAYS_EXCEEDED"])
            )
            
        return EvidenceContribution(
            provider_name=self.get_name(),
            score=score
        )

class TaxEvidenceProvider:
    def get_name(self) -> str:
        return SignalName.TAX_IDENTITY
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [TaxIdentityBlocker()]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        score = _weakest_available(
            purchases,
            gsts,
            lambda r: r.tax_identity,
            tax_identity_score
        )
        
        if score == 0.0:
            return EvidenceContribution(
                provider_name=self.get_name(),
                score=0.0,
                violations=frozenset(["TAX_IDENTITY_CONFLICT"])
            )
            
        return EvidenceContribution(
            provider_name=self.get_name(),
            score=score
        )

class VendorEvidenceProvider:
    def get_name(self) -> str:
        return SignalName.ENTITY
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        score = _weakest_available(
            purchases,
            gsts,
            lambda r: r.vendor_name,
            entity_score
        )
        
        return EvidenceContribution(
            provider_name=self.get_name(),
            score=score
        )

class ReferenceEvidenceProvider:
    def __init__(self, context: ReferenceEvidenceContext):
        self.context = context
        
    def get_name(self) -> str:
        return SignalName.REFERENCE
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [ReferenceTokenBlocker(self.context.profile)]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        p_refs = " ".join(p.reference for p in purchases if p.reference)
        g_refs = " ".join(g.reference for g in gsts if g.reference)
        
        if p_refs and g_refs:
            ref_interpretation = compute_reference_interpretation(p_refs, g_refs, self.context)
            return EvidenceContribution(
                provider_name=self.get_name(),
                score=ref_interpretation.score,
                metadata={"reference_interpretation": ref_interpretation}
            )
        return EvidenceContribution(provider_name=self.get_name(), score=None)
