---
name: sql-query-review
description: Static review of a SQL query — finds anti-patterns, structural problems, and performance issues from the query text alone, then proposes an optimized rewrite with a verification plan. Use when the user says "review this query", "check my SQL", "is this query okay", "clean up this query", or "optimize this" without runtime profile data.
---

# SQL Query Review

## When to use this skill

Use when reviewing or improving a SQL query **from its text alone** — no query profile or runtime stats required. Triggers:

- "Review this query"
- "Check my SQL before I ship it"
- "Can this query be written better?"
- "Optimize this query" (when no query_history / profile is available)
- PR review of a `.sql` file

Routing to related skills:

- Runtime stats available (query_history, query profile, spilling)? → `warehouse-query-optimization`
- Suspected **wrong results** (dupes, fanout, missing rows)? → `sql-correctness-review`
- Query is correct and fast but unreadable? → `modular-sql-ctes`

A full review often chains all three: correctness first, then this skill, then runtime profiling if still slow.

## Required inputs

| Input | Why it matters |
|---|---|
| Query text | The thing being reviewed |
| Intent (one sentence) | "What question does this answer?" — catches queries that are fast but wrong |
| Expected output grain | One row per what? Needed to judge joins and aggregates |
| Approx table sizes | A `SELECT *` on 1K rows is fine; on 1B rows it's a finding |
| Run frequency | One-off ad-hoc vs hourly pipeline changes the bar |

If table sizes / frequency are unknown, review anyway and mark size-dependent findings as conditional.

## Workflow

1. **Restate intent and grain.** One sentence each. If you can't infer them from the query, ask — every later judgment depends on this.

2. **Correctness scan first.** Optimizing a wrong query makes it wrong faster. Quick pass for the big five logic bugs (dupes, fanout, wrong join type, NULL traps, CASE issues). If any are suspected, run `sql-correctness-review` before continuing.

3. **Run the anti-pattern checklist** (full catalog with fixes in `reference.md`):

   ### Projection & scan
   - `SELECT *` feeding downstream steps that use few columns
   - Columns selected but never used
   - Missing date/partition filter on large event tables

   ### Filters
   - Functions wrapping filter columns (`where date(event_at) = ...`) — kills partition pruning
   - Implicit casts in predicates (string column compared to number)
   - Filters applied late (in the outer query) that could be pushed into the first CTE

   ### Joins
   - `OR` in join conditions (forces nested-loop-like plans)
   - Join keys with type mismatch (`varchar` = `number`)
   - Joining then aggregating, where pre-aggregating one side first would shrink the join

   ### Aggregation & dedup
   - `DISTINCT` used as a band-aid for fanout (treat as a correctness smell too)
   - `UNION` where `UNION ALL` is intended (UNION adds an expensive implicit dedup)
   - `count(distinct ...)` repeated many times over the same scan

   ### Windows & CTEs
   - Unbounded window over a huge partition where a `GROUP BY` would do
   - Expensive CTE referenced 2+ times (may be computed twice — consider temp table)
   - `RANGE BETWEEN` where `ROWS BETWEEN` suffices

   ### Misc
   - `NOT IN (subquery)` — both a NULL trap and often slower than `NOT EXISTS`
   - Scalar subqueries in the SELECT list executed per-row
   - `ORDER BY` in subqueries/CTEs (wasted sort — only the final result needs order)

4. **Optionally run the static scanner** for a fast first pass:
   ```bash
   python scripts/antipattern_scan.py my_query.sql
   ```
   It catches the mechanical patterns (SELECT *, NOT IN, UNION vs UNION ALL, function-wrapped filters, OR-joins). Treat its output as leads, not verdicts — confirm each in context.

5. **Classify findings by severity:**
   - **Blocker** — likely wrong results or unbounded cost (missing join condition, NOT IN with nullable subquery)
   - **Major** — significant performance or maintainability cost (no partition filter, fanout-then-distinct)
   - **Minor** — style/readability (unused columns, inconsistent aliases)

6. **Write the optimized rewrite.** Preserve the output contract exactly: same columns, same grain, same row set. If a fix changes results (e.g., removing a `DISTINCT` that was masking fanout), flag it as a correctness finding instead of silently changing behavior.

7. **Provide a verification plan** — concrete queries proving old and new are equivalent:
   ```sql
   -- Row count match
   select (select count(*) from old_result) as old_n,
          (select count(*) from new_result) as new_n;

   -- Full-row equivalence (empty result = identical)
   (select * from old_result minus select * from new_result)
   union all
   (select * from new_result minus select * from old_result);
   ```

## Output format

```markdown
# SQL Review: <one-line description of the query>

## Intent & grain
- **Intent:** <what question the query answers>
- **Output grain:** <one row per ...>

## Findings

| # | Severity | Location | Finding | Fix |
|---|---|---|---|---|
| 1 | Blocker | line 14 join | `orders` joined on `user_id` only — N:M fanout, then DISTINCT masks it | Join on (user_id, order_date); remove DISTINCT |
| 2 | Major | line 3 where | `date(event_at) = current_date - 1` defeats pruning | `event_at >= ... and event_at < ...` |
| 3 | Minor | line 1 | SELECT * but only 4 columns used downstream | Project explicitly |

## Optimized query
\`\`\`sql
-- [rewritten SQL]
\`\`\`

## Key changes
1. <change + why>
2. <change + why>

## Verification plan
\`\`\`sql
-- [equivalence queries]
\`\`\`

## Expected impact
- <e.g., "scan drops from full table to 1 day of partitions; DISTINCT removed after fixing fanout">
- <or "no runtime stats available — re-profile after deploying; see warehouse-query-optimization">
```

## Validation checks

- [ ] Intent and grain stated before any finding
- [ ] Correctness scanned before performance (wrong-but-fast is a failure)
- [ ] Every finding has a severity, a location, and a concrete fix
- [ ] Rewrite preserves the output contract (or behavior changes are flagged as correctness findings)
- [ ] Verification plan included (row count + full-row equivalence)
- [ ] Size-dependent findings marked conditional when table sizes are unknown

## Edge cases & failure modes

- **The query is fine.** Say so explicitly ("no blockers, two minor style notes") rather than inventing findings. A clean review is a valid output.
- **DISTINCT that's load-bearing.** Removing a `DISTINCT` "for performance" when it's masking a fanout changes results. Always trace *why* the dedup exists before touching it.
- **Generated SQL** (ORM, BI tool). Don't review style — flag only blockers and majors, and note the fix belongs in the generator.
- **Vendor differences.** This skill defaults to Snowflake semantics (CTE inlining, pruning). For BigQuery/Postgres/Redshift differences, see `reference.md`.
- **Premature optimization.** A one-off ad-hoc query on a small table needs a correctness scan, not a rewrite. Match effort to run frequency.

## Scripts

- `scripts/antipattern_scan.py` — regex-based static scanner for mechanical anti-patterns. Fast first pass; not a substitute for reading the query.

```bash
python scripts/antipattern_scan.py path/to/query.sql
# or pipe:
cat query.sql | python scripts/antipattern_scan.py -
```

## Related skills

- `sql-correctness-review` — deep logic check (dupes, fanout, joins, NULLs, CASE)
- `warehouse-query-optimization` — runtime-profile-driven tuning when stats are available
- `modular-sql-ctes` — structural refactor into staged CTEs
- `data-quality-audit` — when the problem is the table, not the query
