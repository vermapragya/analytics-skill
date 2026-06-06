---
name: data-quality-audit
description: Runs a structured audit on a table covering nulls, duplicates, freshness, schema drift, primary key uniqueness, value distributions, and referential integrity. Use when the user mentions data quality, DQ check, audit this table, "can I trust this data", null check, dedup, freshness, or before relying on a new source.
---

# Data Quality Audit

## When to use this skill

Use **before** trusting data for analysis, modeling, or reporting. Triggers:

- "Audit this table"
- "Check the data quality of…"
- "Can I trust this data?"
- "Is fct_orders fresh?"
- "Are there duplicates in…"
- Before kicking off any modeling skill (`logistic-regression`, `survival-analysis`, etc.)

## Required inputs

| Input | Why it matters |
|---|---|
| Table name | What to audit |
| Stated primary key | What grain rows should be at |
| Expected freshness | How recent data should be |
| Critical columns | Columns where null/garbage breaks downstream |
| Foreign key columns | For referential integrity |

## Workflow

Run these in order. Stop and report if any check FAILS critically.

### 1. Row count and time range
```sql
select
    count(*) as row_count,
    min(<time_col>) as earliest,
    max(<time_col>) as latest,
    datediff('hour', max(<time_col>), current_timestamp) as hours_since_latest
from <table>;
```

**Expected:** non-zero rows, latest timestamp within freshness SLA.  
**Fail if:** row count = 0, or `hours_since_latest` > freshness SLA × 1.5.

### 2. Primary key uniqueness
```sql
select <pk_cols>, count(*) as dupes
from <table>
group by <pk_cols>
having count(*) > 1
limit 100;
```

**Expected:** zero rows.  
**Fail if:** any duplicates. Investigate before proceeding.

### 3. Null check on critical columns
```sql
select
    sum(case when <col_1> is null then 1 else 0 end) as nulls_col_1,
    sum(case when <col_2> is null then 1 else 0 end) as nulls_col_2,
    ...
from <table>;
```

**Expected:** zero nulls in PK and critical columns.  
**Warn if:** > 1% nulls in non-critical columns.

### 4. Schema check
```sql
-- Snowflake
describe table <table>;
-- or
select column_name, data_type
from information_schema.columns
where table_name = '<table_upper>';
```

**Expected:** columns and types match documentation.  
**Fail if:** columns added/removed/retyped since last documented schema.

### 5. Value distribution sanity
```sql
-- For categorical columns
select <col>, count(*), count(*) * 1.0 / sum(count(*)) over () as share
from <table>
group by 1
order by 2 desc
limit 20;

-- For numeric columns
select
    min(<col>),
    percentile_cont(0.25) within group (order by <col>) as p25,
    median(<col>) as p50,
    percentile_cont(0.75) within group (order by <col>) as p75,
    percentile_cont(0.99) within group (order by <col>) as p99,
    max(<col>),
    avg(<col>),
    stddev(<col>)
from <table>;
```

**Expected:** distributions match prior periods / business expectations.  
**Warn if:** new category dominates, or numeric tail spans multiple orders of magnitude unexpectedly.

### 6. Referential integrity
```sql
select count(*) as orphan_rows
from <child_table> c
left join <parent_table> p on c.<fk_col> = p.<pk_col>
where p.<pk_col> is null;
```

**Expected:** zero orphans.  
**Warn if:** > 0.1% orphans (may indicate join logic issues downstream).

### 7. Time-series gaps (for event tables)
```sql
with daily_counts as (
    select date_trunc('day', <time_col>) as d, count(*) as cnt
    from <table>
    where <time_col> >= dateadd('day', -30, current_date)
    group by 1
)
select d, cnt,
    lag(cnt) over (order by d) as prev_cnt,
    cnt * 1.0 / lag(cnt) over (order by d) as pct_change
from daily_counts
order by d;
```

**Warn if:** any day's count is < 50% or > 200% of prior day's count.  
**Fail if:** any day has 0 rows when prior days have data (pipeline failure).

## Output format

```markdown
# Data Quality Audit: <schema.table>

## TL;DR
**Status:** <PASS | WARN | FAIL>

<one-line summary of any issues>

## Checks
| Check | Result | Status | Notes |
|---|---|---|---|
| Row count | 4,872,109 | PASS | |
| Freshness | 2.1h since latest | PASS | SLA: 24h |
| PK uniqueness | 0 dupes on (user_id, event_date) | PASS | |
| Critical nulls | 0 nulls in user_id, event_at | PASS | |
| Schema | 14 cols, matches docs | PASS | |
| Value distributions | event_name top 3 = login (62%), view (28%), purchase (8%) | PASS | normal |
| Referential integrity | 0 orphan user_id vs dim_users | PASS | |
| Time-series gaps | No missing days; max daily delta +18% | PASS | |

## Issues found
<none, or:>
- **FAIL: 142 duplicate PK rows.** Pipeline likely double-loaded 2026-04-12. Investigate `dbt_upload_log` for that date.
- **WARN: 5.2% nulls in `device_type`.** Recent mobile SDK update may have changed event schema.

## Recommended actions
- <e.g., "Block analysis until dedup is fixed">
- <e.g., "Coerce null device_type to 'unknown' downstream">

## Caveats
- <e.g., "Last 24h of data has pipeline-lag and shouldn't be trusted for freshness check">
```

## Validation checks (meta — does the audit itself work)

- [ ] All seven checks ran without query errors
- [ ] Each check has an explicit pass/warn/fail status
- [ ] Status reasoning is reproducible (numbers + thresholds, not vibes)

## Edge cases & failure modes

- **Slowly-changing-dimension tables**: PK may not be uniqueness check candidate. Audit on `(pk, valid_from)` instead.
- **Append-only event tables**: late-arriving events are normal; treat as "data delay" not "data missing" if within reasonable bounds.
- **Sampled tables**: row count will be low by design. Document the sample rate and adjust expectations.
- **Test/internal data mixed in**: include an `is_test = false` filter in the audit if applicable.
- **Sparse columns**: high null % may be expected (e.g., `referrer_url` for organic users). Warn but don't fail.

## Scripts

- `scripts/audit_table.sql` — Parameterized Snowflake audit script
- `scripts/audit_table.py` — Run audit against any pandas DataFrame

```bash
python scripts/audit_table.py --input data.csv --pk user_id,event_date --critical user_id,event_at --time-col event_at
```

## Related skills

- `modular-sql-ctes` — fix sources structurally rather than band-aid downstream
- `metric-definition` — pin down expected values so the audit has thresholds
- Any modeling skill — always audit inputs first
