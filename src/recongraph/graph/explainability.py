from dataclasses import dataclass
from recongraph.graph.decision import ReconciliationDecision, DecisionAction
from recongraph.matching.scoring import SignalName

from recongraph.domain.financial.pipeline import AmountInterpretation
from recongraph.domain.financial.amount_projection import ProjectedAmountSimilarity

@dataclass(frozen=True)
class EvidenceSummary:
    """A snapshot of the core signals that drove the score."""
    reference_score: float | None
    amount_interpretation: AmountInterpretation | None
    amount_projection: ProjectedAmountSimilarity | None
    temporal_score: float | None
    entity_score: float | None
    tax_identity_score: float | None

@dataclass(frozen=True)
class DecisionExplanation:
    """The complete, auditable explanation of a reconciliation decision."""
    action: DecisionAction
    policy_rationale: str
    positive_reasons: tuple[str, ...]
    limiting_factors: tuple[str, ...]
    ambiguity_context: str | None
    evidence_summary: EvidenceSummary | None

class ExplanationBuilder:
    """Translates mathematical evaluations and decisions into human-readable explanations."""
    
    def build(self, decision: ReconciliationDecision) -> DecisionExplanation:
        if decision.action == DecisionAction.NO_MATCH:
            return DecisionExplanation(
                action=decision.action,
                policy_rationale=decision.rationale,
                positive_reasons=(),
                limiting_factors=("No mathematically eligible hypotheses generated.",),
                ambiguity_context=None,
                evidence_summary=None
            )
            
        hypothesis = decision.selected_hypothesis
        ambiguity_context = None
        
        if decision.action == DecisionAction.REVIEW_AMBIGUOUS:
            if len(decision.competitors) >= 2:
                top_1 = decision.competitors[0]
                top_2 = decision.competitors[1]
                ambiguity_context = f"Competitor was only {top_1.score - top_2.score:.3f} points behind."
                hypothesis = top_1
        
        if not hypothesis:
            return DecisionExplanation(
                action=decision.action,
                policy_rationale=decision.rationale,
                positive_reasons=(),
                limiting_factors=(),
                ambiguity_context=ambiguity_context,
                evidence_summary=None
            )

        signals = hypothesis.supporting_evidence.get("signals", {})
        metadata = hypothesis.supporting_evidence.get("metadata", {})
        amount_meta = metadata.get(SignalName.AMOUNT, {})
        
        summary = EvidenceSummary(
            reference_score=signals.get(SignalName.REFERENCE),
            amount_interpretation=amount_meta.get("interpretation"),
            amount_projection=amount_meta.get("projection"),
            temporal_score=signals.get(SignalName.TEMPORAL),
            entity_score=signals.get(SignalName.ENTITY),
            tax_identity_score=signals.get(SignalName.TAX_IDENTITY)
        )
        
        positives = []
        if summary.amount_interpretation:
            interp = summary.amount_interpretation
            proj = summary.amount_projection
            
            # OBSERVED
            obs = f"OBSERVED: Left amount: {interp.amount_a}. Right amount: {interp.amount_b}. "
            obs += f"Absolute residual: {interp.absolute_difference}. Relative residual: {interp.relative_difference:.2%}. "
            
            if interp.magnitude_relation.value == "LEFT_GREATER":
                obs += "Right amount is lower than left amount. "
            elif interp.magnitude_relation.value == "RIGHT_GREATER":
                obs += "Right amount is higher than left amount. "
            elif interp.magnitude_relation.value == "EQUAL":
                obs += "Amounts are numerically equal. "
                
            obs += f"Currencies are {interp.currency_relation.value}. "
            obs += f"Signs are {interp.sign_relation.value}."
            
            # COMPATIBILITY
            compat = []
            if interp.compatibility_flags:
                compat.append("COMPATIBILITY: The numeric relationship is compatible with: " + 
                              ", ".join(f.value for f in interp.compatibility_flags) + ".")
                              
            # NOT ESTABLISHED
            not_est = "NOT ESTABLISHED: Amount evidence alone does not establish financial causality or settlement."
            
            # LEGACY PROJECTION
            legacy = ""
            if proj:
                legacy = f"LEGACY PROJECTION: Projected amount similarity: {proj.similarity}. Projection policy: {proj.projection_version}."
                if proj.warnings:
                    legacy += f" Warnings: {', '.join(proj.warnings)}."
            
            reason_parts = [obs]
            if compat:
                reason_parts.extend(compat)
            reason_parts.append(not_est)
            if legacy:
                reason_parts.append(legacy)
                
            positives.append("\n".join(reason_parts))
        if summary.reference_score is not None and summary.reference_score >= 0.8:
            positives.append("Strong reference match on a distinct identifier.")
        if summary.entity_score is not None and summary.entity_score >= 0.8:
            positives.append("Vendor identities are highly similar.")
        if summary.temporal_score is not None and summary.temporal_score == 1.0:
            positives.append("Dates match perfectly.")
            
        limits = []
        if hypothesis.violations:
            for v in sorted(list(hypothesis.violations)):
                limits.append(f"Semantic violation: {v}")
                
        if summary.amount_interpretation is None:
            limits.append("Amount evidence unavailable.")
            
        if summary.temporal_score is not None and summary.temporal_score < 0.5:
            limits.append("Dates are far apart.")
        elif summary.temporal_score is None:
            limits.append("Date evidence unavailable.")
            
        if summary.reference_score is None:
            limits.append("No reference provided to match.")

        return DecisionExplanation(
            action=decision.action,
            policy_rationale=decision.rationale,
            positive_reasons=tuple(positives),
            limiting_factors=tuple(limits),
            ambiguity_context=ambiguity_context,
            evidence_summary=summary
        )
