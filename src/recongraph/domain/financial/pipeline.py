from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence
from enum import StrEnum

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.provider_v2 import EvidencePipeline, EvidenceContributionV2


class AmountRelationship(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    ROUNDING_MATCH = "ROUNDING_MATCH"
    FEE_DETECTED = "FEE_DETECTED"
    PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"
    OVERPAYMENT = "OVERPAYMENT"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    UNINTERPRETABLE = "UNINTERPRETABLE"


@dataclass(frozen=True)
class FinancialObservation:
    purchase_gross: tuple[Decimal, ...]
    purchase_net: tuple[Decimal | None, ...]
    purchase_tax: tuple[Decimal | None, ...]
    purchase_currencies: tuple[str, ...]
    purchase_signs: tuple[int, ...]
    
    gst_gross: tuple[Decimal, ...]
    gst_net: tuple[Decimal | None, ...]
    gst_tax: tuple[Decimal | None, ...]
    gst_currencies: tuple[str, ...]
    gst_signs: tuple[int, ...]
    
    @property
    def total_purchase_gross(self) -> Decimal:
        return sum(self.purchase_gross, Decimal("0"))
        
    @property
    def total_gst_gross(self) -> Decimal:
        return sum(self.gst_gross, Decimal("0"))
        
    @property
    def total_purchase_net(self) -> Decimal:
        return sum((n for n in self.purchase_net if n is not None), Decimal("0"))
        
    @property
    def total_gst_tax(self) -> Decimal:
        return sum((t for t in self.gst_tax if t is not None), Decimal("0"))


@dataclass(frozen=True)
class AmountInterpretation:
    """The authoritative semantic model of financial amount relationships."""
    relationship: AmountRelationship
    
    amount_a: Decimal
    amount_b: Decimal
    
    absolute_difference: Decimal
    relative_difference: Decimal
    residual: Decimal
    
    currency_status: str
    comparison_basis: str
    
    notes: tuple[str, ...] = field(default_factory=tuple)
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    provenance: str = "FinancialEvidencePipeline"


class FinancialEvidencePipeline(EvidencePipeline[FinancialObservation, AmountInterpretation]):
    def __init__(self, tolerance: Decimal = Decimal("0.05"), fee_tolerance: Decimal = Decimal("2.00")):
        self.tolerance = tolerance
        self.fee_tolerance = fee_tolerance

    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> FinancialObservation:
        return FinancialObservation(
            purchase_gross=tuple(Decimal(str(p.amount)) for p in purchases),
            purchase_net=tuple(Decimal(str(p.net_amount)) if p.net_amount is not None else None for p in purchases),
            purchase_tax=tuple(Decimal(str(p.tax_amount)) if p.tax_amount is not None else None for p in purchases),
            purchase_currencies=tuple(p.currency for p in purchases),
            purchase_signs=tuple(p.sign for p in purchases),
            
            gst_gross=tuple(Decimal(str(g.amount)) for g in gsts),
            gst_net=tuple(Decimal(str(g.net_amount)) if g.net_amount is not None else None for g in gsts),
            gst_tax=tuple(Decimal(str(g.tax_amount)) if g.tax_amount is not None else None for g in gsts),
            gst_currencies=tuple(g.currency for g in gsts),
            gst_signs=tuple(g.sign for g in gsts)
        )
        
    def interpret(self, observation: FinancialObservation) -> AmountInterpretation:
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
        assumptions = []
        relationship = AmountRelationship.UNINTERPRETABLE
        
        if currency_mismatch:
            relationship = AmountRelationship.CURRENCY_MISMATCH
            notes.append("Currency mismatch detected.")
        else:
            if delta <= Decimal("0"):
                relationship = AmountRelationship.EXACT_MATCH
                if is_split:
                    notes.append("Split payment perfectly matches.")
                else:
                    notes.append("Exact total match.")
            elif delta <= self.tolerance:
                relationship = AmountRelationship.ROUNDING_MATCH
                notes.append("Difference is within rounding tolerance.")
            elif delta <= self.fee_tolerance and residual > 0:
                relationship = AmountRelationship.FEE_DETECTED
                notes.append("Small underpayment modeled as a fee.")
                assumptions.append(f"Difference <= {self.fee_tolerance} is a bank fee.")
            else:
                if residual > 0:
                    relationship = AmountRelationship.PARTIAL_SETTLEMENT
                    notes.append("Underpayment detected.")
                else:
                    relationship = AmountRelationship.OVERPAYMENT
                    notes.append("Overpayment detected.")
                
                # Net to Gross check
                if observation.total_gst_tax > Decimal("0"):
                    if abs(tp - (tg + observation.total_gst_tax)) <= self.tolerance:
                        notes.append("Gross amount equals Net + Tax.")
                        assumptions.append("One record is Net and the other is Gross.")
                        
        max_val = max(abs(tp), abs(tg))
        if max_val == Decimal("0"):
            relative_difference = Decimal("0")
        else:
            relative_difference = delta / max_val
            
        return AmountInterpretation(
            relationship=relationship,
            amount_a=tp,
            amount_b=tg,
            absolute_difference=delta,
            relative_difference=relative_difference,
            residual=residual,
            currency_status="MISMATCH" if currency_mismatch else primary_currency,
            comparison_basis="Gross Amount",
            notes=tuple(notes),
            assumptions=tuple(assumptions)
        )
        

