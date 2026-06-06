# Snowflake Query Optimization — Examples

## Example 1: Slow window function → 10× speedup

**User prompt:** "This query takes 14 seconds. Help me speed it up."

**Original:**
```sql
select *
from (
    select
        event_id, user_id, event_name, event_at,
        row_number() over (partition by user_id order by event_at desc) as rn
    from analytics.events.fct_events
)
where rn = 1
  and event_at >= dateadd('day', -30, current_date);
```

**Diagnosis:**
- Window function applied to entire `fct_events` (800M rows)
- Date filter applied AFTER window, so window can't be partition-pruned
- `SELECT *` pulls 47 columns

**Optimized:**
```sql
select
    event_id, user_id, event_name, event_at
from analytics.events.fct_events
where event_at >= dateadd('day', -30, current_date)
qualify row_number() over (partition by user_id order by event_at desc) = 1;
```

**Result:**
- Runtime: 14.2s → 1.4s (10× faster)
- Bytes scanned: 4.2 GB → 124 MB (34× less)
- Cost: ~0.04 → 0.004 credits per run

---

## Example 2: Function on partition key blocks pruning

**Original:**
```sql
select count(*) from analytics.events.fct_orders
where to_date(order_at) = '2026-04-01';
```

**Diagnosis:**
Partitions scanned: 2,100/2,100 (no pruning). The `to_date(order_at)` wrapper hides the column from Snowflake's metadata-based pruning.

**Optimized:**
```sql
select count(*) from analytics.events.fct_orders
where order_at >= '2026-04-01' and order_at < '2026-04-02';
```

**Result:**
- Partitions scanned: 2,100 → 47 (45× less)
- Runtime: 8.2s → 0.3s

---

## Example 3: Spillage on big join → restructured

**Original:**
```sql
select
    u.user_id, u.country, u.plan_tier,
    e.event_count, o.order_count, o.total_revenue
from dim_users u
left join (
    select user_id, count(*) as event_count from fct_events
    where event_at >= dateadd('day', -90, current_date)
    group by user_id
) e using (user_id)
left join (
    select user_id, count(*) as order_count, sum(amount) as total_revenue
    from fct_orders
    where order_at >= dateadd('day', -90, current_date)
    group by user_id
) o using (user_id);
```

**Diagnosis:**
- 600 GB scanned, 12 GB spilled to remote storage
- Joins on user_id (high cardinality) need to materialize whole hash tables
- 90-day filter applied per subquery; could be applied once

**Optimized (materialized intermediate):**
```sql
create or replace temp table tmp_user_metrics as
with recent_events as (
    select user_id, count(*) as event_count
    from fct_events
    where event_at >= dateadd('day', -90, current_date)
    group by user_id
),
recent_orders as (
    select user_id, count(*) as order_count, sum(amount) as total_revenue
    from fct_orders
    where order_at >= dateadd('day', -90, current_date)
    group by user_id
)
select
    u.user_id, u.country, u.plan_tier,
    coalesce(e.event_count, 0) as event_count,
    coalesce(o.order_count, 0) as order_count,
    coalesce(o.total_revenue, 0) as total_revenue
from dim_users u
left join recent_events e using (user_id)
left join recent_orders o using (user_id);

select * from tmp_user_metrics;
```

**Result:**
- Original: 600 GB scanned, 12 GB spilled, 95s runtime
- Optimized: 180 GB scanned, 0 spill, 18s runtime
- Reusable: subsequent queries hit the temp table (sub-second)

---

## Example 4: SELECT * → 5× speedup

**Original:**
```sql
select * from analytics.events.fct_events_wide
where event_date >= dateadd('day', -1, current_date);
```

50 columns. Most downstream code uses 4 of them.

**Optimized:**
```sql
select event_id, user_id, event_name, event_at
from analytics.events.fct_events_wide
where event_date >= dateadd('day', -1, current_date);
```

**Result:**
- Bytes scanned: 8.4 GB → 1.6 GB
- Runtime: 4.1s → 0.8s

Snowflake is columnar — fewer columns = less I/O. `SELECT *` is rarely the right answer in production.
```
