"""
End-to-end A/B test analyzer.

Input CSV format:
    unit_id, variant, metric_value
    user_001, control, 0
    user_002, treatment, 1
    user_003, control, 1
    ...

Usage:
    python analyze_experiment.py --input results.csv --metric-type proportion
    python analyze_experiment.py --input results.csv --metric-type mean --control-label A --treatment-label B
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Tuple

import pandas as pd
from scipy import stats


def srm_check(counts: dict, expected_ratios: dict) -> Tuple[float, str]:
    """χ² goodness-of-fit on variant counts. Returns (p_value, status)."""
    total = sum(counts.values())
    observed = []
    expected = []
    for variant, count in counts.items():
        observed.append(count)
        expected.append(total * expected_ratios.get(variant, 1.0 / len(counts)))
    chi2, p = stats.chisquare(f_obs=observed, f_exp=expected)
    status = "PASS" if p > 0.001 else "FAIL"
    return p, status


def proportion_analysis(control: pd.Series, treatment: pd.Series) -> dict:
    n1, n2 = len(control), len(treatment)
    p1, p2 = control.mean(), treatment.mean()
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    diff = p2 - p1
    z = diff / se if se > 0 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se
    return {
        "control_n": n1,
        "treatment_n": n2,
        "control_value": p1,
        "treatment_value": p2,
        "absolute_diff": diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "relative_lift": diff / p1 if p1 > 0 else float("nan"),
        "p_value": p_value,
        "test": "two-proportion z-test",
    }


def mean_analysis(control: pd.Series, treatment: pd.Series) -> dict:
    n1, n2 = len(control), len(treatment)
    m1, m2 = control.mean(), treatment.mean()
    s1, s2 = control.std(ddof=1), treatment.std(ddof=1)
    t_stat, p_value = stats.ttest_ind(control, treatment, equal_var=False)
    se = math.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
    diff = m2 - m1
    df = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2 / (
        (s1 ** 2 / n1) ** 2 / (n1 - 1) + (s2 ** 2 / n2) ** 2 / (n2 - 1)
    )
    t_crit = stats.t.ppf(0.975, df)
    return {
        "control_n": n1,
        "treatment_n": n2,
        "control_value": m1,
        "treatment_value": m2,
        "absolute_diff": diff,
        "ci_low": diff - t_crit * se,
        "ci_high": diff + t_crit * se,
        "relative_lift": diff / m1 if m1 != 0 else float("nan"),
        "p_value": float(p_value),
        "test": "Welch's t-test",
    }


def format_readout(srm_p: float, srm_status: str, result: dict, control_label: str, treatment_label: str) -> str:
    out = []
    out.append("# Experiment Readout\n")
    out.append("## Sample Ratio Mismatch")
    out.append(f"χ² p-value: {srm_p:.4f} — **{srm_status}**\n")

    if srm_status == "FAIL":
        out.append("STOP: Assignment is broken. Do not interpret the primary metric.")
        return "\n".join(out)

    out.append("## Primary metric")
    out.append("| Variant | N | Value | |")
    out.append("|---|---|---|---|")
    out.append(f"| {control_label} | {result['control_n']:,} | {result['control_value']:.4f} | |")
    out.append(f"| {treatment_label} | {result['treatment_n']:,} | {result['treatment_value']:.4f} | |")
    out.append("")
    out.append(f"- Absolute diff: {result['absolute_diff']:+.4f} [{result['ci_low']:+.4f}, {result['ci_high']:+.4f}]")
    out.append(f"- Relative lift: {result['relative_lift']:+.2%}")
    out.append(f"- Test: {result['test']}, p = {result['p_value']:.4f}\n")

    ci_excludes_zero = (result['ci_low'] > 0) or (result['ci_high'] < 0)
    sig = "significant" if result['p_value'] < 0.05 else "not significant"
    direction = "positive" if result['absolute_diff'] > 0 else "negative"
    out.append("## Decision Hint")
    out.append(f"Result is **{sig}** in the **{direction}** direction. CI {'excludes' if ci_excludes_zero else 'includes'} zero.")
    out.append("\nNote: Decision should also consider guardrail metrics and the pre-registered MDE.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B test analyzer")
    parser.add_argument("--input", required=True, help="CSV with columns: unit_id, variant, metric_value")
    parser.add_argument("--metric-type", choices=["proportion", "mean"], required=True)
    parser.add_argument("--control-label", default="control")
    parser.add_argument("--treatment-label", default="treatment")
    parser.add_argument("--expected-control-share", type=float, default=0.5)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required_cols = {"unit_id", "variant", "metric_value"}
    if not required_cols.issubset(df.columns):
        print(f"ERROR: input must contain columns {required_cols}", file=sys.stderr)
        return 1

    dupes = df.groupby("unit_id")["variant"].nunique()
    crossover = dupes[dupes > 1]
    if len(crossover) > 0:
        print(f"WARNING: {len(crossover)} units appeared in multiple variants; excluding.", file=sys.stderr)
        df = df[~df["unit_id"].isin(crossover.index)]

    counts = df.groupby("variant")["unit_id"].nunique().to_dict()
    expected = {
        args.control_label: args.expected_control_share,
        args.treatment_label: 1 - args.expected_control_share,
    }
    srm_p, srm_status = srm_check(counts, expected)

    control = df[df["variant"] == args.control_label]["metric_value"]
    treatment = df[df["variant"] == args.treatment_label]["metric_value"]

    if args.metric_type == "proportion":
        result = proportion_analysis(control, treatment)
    else:
        result = mean_analysis(control, treatment)

    print(format_readout(srm_p, srm_status, result, args.control_label, args.treatment_label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
