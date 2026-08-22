import csv
import json
import random
from pathlib import Path
import yaml
import sys
from datetime import date, timedelta
from faker import Faker

sys.path.append(str(Path(__file__).parent.parent / "src"))
from recongraph.learning.noise_engine import NoiseEngine

fake = Faker('en_IN')

DEFAULT_CONFIG = {
    "dataset": {
        "total_examples": 5000,
        "positive_ratio": 0.4,
        "hard_negative_ratio": 0.3,
        "missing_ratio": 0.15,
        "contradiction_ratio": 0.15
    },
    "seed": 42
}

def generate_base_record(record_id: str) -> dict:
    return {
        "base_record_id": record_id,
        "gstin": f"{random.randint(10, 99)}ABCDE{random.randint(1111, 9999)}F1Z5",
        "supplier_name": fake.company(),
        "invoice_no": f"INV-{random.randint(1000, 9999)}/{random.randint(20, 26)}",
        "date": fake.date_between(start_date='-1y', end_date='today').isoformat(),
        "taxable": round(random.uniform(1000.0, 100000.0), 2),
        "igst": 0.0,
        "cgst": 0.0,
        "sgst": 0.0
    }

def generate_dataset(config: dict, output_path: Path):
    NoiseEngine.set_seed(config["seed"])
    random.seed(config["seed"])
    Faker.seed(config["seed"])
    
    total = config["dataset"]["total_examples"]
    num_pos = int(total * config["dataset"]["positive_ratio"])
    num_hard_neg = int(total * config["dataset"]["hard_negative_ratio"])
    num_missing = int(total * config["dataset"]["missing_ratio"])
    num_contradiction = total - num_pos - num_hard_neg - num_missing
    
    dataset = []
    
    # Generate Positives (EXACT_MATCH and FUZZY_MATCH)
    for i in range(num_pos):
        base = generate_base_record(f"POS_{i}")
        if random.random() < 0.2: # 20% exact match
            gstr2b = base.copy()
            mutations = []
            label = "EXACT_MATCH"
        else:
            gstr2b, mutations = NoiseEngine.apply_realistic_noise(base)
            label = "FUZZY_MATCH"
            
        dataset.append({
            "pr_gstin": base["gstin"], "gstr2b_gstin": gstr2b["gstin"],
            "pr_supplier_name": base["supplier_name"], "gstr2b_supplier_name": gstr2b["supplier_name"],
            "pr_invoice_no": base["invoice_no"], "gstr2b_invoice_no": gstr2b["invoice_no"],
            "pr_date": base["date"], "gstr2b_date": gstr2b["date"],
            "pr_taxable": base["taxable"], "gstr2b_taxable": gstr2b["taxable"],
            "pr_igst": base["igst"], "gstr2b_igst": gstr2b["igst"],
            "pr_cgst": base["cgst"], "gstr2b_cgst": gstr2b["cgst"],
            "pr_sgst": base["sgst"], "gstr2b_sgst": gstr2b["sgst"],
            "label": label,
            "provenance": json.dumps({"source": "synthetic", "base_record_id": base["base_record_id"], "mutations": mutations, "seed": config["seed"]})
        })

    # Generate Hard Negatives (sequential, same invoice wrong tax, etc.)
    for i in range(num_hard_neg):
        base = generate_base_record(f"HNEG_{i}")
        gstr2b = base.copy()
        mutations = []
        
        scenario = random.choice(["sequential", "wrong_tax_head", "wrong_gstin", "wrong_amount"])
        if scenario == "sequential":
            # Change invoice number by 1
            num_part = ''.join(filter(str.isdigit, base['invoice_no']))
            if num_part:
                gstr2b['invoice_no'] = base['invoice_no'].replace(num_part, str(int(num_part) + 1))
            mutations.append("sequential_invoice")
        elif scenario == "wrong_tax_head":
            base['cgst'] = round(base['taxable'] * 0.09, 2)
            base['sgst'] = round(base['taxable'] * 0.09, 2)
            gstr2b['igst'] = round(base['taxable'] * 0.18, 2)
            gstr2b['cgst'] = 0.0
            gstr2b['sgst'] = 0.0
            mutations.append("tax_head_swap")
        elif scenario == "wrong_gstin":
            gstr2b['gstin'] = f"99ABCDE{random.randint(1111,9999)}F1Z5"
            mutations.append("different_gstin")
        elif scenario == "wrong_amount":
            gstr2b['taxable'] = round(base['taxable'] * random.uniform(1.1, 2.0), 2)
            mutations.append("large_amount_diff")
            
        dataset.append({
            "pr_gstin": base["gstin"], "gstr2b_gstin": gstr2b["gstin"],
            "pr_supplier_name": base["supplier_name"], "gstr2b_supplier_name": gstr2b["supplier_name"],
            "pr_invoice_no": base["invoice_no"], "gstr2b_invoice_no": gstr2b["invoice_no"],
            "pr_date": base["date"], "gstr2b_date": gstr2b["date"],
            "pr_taxable": base["taxable"], "gstr2b_taxable": gstr2b["taxable"],
            "pr_igst": base["igst"], "gstr2b_igst": gstr2b["igst"],
            "pr_cgst": base["cgst"], "gstr2b_cgst": gstr2b["cgst"],
            "pr_sgst": base["sgst"], "gstr2b_sgst": gstr2b["sgst"],
            "label": "HARD_NEGATIVE",
            "provenance": json.dumps({"source": "synthetic", "base_record_id": base["base_record_id"], "mutations": mutations, "seed": config["seed"]})
        })

    # Generate Missing
    for i in range(num_missing):
        base = generate_base_record(f"MISS_{i}")
        is_missing_in_2b = random.random() < 0.5
        label = "MISSING_IN_2B" if is_missing_in_2b else "MISSING_IN_PR"
        
        pr_rec = base if is_missing_in_2b else {k: "" for k in base}
        gstr2b_rec = {k: "" for k in base} if is_missing_in_2b else base
        
        dataset.append({
            "pr_gstin": pr_rec.get("gstin", ""), "gstr2b_gstin": gstr2b_rec.get("gstin", ""),
            "pr_supplier_name": pr_rec.get("supplier_name", ""), "gstr2b_supplier_name": gstr2b_rec.get("supplier_name", ""),
            "pr_invoice_no": pr_rec.get("invoice_no", ""), "gstr2b_invoice_no": gstr2b_rec.get("invoice_no", ""),
            "pr_date": pr_rec.get("date", ""), "gstr2b_date": gstr2b_rec.get("date", ""),
            "pr_taxable": pr_rec.get("taxable", ""), "gstr2b_taxable": gstr2b_rec.get("taxable", ""),
            "pr_igst": pr_rec.get("igst", ""), "gstr2b_igst": gstr2b_rec.get("igst", ""),
            "pr_cgst": pr_rec.get("cgst", ""), "gstr2b_cgst": gstr2b_rec.get("cgst", ""),
            "pr_sgst": pr_rec.get("sgst", ""), "gstr2b_sgst": gstr2b_rec.get("sgst", ""),
            "label": label,
            "provenance": json.dumps({"source": "synthetic", "base_record_id": base["base_record_id"], "mutations": ["missing"], "seed": config["seed"]})
        })

    # Generate Contradictions
    for i in range(num_contradiction):
        base = generate_base_record(f"CONTRA_{i}")
        gstr2b = generate_base_record(f"CONTRA_OTHER_{i}")
        
        # Share some keys to make it a candidate, but fundamentally different
        gstr2b["gstin"] = base["gstin"]
        gstr2b["date"] = base["date"]
        # Invoice number and amount are completely different
        
        dataset.append({
            "pr_gstin": base["gstin"], "gstr2b_gstin": gstr2b["gstin"],
            "pr_supplier_name": base["supplier_name"], "gstr2b_supplier_name": gstr2b["supplier_name"],
            "pr_invoice_no": base["invoice_no"], "gstr2b_invoice_no": gstr2b["invoice_no"],
            "pr_date": base["date"], "gstr2b_date": gstr2b["date"],
            "pr_taxable": base["taxable"], "gstr2b_taxable": gstr2b["taxable"],
            "pr_igst": base["igst"], "gstr2b_igst": gstr2b["igst"],
            "pr_cgst": base["cgst"], "gstr2b_cgst": gstr2b["cgst"],
            "pr_sgst": base["sgst"], "gstr2b_sgst": gstr2b["sgst"],
            "label": "CONTRADICTION",
            "provenance": json.dumps({"source": "synthetic", "base_record_id": base["base_record_id"], "mutations": ["contradiction"], "seed": config["seed"]})
        })

    # Shuffle the dataset
    random.shuffle(dataset)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
        writer.writeheader()
        writer.writerows(dataset)
    print(f"Generated {total} examples at {output_path}")

if __name__ == "__main__":
    config = DEFAULT_CONFIG
    config_path = Path("dataset_config.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            
    generate_dataset(config, Path("datasets/training/ai_dataset.csv"))
