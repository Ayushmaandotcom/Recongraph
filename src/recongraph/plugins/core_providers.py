from typing import Iterable, Sequence, Callable, TypeVar, Any
from dataclasses import dataclass
import datetime

from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.plugins.provider_v2 import EvidencePipeline, EvidenceContributionV2
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker, ExactAmountBlocker, TaxIdentityBlocker, ReferenceTokenBlocker
from recongraph.matching.scoring import SignalName
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, compute_reference_interpretation
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline
from recongraph.domain.temporal.interpretation import TemporalPairInterpretation
from recongraph.domain.reference.interpretation import ReferencePairInterpretation
from recongraph.matching.purchase_gst_semantics import SemanticFinding

from recongraph.domain.vendor.context import VendorIdentityContext
from recongraph.domain.vendor.parser import DeterministicVendorParser
from recongraph.domain.vendor.artifact import build_vendor_observation_artifact
from recongraph.domain.vendor.interpretation import VendorPairInterpreter
from recongraph.domain.vendor.policy import VendorProjectionPolicyV1

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
    """
    OCR-aware financial evidence provider.

    When an OcrConfidenceReport is attached to a record, the raw financial
    similarity score is attenuated proportionally to OCR confidence on the
    'amount' field. Low-confidence amounts emit a dedicated violation so the
    decision engine can route to review.
    """
    OCR_LOW_CONFIDENCE_VIOLATION = SemanticFinding.OCR_AMOUNT_LOW_CONFIDENCE
    OCR_UNREADABLE_VIOLATION = SemanticFinding.OCR_AMOUNT_UNREADABLE

    def __init__(self, tolerance: float = 0.05):
        from decimal import Decimal
        self.pipeline = FinancialEvidencePipeline(tolerance=Decimal(str(tolerance)))

    def get_name(self) -> str:
        return SignalName.AMOUNT

    def get_blockers(self) -> Iterable[Blocker]:
        return [ExactAmountBlocker()]

    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)

        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )

@dataclass(frozen=True)
class TemporalObservation:
    p_dates: tuple[datetime.date, ...]
    g_dates: tuple[datetime.date, ...]
    p_periods: tuple[str | None, ...]
    g_periods: tuple[str | None, ...]

class TemporalEvidencePipeline(EvidencePipeline[TemporalObservation, tuple[TemporalPairInterpretation, ...]]):
    def __init__(self, max_days: int):
        self.max_days = max_days

    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> TemporalObservation:
        return TemporalObservation(
            p_dates=tuple(p.record_date for p in purchases),
            g_dates=tuple(g.record_date for g in gsts),
            p_periods=tuple(p.filing_period for p in purchases),
            g_periods=tuple(g.filing_period for g in gsts)
        )

    def interpret(self, observation: TemporalObservation) -> tuple[TemporalPairInterpretation, ...]:
        from recongraph.domain.temporal.artifact import TemporalArtifact
        from recongraph.domain.temporal.interpretation import TemporalPairInterpreter
        
        interps = []
        for p_date, p_period in zip(observation.p_dates, observation.p_periods):
            p_art = TemporalArtifact.create(p_date, p_period)
            for g_date, g_period in zip(observation.g_dates, observation.g_periods):
                g_art = TemporalArtifact.create(g_date, g_period)
                interps.append(TemporalPairInterpreter.interpret(p_art, g_art, self.max_days))
                
        return tuple(interps)

    def contribute(self, interpretation: tuple[TemporalPairInterpretation, ...]) -> EvidenceContributionV2[tuple[TemporalPairInterpretation, ...]]:
        from recongraph.domain.temporal.projection import TemporalV1ProjectionContract
        from recongraph.domain.temporal.claims import SAME_FISCAL_PERIOD_CLAIM, VALID_LATE_FILING_CLAIM
        from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
        from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity
        from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
        from recongraph.domain.temporal.factors import TemporalRelationState
        # For missing ancestry, we mock it for tests for now just like in Semantic
        from recongraph.contrib.kernel.assertions import EvidenceAncestryRef
        from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        
        projection = TemporalV1ProjectionContract.project(interpretation)
        
        assertions = []
        for interp in interpretation:
            state = interp.relation.state
            
            if state in (TemporalRelationState.EXACT_MATCH, TemporalRelationState.WITHIN_TOLERANCE):
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(
                        claim=SAME_FISCAL_PERIOD_CLAIM,
                        kind=ScopeKind.RECORD_PAIR,
                        left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]
                    ),
                    polarity=AssertionPolarity.SUPPORT,
                    magnitude=1.0,
                    authority=AuthorityDescriptor(basis=AuthorityBasisId("temporal_model")),
                    ancestry=mock_ancestry
                ))
            elif state == TemporalRelationState.LATE_FILING:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(
                        claim=VALID_LATE_FILING_CLAIM,
                        kind=ScopeKind.RECORD_PAIR,
                        left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]
                    ),
                    polarity=AssertionPolarity.SUPPORT,
                    magnitude=1.0,
                    authority=AuthorityDescriptor(basis=AuthorityBasisId("temporal_model")),
                    ancestry=mock_ancestry
                ))
            elif state == TemporalRelationState.EXCEEDS_WINDOW:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(
                        claim=SAME_FISCAL_PERIOD_CLAIM,
                        kind=ScopeKind.RECORD_PAIR,
                        left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]
                    ),
                    polarity=AssertionPolarity.CONFLICT,
                    magnitude=1.0,
                    authority=AuthorityDescriptor(basis=AuthorityBasisId("temporal_model")),
                    ancestry=mock_ancestry
                ))

        return EvidenceContributionV2(
            provider_name=SignalName.TEMPORAL,
            score=projection.score,
            violations=projection.violations,
            interpretation=interpretation,
            metadata={"temporal_projection": projection, "assertions": tuple(assertions)}
        )

class TemporalEvidenceProvider:
    """
    OCR-aware temporal evidence provider.

    When a record carries an OcrConfidenceReport, low-confidence dates
    generate a warning violation so manual reviewers know the date might
    have been misread. The temporal *score* itself is not attenuated
    (the date can still match correctly even if OCR was uncertain) but
    the violation causes the packet to include highlight bounding boxes.
    """
    OCR_DATE_LOW_CONFIDENCE_VIOLATION = SemanticFinding.OCR_DATE_LOW_CONFIDENCE
    OCR_DATE_UNREADABLE_VIOLATION = SemanticFinding.OCR_DATE_UNREADABLE

    def __init__(self, max_days: int = 7):
        self.max_days = max_days
        self.pipeline = TemporalEvidencePipeline(max_days)

    def get_name(self) -> str:
        return SignalName.TEMPORAL

    def get_blockers(self) -> Iterable[Blocker]:
        return []

    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)

        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )


@dataclass(frozen=True)
class TaxObservation:
    purchases: tuple[PurchaseRecord, ...]
    gsts: tuple[GSTRecord, ...]

from recongraph.domain.tax.parser import DeterministicTaxParser
from recongraph.domain.tax.artifact import TaxIntelligenceArtifact
from recongraph.domain.tax.interpretation import TaxIntelligenceInterpreter, TaxIntelligenceInterpretation
from recongraph.domain.tax.factors import GSTINRelationState, PANRelationState, RegimeRelationState, GrossNetRelationState
from recongraph.contrib.kernel.scopes import Proposition, PropositionSubject, ScopeKind, SubjectRef
from recongraph.contrib.kernel.assertions import EvidenceAssertionIdentity, EvidenceAssertion, AssertionPolarity
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.assertions import EvidenceAncestryRef
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
from recongraph.domain.tax.claims import SAME_TAX_IDENTITY_CLAIM, VALID_REGIME_ALIGNMENT_CLAIM, GROSS_NET_CONSISTENCY_CLAIM

class TaxEvidencePipeline(EvidencePipeline[TaxObservation, tuple[TaxIntelligenceInterpretation, ...]]):
    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> TaxObservation:
        return TaxObservation(purchases=tuple(purchases), gsts=tuple(gsts))

    def interpret(self, observation: TaxObservation) -> tuple[TaxIntelligenceInterpretation, ...]:
        interpretations = []
        for p in observation.purchases:
            p_val = DeterministicTaxParser.parse(p.tax_identity, field_id="tax_identity")
            p_artifact = TaxIntelligenceArtifact.create(p_val, p.amount, p.net_amount, p.tax_amount, p.tax_rate)
            for g in observation.gsts:
                g_val = DeterministicTaxParser.parse(g.tax_identity, field_id="tax_identity")
                g_artifact = TaxIntelligenceArtifact.create(g_val, g.amount, g.net_amount, g.tax_amount, g.tax_rate)
                interp = TaxIntelligenceInterpreter.interpret(p_artifact, g_artifact)
                interpretations.append(interp)
        return tuple(interpretations)

    def contribute(self, interpretation: tuple[TaxIntelligenceInterpretation, ...]) -> EvidenceContributionV2[tuple[TaxIntelligenceInterpretation, ...]]:
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        
        assertions = []
        for interp in interpretation:
            # Tax Identity Assertions
            if interp.gstin_relation.state == GSTINRelationState.EXACT_MATCH or interp.pan_relation.state == PANRelationState.EXACT_MATCH:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=SAME_TAX_IDENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))
            elif interp.gstin_relation.state == GSTINRelationState.DISTINCT and interp.pan_relation.state == PANRelationState.DISTINCT:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=SAME_TAX_IDENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))
                
            # Regime Alignment Assertions
            if interp.regime_relation.state == RegimeRelationState.CONSISTENT:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=VALID_REGIME_ALIGNMENT_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))
            elif interp.regime_relation.state == RegimeRelationState.INCONSISTENT:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=VALID_REGIME_ALIGNMENT_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.CONFLICT, magnitude=0.5, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))
                
            # Gross/Net Consistency Assertions
            if interp.gross_net_relation.state == GrossNetRelationState.CONSISTENT:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=GROSS_NET_CONSISTENCY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))
            elif interp.gross_net_relation.state == GrossNetRelationState.INCONSISTENT:
                assertions.append(EvidenceAssertion(
                    proposition=Proposition.create(claim=GROSS_NET_CONSISTENCY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                    polarity=AssertionPolarity.CONFLICT, magnitude=0.5, authority=AuthorityDescriptor(basis=AuthorityBasisId("tax_model")), ancestry=mock_ancestry
                ))

        # Re-derive score via legacy logic for backward compatibility in score field, but primary evidence is assertions
        from recongraph.domain.tax.projection import TaxV1ProjectionContract
        # TaxV1ProjectionContract expects TaxPairInterpretation, so we must mock or bypass it if it crashes.
        # It expects gstin_relation and pan_relation, which our TaxIntelligenceInterpretation provides!
        projection = TaxV1ProjectionContract.project(interpretation)

        return EvidenceContributionV2(
            provider_name=SignalName.TAX_IDENTITY,
            score=projection.score,
            violations=projection.violations,
            interpretation=interpretation,
            metadata={"assertions": tuple(assertions)}
        )

class TaxEvidenceProvider:
    def __init__(self):
        self.pipeline = TaxEvidencePipeline()

    def get_name(self) -> str:
        return SignalName.TAX_IDENTITY
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [TaxIdentityBlocker()]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)
        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )

@dataclass(frozen=True)
class VendorObservationPayload:
    purchases: tuple[PurchaseRecord, ...]
    gsts: tuple[GSTRecord, ...]

class VendorEvidencePipeline(EvidencePipeline[VendorObservationPayload, Any]):
    def __init__(self, context: VendorIdentityContext):
        from recongraph.domain.vendor.observation import VendorNameObservation
        from recongraph.contrib.kernel.derivations import DerivedArtifactIdentity
        self.context = context
        self._artifact_cache: dict[str | None, tuple[VendorNameObservation, DerivedArtifactIdentity]] = {}

    def _get_artifact(self, raw_name: str | None):
        if raw_name not in self._artifact_cache:
            obs = DeterministicVendorParser.parse(raw_name)
            self._artifact_cache[raw_name] = (obs, build_vendor_observation_artifact(obs).identity)
        return self._artifact_cache[raw_name]

    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> VendorObservationPayload:
        return VendorObservationPayload(tuple(purchases), tuple(gsts))

    def interpret(self, observation: VendorObservationPayload) -> Any:
        scores_with_meta = []
        for p in observation.purchases:
            p_obs, p_id = self._get_artifact(p.vendor_name)
            for g in observation.gsts:
                g_obs, g_id = self._get_artifact(g.vendor_name)
                
                interp = VendorPairInterpreter.interpret(p_obs, p_id, g_obs, g_id, self.context)
                proj = VendorProjectionPolicyV1.project(interp)
                
                if proj.similarity is not None:
                    scores_with_meta.append((proj.similarity, interp, proj))
                    
        if not scores_with_meta:
            return None
            
        weakest = min(scores_with_meta, key=lambda x: x[0])
        return weakest

    def contribute(self, interpretation: Any) -> EvidenceContributionV2[Any]:
        if not interpretation:
            return EvidenceContributionV2(
                provider_name=SignalName.ENTITY,
                score=None,
                metadata={},
                interpretation=None
            )
            
        weakest_similarity, weakest_interp, weakest_proj = interpretation
        
        from recongraph.contrib.kernel.assertions import EvidenceAncestryRef, EvidenceAssertion, AssertionPolarity
        from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
        from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
        from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
        from recongraph.domain.vendor.claims import (
            SAME_ECONOMIC_ENTITY_CLAIM, SAME_LEGAL_ENTITY_CLAIM,
            SHARED_TAX_REGISTRATION_CLAIM, ALIAS_MATCH_CLAIM
        )
        from recongraph.domain.vendor.factors import (
            PANRelationState, GSTRegistrationRelationState, LexicalRelationState, OrganizationalRelationState
        )
        
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        
        assertions = []
        
        # 1. Legal Entity Assertions (PAN)
        pan_state = weakest_interp.pan_relation.state
        if pan_state == PANRelationState.VALID_AND_EQUAL:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_LEGAL_ENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
        elif pan_state == PANRelationState.VALID_AND_DIFFERENT:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_LEGAL_ENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
            
        # 2. Tax Registration Assertions (GSTIN)
        gst_state = weakest_interp.gst_registration_relation.state
        if gst_state == GSTRegistrationRelationState.VALID_AND_EQUAL:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SHARED_TAX_REGISTRATION_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
        elif gst_state == GSTRegistrationRelationState.VALID_AND_DIFFERENT:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SHARED_TAX_REGISTRATION_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
            
        # 3. Alias Match Assertions (Lexical)
        lex_state = weakest_interp.lexical_relation.state
        if lex_state in (LexicalRelationState.EXACT_NORMALIZED_CORE_EQUALITY, LexicalRelationState.TOKEN_SET_EQUALITY, LexicalRelationState.BOUNDED_SUBSET):
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=ALIAS_MATCH_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
        elif lex_state == LexicalRelationState.DIFFERENT:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=ALIAS_MATCH_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=0.5, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
            
        # 4. Economic Entity Assertions (Organizational)
        org_state = weakest_interp.organizational_relation.state
        if org_state in (OrganizationalRelationState.KNOWN_ALIAS, OrganizationalRelationState.PARENT_SUBSIDIARY, OrganizationalRelationState.HISTORICAL_RENAME):
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_ECONOMIC_ENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))
        elif org_state == OrganizationalRelationState.UNAFFILIATED:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=SAME_ECONOMIC_ENTITY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.CONFLICT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")), ancestry=mock_ancestry
            ))

        return EvidenceContributionV2(
            provider_name=SignalName.ENTITY,
            score=weakest_similarity,
            metadata={
                "vendor_interpretation": weakest_interp,
                "vendor_projection": weakest_proj,
                "assertions": tuple(assertions)
            },
            interpretation=interpretation
        )

class VendorEvidenceProvider:
    def __init__(self, context: VendorIdentityContext):
        self.pipeline = VendorEvidencePipeline(context)
        
    def get_name(self) -> str:
        return SignalName.ENTITY
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)
        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )

@dataclass(frozen=True)
class ReferenceObservation:
    p_refs: str
    g_refs: str

class ReferenceEvidencePipeline(EvidencePipeline[ReferenceObservation, tuple[ReferencePairInterpretation, ...]]):
    def __init__(self, context: ReferenceEvidenceContext):
        self.context = context

    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> ReferenceObservation:
        p_refs = " ".join(sorted(set(p.reference for p in purchases if p.reference)))
        g_refs = " ".join(sorted(set(g.reference for g in gsts if g.reference)))
        return ReferenceObservation(p_refs=p_refs, g_refs=g_refs)

    def interpret(self, observation: ReferenceObservation) -> tuple[ReferencePairInterpretation, ...]:
        from recongraph.domain.reference.parser import DeterministicReferenceParser
        from recongraph.domain.reference.artifact import ReferenceIdentifierArtifact
        from recongraph.domain.reference.interpretation import ReferencePairInterpreter

        p_art = ReferenceIdentifierArtifact.create(DeterministicReferenceParser.parse(observation.p_refs))
        g_art = ReferenceIdentifierArtifact.create(DeterministicReferenceParser.parse(observation.g_refs))
        
        interp = ReferencePairInterpreter.interpret(p_art, g_art)
        return (interp,)

    def contribute(self, interpretation: tuple[ReferencePairInterpretation, ...]) -> EvidenceContributionV2[tuple[ReferencePairInterpretation, ...]]:
        from recongraph.domain.reference.projection import ReferenceV1ProjectionContract
        
        projection = ReferenceV1ProjectionContract.project(interpretation)
            
        return EvidenceContributionV2(
            provider_name=SignalName.REFERENCE,
            score=projection.score,
            violations=projection.violations,
            metadata={"reference_projection": projection},
            interpretation=interpretation
        )

class ReferenceEvidenceProvider:
    def __init__(self, context: ReferenceEvidenceContext):
        self.context = context
        self.pipeline = ReferenceEvidencePipeline(context)
        
    def get_name(self) -> str:
        return SignalName.REFERENCE
        
    def get_blockers(self) -> Iterable[Blocker]:
        return [ReferenceTokenBlocker(self.context.profile)]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)
        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )

# --- Document Intelligence Engine ---

from recongraph.domain.document.layout import DocumentLayoutArtifact
from recongraph.domain.document.interpretation import DocumentLayoutInterpreter

@dataclass(frozen=True)
class DocumentObservationPayload:
    purchases: tuple[PurchaseRecord, ...]
    gsts: tuple[GSTRecord, ...]

class DocumentEvidencePipeline(EvidencePipeline[DocumentObservationPayload, Any]):
    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> DocumentObservationPayload:
        return DocumentObservationPayload(tuple(purchases), tuple(gsts))

    def interpret(self, observation: DocumentObservationPayload) -> Any:
        # We evaluate the purchase record's layout (as it represents the invoice)
        # In a real system, we might evaluate both and compare structural fingerprints.
        for p in observation.purchases:
            if p.layout_artifact:
                return DocumentLayoutInterpreter.interpret(p.layout_artifact)
        return None

    def contribute(self, interpretation: Any) -> EvidenceContributionV2[Any]:
        if not interpretation:
            return EvidenceContributionV2(
                provider_name="DocumentIntelligence",
                score=None,
                metadata={},
                interpretation=None
            )
            
        from recongraph.contrib.kernel.assertions import EvidenceAncestryRef, EvidenceAssertion, AssertionPolarity
        from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
        from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
        from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest
        from recongraph.domain.document.claims import (
            HAS_VALID_SIGNATURE_REGION_CLAIM, TOTALS_BLOCK_CONSISTENCY_CLAIM, HEADER_MATCH_CLAIM
        )
        
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        
        assertions = []
        
        if interpretation.has_signature:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=HAS_VALID_SIGNATURE_REGION_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("document_model")), ancestry=mock_ancestry
            ))
            
        if interpretation.has_totals_block:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=TOTALS_BLOCK_CONSISTENCY_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("document_model")), ancestry=mock_ancestry
            ))
            
        if interpretation.has_header:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(claim=HEADER_MATCH_CLAIM, kind=ScopeKind.RECORD_PAIR, left=[SubjectRef("urn:purchase")], right=[SubjectRef("urn:gst")]),
                polarity=AssertionPolarity.SUPPORT, magnitude=1.0, authority=AuthorityDescriptor(basis=AuthorityBasisId("document_model")), ancestry=mock_ancestry
            ))
            
        return EvidenceContributionV2(
            provider_name="DocumentIntelligence",
            score=None,
            metadata={
                "document_interpretation": interpretation,
                "assertions": tuple(assertions)
            },
            interpretation=interpretation
        )

class DocumentIntelligenceProvider:
    def __init__(self):
        self.pipeline = DocumentEvidencePipeline()

    def get_name(self) -> str:
        return "DocumentIntelligence"
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        observation = self.pipeline.extract(purchases, gsts)
        interpretation = self.pipeline.interpret(observation)
        contrib_v2 = self.pipeline.contribute(interpretation)
        return EvidenceContribution(
            provider_name=contrib_v2.provider_name,
            score=contrib_v2.score,
            violations=contrib_v2.violations,
            metadata=contrib_v2.metadata
        )
