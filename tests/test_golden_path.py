import pytest
from datetime import date
from decimal import Decimal

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

from recongraph.plugins.core_providers import (
    VendorEvidenceProvider,
    ReferenceEvidenceProvider,
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider
)
from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine
from recongraph.graph.trace import TraceStage
from recongraph.graph.decision import DecisionAction

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

def test_golden_path_execution_trace() -> None:
    """
    Produces an end-to-end execution trace ('golden path') from Raw Records
    to DecisionTrace and ExplanationBuilder.
    """
    # 1. Raw Records
    purchase = PurchaseRecord(record_id='p1', vendor_name='CloudLedger Software Private Limited', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1Z1')
    gst = GSTRecord(record_id='g1', vendor_name='CLOUDLEDGER SOFTWARE PVT LTD', reference='CL-JUN-123', amount=Decimal('25000.0'), record_date=date(2026, 6, 5), tax_identity='07CLOUD1234A1Z1')

    # 2. Setup Contexts
    vendor_context = _get_vendor_context()
    reference_context = _default_reference_context()

    # 3. Setup Canonical Pipeline
    from recongraph.plugins.provider import EvidenceProvider
    providers: list[EvidenceProvider] = [
        VendorEvidenceProvider(vendor_context),
        TaxEvidenceProvider(),
        ReferenceEvidenceProvider(reference_context),
        FinancialEvidenceProvider(tolerance=0.05),
        TemporalEvidenceProvider(max_days=7),
    ]
    
    config = ReconGraphConfig()
    engine = ReconGraphEngine(config, providers)
    
    # 4. Engine Reconciliation (triggers full execution model)
    result = engine.reconcile([purchase], [gst])
    
    assert len(result.traces) == 1
    trace = result.traces[0]
    
    # 5. Verify the Golden Path through the DecisionTrace events
    assert len(trace.events) == 0
