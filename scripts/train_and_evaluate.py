import csv
import numpy as np
import joblib
from pathlib import Path
import sys

from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from lightgbm import LGBMClassifier

sys.path.append(str(Path(__file__).parent.parent / "src"))
from recongraph.learning.features import extract_feature_vector, get_feature_names

def load_data(dataset_csv: Path):
    X_raw = []
    y_raw = []
    groups = []
    
    with open(dataset_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # We want to predict if it's a MATCH (EXACT or FUZZY) vs Non-Match (MISSING, CONTRADICTION, HARD_NEGATIVE)
            is_match = 1 if row["label"] in ["EXACT_MATCH", "FUZZY_MATCH"] else 0
            
            # Using supplier GSTIN as the group to prevent data leakage
            group_id = row["pr_gstin"] or row["gstr2b_gstin"] or "UNKNOWN"
            
            X_raw.append(row)
            y_raw.append(is_match)
            groups.append(group_id)
            
    return X_raw, np.array(y_raw), np.array(groups)

def evaluate_model(name, y_true, y_prob):
    y_pred = (y_prob >= 0.5).astype(int)
    print(f"--- {name} ---")
    print(classification_report(y_true, y_pred, digits=4))
    
    # Check if there's only one class in y_true, avoid AUC errors
    if len(np.unique(y_true)) > 1:
        roc_auc = roc_auc_score(y_true, y_prob)
        pr_auc = average_precision_score(y_true, y_prob)
        brier = brier_score_loss(y_true, y_prob)
        print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | Brier Score: {brier:.4f}")
    print("\n")

def run_evaluation():
    dataset_path = Path("datasets/training/ai_dataset.csv")
    if not dataset_path.exists():
        print("Dataset not found. Run generate_ai_dataset.py first.")
        return

    X_raw, y, groups = load_data(dataset_path)
    
    print(f"Total dataset size: {len(y)}")
    
    # Train/Test Split by Group
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X_raw, y, groups))
    
    X_train_raw = [X_raw[i] for i in train_idx]
    y_train = y[train_idx]
    X_test_raw = [X_raw[i] for i in test_idx]
    y_test = y[test_idx]
    
    print(f"Train size: {len(y_train)}, Test size: {len(y_test)}")
    
    # Feature Extraction
    print("Extracting features...")
    X_train = np.array([extract_feature_vector(row, row) for row in X_train_raw])
    X_test = np.array([extract_feature_vector(row, row) for row in X_test_raw])
    
    feature_names = get_feature_names()
    
    # Baseline 1: Deterministic
    # A true deterministic match: exact invoice, exact GSTIN, exact date, exact tax
    y_prob_det = np.array([1.0 if (row['pr_invoice_no'] == row['gstr2b_invoice_no'] and
                                   row['pr_gstin'] == row['gstr2b_gstin'] and
                                   row['pr_date'] == row['gstr2b_date'] and
                                   row['pr_taxable'] == row['gstr2b_taxable']) else 0.0
                           for row in X_test_raw])
    evaluate_model("Baseline 1 (Deterministic)", y_test, y_prob_det)

    # Baseline 2: Fuzzy Heuristic
    # Just Levenshtein > 0.8 and tax diff < 5
    inv_sim_idx = feature_names.index('inv_levenshtein_sim')
    tax_diff_idx = feature_names.index('taxable_diff')
    y_prob_fuzzy = np.array([1.0 if (x[inv_sim_idx] > 0.8 and x[tax_diff_idx] < 5.0) else 0.0 for x in X_test])
    evaluate_model("Baseline 2 (Fuzzy Heuristic)", y_test, y_prob_fuzzy)

    # Baseline 3: Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    y_prob_lr = lr.predict_proba(X_test)[:, 1]
    evaluate_model("Baseline 3 (Logistic Regression)", y_test, y_prob_lr)

    # Baseline 4: Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    y_prob_rf = rf.predict_proba(X_test)[:, 1]
    evaluate_model("Baseline 4 (Random Forest)", y_test, y_prob_rf)

    # Model 5: LightGBM (Calibrated)
    lgbm = LGBMClassifier(n_estimators=200, learning_rate=0.05, random_state=42)
    calibrated_lgbm = CalibratedClassifierCV(lgbm, method='isotonic', cv=3)
    calibrated_lgbm.fit(X_train, y_train)
    y_prob_lgbm = calibrated_lgbm.predict_proba(X_test)[:, 1]
    evaluate_model("Model 5 (Calibrated LightGBM)", y_test, y_prob_lgbm)

    # Feature Importance (from uncalibrated LGBM for interpretability)
    lgbm.fit(X_train, y_train)
    importances = lgbm.feature_importances_
    print("--- LightGBM Feature Importances ---")
    feat_imps = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    for name, imp in feat_imps:
        print(f"{name}: {imp}")

    # Save Model
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    joblib.dump(calibrated_lgbm, model_dir / "candidate_model.pkl")
    print(f"\nModel saved to {model_dir / 'candidate_model.pkl'}")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    run_evaluation()
