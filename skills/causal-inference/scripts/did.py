"""
Difference-in-Differences estimator with cluster-robust SEs.

Input CSV format:
    unit_id, period, treated, post, outcome, [extra covariates]

Where:
    treated = 1 if unit eventually receives treatment, 0 otherwise
    post = 1 if period is after treatment date, 0 otherwise
    outcome = the metric to measure effect on

Usage:
    python did.py --input panel.csv --outcome wau --unit unit_id \\
        --treated treated --post post --controls age,country
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd
import statsmodels.formula.api as smf


def run_did(df: pd.DataFrame, outcome: str, unit: str, treated: str, post: str, controls: list[str]) -> dict:
    control_str = " + ".join(controls) if controls else ""
    if control_str:
        formula = f"{outcome} ~ {treated} * {post} + {control_str}"
    else:
        formula = f"{outcome} ~ {treated} * {post}"

    model = smf.ols(formula, data=df).fit(
        cov_type="cluster",
        cov_kwds={"groups": df[unit]},
    )

    interaction = f"{treated}:{post}"
    estimate = float(model.params.get(interaction, float("nan")))
    se = float(model.bse.get(interaction, float("nan")))
    ci = model.conf_int().loc[interaction]
    p = float(model.pvalues.get(interaction, float("nan")))

    return {
        "estimate": estimate,
        "se": se,
        "ci_low": float(ci[0]),
        "ci_high": float(ci[1]),
        "p_value": p,
        "n_obs": int(model.nobs),
        "summary": str(model.summary()),
    }


def parallel_trends_check(df: pd.DataFrame, outcome: str, unit: str, treated: str, period_col: str) -> str:
    pre = df[df[period_col] == 0] if df[period_col].dtype == bool else df.head(0)
    pre_means = (
        df[df["post"] == 0]
        .groupby([period_col, treated])[outcome]
        .mean()
        .unstack()
        .rename(columns={0: "control", 1: "treated"})
    )
    return "\n## Pre-period means (parallel trends visual check)\n" + pre_means.to_string()


def main() -> int:
    parser = argparse.ArgumentParser(description="Difference-in-Differences")
    parser.add_argument("--input", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--unit", required=True, help="Unit ID column for clustering")
    parser.add_argument("--treated", default="treated", help="Treatment dummy column")
    parser.add_argument("--post", default="post", help="Post-period dummy column")
    parser.add_argument("--period", default=None, help="Period column for parallel trends check")
    parser.add_argument("--controls", default="", help="Comma-separated additional control columns")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required = [args.outcome, args.unit, args.treated, args.post]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns {missing}", file=sys.stderr)
        return 1

    controls = [c.strip() for c in args.controls.split(",") if c.strip()]
    missing_ctrl = [c for c in controls if c not in df.columns]
    if missing_ctrl:
        print(f"ERROR: missing control columns {missing_ctrl}", file=sys.stderr)
        return 1

    result = run_did(df, args.outcome, args.unit, args.treated, args.post, controls)

    print("# DiD Estimate")
    print(f"- Effect (interaction): {result['estimate']:+.4f}")
    print(f"- SE (cluster-robust): {result['se']:.4f}")
    print(f"- 95% CI: [{result['ci_low']:+.4f}, {result['ci_high']:+.4f}]")
    print(f"- p-value: {result['p_value']:.4g}")
    print(f"- N obs: {result['n_obs']:,}")

    if args.period and args.period in df.columns:
        print(parallel_trends_check(df, args.outcome, args.unit, args.treated, args.period))

    return 0


if __name__ == "__main__":
    sys.exit(main())
