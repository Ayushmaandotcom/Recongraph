import pytest
from datetime import date
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.financial.pipeline import FinancialEvidencePipeline, EvaluatedFinancialEvidence

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
    assert interp.is_exact_match
    assert "EXACT_TOTAL_MATCH" in interp.notes
    
def test_split_payment():
    purchases, gsts = split_payment_scenario(100.0, [60.0, 40.0])
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.is_exact_match
    assert "SPLIT_PAYMENT" in interp.notes
    
def test_partial_payment():
    purchases, gsts = partial_payment_scenario(100.0, 90.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert not interp.is_exact_match
    assert interp.is_partial
    assert interp.residual == 10.0
    assert "UNDERPAYMENT" in interp.notes
    
def test_over_payment():
    purchases, gsts = over_payment_scenario(100.0, 105.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert not interp.is_exact_match
    assert interp.is_overpayment
    assert interp.residual == -5.0
    assert "OVERPAYMENT" in interp.notes
    
def test_rounding():
    purchases, gsts = rounding_scenario(100.0, 0.04) # within 0.05 tolerance
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.is_exact_match
    assert "ROUNDING_MATCH" in interp.notes
    
def test_fee_detected():
    purchases, gsts = fee_scenario(100.0, 1.50) # within 2.00 fee tolerance
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.is_exact_match
    assert "FEE_DETECTED" in interp.notes
    
def test_currency_mismatch():
    purchases, gsts = currency_mismatch_scenario(100.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert interp.currency_mismatch
    assert "CURRENCY_MISMATCH" in interp.notes
    assert interp.amount_score == 0.0
    
def test_gross_net_match():
    purchases, gsts = gross_net_scenario(100.0, 18.0)
    interp = FinancialEvidencePipeline().interpret(FinancialEvidencePipeline().extract(purchases, gsts))
    assert not interp.is_exact_match
    assert interp.is_partial
    assert "GROSS_NET_MATCH" in interp.notes
    
def test_contribution_mapping():
    pipeline = FinancialEvidencePipeline()
    purchases, gsts = currency_mismatch_scenario(100.0)
    interp = pipeline.interpret(pipeline.extract(purchases, gsts))
    contrib = pipeline.contribute(interp)
    assert contrib.score == 0.0
    assert "CURRENCY_MISMATCH" in contrib.violations
