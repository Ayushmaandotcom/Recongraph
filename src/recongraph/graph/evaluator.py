from typing import Iterable
from recongraph.graph.candidate import CandidateGraph
from recongraph.graph.hypotheses import Hypothesis, EvaluatedHypothesis, EligibilityStatus
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
        if not hypothesis.matched_nodes:
            return EvaluatedHypothesis(
                hypothesis=hypothesis,
                score=0.0,
                coverage=0.0,
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
                coverage=0.0,
                eligibility=EligibilityStatus.INELIGIBLE,
                supporting_evidence={},
                violations=frozenset(["MISSING_COUNTERPARTY"])
            )
            
        # Evidence Aggregation via Plugins
        signals = {}
        violations: set[str] = set()
        supporting_metadata = {}
        contributions = {}
        
        from recongraph.domain.reliability import convert_ocr_report_to_envelope, ExtractionQuality
        
        # 1. Collect ReliabilityEnvelopes
        envelopes = []
        for record in purchases + gsts:
            if getattr(record, "reliability_envelope", None):
                envelopes.append(record.reliability_envelope)
            elif getattr(record, "ocr_confidence_report", None):
                envelopes.append(convert_ocr_report_to_envelope(record.ocr_confidence_report))
                
        # 2. Evaluate Evidence Providers
        for provider in self.evidence_providers:
            contrib = provider.evaluate(purchases, gsts)
            contributions[contrib.provider_name] = contrib
            signals[contrib.provider_name] = contrib.score
            violations.update(contrib.violations)
            if contrib.metadata:
                supporting_metadata[contrib.provider_name] = contrib.metadata
                
        # 3. Apply Attenuation Policy
        if hasattr(self.policy, "attenuation_policy"):
            quality_order = {
                ExtractionQuality.AUTHORITATIVE: 4,
                ExtractionQuality.HIGH: 3,
                ExtractionQuality.DEGRADED: 2,
                ExtractionQuality.LOW: 1,
                ExtractionQuality.FAILED: 0
            }
            
            # Group rules by (signal_name, field_name) to avoid multiple attenuation
            fields_to_check = set((r.signal_name, r.field_name) for r in self.policy.attenuation_policy.rules)
            
            for signal_name, field_name in fields_to_check:
                if signal_name not in signals or signals[signal_name] is None:
                    continue
                    
                lowest_quality = None
                
                for env in envelopes:
                    profile = env.get(field_name)
                    if profile:
                        q = profile.extraction_quality
                        if lowest_quality is None or quality_order.get(q, 5) < quality_order.get(lowest_quality, 5):
                            lowest_quality = q
                                
                if lowest_quality is not None:
                    weight, new_violations = self.policy.attenuation_policy.apply(signal_name, lowest_quality)
                    signals[signal_name] *= weight
                    violations.update(new_violations)
                
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
            "metadata": supporting_metadata,
            "contributions": contributions
        }

        return EvaluatedHypothesis(
            hypothesis=hypothesis,
            score=relationship.score if relationship.score is not None else 0.0,
            coverage=relationship.coverage,
            eligibility=eligibility,
            supporting_evidence=supporting_evidence,
            violations=frozenset(violations)
        )
