"""
Propensity Score Matching with balance diagnostics and ATT estimate.

Usage:
    python psm.py --input data.csv --outcome retained_90d \\
        --treated opted_in_beta \\
        --confounders signup_channel,plan_tier,tenure_at_opt_in,sessions_30d,purchases_30d,tickets_30d \\
        --caliper 0.1
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors


def fit_propensity(df: pd.DataFrame, treated_col: str, confounder_cols: list[str]) -> pd.Series:
    X = pd.get_dummies(df[confounder_cols], drop_first=True).fillna(0)
    y = df[treated_col].astype(int)
    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)
    return pd.Series(model.predict_proba(X)[:, 1], index=df.index, name="propensity")


def match_1to1(df: pd.DataFrame, treated_col: str, caliper: float) -> pd.DataFrame:
    treated = df[df[treated_col] == 1].copy()
    control = df[df[treated_col] == 0].copy()

    if len(treated) == 0 or len(control) == 0:
        raise ValueError("Need both treated and control units to match.")

    nn = NearestNeighbors(n_neighbors=1).fit(control[["propensity"]])
    distances, indices = nn.kneighbors(treated[["propensity"]])

    matched_control = control.iloc[indices.flatten()].reset_index(drop=True)
    treated_reset = treated.reset_index(drop=True)

    valid = distances.flatten() <= caliper
    treated_matched = treated_reset[valid].reset_index(drop=True)
    control_matched = matched_control[valid].reset_index(drop=True)

    treated_matched["_role"] = "treated"
    control_matched["_role"] = "control"
    return pd.concat([treated_matched, control_matched], ignore_index=True), valid.mean()


def std_diff(treated_vals: pd.Series, control_vals: pd.Series) -> float:
    pooled_std = np.sqrt((treated_vals.var(ddof=0) + control_vals.var(ddof=0)) / 2)
    if pooled_std == 0:
        return 0.0
    return (treated_vals.mean() - control_vals.mean()) / pooled_std


def balance_table(matched: pd.DataFrame, confounder_cols: list[str]) -> pd.DataFrame:
    treated = matched[matched["_role"] == "treated"]
    control = matched[matched["_role"] == "control"]
    rows = []
    for col in confounder_cols:
        if matched[col].dtype == "object":
            for level in matched[col].unique():
                tval = (treated[col] == level).astype(int)
                cval = (control[col] == level).astype(int)
                rows.append({
                    "covariate": f"{col}={level}",
                    "treated_mean": tval.mean(),
                    "control_mean": cval.mean(),
                    "std_diff": std_diff(tval, cval),
                })
        else:
            rows.append({
                "covariate": col,
                "treated_mean": treated[col].mean(),
                "control_mean": control[col].mean(),
                "std_diff": std_diff(treated[col], control[col]),
            })
    bal = pd.DataFrame(rows)
    bal["balanced"] = bal["std_diff"].abs() < 0.10
    return bal


def compute_att(matched: pd.DataFrame, outcome: str) -> dict:
    treated = matched[matched["_role"] == "treated"][outcome].values
    control = matched[matched["_role"] == "control"][outcome].values
    diff = treated - control
    return {
        "att": float(diff.mean()),
        "se": float(diff.std(ddof=1) / np.sqrt(len(diff))),
        "ci_low": float(diff.mean() - 1.96 * diff.std(ddof=1) / np.sqrt(len(diff))),
        "ci_high": float(diff.mean() + 1.96 * diff.std(ddof=1) / np.sqrt(len(diff))),
        "n_pairs": len(diff),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Propensity Score Matching (1:1 NN)")
    parser.add_argument("--input", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--treated", required=True, help="Binary treatment column")
    parser.add_argument("--confounders", required=True, help="Comma-separated confounder columns")
    parser.add_argument("--caliper", type=float, default=0.1)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    confounders = [c.strip() for c in args.confounders.split(",") if c.strip()]
    required = [args.outcome, args.treated] + confounders
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns {missing}", file=sys.stderr)
        return 1

    df["propensity"] = fit_propensity(df, args.treated, confounders)
    matched, match_rate = match_1to1(df, args.treated, args.caliper)

    print("# Propensity Score Matching Report\n")
    print(f"Treated: {(df[args.treated]==1).sum():,}  Controls: {(df[args.treated]==0).sum():,}")
    print(f"Matched pairs (within caliper {args.caliper}): {len(matched[matched['_role']=='treated']):,}")
    print(f"Match rate (treated matched): {match_rate:.1%}\n")

    print("## Balance table (post-match)")
    bal = balance_table(matched, confounders)
    print(bal.to_string(index=False))
    unbalanced = bal[~bal["balanced"]]
    if len(unbalanced) > 0:
        print(f"\nWARNING: {len(unbalanced)} covariate(s) have |std_diff| >= 0.10 after matching.")

    print("\n## ATT estimate")
    att = compute_att(matched, args.outcome)
    print(f"- ATT: {att['att']:+.4f}")
    print(f"- SE:  {att['se']:.4f}")
    print(f"- 95% CI: [{att['ci_low']:+.4f}, {att['ci_high']:+.4f}]")
    print(f"- Matched pairs: {att['n_pairs']:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
