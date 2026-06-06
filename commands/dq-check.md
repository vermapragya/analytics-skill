---
name: dq-check
description: Run a data quality audit on a table
---

# /dq-check

Run a structured data quality audit on a Snowflake table or local CSV.

## Usage

```
/dq-check <schema.table> [pk_columns] [time_col]
```

Examples:
```
/dq-check analytics.events.fct_orders order_id order_at
/dq-check ./data.csv user_id,event_date event_at
```

## Workflow

1. Load `skills/data-quality-audit/SKILL.md`
2. Run all 7 standard checks (row count, freshness, PK uniqueness, nulls, schema, distributions, day-over-day)
3. Return a status table with PASS/WARN/FAIL per check
4. If any FAIL, recommend blocking downstream analysis
5. If WARN, surface in caveats

## Output

A markdown audit report with status, issues, recommended actions, and blast radius.
