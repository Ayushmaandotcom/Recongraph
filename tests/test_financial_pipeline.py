import pytest
from decimal import Decimal
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline, AmountInterpretation, AmountRelationship
from recongraph.domain.financial.amount_projection import project_amount_similarity

def base_purchase(amount: float, curr="USD", net=None, tax=None) -> PurchaseRecord:
    return PurchaseRecord(record_id="p", amount=amount, record_date=date(2023,1,1), reference="R", vendor_name="V", tax_identity="T", currency=curr, net_amount=net, tax_amount=tax)

def base_gst(amount: float, curr="USD", net=None, tax=None) -> GSTRecord:
    return GSTRecord(record_id="g", amount=amount, record_date=date(2023,1,1), reference="R", vendor_name="V", tax_identity="T", currency=curr, net_amount=net, tax_amount=tax)

# --- Synthetic Mutation Operators ---

def exact_match_scenario(amount: float):
    return [base_purchase(amount)], [base_gst(amount)]

def split_payment_scenario(amount: float, parts: list[float]):
    assert sum(parts) == amount
    return [base_purchase(amount)], [base_gst(p) for p in parts]
    
def partial_payment_scenario(amount: float, payment: float):
    assert payment < amount
    return [base_purchase(amount)], [base_gst(payment)]
    
def over_payment_scenario(amount: float, payment: float):
    assert payment > amount
    return [base_purchase(amount)], [base_gst(payment)]
    
def rounding_scenario(amount: float, diff: float):
    return [base_purchase(amount)], [base_gst(amount + diff)]
    
def currency_mismatch_scenario(amount: float):
    return [base_purchase(amount, curr="USD")], [base_gst(amount, curr="EUR")]
    
def fee_scenario(amount: float, fee: float):
    return [base_purchase(amount)], [base_gst(amount - fee)]
    
def gross_net_scenario(net: float, tax: float):
    gross = net + tax
    return [base_purchase(gross, net=net, tax=tax)], [base_gst(net, net=net, tax=tax)]

# --- Tests ---

def test_exact_match():
    purchases, gsts = exact_match_scenario(100.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.EXACT_MATCH
    
def test_split_payment():
    purchases, gsts = split_payment_scenario(100.0, [60.0, 40.0])
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.EXACT_MATCH
    
def test_partial_payment():
    purchases, gsts = partial_payment_scenario(100.0, 90.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.PARTIAL_SETTLEMENT
    assert interp.residual == Decimal("10.0")
    
def test_over_payment():
    purchases, gsts = over_payment_scenario(100.0, 105.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.OVERPAYMENT
    assert interp.residual == Decimal("-5.0")
    
def test_rounding():
    purchases, gsts = rounding_scenario(100.0, 0.04) # within 0.05 tolerance
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.ROUNDING_MATCH
    
def test_fee_detected():
    purchases, gsts = fee_scenario(100.0, 1.50) # within 2.00 fee tolerance
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.FEE_DETECTED
    
def test_currency_mismatch():
    purchases, gsts = currency_mismatch_scenario(100.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.CURRENCY_MISMATCH
    
def test_gross_net_match():
    purchases, gsts = gross_net_scenario(100.0, 18.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.relationship == AmountRelationship.PARTIAL_SETTLEMENT
    
def test_contribution_mapping():
    pipeline = FinancialEvidencePipeline()
    purchases, gsts = currency_mismatch_scenario(100.0)
    interp = pipeline.interpret(pipeline.extract(purchases, gsts))
    proj = project_amount_similarity(interp)
    assert proj.similarity == 0.0
    assert "CURRENCY_MISMATCH" in proj.warnings
