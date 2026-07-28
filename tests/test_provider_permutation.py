import pytest
import itertools
from datetime import date
from decimal import Decimal

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.hypotheses import Hypothesis

from recongraph.plugins.core_providers import (
    VendorEvidenceProvider,
    ReferenceEvidenceProvider,
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider
)

from recongraph.graph.evaluator import HypothesisEvaluator

from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine

def _get_vendor_context() -> VendorIdentityContext:
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'),
        interpreter_policy_version='1.0.0',
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )

def _default_reference_context() -> ReferenceEvidenceContext:
    prof = ReferenceCorpusProfile(
        reference_count=1000, 
        normalized_reference_frequency={'dummy': 998, 'inv1042': 2}, 
        numeric_token_document_frequency={'2026': 100, '1042': 2}
    )
    return ReferenceEvidenceContext(profile=prof, policy=ReferenceEvidencePolicy())

def test_evidence_provider_order_independence() -> None:
    purchase = PurchaseRecord(record_id='p1', vendor_name='CloudLedger Software Private Limited', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1ZF')
    gst = GSTRecord(record_id='g1', vendor_name='CLOUDLEDGER SOFTWARE PVT LTD', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1ZF')

    vendor_context = _get_vendor_context()
    reference_context = _default_reference_context()

    from recongraph.plugins.provider import EvidenceProvider
    all_providers: list[EvidenceProvider] = [
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(reference_context),
        FinancialEvidenceProvider(tolerance=0.05),
        TemporalEvidenceProvider(max_days=365),
        TaxEvidenceProvider()
    ]
    
    permutations = list(itertools.permutations(all_providers))
    assert len(permutations) == 120
    
    config = ReconGraphConfig()
    
    baseline_trace_id = None
    baseline_trace_hash = None
    
    for idx, permuted_providers in enumerate(permutations):
        engine = ReconGraphEngine(config, permuted_providers)
        
        result = engine.reconcile([purchase], [gst])
        
        assert len(result.traces) == 1
        trace = result.traces[0]
        
        # We check order independence
        if idx == 0:
            baseline_trace_id = trace.trace_id
        else:
            assert trace.trace_id == baseline_trace_id
