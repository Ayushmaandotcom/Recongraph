from typing import Iterable, Sequence
from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker, ExactAmountBlocker, TaxIdentityBlocker, ReferenceTokenBlocker
from recongraph.matching.scoring import SignalName
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, compute_reference_interpretation
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline

class FinancialEvidenceProvider:
    def __init__(self, tolerance: float = 0.05):
        self.pipeline = FinancialEvidencePipeline(tolerance=tolerance)
        
    def get_name(self) -> str:
        return SignalName.AMOUNT
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [ExactAmountBlocker()]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)
        
        return EvidenceContribution(
            provider_name=self.get_name(),
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata={"interpretation": contrib_v2.interpretation}
        )

class TemporalEvidenceProvider:
    def __init__(self, max_days: int = 14):
        self.max_days = max_days
        
    def get_name(self) -> str:
        return SignalName.TEMPORAL
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        max_day_diff = max(
            abs((p.record_date - g.record_date).days) 
            for p in purchases for g in gsts
        )
        
        if max_day_diff > self.max_days:
            return EvidenceContribution(
                provider_name=self.get_name(),
                score=0.0,
                violations=frozenset(["TEMPORAL_MAX_DAYS_EXCEEDED"])
            )
            
        score = 1.0 - (max_day_diff / self.max_days)
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
        tax_ids_p = {p.tax_identity for p in purchases if p.tax_identity}
        tax_ids_g = {g.tax_identity for g in gsts if g.tax_identity}
        
        tax_id_p_val = next(iter(tax_ids_p)) if len(tax_ids_p) == 1 else None
        tax_id_g_val = next(iter(tax_ids_g)) if len(tax_ids_g) == 1 else None
        
        if tax_id_p_val and tax_id_g_val:
            if tax_id_p_val == tax_id_g_val:
                return EvidenceContribution(provider_name=self.get_name(), score=1.0)
            else:
                return EvidenceContribution(provider_name=self.get_name(), score=0.0, violations=frozenset(["TAX_IDENTITY_CONFLICT"]))
        return EvidenceContribution(provider_name=self.get_name(), score=None)

class VendorEvidenceProvider:
    def get_name(self) -> str:
        return SignalName.ENTITY
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        p_vendors = " ".join(p.vendor_name for p in purchases if p.vendor_name)
        g_vendors = " ".join(g.vendor_name for g in gsts if g.vendor_name)
        
        if p_vendors and g_vendors:
            score = 1.0 if p_vendors.lower() == g_vendors.lower() else 0.5 # Very basic fuzzy mock for now
            return EvidenceContribution(provider_name=self.get_name(), score=score)
        return EvidenceContribution(provider_name=self.get_name(), score=None)

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
