import pandas as pd
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))
from recongraph.learning.candidate_model import extract_features

from evidently import Report
from evidently.presets import DataDriftPreset

def build_feature_df(dataset_csv: Path) -> pd.DataFrame:
    features_list = []
    with open(dataset_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            feats = extract_features(row, row)
            features_list.append({
                "invoice_similarity": feats[0],
                "date_difference_days": feats[1],
                "tax_difference": feats[2],
                "gstin_exact_match": feats[3],
                "pr_node_degree": feats[4],
                "gst_node_degree": feats[5],
                "component_size": feats[6]
            })
    return pd.DataFrame(features_list)

def detect_drift():
    print("Loading Reference Dataset (Hackathon)...")
    ref_df = build_feature_df(Path("datasets/training/hackathon_dataset.csv"))
    
    print("Loading Current Dataset (Production)...")
    cur_df = build_feature_df(Path("datasets/training/production_dataset.csv"))
    
    # We will sample current dataset to make report generation faster
    if len(cur_df) > 10000:
        cur_df = cur_df.sample(n=10000, random_state=42)
        
    print("Generating Drift Report...")
    drift_report = Report(metrics=[DataDriftPreset()])
    snapshot = drift_report.run(current_data=cur_df, reference_data=ref_df)
    
    out_path = Path("drift_report.html")
    snapshot.save_html(str(out_path))
    print(f"Drift Report saved to {out_path.absolute()}")

if __name__ == "__main__":
    detect_drift()
