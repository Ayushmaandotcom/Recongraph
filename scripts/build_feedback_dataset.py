import sqlite3
import json
import csv
from pathlib import Path
import argparse

def extract_dataset(db_path="hitl_feedback.db", output_csv="datasets/training/feedback_dataset.csv"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check if v2 exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_v2'")
    if c.fetchone() is None:
        print("No feedback_v2 table found. No data to extract.")
        conn.close()
        return

    c.execute("""
        SELECT 
            packet_id, 
            final_human_decision, 
            deterministic_decision,
            ml_score, 
            calibrated_ml_probability,
            graph_features, 
            evidence_features,
            engine_version,
            model_version
        FROM feedback_v2
    """)
    rows = c.fetchall()
    
    if not rows:
        print("Feedback table is empty.")
        conn.close()
        return
        
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dataset = []
    all_feature_keys = set()
    
    for row in rows:
        (packet_id, human_decision, det_decision, ml_score, cal_prob,
         graph_json, evidence_json, engine_ver, model_ver) = row
         
        try:
            graph_features = json.loads(graph_json) if graph_json else {}
        except:
            graph_features = {}
            
        try:
            evidence_features = json.loads(evidence_json) if evidence_json else {}
        except:
            evidence_features = {}
            
        record = {
            "packet_id": packet_id,
            "label": human_decision,
            "deterministic_decision": det_decision,
            "engine_version": engine_ver,
            "model_version": model_ver,
            "ml_score": ml_score,
            "calibrated_ml_probability": cal_prob
        }
        
        # Flatten features
        for k, v in graph_features.items():
            record[f"graph_{k}"] = v
            all_feature_keys.add(f"graph_{k}")
            
        for k, v in evidence_features.items():
            record[f"ev_{k}"] = v
            all_feature_keys.add(f"ev_{k}")
            
        dataset.append(record)
        
    conn.close()
    
    # Write to CSV
    fieldnames = ["packet_id", "label", "deterministic_decision", "engine_version", 
                  "model_version", "ml_score", "calibrated_ml_probability"] + sorted(list(all_feature_keys))
                  
    with open(output_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in dataset:
            # Fill missing with empty string or 0.0 depending on preference
            row_to_write = {k: r.get(k, "") for k in fieldnames}
            writer.writerow(row_to_write)
            
    print(f"Extracted {len(dataset)} examples to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="hitl_feedback.db", help="Path to SQLite DB")
    parser.add_argument("--output", default="datasets/training/feedback_dataset.csv", help="Output CSV path")
    args = parser.parse_args()
    
    extract_dataset(args.db, args.output)
