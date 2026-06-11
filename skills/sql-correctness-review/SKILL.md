---
name: sql-correctness-review
description: Audits a SQL query's logic for wrong-results bugs — duplicate rows, join fanout, wrong join types, NULL handling traps, and CASE branch issues — with evidence queries that prove or clear each suspicion. Use when the user says "numbers look wrong", "double counting", "rows are duplicated", "this join is exploding", "check my query logic", or when totals don't reconcile.
---

# SQL Correctness Review

## When to use this skill

Use when a query might return **wrong results** — regardless of how fast it runs. Triggers:

- "These numbers look too high/low"
- "Revenue is double-counting"
- "Why do I have duplicate rows?"
- "This join is exploding"
- "Check the logic of this query"
- Two reports disagree on the same metric

Routing: performance/anti-patterns → `sql-query-review`. Bad data *in the table* (not the query) → `data-quality-audit`. The first job here is deciding which of the two it is.

## Required inputs

| Input | Why it matters |
|---|---|
| Query text | The suspect |
| Expected output grain | "One row per X" — every check is relative to this |
| Key relationships | Which joins are 1:1 vs 1:N (or what you *believe* they are) |
| A reconciliation anchor | A number you trust (row count, total from a source system) to diff against |
| Access to run SQL | Evidence queries are the core of this skill |

## The five bug classes

| # | Class | Symptom | Canonical cause |
|---|---|---|---|
| 1 | Duplicates | Row count too high; metrics inflated | Source table grain misunderstood; missing dedup |
| 2 | Join fanout | Totals inflate after a join | Joining on a partial key (1:N or N:M treated as 1:1) |
| 3 | Wrong join type | Rows silently disappear | INNER where LEFT intended; WHERE on a LEFT join's right table |
| 4 | NULL handling | Rows vanish or comparisons silently fail | NOT IN + NULL; `col != 'x'` dropping NULLs; NULL join keys |
| 5 | CASE issues | Misclassified or NULL categories | Missing ELSE; overlapping branches; NULL never matching |

## Workflow

1. **Pin the expected grain.** Write it down: "one row per (user_id, day)". Every subsequent check compares reality to this statement.

2. **Check output grain (duplicates).**
   ```sql
   select <grain_cols>, count(*) as n
   from (<query>)
   group by <grain_cols>
   having count(*) > 1
   order by n desc
   limit 20;
   ```
   Zero rows = clean. Any rows = pull one offending key and eyeball the duplicated rows — the differing columns point at the culprit join or missing dedup.

3. **Audit every join for fanout.** For each join, verify the key's uniqueness on the side you assume is "1":
   ```sql
   select join_key, count(*) from right_table group by join_key having count(*) > 1 limit 10;
   ```
   Then measure the explosion directly: row count before vs after the join. A join you believed was 1:1 that grows rows is the smoking gun. `scripts/logic_checks.sql` has templated checks.

4. **Audit join types and direction.**
   - For each INNER join: "is it okay to drop left-side rows with no match?" If not → LEFT.
   - For each LEFT join: check the WHERE clause for conditions on right-table columns — `where r.col = 'x'` silently converts LEFT to INNER. Move the condition into the ON clause or handle NULL explicitly.
   - Count rows lost: `select count(*) from left_table l left join r on ... where r.key is null;` — is that number expected?

5. **Audit NULL handling.**
   - `NOT IN (subquery)` where the subquery can yield NULL → returns zero rows. Use NOT EXISTS.
   - `where col != 'x'` — NULLs are dropped too. Intended? If not: `where col != 'x' or col is null`.
   - NULL join keys never match (even to other NULLs) — measure: `select count(*) from t where join_key is null;`
   - `count(col)` vs `count(*)` — the former skips NULLs.
   - Aggregates ignore NULLs: `avg(col)` averages only non-null rows. Decide if that's the intended denominator.

6. **Audit CASE expressions.**
   - **Missing ELSE** → unmatched rows become NULL and often vanish from grouped reports.
   - **Branch order**: first match wins. Overlapping conditions (`>= 100` before `>= 1000`) make later branches dead code.
   - **NULL never matches** `when col = 'x'` — handle with an explicit `when col is null` branch.
   - **Coverage check**: count rows per branch including the implicit-NULL bucket:
   ```sql
   select <case_expression> as branch, count(*) from t group by 1 order by 2 desc;
   ```
   A NULL branch with rows in it is a missing-ELSE or missing-NULL-branch finding.

7. **Reconcile against the anchor.** Compare the query's total to the trusted number. State the remaining gap explicitly — "fixed fanout, totals now within 0.2% of finance's number; residual is refunds timing" beats "looks right now."

8. **Report** with evidence for every finding (the query you ran + what it returned).

## Output format

```markdown
# SQL Correctness Review: <query description>

## Expected grain
One row per <grain>. Verified: <yes / NO — see finding 1>

## Findings

### Finding 1 (blocker): orders→items join fans out 3.2×
- **Evidence:** `select order_id, count(*) from order_items group by 1 having count(*) > 1` → 84% of orders have multiple items; query treats join as 1:1
- **Impact:** revenue inflated ~3.2× (matches the "too high" report)
- **Fix:** pre-aggregate items to order grain before joining

### Finding 2 (major): LEFT join silently converted to INNER
- **Evidence:** `where i.status = 'shipped'` filters NULLs from unmatched orders; 12,440 orders dropped
- **Fix:** move predicate to ON clause: `on ... and i.status = 'shipped'`

## Corrected query
\`\`\`sql
-- [fixed SQL]
\`\`\`

## Reconciliation
| Measure | Before | After | Anchor | Gap |
|---|---|---|---|---|
| Row count | 412,032 | 128,760 | 128,760 (orders table) | 0 |
| Revenue | $4.1M | $1.28M | $1.27M (finance) | +0.8% (refund timing) |

## Remaining risks
- <anything not fully resolved>
```

## Validation checks

- [ ] Expected grain stated and verified with a HAVING > 1 check
- [ ] Every join audited: key uniqueness + row count before/after
- [ ] Every LEFT join checked for WHERE-clause conversion to INNER
- [ ] NOT IN / != / NULL-key traps explicitly checked
- [ ] Every CASE checked for ELSE, branch order, and NULL branch
- [ ] Output reconciled against an independent anchor, residual gap explained
- [ ] Every finding backed by an evidence query and its result

## Edge cases & failure modes

- **The query is right; the table is wrong.** If the grain check fails on the *source* table (true duplicates upstream), this is a `data-quality-audit` problem. Don't patch it silently with DISTINCT in the query — flag it.
- **Intentional fanout.** Some joins are supposed to multiply (exploding a date spine, unnesting). The bug is unstated intent, not the fanout — document the expected multiplier.
- **DISTINCT hiding the evidence.** A query with DISTINCT may pass the duplicate check while still being wrong (dedup picks arbitrary rows when non-key columns differ). Remove the DISTINCT during the audit, find the fanout, fix the grain, then decide if DISTINCT is still needed.
- **Two queries disagree and both look right.** Diff their populations first (`minus` both directions), not their logic. The population difference usually names the bug (filters, join type, time window).
- **No reconciliation anchor exists.** Construct one: count the driving table with the same filters. The output of a 1:1-joined pipeline can't exceed it.

## Scripts

- `scripts/logic_checks.sql` — templated evidence queries: grain/duplicate check, join fanout audit, LEFT-join loss count, NULL-key share, NOT IN trap detector, CASE branch coverage.

## Related skills

- `sql-query-review` — performance and anti-pattern review of the same query
- `data-quality-audit` — when the source table, not the query, is broken
- `modular-sql-ctes` — restructuring so each CTE has one verifiable grain
- `metric-definition` — when two reports disagree because the metric was never pinned down
