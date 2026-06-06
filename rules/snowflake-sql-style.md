# Rule: Snowflake SQL Style

Always-follow conventions for Snowflake SQL written for analytics work.

## Casing
- Lowercase all SQL keywords (`select`, `from`, `where`, not `SELECT`)
- Lowercase column and table names in queries (Snowflake stores uppercase but case-insensitive in queries)

## Structure
- Use CTEs over subqueries
- One CTE per logical step (`stg_`, `int_`, `fct_`/`dim_` prefixes)
- Final select should be a single line at the bottom

## Joins
- Always explicit join type: `inner join`, `left join`, `full outer join` — never bare `join`
- Use `using (col)` when join keys have the same name
- Filter outer-joined tables in the `on` clause, NOT `where` (preserves outer join)

## Column projection
- Never `select *` outside staging CTEs
- One column per line for non-trivial selects
- Trailing commas preferred

## Filtering
- Apply filters at the staging layer where possible (reduces data scanned)
- Date filters use range comparison, not function-wrapping:
  - GOOD: `where event_at >= '2026-04-01' and event_at < '2026-05-01'`
  - BAD: `where date_trunc('month', event_at) = '2026-04-01'` (blocks partition pruning)

## Date/time
- All timestamps in UTC unless explicitly noted
- Use `date_trunc`, `dateadd`, `datediff` (Snowflake natives)
- Use `current_date` not `current_timestamp::date`

## Performance
- Don't `select *` from wide tables
- Use `qualify` for window-based filtering
- Use `approx_count_distinct` for high-cardinality counts when exact not required
- Avoid `distinct` when `group by` will work

## Comments
- Header comment block on every production model (grain, PK, sources, refresh, owner)
- Inline comments ONLY for non-obvious business rules
- Do not narrate what the SQL does in comments

## Header template

```sql
-- =========================================================
-- Model: <name>
-- Grain: <one row per X>
-- Primary key: <columns>
-- Sources: <table_1>, <table_2>
-- Refresh: <cadence>
-- Owner: @<handle>
-- =========================================================
```

## See also
- `skills/modular-sql-ctes/` for full workflow
- `skills/warehouse-query-optimization/` for performance tuning
- `agents/sql-reviewer.md` for automated review
