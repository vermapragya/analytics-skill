# Snowflake Query Optimization — Reference

## Snowflake architecture (brief)

- **Storage**: micro-partitions (~16 MB compressed columnar chunks)
- **Metadata**: per-partition column min/max stored; used for partition pruning
- **Compute**: warehouse = cluster of VMs; size affects parallelism and memory
- **Caching**: result cache (24h), local disk cache, remote SSD cache

## Reading a query plan

| Operator | What it means | What to look for |
|---|---|---|
| TableScan | Reading from disk | Bytes scanned, partitions pruned |
| Filter | Applying WHERE | Should be near TableScan (pushed down) |
| Aggregate | GROUP BY | Grouping sets size |
| Join | Joining two streams | Hash table size, spill warnings |
| Sort | ORDER BY or window | Memory needed, spill warnings |
| WindowFunction | OVER(...) | Partition by cardinality |
| UnionAll | UNION ALL | Cheap |
| Result | Final output | Row count |

## Micro-partition pruning

A query prunes (skips) a partition if no rows could match the WHERE clause based on column min/max metadata.

```sql
-- Prunes well: event_date is min/max-trackable
where event_date >= '2026-04-01'

-- Prunes well: user_id is min/max-trackable
where user_id between 1000 and 2000

-- Doesn't prune: function on the column
where date_trunc('month', event_date) = '2026-04-01'

-- Doesn't prune: implicit cast
where event_date = '2026-04-01'  -- if event_date is timestamp, both sides cast
```

Fixes:
```sql
-- Bad
where date_trunc('month', event_date) = '2026-04-01'

-- Good
where event_date >= '2026-04-01' and event_date < '2026-05-01'
```

## Clustering keys

```sql
alter table fct_events cluster by (event_date, user_id);
```

When to add clustering:
- Table is large (> 1 TB)
- Frequently filtered on the cluster keys
- Natural data distribution is not already clustered (check `system$clustering_information`)

Cost: re-clustering consumes credits. Monitor with `automatic_clustering_history`.

## Spillage

When query memory exceeds warehouse RAM:
- **Local spill**: SSD on the warehouse VM. Slow but tolerable.
- **Remote spill**: S3-like remote storage. Very slow. Indicates undersized warehouse OR rewritable query.

Diagnose from `query_history`:
```sql
select query_id, bytes_spilled_to_local_storage, bytes_spilled_to_remote_storage
from snowflake.account_usage.query_history
where bytes_spilled_to_remote_storage > 0
order by bytes_spilled_to_remote_storage desc
limit 20;
```

## Join strategies

| Pattern | Snowflake behavior |
|---|---|
| Join on equality | Hash join (default, fast) |
| Join on inequality / function | Nested loop join (slow on big tables) |
| `BETWEEN` join | Often becomes nested loop |
| Cross join (missing join condition) | Cartesian — usually a bug |

To force broadcast (small table) join:
- Snowflake usually picks the right join order; if not, restructure with subqueries or temp tables.

## Common anti-patterns

### Anti-pattern: SELECT * from wide table
```sql
select * from analytics.events.fct_events_v2 where event_date = current_date;
```
50+ columns × 1B rows = lots of bytes scanned. Project only what you need.

### Anti-pattern: function on the partition key
```sql
where to_date(event_at_string) = '2026-04-01'  -- forces full scan
```
Fix by casting once during load, or:
```sql
where event_at_string >= '2026-04-01' and event_at_string < '2026-04-02'
```
(if string format is sortable).

### Anti-pattern: window function over full table
```sql
select *, row_number() over (partition by user_id order by event_at desc) as rn
from huge_events
qualify rn = 1;
```
For "latest row per user" on a huge table, pre-filter first:
```sql
with recent as (
    select * from huge_events where event_at >= dateadd('day', -7, current_date)
)
select *, row_number() over (partition by user_id order by event_at desc) as rn
from recent
qualify rn = 1;
```

### Anti-pattern: COUNT(DISTINCT) on huge cardinality
```sql
select count(distinct user_id) from billion_row_table;
```
Use `approx_count_distinct(user_id)` if exact isn't needed (HyperLogLog, ~1-2% error).

### Anti-pattern: DISTINCT instead of GROUP BY
```sql
select distinct a, b, c from t;  -- often slower than:
select a, b, c from t group by 1, 2, 3;
```

### Anti-pattern: Repeated heavy CTE
```sql
with heavy as (select ... from huge_table)
select ... from heavy h1 join heavy h2 on ...
-- heavy CTE may be computed twice
```
Fix: materialize.
```sql
create temp table heavy_t as select ... from huge_table;
select ... from heavy_t h1 join heavy_t h2 on ...
```

## Warehouse sizing guide

| Warehouse | When |
|---|---|
| XS (1 credit/hr) | Dashboard refresh, small ad-hoc |
| S (2) | Most analytics queries |
| M (4) | Medium ETL, big aggregations |
| L (8) | Large joins, ML feature engineering |
| XL (16) | Heavy ETL with large spillage on L |
| 2XL+ | Rare; usually indicates query needs rewrite |

Rule: upsizing should be the **last** resort, not the first.

## Cost estimation

```
credits_used = warehouse_size_credits_per_hour × (elapsed_time_seconds / 3600)
```

E.g., a 10-second query on M (4 credits/hr) = 0.011 credits ≈ $0.022 at $2/credit.

Multiply by frequency:
- 1 query × 24 runs/day × 365 days = 8,760 runs/year
- 0.011 credits × 8,760 = 96 credits/year ≈ $193/year

## Search optimization service

For point-lookup queries on high-cardinality columns:
```sql
alter table fct_events add search optimization on (user_id, session_id);
```
Trade-off: storage cost + maintenance cost vs query speed.

Use when:
- Frequent equality lookups on a column with cardinality > 100k
- Query pattern is point lookup (not range scan)

## Other warehouses (high-level differences)

| Feature | Snowflake | BigQuery | Redshift |
|---|---|---|---|
| Partition pruning | Auto via micro-partitions | Auto via partitioned columns | Manual via distkey/sortkey |
| Clustering | `cluster by` | `cluster by` | `sortkey` |
| Spill | Auto, visible in profile | Slot-based, less direct | Disk-based, visible in svl_query_summary |
| Cost model | Per-credit (compute time × WH size) | Per-byte scanned | Per-second cluster |

Optimization principles (column pruning, filter pushdown, avoid full scans) apply everywhere.
