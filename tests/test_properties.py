from decimal import Decimal
import datetime
from hypothesis import given, settings, strategies as st

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.plugins.semantic_providers import SemanticEvidenceProvider
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile

def make_engine():
    context = ReferenceEvidenceContext(
        profile=ReferenceCorpusProfile(reference_count=1, normalized_reference_frequency={"inv1": 1}, numeric_token_document_frequency={"1": 1}),
        policy=ReferenceEvidencePolicy()
    )
    vendor_context = VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )
    return ReconGraphEngine(
        config=ReconGraphConfig(),
        providers=[
            FinancialEvidenceProvider(0.05),
            TemporalEvidenceProvider(30),
            TaxEvidenceProvider(),
            VendorEvidenceProvider(vendor_context),
            ReferenceEvidenceProvider(context)
        ]
    )

@st.composite
def purchase_strategy(draw):
    return PurchaseRecord(
        record_id=draw(st.text(min_size=1, max_size=10)),
        vendor_name=draw(st.text(min_size=1, max_size=20) | st.none()),
        reference=draw(st.text(min_size=1, max_size=10) | st.none()),
        amount=Decimal(draw(st.integers(min_value=1, max_value=100000))),
        record_date=draw(st.dates(min_value=datetime.date(2020, 1, 1), max_value=datetime.date(2025, 12, 31))),
        tax_identity=draw(st.text(min_size=10, max_size=15) | st.none()),
        net_amount=None, tax_amount=None
    )

@st.composite
def gst_strategy(draw):
    return GSTRecord(
        record_id=draw(st.text(min_size=1, max_size=10)),
        vendor_name=draw(st.text(min_size=1, max_size=20) | st.none()),
        reference=draw(st.text(min_size=1, max_size=10) | st.none()),
        amount=Decimal(draw(st.integers(min_value=1, max_value=100000))),
        record_date=draw(st.dates(min_value=datetime.date(2020, 1, 1), max_value=datetime.date(2025, 12, 31))),
        tax_identity=draw(st.text(min_size=10, max_size=15) | st.none()),
        net_amount=None, tax_amount=None
    )

@settings(max_examples=50)
@given(purchase_strategy(), gst_strategy())
def test_score_and_coverage_bounds(p: PurchaseRecord, g: GSTRecord):
    # Ensure they have different IDs to avoid collision if they happen to draw the same
    if p.record_id == g.record_id:
        g = GSTRecord(
            record_id=g.record_id + "_g", vendor_name=g.vendor_name, reference=g.reference,
            amount=g.amount, record_date=g.record_date, tax_identity=g.tax_identity,
            net_amount=g.net_amount, tax_amount=g.tax_amount
        )

    engine = make_engine()
    result = engine.reconcile([p], [g])
    
    if result.auto_matches:
        for match in result.auto_matches:
            assert 0.0 <= match.confidence_score <= 1.0
            for trace in match.sub_graph.nodes.values():
                assert 0.0 <= trace.evidence.relationship.score <= 1.0
                assert 0.0 <= trace.evidence.relationship.coverage <= 1.0

@settings(max_examples=20)
@given(
    st.lists(purchase_strategy(), min_size=1, max_size=3, unique_by=lambda x: x.record_id),
    st.lists(gst_strategy(), min_size=1, max_size=3, unique_by=lambda x: x.record_id)
)
def test_permutation_invariance(ps: list[PurchaseRecord], gs: list[GSTRecord]):
    # Ensure no collision between P and G ids
    p_ids = {p.record_id for p in ps}
    for i, g in enumerate(gs):
        if g.record_id in p_ids:
            gs[i] = GSTRecord(
                record_id=g.record_id + "_g", vendor_name=g.vendor_name, reference=g.reference,
                amount=g.amount, record_date=g.record_date, tax_identity=g.tax_identity,
                net_amount=g.net_amount, tax_amount=g.tax_amount
            )

    engine = make_engine()
    res1 = engine.reconcile(ps, gs)
    
    ps_rev = list(reversed(ps))
    gs_rev = list(reversed(gs))
    res2 = engine.reconcile(ps_rev, gs_rev)
    
    def extract_matches(result):
        return {
            (frozenset(p.record_id for p in match.purchases), frozenset(g.record_id for g in match.gsts))
            for match in result.auto_matches
        }
    
    assert extract_matches(res1) == extract_matches(res2)
