# Funnel Analysis — Reference

## Strict vs non-strict funnels

### Strict (sequential)

```sql
with step1 as (select user_id, min(event_at) as t1 from events where event_name = 'landing' group by user_id),
step2 as (
    select s1.user_id, min(e.event_at) as t2
    from step1 s1
    join events e on e.user_id = s1.user_id
    where e.event_name = 'signup'
      and e.event_at > s1.t1
      and e.event_at < dateadd('hour', 1, s1.t1)
    group by s1.user_id
),
...
```

Each step depends on the previous step's timestamp. Event must occur **after** the prior step within the conversion window.

### Non-strict (any order)

```sql
select
    count(distinct case when event_name = 'a' then user_id end) as did_a,
    count(distinct case when event_name = 'b' then user_id end) as did_b,
    count(distinct case when event_name = 'c' then user_id end) as did_c,
    count(distinct case when event_name in ('a','b','c')
        and user_id in (subquery for users with all 3)
    then user_id end) as did_all
from events;
```

Use when measuring feature adoption combinations rather than a flow.

## Conversion window pitfalls

Choosing too long a window:
- Inflates conversion to artificial highs
- Hides drop-off (users still "converting" in week 4 dilute the signal)
- Makes the funnel insensitive to product changes

Choosing too short a window:
- Misses legitimately converting users
- Penalizes slow-but-real conversion paths

**Default heuristic:** match the window to the natural user intent timeframe:
- Single session (30 min) — fast flows like checkout, signup
- Same day (24h) — onboarding requiring email check, etc.
- Week — multi-touch purchase or activation
- Month — sales-led / enterprise flows

## Time-between-steps measurement

```sql
select
    median(datediff('second', t1, t2)) as median_s_step1_to_step2,
    avg(datediff('second', t1, t2))    as avg_s_step1_to_step2,
    percentile_cont(0.95) within group (order by datediff('second', t1, t2)) as p95_s
from funnel_table;
```

`p50` is more useful than `avg` because funnel times are heavily right-skewed.

## Drop-off diagnosis decision tree

```
Is the drop-off concentrated in a segment?
├── Yes
│   ├── Is the segment a meaningful share (> 10%)? → fix the segment
│   └── No → segment-specific bug, lower priority
└── No (uniform across segments)
    ├── Is the step technically reliable? (no errors, fast load)
    │   ├── No → engineering fix
    │   └── Yes → UX/design fix
```

## Funnel chart conventions

- **Bar chart**: each bar = step. Width or height = users. Most readable.
- **Sankey diagram**: shows where users go after dropping off. Useful for non-strict funnels with multiple paths.
- **Step CR labels above bars**: shows the step-to-step rate (the actionable number).
- **End-to-end CR in title**: gives the headline.

Avoid the literal "funnel" trapezoid shape — it's harder to read than a bar chart and the visual width adds no information.

## Snowflake template

```sql
-- 4-step strict funnel with same-session window (30 min between steps)
with base as (
    select user_id, event_name, event_at
    from events
    where event_at >= dateadd('day', -14, current_date)
      and event_at <  current_date
),
s1 as (
    select user_id, min(event_at) as t1
    from base where event_name = 'landing'
    group by user_id
),
s2 as (
    select s1.user_id, min(b.event_at) as t2
    from s1 join base b on b.user_id = s1.user_id
    where b.event_name = 'signup'
      and b.event_at >= s1.t1
      and b.event_at <= dateadd('minute', 30, s1.t1)
    group by s1.user_id
),
s3 as (
    select s2.user_id, min(b.event_at) as t3
    from s2 join base b on b.user_id = s2.user_id
    where b.event_name = 'email_verify'
      and b.event_at >= s2.t2
      and b.event_at <= dateadd('day', 1, s2.t2)
    group by s2.user_id
),
s4 as (
    select s3.user_id, min(b.event_at) as t4
    from s3 join base b on b.user_id = s3.user_id
    where b.event_name = 'first_action'
      and b.event_at >= s3.t3
      and b.event_at <= dateadd('day', 7, s3.t3)
    group by s3.user_id
)
select
    (select count(*) from s1) as n_landing,
    (select count(*) from s2) as n_signup,
    (select count(*) from s3) as n_verify,
    (select count(*) from s4) as n_first_action;
```

## Pre-aggregated event store optimization

If running funnels frequently on large data, pre-compute a user-event matrix:

```sql
create or replace table user_first_event_times as
select
    user_id,
    min(case when event_name = 'landing' then event_at end)      as t_landing,
    min(case when event_name = 'signup' then event_at end)       as t_signup,
    min(case when event_name = 'email_verify' then event_at end) as t_verify,
    min(case when event_name = 'first_action' then event_at end) as t_first
from events
group by user_id;
```

Then funnel queries become single-table scans with `where t_signup is not null and t_signup > t_landing and ...`.
