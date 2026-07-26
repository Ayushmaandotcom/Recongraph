import pytest
from decimal import Decimal
from datetime import date
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine
from recongraph.graph.decision import DecisionAction
from recongraph.graph.differential import DifferenceType
from recongraph.plugins.provider import EvidenceProvider, EvidenceContribution
from recongraph.candidate_generation.blockers import Blocker, TaxIdentityBlocker
from recongraph.matching.scoring import SignalName

from typing import Sequence
class DummyProvider(EvidenceProvider):
    def __init__(self, name: str, score: float):
        self.name = name
        self.score_value = score
        
    def get_name(self) -> str:
        return self.name
        
    def get_blockers(self) -> list[Blocker]:
        return [TaxIdentityBlocker()]
        
    def evaluate(self, purchases: Sequence[PurchaseRecord], gsts: Sequence[GSTRecord]) -> EvidenceContribution:
        return EvidenceContribution(
            provider_name=self.name,
            score=self.score_value
        )

@pytest.fixture
def test_engine():
    config = ReconGraphConfig(
        decision_config=DecisionConfig(
            decision_mode=DecisionMode.SHADOW
        )
    )
    providers = [
        DummyProvider(SignalName.TAX_IDENTITY, 1.0),
        DummyProvider(SignalName.ENTITY, 1.0),
        DummyProvider(SignalName.AMOUNT, 1.0),
        DummyProvider(SignalName.TEMPORAL, 1.0),
        DummyProvider(SignalName.REFERENCE, 1.0)
    ]
    return ReconGraphEngine(config=config, providers=providers)

def test_shadow_evaluation_baseline_match(test_engine):
    """
    Baseline Case: Clean Exact Match.
    Both engines should return AUTO_MATCH, producing EQUIVALENT classification.
    """
    purchases = [PurchaseRecord(record_id="P1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100.0"), record_date=date(2023, 1, 1))]
    gsts = [GSTRecord(record_id="G1", vendor_name="Acme Corp", tax_identity="GST123", reference=None, amount=Decimal("100.0"), record_date=date(2023, 1, 1))]
    
    result = test_engine.reconcile(purchases, gsts)
    
    assert len(result.differential_results) == 1
    diff = result.differential_results[0]
    
    assert diff.legacy_decision == DecisionAction.AUTO_MATCH
    assert diff.fusion_decision == DecisionAction.AUTO_MATCH
    assert diff.classification == DifferenceType.EQUIVALENT

def test_shadow_evaluation_adversarial_contradiction():
    """
    Adversarial Case: Tax Match, but Vendor Name strongly contradicts.
    """
    config = ReconGraphConfig(
        decision_config=DecisionConfig(
            decision_mode=DecisionMode.SHADOW
        )
    )
    providers = [
        DummyProvider(SignalName.TAX_IDENTITY, 1.0),
        DummyProvider(SignalName.ENTITY, 0.0), # contradiction
        DummyProvider(SignalName.AMOUNT, 1.0),
        DummyProvider(SignalName.TEMPORAL, 1.0),
        DummyProvider(SignalName.REFERENCE, 1.0)
    ]
    engine = ReconGraphEngine(config=config, providers=providers)
    
    purchases = [PurchaseRecord(record_id="P2", vendor_name="Acme Corp", tax_identity="GST999", reference=None, amount=Decimal("100.0"), record_date=date(2023, 1, 1))]
    gsts = [GSTRecord(record_id="G2", vendor_name="Zenith LLC", tax_identity="GST999", reference=None, amount=Decimal("100.0"), record_date=date(2023, 1, 1))]
    
    result = engine.reconcile(purchases, gsts)
    
    assert len(result.differential_results) == 1
    diff = result.differential_results[0]
    
    assert diff.legacy_decision in (DecisionAction.REVIEW_WEAK, DecisionAction.AUTO_MATCH)
    
def test_production_safety_in_shadow_mode(test_engine):
    """
    Verify that an exception in Fusion Decision Engine during SHADOW mode 
    is caught and does not block Legacy results.
    """
    purchases = [PurchaseRecord(record_id="P3", vendor_name="Test", tax_identity="GST000", reference=None, amount=Decimal("0.0"), record_date=date(2023, 1, 1))]
    gsts = [GSTRecord(record_id="G3", vendor_name="Test", tax_identity="GST000", reference=None, amount=Decimal("0.0"), record_date=date(2023, 1, 1))]
    
    import recongraph.graph.propagation
    original_propagate = recongraph.graph.propagation.SemanticPropagator.propagate
    
    def boom(*args, **kwargs):
        raise ValueError("Fusion engine crashed!")
        
    recongraph.graph.propagation.SemanticPropagator.propagate = boom
    
    try:
        result = test_engine.reconcile(purchases, gsts)
        assert len(result.auto_matches) + len(result.review_packets) == 1
        assert len(result.differential_results) == 0
    finally:
        recongraph.graph.propagation.SemanticPropagator.propagate = original_propagate
