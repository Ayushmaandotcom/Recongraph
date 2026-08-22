import csv
import random
import uuid
from decimal import Decimal
from datetime import date, timedelta
from pathlib import Path

def generate_dataset(output_path: Path, num_exact=2500, num_fuzzy=1500, num_hard_neg=1000):
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
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        def random_gstin():
            return f"07ABCDE{random.randint(1000,9999)}F1Z5"
            
        def random_date():
            start_date = date(2026, 1, 1)
            return start_date + timedelta(days=random.randint(0, 365))
            
        def random_amount():
            return Decimal(str(random.randint(1000, 100000)))
            
        # 1. Exact Matches
        for i in range(num_exact):
            gstin = random_gstin()
            supplier = f"Supplier {i}"
            inv = f"INV-{i:05d}"
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
            
        # 2. Fuzzy Matches
        for i in range(num_fuzzy):
            gstin = random_gstin()
            supplier = f"Fuzzy Supplier {i}"
            inv_base = f"INV-{i:05d}"
            inv_fuzzy = inv_base.replace("-", "") if random.random() > 0.5 else inv_base.lower()
            if random.random() > 0.8:
                inv_fuzzy = inv_fuzzy + "A"
                
            d = random_date()
            d_fuzzy = d + timedelta(days=random.choice([-1, 1, 0, 0]))
            
            taxable = random_amount()
            igst = taxable * Decimal("0.18")
            igst_fuzzy = igst + Decimal(str(random.choice([-1, 1, 0])))
            
            writer.writerow({
                "pr_gstin": gstin, "gstr2b_gstin": gstin,
                "pr_supplier_name": supplier, "gstr2b_supplier_name": supplier + " Pvt Ltd",
                "pr_invoice_no": inv_base, "gstr2b_invoice_no": inv_fuzzy,
                "pr_date": d.isoformat(), "gstr2b_date": d_fuzzy.isoformat(),
                "pr_taxable": str(taxable), "gstr2b_taxable": str(taxable),
                "pr_igst": str(igst), "gstr2b_igst": str(igst_fuzzy),
                "pr_node_degree": 1, "gst_node_degree": 1, "component_size": 2,
                "label": "FUZZY_MATCH"
            })
            
        # 3. Hard Negatives
        for i in range(num_hard_neg):
            gstin = random_gstin()
            supplier = f"Hard Supplier {i}"
            inv_base = f"INV-{i:05d}"
            
            # Same invoice number, different amounts (different line items/invoices essentially)
            # Or sequentially off by 1
            if random.random() > 0.5:
                inv_neg = f"INV-{i+1:05d}"
                taxable = random_amount()
                taxable_neg = taxable
            else:
                inv_neg = inv_base
                taxable = random_amount()
                taxable_neg = taxable + Decimal("5000")
                
            d = random_date()
            
            igst = taxable * Decimal("0.18")
            igst_neg = taxable_neg * Decimal("0.18")
            
            writer.writerow({
                "pr_gstin": gstin, "gstr2b_gstin": gstin,
                "pr_supplier_name": supplier, "gstr2b_supplier_name": supplier,
                "pr_invoice_no": inv_base, "gstr2b_invoice_no": inv_neg,
                "pr_date": d.isoformat(), "gstr2b_date": d.isoformat(),
                "pr_taxable": str(taxable), "gstr2b_taxable": str(taxable_neg),
                "pr_igst": str(igst), "gstr2b_igst": str(igst_neg),
                "pr_node_degree": random.choice([1, 2, 3]), 
                "gst_node_degree": random.choice([1, 2]), 
                "component_size": random.choice([3, 4, 5]),
                "label": "CONTRADICTION"
            })

if __name__ == "__main__":
    out = Path("datasets/training/hackathon_dataset.csv")
    generate_dataset(out)
    print(f"Generated {out.absolute()}")
