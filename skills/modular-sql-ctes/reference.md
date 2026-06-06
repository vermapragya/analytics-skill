# Modular SQL — Reference

## The three-layer model in detail

### Layer 1: Staging (`stg_`)
- One staging CTE per source table
- Purpose: rename, cast, filter
- **Allowed**: light `WHERE` clauses, casts, column renames, derived flags (`is_*`)
- **NOT allowed**: joins, aggregations, business logic

### Layer 2: Intermediate (`int_`)
- Where business logic lives
- Joins between staging CTEs
- Aggregations to intermediate grains
- Derived metrics

### Layer 3: Fact / Dim / Final
- Final shape consumers see
- Only columns needed downstream
- Single SELECT statement at the bottom referencing the final CTE

## Naming conventions

| Prefix | Meaning |
|---|---|
| `stg_` | Staged from raw source |
| `int_` | Intermediate transformation |
| `fct_` | Fact table (events, transactions) |
| `dim_` | Dimension table (entities, attributes) |
| `agg_` | Pre-aggregated rollup |
| `tmp_` | Throwaway scratch (avoid in production) |

## Anti-patterns

### Anti-pattern: monolithic query
```sql
-- BAD: 200-line query in one SELECT
select
    u.user_id,
    count(distinct case when e.event_name = 'a' and ... then ... end),
    sum(...),
    ...
from users u
left join events e on ... and ...
left join orders o on ...
group by 1
having ...;
```

### Refactored
Split into staging, enrichment, aggregation. Each CTE 10-30 lines.

### Anti-pattern: join inflating grain
```sql
-- users joined to orders (1:N) without dedup → row count inflated
select u.user_id, u.country, o.order_amount
from users u
join orders o using (user_id);
```

### Refactored
Aggregate orders to user level first, then join.

```sql
with user_orders as (
    select user_id, sum(order_amount) as total_amount
    from orders
    group by user_id
)
select u.user_id, u.country, uo.total_amount
from users u
left join user_orders uo using (user_id);
```

### Anti-pattern: `WHERE` filter on outer-joined table
```sql
-- LEFT JOIN becomes INNER JOIN due to WHERE on right side
select u.*, e.event_at
from users u
left join events e on e.user_id = u.user_id
where e.event_at >= current_date - 7;
```

### Refactored
Move filter into ON clause.

```sql
select u.*, e.event_at
from users u
left join events e
    on e.user_id = u.user_id
   and e.event_at >= current_date - 7;
```

## Window function patterns

### Latest record per group
```sql
select *
from events
qualify row_number() over (partition by user_id order by event_at desc) = 1;
```

### Running total
```sql
select
    user_id,
    event_date,
    amount,
    sum(amount) over (
        partition by user_id
        order by event_date
        rows between unbounded preceding and current row
    ) as running_total
from transactions;
```

### Rolling 7-day window
```sql
select
    event_date,
    sum(events) over (
        order by event_date
        rows between 6 preceding and current row
    ) as events_trailing_7d
from daily_events;
```

## SQL style conventions

- Lowercase keywords (`select`, not `SELECT`)
- Comma-leading or comma-trailing — pick one and stick to it
- Indent CTEs at the same level
- One column per line in `SELECT` for non-trivial queries
- Align ON conditions
- Avoid trailing whitespace

```sql
-- comma-trailing style (preferred for this repo)
select
    user_id,
    event_date,
    total_events,
    purchase_count
from int_user_daily;
```

## Snowflake-specific patterns

### `QUALIFY` for window-based filtering
```sql
select *
from events
qualify row_number() over (partition by user_id order by event_at desc) <= 5;
```

### `RATIO_TO_REPORT` for shares
```sql
select
    variant,
    user_count,
    ratio_to_report(user_count) over () as share
from variant_counts;
```

### `LATERAL FLATTEN` for arrays
```sql
select user_id, f.value as tag
from users, lateral flatten(input => tags) f;
```

## When to materialize

Convert a CTE into a real table when:
- Used by 3+ downstream models
- Computation is expensive (> 30s)
- Logic should be reused across teams

Use dbt incremental materialization for tables with append-only growth.

## File organization (for dbt projects)

```
models/
├── staging/
│   ├── stg_events.sql
│   ├── stg_users.sql
│   └── sources.yml
├── intermediate/
│   ├── int_user_daily.sql
│   └── int_events_enriched.sql
└── marts/
    ├── fct_user_daily_activity.sql
    ├── fct_orders.sql
    └── dim_users.sql
```
