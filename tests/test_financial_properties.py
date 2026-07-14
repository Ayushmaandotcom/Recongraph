from decimal import Decimal
from hypothesis import given, strategies as st
import pytest

from recongraph.domain.records import PurchaseRecord, GSTRecord
from datetime import date
from recongraph.domain.financial.pipeline import (
    FinancialEvidencePipeline,
    EqualityRelation,
    CurrencyRelation,
    SignRelation,
    CompatibilityFlag
)
from recongraph.domain.financial.amount_projection import project_amount_similarity

def create_mock_records(purchase_amount: str, gst_amount: str):
    p = PurchaseRecord(
        record_id="p1",
        vendor_name="V",
        reference="REF",
        amount=Decimal(purchase_amount),
        record_date=date(2025, 1, 1),
        tax_identity="T"
    )
    g = GSTRecord(
        record_id="g1",
        vendor_name="V",
        reference="REF",
        amount=Decimal(gst_amount),
        record_date=date(2025, 1, 1),
        tax_identity="T"
    )
    return [p], [g]


@given(
    st.decimals(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False)
)
def test_identity_always_exact_match(amount: Decimal):
    pipeline = FinancialEvidencePipeline(tolerance=Decimal("0.05"))
    p, g = create_mock_records(str(amount), str(amount))
    
    obs = pipeline.extract(p, g)
    interpretation = pipeline.interpret(obs)
    
    assert interpretation.equality == EqualityRelation.EQUAL
    assert interpretation.absolute_difference == Decimal("0")
    
    projection = project_amount_similarity(interpretation)
    assert projection.similarity == 1.0


@given(
    st.decimals(min_value=10, max_value=1_000_000, allow_nan=False, allow_infinity=False)
)
def test_symmetry(amount_a: Decimal):
    # Exclude diff <= 2.0 to avoid FEE_DETECTED breaking symmetry
    amount_b = amount_a * Decimal("1.30") # 30% diff, guarantees diff > 2.0 for amount_a >= 10
    
    pipeline = FinancialEvidencePipeline(tolerance=Decimal("0.05"))
    p1, g1 = create_mock_records(str(amount_a), str(amount_b))
    obs1 = pipeline.extract(p1, g1)
    interp1 = pipeline.interpret(obs1)
    proj1 = project_amount_similarity(interp1)
    
    p2, g2 = create_mock_records(str(amount_b), str(amount_a))
    obs2 = pipeline.extract(p2, g2)
    interp2 = pipeline.interpret(obs2)
    proj2 = project_amount_similarity(interp2)
    
    assert interp1.absolute_difference == interp2.absolute_difference
    assert interp1.relative_difference == interp2.relative_difference
    assert proj1.similarity == proj2.similarity


@given(
    st.decimals(min_value=100, max_value=100_000, allow_nan=False, allow_infinity=False),
    st.decimals(min_value=10, max_value=50, allow_nan=False, allow_infinity=False)
)
def test_monotonicity(base: Decimal, diff1: Decimal):
    diff2 = diff1 + Decimal("10") # diff2 is strictly greater than diff1
    
    amount_a = base
    amount_b1 = base + diff1
    amount_b2 = base + diff2
    
    pipeline = FinancialEvidencePipeline(tolerance=Decimal("0.01"))
    
    p1, g1 = create_mock_records(str(amount_a), str(amount_b1))
    interp1 = pipeline.interpret(pipeline.extract(p1, g1))
    proj1 = project_amount_similarity(interp1)
    
    p2, g2 = create_mock_records(str(amount_a), str(amount_b2))
    interp2 = pipeline.interpret(pipeline.extract(p2, g2))
    proj2 = project_amount_similarity(interp2)
    
    assert proj1.similarity >= proj2.similarity


def test_missing_values_do_not_synthesize_contradiction():
    # If there's an amount, but we don't have enough data or currency mismatches
    p, g = create_mock_records("100", "100")
    from dataclasses import replace
    p[0] = replace(p[0], currency="USD")
    g[0] = replace(g[0], currency="INR")
    
    pipeline = FinancialEvidencePipeline()
    obs = pipeline.extract(p, g)
    interp = pipeline.interpret(obs)
    
    assert interp.currency_relation == CurrencyRelation.DIFFERENT
    
    proj = project_amount_similarity(interp)
    assert proj.similarity == 0.0
    assert "CURRENCY_MISMATCH" in proj.warnings


def test_projection_purity():
    # Ensure projection never changes relationship type
    pipeline = FinancialEvidencePipeline()
    p, g = create_mock_records("100", "101")
    obs = pipeline.extract(p, g)
    interp = pipeline.interpret(obs)
    
    proj = project_amount_similarity(interp)
    
    # Projection doesn't hold the relationship, it just outputs scalar
    assert proj.similarity > 0 and proj.similarity < 1.0
