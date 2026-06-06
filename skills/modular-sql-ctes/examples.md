# Modular SQL — Examples

## Example 1: Refactor a monolithic user-engagement query

**Before:**

```sql
SELECT
    u.user_id,
    u.country,
    u.plan_tier,
    COUNT(DISTINCT CASE WHEN e.event_name = 'login' THEN e.session_id END) AS sessions,
    SUM(CASE WHEN e.event_name = 'purchase' THEN o.amount ELSE 0 END) AS revenue,
    COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN o.order_id END) AS orders,
    MAX(e.event_at) AS last_seen
FROM raw.users.users u
LEFT JOIN raw.events.product_events e ON e.user_id = u.user_id
LEFT JOIN raw.orders.orders o ON o.user_id = u.user_id AND o.order_at BETWEEN e.event_at - INTERVAL '1 hour' AND e.event_at + INTERVAL '1 hour'
WHERE u.created_at >= '2026-01-01'
  AND u.is_test = FALSE
  AND e.event_at >= '2026-01-01'
GROUP BY 1, 2, 3
HAVING COUNT(*) > 0;
```

**After (refactored):**

```sql
-- =========================================================
-- Model: fct_user_engagement_30d
-- Grain: one row per user (created in last 30 days)
-- Primary key: user_id
-- Sources: raw.users.users, raw.events.product_events, raw.orders.orders
-- =========================================================

with stg_users as (
    select
        user_id,
        country,
        plan_tier,
        created_at
    from raw.users.users
    where created_at >= dateadd('day', -30, current_date)
      and is_test = false
),

stg_events as (
    select
        user_id,
        session_id,
        event_name,
        event_at
    from raw.events.product_events
    where event_at >= dateadd('day', -30, current_date)
),

stg_orders as (
    select
        user_id,
        order_id,
        amount,
        order_at
    from raw.orders.orders
    where order_at >= dateadd('day', -30, current_date)
),

int_sessions as (
    select
        user_id,
        count(distinct session_id) as session_count,
        max(event_at) as last_seen
    from stg_events
    where event_name = 'login'
    group by user_id
),

int_orders_agg as (
    select
        user_id,
        count(distinct order_id) as order_count,
        sum(amount) as total_revenue
    from stg_orders
    group by user_id
),

fct_user_engagement_30d as (
    select
        u.user_id,
        u.country,
        u.plan_tier,
        coalesce(s.session_count, 0) as sessions,
        coalesce(o.order_count, 0) as orders,
        coalesce(o.total_revenue, 0) as revenue,
        s.last_seen
    from stg_users u
    left join int_sessions s using (user_id)
    left join int_orders_agg o using (user_id)
)

select * from fct_user_engagement_30d;
```

**What changed:**
- Removed the time-window join between events and orders (was both wrong and slow)
- Filtered each source independently at the staging layer
- Aggregated orders separately, then joined (avoids grain inflation)
- `coalesce` ensures missing data shows as 0, not NULL
- Header documents grain and PK

---

## Example 2: dbt model layout

**File structure:**
```
models/
├── staging/
│   ├── stg_product__events.sql
│   ├── stg_product__users.sql
│   └── sources.yml
├── intermediate/
│   └── int_user_daily_metrics.sql
└── marts/
    └── product/
        ├── fct_user_daily_activity.sql
        └── fct_user_daily_activity.yml
```

**`fct_user_daily_activity.sql`:**
```sql
with daily as (
    select * from {{ ref('int_user_daily_metrics') }}
),
users as (
    select * from {{ ref('stg_product__users') }}
)
select
    d.user_id,
    d.activity_date,
    u.country,
    u.plan_tier,
    d.total_events,
    d.purchase_count,
    d.session_count,
    case when d.purchase_count > 0 then 1 else 0 end as did_purchase
from daily d
inner join users u using (user_id)
```

**`fct_user_daily_activity.yml`:**
```yaml
version: 2
models:
  - name: fct_user_daily_activity
    description: One row per user per day with engagement and purchase metrics
    columns:
      - name: user_id
        description: Unique user identifier
        tests: [not_null]
      - name: activity_date
        description: UTC date of activity
        tests: [not_null]
      - name: total_events
        tests: [not_null]
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [user_id, activity_date]
```

---

## Example 3: Fixing a hidden grain bug

**User prompt:** "This query returns more rows than I expect."

**Before:**
```sql
select u.user_id, count(*) as order_count
from users u
left join orders o using (user_id)
left join refunds r using (order_id)
group by u.user_id;
```

**Diagnosis:**

`order_count` counts (user × order × refund) rows. Users with multiple refunds per order get double-counted.

**After:**
```sql
with order_dedup as (
    select distinct user_id, order_id
    from orders
)
select user_id, count(*) as order_count
from order_dedup
group by user_id;
```

**Lesson:** when joining a 1:N table you don't need, dedupe at the right grain before counting.
