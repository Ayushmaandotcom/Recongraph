import pytest
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.config import ReconGraphConfig
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, ReferenceEvidenceProvider, VendorEvidenceProvider, TaxEvidenceProvider
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.engine import ReconGraphEngine
from recongraph.graph.decision import DecisionAction

def test_engine_reconcile():
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")

    config = ReconGraphConfig()
    context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=1, normalized_reference_frequency={"inv1": 1}, numeric_token_document_frequency={"1": 1}),
        policy=ReferenceEvidencePolicy()
    )
    providers = [
        FinancialEvidenceProvider(), 
        TemporalEvidenceProvider(), 
        TaxEvidenceProvider(),
        VendorEvidenceProvider(),
        ReferenceEvidenceProvider(context)
    ]
    
    engine = ReconGraphEngine(config, providers)
    result = engine.reconcile([p1], [g1])
    
    assert result.engine_version == "1.0.0"
    assert len(result.traces) == 1
    trace = result.traces[0]
    
    assert trace.engine_version == "1.0.0"
    assert trace.config_hash is not None
    assert len(trace.events) == 1
    
    # Assert serializability
    trace_dict = trace.to_dict()
    assert trace_dict["engine_version"] == "1.0.0"
    assert len(trace_dict["events"]) == 1
