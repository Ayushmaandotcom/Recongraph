"""
ARCH-002 Equivalence Lock: HypothesisEvaluator ↔ score_purchase_to_gst

The evaluator delegates to score_purchase_to_gst for 1:1 hypotheses.
These tests lock that equivalence so the two stacks can never diverge silently.
Parametrized over diverse challenge pairs covering exact matches, vendor
mismatches, amount conflicts, date gaps, and missing references.
"""
from decimal import Decimal
from datetime import date
import pytest

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.graph.candidate import CandidateGraphBuilder, build_purchase_urn, build_gst_urn
from recongraph.graph.hypotheses import Hypothesis, EligibilityStatus
from recongraph.graph.evaluator import HypothesisEvaluator
from recongraph.matching.pair_scorers import score_purchase_to_gst, PURCHASE_TO_GST_POLICY
from recongraph.matching.purchase_gst_semantics import OneToOneEligibility
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider,
    TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider,
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import (
    ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _vendor_ctx():
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(
            corpus_size=1, token_document_frequencies={}, digest="1"
        ),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01,
    )


def _providers(refs: list[str]):
    from recongraph.normalization.text import normalize_reference
    freq: dict[str, int] = {}
    for r in refs:
        n = normalize_reference(r)
        freq[n] = freq.get(n, 0) + 1
    profile = ReferenceCorpusProfile(
        reference_count=max(len(refs), 1),
        normalized_reference_frequency=freq if freq else {"dummy": 1},
        numeric_token_document_frequency={},
    )
    return [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(_vendor_ctx()),
        ReferenceEvidenceProvider(
            ReferenceEvidenceContext(profile, ReferenceEvidencePolicy())
        ),
    ]


def _evaluator_result_for(p: PurchaseRecord, g: GSTRecord, providers):
    """Build a 1:1 hypothesis and evaluate it through HypothesisEvaluator."""
    builder = CandidateGraphBuilder()
    p_urn = build_purchase_urn(p.record_id)
    g_urn = build_gst_urn(g.record_id)
    builder.add_node(p_urn, p)
    builder.add_node(g_urn, g)
    builder.add_candidate_edge(p_urn, g_urn, frozenset())
    graph = builder.build()

    hypothesis = Hypothesis(
        component_nodes=frozenset([p_urn, g_urn]),
        proposed_edges=frozenset([frozenset([p_urn, g_urn])]),
    )

    evaluator = HypothesisEvaluator(providers, PURCHASE_TO_GST_POLICY)
    return evaluator.evaluate(graph, hypothesis)


# ---------------------------------------------------------------------------
# Challenge Pairs
# ---------------------------------------------------------------------------

CHALLENGE_PAIRS = [
    pytest.param(
        PurchaseRecord(record_id="p_exact", amount=Decimal("1000.00"),
                       record_date=date(2023, 1, 15), reference="INV-001",
                       vendor_name="TechCorp Pvt Ltd", tax_identity="TAX001"),
        GSTRecord(record_id="g_exact", amount=Decimal("1000.00"),
                  record_date=date(2023, 1, 15), reference="INV-001",
                  vendor_name="TechCorp Pvt Ltd", tax_identity="TAX001"),
        id="exact_match",
    ),
    pytest.param(
        PurchaseRecord(record_id="p_vendor", amount=Decimal("500.00"),
                       record_date=date(2023, 3, 1), reference="REF-A",
                       vendor_name="Alpha Corp", tax_identity="TAX002"),
        GSTRecord(record_id="g_vendor", amount=Decimal("500.00"),
                  record_date=date(2023, 3, 1), reference="REF-A",
                  vendor_name="Completely Unrelated Inc", tax_identity="TAX002"),
        id="vendor_mismatch",
    ),
    pytest.param(
        PurchaseRecord(record_id="p_amount", amount=Decimal("2000.00"),
                       record_date=date(2023, 6, 10), reference="INV-B",
                       vendor_name="Beta LLC", tax_identity="TAX003"),
        GSTRecord(record_id="g_amount", amount=Decimal("999.00"),
                  record_date=date(2023, 6, 10), reference="INV-B",
                  vendor_name="Beta LLC", tax_identity="TAX003"),
        id="severe_amount_conflict",
    ),
    pytest.param(
        PurchaseRecord(record_id="p_date", amount=Decimal("750.00"),
                       record_date=date(2023, 1, 1), reference="INV-C",
                       vendor_name="Gamma Ltd", tax_identity="TAX004"),
        GSTRecord(record_id="g_date", amount=Decimal("750.00"),
                  record_date=date(2023, 12, 31), reference="INV-C",
                  vendor_name="Gamma Ltd", tax_identity="TAX004"),
        id="temporal_gap_364_days",
    ),
    pytest.param(
        PurchaseRecord(record_id="p_noref", amount=Decimal("300.00"),
                       record_date=date(2023, 4, 1), reference=None,
                       vendor_name="Delta Inc", tax_identity="TAX005"),
        GSTRecord(record_id="g_noref", amount=Decimal("300.00"),
                  record_date=date(2023, 4, 1), reference=None,
                  vendor_name="Delta Inc", tax_identity="TAX005"),
        id="missing_references",
    ),
]


# ---------------------------------------------------------------------------
# Equivalence Lock Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("purchase,gst", CHALLENGE_PAIRS)
def test_evaluator_agrees_with_pair_scorer_on_one_to_one(purchase, gst):
    """ARCH-002: HypothesisEvaluator and score_purchase_to_gst must produce
    identical scores and eligibility for any 1:1 hypothesis."""
    refs = [r for r in [purchase.reference, gst.reference] if r]
    provs = _providers(refs)

    # Direct pair scorer
    pair = score_purchase_to_gst(
        purchases=[purchase], gsts=[gst],
        providers=provs, policy=PURCHASE_TO_GST_POLICY,
    )

    # Through HypothesisEvaluator
    evaluated = _evaluator_result_for(purchase, gst, provs)

    # Score equivalence
    assert evaluated.score == pytest.approx(pair.score), (
        f"Score divergence: evaluator={evaluated.score}, pair_scorer={pair.score}"
    )

    # Coverage equivalence
    assert evaluated.coverage == pytest.approx(pair.coverage), (
        f"Coverage divergence: evaluator={evaluated.coverage}, pair_scorer={pair.coverage}"
    )

    # Eligibility equivalence
    evaluator_ineligible = evaluated.eligibility is EligibilityStatus.INELIGIBLE
    scorer_ineligible = not pair.is_eligible
    assert evaluator_ineligible == scorer_ineligible, (
        f"Eligibility divergence: evaluator_ineligible={evaluator_ineligible}, "
        f"scorer_ineligible={scorer_ineligible}"
    )

    # Signal equivalence (every signal must match)
    for signal_name in pair.signals:
        eval_signal = evaluated.supporting_evidence.signals.get(signal_name)
        pair_signal = pair.signals[signal_name]
        if pair_signal is None:
            assert eval_signal is None, (
                f"Signal {signal_name}: evaluator={eval_signal}, pair_scorer=None"
            )
        else:
            assert eval_signal == pytest.approx(pair_signal), (
                f"Signal {signal_name} divergence: "
                f"evaluator={eval_signal}, pair_scorer={pair_signal}"
            )
