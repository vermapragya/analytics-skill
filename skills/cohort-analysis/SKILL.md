---
name: cohort-analysis
description: Builds cohort retention tables and retention curves with a single consistent denominator policy. Use when the user mentions cohort, retention, retention curve, "by signup month", "by acquisition channel", N-day retention, churn over time, or lifecycle analysis.
---

# Cohort Analysis

## When to use this skill

Use when the user wants to understand how behavior changes over the **lifecycle of users**, segmented by when they entered. Triggers:

- "Show retention by signup cohort…"
- "Build a cohort table…"
- "N-day retention for…"
- "Compare cohorts by acquisition channel"
- "Is retention improving?"

If the user wants step-by-step conversion within a single session/flow, use `funnel-analysis` instead.

## Required inputs

| Input | Why it matters |
|---|---|
| Cohort anchor event | Defines when a user enters the cohort (signup, first purchase, install) |
| Cohort grain | Day, week, or month |
| Retention event | What action defines "retained" (any session, key feature use, purchase) |
| Time window per period | Daily / weekly / monthly columns |
| Lookback window | How many periods to display |

## Workflow

1. **Confirm the anchor event.** A user belongs to exactly one cohort. If they could be re-anchored (e.g., resubscribe), pre-specify the rule (first only, latest, both as separate cohorts).

2. **Pick the cohort grain.**
   - Daily: short time-scale features, fast-moving products
   - Weekly: most product analytics defaults — smooths weekday/weekend variance
   - Monthly: long sales/subscription cycles

3. **Define "retained" precisely.** Most common definitions:
   - **Any-activity**: at least one logged event in period
   - **Key-action**: specific event (e.g., completed_order)
   - **N-day**: active on day N exactly (rolling vs absolute matters)
   - **N-day-bracket**: active anywhere in days [N, N+window)

   Pick one. Document it in the readout.

4. **Pick the denominator policy.** This is the most common source of misleading cohort charts:
   - **Cohort-fixed**: divide by original cohort size every period. Curves only go down.
   - **Active-base**: divide by users active in previous period. Shows period-over-period stickiness, but can hide leaky retention.
   - **Eligible-base**: divide by users who had the *opportunity* to retain (e.g., still on the platform). Use when accounts can churn permanently.

   **Default to cohort-fixed.** Only switch if there's a specific question about period-over-period stickiness.

5. **Generate cohort matrix** using `scripts/cohort_table.sql` (Snowflake) or `scripts/cohort_table.py` (pandas).

6. **Compute key summary stats:**
   - D1, D7, D30 retention by cohort
   - "Smile curve" check (does retention stabilize after some N?)
   - Cohort-over-cohort delta (is the latest cohort retaining better than 4 cohorts ago?)

7. **Write the readout** with the matrix, summary stats, and interpretation.

## Output format

```markdown
# Cohort Analysis: <product/segment>

## Definitions
- Cohort anchor: <event> on <grain>
- Retention event: <event>
- Denominator: cohort-fixed (original cohort size)
- Lookback: <N> periods

## Summary
- Latest cohort D7 retention: <X%> (vs <Y%> 4 weeks ago, <delta>pp)
- D30 retention asymptote: <Z%>
- Retention "stabilizes" around day <N>

## Cohort table
| Cohort | Size | D1 | D7 | D14 | D30 | D60 | D90 |
|---|---|---|---|---|---|---|---|
| 2026-01 | 12,400 | 48.2% | 22.1% | 16.4% | 12.0% | 9.8% | 8.5% |
| 2026-02 | 14,100 | 51.0% | 24.8% | 18.2% | 13.5% | 10.4% | — |
| ...    | ... | ... | ... | ... | ... | ... | ... |

## Interpretation
- <Are recent cohorts improving, flat, or declining?>
- <What's the asymptote? Is the long-term retained base stable?>
- <Any anomalies — single bad cohort, missing data?>

## Caveats
- Recent cohorts have incomplete data through the latest periods (mark provisional)
- Cohort assignment uses <rule>; users who re-anchored are <treated as>
- <late-arriving events caveat if applicable>

## Next steps
- <e.g., investigate the drop in 2026-03 cohort>
- <e.g., segment by acquisition channel to find a driver>
```

## Validation checks

- [ ] Each user appears in exactly one cohort
- [ ] Denominator policy stated and consistent across all cells
- [ ] Recent incomplete cohorts flagged as provisional
- [ ] Period boundaries aligned (Mon-Sun or 1st-end-of-month, not mid-week)
- [ ] Late-arriving events caveat if data has > 24h pipeline lag

## Edge cases & failure modes

- **Mid-week cohort start**: if your cohort grain is "week" but anchor events occur all days, define week as Mon-Sun and align. Don't let cohort #1 be 3 days long.
- **Re-engaging users**: if a user goes dormant and comes back, are they in their original cohort or a new "reactivation" cohort? Pre-specify.
- **Sparse recent cohorts**: the last 1-2 periods of the matrix have <100% observation. Mark cells as "—" (no data) rather than 0% (no retention).
- **Cohort size differences**: if cohort sizes vary 10x, displaying raw percentages can mislead. Add absolute counts or use rolling averages.
- **Survivorship in subscription products**: if users *can't* churn within a billing cycle, "retention" before cycle end is meaningless. Use eligible-base denominator.

## Scripts

- `scripts/cohort_table.sql` — Snowflake template producing a cohort matrix
- `scripts/cohort_table.py` — pandas implementation for in-memory data

```bash
python scripts/cohort_table.py \
    --input events.csv \
    --user-col user_id \
    --event-time-col event_at \
    --cohort-grain week \
    --periods 12
```

## Related skills

- `funnel-analysis` — for within-session/within-flow conversion
- `survival-analysis` — when you need time-to-churn distribution with censoring
- `metric-definition` — write a clean retention metric spec
- `stakeholder-readout` — for packaging cohort findings
