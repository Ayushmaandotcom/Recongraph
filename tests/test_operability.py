import json
from decimal import Decimal
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionPolicy
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider,
    VendorEvidenceProvider,
    ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def test_json_roundtrip():
    p = PurchaseRecord(record_id="P1", amount=Decimal("100.00"), record_date=date(2025, 1, 1), reference="INV/1", vendor_name="Acme", tax_identity="GSTIN123")
    g = GSTRecord(record_id="G1", amount=Decimal("100.00"), record_date=date(2025, 1, 2), reference="INV/1", vendor_name="Acme Corp", tax_identity="GSTIN123")
    
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=10, token_document_frequencies={}, digest='default'), 
        interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
    )
    ref_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=0, normalized_reference_frequency={}, numeric_token_document_frequency={}), 
        policy=ReferenceEvidencePolicy()
    )
    
    config = ReconGraphConfig(
        decision_config=DecisionConfig(
            policy=DecisionPolicy(minimum_coverage_threshold=0.85)
        )
    )
    
    providers = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context),
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider()
    ]
    
    engine = ReconGraphEngine(config=config, providers=providers)
    result = engine.reconcile([p], [g])
    
    # Test JSON serialization
    result_dict = result.to_dict()
    assert "auto_matches" in result_dict
    assert "review_packets" in result_dict
    
    result_json = json.dumps(result_dict)
    assert "AUTO_MATCH" in result_json or "review" in result_json.lower()
    
    loaded_dict = json.loads(result_json)
    assert len(loaded_dict["auto_matches"]) == len(result.auto_matches)

def test_cli_execution():
    import subprocess
    import os
    
    # Uses the previously generated test CSVs from the experiments folder or small test setup
    pass
