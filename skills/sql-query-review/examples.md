# SQL Query Review — Examples

## Example 1: Daily revenue query with three classic findings

**User prompt:** "Review this query before I schedule it hourly."

```sql
select distinct u.user_id, u.email, o.total
from users u
join orders o on o.user_id = u.user_id
where date(o.created_at) = current_date - 1;
```

**Skill output (abbreviated):**

> **Intent:** users with their order totals from yesterday. **Grain:** ambiguous — and that's finding #1.
>
> | # | Severity | Finding | Fix |
> |---|---|---|---|
> | 1 | Blocker | Grain is broken: a user with 3 orders yields 3 rows; the `DISTINCT` only dedups *identical* rows, so users with multiple different totals still multiply | Decide the grain: per-order (drop DISTINCT, add order_id) or per-user (aggregate `sum(o.total)`) |
> | 2 | Major | `date(o.created_at) = current_date - 1` defeats partition pruning — full scan of orders, hourly | Range predicate on the raw column |
> | 3 | Minor | `email` selected but the downstream job only uses user_id + total | Drop it |
>
> **Optimized (per-user grain, confirmed with user):**
>
> ```sql
> select o.user_id, sum(o.total) as revenue
> from orders o
> where o.created_at >= dateadd('day', -1, current_date)
>   and o.created_at <  current_date
> group by o.user_id;
> ```
>
> Note the `users` join was dropped entirely — it contributed no columns and no filtering. **Verification:** row count = distinct users with orders yesterday; `sum(revenue)` must equal `sum(total)` from the raw table for the same window.

---

## Example 2: "Optimize this" with no profile available

**User prompt:** "This takes 11 minutes, can you optimize it? I don't have access to query history."

```sql
with events_enriched as (
    select *,
           row_number() over (partition by user_id order by event_at) as rn
    from events
)
select e1.user_id, count(*) as n_pairs
from events_enriched e1
join events_enriched e2
  on e1.user_id = e2.user_id and e2.rn = e1.rn + 1
where e1.event_name = 'search' and e2.event_name = 'purchase'
group by e1.user_id;
```

**Skill output (abbreviated):**

> Static findings, no profile needed:
>
> 1. **Major:** `events_enriched` is referenced twice — Snowflake may compute the full-table window **twice**.
> 2. **Major:** the window runs over all columns (`select *`) and all history — no date bound.
> 3. **Major:** self-join to find adjacent events — `lead()` does this in one pass, no join.
>
> **Rewrite:**
>
> ```sql
> select user_id, count(*) as n_pairs
> from (
>     select user_id, event_name,
>            lead(event_name) over (partition by user_id order by event_at) as next_event
>     from events
>     where event_at >= dateadd('day', -90, current_date)  -- confirm window with user
> )
> where event_name = 'search' and next_event = 'purchase'
> group by user_id;
> ```
>
> One scan, one window, no self-join. Flagged: the 90-day bound is an assumption — if the original intent was all-history, remove it (and expect proportional cost). For before/after runtime numbers, chain to `warehouse-query-optimization` once query_history access exists.

---

## Example 3: The query is fine

**User prompt:** "Anything wrong with this?"

```sql
select user_id, plan, signup_at
from dim_users
where signup_at >= '2026-01-01'
  and plan in ('pro', 'team');
```

**Skill output:**

> No blockers, no majors. Two notes:
>
> - Explicit projection, sargable filters, bounded scan — this is the shape we want.
> - Minor: if `dim_users` is rebuilt daily, consider pinning the snapshot date in pipelines for reproducibility.
>
> Clean review. No rewrite needed.

(A clean review is a valid output — don't invent findings.)
