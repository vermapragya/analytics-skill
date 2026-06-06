"""
Fit OLS linear regression with diagnostics and a readout-ready output.

Usage:
    python fit_linear.py --input data.csv --target revenue \\
        --features feature_list.txt --transform log1p \\
        --split-by month --split-date 2026-03-01
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.stats.outliers_influence import variance_inflation_factor


def load_features(path: str) -> list[str]:
    return [line.strip() for line in Path(path).read_text().splitlines() if line.strip()]


def transform_target(y: pd.Series, kind: str) -> pd.Series:
    if kind == "none":
        return y
    if kind == "log1p":
        return np.log1p(y.clip(lower=0))
    if kind == "winsorize":
        lo, hi = y.quantile(0.01), y.quantile(0.99)
        return y.clip(lower=lo, upper=hi)
    raise ValueError(f"Unknown transform: {kind}")


def back_transform(y: np.ndarray, kind: str) -> np.ndarray:
    if kind == "log1p":
        return np.expm1(y)
    return y


def temporal_split(df: pd.DataFrame, split_col: str, split_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df[split_col] = pd.to_datetime(df[split_col])
    cutoff = pd.Timestamp(split_date)
    return df[df[split_col] < cutoff].copy(), df[df[split_col] >= cutoff].copy()


def compute_vif(X: pd.DataFrame) -> pd.DataFrame:
    X_with_const = sm.add_constant(X)
    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        if col == "const":
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
        except Exception:
            vif = float("nan")
        vif_data.append({"feature": col, "vif": vif})
    return pd.DataFrame(vif_data).sort_values("vif", ascending=False)


def fit_and_evaluate(
    train: pd.DataFrame, test: pd.DataFrame,
    features: list[str], target: str, transform: str,
) -> dict:
    X_train = train[features].fillna(0)
    X_test = test[features].fillna(0)

    y_train_raw = train[target].astype(float)
    y_test_raw = test[target].astype(float)

    y_train = transform_target(y_train_raw, transform)
    y_test = transform_target(y_test_raw, transform)

    X_train_const = sm.add_constant(X_train, has_constant="add")
    X_test_const = sm.add_constant(X_test, has_constant="add")

    model = sm.OLS(y_train, X_train_const).fit(cov_type="HC3")

    y_pred_log = model.predict(X_test_const).values
    y_pred = back_transform(y_pred_log, transform)
    y_test_orig = y_test_raw.values

    rmse = float(np.sqrt(mean_squared_error(y_test_orig, y_pred)))
    mae = float(mean_absolute_error(y_test_orig, y_pred))
    r2_orig = float(r2_score(y_test_orig, y_pred))
    r2_transformed = float(r2_score(y_test, y_pred_log))

    coef_summary = pd.DataFrame({
        "feature": model.params.index,
        "beta": model.params.values,
        "se": model.bse.values,
        "t": model.tvalues.values,
        "ci_low": model.conf_int()[0].values,
        "ci_high": model.conf_int()[1].values,
    })

    std_X = X_train.std(ddof=1)
    std_y = y_train.std(ddof=1)
    coef_summary["beta_std"] = coef_summary.apply(
        lambda r: r["beta"] * (std_X.get(r["feature"], 1) / std_y) if r["feature"] in std_X.index else 0,
        axis=1,
    )
    coef_summary = coef_summary.reindex(coef_summary["beta_std"].abs().sort_values(ascending=False).index)

    vif = compute_vif(X_train)
    durbin_watson = float(sm.stats.stattools.durbin_watson(model.resid))

    return {
        "metrics": {
            "rmse": rmse, "mae": mae,
            "r2_original_scale": r2_orig,
            "r2_transformed_scale": r2_transformed,
            "n_train": len(train), "n_test": len(test),
            "target_mean": float(y_train_raw.mean()),
            "target_std": float(y_train_raw.std()),
            "durbin_watson": durbin_watson,
            "max_vif": float(vif["vif"].max()) if len(vif) else float("nan"),
        },
        "coefficients": coef_summary,
        "vif": vif,
        "model_summary": str(model.summary()),
    }


def render_report(result: dict, target: str, transform: str) -> str:
    m = result["metrics"]
    out = [f"# Linear Regression Report: {target}\n"]
    out.append(f"Transform: {transform}\n")
    out.append("## Performance")
    out.append(f"- RMSE (original scale): {m['rmse']:.3f}")
    out.append(f"- MAE: {m['mae']:.3f}")
    out.append(f"- R² (original scale): {m['r2_original_scale']:.3f}")
    out.append(f"- R² ({'transformed' if transform != 'none' else 'native'} scale): {m['r2_transformed_scale']:.3f}")
    out.append(f"- N train: {m['n_train']:,}  N test: {m['n_test']:,}")
    out.append(f"- Target mean: {m['target_mean']:.2f}  std: {m['target_std']:.2f}")
    out.append(f"- Durbin-Watson: {m['durbin_watson']:.2f}")
    out.append(f"- Max VIF: {m['max_vif']:.2f}\n")
    out.append("## Top 10 coefficients (by |β std|)")
    out.append(result["coefficients"].head(10).to_string(index=False))
    out.append("\n## VIF (top 5)")
    out.append(result["vif"].head(5).to_string(index=False))
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fit OLS linear regression")
    parser.add_argument("--input", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--features", required=True)
    parser.add_argument("--transform", choices=["none", "log1p", "winsorize"], default="none")
    parser.add_argument("--split-by", default=None)
    parser.add_argument("--split-date", default=None)
    parser.add_argument("--test-frac", type=float, default=0.25)
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

    result = fit_and_evaluate(train, test, features, args.target, args.transform)
    print(render_report(result, args.target, args.transform))
    return 0


if __name__ == "__main__":
    sys.exit(main())
