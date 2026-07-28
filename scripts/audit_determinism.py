import sys
import random
from pathlib import Path
from datetime import date
from decimal import Decimal

# Ensure src is in python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionMode
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider,
    VendorEvidenceProvider,
    ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def test_determinism():
    print("Running Phase F: Determinism Audit...")
    
    config = ReconGraphConfig(decision_config=DecisionConfig(decision_mode=DecisionMode.FUSION))
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'), 
        interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
    )
    ref_context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=0, normalized_reference_frequency={}, numeric_token_document_frequency={}), 
        policy=ReferenceEvidencePolicy()
    )
    
    providers = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(ref_context),
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider()
    ]
    
    engine = ReconGraphEngine(config=config, providers=providers)
    
    # We will generate a base set of candidates.
    purchase = PurchaseRecord(
        record_id="P-001",
        vendor_name="Determinism Test Pvt Ltd",
        reference="INV-999",
        amount=Decimal("15000.00"),
        record_date=date(2026, 1, 15),
        tax_identity="07ABCDE1234F1Z2"
    )
    
    gsts = [
        GSTRecord(
            record_id=f"G-{i}",
            vendor_name=f"DETERMINISM TEST PVT LTD {i}",
            reference="INV-999" if i == 0 else f"INV-{i}",
            amount=Decimal("15000.00") if i == 0 else Decimal(f"{1000 * i}.00"),
            record_date=date(2026, 1, 15),
            tax_identity="07ABCDE1234F1Z2"
        )
        for i in range(5)
    ]
    
    trace_ids = set()
    packet_hashes = set()
    
    run_hashes = []
    
    for run in range(10):
        # Randomize input order
        shuffled_gsts = list(gsts)
        random.shuffle(shuffled_gsts)
        
        result = engine.reconcile([purchase], shuffled_gsts)
        
        current_run_trace_ids = set()
        current_run_packet_hashes = set()
        
        for trace in result.traces:
            current_run_trace_ids.add(trace.trace_id)
            
        for packet in result.review_packets:
            current_run_packet_hashes.add((packet.action.value, tuple(sorted(packet.competitors))))
            
        for match in result.auto_matches:
            current_run_packet_hashes.add((match.action.value, tuple(sorted(match.competitors))))
            
        run_hashes.append((frozenset(current_run_trace_ids), frozenset(current_run_packet_hashes)))
        
    print(f"Executed 10 randomized runs.")
    unique_outcomes = set(run_hashes)
    print(f"Unique Outcomes: {len(unique_outcomes)}")
    
    assert len(unique_outcomes) == 1, "Determinism failed! Different outcomes across runs."
    
    print("SUCCESS: Engine is strictly deterministic.")

if __name__ == "__main__":
    test_determinism()
