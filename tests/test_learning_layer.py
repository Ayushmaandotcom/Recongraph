import pytest
from recongraph.learning.vendor_learner import VendorAliasLearner, AliasInsight
from recongraph.learning.calibration_learner import CalibrationLearner, CalibrationInsight
from recongraph.learning.manager import LearningManager
from recongraph.graph.review import ReviewPacket, ReviewOutcome
from recongraph.graph.decision import DecisionAction
from recongraph.domain.records import PurchaseRecord, GSTRecord
from datetime import date
from decimal import Decimal
from recongraph.graph.hypotheses import EvaluatedHypothesis
from recongraph.contrib.kernel.assertions import EvidenceAssertion, AssertionPolarity, EvidenceAncestryRef
from recongraph.contrib.kernel.claims import ClaimId, ClaimSemanticVersion, ClaimDescriptor, ClaimSymmetry
from recongraph.contrib.kernel.authority import AuthorityDescriptor, AuthorityBasisId
from recongraph.contrib.kernel.scopes import Proposition, ScopeKind, SubjectRef, PropositionSubject
from recongraph.contrib.kernel.identity import KernelIdentityRef, IdentityDomainId, IdentitySchemaId, IdentityDigest

def create_mock_packet(vendor_score: float, action: DecisionAction = DecisionAction.REVIEW_AMBIGUOUS) -> ReviewPacket:
    p = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023, 1, 1), vendor_name="Acme Corp", reference="ref", tax_identity="id")
    g = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023, 1, 1), vendor_name="Acme Corporation", reference="ref", tax_identity="id")
    
    # create assertion
    assertion = EvidenceAssertion(
        proposition=Proposition(
            claim=ClaimDescriptor(
                claim_id=ClaimId("vendor.alias_match"),
                semantic_version=ClaimSemanticVersion(1),
                symmetry=ClaimSymmetry.SYMMETRIC,
                allowed_scope_kinds=frozenset([ScopeKind.RECORD_PAIR])
            ),
            subject=PropositionSubject(
                claim_id="vendor.alias_match",
                claim_semantic_version=1,
                kind=ScopeKind.RECORD_PAIR,
                left=(SubjectRef(urn="urn:g1"),),
                right=(SubjectRef(urn="urn:p1"),)
            )
        ),
        polarity=AssertionPolarity.SUPPORT,
        magnitude=vendor_score,
        authority=AuthorityDescriptor(basis=AuthorityBasisId("vendor_model")),
        ancestry=EvidenceAncestryRef(
            identity=KernelIdentityRef(
                domain=IdentityDomainId("recongraph.observation_occurrence"), 
                schema=IdentitySchemaId("recongraph.observation_occurrence.v1"), 
                digest=IdentityDigest("sha256:0000000000000000000000000000000000000000000000000000000000000000")
            )
        )
    )
    
    from recongraph.graph.hypotheses import EvaluatedHypothesis, Hypothesis, EligibilityStatus
    from recongraph.matching.scoring import ScoringEvidence
    
    hypothesis = EvaluatedHypothesis(
        hypothesis=Hypothesis(component_nodes=frozenset(), proposed_edges=frozenset()),
        score=vendor_score,
        coverage=1.0,
        eligibility=EligibilityStatus.ELIGIBLE,
        supporting_evidence=ScoringEvidence(assertions=(assertion,)),
        violations=frozenset()
    )
    
    return ReviewPacket(
        packet_id="pkt1",
        action=action,
        purchases=(p,),
        gsts=(g,),
        explanation=None,
        competitors=(hypothesis,),
        checklist=()
    )

def test_vendor_alias_learner():
    learner = VendorAliasLearner(vendor_score_threshold=0.5)
    
    # Scenario: Human approves a low score vendor match
    packet = create_mock_packet(vendor_score=0.4)
    outcome = ReviewOutcome(reviewer_id="human1", final_action="APPROVED", comments="Looks like same company")
    
    learner.observe(packet, outcome)
    insights = list(learner.get_insights())
    
    assert len(insights) == 1
    insight = insights[0]
    assert isinstance(insight, AliasInsight)
    assert insight.primary_name == "Acme Corporation"
    assert insight.alias_name == "Acme Corp"
    assert insight.metadata["original_vendor_score"] == 0.4
    
    # Scenario: Human rejects a low score vendor match
    packet2 = create_mock_packet(vendor_score=0.4)
    outcome2 = ReviewOutcome(reviewer_id="human1", final_action="REJECTED", comments="Not the same")
    learner.observe(packet2, outcome2)
    insights2 = list(learner.get_insights())
    assert len(insights2) == 0

def test_calibration_learner():
    learner = CalibrationLearner(sample_threshold=3)
    
    # Send 3 approvals for a low score bucket (0.4)
    for _ in range(3):
        packet = create_mock_packet(vendor_score=0.4) # bucket 4, midpoint 0.45
        outcome = ReviewOutcome(reviewer_id="human1", final_action="APPROVED", comments="")
        learner.observe(packet, outcome)
        
    insights = list(learner.get_insights())
    assert len(insights) == 1
    insight = insights[0]
    assert isinstance(insight, CalibrationInsight)
    assert insight.claim_id == "vendor.alias_match"
    assert insight.empirical_accuracy == 1.0
    assert insight.current_prediction == 0.45
    assert insight.sample_size == 3

def test_learning_manager():
    vendor_learner = VendorAliasLearner()
    calib_learner = CalibrationLearner(sample_threshold=1)
    
    manager = LearningManager([vendor_learner, calib_learner])
    
    packet = create_mock_packet(vendor_score=0.2)
    outcome = ReviewOutcome(reviewer_id="human1", final_action="APPROVED", comments="")
    
    manager.observe(packet, outcome)
    
    insights = manager.extract_insights()
    assert len(insights) == 2
    
    has_alias = False
    has_calib = False
    for ins in insights:
        if isinstance(ins, AliasInsight): has_alias = True
        if isinstance(ins, CalibrationInsight): has_calib = True
        
    assert has_alias and has_calib
