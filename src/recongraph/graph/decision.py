from dataclasses import dataclass
from enum import StrEnum
from collections.abc import Iterable
from recongraph.graph.hypotheses import EvaluatedHypothesis, EligibilityStatus

class DecisionAction(StrEnum):
    AUTO_MATCH = "auto_match"
    REVIEW_AMBIGUOUS = "review_ambiguous"
    REVIEW_WEAK = "review_weak"
    REVIEW_INSUFFICIENT_EVIDENCE = "review_insufficient_evidence"
    NO_MATCH = "no_match"

@dataclass(frozen=True)
class ReconciliationDecision:
    action: DecisionAction
    selected_hypothesis: EvaluatedHypothesis | None
    competitors: tuple[EvaluatedHypothesis, ...]
    rationale: str

@dataclass(frozen=True)
class DecisionPolicy:
    auto_match_threshold: float = 0.95
    ambiguity_margin: float = 0.05
    # 0.80 is a conservative V1 operational policy, not a scientifically 
    # proven sufficiency boundary. It requires eventual calibration against 
    # a labelled reconciliation corpus. Coverage is a policy-weight completeness 
    # ratio; it is not probability, statistical confidence, or certainty.
    minimum_coverage_threshold: float = 0.80

class DecisionEngine:
    """
    Consumes evaluated hypotheses and decides what action the 
    reconciliation system should take based on an injected policy.
    It does not recompute scores or query the graph.
    """
    def __init__(self, policy: DecisionPolicy | None = None):
        self.policy = policy or DecisionPolicy()

    def decide(self, evaluated_hypotheses: Iterable[EvaluatedHypothesis]) -> ReconciliationDecision:
        eligible = []
        ineligible = []
        for h in evaluated_hypotheses:
            # Only strictly ELIGIBLE hypotheses can be considered for matching
            if h.eligibility == EligibilityStatus.ELIGIBLE:
                eligible.append(h)
            else:
                ineligible.append(h)

        all_hypotheses = tuple(eligible + ineligible)

        if not eligible:
            return ReconciliationDecision(
                action=DecisionAction.NO_MATCH,
                selected_hypothesis=None,
                competitors=all_hypotheses,
                rationale="No mathematically eligible hypotheses generated."
            )

        # Rank eligible hypotheses by score (descending)
        eligible.sort(key=lambda x: x.score, reverse=True)
        
        top_hypothesis = eligible[0]
        competitors = tuple([h for h in all_hypotheses if h is not top_hypothesis])
        
        # Check for ambiguity (Competitive landscape)
        if len(eligible) > 1:
            runner_up = eligible[1]
            spread = top_hypothesis.score - runner_up.score
            if spread <= self.policy.ambiguity_margin:
                return ReconciliationDecision(
                    action=DecisionAction.REVIEW_AMBIGUOUS,
                    selected_hypothesis=None, # Explicitly refuse to guess
                    competitors=all_hypotheses,
                    rationale=f"Score spread ({spread:.3f}) is within ambiguity margin ({self.policy.ambiguity_margin})."
                )

        # Check against automation threshold
        if top_hypothesis.score >= self.policy.auto_match_threshold:
            if top_hypothesis.coverage >= self.policy.minimum_coverage_threshold:
                return ReconciliationDecision(
                    action=DecisionAction.AUTO_MATCH,
                    selected_hypothesis=top_hypothesis,
                    competitors=competitors,
                    rationale=f"Dominant hypothesis score ({top_hypothesis.score:.3f}) and coverage ({top_hypothesis.coverage:.3f}) cleared the auto-match threshold."
                )
            else:
                return ReconciliationDecision(
                    action=DecisionAction.REVIEW_WEAK,
                    selected_hypothesis=top_hypothesis,
                    competitors=competitors,
                    rationale=f"Dominant hypothesis score ({top_hypothesis.score:.3f}) is high, but coverage ({top_hypothesis.coverage:.3f}) is below minimum threshold ({self.policy.minimum_coverage_threshold})."
                )
        else:
            return ReconciliationDecision(
                action=DecisionAction.REVIEW_WEAK,
                selected_hypothesis=top_hypothesis,
                competitors=competitors,
                rationale=f"Dominant hypothesis score ({top_hypothesis.score:.3f}) fell below the auto-match threshold ({self.policy.auto_match_threshold})."
            )

from recongraph.graph.fusion_result import FusionResult

class FusionDecisionEngine:
    """
    Translates a descriptive FusionResult into an actionable DecisionAction.
    Used in SHADOW and FUSION modes.
    """
    def decide(self, fusion_result: FusionResult, fallback_hypothesis: EvaluatedHypothesis | None = None) -> ReconciliationDecision:
        if fusion_result.contradictions:
            # If there are explicit contradictions, it's ambiguous
            action = DecisionAction.REVIEW_AMBIGUOUS
        elif not fusion_result.independent_support and not fusion_result.derived_support:
            action = DecisionAction.NO_MATCH
        elif len(fusion_result.independent_support) >= 2:
            action = DecisionAction.AUTO_MATCH
        else:
            action = DecisionAction.REVIEW_WEAK
            
        return ReconciliationDecision(
            action=action,
            selected_hypothesis=fallback_hypothesis,
            competitors=(),
            rationale="Decision derived via Semantic Fusion Engine"
        )
