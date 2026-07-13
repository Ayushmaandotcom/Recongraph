import pytest
from datetime import date
from recongraph.benchmark.runner import BenchmarkRunner
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.matching.reference_evidence import ReferenceCorpusProfile
from recongraph.graph.decision import DecisionPolicy

def test_benchmark_runner():
    p1 = PurchaseRecord(record_id="p1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    g1 = GSTRecord(record_id="g1", amount=100.0, record_date=date(2023,1,1), reference="INV1", vendor_name="A", tax_identity="TAX1")
    
    corpus_profile = ReferenceCorpusProfile(
        reference_count=1,
        normalized_reference_frequency={"inv1": 1},
        numeric_token_document_frequency={"1": 1}
    )
    decision_policy = DecisionPolicy(auto_match_threshold=0.95, ambiguity_margin=0.05)
    
    runner = BenchmarkRunner("DS-TEST", [p1], [g1], corpus_profile, decision_policy)
    report = runner.run()
    
    assert report.dataset_metadata.dataset_id == "DS-TEST"
    assert report.dataset_metadata.purchase_count == 1
    assert report.search_statistics.components_extracted == 1
    assert report.search_statistics.candidate_edges == 1
    assert sum(report.decision_statistics.__dict__.values()) == 1
    assert report.timing_statistics.total_runtime_ms > 0
    assert sum(report.confidence_distribution.bins.values()) == 2
