import pytest
from decimal import Decimal
import datetime

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.matching.pair_scorers import score_purchase_to_gst, PURCHASE_TO_GST_POLICY
from recongraph.plugins.core_providers import FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
from recongraph.matching.purchase_gst_semantics import SemanticFinding

def make_providers():
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
    return [
        FinancialEvidenceProvider(0.05),
        TemporalEvidenceProvider(30),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_context),
        ReferenceEvidenceProvider(context)
    ]

def test_amount_multiple_detection():
    # 2x amount
    p = PurchaseRecord(
        record_id="P1", vendor_name="Vendor A", tax_identity="29ABCDE1234F1Z5", 
        record_date=datetime.date(2023, 1, 1),
        reference="INV-001",
        net_amount=Decimal("1000.00"),
        tax_amount=Decimal("180.00"),
        amount=Decimal("1180.00")
    )
    g = GSTRecord(
        record_id="G1", vendor_name="Vendor A", tax_identity="29ABCDE1234F1Z5", 
        record_date=datetime.date(2023, 1, 1),
        reference="INV-001",
        net_amount=Decimal("2000.00"),  # Doubled
        tax_amount=Decimal("360.00"),
        amount=Decimal("2360.00"),
        filing_period="2023-01"
    )
    
    scored_pair = score_purchase_to_gst(
        purchases=[p],
        gsts=[g],
        providers=make_providers(),
        policy=PURCHASE_TO_GST_POLICY
    )
    
    assert SemanticFinding.AMOUNT_MULTIPLE in scored_pair.violations

def test_amount_not_multiple():
    # 2.5x amount (not integer multiple)
    p = PurchaseRecord(
        record_id="P1", vendor_name="Vendor A", tax_identity="29ABCDE1234F1Z5", 
        record_date=datetime.date(2023, 1, 1),
        reference="INV-001",
        net_amount=Decimal("1000.00"),
        tax_amount=Decimal("180.00"),
        amount=Decimal("1180.00")
    )
    g = GSTRecord(
        record_id="G1", vendor_name="Vendor A", tax_identity="29ABCDE1234F1Z5", 
        record_date=datetime.date(2023, 1, 1),
        reference="INV-001",
        net_amount=Decimal("2500.00"), 
        tax_amount=Decimal("450.00"),
        amount=Decimal("2950.00"),
        filing_period="2023-01"
    )
    
    scored_pair = score_purchase_to_gst(
        purchases=[p],
        gsts=[g],
        providers=make_providers(),
        policy=PURCHASE_TO_GST_POLICY
    )
    
    assert SemanticFinding.AMOUNT_MULTIPLE not in scored_pair.violations
