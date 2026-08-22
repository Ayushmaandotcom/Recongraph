import csv
import json
import uuid
import random
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal

class ReconDatasetGenerator:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.categories = [
            "exact", "fuzzy", "ocr", "date_variations", "tax_variations", 
            "gstin_variations", "duplicates", "missing", "contradictions", 
            "hard_negatives", "multi_candidate", "adversarial"
        ]
        self.version = "v1-ai-prod"
        self.random = random.Random(42) # Seed for reproducibility
        
        for cat in self.categories:
            (self.base_dir / cat).mkdir(parents=True, exist_ok=True)
            
    def _generate_base_invoice(self, index: int) -> dict:
        amount = Decimal(str(round(self.random.uniform(100.0, 50000.0), 2)))
        dt = date(2023, self.random.randint(1, 12), self.random.randint(1, 28))
        return {
            "record_id": f"PR-BASE-{index}",
            "vendor_name": f"Supplier {self.random.choice(['Inc', 'Corp', 'LLC', 'Ltd'])} {index}",
            "reference": f"INV-{10000+index}",
            "amount": amount,
            "record_date": dt.isoformat(),
            "tax_identity": f"27AAAAA{1000+index}A1Z5"
        }

    def generate_dataset(self, num_samples: int = 1000):
        provenance_log = []
        
        for i in range(num_samples):
            base = self._generate_base_invoice(i)
            
            # Select mutation category
            cat = self.random.choice(self.categories)
            
            p_record = base.copy()
            p_record["record_id"] = f"PR-{cat}-{i}"
            
            g_record = base.copy()
            g_record["record_id"] = f"GST-{cat}-{i}"
            
            label = "EXACT_MATCH"
            mutation_type = "none"
            severity = "none"
            
            if cat == "exact":
                pass
            elif cat == "fuzzy":
                g_record["vendor_name"] = g_record["vendor_name"].replace("Supplier", "Suplier")
                g_record["reference"] = g_record["reference"].replace("-", "")
                label = "FUZZY_MATCH"
                mutation_type = "string_distance"
                severity = "low"
            elif cat == "ocr":
                g_record["reference"] = g_record["reference"].replace("0", "O").replace("1", "I")
                g_record["amount"] = Decimal(str(g_record["amount"])).quantize(Decimal('1.00')) + Decimal('0.01')
                label = "FUZZY_MATCH"
                mutation_type = "ocr_artifacts"
                severity = "medium"
            elif cat == "date_variations":
                dt = date.fromisoformat(g_record["record_date"])
                dt += timedelta(days=self.random.randint(-5, 5))
                g_record["record_date"] = dt.isoformat()
                label = "FUZZY_MATCH"
                mutation_type = "date_shift"
                severity = "medium"
            elif cat == "tax_variations":
                g_record["amount"] += Decimal(self.random.choice(["-1.00", "0.50", "1.00", "2.50"]))
                label = "FUZZY_MATCH"
                mutation_type = "minor_amount_diff"
                severity = "low"
            elif cat == "gstin_variations":
                g_record["tax_identity"] = g_record["tax_identity"][:-1] + "X"
                label = "NO_MATCH"
                mutation_type = "invalid_gstin_suffix"
                severity = "high"
            elif cat == "missing":
                g_record = None # Emulate missing from GSTR2B
                label = "NO_MATCH"
                mutation_type = "missing_record"
                severity = "high"
            elif cat == "contradictions":
                g_record["amount"] *= Decimal("2.0")
                label = "CONTRADICTION"
                mutation_type = "major_amount_diff"
                severity = "high"
            elif cat == "hard_negatives":
                g_record["vendor_name"] = "Different Supplier Inc"
                g_record["tax_identity"] = "27BBBBB1234B1Z5"
                label = "NO_MATCH"
                mutation_type = "different_entity"
                severity = "high"
            else:
                # Default for unhandled categories in this basic stub
                label = "EXACT_MATCH"

            # Write individual category CSVs
            cat_dir = self.base_dir / cat
            
            with open(cat_dir / f"pair_{i}.json", "w") as f:
                json.dump({
                    "pr": p_record,
                    "gst": g_record,
                    "label": label
                }, f, indent=2, default=str)
                
            prov = {
                "source": "recongraph_synthetic_generator",
                "base_invoice_id": base["record_id"],
                "packet_id": f"pkt-{i}",
                "mutation_type": mutation_type,
                "mutation_severity": severity,
                "label": label,
                "generation_seed": 42,
                "dataset_version": self.version,
                "category": cat
            }
            provenance_log.append(prov)
            
        # Write master provenance log
        with open(self.base_dir / "provenance.json", "w") as f:
            json.dump(provenance_log, f, indent=2)
            
        # Write master CSV for ML Training
        with open(self.base_dir / "master_dataset.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "packet_id", "label", "mutation_type", "severity", 
                "pr_vendor", "gst_vendor", "pr_ref", "gst_ref",
                "pr_amount", "gst_amount", "pr_date", "gst_date",
                "pr_gstin", "gst_gstin"
            ])
            for i, prov in enumerate(provenance_log):
                cat = prov["category"]
                with open(self.base_dir / cat / f"pair_{i}.json", "r") as pf:
                    pair = json.load(pf)
                    pr = pair.get("pr") or {}
                    gst = pair.get("gst") or {}
                    writer.writerow([
                        prov["packet_id"], prov["label"], prov["mutation_type"], prov["mutation_severity"],
                        pr.get("vendor_name"), gst.get("vendor_name"),
                        pr.get("reference"), gst.get("reference"),
                        pr.get("amount"), gst.get("amount"),
                        pr.get("record_date"), gst.get("record_date"),
                        pr.get("tax_identity"), gst.get("tax_identity")
                    ])

if __name__ == "__main__":
    out_dir = Path("datasets/ai_production")
    gen = ReconDatasetGenerator(out_dir)
    gen.generate_dataset(num_samples=2500)
    print(f"Dataset generated at {out_dir} with full provenance tracking.")
