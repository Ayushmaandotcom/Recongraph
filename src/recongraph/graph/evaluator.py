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

from recongraph.plugins.provider import EvidenceProvider

class HypothesisEvaluator:
    """
    Evaluates a structural hypothesis by delegating to EvidenceProviders.
    """
    def __init__(self, evidence_providers: Iterable[EvidenceProvider]):
        self.evidence_providers = tuple(evidence_providers)

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
            
        from recongraph.matching.scoring import ScoringEvidence
        
        contributions = {}
        for provider in self.evidence_providers:
            contrib = provider.evaluate(purchases, gsts)
            contributions[provider.get_name()] = contrib
            
        supporting_evidence = ScoringEvidence(
            signals={}, # Legacy
            relationship=None, # Legacy
            metadata={}, # Legacy
            contributions=contributions
        )

        return EvaluatedHypothesis(
            hypothesis=hypothesis,
            score=0.0, # Handled by fusion later
            coverage=len(hypothesis.matched_nodes) / max(1, len(hypothesis.component_nodes)),
            eligibility=EligibilityStatus.ELIGIBLE, # We defer constraints to fusion
            supporting_evidence=supporting_evidence,
            violations=frozenset()
        )
