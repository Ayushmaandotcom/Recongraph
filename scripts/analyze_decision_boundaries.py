import argparse
import joblib
import json
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import csv

def generate_threshold_report(dataset_path: str, model_path: str, output_path: str):
    y_true = []
    y_scores = []
    
    if not Path(dataset_path).exists():
        print(f"Dataset {dataset_path} not found. Ensure you have run the feedback extractor or synthetic generation first.")
        return

    with open(dataset_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "ml_score" in row and row["ml_score"]:
                y_scores.append(float(row["ml_score"]))
            else:
                y_scores.append(float(row.get("calibrated_ml_probability", 0)))
            label = row.get("label", "")
            y_true.append(1 if label in ("MATCH", "EXACT_MATCH", "FUZZY_MATCH") else 0)
            
    if not y_true:
        print("No valid data found in dataset.")
        return
        
    y_true = np.array(y_true)
    y_scores = np.array(y_scores)
    
    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.98, 0.99, 0.995]
    results = []
    
    for t in thresholds:
        preds = (y_scores >= t).astype(int)
        precision = precision_score(y_true, preds, zero_division=0)
        recall = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
        review_rate = (len(y_true) - (tp + tn)) / len(y_true) if len(y_true) > 0 else 0
        
        results.append({
            "threshold": t,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fp": int(fp),
            "fn": int(fn),
            "review_rate": float(review_rate)
        })
        
    html = "<html><head><style>table { border-collapse: collapse; width: 100%; } th, td { border: 1px solid #ddd; padding: 8px; text-align: left; } th { background-color: #f2f2f2; }</style></head><body>"
    html += "<h1>Decision Boundary Analysis</h1>"
    html += "<table><tr><th>Threshold</th><th>Precision</th><th>Recall</th><th>F1</th><th>False Positives</th><th>False Negatives</th><th>Review Rate</th></tr>"
    for r in results:
        html += f"<tr><td>{r['threshold']}</td><td>{r['precision']:.3f}</td><td>{r['recall']:.3f}</td><td>{r['f1']:.3f}</td><td>{r['fp']}</td><td>{r['fn']}</td><td>{r['review_rate']:.3f}</td></tr>"
    html += "</table></body></html>"
    
    with open(output_path, "w") as f:
        f.write(html)
        
    print(f"Generated {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="datasets/training/feedback_dataset.csv")
    parser.add_argument("--model", default="models/candidate_model.pkl")
    parser.add_argument("--output", default="reports/threshold_report.html")
    args = parser.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    generate_threshold_report(args.dataset, args.model, args.output)
