import csv
import random
from decimal import Decimal
from datetime import date, timedelta
from pathlib import Path
import sys

# Add src to path to import NoiseEngine
sys.path.append(str(Path(__file__).parent.parent / "src"))
from recongraph.learning.noise_engine import NoiseEngine

def generate_production_dataset(output_path: Path, num_exact=50000, num_fuzzy=30000, num_hard_neg=20000):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = [
        "pr_gstin", "gstr2b_gstin",
        "pr_supplier_name", "gstr2b_supplier_name",
        "pr_invoice_no", "gstr2b_invoice_no",
        "pr_date", "gstr2b_date",
        "pr_taxable", "gstr2b_taxable",
        "pr_igst", "gstr2b_igst",
        "pr_node_degree", "gst_node_degree", "component_size",
        "label"
    ]
    
    def random_gstin():
        return f"{random.randint(10,37):02d}ABCDE{random.randint(1000,9999)}F1Z5"
        
    def random_date():
        start_date = date(2025, 4, 1)
        return start_date + timedelta(days=random.randint(0, 365))
        
    def random_amount():
        return Decimal(str(random.randint(100, 500000)))

    print(f"Generating {num_exact + num_fuzzy + num_hard_neg} records to {output_path}...")
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        # 1. Exact Matches
        for i in range(num_exact):
            gstin = random_gstin()
            supplier = f"Supplier Corp {i}"
            inv = f"INV/{2025}/{i:06d}"
            d = random_date()
            taxable = random_amount()
            igst = taxable * Decimal("0.18")
            
            writer.writerow({
                "pr_gstin": gstin, "gstr2b_gstin": gstin,
                "pr_supplier_name": supplier, "gstr2b_supplier_name": supplier,
                "pr_invoice_no": inv, "gstr2b_invoice_no": inv,
                "pr_date": d.isoformat(), "gstr2b_date": d.isoformat(),
                "pr_taxable": str(taxable), "gstr2b_taxable": str(taxable),
                "pr_igst": str(igst), "gstr2b_igst": str(igst),
                "pr_node_degree": 1, "gst_node_degree": 1, "component_size": 2,
                "label": "EXACT_MATCH"
            })
            
        # 2. Fuzzy Matches (using NoiseEngine)
        for i in range(num_fuzzy):
            gstin = random_gstin()
            supplier = f"Vendor Enterprises {i}"
            inv_base = f"INV-{2025}-{i:06d}"
            d_base = random_date()
            taxable = random_amount()
            igst = taxable * Decimal("0.18")
            
            # Apply procedural noise
            inv_fuzzy = NoiseEngine.ocr_mutation(inv_base)
            inv_fuzzy = NoiseEngine.format_mutation(inv_fuzzy)
            d_fuzzy = NoiseEngine.date_mutation(d_base.isoformat())
            igst_fuzzy = str(NoiseEngine.tax_mutation(float(igst)))
            
            writer.writerow({
                "pr_gstin": gstin, "gstr2b_gstin": gstin,
                "pr_supplier_name": supplier, "gstr2b_supplier_name": supplier + " Ltd.",
                "pr_invoice_no": inv_base, "gstr2b_invoice_no": inv_fuzzy,
                "pr_date": d_base.isoformat(), "gstr2b_date": d_fuzzy,
                "pr_taxable": str(taxable), "gstr2b_taxable": str(taxable),
                "pr_igst": str(igst), "gstr2b_igst": igst_fuzzy,
                "pr_node_degree": random.choice([1, 1, 1, 2]), "gst_node_degree": random.choice([1, 1, 1, 2]), "component_size": random.choice([2, 3]),
                "label": "FUZZY_MATCH"
            })
            
        # 3. Hard Negatives (Contradictions & Mismatches)
        for i in range(num_hard_neg):
            gstin = random_gstin()
            supplier = f"Tech Solutions {i}"
            inv_base = f"TXN/{2025}/{i:06d}"
            taxable = random_amount()
            d = random_date()
            
            error_type = random.choice(["TIMING_MISMATCH", "TAX_MISMATCH", "CONTRADICTION"])
            
            inv_neg = inv_base
            taxable_neg = taxable
            igst_neg = taxable_neg * Decimal("0.18")
            d_neg = d
            
            if error_type == "TIMING_MISMATCH":
                # Shift by a whole month or year (different return period)
                d_neg = d + timedelta(days=random.choice([30, -30, 365]))
            elif error_type == "TAX_MISMATCH":
                # Completely wrong tax amount (e.g. CGST/SGST swapped for IGST)
                igst_neg = Decimal("0.00")
            elif error_type == "CONTRADICTION":
                # Sequence increment
                inv_neg = f"TXN/{2025}/{i+1:06d}"
                
            writer.writerow({
                "pr_gstin": gstin, "gstr2b_gstin": gstin,
                "pr_supplier_name": supplier, "gstr2b_supplier_name": supplier,
                "pr_invoice_no": inv_base, "gstr2b_invoice_no": inv_neg,
                "pr_date": d.isoformat(), "gstr2b_date": d_neg.isoformat(),
                "pr_taxable": str(taxable), "gstr2b_taxable": str(taxable_neg),
                "pr_igst": str(taxable * Decimal("0.18")), "gstr2b_igst": str(igst_neg),
                "pr_node_degree": random.choice([2, 3, 4]), 
                "gst_node_degree": random.choice([2, 3]), 
                "component_size": random.choice([4, 5, 6]),
                "label": error_type
            })

if __name__ == "__main__":
    out = Path("datasets/training/production_dataset.csv")
    generate_production_dataset(out)
    print(f"Generated {out.absolute()}")
