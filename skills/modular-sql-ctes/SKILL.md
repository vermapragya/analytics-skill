---
name: modular-sql-ctes
description: Refactors SQL into staging, intermediate, and fact CTE layers with explicit grain and naming conventions. Use when the user asks to refactor a SQL query, clean up a model, build a dbt model, modularize a query, or mentions CTE structure, query readability, or "this SQL is hard to follow."
---

# Modular SQL with Layered CTEs

## When to use this skill

Use when transforming a working-but-unreadable SQL query into a maintainable, testable model. Triggers:

- "Refactor this SQL"
- "Make this query more readable"
- "Build a dbt model for…"
- "Modularize this query"
- "This SQL is hard to follow"

Don't use for one-off exploration queries that won't be reused. Refactoring exploratory code is over-engineering.

## Required inputs

| Input | Why it matters |
|---|---|
| Current SQL | The query to refactor |
| Target grain | What one row in the final output represents |
| Source tables | Where the data is coming from |
| Warehouse | Snowflake / BigQuery / Postgres / Redshift |
| dbt or raw SQL | Affects model layout |

## Workflow

1. **Restate the grain in plain English.** "Each row is one *user-day*" or "one *order*" or "one *experiment-variant-day*." If you can't say this clearly, the query has a grain bug.

2. **Identify the layers.** Every analytics query has 3 logical layers:
   - **Staging (`stg_`)**: rename columns, cast types, light filters. One staging CTE per source table.
   - **Intermediate (`int_`)**: business logic — joins, derived columns, aggregations to intermediate grain.
   - **Fact / Final (`fct_`/`dim_` or final select)**: the output at target grain, with only the columns consumers need.

3. **One purpose per CTE.** If a CTE name needs "and" ("users_and_orders_and_revenue"), split it.

4. **Filter early.** Apply `WHERE` clauses in staging where possible to reduce data scanned downstream.

5. **Use explicit JOIN types** — `inner join`, `left join`, `full join`. Never bare `join`.

6. **No `SELECT *` in production layers.** Only allowed in staging if every source column is intentionally used. List columns explicitly in `int_` and `fct_`.

7. **Add inline comments** ONLY for non-obvious business rules. Don't narrate what the SQL does.

8. **Add a final-select preamble.** A 1-line comment block at the top of the file stating: grain, primary key, source tables, and refresh cadence.

## Output format

```sql
-- =========================================================
-- Model: fct_user_daily_activity
-- Grain: one row per (user_id, activity_date) in UTC
-- Primary key: (user_id, activity_date)
-- Sources:
--   raw.events.product_events
--   raw.users.dim_user
-- Refresh: daily at 06:00 UTC
-- Owner: @sarah.kim
-- =========================================================

with stg_events as (
    select
        cast(user_id as varchar) as user_id,
        lower(event_name) as event_name,
        cast(event_at as timestamp_ntz) as event_ts,
        cast(event_at as date) as event_date
    from raw.events.product_events
    where event_at >= '2024-01-01'
      and user_id is not null
),

stg_users as (
    select
        cast(user_id as varchar) as user_id,
        country,
        plan_tier,
        signup_at
    from raw.users.dim_user
    where is_internal_user = false
),

int_events_enriched as (
    select
        e.user_id,
        e.event_ts,
        e.event_date,
        e.event_name,
        case when e.event_name = 'purchase' then 1 else 0 end as is_purchase,
        case when e.event_name = 'session_start' then 1 else 0 end as is_session
    from stg_events e
),

int_user_daily as (
    select
        ee.user_id,
        ee.event_date,
        count(*) as total_events,
        sum(ee.is_purchase) as purchase_count,
        sum(ee.is_session) as session_count
    from int_events_enriched ee
    group by ee.user_id, ee.event_date
),

fct_user_daily_activity as (
    select
        ud.user_id,
        ud.event_date as activity_date,
        u.country,
        u.plan_tier,
        ud.total_events,
        ud.purchase_count,
        ud.session_count,
        case when ud.purchase_count > 0 then 1 else 0 end as did_purchase
    from int_user_daily ud
    inner join stg_users u using (user_id)
)

select * from fct_user_daily_activity;
```

## Validation checks

- [ ] Grain stated in header and matches actual output
- [ ] Primary key uniqueness can be verified (one row per stated key)
- [ ] No `select *` outside staging
- [ ] All joins have explicit type
- [ ] CTE names follow `stg_` / `int_` / `fct_` convention
- [ ] No CTE has both "and" in its name and >50 lines
- [ ] Recent partitions filtered early (no full-table scans without reason)

## Edge cases & failure modes

- **Snowflake views vs tables**: views recompute every time; for expensive logic, materialize as table or dynamic table.
- **Joins changing grain**: joining a `1:N` table without aggregating first inflates row counts. Add `qualify row_number() over ... = 1` or aggregate before joining.
- **Window functions over too-large partitions**: Snowflake spills to disk. Pre-aggregate, then window.
- **Date filter in WHERE vs ON**: filtering an outer-joined table's date in `WHERE` converts the join to inner. Put it in `ON` instead.

## dbt-specific notes

- One model per file, named after the final table
- Source declarations in `sources.yml`
- Column-level docs in `<model>.yml`
- Tests: at minimum `unique` and `not_null` on primary key columns
- Use `{{ ref('stg_users') }}` for cross-model dependencies
- Materialize `stg_` as views, `int_` and `fct_` as tables

## Cross-warehouse notes

| Snowflake | BigQuery | Postgres |
|---|---|---|
| `date_trunc('week', d)` | `date_trunc(d, week)` | `date_trunc('week', d)` |
| `datediff('day', a, b)` | `date_diff(b, a, day)` | `(b - a)` |
| `dateadd('day', n, d)` | `date_add(d, interval n day)` | `d + interval 'n day'` |
| `qualify` | `qualify` | use subquery |
| `nullif(a, b)` | `nullif(a, b)` | `nullif(a, b)` |

## Related skills

- `warehouse-query-optimization` — when the refactored query needs to be fast
- `data-quality-audit` — verify the output meets grain/uniqueness expectations
- `metric-definition` — wrap the final model in a metric spec
