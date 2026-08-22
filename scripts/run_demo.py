import csv
from pathlib import Path
from datetime import date
from decimal import Decimal
from recongraph.domain.records import PurchaseRecord, GSTRecord

def generate_demo_dataset(output_dir: str):
    """
    Generates a bespoke mock dataset hitting exactly the 8 key scenarios 
    required for demonstration of Phase 7 (7Y).
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    p_csv = out / "purchase_register_demo.csv"
    g_csv = out / "gst_records_demo.csv"
    
    # 8 Scenarios:
    # 1. Exact Match
    # 2. OCR Error (Fuzzy Reference)
    # 3. Date Shift (1 day)
    # 4. Tax Shift (Rounding)
    # 5. Missing Evidence (Purchase side missing)
    # 6. Strict Contradiction (GSTIN mismatch)
    # 7. Ambiguous Dual Candidate (One GST, two similar Purchases)
    # 8. Out of Scope Date (Past Nov 30 threshold)
    
    purchases = [
        # 1. Exact Match
        {"id": "P1", "vendor": "Acme Corp", "ref": "INV-100", "date": "2023-05-10", "amt": "5000", "gstin": "27AAAAA0000A1Z5"},
        # 2. OCR Error
        {"id": "P2", "vendor": "Globex", "ref": "INV-I01", "date": "2023-06-15", "amt": "1500", "gstin": "27BBBBB0000B1Z5"},
        # 3. Date Shift
        {"id": "P3", "vendor": "Stark Ind", "ref": "INV-300", "date": "2023-07-01", "amt": "2000", "gstin": "27CCCCC0000C1Z5"},
        # 4. Tax Shift
        {"id": "P4", "vendor": "Wayne Ent", "ref": "INV-400", "date": "2023-08-10", "amt": "4500.50", "gstin": "27DDDDD0000D1Z5"},
        # 5. Missing Evidence
        # No Purchase Record for G5
        # 6. Strict Contradiction
        {"id": "P6", "vendor": "Cyberdyne", "ref": "INV-600", "date": "2023-09-01", "amt": "3000", "gstin": "27EEEEE0000E1Z5"},
        # 7. Ambiguous Dual Candidate
        {"id": "P7A", "vendor": "Tyrell Corp", "ref": "INV-700A", "date": "2023-10-01", "amt": "1000", "gstin": "27FFFFF0000F1Z5"},
        {"id": "P7B", "vendor": "Tyrell Corp", "ref": "INV-700B", "date": "2023-10-01", "amt": "1000", "gstin": "27FFFFF0000F1Z5"},
        # 8. Out of Scope
        {"id": "P8", "vendor": "Umbrella", "ref": "INV-800", "date": "2022-12-01", "amt": "8000", "gstin": "27GGGGG0000G1Z5"},
    ]
    
    gsts = [
        # 1. Exact Match
        {"id": "G1", "vendor": "Acme Corp", "ref": "INV-100", "date": "2023-05-10", "amt": "5000", "gstin": "27AAAAA0000A1Z5"},
        # 2. OCR Error
        {"id": "G2", "vendor": "Globex", "ref": "INV-101", "date": "2023-06-15", "amt": "1500", "gstin": "27BBBBB0000B1Z5"},
        # 3. Date Shift
        {"id": "G3", "vendor": "Stark Ind", "ref": "INV-300", "date": "2023-07-02", "amt": "2000", "gstin": "27CCCCC0000C1Z5"},
        # 4. Tax Shift
        {"id": "G4", "vendor": "Wayne Ent", "ref": "INV-400", "date": "2023-08-10", "amt": "4500.00", "gstin": "27DDDDD0000D1Z5"},
        # 5. Missing Evidence
        {"id": "G5", "vendor": "LexCorp", "ref": "INV-500", "date": "2023-08-20", "amt": "6000", "gstin": "27HHHHH0000H1Z5"},
        # 6. Strict Contradiction (GSTIN mismatch!)
        {"id": "G6", "vendor": "Cyberdyne", "ref": "INV-600", "date": "2023-09-01", "amt": "3000", "gstin": "27ZZZZZ0000Z1Z5"},
        # 7. Ambiguous Dual Candidate
        {"id": "G7", "vendor": "Tyrell Corp", "ref": "INV-700A", "date": "2023-10-01", "amt": "1000", "gstin": "27FFFFF0000F1Z5"},
        # 8. Out of Scope
        {"id": "G8", "vendor": "Umbrella", "ref": "INV-800", "date": "2022-12-01", "amt": "8000", "gstin": "27GGGGG0000G1Z5"},
    ]
    
    with open(p_csv, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "vendor_name", "reference", "amount", "record_date", "gstin"])
        for p in purchases:
            writer.writerow([p["id"], p["vendor"], p["ref"], p["amt"], p["date"], p["gstin"]])
            
    with open(g_csv, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "vendor_name", "reference", "amount", "record_date", "gstin"])
        for g in gsts:
            writer.writerow([g["id"], g["vendor"], g["ref"], g["amt"], g["date"], g["gstin"]])
            
    print(f"Demo datasets generated in {output_dir}")

if __name__ == "__main__":
    generate_demo_dataset("datasets/demo")
