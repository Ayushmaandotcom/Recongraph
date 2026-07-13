from dataclasses import dataclass
from typing import Sequence
import math

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.provider_v2 import EvidencePipeline, EvidenceContributionV2

@dataclass(frozen=True)
class FinancialObservation:
    purchase_gross: tuple[float, ...]
    purchase_net: tuple[float | None, ...]
    purchase_tax: tuple[float | None, ...]
    purchase_currencies: tuple[str, ...]
    purchase_signs: tuple[int, ...]
    
    gst_gross: tuple[float, ...]
    gst_net: tuple[float | None, ...]
    gst_tax: tuple[float | None, ...]
    gst_currencies: tuple[str, ...]
    gst_signs: tuple[int, ...]
    
    @property
    def total_purchase_gross(self) -> float:
        return sum(self.purchase_gross)
        
    @property
    def total_gst_gross(self) -> float:
        return sum(self.gst_gross)
        
    @property
    def total_purchase_net(self) -> float:
        return sum(n for n in self.purchase_net if n is not None)
        
    @property
    def total_gst_tax(self) -> float:
        return sum(t for t in self.gst_tax if t is not None)

@dataclass(frozen=True)
class EvaluatedFinancialEvidence:
    sum_purchases: float
    sum_payments: float
    currency: str
    amount_score: float
    is_exact_match: bool
    is_partial: bool
    is_overpayment: bool
    residual: float
    currency_mismatch: bool
    notes: list[str]

class FinancialEvidencePipeline(EvidencePipeline[FinancialObservation, EvaluatedFinancialEvidence]):
    def __init__(self, tolerance: float = 0.05, fee_tolerance: float = 2.00):
        self.tolerance = tolerance
        self.fee_tolerance = fee_tolerance

    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> FinancialObservation:
        return FinancialObservation(
            purchase_gross=tuple(p.amount for p in purchases),
            purchase_net=tuple(p.net_amount for p in purchases),
            purchase_tax=tuple(p.tax_amount for p in purchases),
            purchase_currencies=tuple(p.currency for p in purchases),
            purchase_signs=tuple(p.sign for p in purchases),
            
            gst_gross=tuple(g.amount for g in gsts),
            gst_net=tuple(g.net_amount for g in gsts),
            gst_tax=tuple(g.tax_amount for g in gsts),
            gst_currencies=tuple(g.currency for g in gsts),
            gst_signs=tuple(g.sign for g in gsts)
        )
        
    def interpret(self, observation: FinancialObservation) -> EvaluatedFinancialEvidence:
        tp = observation.total_purchase_gross
        tg = observation.total_gst_gross
        delta = abs(tp - tg)
        residual = tp - tg # Positive means underpayment (invoice > payment)
        
        all_currencies = set(observation.purchase_currencies) | set(observation.gst_currencies)
        currency_mismatch = len(all_currencies) > 1
        primary_currency = next(iter(all_currencies)) if all_currencies else "USD"
        
        num_p = len(observation.purchase_gross)
        num_g = len(observation.gst_gross)
        is_split = (num_p > 1 or num_g > 1)
        
        notes = []
        is_exact = False
        is_partial = False
        is_over = False
        score = 0.0
        
        if currency_mismatch:
            notes.append("CURRENCY_MISMATCH")
            score = 0.0
        else:
            if delta <= 1e-9:
                is_exact = True
                score = 1.0
                if is_split:
                    notes.append("SPLIT_PAYMENT")
                else:
                    notes.append("EXACT_TOTAL_MATCH")
            elif delta <= self.tolerance:
                is_exact = True
                score = 0.99
                notes.append("ROUNDING_MATCH")
            elif delta <= self.fee_tolerance and residual > 0:
                # Small underpayment modeled as a fee
                is_exact = True
                score = 0.95
                notes.append("FEE_DETECTED")
            else:
                if residual > 0:
                    is_partial = True
                    notes.append("UNDERPAYMENT")
                else:
                    is_over = True
                    notes.append("OVERPAYMENT")
                
                max_val = max(tp, tg, 1.0)
                score = max(0.0, 1.0 - (delta / max_val))
                
                # Rough net/gross heuristic checking if Gross ≈ Payment + Tax
                # The user noted: If (GrossInvoice == Sum(Payments) + Sum(Tax)) -> NET_TO_GROSS_MATCH
                if observation.total_gst_tax > 0:
                    if abs(tp - (tg + observation.total_gst_tax)) <= self.tolerance:
                        notes.append("GROSS_NET_MATCH")
                        
        return EvaluatedFinancialEvidence(
            sum_purchases=tp,
            sum_payments=tg,
            currency=primary_currency,
            amount_score=score,
            is_exact_match=is_exact,
            is_partial=is_partial,
            is_overpayment=is_over,
            residual=residual,
            currency_mismatch=currency_mismatch,
            notes=notes
        )
        
    def contribute(self, interpretation: EvaluatedFinancialEvidence) -> EvidenceContributionV2[EvaluatedFinancialEvidence]:
        violations = set()
        
        if interpretation.currency_mismatch:
            violations.add("CURRENCY_MISMATCH")
        elif not interpretation.is_exact_match and interpretation.amount_score < 0.5:
            violations.add("SEVERE_AMOUNT_CONFLICT")
            
        return EvidenceContributionV2(
            provider_name="FinancialEvidenceProvider",
            score=interpretation.amount_score,
            violations=frozenset(violations),
            interpretation=interpretation
        )
