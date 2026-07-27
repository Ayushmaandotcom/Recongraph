import pytest
from decimal import Decimal
from datetime import date

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import TaxEvidenceProvider

def test_tax_intelligence_engine_assertions():
    # Both exactly the same tax (18%), math valid:
    p1 = PurchaseRecord(
        record_id="p1", vendor_name="V", reference="1", 
        amount=Decimal("118"), record_date=date(2023,1,1),
        tax_identity="27ABCDE1234F1Z0", net_amount=Decimal("100"), 
        tax_amount=Decimal("18"), tax_rate=Decimal("18")
    )
    g1 = GSTRecord(
        record_id="g1", vendor_name="V", reference="1", 
        amount=Decimal("118"), record_date=date(2023,1,1),
        tax_identity="27ABCDE1234F1Z0", net_amount=Decimal("100"), 
        tax_amount=Decimal("18"), tax_rate=Decimal("18")
    )

    provider = TaxEvidenceProvider()
    contrib = provider.evaluate([p1], [g1])
    assertions = contrib.metadata.get("assertions", [])
    
    # Expecting 3 SUPPORT assertions:
    # 1. same_tax_identity
    # 2. valid_regime_alignment
    # 3. gross_net_consistency
    assert len(assertions) == 3
    for a in assertions:
        assert a.polarity.value == "support"
        
    claims = {a.proposition.claim.claim_id.value for a in assertions}
    assert "tax.same_tax_identity" in claims
    assert "tax.valid_regime_alignment" in claims
    assert "tax.gross_net_consistency" in claims

def test_tax_intelligence_engine_conflict():
    # Inconsistent regime (18% vs 5%)
    p1 = PurchaseRecord(
        record_id="p1", vendor_name="V", reference="1", 
        amount=Decimal("118"), record_date=date(2023,1,1),
        tax_identity="27ABCDE1234F1Z0", net_amount=Decimal("100"), 
        tax_amount=Decimal("18"), tax_rate=Decimal("18")
    )
    g1 = GSTRecord(
        record_id="g1", vendor_name="V", reference="1", 
        amount=Decimal("105"), record_date=date(2023,1,1),
        tax_identity="27ABCDE1234F1Z0", net_amount=Decimal("100"), 
        tax_amount=Decimal("5"), tax_rate=Decimal("5")
    )

    provider = TaxEvidenceProvider()
    contrib = provider.evaluate([p1], [g1])
    assertions = contrib.metadata.get("assertions", [])
    
    assert len(assertions) == 3
    
    # same_tax_identity is SUPPORT
    # valid_regime_alignment is CONFLICT
    # gross_net_consistency is SUPPORT (because math is valid internally on both sides)
    polarities = {a.proposition.claim.claim_id.value: a.polarity.value for a in assertions}
    assert polarities["tax.same_tax_identity"] == "support"
    assert polarities["tax.valid_regime_alignment"] == "conflict"
    assert polarities["tax.gross_net_consistency"] == "support"
