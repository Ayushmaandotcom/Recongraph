from typing import Iterable, Sequence, Any
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import Blocker
from recongraph.domain.semantics.artifact import SimulatedEmbeddingProvider
from recongraph.domain.semantics.observation import SemanticObservation
from recongraph.domain.semantics.interpretation import SemanticPairInterpreter, SemanticInterpretationResult
from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
from recongraph.contrib.kernel.claims import ClaimId, ClaimSemanticVersion
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef
from recongraph.domain.semantics.claims import SAME_BUSINESS_PURPOSE_CLAIM
from recongraph.plugins.provider_v2 import EvidenceProviderV2, EvidencePipeline, EvidenceContributionV2
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest

class SemanticEvidencePipeline(EvidencePipeline[tuple[SemanticObservation, SemanticObservation], SemanticInterpretationResult]):
    """
    Implements the typed pipeline for semantic evaluation.
    """
    def extract(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> tuple[SemanticObservation, SemanticObservation]:
        p_desc = " ".join(p.description for p in purchases if p.description)
        g_desc = " ".join(g.description for g in gsts if g.description)
        
        p_embed = SimulatedEmbeddingProvider.embed(p_desc)
        g_embed = SimulatedEmbeddingProvider.embed(g_desc)
        
        p_obs = SemanticObservation.create(p_desc, p_embed)
        g_obs = SemanticObservation.create(g_desc, g_embed)
        
        return (p_obs, g_obs)

    def interpret(self, extraction: tuple[SemanticObservation, SemanticObservation]) -> SemanticInterpretationResult:
        p_obs, g_obs = extraction
        return SemanticPairInterpreter.interpret(p_obs, g_obs)

    def contribute(self, interpretation: SemanticInterpretationResult) -> EvidenceContributionV2[SemanticInterpretationResult]:
        # EvidenceProviderV2 returns EvidenceContributionV2. 
        # But for Stage 8H-1, we want to emit K6 EvidenceAssertion.
        # We will embed the assertions directly in the EvidenceContributionV2 metadata
        # to bridge the engine's legacy scoring with the new K6 assertion architecture.
        
        # Determine base scalar score for backward compatibility while testing
        score = None
        if interpretation.supports_same_business_purpose:
            score = 1.0
        elif interpretation.contradicts_business_purpose:
            score = 0.0
            
        assertions = []
        
        # We need a dummy ancestry reference for the assertion. 
        # In a fully integrated system, the observation occurs in K5 and gets a derivation occurrence identity.
        # For now, we mock the ancestry reference as an observation occurrence.
        mock_ancestry = EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"),
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"),
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
        
        if interpretation.supports_same_business_purpose:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(
                    claim=SAME_BUSINESS_PURPOSE_CLAIM,
                    kind=ScopeKind.RECORD_PAIR,
                    left=[SubjectRef("urn:semantic_left")],
                    right=[SubjectRef("urn:semantic_right")]
                ),
                polarity=AssertionPolarity.SUPPORT,
                magnitude=min(max(interpretation.cosine_similarity, 0.0001), 1.0), # Must be strictly positive
                authority=AuthorityDescriptor(basis=AuthorityBasisId("semantic_model")),
                ancestry=mock_ancestry
            ))
            
        elif interpretation.contradicts_business_purpose:
            assertions.append(EvidenceAssertion(
                proposition=Proposition.create(
                    claim=SAME_BUSINESS_PURPOSE_CLAIM,
                    kind=ScopeKind.RECORD_PAIR,
                    left=[SubjectRef("urn:semantic_left")],
                    right=[SubjectRef("urn:semantic_right")]
                ),
                polarity=AssertionPolarity.CONFLICT,
                # Magnitude of conflict is how far it is from the threshold
                magnitude=min(max(1.0 - interpretation.cosine_similarity, 0.0001), 1.0), 
                authority=AuthorityDescriptor(basis=AuthorityBasisId("semantic_model")),
                ancestry=mock_ancestry
            ))

        return EvidenceContributionV2(
            provider_name=SignalName.SEMANTICS,
            score=score,
            violations=frozenset({"SEMANTIC_PURPOSE_CONTRADICTION"}) if interpretation.contradicts_business_purpose else frozenset(),
            metadata={"assertions": tuple(assertions)},
            interpretation=interpretation
        )

from recongraph.plugins.provider import EvidenceContribution

from recongraph.matching.scoring import SignalName

class SemanticEvidenceProvider:
    """
    Exposes the SemanticEvidencePipeline as an EvidenceProviderV2.
    """
    def __init__(self):
        self.pipeline = SemanticEvidencePipeline()
        
    def get_name(self) -> str:
        return SignalName.SEMANTICS
        
    def get_blockers(self) -> Iterable[Blocker]:
        return []
        
    def get_pipeline(self) -> EvidencePipeline[Any, Any]:
        return self.pipeline
        
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
