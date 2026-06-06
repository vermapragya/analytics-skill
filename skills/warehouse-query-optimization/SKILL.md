---
name: warehouse-query-optimization
description: Diagnoses and fixes slow Snowflake queries — clustering, partition pruning, joins, spilling, warehouse sizing, and query plan reading. Use when the user mentions slow query, query optimization, Snowflake performance, query plan, clustering, micro-partitions, spilling, warehouse cost, or "this query is taking forever."
---

# Warehouse Query Optimization (Snowflake)

## When to use this skill

Use when a Snowflake query is **too slow, too expensive, or both**. Triggers:

- "This query is slow"
- "Why is this query scanning so much data?"
- "Reduce cost of this query"
- "Optimize this Snowflake query"
- "What does this query plan mean?"

Default to Snowflake. For BigQuery / Postgres / Redshift, the principles transfer but specific syntax/internals differ — see `reference.md`.

## Required inputs

| Input | Why it matters |
|---|---|
| Query text | What to optimize |
| Query history info | Run time, MB scanned, warehouse size — use `query_history` |
| Table sizes / partitioning | Whether clustering helps |
| Frequency of use | Is it run once (don't over-optimize) or hourly (very worth it) |
| Acceptable runtime / cost | The bar to clear |

## Workflow

1. **Pull query profile.** In Snowflake UI: Query History → click query → Query Profile. Or:
   ```sql
   select * from snowflake.account_usage.query_history
   where query_id = '<id>';
   ```

2. **Identify the biggest cost.** Look at the query profile waterfall. The bottom of the tree (deepest operator) usually shows what's slow.

3. **Apply the diagnostic checklist** (in order):

   ### a) Partition pruning
   Is the query scanning more partitions than needed?
   - Query profile: "Partitions scanned / total partitions" — if ratio > 5%, you may need a date filter or clustering.
   - Fix: add `WHERE date_col >= '...'` on a clustering key.

   ### b) Full-table scans on huge tables
   `SELECT *` from a 10TB table is almost always wrong.
   - Fix: project only needed columns. Snowflake is columnar — fewer columns = less I/O.

   ### c) Join order and join type
   Largest table on the left, smallest hash table on the right.
   - Look for "Cartesian product" in the plan — usually a missing join condition.
   - Look for "Bytes spilled to local/remote disk" — joins too big for memory; either filter earlier or upsize the warehouse.

   ### d) Filter pushdown
   Is the `WHERE` clause applied early or late?
   - Look for "Filter" operator. If it's near the top of the plan instead of near the table scan, push it down by restructuring the CTE.

   ### e) Subquery / CTE materialization
   Snowflake doesn't always materialize CTEs. A CTE used twice may be computed twice.
   - Fix: for expensive CTEs used multiple times, write to a temporary table.

   ### f) Window function size
   `OVER (PARTITION BY user_id)` on 1B rows may spill.
   - Fix: pre-aggregate before windowing, or partition processing by date.

   ### g) Warehouse sizing
   Is the warehouse undersized for the query?
   - Bytes spilled to remote storage = warehouse too small. Up-size temporarily or rewrite.
   - Bytes spilled to local disk = OK in moderation. Heavy local spilling = upsize.

4. **Apply fix, re-measure.** Always re-run after the change and compare:
   - Run time
   - MB scanned
   - MB spilled
   - Cost (credits)

5. **Report results** with before/after numbers.

## Output format

```markdown
# Query Optimization: <description>

## Original query stats
- Run time: 14.2s
- Partitions scanned: 1,840 / 2,100 (88%)
- Bytes scanned: 4.2 GB
- Bytes spilled (remote): 612 MB
- Warehouse: M

## Diagnosis
- **Primary issue:** Window function over 800M rows spills to remote storage
- **Secondary:** WHERE filter on event_date applied after window — should be pushed down
- **Minor:** SELECT * pulls 47 columns; only 6 are used downstream

## Optimized query
\`\`\`sql
-- [optimized SQL here]
\`\`\`

## Key changes
1. Pre-filtered to last 30 days before the window function (10× row reduction)
2. Selected only 6 needed columns instead of *
3. Replaced `qualify row_number() over (...) = 1` with `argmax`-equivalent pattern

## New query stats
- Run time: 1.4s (10× faster)
- Partitions scanned: 64 / 2,100 (3%)
- Bytes scanned: 124 MB (34× less)
- Bytes spilled: 0
- Warehouse: M (no upsize needed)

## Cost impact
- Original: ~0.04 credits/run × 24 runs/day = 1.0 credits/day
- Optimized: ~0.004 credits/run × 24 runs/day = 0.1 credits/day
- Savings: ~0.9 credits/day = ~$650/year at $2/credit

## Caveats
- Optimization assumes event_date filter is acceptable. If full history is needed, fix doesn't apply.
- 0 spillage assumes M warehouse with current data volume. If table grows 5×, may need to revisit.
```

## Validation checks

- [ ] Before/after stats both captured from query_history
- [ ] Output of new query matches output of old query (row-for-row, not just row count)
- [ ] Warehouse size unchanged (or explicitly justified if changed)
- [ ] Cost impact estimated when frequency is known
- [ ] Edge cases identified

## Edge cases & failure modes

- **Query plan looks fine but still slow:** the cluster may have caching pressure. Check `bytes_scanned_from_cache`. First run cold can be much slower than subsequent warm runs.

- **Optimization works on small data but slow on prod:** likely missing micro-partition pruning. Add a clustering key or a date filter.

- **CTE inlining backfire:** Snowflake may inline a CTE used twice, doubling work. Use `TEMP TABLE` for expensive CTEs referenced multiple times.

- **Window functions with `RANGE` are slow:** prefer `ROWS BETWEEN ...`. `RANGE` requires sort and is more expensive.

- **JOINS exploding row count:** a `1:N` join without aggregation first inflates the right side. Look for "Cartesian product" or unexpectedly large intermediate result sets.

## Scripts

- `scripts/profile_query.sql` — Pull stats for a query_id from query_history.

```sql
-- Get profile stats
select query_id, query_text, total_elapsed_time, bytes_scanned, bytes_spilled_to_remote_storage,
       partitions_scanned, partitions_total, warehouse_size, credits_used_cloud_services
from snowflake.account_usage.query_history
where query_id = '<id>';
```

## Related skills

- `modular-sql-ctes` — well-structured SQL is also faster SQL
- `data-quality-audit` — sometimes "slow" is "scanning too much because the table has dupes"
- `metric-definition` — pre-aggregating into a metric layer often beats optimizing ad-hoc queries
