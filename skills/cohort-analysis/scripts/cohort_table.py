"""
Build a cohort retention table from an events CSV.

Input CSV (long format):
    user_id, event_at, event_name (optional)

Usage:
    python cohort_table.py --input events.csv --cohort-grain week --periods 12
    python cohort_table.py --input events.csv --cohort-grain week --anchor-event signup --percentages
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd


GRAIN_FREQ = {"day": "D", "week": "W-MON", "month": "MS"}
GRAIN_DELTA = {"day": "D", "week": "W", "month": "M"}


def build_cohort_table(
    events: pd.DataFrame,
    user_col: str,
    time_col: str,
    grain: str,
    periods: int,
    anchor_event: str | None = None,
    event_name_col: str = "event_name",
) -> pd.DataFrame:
    if anchor_event is not None and event_name_col in events.columns:
        anchor_df = events[events[event_name_col] == anchor_event]
    else:
        anchor_df = events

    cohort_anchor = (
        anchor_df.groupby(user_col)[time_col]
        .min()
        .dt.to_period(GRAIN_FREQ[grain])
        .reset_index()
        .rename(columns={time_col: "cohort_period"})
    )

    activity = events.copy()
    activity["activity_period"] = activity[time_col].dt.to_period(GRAIN_FREQ[grain])
    activity = activity[[user_col, "activity_period"]].drop_duplicates()

    joined = activity.merge(cohort_anchor, on=user_col)
    joined["period_n"] = (
        joined["activity_period"].astype(int) - joined["cohort_period"].astype(int)
    )
    joined = joined[(joined["period_n"] >= 0) & (joined["period_n"] <= periods)]

    table = (
        joined.groupby(["cohort_period", "period_n"])[user_col]
        .nunique()
        .unstack(fill_value=0)
    )

    cohort_size = cohort_anchor.groupby("cohort_period").size().rename("cohort_size")
    out = table.join(cohort_size)
    out = out[["cohort_size"] + [c for c in table.columns]]
    out.columns = ["cohort_size"] + [f"p{c}" for c in table.columns]
    return out.sort_index()


def to_percentages(table: pd.DataFrame) -> pd.DataFrame:
    pct = table.copy()
    period_cols = [c for c in pct.columns if c.startswith("p")]
    for col in period_cols:
        pct[col] = (pct[col] / pct["cohort_size"]).round(4)
    return pct


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a cohort retention table")
    parser.add_argument("--input", required=True)
    parser.add_argument("--user-col", default="user_id")
    parser.add_argument("--event-time-col", default="event_at")
    parser.add_argument("--cohort-grain", choices=["day", "week", "month"], default="week")
    parser.add_argument("--periods", type=int, default=12)
    parser.add_argument("--anchor-event", default=None, help="Filter to this event for cohort anchor (uses event_name col)")
    parser.add_argument("--event-name-col", default="event_name")
    parser.add_argument("--percentages", action="store_true", help="Output retention percentages instead of counts")
    parser.add_argument("--output", default=None, help="Optional CSV output path")
    args = parser.parse_args()

    df = pd.read_csv(args.input, parse_dates=[args.event_time_col])
    table = build_cohort_table(
        events=df,
        user_col=args.user_col,
        time_col=args.event_time_col,
        grain=args.cohort_grain,
        periods=args.periods,
        anchor_event=args.anchor_event,
        event_name_col=args.event_name_col,
    )
    if args.percentages:
        table = to_percentages(table)

    if args.output:
        table.to_csv(args.output)
        print(f"Wrote cohort table to {args.output}", file=sys.stderr)
    else:
        print(table.to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
