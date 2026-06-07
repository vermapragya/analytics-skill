"""
Funnel visualizations.

Produces three PNG charts from event-level data:
  1. waterfall.png       — end-to-end conversion from step 1 to each step
                           (bars = users at each step, gray overlay = users lost
                           since previous step)
  2. step_to_step.png    — per-transition conversion (step N -> step N+1)
                           rendered as horizontal bar chart, color-coded by health
  3. cohort_heatmap.png  — monthly cohort * funnel step end-to-end conversion %,
                           heatmap with cell annotations

Usage:
    python visualize_funnel.py \\
        --input events.csv \\
        --steps landing,signup,email_verify,profile_complete,first_action \\
        --output-dir charts/

Input CSV (long format):
    user_id, event_name, event_at

Options:
    --strict             enforce sequential ordering (step N+1 must occur after step N)
    --cohort-grain       day | week | month  (default: month)
    --user-col           default: user_id
    --event-col          default: event_name
    --time-col           default: event_at
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


GRAIN_FREQ = {"day": "D", "week": "W-MON", "month": "M"}


def build_per_user_step_times(
    events: pd.DataFrame,
    steps: list[str],
    user_col: str,
    event_col: str,
    time_col: str,
    strict: bool,
) -> pd.DataFrame:
    """For each user, find the first occurrence time of each step event.

    Returns a DataFrame indexed by user_id with one column per step holding the
    first timestamp at which that user reached the step (NaT if they didn't).
    """
    events = events.copy()
    events[time_col] = pd.to_datetime(events[time_col])

    relevant = events[events[event_col].isin(steps)]
    first_times = (
        relevant.sort_values(time_col)
        .groupby([user_col, event_col])[time_col]
        .first()
        .unstack()
    )

    for step in steps:
        if step not in first_times.columns:
            first_times[step] = pd.NaT
    first_times = first_times[steps]

    if strict:
        for i in range(1, len(steps)):
            prev_step, curr_step = steps[i - 1], steps[i]
            mask = first_times[curr_step] <= first_times[prev_step]
            first_times.loc[mask, curr_step] = pd.NaT
            mask_prev_missing = first_times[prev_step].isna()
            first_times.loc[mask_prev_missing, curr_step] = pd.NaT

    return first_times


def compute_step_counts(step_times: pd.DataFrame) -> pd.Series:
    return step_times.notna().sum()


def waterfall_chart(step_counts: pd.Series, output_path: Path) -> None:
    steps = list(step_counts.index)
    counts = step_counts.values.astype(float)
    base = counts[0] if counts[0] > 0 else 1
    pcts = counts / base * 100

    fig, ax = plt.subplots(figsize=(max(10, len(steps) * 1.5), 6))
    bar_color = "#3b82f6"
    bars = ax.bar(range(len(steps)), counts, color=bar_color, edgecolor="white", zorder=3)

    for bar, count, pct in zip(bars, counts, pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(count):,}\n{pct:.1f}%",
            ha="center", va="bottom", fontsize=10, zorder=4,
        )

    for i in range(1, len(steps)):
        lost = counts[i - 1] - counts[i]
        if lost > 0:
            ax.bar(
                i, lost, bottom=counts[i],
                color="#e5e7eb", edgecolor="white",
                width=0.78, alpha=0.55, zorder=2,
            )
            ax.text(
                i, counts[i] + lost / 2,
                f"−{int(lost):,}\nlost",
                ha="center", va="center", fontsize=9, color="#6b7280", zorder=4,
            )

    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels(steps, rotation=20, ha="right")
    ax.set_ylabel("Users")
    ax.set_title(
        f"Funnel waterfall — end-to-end conversion: {pcts[-1]:.1f}% "
        f"(step 1: {int(counts[0]):,} → final: {int(counts[-1]):,})"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.3, zorder=0)
    ax.set_ylim(0, base * 1.1)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def step_to_step_chart(step_counts: pd.Series, output_path: Path) -> None:
    steps = list(step_counts.index)
    counts = step_counts.values.astype(float)

    transitions: list[str] = []
    rates: list[float] = []
    lost: list[int] = []
    for i in range(1, len(steps)):
        prev = counts[i - 1]
        curr = counts[i]
        rate = 0.0 if prev == 0 else curr / prev * 100
        transitions.append(f"{steps[i - 1]}  →  {steps[i]}")
        rates.append(rate)
        lost.append(int(prev - curr))

    colors = ["#10b981" if r >= 80 else "#f59e0b" if r >= 50 else "#ef4444" for r in rates]

    fig, ax = plt.subplots(figsize=(11, max(4, len(transitions) * 0.85)))
    bars = ax.barh(range(len(transitions)), rates, color=colors, edgecolor="white", zorder=3)

    for bar, rate, l in zip(bars, rates, lost):
        ax.text(
            min(rate + 1.5, 103),
            bar.get_y() + bar.get_height() / 2,
            f"{rate:.1f}%   ({l:,} users lost)",
            ha="left", va="center", fontsize=10,
        )

    ax.set_yticks(range(len(transitions)))
    ax.set_yticklabels(transitions)
    ax.invert_yaxis()
    ax.set_xlim(0, 115)
    ax.set_xlabel("Step-to-step conversion (%)")
    ax.set_title("Per-transition conversion rate (green ≥80%, amber ≥50%, red <50%)")
    ax.axvline(80, color="#10b981", linestyle=":", linewidth=1, zorder=0, alpha=0.5)
    ax.axvline(50, color="#f59e0b", linestyle=":", linewidth=1, zorder=0, alpha=0.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def cohort_heatmap_chart(
    step_times: pd.DataFrame,
    steps: list[str],
    output_path: Path,
    cohort_grain: str = "month",
) -> None:
    cohort_step = steps[0]
    cohort = step_times[cohort_step].dt.to_period(GRAIN_FREQ[cohort_grain])
    df = step_times.assign(_cohort=cohort).dropna(subset=["_cohort"]).copy()
    df["_cohort"] = df["_cohort"].astype(str)

    cohort_size = df.groupby("_cohort").size().rename("cohort_size")
    reached = (
        df.groupby("_cohort")[steps]
        .apply(lambda g: g.notna().sum())
    )
    pct = reached.div(cohort_size, axis=0) * 100
    pct = pct.sort_index()

    fig, ax = plt.subplots(
        figsize=(max(8, len(steps) * 1.4), max(4, len(pct) * 0.45 + 1))
    )
    im = ax.imshow(pct.values, cmap="YlGnBu", aspect="auto", vmin=0, vmax=100)

    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels(steps, rotation=20, ha="right")
    ax.set_yticks(range(len(pct.index)))
    ax.set_yticklabels([f"{c}  (n={int(cohort_size.loc[c]):,})" for c in pct.index])

    for i in range(len(pct.index)):
        for j in range(len(steps)):
            value = pct.values[i, j]
            text_color = "white" if value > 55 else "#1f2937"
            ax.text(j, i, f"{value:.0f}%", ha="center", va="center",
                    color=text_color, fontsize=9)

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("% of cohort reaching step")

    ax.set_title(f"Cohort-wise funnel conversion ({cohort_grain}ly cohorts)")
    ax.set_xlabel("Funnel step")
    ax.set_ylabel(f"Cohort ({cohort_grain} of {steps[0]})")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Funnel visualizations")
    parser.add_argument("--input", required=True, help="Long-format events CSV")
    parser.add_argument("--steps", required=True, help="Ordered, comma-separated event names")
    parser.add_argument("--output-dir", default="charts", help="Directory for output PNGs")
    parser.add_argument("--user-col", default="user_id")
    parser.add_argument("--event-col", default="event_name")
    parser.add_argument("--time-col", default="event_at")
    parser.add_argument("--strict", action="store_true",
                        help="Enforce sequential step ordering")
    parser.add_argument("--cohort-grain", choices=["day", "week", "month"], default="month")
    args = parser.parse_args()

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    if len(steps) < 2:
        print("ERROR: need at least 2 steps", file=sys.stderr)
        return 1

    df = pd.read_csv(args.input)
    required = [args.user_col, args.event_col, args.time_col]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: missing columns {missing}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    step_times = build_per_user_step_times(
        df, steps, args.user_col, args.event_col, args.time_col, args.strict
    )
    step_counts = compute_step_counts(step_times)

    print("Step counts:")
    for step, count in step_counts.items():
        e2e_pct = count / step_counts.iloc[0] * 100 if step_counts.iloc[0] > 0 else 0
        print(f"  {step:30s}  {int(count):>10,}   ({e2e_pct:5.1f}%)")

    waterfall_chart(step_counts, output_dir / "waterfall.png")
    step_to_step_chart(step_counts, output_dir / "step_to_step.png")
    cohort_heatmap_chart(step_times, steps, output_dir / "cohort_heatmap.png", args.cohort_grain)

    print(f"\nCharts written to: {output_dir.resolve()}")
    print("  - waterfall.png")
    print("  - step_to_step.png")
    print("  - cohort_heatmap.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
