from typing import Iterable
from recongraph.graph.candidate import CandidateGraph
from recongraph.graph.hypotheses import Hypothesis, EvaluatedHypothesis, EligibilityStatus
from recongraph.matching.scoring import SignalName, calculate_relationship_score
from recongraph.matching.purchase_gst_semantics import (
    analyze_purchase_gst_semantics, 
    evaluate_purchase_gst_one_to_one_eligibility, 
    OneToOneEligibility,
    SemanticFinding
)
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, compute_reference_interpretation
from recongraph.matching.pair_scorers import PURCHASE_TO_GST_POLICY, PURCHASE_TO_GST_MAX_DAYS
from recongraph.matching.scoring import RelationshipPolicy

from recongraph.plugins.provider import EvidenceProvider

class HypothesisEvaluator:
    """
    Evaluates a structural hypothesis by delegating to EvidenceProviders.
    """
    def __init__(self, evidence_providers: Iterable[EvidenceProvider], policy: RelationshipPolicy):
        self.evidence_providers = tuple(evidence_providers)
        self.policy = policy

    def evaluate(self, graph: CandidateGraph, hypothesis: Hypothesis) -> EvaluatedHypothesis:
        if not hypothesis.matched_nodes:
            from recongraph.matching.scoring import ScoringEvidence
            return EvaluatedHypothesis(
                hypothesis=hypothesis,
                score=0.0,
                coverage=0.0,
                eligibility=EligibilityStatus.INELIGIBLE,
                supporting_evidence=ScoringEvidence(),
                violations=frozenset([SemanticFinding.EMPTY_HYPOTHESIS])
            )
            
        purchases = []
        gsts = []
        
        for u in hypothesis.matched_nodes:
            if u.startswith("urn:recongraph:purchase:"):
                purchases.append(graph.nodes[u])
            elif u.startswith("urn:recongraph:gst:"):
                gsts.append(graph.nodes[u])
                
        # Must be bipartite
        if not purchases or not gsts:
            from recongraph.matching.scoring import ScoringEvidence
            return EvaluatedHypothesis(
                hypothesis=hypothesis,
                score=0.0,
                coverage=0.0,
                eligibility=EligibilityStatus.INELIGIBLE,
                supporting_evidence=ScoringEvidence(),
                violations=frozenset([SemanticFinding.MISSING_COUNTERPARTY])
            )
            
        from recongraph.matching.pair_scorers import score_purchase_to_gst
        from recongraph.matching.scoring import ScoringEvidence
        
        scored_pair = score_purchase_to_gst(
            purchases=purchases,
            gsts=gsts,
            providers=self.evidence_providers,
            policy=self.policy
        )
        
        eligibility = EligibilityStatus.ELIGIBLE if scored_pair.is_eligible else EligibilityStatus.INELIGIBLE
        
        supporting_evidence = ScoringEvidence(
            signals=scored_pair.signals,
            relationship=scored_pair.relationship,
            metadata=scored_pair.supporting_metadata,
            contributions=scored_pair.contributions,
            assertions=scored_pair.assertions
        )

        return EvaluatedHypothesis(
            hypothesis=hypothesis,
            score=scored_pair.score,
            coverage=scored_pair.coverage,
            eligibility=eligibility,
            supporting_evidence=supporting_evidence,
            violations=scored_pair.violations
        )
