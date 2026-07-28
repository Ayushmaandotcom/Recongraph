"""Challenge referee — adversarial labeled cases HN001-HN005.

Restored from the July 14 pre-repository tree. These datasets existed in the
original project but were never committed to this repo's git history, so no
commit here has ever been evaluated against them until now.

Self-contained: datasets embedded below. Engine-level API only.
HN001 amount_mismatch_identity_agreement | HN002 tax_identity_contradiction
HN003 recurring_invoice_collision | HN004 weak_reference_collision
HN005 one_to_many_invoice_relationship
"""
import csv, io
from datetime import date

from recongraph.config import ReconGraphConfig
from recongraph.engine import ReconGraphEngine
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.domain.vendor.context import VendorIdentityContext
from recongraph.matching.reference_evidence import (
    ReferenceEvidenceContext, ReferenceEvidencePolicy,
    build_reference_corpus_profile)
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider, TaxEvidenceProvider,
    VendorEvidenceProvider, ReferenceEvidenceProvider)

PURCHASES = """record_id,vendor_name,invoice_number,invoice_date,amount,gstin
CP001,ABC Steel Private Limited,INV-1042,2026-06-12,118000.00,07ABCDE1234F1Z5
CP002,CloudLedger Software Private Limited,CL-JUN-2026,2026-06-05,25000.00,07CLOUD1234A1Z1
CP003,Orion Medical Devices Private Limited,OMD-001,2026-06-20,75000.00,07ORION5678B1Z2
CP004,Apex Industrial Supplies,AIS-9001,2026-06-25,100000.00,07APEXS1234C1Z3
CP005,Beta Electronics Pvt Ltd,BEP-2200,2026-07-01,50000.00,07BETAE5678G1Z3
"""
GSTS = """record_id,supplier_name,invoice_number,invoice_date,amount,gstin
CG001,ABC STEELS PVT. LTD.,AB/1042,2026-06-13,236000.00,07ABCDE1234F1Z5
CG002,ABC STEELS PVT. LTD.,AB/1042,2026-06-13,118000.00,27ZZZZZ9999Z9Z9
CG003,CLOUDLEDGER SOFTWARE PVT LTD,CL-JUL-2026,2026-07-05,25000.00,07CLOUD1234A1Z1
CG004,Nova Surgical Systems Private Limited,NSS-001,2026-06-20,75000.00,29NOVAS9876D1Z4
CG005,APEX INDUSTRIAL SUPPLIES,AIS/9001-A,2026-06-25,50000.00,07APEXS1234C1Z3
CG006,APEX INDUSTRIAL SUPPLIES,AIS/9001-B,2026-06-25,50000.00,07APEXS1234C1Z3
CG007,BETA ELECTRONICS PVT LTD,BEP-2200,2026-07-01,100000.00,07BETAE5678G1Z3
"""
NEGATIVE_PAIRS = [  # (case, purchase, gst) — must NEVER be auto-matched together
    ("HN001", "CP001", "CG001"),  # amount mismatch with identity agreement
    ("HN002", "CP001", "CG002"),  # tax identity contradiction
    ("HN003", "CP002", "CG003"),  # recurring invoice collision
    ("HN004", "CP003", "CG004"),  # weak reference collision (different entities)
    # HN005: same reference + same tax identity, but GST amount = 2× purchase amount
    # (split invoice / amount-multiple detection)
    ("HN005", "CP005", "CG007"),
]

from decimal import Decimal

def _records():
    P = [PurchaseRecord(record_id=r["record_id"], vendor_name=r["vendor_name"] or None,
         reference=r["invoice_number"] or None, amount=Decimal(r["amount"]),
         record_date=date.fromisoformat(r["invoice_date"]),
         tax_identity=r["gstin"] or None)
         for r in csv.DictReader(io.StringIO(PURCHASES))]
    G = [GSTRecord(record_id=r["record_id"], vendor_name=r["supplier_name"] or None,
         reference=r["invoice_number"] or None, amount=Decimal(r["amount"]),
         record_date=date.fromisoformat(r["invoice_date"]),
         tax_identity=r["gstin"] or None)
         for r in csv.DictReader(io.StringIO(GSTS))]
    return P, G

def _run():
    P, G = _records()
    ctx = ReferenceEvidenceContext(
        profile=build_reference_corpus_profile([r.reference for r in P + G]),
        policy=ReferenceEvidencePolicy())
    vendor_ctx = VendorIdentityContext(corpus_profile=None)  # Optional per probe
    providers = [FinancialEvidenceProvider(), TemporalEvidenceProvider(),
                 TaxEvidenceProvider(), VendorEvidenceProvider(vendor_ctx),
                 ReferenceEvidenceProvider(ctx)]
    return ReconGraphEngine(ReconGraphConfig(), providers).reconcile(P, G), P, G

def _matched_ids(decision):
    h = getattr(getattr(decision, "selected_hypothesis", None), "hypothesis", None)
    nodes = getattr(h, "matched_nodes", None)
    assert nodes is not None, (
        f"Decision shape changed — cannot extract matched nodes from: {repr(decision)[:300]}")
    return {u.split(":")[-1] for u in nodes}

def _auto_matched_pairs(result):
    pairs = set()
    for d in result.auto_matches:
        pairs.add(frozenset(_matched_ids(d)))
    return pairs

def test_conservation_every_record_in_output():
    result, P, G = _run()
    out = set()
    for d in result.auto_matches:
        out.update(_matched_ids(d))
    for pkt in result.review_packets:
        out.update(r.record_id for r in pkt.purchases)
        out.update(r.record_id for r in pkt.gsts)
    lost = {r.record_id for r in P + G} - out
    assert not lost, f"RECORDS LOST: {sorted(lost)}"

def test_no_negative_pair_is_auto_matched():
    result, _, _ = _run()
    auto = _auto_matched_pairs(result)
    for case, p, g in NEGATIVE_PAIRS:
        assert not any({p, g} <= s for s in auto), \
            f"{case}: labeled-negative pair {p}->{g} was AUTO-MATCHED"

def test_group_hypothesis_survives_amount_multiple():
    """Verify that group hypotheses don't falsely inherit pairwise AMOUNT_MULTIPLE blocks."""
    result, _, _ = _run()
    
    # CP004 should be reviewed together with CG005 and CG006
    # because they sum up to 100,000 (CP004) = 50,000 (CG005) + 50,000 (CG006)
    # If the group hypothesis incorrectly inherits AMOUNT_MULTIPLE from the pairs 
    # (since 100k = 2 * 50k), it would be broken apart or rendered ineligible.
    
    found = False
    for pkt in result.review_packets:
        p_ids = {r.record_id for r in pkt.purchases}
        g_ids = {r.record_id for r in pkt.gsts}
        
        if "CP004" in p_ids and "CG005" in g_ids and "CG006" in g_ids:
            found = True
            break
            
    assert found, "CP004 -> CG005+CG006 group hypothesis was broken! (Check if AMOUNT_MULTIPLE blocked it at the group level)"

if __name__ == "__main__":
    result, P, G = _run()
    print(f"auto_matches={len(result.auto_matches)} review_packets={len(result.review_packets)}")
    for d in result.auto_matches:
        ids = sorted(_matched_ids(d))
        print(f"  AUTO: {ids} | {d.rationale[:90]}")
    for pkt in result.review_packets:
        print(f"  {pkt.packet_id} [{pkt.action}] P={[r.record_id for r in pkt.purchases]} "
              f"G={[r.record_id for r in pkt.gsts]}")

