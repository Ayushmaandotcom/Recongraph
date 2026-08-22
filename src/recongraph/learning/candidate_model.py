import csv
import joblib
from pathlib import Path
from datetime import date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from rapidfuzz import fuzz

try:
    from lightgbm import LGBMClassifier
    from sklearn.calibration import CalibratedClassifierCV
    import numpy as np
    import mlflow
except ImportError:
    pass # Gracefully handle in case it's loaded without lightgbm/sklearn

from recongraph.domain.records import PurchaseRecord, GSTRecord

MODEL_PATH = Path("models/candidate_model.pkl")

def extract_features(pr: PurchaseRecord | dict, gstr2b: GSTRecord | dict, graph_context: dict = None) -> list[float]:
    # Handle both domain objects and dicts (from CSV)
    def _get(obj, attr, dict_key):
        if isinstance(obj, dict):
            return obj.get(dict_key)
        return getattr(obj, attr)
        
    if not graph_context:
        # Defaults for safe fallback
        if isinstance(pr, dict):
            graph_context = {
                "pr_node_degree": int(pr.get("pr_node_degree", 1)),
                "gst_node_degree": int(pr.get("gst_node_degree", 1)),
                "component_size": int(pr.get("component_size", 2))
            }
        else:
            graph_context = {"pr_node_degree": 1, "gst_node_degree": 1, "component_size": 2}
        
    pr_inv = str(_get(pr, "reference", "pr_invoice_no") or "")
    gs_inv = str(_get(gstr2b, "reference", "gstr2b_invoice_no") or "")
    
    pr_gstin = str(_get(pr, "tax_identity", "pr_gstin") or "")
    gs_gstin = str(_get(gstr2b, "tax_identity", "gstr2b_gstin") or "")
    
    pr_date_val = _get(pr, "record_date", "pr_date")
    gs_date_val = _get(gstr2b, "record_date", "gstr2b_date")
    
    pr_tax = _get(pr, "amount", "pr_taxable") # Using taxable or amount
    gs_tax = _get(gstr2b, "amount", "gstr2b_taxable")
    
    # 1. Levenshtein ratio (0-100)
    inv_sim = fuzz.ratio(pr_inv.lower(), gs_inv.lower()) / 100.0
    
    # 2. Date diff
    if isinstance(pr_date_val, str):
        try:
            d1 = date.fromisoformat(pr_date_val)
        except:
            d1 = date(2000, 1, 1)
    else:
        d1 = pr_date_val
        
    if isinstance(gs_date_val, str):
        try:
            d2 = date.fromisoformat(gs_date_val)
        except:
            d2 = date(2000, 1, 1)
    else:
        d2 = gs_date_val
        
    date_diff = abs((d1 - d2).days) if d1 and d2 else 999
    
    # 3. Tax diff
    try:
        t1 = float(pr_tax)
    except:
        t1 = 0.0
    try:
        t2 = float(gs_tax)
    except:
        t2 = 0.0
    tax_diff = abs(t1 - t2)
    
    # 4. GSTIN exact match
    gstin_match = 1.0 if pr_gstin == gs_gstin and pr_gstin else 0.0
    
    # 5. Graph Features
    pr_deg = float(graph_context.get("pr_node_degree", 1))
    gs_deg = float(graph_context.get("gst_node_degree", 1))
    comp_size = float(graph_context.get("component_size", 2))
    
    return [
        float(inv_sim), float(date_diff), float(tax_diff), float(gstin_match),
        pr_deg, gs_deg, comp_size
    ]

def train_model(dataset_csv: Path):
    X = []
    y = []
    
    with open(dataset_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = extract_features(row, row)
            X.append(features)
            label = row["label"]
            # Treat EXACT_MATCH and FUZZY_MATCH as positive (1), CONTRADICTION as negative (0)
            y.append(1 if label in ("EXACT_MATCH", "FUZZY_MATCH") else 0)
            
    X = np.array(X)
    y = np.array(y)
    
    # MLflow Tracking
    mlflow.set_experiment("ReconGraph_Candidate_Filter")
    with mlflow.start_run():
        # Base model - LightGBM for production scale
        base_lgbm = LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbose=-1)
        
        # Calibrate using Isotonic Regression (Platt scaling is sigmoid, Isotonic is better for larger datasets/imbalances)
        calibrated_lgbm = CalibratedClassifierCV(base_lgbm, method='isotonic', cv=3)
        calibrated_lgbm.fit(X, y)
        
        # Calculate training accuracy
        preds = calibrated_lgbm.predict(X)
        accuracy = np.mean(preds == y)
        
        # Log params & metrics
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 5)
        mlflow.log_param("calibration_method", "isotonic")
        mlflow.log_metric("train_accuracy", accuracy)
        
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(calibrated_lgbm, MODEL_PATH)
        mlflow.log_artifact(str(MODEL_PATH))
        print(f"Model trained with accuracy {accuracy:.2f} and saved to {MODEL_PATH}")

class MLCandidateFilter:
    def __init__(self):
        self.model = None
        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            
    def predict_confidence(self, pr: PurchaseRecord, gstr2b: GSTRecord, graph_context: dict = None) -> float:
        if not self.model:
            return 0.0
            
        features = extract_features(pr, gstr2b, graph_context)
        # predict_proba returns [[prob_0, prob_1]]
        probs = self.model.predict_proba([features])
        return float(probs[0][1])

if __name__ == "__main__":
    train_model(Path("datasets/training/production_dataset.csv"))
