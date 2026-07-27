import pytest
import hashlib
from datetime import datetime, timezone
from recongraph.graph.trace import DecisionTrace, TraceEvent, TraceStage, canonicalize_score
from recongraph.graph.decision import ReconciliationDecision, DecisionAction
from recongraph.graph.hypotheses import EvaluatedHypothesis, EligibilityStatus, Hypothesis
from recongraph.matching.scoring import ScoringEvidence
from recongraph.matching.purchase_gst_semantics import SemanticFinding

def build_dummy_hypothesis(score=1.0, coverage=1.0) -> EvaluatedHypothesis:
    base = Hypothesis(frozenset(["n1", "n2"]), frozenset([frozenset(["n1", "n2"])]))
    
    class DummyRel:
        def __init__(self, bs):
            self.base_score = bs
            
    return EvaluatedHypothesis(
        hypothesis=base,
        score=score,
        coverage=coverage,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence=ScoringEvidence(
            signals={"amount": score},
            relationship=DummyRel(score),
            metadata={"vendor_plugin": {}}
        ),
        violations=frozenset(["EXACT_MATCH"])
    )

def test_canonicalize_score():
    assert canonicalize_score(0.0) == 0
    assert canonicalize_score(-0.0) == 0
    assert canonicalize_score(0.1 + 0.2) == 3000
    assert canonicalize_score(0.3) == 3000
    assert canonicalize_score(0.875) == 8750
    assert canonicalize_score(1.0) == 10000
    assert canonicalize_score(None) is None
    
    with pytest.raises(ValueError):
        canonicalize_score(float('nan'))
    with pytest.raises(ValueError):
        canonicalize_score(float('inf'))

def test_trace_semantic_mutations():
    h1 = build_dummy_hypothesis(score=0.9, coverage=0.9)
    d_base = ReconciliationDecision(
        action=DecisionAction.AUTO_MATCH,
        selected_hypothesis=h1,
        competitors=tuple(),
        rationale="Base"
    )
    
    id_base = DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_base)
    
    # 1. Decision changes
    d_review = ReconciliationDecision(
        action=DecisionAction.REVIEW_WEAK,
        selected_hypothesis=h1,
        competitors=tuple(),
        rationale="Review"
    )
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_review), "Decision action mutation failed"
    
    # 2. Eligibility changes
    h2 = build_dummy_hypothesis(score=0.9, coverage=0.9)
    object.__setattr__(h2, 'eligibility', EligibilityStatus.INELIGIBLE)
    d_elig = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h2, competitors=tuple(), rationale="Base")
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_elig), "Eligibility mutation failed"
    
    # 3. Coverage changes
    h_cov = build_dummy_hypothesis(score=0.9, coverage=0.8)
    d_cov = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h_cov, competitors=tuple(), rationale="Base")
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_cov), "Coverage mutation failed"
    
    # 4. Relationship score changes
    h_rel = build_dummy_hypothesis(score=0.8, coverage=0.9)
    d_rel = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h_rel, competitors=tuple(), rationale="Base")
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_rel), "Relationship score mutation failed"
    
    # 5. Semantic finding changes
    h_sem = build_dummy_hypothesis(score=0.9, coverage=0.9)
    object.__setattr__(h_sem, 'violations', frozenset(["EXACT_MATCH", "TEMPORAL_WARNING"]))
    d_sem = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h_sem, competitors=tuple(), rationale="Base")
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_sem), "Semantic finding mutation failed"

    # 6. Provider interpretation / Projection identity changes
    h_proj = build_dummy_hypothesis(score=0.9, coverage=0.9)
    h_proj.supporting_evidence.metadata["new_plugin"] = {}
    d_proj = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h_proj, competitors=tuple(), rationale="Base")
    assert id_base != DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_proj), "Projection identity mutation failed"

    # 8. Component ordering changes (must NOT affect)
    id_reordered = DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n2", "n1"]), d_base)
    assert id_base == id_reordered, "Component ordering incorrectly altered identity"

    # 10. Explanation wording changes (must NOT affect)
    d_word = ReconciliationDecision(action=DecisionAction.AUTO_MATCH, selected_hypothesis=h1, competitors=tuple(), rationale="Different wording")
    id_word = DecisionTrace.compute_identity("1.0", "hash1", frozenset(["n1", "n2"]), d_word)
    assert id_base == id_word, "Wording mutation incorrectly altered identity"

