# Cohort Analysis — Reference

## Denominator policies in detail

### Cohort-fixed (default)

```
retention_pct(cohort, period) = active_in_period / original_cohort_size
```

Pros: monotonic, easy to interpret, comparable across cohorts.  
Cons: hides whether dormant users return.

### Active-base (period-over-period)

```
retention_pct(cohort, period) = active_in_period / active_in_previous_period
```

Pros: shows stickiness of each period.  
Cons: can mask permanent loss; a tiny remaining cohort with 100% stickiness looks identical to a healthy one.

### Eligible-base (subscription products)

```
retention_pct(cohort, period) = active_in_period / users_with_active_subscription_in_period
```

Pros: correct for products where churn means account termination.  
Cons: requires precise subscription state tracking.

## "Smile curve" diagnostic

In healthy products, cohort retention has three phases:
1. Sharp drop in first few periods (onboarding losses)
2. Slower decline (lifecycle churn)
3. Asymptote — the long-term retained user base

If period 3 doesn't materialize and the curve keeps dropping toward zero, the product has no long-term retention. Common in tools that solve a one-time problem.

## Retention math reference

### N-day retention (point-in-time)

```sql
sum(case when has_event_on_day_n then 1 else 0 end) / cohort_size
```

### N-day-bracket retention (rolling)

```sql
sum(case when has_event_in_days_n_to_n_plus_window then 1 else 0 end) / cohort_size
```

Bracket retention is less noisy and more useful for most products.

### Rolling N-day-active (DAU/MAU style)

For a "DAU" definition: "active in the last 1 day" — equivalent to bracket retention with window=1.  
For a "WAU" definition: "active in the last 7 days" — bracket retention with window=7.

## Snowflake cohort table template

```sql
with cohort_anchor as (
    select
        user_id,
        date_trunc('week', min(event_at)) as cohort_week
    from events
    where event_name = 'signup'
    group by user_id
),
activity as (
    select
        user_id,
        date_trunc('week', event_at) as activity_week
    from events
    where event_at >= dateadd('week', -16, current_date)
    group by user_id, activity_week
),
joined as (
    select
        c.user_id,
        c.cohort_week,
        a.activity_week,
        datediff('week', c.cohort_week, a.activity_week) as week_n
    from cohort_anchor c
    left join activity a using (user_id)
)
select
    cohort_week,
    count(distinct user_id) as cohort_size,
    count(distinct case when week_n = 0 then user_id end) as w0,
    count(distinct case when week_n = 1 then user_id end) as w1,
    count(distinct case when week_n = 2 then user_id end) as w2,
    count(distinct case when week_n = 4 then user_id end) as w4,
    count(distinct case when week_n = 8 then user_id end) as w8,
    count(distinct case when week_n = 12 then user_id end) as w12
from joined
group by cohort_week
order by cohort_week;
```

For percentages, divide each `wN` column by `cohort_size` in a final select.

## BigQuery / Postgres notes

- BigQuery: `DATE_TRUNC(date, WEEK)` and `DATE_DIFF(d1, d2, WEEK)`
- Postgres: `date_trunc('week', timestamp_col)::date` and `(d1 - d2) / 7`

## Visualization conventions

- **Cohort table**: rows = cohort, columns = period. Conditional formatting (heatmap) reveals patterns.
- **Retention curves**: x = periods since anchor, y = retention %. One line per cohort. Newer cohorts = darker color.
- **Cohort triangle**: same as table but render only filled cells; missing = future periods.

## Sample-size warnings

A cohort with < 100 users produces unstable retention estimates. Either:
- Roll up to a longer cohort grain (weekly → monthly)
- Pool small cohorts
- Mark in the readout as "noisy estimate"
