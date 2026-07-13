from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.candidate_generation.blockers import (
    ExactAmountBlocker,
    TaxIdentityBlocker,
    ReferenceTokenBlocker,
)
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TaxEvidenceProvider, ReferenceEvidenceProvider
from recongraph.candidate_generation.index import InvertedIndex
from recongraph.candidate_generation.generator import CandidateGenerator
from recongraph.matching.reference_evidence import ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy

def test_exact_amount_blocker():
    blocker = ExactAmountBlocker()
    record = PurchaseRecord(record_id="dummy_p", vendor_name="A", reference="B", amount=150.00, record_date=date(2026, 1, 1), tax_identity="AB123")
    keys = blocker.extract_keys(record)
    assert keys == frozenset(["AMT:150.00"])

def test_tax_identity_blocker():
    blocker = TaxIdentityBlocker()
    record = PurchaseRecord(record_id="dummy_p", vendor_name="A", reference="B", amount=150.00, record_date=date(2026, 1, 1), tax_identity=" AB123 ")
    keys = blocker.extract_keys(record)
    assert keys == frozenset(["TAX:AB123"])

def test_reference_token_blocker_statistical():
    # Profile where '874219' is rare (freq=1/100 -> mag=0.9)
    # and '001' is common (freq=81/100 -> mag=0.1)
    prof = ReferenceCorpusProfile(
        reference_count=100,
        normalized_reference_frequency={"inv874219": 1, "inv001": 81, "dummy": 18},
        numeric_token_document_frequency={"874219": 1, "001": 81}
    )
    # Rarity threshold 0.8
    blocker = ReferenceTokenBlocker(profile=prof, rarity_threshold=0.8)
    
    # Rare token test
    record_rare = PurchaseRecord(record_id="dummy_p", vendor_name="A", reference="INV-874219", amount=150.00, record_date=date(2026, 1, 1), tax_identity="AB123")
    keys_rare = blocker.extract_keys(record_rare)
    assert "REF_NORM:inv874219" in keys_rare
    assert "REF_TOK:874219" in keys_rare
    
    # Common token test
    record_common = PurchaseRecord(record_id="dummy_p", vendor_name="A", reference="INV-001", amount=150.00, record_date=date(2026, 1, 1), tax_identity="AB123")
    keys_common = blocker.extract_keys(record_common)
    assert "REF_NORM:inv001" not in keys_common
    assert "REF_TOK:001" not in keys_common
    assert not keys_common

def test_candidate_generator_reduction():
    prof = ReferenceCorpusProfile(
        reference_count=1000,
        normalized_reference_frequency={"inv123": 1, "inv999": 1, "dummy": 998},
        numeric_token_document_frequency={"123": 1, "999": 1}
    )
    providers = [
        FinancialEvidenceProvider(), 
        TaxEvidenceProvider(),
        ReferenceEvidenceProvider(ReferenceEvidenceContext(prof, ReferenceEvidencePolicy()))
    ]
    generator = CandidateGenerator(providers)
    
    # 1 Purchase
    purchases = [
        PurchaseRecord(record_id="dummy_p", vendor_name="A", reference="INV-123", amount=500.0, record_date=date(2026, 1, 1), tax_identity="TAX-A")
    ]
    
    # 3 GST Records
    gst_records = [
        # Match by Reference
        GSTRecord(record_id="dummy_g", vendor_name="A", reference="INV-123", amount=999.0, record_date=date(2026, 1, 1), tax_identity="TAX-B"),
        # Match by Amount
        GSTRecord(record_id="dummy_g", vendor_name="B", reference="INV-999", amount=500.0, record_date=date(2026, 1, 1), tax_identity="TAX-C"),
        # No Match (Should be filtered out)
        GSTRecord(record_id="dummy_g", vendor_name="C", reference="INV-888", amount=100.0, record_date=date(2026, 1, 1), tax_identity="TAX-D"),
    ]
    
    edges = list(generator.generate(purchases, gst_records))
    
    assert len(edges) == 2
    
    # Find the edges
    edge_ref = next(e for e in edges if e.gst_record.reference == "INV-123")
    assert "REF_TOK:123" in edge_ref.shared_blocking_keys
    
    edge_amt = next(e for e in edges if e.gst_record.reference == "INV-999")
    assert "AMT:500.00" in edge_amt.shared_blocking_keys
