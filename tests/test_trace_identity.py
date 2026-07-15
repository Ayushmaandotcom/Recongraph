import pytest
from datetime import date
from decimal import Decimal
import uuid
from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord

def _get_vendor_context():
    return VendorIdentityContext(corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'), interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01)

def _default_context():
    prof = ReferenceCorpusProfile(reference_count=1000, normalized_reference_frequency={'dummy': 998, 'inv1042': 2}, numeric_token_document_frequency={'2026': 100, '1042': 2})
    return ReferenceEvidenceContext(profile=prof, policy=ReferenceEvidencePolicy())

def test_trace_determinism():
    config = ReconGraphConfig()
    vendor_ctx = _get_vendor_context()
    ref_ctx = _default_context()
    providers = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_ctx),
        ReferenceEvidenceProvider(ref_ctx)
    ]
    engine = ReconGraphEngine(config, providers)
    
    p = PurchaseRecord("p1", "Vendor", "ref", Decimal("100"), date(2026,1,1), "TAX123")
    g = GSTRecord("g1", "Vendor", "ref", Decimal("100"), date(2026,1,1), "TAX123")
    
    result1 = engine.reconcile([p], [g])
    result2 = engine.reconcile([p], [g])
    
    assert len(result1.traces) == 1
    assert len(result2.traces) == 1
    
    assert result1.traces[0].trace_id == result2.traces[0].trace_id

