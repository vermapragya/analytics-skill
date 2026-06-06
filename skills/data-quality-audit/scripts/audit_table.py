"""
Run a data quality audit on a pandas DataFrame.

Usage:
    python audit_table.py --input data.csv --pk order_id --critical order_id,user_id,amount --time-col order_at
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

import pandas as pd


def check_row_count(df: pd.DataFrame) -> dict:
    n = len(df)
    return {
        "check": "row_count",
        "value": f"{n:,}",
        "status": "PASS" if n > 0 else "FAIL",
        "notes": "" if n > 0 else "Table is empty",
    }


def check_freshness(df: pd.DataFrame, time_col: str | None, sla_hours: float) -> dict:
    if time_col is None or time_col not in df.columns:
        return {"check": "freshness", "value": "n/a", "status": "SKIP", "notes": "No time column"}
    latest = pd.to_datetime(df[time_col]).max()
    delta_hours = (pd.Timestamp.utcnow().tz_localize(None) - latest).total_seconds() / 3600
    if delta_hours > sla_hours * 1.5:
        status = "FAIL"
    elif delta_hours > sla_hours:
        status = "WARN"
    else:
        status = "PASS"
    return {
        "check": "freshness",
        "value": f"{delta_hours:.1f}h since latest",
        "status": status,
        "notes": f"SLA: {sla_hours}h",
    }


def check_pk(df: pd.DataFrame, pk_cols: list[str]) -> dict:
    if not pk_cols:
        return {"check": "pk_uniqueness", "value": "n/a", "status": "SKIP", "notes": "No PK specified"}
    missing = [c for c in pk_cols if c not in df.columns]
    if missing:
        return {"check": "pk_uniqueness", "value": "n/a", "status": "FAIL", "notes": f"PK cols missing: {missing}"}
    dupes = df.duplicated(subset=pk_cols).sum()
    return {
        "check": "pk_uniqueness",
        "value": f"{dupes:,} dupes on ({', '.join(pk_cols)})",
        "status": "PASS" if dupes == 0 else "FAIL",
        "notes": "",
    }


def check_critical_nulls(df: pd.DataFrame, critical_cols: list[str]) -> list[dict]:
    rows = []
    for col in critical_cols:
        if col not in df.columns:
            rows.append({"check": f"nulls:{col}", "value": "missing col", "status": "FAIL", "notes": ""})
            continue
        nulls = df[col].isnull().sum()
        rows.append({
            "check": f"nulls:{col}",
            "value": f"{nulls:,} nulls",
            "status": "PASS" if nulls == 0 else "FAIL",
            "notes": "",
        })
    return rows


def check_distributions(df: pd.DataFrame, sample_cols: list[str]) -> list[dict]:
    rows = []
    for col in sample_cols:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            s = df[col].dropna()
            if len(s) == 0:
                continue
            rows.append({
                "check": f"dist:{col}",
                "value": f"p50={s.median():.2f}, p99={s.quantile(0.99):.2f}, max={s.max():.2f}",
                "status": "INFO",
                "notes": "review for outliers",
            })
        else:
            vc = df[col].value_counts(normalize=True).head(3)
            top = ", ".join(f"{k}({v:.0%})" for k, v in vc.items())
            null_pct = df[col].isnull().mean()
            status = "WARN" if null_pct > 0.05 else "INFO"
            rows.append({
                "check": f"dist:{col}",
                "value": f"top: {top}, null: {null_pct:.1%}",
                "status": status,
                "notes": "",
            })
    return rows


def check_daily_volume(df: pd.DataFrame, time_col: str | None) -> dict:
    if time_col is None or time_col not in df.columns:
        return {"check": "daily_volume", "value": "n/a", "status": "SKIP", "notes": ""}
    ts = pd.to_datetime(df[time_col])
    daily = ts.dt.date.value_counts().sort_index()
    if len(daily) < 2:
        return {"check": "daily_volume", "value": "single day", "status": "INFO", "notes": ""}
    pct_changes = daily.pct_change().abs().dropna()
    max_change = pct_changes.max()
    status = "FAIL" if max_change > 0.5 else "WARN" if max_change > 0.25 else "PASS"
    return {
        "check": "daily_volume",
        "value": f"max day-over-day delta: {max_change:+.0%}",
        "status": status,
        "notes": f"{len(daily)} days observed",
    }


def render(results: Iterable[dict]) -> str:
    out = ["# Data Quality Audit\n"]
    out.append("| Check | Result | Status | Notes |")
    out.append("|---|---|---|---|")
    fail = False
    warn = False
    for r in results:
        out.append(f"| {r['check']} | {r['value']} | {r['status']} | {r.get('notes', '')} |")
        if r["status"] == "FAIL":
            fail = True
        elif r["status"] == "WARN":
            warn = True
    summary = "**Status: FAIL**" if fail else "**Status: WARN**" if warn else "**Status: PASS**"
    out.insert(1, summary + "\n")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Data quality audit for a CSV/DataFrame")
    parser.add_argument("--input", required=True)
    parser.add_argument("--pk", default="", help="Comma-separated PK columns")
    parser.add_argument("--critical", default="", help="Comma-separated critical columns")
    parser.add_argument("--time-col", default=None)
    parser.add_argument("--sla-hours", type=float, default=24.0)
    parser.add_argument("--dist-cols", default="", help="Comma-separated columns to summarize")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    pk = [c.strip() for c in args.pk.split(",") if c.strip()]
    critical = [c.strip() for c in args.critical.split(",") if c.strip()]
    dist = [c.strip() for c in args.dist_cols.split(",") if c.strip()]

    results = []
    results.append(check_row_count(df))
    results.append(check_freshness(df, args.time_col, args.sla_hours))
    results.append(check_pk(df, pk))
    results.extend(check_critical_nulls(df, critical))
    results.extend(check_distributions(df, dist))
    results.append(check_daily_volume(df, args.time_col))

    print(render(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
