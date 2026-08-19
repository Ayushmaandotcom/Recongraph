import pytest
from decimal import Decimal
from datetime import date
from hypothesis import given, settings, strategies as st, HealthCheck

from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import FinancialEvidenceProvider

@st.composite
def record_strategy(draw, is_purchase: bool):
    record_id = draw(st.uuids()).hex
    amount = draw(st.decimals(min_value=0, max_value=1000000, places=2))
    # Keep dates small to avoid extreme outliers
    year = draw(st.integers(min_value=2020, max_value=2025))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))
    rec_date = date(year, month, day)
    
    ref = draw(st.text(min_size=1, max_size=10))
    vendor = draw(st.text(min_size=1, max_size=20))
    tax_id = draw(st.text(min_size=5, max_size=15))
    
    if is_purchase:
        return PurchaseRecord(
            record_id=f"P_{record_id}", 
            amount=amount, 
            record_date=rec_date, 
            reference=ref, 
            vendor_name=vendor, 
            tax_identity=tax_id
        )
    else:
        return GSTRecord(
            record_id=f"G_{record_id}", 
            amount=amount, 
            record_date=rec_date, 
            reference=ref, 
            vendor_name=vendor, 
            tax_identity=tax_id
        )

from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def _get_vendor_context():
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest="1"),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01
    )

def _get_providers():
    corpus_profile = ReferenceCorpusProfile(
        reference_count=1,
        normalized_reference_frequency={"inv1": 1},
        numeric_token_document_frequency={"1": 1}
    )
    return [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(_get_vendor_context()),
        ReferenceEvidenceProvider(ReferenceEvidenceContext(corpus_profile, ReferenceEvidencePolicy()))
    ]

@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    purchases=st.lists(record_strategy(is_purchase=True), max_size=10),
    gsts=st.lists(record_strategy(is_purchase=False), max_size=10)
)
def test_conservation_property(purchases, gsts):
    """
    PROPERTY: Output Record Set == Input Record Set
    No matter what happens during Candidate Generation, Graph Building, 
    Hypothesis Evaluation, or Decision Routing, NO RECORD IS EVER LOST.
    """
    config = ReconGraphConfig(decision_config=DecisionConfig())
    engine = ReconGraphEngine(config=config, providers=_get_providers())
    
    result = engine.reconcile(purchases, gsts)
    
    # Collect all records from output
    output_purchase_ids = set()
    output_gst_ids = set()
    
    for match in result.auto_matches:
        if match.selected_hypothesis:
            for urn in match.selected_hypothesis.hypothesis.matched_nodes:
                if urn.startswith("urn:recongraph:purchase:"):
                    output_purchase_ids.add(urn.split(":")[-1])
                elif urn.startswith("urn:recongraph:gst:"):
                    output_gst_ids.add(urn.split(":")[-1])
                    
    for packet in result.review_packets:
        for p in packet.purchases:
            output_purchase_ids.add(p.record_id)
        for g in packet.gsts:
            output_gst_ids.add(g.record_id)
            
    input_purchase_ids = {p.record_id for p in purchases}
    input_gst_ids = {g.record_id for g in gsts}
    
    # Assert Exact Conservation
    assert output_purchase_ids == input_purchase_ids, "Purchases were lost or hallucinated!"
    assert output_gst_ids == input_gst_ids, "GSTs were lost or hallucinated!"
