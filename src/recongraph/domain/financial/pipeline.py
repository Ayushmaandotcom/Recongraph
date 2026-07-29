from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence
from enum import StrEnum

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.provider_v2 import EvidencePipeline, EvidenceContributionV2


class EqualityRelation(StrEnum):
    EQUAL = "EQUAL"
    UNEQUAL = "UNEQUAL"

class MagnitudeRelation(StrEnum):
    LEFT_GREATER = "LEFT_GREATER"
    EQUAL = "EQUAL"
    RIGHT_GREATER = "RIGHT_GREATER"

class CurrencyRelation(StrEnum):
    SAME = "SAME"
    DIFFERENT = "DIFFERENT"
    LEFT_MISSING = "LEFT_MISSING"
    RIGHT_MISSING = "RIGHT_MISSING"
    BOTH_MISSING = "BOTH_MISSING"

class SignRelation(StrEnum):
    SAME_POSITIVE = "SAME_POSITIVE"
    SAME_NEGATIVE = "SAME_NEGATIVE"
    OPPOSITE = "OPPOSITE"
    ZERO_ZERO = "ZERO_ZERO"
    ZERO_NONZERO = "ZERO_NONZERO"

class CompatibilityFlag(StrEnum):
    WITHIN_STRICT_TOLERANCE = "WITHIN_STRICT_TOLERANCE"
    WITHIN_RELAXED_TOLERANCE = "WITHIN_RELAXED_TOLERANCE"
    OUTSIDE_TOLERANCE_LEFT_GREATER = "OUTSIDE_TOLERANCE_LEFT_GREATER"
    OUTSIDE_TOLERANCE_RIGHT_GREATER = "OUTSIDE_TOLERANCE_RIGHT_GREATER"


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
    equality: EqualityRelation
    magnitude_relation: MagnitudeRelation
    currency_relation: CurrencyRelation
    sign_relation: SignRelation
    
    amount_a: Decimal
    amount_b: Decimal
    
    absolute_difference: Decimal
    relative_difference: Decimal
    residual: Decimal
    
    is_multiple: bool = False
    multiple_factor: int | None = None
    
    compatibility_flags: tuple[CompatibilityFlag, ...] = field(default_factory=tuple)
    
    comparison_basis: str = "Gross Amount"
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
        
        # Determine signs based on total amounts if aggregated, or the single sign.
        # If there are mixed signs in a group, we simplify by looking at the net total sign.
        def get_sign(amounts: tuple[Decimal, ...], signs: tuple[int, ...]) -> int:
            if not amounts:
                return 1
            total = sum(a * Decimal(s) for a, s in zip(amounts, signs))
            if total > 0: return 1
            if total < 0: return -1
            return 0
            
        sign_p = get_sign(observation.purchase_gross, observation.purchase_signs)
        sign_g = get_sign(observation.gst_gross, observation.gst_signs)
        
        if sign_p == 0 and sign_g == 0:
            sign_relation = SignRelation.ZERO_ZERO
        elif sign_p == 0 or sign_g == 0:
            sign_relation = SignRelation.ZERO_NONZERO
        elif sign_p == sign_g:
            sign_relation = SignRelation.SAME_POSITIVE if sign_p > 0 else SignRelation.SAME_NEGATIVE
        else:
            sign_relation = SignRelation.OPPOSITE
            
        # Currency relation
        p_curr = set(c for c in observation.purchase_currencies if c)
        g_curr = set(c for c in observation.gst_currencies if c)
        
        if not p_curr and not g_curr:
            currency_relation = CurrencyRelation.BOTH_MISSING
        elif not p_curr:
            currency_relation = CurrencyRelation.LEFT_MISSING
        elif not g_curr:
            currency_relation = CurrencyRelation.RIGHT_MISSING
        else:
            if len(p_curr | g_curr) == 1:
                currency_relation = CurrencyRelation.SAME
            else:
                currency_relation = CurrencyRelation.DIFFERENT
                
        # Magnitude relation (absolute values)
        mag_p = abs(tp)
        mag_g = abs(tg)
        delta = abs(mag_p - mag_g)
        residual = mag_p - mag_g
        
        if delta == Decimal("0"):
            equality = EqualityRelation.EQUAL
            magnitude_relation = MagnitudeRelation.EQUAL
        else:
            equality = EqualityRelation.UNEQUAL
            if residual > 0:
                magnitude_relation = MagnitudeRelation.LEFT_GREATER
            else:
                magnitude_relation = MagnitudeRelation.RIGHT_GREATER
                
        flags = []
        if equality == EqualityRelation.UNEQUAL:
            if delta <= self.tolerance:
                flags.append(CompatibilityFlag.WITHIN_STRICT_TOLERANCE)
            if self.tolerance < delta <= self.fee_tolerance and residual > 0:
                flags.append(CompatibilityFlag.WITHIN_RELAXED_TOLERANCE)
            if residual > 0:
                flags.append(CompatibilityFlag.OUTSIDE_TOLERANCE_LEFT_GREATER)
            elif residual < 0:
                flags.append(CompatibilityFlag.OUTSIDE_TOLERANCE_RIGHT_GREATER)
                
        max_val = max(mag_p, mag_g)
        relative_difference = Decimal("0") if max_val == Decimal("0") else delta / max_val
        
        is_multiple = False
        multiple_factor = None
        
        if mag_p > 0 and mag_g > 0:
            if mag_p > mag_g and mag_p % mag_g == 0:
                is_multiple = True
                multiple_factor = int(mag_p / mag_g)
            elif mag_g > mag_p and mag_g % mag_p == 0:
                is_multiple = True
                multiple_factor = int(mag_g / mag_p)

        return AmountInterpretation(
            equality=equality,
            magnitude_relation=magnitude_relation,
            currency_relation=currency_relation,
            sign_relation=sign_relation,
            amount_a=mag_p,
            amount_b=mag_g,
            absolute_difference=delta,
            relative_difference=relative_difference,
            residual=residual,
            is_multiple=is_multiple,
            multiple_factor=multiple_factor,
            compatibility_flags=tuple(flags),
            notes=(),
            assumptions=()
        )

    def contribute(self, interpretation: AmountInterpretation) -> EvidenceContributionV2[AmountInterpretation]:
        from recongraph.domain.financial.amount_projection import project_amount_similarity
        from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
        from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
        from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
        from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
        from recongraph.domain.financial.claims import SAME_AMOUNT_CLAIM, WITHIN_FEE_TOLERANCE_CLAIM, CURRENCY_CONSISTENCY_CLAIM
        
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )

        assertions = []
        
        # 1. Amount Assertions
        if interpretation.equality.value == "EQUAL":
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_AMOUNT_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))
        elif CompatibilityFlag.WITHIN_STRICT_TOLERANCE in interpretation.compatibility_flags:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_AMOUNT_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=0.9, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))
        elif CompatibilityFlag.WITHIN_RELAXED_TOLERANCE in interpretation.compatibility_flags:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=WITHIN_FEE_TOLERANCE_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))
        else:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_AMOUNT_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))

        # 2. Currency Assertions
        if interpretation.currency_relation.value == "SAME":
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=CURRENCY_CONSISTENCY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))
        elif interpretation.currency_relation.value == "DIFFERENT":
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=CURRENCY_CONSISTENCY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("financial_model")), ancestry=mock_ancestry
            ))

        projection = project_amount_similarity(interpretation)
        violations = set(projection.warnings)
        if interpretation.currency_relation.value == "DIFFERENT":
            violations.add("CURRENCY_MISMATCH")
        elif projection.similarity is not None and projection.similarity < 0.5 and interpretation.equality.value != "EQUAL":
            violations.add("SEVERE_AMOUNT_CONFLICT")
            
        return EvidenceContributionV2(
            provider_name="amount",
            score=projection.similarity,
            violations=frozenset(violations),
            metadata={
                "interpretation": interpretation,
                "projection": projection,
                "assertions": tuple(assertions)
            },
            interpretation=interpretation
        )

        

