"""
Serialization round-trip tests (A3).

Verifies that ReconciliationResult.to_dict() produces a JSON-safe dict that
preserves all top-level keys, and that the CLI reconcile subcommand exits 0
and produces well-formed JSON output.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_referee_result():
    """Return a ReconciliationResult from the challenge referee dataset."""
    import csv
    import io
    from decimal import Decimal
    from datetime import date

    from recongraph.domain.records import PurchaseRecord, GSTRecord
    from recongraph.config import ReconGraphConfig
    from recongraph.engine import ReconGraphEngine
    from recongraph.plugins.core_providers import (
        FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider,
        VendorEvidenceProvider, ReferenceEvidenceProvider,
    )
    from recongraph.domain.vendor.context import VendorIdentityContext
    from recongraph.matching.reference_evidence import (
        build_reference_corpus_profile, ReferenceEvidenceContext, ReferenceEvidencePolicy,
    )

    PURCHASES = """record_id,vendor_name,invoice_number,invoice_date,amount,gstin
CP001,ABC Steel Private Limited,INV-1042,2026-06-12,118000.00,07ABCDE1234F1Z5
CP002,CloudLedger Software Private Limited,CL-JUN-2026,2026-06-05,25000.00,07CLOUD1234A1Z1
"""
    GSTS = """record_id,supplier_name,invoice_number,invoice_date,amount,gstin
CG001,ABC STEELS PVT. LTD.,AB/1042,2026-06-13,236000.00,07ABCDE1234F1Z5
CG003,CLOUDLEDGER SOFTWARE PVT LTD,CL-JUL-2026,2026-07-05,25000.00,07CLOUD1234A1Z1
"""

    P = [PurchaseRecord(
        record_id=r["record_id"], vendor_name=r["vendor_name"] or None,
        reference=r["invoice_number"] or None, amount=Decimal(r["amount"]),
        record_date=date.fromisoformat(r["invoice_date"]),
        tax_identity=r["gstin"] or None)
        for r in csv.DictReader(io.StringIO(PURCHASES))]
    G = [GSTRecord(
        record_id=r["record_id"], vendor_name=r["supplier_name"] or None,
        reference=r["invoice_number"] or None, amount=Decimal(r["amount"]),
        record_date=date.fromisoformat(r["invoice_date"]),
        tax_identity=r["gstin"] or None)
        for r in csv.DictReader(io.StringIO(GSTS))]

    corpus = build_reference_corpus_profile([r.reference for r in P + G])
    ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
    vendor_ctx = VendorIdentityContext(corpus_profile=None)

    providers = [
        FinancialEvidenceProvider(), TemporalEvidenceProvider(), TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_ctx), ReferenceEvidenceProvider(ref_ctx),
    ]
    return ReconGraphEngine(config=ReconGraphConfig(), providers=providers).reconcile(P, G)


def test_to_dict_produces_json_safe_dict() -> None:
    """to_dict() must return a plain Python dict serializable by json.dumps."""
    result = _run_referee_result()
    d = result.to_dict()
    assert isinstance(d, dict), f"Expected dict, got {type(d)}"
    # Must be JSON-safe — no Decimal, date, frozenset, or dataclass instances
    raw = json.dumps(d)  # Would raise TypeError if not JSON-safe
    assert raw  # non-empty


def test_to_dict_top_level_keys() -> None:
    """to_dict() must contain the four canonical top-level keys."""
    result = _run_referee_result()
    d = result.to_dict()
    assert "auto_matches" in d
    assert "review_packets" in d
    assert "traces" in d
    assert "engine_version" in d


def test_to_dict_review_packets_have_headline() -> None:
    """Each review packet dict must include a headline field."""
    result = _run_referee_result()
    d = result.to_dict()
    for pkt in d.get("review_packets", []):
        assert "headline" in pkt, f"Packet {pkt.get('packet_id')} missing headline"
        assert isinstance(pkt["headline"], str)
        assert pkt["headline"]  # non-empty


def test_to_dict_round_trip_key_count() -> None:
    """Round-tripping through JSON must not lose top-level keys."""
    result = _run_referee_result()
    d1 = result.to_dict()
    d2 = json.loads(json.dumps(d1))
    assert set(d1.keys()) == set(d2.keys())
    assert len(d1["review_packets"]) == len(d2["review_packets"])


CHALLENGE_DIR = Path(__file__).parent.parent / "datasets" / "challenge"


@pytest.mark.skipif(
    not CHALLENGE_DIR.exists(),
    reason="challenge dataset not found"
)
def test_cli_reconcile_exits_0_and_produces_json(tmp_path: Path) -> None:
    """python -m recongraph reconcile <csv> <csv> --out <file> must exit 0 and
    produce a well-formed JSON file with the canonical top-level keys."""
    purchases_csv = CHALLENGE_DIR / "purchase_register_v1.csv"
    gst_csv = CHALLENGE_DIR / "gst_records_v1.csv"
    out_file = tmp_path / "results.json"

    proc = subprocess.run(
        [sys.executable, "-m", "recongraph", "reconcile",
         str(purchases_csv), str(gst_csv), "--out", str(out_file)],
        capture_output=True, text=True,
        cwd=str(CHALLENGE_DIR.parent.parent)
    )
    assert proc.returncode == 0, (
        f"CLI exited with {proc.returncode}.\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    assert out_file.exists(), "CLI did not create output file"

    with out_file.open() as f:
        data = json.load(f)

    assert "auto_matches" in data
    assert "review_packets" in data
    assert "engine_version" in data
