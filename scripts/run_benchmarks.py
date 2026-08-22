import time
import argparse
from pathlib import Path
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
from recongraph.matching.reference_evidence import build_reference_corpus_profile, ReferenceEvidenceContext, ReferenceEvidencePolicy

def generate_mock_data(num_records: int):
    P = []
    G = []
    for i in range(num_records):
        P.append(PurchaseRecord(f"P{i}", f"Vendor {i%10}", f"INV-{i}", Decimal("100"), date(2023,1,1), f"GSTIN{i%10}"))
        G.append(GSTRecord(f"G{i}", f"Vendor {i%10}", f"INV-{i}", Decimal("100"), date(2023,1,1), f"GSTIN{i%10}"))
    return P, G

def run_benchmark(output_path: str):
    volumes = [1000, 5000, 10000, 20000] # Kept smaller than 100k for feasible local testing
    results = []
    
    for vol in volumes:
        print(f"Benchmarking volume: {vol} records...")
        P, G = generate_mock_data(vol)
        
        t0 = time.time()
        
        corpus = build_reference_corpus_profile([r.reference for r in P + G])
        ref_ctx = ReferenceEvidenceContext(corpus, ReferenceEvidencePolicy())
        vendor_ctx = VendorIdentityContext(corpus_profile=None)
        
        providers = [
            FinancialEvidenceProvider(),
            TemporalEvidenceProvider(),
            TaxEvidenceProvider(),
            VendorEvidenceProvider(vendor_ctx),
            ReferenceEvidenceProvider(ref_ctx),
        ]
        
        engine = ReconGraphEngine(config=ReconGraphConfig(), providers=providers)
        
        t1 = time.time()
        result = engine.reconcile(P, G)
        t2 = time.time()
        
        setup_time = t1 - t0
        reconcile_time = t2 - t1
        total_time = t2 - t0
        records_per_sec = vol / (reconcile_time + 1e-5)
        
        results.append({
            "volume": vol,
            "setup_time": setup_time,
            "reconcile_time": reconcile_time,
            "total_time": total_time,
            "records_per_sec": records_per_sec
        })
        
    html = """<html>
<head><style>
    body { font-family: sans-serif; padding: 20px; }
    table { border-collapse: collapse; width: 80%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
</style></head>
<body>
    <h1>Performance Benchmark Report</h1>
    <table>
        <tr><th>Volume (Records)</th><th>Setup Time (s)</th><th>Reconcile Time (s)</th><th>Total Time (s)</th><th>Throughput (records/sec)</th></tr>"""
        
    for r in results:
        html += f"<tr><td>{r['volume']}</td><td>{r['setup_time']:.3f}</td><td>{r['reconcile_time']:.3f}</td><td>{r['total_time']:.3f}</td><td>{r['records_per_sec']:.1f}</td></tr>"
        
    html += "</table></body></html>"
    
    with open(output_path, "w") as f:
        f.write(html)
        
    print(f"Generated benchmark report at {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="reports/performance_report.html")
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    run_benchmark(args.output)
