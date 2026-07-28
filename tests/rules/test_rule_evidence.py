import pytest
from recongraph.rules.models import RuleSet, Rule
from recongraph.rules.evidence import RuleEvidenceProvider
from recongraph.domain.records import PurchaseRecord, GSTRecord

def test_rule_evidence_provider():
    rule = Rule(
        rule_id="R001",
        description="Block if vendor conflict",
        condition_ast={"type": "BLOCK", "if": {"type": "AND", "conditions": ["vendor_name_conflict"]}},
        severity="BLOCK"
    )
    rule_set = RuleSet(tenant_id="tenant_A", rules=(rule,))
    
    provider = RuleEvidenceProvider({"tenant_A": rule_set}, tenant_id="tenant_A")
    
    # Mock records
    from decimal import Decimal
    from datetime import date
    purchase = PurchaseRecord(record_id="p1", vendor_name="A", tax_identity=None, amount=Decimal("100.0"), record_date=date(2024,1,1), reference="INV1")
    gst = GSTRecord(record_id="g1", tax_identity="GST1", vendor_name="B", amount=Decimal("100.0"), record_date=date(2024,1,1), reference="INV1")
    
    # Mock context is hardcoded in the stub for now, so we just pass records
    contrib = provider.evaluate([purchase], [gst])
    
    assert contrib.score == 0.0  # blocked by vendor_name_conflict
    assert "R001" in contrib.metadata["violations"]
    
    # Check tenant isolation
    provider_b = RuleEvidenceProvider({"tenant_A": rule_set}, tenant_id="tenant_B")
    contrib_b = provider_b.evaluate([purchase], [gst])
    assert contrib_b.score == 1.0
