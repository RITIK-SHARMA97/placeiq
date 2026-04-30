"""
PlaceIQ — Model Training Pipeline
Trains 3 placement classifiers (3mo/6mo/12mo) + salary regressor
Saves models + SHAP explainer + metadata
"""

import numpy as np
import pandas as pd
import json
import pickle
import warnings
import os
from pathlib import Path
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, mean_absolute_error
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import shap

# ─── Config ──────────────────────────────────────────────────────
FEATURE_COLS = [
    "cgpa", "cgpa_sem_prev1", "cgpa_sem_prev2",
    "backlogs", "sem_gap_years",
    "num_internships", "internship_quality",
    "num_certifications", "has_github", "has_linkedin",
    "job_portal_activity", "city_labor_demand",
    "sector_growth_index", "institute_tier"
]

FEATURE_LABELS = {
    "cgpa":                   "Current CGPA",
    "cgpa_sem_prev1":         "CGPA last semester",
    "cgpa_sem_prev2":         "CGPA 2 semesters ago",
    "backlogs":               "Number of backlogs",
    "sem_gap_years":          "Academic gap years",
    "num_internships":        "Internships completed",
    "internship_quality":     "Internship quality",
    "num_certifications":     "Certifications earned",
    "has_github":             "Active GitHub profile",
    "has_linkedin":           "LinkedIn presence",
    "job_portal_activity":    "Job portal engagement",
    "city_labor_demand":      "City labor demand",
    "sector_growth_index":    "Sector growth index",
    "institute_tier":         "Institute tier",
}

HORIZONS = {
    "3mo":  "is_placed_3mo",
    "6mo":  "is_placed_6mo",
    "12mo": "is_placed_12mo",
}

XGB_PARAMS = dict(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.08,
    subsample=0.85,
    colsample_bytree=0.85,
    min_child_weight=3,
    reg_alpha=0.1,
    reg_lambda=1.0,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1,
)

ARTIFACTS = Path(__file__).parent / "artifacts"


def load_data():
    path = Path(__file__).parent.parent / "data" / "students.csv"
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} students, {len(df.columns)} columns")
    return df


def train_placement_models(df):
    X = df[FEATURE_COLS].copy()
    models, metrics = {}, {}

    for horizon, target_col in HORIZONS.items():
        y = df[target_col]
        print(f"\n{'─'*50}")
        print(f"Training {horizon} placement model  (positive={y.mean():.1%})")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        model = xgb.XGBClassifier(**XGB_PARAMS)
        model.fit(X_train, y_train, verbose=False)

        proba = model.predict_proba(X_test)[:, 1]
        auc   = roc_auc_score(y_test, proba)
        acc   = accuracy_score(y_test, (proba >= 0.5).astype(int))

        lr = LogisticRegression(max_iter=500, random_state=42)
        lr.fit(X_train, y_train)
        lr_auc = roc_auc_score(y_test, lr.predict_proba(X_test)[:, 1])

        print(f"  XGBoost AUC={auc:.4f}  Acc={acc:.3f}  | LR baseline={lr_auc:.4f}  Δ=+{auc-lr_auc:.4f}")

        models[horizon]  = model
        metrics[horizon] = {"auc": auc, "accuracy": acc, "lr_baseline_auc": lr_auc,
                             "n_train": len(X_train), "n_test": len(X_test)}
    return models, metrics


def train_salary_models(df):
    X = df[FEATURE_COLS].copy()
    y = np.log1p(df["expected_salary"])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"\n{'─'*50}")
    print("Training salary quantile models (P25 / P50 / P75)")

    salary_models, salary_metrics = {}, {}
    for q, label in [(0.25, "p25"), (0.50, "p50"), (0.75, "p75")]:
        m = xgb.XGBRegressor(
            n_estimators=200, max_depth=5, learning_rate=0.08,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.5, reg_lambda=1.5, random_state=42,
            objective="reg:quantileerror", quantile_alpha=q,
        )
        m.fit(X_train, y_train, verbose=False)
        mae = mean_absolute_error(np.expm1(y_test), np.expm1(m.predict(X_test)))
        print(f"  {label.upper()} MAE: ₹{mae:,.0f}")
        salary_models[label]  = m
        salary_metrics[label] = {"mae": float(mae)}
    return salary_models, salary_metrics


def build_shap_explainer(models, df):
    print(f"\n{'─'*50}")
    print("Building SHAP TreeExplainer (6mo model)...")
    X = df[FEATURE_COLS].copy()
    explainer = shap.TreeExplainer(models["6mo"])
    sv = explainer.shap_values(X)
    mean_abs = np.abs(sv).mean(axis=0)
    imp = pd.DataFrame({"feature": FEATURE_COLS,
                         "label":   [FEATURE_LABELS[f] for f in FEATURE_COLS],
                         "mean_abs_shap": mean_abs}).sort_values("mean_abs_shap", ascending=False)
    print("  Top 5 features:")
    for _, r in imp.head(5).iterrows():
        print(f"    {r['label']}: {r['mean_abs_shap']:.4f}")
    return explainer, imp


def save_artifacts(placement, salary, explainer, imp, pm, sm, df):
    ARTIFACTS.mkdir(exist_ok=True)

    for h, m in placement.items():
        with open(ARTIFACTS / f"model_placement_{h}.pkl", "wb") as f:
            pickle.dump(m, f)

    for lb, m in salary.items():
        with open(ARTIFACTS / f"model_salary_{lb}.pkl", "wb") as f:
            pickle.dump(m, f)

    with open(ARTIFACTS / "shap_explainer.pkl", "wb") as f:
        pickle.dump(explainer, f)

    imp.to_csv(ARTIFACTS / "feature_importance.csv", index=False)

    meta = {
        "feature_columns": FEATURE_COLS,
        "feature_labels":  FEATURE_LABELS,
        "placement_metrics": pm,
        "salary_metrics":    sm,
        "n_students": len(df),
        "trained_at": pd.Timestamp.now().isoformat(),
        "model_version": "1.0.0",
    }
    with open(ARTIFACTS / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2, default=str)

    print(f"\n{'─'*50}")
    print(f"Artifacts saved → {ARTIFACTS}/")
    for name in ["model_placement_3mo.pkl","model_placement_6mo.pkl","model_placement_12mo.pkl",
                 "model_salary_p25.pkl","model_salary_p50.pkl","model_salary_p75.pkl",
                 "shap_explainer.pkl","feature_importance.csv","metadata.json"]:
        print(f"  ✓ {name}")


def main():
    print("="*50)
    print("PlaceIQ — Model Training Pipeline")
    print("="*50)
    df = load_data()
    pm, p_metrics = train_placement_models(df)
    sm, s_metrics = train_salary_models(df)
    explainer, imp = build_shap_explainer(pm, df)
    save_artifacts(pm, sm, explainer, imp, p_metrics, s_metrics, df)
    print("\n" + "="*50)
    print("Training complete!")
    for h, m in p_metrics.items():
        print(f"  {h}: AUC={m['auc']:.4f}  Acc={m['accuracy']:.3f}")


if __name__ == "__main__":
    main()
