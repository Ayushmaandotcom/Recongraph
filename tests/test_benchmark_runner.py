from decimal import Decimal
import pytest
from datetime import date
from recongraph.benchmark.runner import BenchmarkRunner
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.graph.decision import DecisionPolicy
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider

def _get_vendor_context():
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )

def test_benchmark_runner():
    p1 = PurchaseRecord(record_id="p1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=Decimal("100.0"), record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    corpus_profile = ReferenceCorpusProfile(
        reference_count=1,
        normalized_reference_frequency={"inv1": 1},
        numeric_token_document_frequency={"1": 1}
    )
    
    decision_policy = DecisionPolicy(auto_match_threshold=0.95, ambiguity_margin=0.05)
    
    providers = [
        FinancialEvidenceProvider(), 
        TemporalEvidenceProvider(), 
        TaxEvidenceProvider(),
        VendorEvidenceProvider(_get_vendor_context()),
        ReferenceEvidenceProvider(ReferenceEvidenceContext(corpus_profile, ReferenceEvidencePolicy()))
    ]
    
    runner = BenchmarkRunner("DS-TEST", [p1], [g1], providers, decision_policy)
    report = runner.run()
    
    assert report.dataset_metadata.dataset_id == "DS-TEST"
    assert report.dataset_metadata.purchase_count == 1
    assert report.search_statistics.components_extracted == 1
    assert report.search_statistics.candidate_edges == 1
    assert sum(report.decision_statistics.__dict__.values()) == 1
    assert report.timing_statistics.total_runtime_ms > 0
