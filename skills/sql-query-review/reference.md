# SQL Query Review — Reference

Full anti-pattern catalog with before/after fixes. Snowflake-first; vendor notes at the end.

## Projection & scan

### SELECT * into downstream steps

```sql
-- Before: pulls 47 columns through 3 CTEs to use 4
with base as (select * from events), ...

-- After
with base as (
    select user_id, event_name, event_at, device
    from events
), ...
```

Columnar warehouses charge I/O per column. The cost compounds when the wide CTE feeds joins or windows.

### Missing partition/date filter

Any query on a large event table without a time bound is a finding — even if "it works." Default to an explicit window and make "all history" an intentional choice, not an accident.

## Filters

### Function-wrapped filter columns

```sql
-- Before: evaluates date() per row, prunes nothing
where date(event_at) = '2026-06-01'

-- After: range predicate on the raw column, prunes partitions
where event_at >= '2026-06-01'
  and event_at <  '2026-06-02'
```

Same for `to_char(...)`, `year(...) = 2026`, `lower(email) = ...` (consider a computed column if lowercasing is routine).

### Implicit casts

```sql
-- Before: user_id is varchar; the column gets cast, killing pruning/index use
where user_id = 12345

-- After
where user_id = '12345'
```

Watch for join keys with mismatched types — same problem, worse blast radius.

### Late filters

If the outer query filters on a column available in the first CTE, push the filter down. In strict CTE pipelines, each stage should carry only the rows it needs.

## Joins

### OR in join conditions

```sql
-- Before: cannot hash-join, degenerates badly
on a.id = b.id or a.legacy_id = b.legacy_id

-- After: two joins + coalesce, or a UNION ALL of two clean joins
left join b b1 on a.id = b1.id
left join b b2 on a.legacy_id = b2.legacy_id
-- then coalesce(b1.col, b2.col)
```

### Join-then-aggregate vs aggregate-then-join

```sql
-- Before: joins 500M order lines to users, then aggregates
select u.user_id, count(*) as n_lines
from users u join order_lines ol on ol.user_id = u.user_id
group by u.user_id;

-- After: shrink the big side first
with lines_per_user as (
    select user_id, count(*) as n_lines
    from order_lines
    group by user_id
)
select u.user_id, coalesce(l.n_lines, 0) as n_lines
from users u left join lines_per_user l on l.user_id = u.user_id;
```

Pre-aggregating also removes a whole class of fanout bugs.

## Aggregation & dedup

### DISTINCT as a fanout band-aid

`select distinct` immediately after a join is the classic smell: the join fans out, someone slapped DISTINCT on top. It "works" until a non-key column differs between the duplicated rows. **Treat as a correctness finding** — fix the join grain (see `sql-correctness-review`), then delete the DISTINCT.

### UNION vs UNION ALL

`UNION` dedups across the full row — an expensive sort/hash you usually don't want. Default to `UNION ALL`; use `UNION` only when dedup is the intent (and say so in a comment).

### Repeated count(distinct)

```sql
-- Before: several distinct aggregations, each its own expensive pass
select count(distinct user_id), count(distinct session_id), count(distinct device_id) from events;
```

Fine occasionally. In hot pipelines, consider one pass building a dedup table per entity, or approximate counts (`approx_count_distinct` / HLL) when exactness isn't required.

## Windows & CTEs

### Window where GROUP BY would do

```sql
-- Before: windows the whole table to keep one row per user
qualify row_number() over (partition by user_id order by event_at desc) = 1

-- Often fine — but if you only need (user_id, max(event_at)):
select user_id, max(event_at) from events group by user_id
```

`QUALIFY row_number()` is the right tool when you need the *whole latest row*. If you need one or two columns, aggregate instead.

### CTE referenced multiple times

Snowflake may recompute a CTE per reference. For an expensive CTE used 2+ times, materialize:

```sql
create temporary table tmp_expensive as (...);
```

### RANGE vs ROWS frames

`range between` requires value-based sorting and is slower; `rows between` is positional and cheap. Prefer ROWS unless tie semantics genuinely require RANGE.

## Misc

### NOT IN with a nullable subquery

```sql
-- Before: returns ZERO rows if the subquery contains a single NULL
where user_id not in (select user_id from churned)

-- After
where not exists (
    select 1 from churned c where c.user_id = t.user_id
)
```

Both a correctness trap and usually a performance win.

### Scalar subqueries in SELECT

```sql
-- Before: correlated subquery per row
select u.user_id,
       (select max(o.created_at) from orders o where o.user_id = u.user_id) as last_order
from users u;

-- After: one aggregation + join
```

### ORDER BY inside CTEs / subqueries

Ordering is only meaningful (and only guaranteed) at the outermost query. Interior sorts are wasted work — delete them unless paired with a LIMIT that needs them.

## Severity rubric

| Severity | Definition | Examples |
|---|---|---|
| Blocker | Wrong results possible, or unbounded cost | missing join condition; NOT IN + nullable subquery; fanout + DISTINCT |
| Major | Materially slower/costlier, or fragile | no date filter on event table; function-wrapped filters; OR-joins; UNION-not-ALL on big sets |
| Minor | Style, readability, small waste | SELECT * on small tables; unused columns; interior ORDER BY; alias inconsistency |

When run frequency is high (hourly+), promote majors aggressively — a 2× cost on an hourly job is a real bill.

## Verification patterns

Always prove the rewrite before declaring victory:

```sql
-- 1. Row counts
select (select count(*) from old_r) old_n, (select count(*) from new_r) new_n;

-- 2. Full-row symmetric difference (empty = equivalent)
(select * from old_r minus select * from new_r)
union all
(select * from new_r minus select * from old_r);

-- 3. Aggregate checksums when full MINUS is too expensive
select count(*), sum(hash(*)) from old_r;
select count(*), sum(hash(*)) from new_r;
```

If the rewrite intentionally changes results (fixed a bug), document the delta instead: how many rows differ and why the new behavior is correct.

## Vendor notes

| Topic | Snowflake | BigQuery | Postgres |
|---|---|---|---|
| CTE materialization | May inline (recompute per reference) | Generally inlined; use temp tables for reuse | Materialized by default pre-12; `MATERIALIZED` keyword 12+ |
| Pruning unit | Micro-partitions; clustering keys | Partitions + clustering columns | Indexes; BRIN for time-series |
| QUALIFY | Supported | Supported | Not supported — wrap in subquery |
| approx distinct | `approx_count_distinct` | `approx_count_distinct` | extension (`hll`) |
| Cost lever | Warehouse seconds | Bytes scanned | Shared instance — locks/IO matter more |

On BigQuery, "bytes scanned" is the bill — projection and partition filters dominate everything else.
