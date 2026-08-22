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
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    import numpy as np
    import mlflow
except ImportError:
    pass # Gracefully handle in case it's loaded without lightgbm/sklearn

from recongraph.domain.records import PurchaseRecord, GSTRecord

MODEL_PATH = Path("models/candidate_model.pkl")

from recongraph.learning.features import extract_feature_vector, get_feature_names

def extract_features(pr, gstr2b, graph_context=None):
    return extract_feature_vector(pr, gstr2b, graph_context)

def train_model(dataset_csv: Path):
    data = []
    
    with open(dataset_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr = {
                "reference": row.get("pr_ref"),
                "supplier_name": row.get("pr_vendor"),
                "amount": row.get("pr_amount"),
                "record_date": row.get("pr_date"),
                "tax_identity": row.get("pr_gstin")
            }
            gst = {
                "reference": row.get("gst_ref"),
                "supplier_name": row.get("gst_vendor"),
                "amount": row.get("gst_amount"),
                "record_date": row.get("gst_date"),
                "tax_identity": row.get("gst_gstin")
            }
            features = extract_features(pr, gst)
            label = row.get("label", "")
            y_val = 1 if label in ("EXACT_MATCH", "FUZZY_MATCH") else 0
            data.append((features, y_val))
            
    # Shuffle data to avoid alphabetized category splitting issues
    import random
    random.seed(42)
    random.shuffle(data)
    
    X = np.array([x[0] for x in data])
    y = np.array([x[1] for x in data])
    
    # 80/20 split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # MLflow Tracking
    mlflow.set_experiment("ReconGraph_Candidate_Filter")
    with mlflow.start_run():
        # Use LGBMClassifier for pointwise binary classification
        classifier = LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbose=-1)
        classifier.fit(X_train, y_train)
        
        # Calibration (Platt vs Isotonic)
        scores = classifier.predict_proba(X_train)[:, 1]
        
        iso_calibrator = IsotonicRegression(out_of_bounds='clip')
        iso_calibrator.fit(scores, y_train)
        
        # Log params & metrics
        preds_test = classifier.predict(X_test)
        acc_test = np.mean(preds_test == y_test)
        
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 5)
        mlflow.log_param("model_type", "LGBMClassifier")
        mlflow.log_param("calibration_method", "isotonic")
        mlflow.log_metric("test_accuracy", acc_test)
        
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Save both classifier and calibrator
        model_artifact = {
            "classifier": classifier,
            "calibrator": iso_calibrator
        }
        joblib.dump(model_artifact, MODEL_PATH)
        mlflow.log_artifact(str(MODEL_PATH))
        print(f"Model trained with accuracy {acc_test:.2f} and saved to {MODEL_PATH}")

class MLCandidateFilter:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model = None
        self.calibrator = None
        if model_path.exists():
            artifact = joblib.load(model_path)
            if isinstance(artifact, dict) and "classifier" in artifact:
                self.model = artifact["classifier"]
                self.calibrator = artifact["calibrator"]
            elif isinstance(artifact, dict) and "ranker" in artifact:
                self.model = artifact["ranker"]
                self.calibrator = artifact["calibrator"]
            else:
                self.model = artifact # Legacy fallback
            
    def predict_confidence(self, pr: PurchaseRecord, gstr2b: GSTRecord, graph_context: dict = None) -> float:
        if not self.model:
            return 0.0
            
        features = extract_features(pr, gstr2b, graph_context)
        
        if hasattr(self.model, "predict_proba"):
            score = self.model.predict_proba([features])[0][1]
        else:
            score = self.model.predict([features])[0]
            
        if self.calibrator:
            prob = self.calibrator.transform([score])[0]
        else:
            prob = score
            
        return float(prob)
            
    def rank_candidates(self, pr: PurchaseRecord, candidates: List[GSTRecord], graph_contexts: List[dict]) -> List[float]:
        if not self.model or not candidates:
            return [0.0] * len(candidates)
            
        X = [extract_features(pr, c, ctx) for c, ctx in zip(candidates, graph_contexts)]
        
        if hasattr(self.model, "predict_proba"):
            scores = self.model.predict_proba(X)[:, 1]
        else:
            scores = self.model.predict(X)
            
        if self.calibrator:
            probs = self.calibrator.transform(scores)
        else:
            probs = scores
            
        return [float(p) for p in probs]

if __name__ == "__main__":
    train_model(Path("datasets/ai_production/master_dataset.csv"))
