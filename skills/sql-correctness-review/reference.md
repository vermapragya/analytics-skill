# SQL Correctness Review — Reference

Deep catalog of the five bug classes with worked mechanics, detection queries, and fixes.

## 1. Duplicates

### Mechanism

The query's output grain doesn't match the stated grain. Causes, in rough order of frequency:

1. A join fanned out (see §2) — by far the most common
2. The source table's grain was misunderstood (e.g., `users` is actually an SCD with one row per user *per version*)
3. UNION ALL of overlapping populations
4. A dedup step that dedups on the wrong key

### Detection

```sql
-- The universal grain check
select <grain_cols>, count(*) as n
from (<query>)
group by <grain_cols>
having count(*) > 1
order by n desc;
```

Then inspect one offender fully:

```sql
select * from (<query>) where <grain_col> = '<offending_key>' order by 1;
```

The columns that *differ* between the duplicate rows identify the source: if `item_id` differs, the items join fanned out; if `valid_from` differs, you're reading an SCD without filtering to current.

### SCD trap specifically

```sql
-- Wrong: 1 row per user per version
select user_id, plan from dim_users;

-- Right
select user_id, plan from dim_users where is_current
-- or: qualify row_number() over (partition by user_id order by valid_from desc) = 1
```

## 2. Join fanout

### Mechanism

Row multiplication = (matches on left) × (matches on right) per key. A join believed to be 1:1 that is actually 1:N multiplies every left row N times — and every additive metric with it.

### Detection — three levels

```sql
-- Level 1: is the "1" side actually unique on the join key?
select join_key, count(*) as n
from right_table
group by join_key
having count(*) > 1
limit 10;

-- Level 2: measure the explosion directly
select
    (select count(*) from left_table)                       as before_join,
    (select count(*) from left_table l join right_table r
        on l.key = r.key)                                   as after_join;
-- after > before on an inner join = fanout, full stop.

-- Level 3: which keys multiply worst
select l.key, count(*) as n_rows
from left_table l join right_table r on l.key = r.key
group by l.key
order by n_rows desc
limit 10;
```

### Fixes

```sql
-- Fix A (preferred): pre-aggregate the N side to the join grain
with items_per_order as (
    select order_id, sum(amount) as order_amount, count(*) as n_items
    from order_items
    group by order_id
)
select o.*, i.order_amount
from orders o
left join items_per_order i on i.order_id = o.order_id;

-- Fix B: pick one row deterministically (when you need a representative row)
qualify row_number() over (partition by order_id order by created_at desc) = 1

-- Anti-fix: SELECT DISTINCT on top. Hides the symptom, keeps the bug:
-- when non-key columns differ between duplicated rows, DISTINCT keeps them ALL.
```

### N:M joins

If *both* sides are non-unique on the key, rows multiply as N×M and almost nothing downstream survives. There is no "fix the join" here — restructure: aggregate both sides to the key grain first, or rethink the relationship via a bridge table.

## 3. Wrong join types

### INNER that should be LEFT

Silently drops left rows with no match. Symptom: denominators shrink ("why do we only have 81k users this week?").

```sql
-- How many rows does the INNER join drop?
select count(*)
from users u
left join orders o on o.user_id = u.user_id
where o.user_id is null;
```

If that count should be in your output (users with zero orders), the join must be LEFT and downstream aggregates need `coalesce(x, 0)`.

### The WHERE-clause conversion (most common LEFT-join bug)

```sql
-- Looks like a LEFT join. Behaves like an INNER join.
select u.user_id, o.total
from users u
left join orders o on o.user_id = u.user_id
where o.status = 'completed';
-- Unmatched users have o.status = NULL → NULL = 'completed' is not true → row dropped.
```

Fixes by intent:

```sql
-- Intent: keep all users, only join completed orders
left join orders o on o.user_id = u.user_id and o.status = 'completed'

-- Intent: keep all users, filter applies only when matched
where o.status = 'completed' or o.user_id is null
```

### Join key type mismatch

`on a.user_id = b.user_id` where one side is VARCHAR and the other NUMBER: implicit casts can fail rows silently (or error late). Detect with `show columns` / information_schema; fix with explicit cast on the *non-pruned* side.

### Accidental Cartesian

JOIN with a missing/incomplete ON condition. Detect: output row count ≈ left × right. Also check ON clauses that reference only one table (`on a.id = a.id` — typo'd self-comparison is always true).

## 4. NULL handling

### The NOT IN trap

```sql
-- If churned contains ONE null user_id, this returns ZERO rows:
where user_id not in (select user_id from churned)
```

Mechanics: `x NOT IN (a, b, NULL)` expands to `x != a AND x != b AND x != NULL`. The last term is UNKNOWN, so the whole predicate can never be TRUE.

```sql
-- Fix
where not exists (select 1 from churned c where c.user_id = t.user_id)
```

### Negative filters drop NULLs

```sql
where plan != 'free'      -- rows with plan IS NULL are ALSO dropped
where plan != 'free' or plan is null   -- if NULLs should be kept
```

Every `!=`, `not like`, `not in (literal list)` has this property. Decide NULL's fate explicitly.

### NULL join keys

NULL never equals NULL. Rows with NULL keys silently vanish from inner joins (and never match in left joins).

```sql
-- Measure exposure
select count(*) as null_keys, count(*) / (select count(*) from t) as share
from t where join_key is null;
```

If NULL-keyed rows must be retained, LEFT join from the driving table; never "fix" with `coalesce(key, -1)` on both sides unless you genuinely intend NULLs to match each other.

### Aggregates and NULLs

| Expression | Behavior |
|---|---|
| `count(*)` | counts rows |
| `count(col)` | counts non-NULL values |
| `avg(col)` | sum of non-NULL / count of non-NULL — denominator excludes NULLs |
| `sum(col)` | NULLs ignored; all-NULL group → NULL (not 0) |
| `col1 + col2` | NULL if either is NULL — additive columns need coalesce |

The `avg` denominator is the sneaky one: "average order value" over a column that's NULL for refunds quietly excludes refunds from the denominator.

## 5. CASE branch issues

### Missing ELSE

```sql
case when amount >= 100 then 'large'
     when amount >= 10  then 'medium'
     when amount >= 0   then 'small'
end
-- amount IS NULL → result NULL. Negative amount (refund) → result NULL.
```

Rule: every CASE in production gets an ELSE — even if it's `else 'UNEXPECTED'`. An 'UNEXPECTED' bucket showing up in a report is a feature: it surfaces data you didn't model.

### Branch order (first match wins)

```sql
-- Bug: 'whale' is dead code — every amount >= 1000 already matched '>= 100'
case when amount >= 100  then 'large'
     when amount >= 1000 then 'whale'   -- unreachable
     ...
-- Order conditions from most to least specific.
```

### NULL never matches equality

```sql
case when status = 'active'   then 'live'
     when status != 'active'  then 'not live'   -- NULL status matches NEITHER branch
     else 'unknown'                              -- NULLs land here — make it explicit:
case when status is null      then 'missing'
     when status = 'active'   then 'live'
     else 'not live'
end
```

### Coverage check (run it for every CASE under audit)

```sql
select <the_case_expression> as branch, count(*) as n
from t
group by 1
order by n desc;
```

Read it like a CASE-branch histogram: a NULL branch with rows = missing ELSE/NULL handling; a branch with 0 rows (absent from output) = possibly dead code.

## Reconciliation strategy

Order of preference for anchors:

1. **Source-system total** (finance revenue, billing MRR) — best, externally owned
2. **Driving-table count with same filters** — output of a 1:1 pipeline can't exceed it
3. **Yesterday's accepted report** — weakest (it may share the bug), but catches regressions

State residual gaps with a cause: "+0.8% vs finance, attributable to refund timing (booked T+2 here, T+0 there)". An unexplained residual means the review isn't done.

## Diffing two disagreeing queries

When two queries claim the same metric and disagree, diff populations before logic:

```sql
-- Who does A have that B doesn't, and vice versa?
select 'A_only' as side, * from (select <keys> from query_a minus select <keys> from query_b)
union all
select 'B_only' as side, * from (select <keys> from query_b minus select <keys> from query_a);
```

Profile the difference set (by date, status, segment) — the skew names the divergent filter or join. This is faster than reading both queries line by line.
