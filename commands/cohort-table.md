---
name: cohort-table
description: Build a cohort retention table from event data
---

# /cohort-table

Build a cohort retention table from raw event data.

## Usage

```
/cohort-table
```

Then provide:
- Event table (Snowflake table name or CSV path)
- Cohort anchor event (e.g., signup)
- Retention event (e.g., any activity, or specific action)
- Cohort grain (day, week, month)
- Lookback periods

## Workflow

1. Load `skills/cohort-analysis/SKILL.md` for the workflow
2. Verify input data with `skills/data-quality-audit/SKILL.md` checks
3. Generate cohort table SQL (Snowflake) or pandas code, depending on input
4. Compute summary stats: D1/D7/D30 retention, cohort-over-cohort delta
5. Produce a formatted table + brief interpretation

## Output

- Cohort matrix (rows = cohort, cols = periods, cells = retention %)
- Summary stats
- One-paragraph interpretation
- Caveats (incomplete recent cohorts, denominator policy)
