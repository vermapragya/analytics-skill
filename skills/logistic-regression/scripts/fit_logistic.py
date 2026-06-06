"""
Fit and evaluate a logistic regression with proper temporal split, calibration,
and a readout-ready output.

Usage:
    python fit_logistic.py --input data.csv --target churned_30d \\
        --features feature_list.txt --split-by as_of_date --split-date 2026-02-01

Expects:
    --input: CSV with target, features, and split column
    --features: text file with one feature column name per line
    --target: name of the binary target column (0/1)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    precision_recall_curve, confusion_matrix
)
from sklearn.preprocessing import StandardScaler


def load_features(path: str) -> list[str]:
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]


def temporal_split(df: pd.DataFrame, split_col: str, split_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df[split_col] = pd.to_datetime(df[split_col])
    cutoff = pd.Timestamp(split_date)
    train = df[df[split_col] < cutoff].copy()
    test = df[df[split_col] >= cutoff].copy()
    return train, test


def fit_and_evaluate(train: pd.DataFrame, test: pd.DataFrame, features: list[str], target: str) -> dict:
    X_train, y_train = train[features].fillna(0), train[target].astype(int)
    X_test, y_test = test[features].fillna(0), test[target].astype(int)

    scaler = StandardScaler()
    X_train_std = scaler.fit_transform(X_train)
    X_test_std = scaler.transform(X_test)

    model = LogisticRegression(
        C=1.0,
        penalty="l2",
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs",
    )
    model.fit(X_train_std, y_train)

    y_proba = model.predict_proba(X_test_std)[:, 1]

    metrics = {
        "auc_roc": roc_auc_score(y_test, y_proba),
        "auc_pr": average_precision_score(y_test, y_proba),
        "brier": brier_score_loss(y_test, y_proba),
        "n_train": len(train),
        "n_test": len(test),
        "base_rate_train": y_train.mean(),
        "base_rate_test": y_test.mean(),
    }

    coef_df = pd.DataFrame({
        "feature": features,
        "coef_standardized": model.coef_[0],
        "odds_ratio": np.exp(model.coef_[0]),
    }).reindex(np.argsort(np.abs(model.coef_[0]))[::-1])

    deciles = pd.qcut(y_proba, 10, labels=False, duplicates="drop")
    calibration = pd.DataFrame({
        "decile": deciles,
        "y_true": y_test.values,
        "y_proba": y_proba,
    }).groupby("decile").agg(
        predicted=("y_proba", "mean"),
        observed=("y_true", "mean"),
        n=("y_true", "size"),
    )

    precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    best_idx = f1[:-1].argmax()
    best_threshold = thresholds[best_idx]
    y_pred = (y_proba >= best_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    threshold_summary = {
        "threshold": float(best_threshold),
        "precision": float(tp / max(tp + fp, 1)),
        "recall": float(tp / max(tp + fn, 1)),
        "flag_rate": float(y_pred.mean()),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
    }

    return {
        "metrics": metrics,
        "coefficients": coef_df,
        "calibration": calibration,
        "threshold": threshold_summary,
    }


def render_report(result: dict, target: str) -> str:
    m = result["metrics"]
    th = result["threshold"]
    out = []
    out.append(f"# Logistic Regression Report: {target}\n")
    out.append("## Performance")
    out.append(f"- AUC-ROC: {m['auc_roc']:.3f}")
    out.append(f"- AUC-PR:  {m['auc_pr']:.3f}  (base rate test: {m['base_rate_test']:.3f})")
    out.append(f"- Brier:   {m['brier']:.4f}")
    out.append(f"- N train: {m['n_train']:,}  N test: {m['n_test']:,}\n")
    out.append("## Threshold (F1-optimal)")
    out.append(f"- Threshold: {th['threshold']:.3f}")
    out.append(f"- Precision: {th['precision']:.3f}")
    out.append(f"- Recall:    {th['recall']:.3f}")
    out.append(f"- Flag rate: {th['flag_rate']:.3f}")
    out.append(f"- TP={th['tp']:,}  FP={th['fp']:,}  TN={th['tn']:,}  FN={th['fn']:,}\n")
    out.append("## Top 10 coefficients (by |effect|)")
    out.append(result["coefficients"].head(10).to_string(index=False))
    out.append("\n## Calibration (predicted vs observed by decile)")
    out.append(result["calibration"].to_string())
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fit logistic regression")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--features", required=True, help="Path to feature list file (one per line)")
    parser.add_argument("--split-by", default=None, help="Column to split on temporally")
    parser.add_argument("--split-date", default=None)
    parser.add_argument("--test-frac", type=float, default=0.25, help="Used if --split-by not given")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    features = load_features(args.features)

    missing = [f for f in features + [args.target] if f not in df.columns]
    if missing:
        print(f"ERROR: missing columns: {missing}", file=sys.stderr)
        return 1

    if args.split_by and args.split_date:
        train, test = temporal_split(df, args.split_by, args.split_date)
    else:
        shuffled = df.sample(frac=1.0, random_state=42)
        split_idx = int(len(shuffled) * (1 - args.test_frac))
        train, test = shuffled.iloc[:split_idx], shuffled.iloc[split_idx:]

    result = fit_and_evaluate(train, test, features, args.target)
    print(render_report(result, args.target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
