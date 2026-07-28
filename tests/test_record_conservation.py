"""
PIPE-003 Conservation Regression Tests

These tests lock the invariant that every input record appears in the output,
either as part of an auto_match or as a review_packet. No record is ever silently
dropped by the engine.
"""
from decimal import Decimal
from datetime import date
import pytest

from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.config import ReconGraphConfig, DecisionConfig
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider,
    TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
)
from recongraph.matching.reference_evidence import (
    ReferenceCorpusProfile, ReferenceEvidenceContext, ReferenceEvidencePolicy
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.engine import ReconGraphEngine
from recongraph.graph.decision import DecisionAction


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_vendor_context():
    return VendorIdentityContext(
        corpus_profile=VendorCorpusProfile(
            corpus_size=1, token_document_frequencies={}, digest="1"
        ),
        interpreter_policy_version="1.0.0",
        fuzzy_minimum_length=6,
        fuzzy_threshold=0.85,
        distinctiveness_threshold=0.01,
    )


def _make_providers(references: list[str]):
    """Build providers whose corpus profile covers the given references."""
    # Build a minimal corpus profile from the reference list
    from recongraph.normalization.text import normalize_reference
    freq: dict[str, int] = {}
    for ref in references:
        norm = normalize_reference(ref)
        freq[norm] = freq.get(norm, 0) + 1
    profile = ReferenceCorpusProfile(
        reference_count=max(len(references), 1),
        normalized_reference_frequency=freq if freq else {"dummy": 1},
        numeric_token_document_frequency={},
    )
    return [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(_make_vendor_context()),
        ReferenceEvidenceProvider(
            ReferenceEvidenceContext(profile, ReferenceEvidencePolicy())
        ),
    ]


def _collect_output_ids(result):
    """Extract all record IDs present in the engine output."""
    purchase_ids: set[str] = set()
    gst_ids: set[str] = set()

    for match in result.auto_matches:
        if match.selected_hypothesis:
            for urn in match.selected_hypothesis.hypothesis.matched_nodes:
                if urn.startswith("urn:recongraph:purchase:"):
                    purchase_ids.add(urn.split(":")[-1])
                elif urn.startswith("urn:recongraph:gst:"):
                    gst_ids.add(urn.split(":")[-1])

    for packet in result.review_packets:
        for p in packet.purchases:
            purchase_ids.add(p.record_id)
        for g in packet.gsts:
            gst_ids.add(g.record_id)

    return purchase_ids, gst_ids


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAutoMatchLeftoversRouteToReview:
    """When p1↔g1 auto-match but p2 shares a blocking key, p2 MUST appear
    in a review packet — never silently dropped."""

    def test_leftover_purchase_becomes_review_packet(self):
        p1 = PurchaseRecord(
            record_id="p1", amount=Decimal("100.0"),
            record_date=date(2023, 1, 1), reference="INV1",
            vendor_name="Alpha", tax_identity="TAX1",
        )
        g1 = GSTRecord(
            record_id="g1", amount=Decimal("100.0"),
            record_date=date(2023, 1, 1), reference="INV1",
            vendor_name="Alpha", tax_identity="TAX1",
        )
        # p2 shares tax_identity → same component, but nothing matches it.
        p2 = PurchaseRecord(
            record_id="p2", amount=Decimal("999.0"),
            record_date=date(2023, 6, 15), reference="INV-OTHER",
            vendor_name="Beta", tax_identity="TAX1",
        )

        providers = _make_providers(["INV1", "INV-OTHER"])
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile([p1, p2], [g1])

        # The engine may auto-match or review p1↔g1 depending on coverage
        # thresholds (3-node component → coverage < 1.0). Either way, p2 MUST
        # appear in a review packet. That is the conservation invariant.
        out_p, _ = _collect_output_ids(result)
        assert "p1" in out_p, "p1 missing from output"

        # p2 must surface somewhere in review_packets
        review_purchase_ids = {
            p.record_id
            for pkt in result.review_packets
            for p in pkt.purchases
        }
        assert "p2" in review_purchase_ids, (
            "PIPE-003: leftover purchase p2 was silently dropped"
        )

    def test_leftover_gst_becomes_review_packet(self):
        """Mirror: leftover GST record must also be conserved."""
        p1 = PurchaseRecord(
            record_id="p1", amount=Decimal("500.0"),
            record_date=date(2023, 3, 1), reference="REF-A",
            vendor_name="Gamma", tax_identity="TAX2",
        )
        g1 = GSTRecord(
            record_id="g1", amount=Decimal("500.0"),
            record_date=date(2023, 3, 1), reference="REF-A",
            vendor_name="Gamma", tax_identity="TAX2",
        )
        g2 = GSTRecord(
            record_id="g2", amount=Decimal("12345.0"),
            record_date=date(2023, 9, 20), reference="REF-UNRELATED",
            vendor_name="Delta", tax_identity="TAX2",
        )

        providers = _make_providers(["REF-A", "REF-UNRELATED"])
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile([p1], [g1, g2])

        review_gst_ids = {
            g.record_id
            for pkt in result.review_packets
            for g in pkt.gsts
        }
        assert "g2" in review_gst_ids, (
            "PIPE-003: leftover GST g2 was silently dropped"
        )


class TestNoMatchComponentFullConservation:
    """When a decision is NO_MATCH, consumed_nodes is empty, so EVERY node
    in the component must get its own review packet."""

    def test_all_nodes_become_review_packets_on_no_match(self):
        # Two records that share a blocking key but disagree on everything else.
        p1 = PurchaseRecord(
            record_id="p_nm1", amount=Decimal("100.0"),
            record_date=date(2023, 1, 1), reference="SHARED-REF",
            vendor_name="Vendor X", tax_identity="TAX-SHARED",
        )
        g1 = GSTRecord(
            record_id="g_nm1", amount=Decimal("99999.0"),
            record_date=date(2023, 12, 31), reference="SHARED-REF",
            vendor_name="Completely Different Vendor",
            tax_identity="TAX-SHARED",
        )

        providers = _make_providers(["SHARED-REF"])
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile([p1], [g1])

        out_p, out_g = _collect_output_ids(result)
        assert "p_nm1" in out_p, "p_nm1 missing from output"
        assert "g_nm1" in out_g, "g_nm1 missing from output"


class TestConservationInvariant:
    """The fundamental conservation invariant:
    len(auto_matched_records) + len(review_packet_records) == len(input_records)

    This is the deterministic version of the property test in test_properties.py.
    """

    def test_exact_conservation_simple(self) -> None:
        """1 purchase + 1 GST → they either match or both go to review."""
        p = PurchaseRecord(
            record_id="pC1", amount=Decimal("250.0"),
            record_date=date(2023, 5, 10), reference="INV-C1",
            vendor_name="ConsCorp", tax_identity="TAX-C",
        )
        g = GSTRecord(
            record_id="gC1", amount=Decimal("250.0"),
            record_date=date(2023, 5, 10), reference="INV-C1",
            vendor_name="ConsCorp", tax_identity="TAX-C",
        )

        providers = _make_providers(["INV-C1"])
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile([p], [g])

        out_p, out_g = _collect_output_ids(result)
        assert out_p == {"pC1"}, f"Purchase conservation violated: {out_p}"
        assert out_g == {"gC1"}, f"GST conservation violated: {out_g}"

    def test_exact_conservation_multi_record(self) -> None:
        """3 purchases + 2 GSTs → all 5 record IDs must appear in output."""
        records_p = [
            PurchaseRecord(
                record_id=f"pM{i}", amount=Decimal(str(100 * (i + 1))),
                record_date=date(2023, i + 1, 1), reference=f"REF-M{i}",
                vendor_name=f"Vendor {i}", tax_identity=f"TAX-M{i}",
            )
            for i in range(3)
        ]
        records_g = [
            GSTRecord(
                record_id=f"gM{i}", amount=Decimal(str(100 * (i + 1))),
                record_date=date(2023, i + 1, 1), reference=f"REF-M{i}",
                vendor_name=f"Vendor {i}", tax_identity=f"TAX-M{i}",
            )
            for i in range(2)
        ]

        all_refs = [f"REF-M{i}" for i in range(3)]
        providers = _make_providers(all_refs)
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile(records_p, records_g)

        out_p, out_g = _collect_output_ids(result)
        expected_p = {f"pM{i}" for i in range(3)}
        expected_g = {f"gM{i}" for i in range(2)}
        assert out_p == expected_p, f"Purchase conservation: expected {expected_p}, got {out_p}"
        assert out_g == expected_g, f"GST conservation: expected {expected_g}, got {out_g}"

    def test_empty_inputs_produce_empty_outputs(self):
        """Zero records in → zero records out. No hallucination."""
        providers = _make_providers([])
        engine = ReconGraphEngine(ReconGraphConfig(), providers)
        result = engine.reconcile([], [])

        assert result.auto_matches == []
        assert result.review_packets == []
        assert result.traces == []
