import argparse
import sys
import json
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from recongraph.domain.records import PurchaseRecord, GSTRecord
from recongraph.engine import ReconGraphEngine
from recongraph.config import ReconGraphConfig, DecisionConfig, DecisionPolicy, DecisionMode
from recongraph.plugins.core_providers import (
    FinancialEvidenceProvider,
    TemporalEvidenceProvider,
    TaxEvidenceProvider,
    VendorEvidenceProvider,
    ReferenceEvidenceProvider
)
from recongraph.domain.vendor.context import VendorIdentityContext, VendorCorpusProfile
from recongraph.matching.reference_evidence import ReferenceEvidenceContext, ReferenceCorpusProfile, ReferenceEvidencePolicy

def parse_args():
    parser = argparse.ArgumentParser(description="ReconGraph CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    reconcile_parser = subparsers.add_parser("reconcile", help="Run reconciliation engine")
    reconcile_parser.add_argument("--purchases", type=str, required=True, help="Path to purchases CSV")
    reconcile_parser.add_argument("--gsts", type=str, required=True, help="Path to GST records CSV")
    reconcile_parser.add_argument("--out", type=str, required=True, help="Path to output JSON")
    
    return parser.parse_args()

def load_purchases(path: str) -> list[PurchaseRecord]:
    records = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(PurchaseRecord(
                record_id=row["record_id"],
                amount=Decimal(row["amount"]),
                record_date=datetime.strptime(row["record_date"], "%Y-%m-%d").date(),
                reference=row["reference"] if row["reference"] != "" else None,
                vendor_name=row["vendor_name"],
                tax_identity=row["tax_identity"] if row["tax_identity"] != "" else None
            ))
    return records

def load_gsts(path: str) -> list[GSTRecord]:
    records = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(GSTRecord(
                record_id=row["record_id"],
                amount=Decimal(row["amount"]),
                record_date=datetime.strptime(row["record_date"], "%Y-%m-%d").date(),
                reference=row["reference"] if row["reference"] != "" else None,
                vendor_name=row["vendor_name"],
                tax_identity=row["tax_identity"] if row["tax_identity"] != "" else None
            ))
    return records

def main():
    args = parse_args()
    
    if args.command == "reconcile":
        purchases = load_purchases(args.purchases)
        gsts = load_gsts(args.gsts)
        
        # Load default contexts
        vendor_context = VendorIdentityContext(
            corpus_profile=VendorCorpusProfile(corpus_size=1000, token_document_frequencies={}, digest='default'), 
            interpreter_policy_version='1.0.0', fuzzy_minimum_length=6, fuzzy_threshold=0.85, distinctiveness_threshold=0.01
        )
        ref_context = ReferenceEvidenceContext(
            profile=ReferenceCorpusProfile(reference_count=0, normalized_reference_frequency={}, numeric_token_document_frequency={}), 
            policy=ReferenceEvidencePolicy()
        )
        
        config = ReconGraphConfig(decision_config=DecisionConfig(
            decision_mode=DecisionMode.LEGACY,
            policy=DecisionPolicy(auto_match_threshold=0.85)
        ))
        
        providers = [
            VendorEvidenceProvider(vendor_context),
            ReferenceEvidenceProvider(ref_context),
            FinancialEvidenceProvider(),
            TemporalEvidenceProvider(),
            TaxEvidenceProvider()
        ]
        
        engine = ReconGraphEngine(config=config, providers=providers)
        result = engine.reconcile(purchases, gsts)
        
        with open(args.out, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
            
        print(f"Reconciliation completed successfully. Output written to {args.out}")

if __name__ == "__main__":
    main()
