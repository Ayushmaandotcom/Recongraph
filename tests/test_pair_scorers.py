from datetime import date
import pytest
from decimal import Decimal
from recongraph.domain.records import GSTRecord, PurchaseRecord
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile

def _get_vendor_context():
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(corpus_size=1, token_document_frequencies={}, digest='1'), 
        interpreter_policy_version='1.0.0', 
        fuzzy_minimum_length=6, 
        fuzzy_threshold=0.85, 
        distinctiveness_threshold=0.01
    )

from recongraph.matching.pair_scorers import PURCHASE_TO_GST_MAX_DAYS, PURCHASE_TO_GST_POLICY, PairScoringResult
from recongraph.matching.scoring import SignalName
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceEvidencePolicy, ReferenceCorpusProfile

def _default_context() -> ReferenceEvidenceContext:
    prof = ReferenceCorpusProfile(
        reference_count=1000, 
        normalized_reference_frequency={'dummy': 998, 'inv1042': 2}, 
        numeric_token_document_frequency={'2026': 100, '1042': 2}
    )
    return ReferenceEvidenceContext(profile=prof, policy=ReferenceEvidencePolicy())

def test_purchase_record_preserves_financial_fields() -> None:
    record = PurchaseRecord(record_id='dummy_p', vendor_name='ABC Steel Private Limited', reference='INV-1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 12), tax_identity='07ABCDE1234F1Z5')
    assert record.vendor_name == 'ABC Steel Private Limited'
    assert record.reference == 'INV-1042'
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 12)
    assert record.tax_identity == '07ABCDE1234F1Z5'

def test_gst_record_preserves_financial_fields() -> None:
    record = GSTRecord(record_id='dummy_g', vendor_name='ABC STEELS PVT. LTD.', reference='AB/1042', amount=Decimal('118000.0'), record_date=date(2026, 6, 13), tax_identity='07ABCDE1234F1Z5')
    assert record.vendor_name == 'ABC STEELS PVT. LTD.'
    assert record.reference == 'AB/1042'
    assert record.amount == 118000.0
    assert record.record_date == date(2026, 6, 13)
    assert record.tax_identity == '07ABCDE1234F1Z5'

def test_purchase_to_gst_policy_uses_expected_weights() -> None:
    assert PURCHASE_TO_GST_POLICY.weights == {
        SignalName.ENTITY: 0.2, 
        SignalName.REFERENCE: 0.2, 
        SignalName.AMOUNT: 0.25, 
        SignalName.TEMPORAL: 0.1, 
        SignalName.TAX_IDENTITY: 0.25
    }



def test_purchase_to_gst_temporal_window_is_seven_days() -> None:
    assert PURCHASE_TO_GST_MAX_DAYS == 7