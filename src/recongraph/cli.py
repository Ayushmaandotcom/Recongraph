"""ReconGraph Command Line Interface."""
import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="ReconGraph — GST Reconciliation Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: reconcile
    reconcile_parser = subparsers.add_parser(
        "reconcile",
        help="Reconcile a purchase register against GST records and write results to JSON"
    )
    reconcile_parser.add_argument("purchases", help="Path to purchase register CSV file")
    reconcile_parser.add_argument("gst", help="Path to GST records CSV file")
    reconcile_parser.add_argument("--out", default="results.json",
                                  help="Output JSON file path (default: results.json)")

    # Subcommand: benchmark
    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="Run the ReconBench evaluation suite"
    )
    benchmark_parser.add_argument("--size", type=int, default=1000,
                                  help="Number of scenarios to generate and run")

    args = parser.parse_args()

    if args.command == "reconcile":
        _cmd_reconcile(args)
    elif args.command == "benchmark":
        from recongraph.benchmark.runner import execute_reconbench
        sys.exit(execute_reconbench(size=args.size))
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_reconcile(args: argparse.Namespace) -> None:
    """Run the engine against two CSVs and write results to JSON."""
    import csv
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
    from recongraph.serialization import ReconEncoder

    purchases_path = Path(args.purchases)
    gst_path = Path(args.gst)

    if not purchases_path.exists():
        print(f"ERROR: purchase file not found: {purchases_path}", file=sys.stderr)
        sys.exit(1)
    if not gst_path.exists():
        print(f"ERROR: GST file not found: {gst_path}", file=sys.stderr)
        sys.exit(1)

    # Load purchases
    purchases: list[PurchaseRecord] = []
    with purchases_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                purchases.append(PurchaseRecord(
                    record_id=row.get("record_id") or row.get("id", ""),
                    vendor_name=row.get("vendor_name") or row.get("supplier_name") or None,
                    reference=row.get("reference") or row.get("invoice_number") or None,
                    amount=Decimal(str(row.get("amount", "0"))),
                    record_date=date.fromisoformat(
                        row.get("record_date") or row.get("invoice_date", "2000-01-01")
                    ),
                    tax_identity=row.get("gstin") or row.get("tax_identity") or None,
                ))
            except Exception as e:
                print(f"WARNING: skipping purchase row {row}: {e}", file=sys.stderr)

    # Load GST records
    gsts: list[GSTRecord] = []
    with gst_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                gsts.append(GSTRecord(
                    record_id=row.get("record_id") or row.get("id", ""),
                    vendor_name=row.get("supplier_name") or row.get("vendor_name") or None,
                    reference=row.get("reference") or row.get("invoice_number") or None,
                    amount=Decimal(str(row.get("amount", "0"))),
                    record_date=date.fromisoformat(
                        row.get("record_date") or row.get("invoice_date", "2000-01-01")
                    ),
                    tax_identity=row.get("gstin") or row.get("tax_identity") or None,
                ))
            except Exception as e:
                print(f"WARNING: skipping GST row {row}: {e}", file=sys.stderr)

    if not purchases:
        print("ERROR: no purchase records loaded", file=sys.stderr)
        sys.exit(1)
    if not gsts:
        print("ERROR: no GST records loaded", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(purchases)} purchase record(s) and {len(gsts)} GST record(s).",
          file=sys.stderr)

    # Build providers
    all_refs = [r.reference for r in purchases + gsts]  # type: ignore[arg-type]
    corpus = build_reference_corpus_profile(all_refs)
    ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
    vendor_ctx = VendorIdentityContext(corpus_profile=None)

    from recongraph.plugins.provider import EvidenceProvider
    from recongraph.plugins.provider_v2 import EvidenceProviderV2
    providers: list[EvidenceProvider | EvidenceProviderV2] = [
        FinancialEvidenceProvider(),
        TemporalEvidenceProvider(),
        TaxEvidenceProvider(),
        VendorEvidenceProvider(vendor_ctx),
        ReferenceEvidenceProvider(ref_ctx),
    ]

    config = ReconGraphConfig()
    engine = ReconGraphEngine(config=config, providers=providers)
    result = engine.reconcile(purchases, gsts)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, cls=ReconEncoder, indent=2)

    n_auto = len(result.auto_matches)
    n_review = len(result.review_packets)
    print(f"Done. auto_matches={n_auto}  review_packets={n_review}", file=sys.stderr)
    print(f"Results written to: {out_path}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
