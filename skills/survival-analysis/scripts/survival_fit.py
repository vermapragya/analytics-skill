"""
Survival analysis: KM curves by segment + Cox proportional hazards model.

Usage:
    python survival_fit.py --input subjects.csv \\
        --duration tenure_days --event churned \\
        --segment plan_tier \\
        --covariates plan_tier,support_tickets,billing_failures

Input CSV must have:
    duration column (numeric, days/weeks/etc.)
    event column (0/1)
    optional segment column
    covariate columns
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import multivariate_logrank_test


def km_summary(df: pd.DataFrame, duration_col: str, event_col: str, segment_col: str | None = None) -> pd.DataFrame:
    rows = []

    def _summary(g: pd.DataFrame, label: str) -> dict:
        kmf = KaplanMeierFitter()
        kmf.fit(g[duration_col], g[event_col], label=label)
        sf = kmf.survival_function_
        median = kmf.median_survival_time_
        max_t = g[duration_col].max()
        s30 = float(kmf.predict(min(30, max_t)))
        s90 = float(kmf.predict(min(90, max_t)))
        s180 = float(kmf.predict(min(180, max_t)))
        s365 = float(kmf.predict(min(365, max_t)))
        return {
            "segment": label,
            "n": len(g),
            "events": int(g[event_col].sum()),
            "event_rate": f"{g[event_col].mean():.1%}",
            "median_survival": median if median != float("inf") else "not reached",
            "S(30)": s30,
            "S(90)": s90,
            "S(180)": s180,
            "S(365)": s365,
        }

    rows.append(_summary(df, "Overall"))
    if segment_col and segment_col in df.columns:
        for seg, g in df.groupby(segment_col):
            rows.append(_summary(g, str(seg)))
    return pd.DataFrame(rows)


def run_logrank(df: pd.DataFrame, duration_col: str, event_col: str, segment_col: str) -> tuple[float, float]:
    res = multivariate_logrank_test(df[duration_col], df[segment_col], df[event_col])
    return float(res.test_statistic), float(res.p_value)


def fit_cox(df: pd.DataFrame, duration_col: str, event_col: str, covariate_cols: list[str]) -> dict:
    cox_df = df[[duration_col, event_col] + covariate_cols].copy()

    cat_cols = cox_df[covariate_cols].select_dtypes(include="object").columns.tolist()
    if cat_cols:
        cox_df = pd.get_dummies(cox_df, columns=cat_cols, drop_first=True)

    cph = CoxPHFitter(penalizer=0.001)
    cph.fit(cox_df, duration_col=duration_col, event_col=event_col)

    hr_table = pd.DataFrame({
        "covariate": cph.params_.index,
        "HR": cph.hazard_ratios_.values,
        "ci_low": cph.confidence_intervals_.iloc[:, 0].apply(lambda v: round(v, 4)).values,
        "ci_high": cph.confidence_intervals_.iloc[:, 1].apply(lambda v: round(v, 4)).values,
        "p_value": cph.summary["p"].values,
    })
    hr_table["ci_low"] = [float(c) for c in cph.confidence_intervals_.iloc[:, 0].apply(lambda v: 2.718281828 ** v).values]
    hr_table["ci_high"] = [float(c) for c in cph.confidence_intervals_.iloc[:, 1].apply(lambda v: 2.718281828 ** v).values]

    return {
        "hr_table": hr_table,
        "concordance": float(cph.concordance_index_),
        "n_obs": int(cph.event_observed.shape[0]),
        "n_events": int(cph.event_observed.sum()),
    }


def render_report(km: pd.DataFrame, cox: dict | None, logrank: tuple[float, float] | None) -> str:
    out = ["# Survival Analysis Report\n"]
    out.append("## Kaplan-Meier summary")
    out.append(km.to_string(index=False))

    if logrank is not None:
        chi2, p = logrank
        sig = "significantly different" if p < 0.05 else "not significantly different"
        out.append(f"\n## Log-rank test across segments")
        out.append(f"χ² = {chi2:.2f}, p = {p:.4g} — **{sig}**")

    if cox is not None:
        out.append("\n## Cox Proportional Hazards")
        out.append(f"N = {cox['n_obs']:,}, events = {cox['n_events']:,}")
        out.append(f"Concordance: {cox['concordance']:.3f}\n")
        out.append("### Hazard ratios")
        hr = cox["hr_table"].copy()
        hr["HR"] = hr["HR"].round(3)
        hr["ci_low"] = hr["ci_low"].round(3)
        hr["ci_high"] = hr["ci_high"].round(3)
        hr["p_value"] = hr["p_value"].apply(lambda p: f"{p:.4g}")
        out.append(hr.to_string(index=False))

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Survival analysis (KM + Cox PH)")
    parser.add_argument("--input", required=True)
    parser.add_argument("--duration", required=True, help="Duration column name")
    parser.add_argument("--event", required=True, help="Event indicator column (0/1)")
    parser.add_argument("--segment", default=None, help="Optional segment column for KM stratification")
    parser.add_argument("--covariates", default=None, help="Comma-separated covariate columns for Cox model")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required = [args.duration, args.event]
    if args.segment:
        required.append(args.segment)
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns {missing}", file=sys.stderr)
        return 1

    df = df.dropna(subset=[args.duration, args.event])
    df[args.event] = df[args.event].astype(int)

    km = km_summary(df, args.duration, args.event, args.segment)

    logrank = None
    if args.segment and df[args.segment].nunique() > 1:
        logrank = run_logrank(df, args.duration, args.event, args.segment)

    cox = None
    if args.covariates:
        cov_cols = [c.strip() for c in args.covariates.split(",") if c.strip()]
        missing = [c for c in cov_cols if c not in df.columns]
        if missing:
            print(f"ERROR: missing covariates {missing}", file=sys.stderr)
            return 1
        cox = fit_cox(df, args.duration, args.event, cov_cols)

    print(render_report(km, cox, logrank))
    return 0


if __name__ == "__main__":
    sys.exit(main())
