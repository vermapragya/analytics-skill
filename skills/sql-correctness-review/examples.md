# SQL Correctness Review — Examples

## Example 1: "Revenue is 3× too high"

**User prompt:** "Finance says June revenue is $1.27M but my query says $4.1M. Query below."

```sql
select sum(o.total) as revenue
from orders o
join order_items i on i.order_id = o.order_id
where o.created_at >= '2026-06-01' and o.created_at < '2026-07-01';
```

**Skill output (abbreviated):**

> Grain check on the join: is `order_items` unique on `order_id`?
>
> ```sql
> select order_id, count(*) from order_items group by 1 having count(*) > 1 limit 5;
> -- → 84% of orders have 2+ items. Average 3.2 items/order.
> ```
>
> **Finding (blocker): join fanout.** `o.total` is order-grain, but the items join repeats each order row once per item — `sum(o.total)` is inflated by the average items-per-order (3.2×). $4.1M / 3.2 ≈ $1.28M ≈ finance's number.
>
> **Fix:** the items join contributes nothing here — drop it:
>
> ```sql
> select sum(o.total) as revenue
> from orders o
> where o.created_at >= '2026-06-01' and o.created_at < '2026-07-01';
> ```
>
> **Reconciliation:** $1.281M vs finance $1.270M (+0.8%) — residual is refund timing (we book at order time; finance nets refunds). Documented, not hidden.

---

## Example 2: The LEFT join that wasn't

**User prompt:** "I want ALL users with their completed-order count, but users with zero orders are missing from my output."

```sql
select u.user_id, count(o.order_id) as n_orders
from users u
left join orders o on o.user_id = u.user_id
where o.status = 'completed'
group by u.user_id;
```

**Skill output (abbreviated):**

> **Finding (blocker): WHERE clause converts the LEFT join to INNER.** For users with no orders, `o.status` is NULL; `NULL = 'completed'` is not true; the row is filtered out.
>
> Evidence: `select count(*) from users u left join orders o on o.user_id = u.user_id where o.user_id is null` → 18,212 users with zero orders, all missing from your output.
>
> **Fix:** move the predicate into the ON clause:
>
> ```sql
> select u.user_id, count(o.order_id) as n_orders
> from users u
> left join orders o
>   on o.user_id = u.user_id
>  and o.status = 'completed'
> group by u.user_id;
> ```
>
> Note `count(o.order_id)` (not `count(*)`) is correct here — it counts non-NULL matches, so zero-order users get 0, not 1.

---

## Example 3: The NOT IN that returned nothing

**User prompt:** "This should return active non-churned users but it returns 0 rows. The tables aren't empty."

```sql
select user_id from users
where status = 'active'
  and user_id not in (select user_id from churn_events);
```

**Skill output (abbreviated):**

> ```sql
> select count(*) from churn_events where user_id is null;
> -- → 37 rows with NULL user_id (unattributed churn events)
> ```
>
> **Finding (blocker): NOT IN + NULL.** `x NOT IN (..., NULL)` can never evaluate TRUE — one NULL in the subquery zeroes the whole result.
>
> **Fix:**
>
> ```sql
> select u.user_id from users u
> where u.status = 'active'
>   and not exists (select 1 from churn_events c where c.user_id = u.user_id);
> -- → 84,310 rows
> ```
>
> Also flagged for `data-quality-audit`: why does `churn_events` have NULL user_ids at all?

---

## Example 4: CASE buckets that don't add up

**User prompt:** "My order-size segments sum to less than total orders."

```sql
select case when amount >= 100 then 'large'
            when amount >= 10  then 'medium'
            when amount >= 0   then 'small'
       end as segment,
       count(*) as n
from orders
group by 1;
```

**Skill output (abbreviated):**

> Branch coverage check:
>
> | segment | n |
> |---|---|
> | small | 61,204 |
> | medium | 48,112 |
> | large | 12,007 |
> | NULL | 3,491 |
>
> **Finding (major): no ELSE, two unmodeled populations land in NULL:**
> - `amount IS NULL` (1,204 rows — pending orders not yet priced)
> - `amount < 0` (2,287 rows — refunds)
>
> **Fix:**
>
> ```sql
> case when amount is null then 'unpriced'
>      when amount < 0     then 'refund'
>      when amount >= 100  then 'large'
>      when amount >= 10   then 'medium'
>      else 'small'
> end
> ```
>
> Rule applied: every production CASE gets an ELSE, and NULL gets an explicit branch. The 'unpriced' and 'refund' buckets appearing in the report is a feature — they were invisible before.
