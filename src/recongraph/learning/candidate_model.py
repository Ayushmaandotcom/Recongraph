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

from recongraph.learning.features import extract_feature_vector, get_feature_names

def extract_features(pr, gstr2b, graph_context=None):
    return extract_feature_vector(pr, gstr2b, graph_context)

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
