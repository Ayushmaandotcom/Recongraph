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
        matches = set()
        for match in result.auto_matches:
            if match.selected_hypothesis:
                p_nodes = {n.replace("urn:recongraph:purchase:", "") for n in match.selected_hypothesis.hypothesis.matched_nodes if "purchase" in n}
                g_nodes = {n.replace("urn:recongraph:gst:", "") for n in match.selected_hypothesis.hypothesis.matched_nodes if "gst" in n}
                matches.add((frozenset(p_nodes), frozenset(g_nodes)))
        return matches
    
    assert extract_matches(res1) == extract_matches(res2)
