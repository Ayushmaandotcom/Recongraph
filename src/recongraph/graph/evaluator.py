from typing import Iterable
from recongraph.graph.candidate import CandidateGraph
from recongraph.graph.hypotheses import Hypothesis, EvaluatedHypothesis, EligibilityStatus
from recongraph.matching.signals import tax_identity_score, entity_score
from recongraph.matching.scoring import SignalName, calculate_relationship_score
from recongraph.matching.purchase_gst_semantics import (
    analyze_purchase_gst_semantics, 
    evaluate_purchase_gst_one_to_one_eligibility, 
    OneToOneEligibility
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
        # HS-004: If hypothesis is empty, it resolves nothing.
        if not hypothesis.matched_nodes:
            return EvaluatedHypothesis(
                hypothesis=hypothesis,
                score=0.0,
                eligibility=EligibilityStatus.INELIGIBLE,
                supporting_evidence={},
                violations=frozenset(["EMPTY_HYPOTHESIS"])
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
            return EvaluatedHypothesis(
                hypothesis=hypothesis,
                score=0.0,
                eligibility=EligibilityStatus.INELIGIBLE,
                supporting_evidence={},
                violations=frozenset(["MISSING_COUNTERPARTY"])
            )
            
        # Evidence Aggregation via Plugins
        signals = {}
        violations = set()
        supporting_metadata = {}
        
        for provider in self.evidence_providers:
            contrib = provider.evaluate(purchases, gsts)
            signals[contrib.provider_name] = contrib.score
            violations.update(contrib.violations)
            if contrib.metadata:
                supporting_metadata[contrib.provider_name] = contrib.metadata
                
        semantic_findings = analyze_purchase_gst_semantics(signals)
        legacy_eligibility = evaluate_purchase_gst_one_to_one_eligibility(semantic_findings)
        
        if legacy_eligibility.status == OneToOneEligibility.ELIGIBLE:
            eligibility = EligibilityStatus.ELIGIBLE
        elif legacy_eligibility.status == OneToOneEligibility.INELIGIBLE:
            eligibility = EligibilityStatus.INELIGIBLE
        else:
            raise NotImplementedError(f"Cannot map eligibility status: {legacy_eligibility.status}")
            
        relationship = calculate_relationship_score(
            signals=signals, policy=self.policy
        )
        
        violations.update({str(f.value) for f in semantic_findings})
        
        if "TEMPORAL_MAX_DAYS_EXCEEDED" in violations:
            eligibility = EligibilityStatus.INELIGIBLE
        
        supporting_evidence = {
            "signals": signals,
            "relationship": relationship,
            "metadata": supporting_metadata
        }

        return EvaluatedHypothesis(
            hypothesis=hypothesis,
            score=relationship.score,
            eligibility=eligibility,
            supporting_evidence=supporting_evidence,
            violations=frozenset(violations)
        )
