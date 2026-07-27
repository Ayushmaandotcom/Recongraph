"""
quickstart.py — executed in CI, so the docs can never rot again.

This script demonstrates the simplest possible ReconGraph workflow.
If this script fails, the README is lying.
"""
from datetime import date
from decimal import Decimal
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider, TemporalEvidenceProvider,
    TaxEvidenceProvider, VendorEvidenceProvider, ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import (
    ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy
)

# 1. Create records
purchase = PurchaseRecord(
    record_id="P-001",
    vendor_name="TechCorp Private Limited",
    reference="INV-2026-A",
    amount=Decimal("15000.00"),
    record_date=date(2026, 1, 15),
    tax_identity="07TECHC1234A1Z5",
)
gst = GSTRecord(
    record_id="G-001",
    vendor_name="TECHCORP PVT LTD",
    reference="INV-2026-A",
    amount=Decimal("15000.00"),
    record_date=date(2026, 1, 16),
    tax_identity="07TECHC1234A1Z5",
)

# 2. Setup providers with minimal context
vendor_ctx = VendorIdentityContext(
    corpus_profile=VendorCorpusProfile(
        corpus_size=1, token_document_frequencies={}, digest="1"
    ),
    interpreter_policy_version="1.0.0",
    fuzzy_minimum_length=6,
    fuzzy_threshold=0.85,
    distinctiveness_threshold=0.01,
)
ref_ctx = ReferenceEvidenceContext(
    profile=ReferenceCorpusProfile(
        reference_count=1,
        normalized_reference_frequency={"inv2026a": 1},
        numeric_token_document_frequency={"2026": 1},
    ),
    policy=ReferenceEvidencePolicy(),
)

providers = [
    FinancialEvidenceProvider(),
    TemporalEvidenceProvider(),
    TaxEvidenceProvider(),
    VendorEvidenceProvider(vendor_ctx),
    ReferenceEvidenceProvider(ref_ctx),
]

# 3. Run
result = ReconGraphEngine(ReconGraphConfig(), providers).reconcile(
    [purchase], [gst]
)

# 4. Verify
if result.auto_matches:
    print("AUTO_MATCH:", result.auto_matches[0].rationale)
elif result.review_packets:
    pkt = result.review_packets[0]
    print(f"REVIEW ({pkt.action.value}): checklist = {pkt.checklist}")
else:
    print("NO_MATCH — no hypothesis survived evaluation")

# Conservation invariant: every input record appears in the output
output_ids = set()
for m in result.auto_matches:
    if m.selected_hypothesis:
        output_ids |= m.selected_hypothesis.hypothesis.matched_nodes
for pkt in result.review_packets:
    for p in pkt.purchases:
        output_ids.add(p.record_id)
    for g in pkt.gsts:
        output_ids.add(g.record_id)

assert "P-001" in str(output_ids), "Purchase P-001 was lost!"
assert "G-001" in str(output_ids), "GST G-001 was lost!"
print("Conservation check passed — no records lost.")
