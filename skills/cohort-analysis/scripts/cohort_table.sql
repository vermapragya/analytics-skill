-- Cohort retention table template (Snowflake).
--
-- Parameters (replace with literals or use a templating layer):
--   {anchor_event}   : e.g., 'signup'
--   {grain}          : 'week' | 'day' | 'month'
--   {lookback}       : how many cohort periods to include (e.g., 16)
--
-- Output: one row per cohort, columns = period N retention counts.
-- Divide by cohort_size in a downstream layer or visualization tool to get percentages.

with cohort_anchor as (
    select
        user_id,
        date_trunc('{grain}', min(event_at)) as cohort_period
    from events
    where event_name = '{anchor_event}'
      and event_at >= dateadd('{grain}', -{lookback}, current_date)
    group by user_id
),

activity as (
    select
        user_id,
        date_trunc('{grain}', event_at) as activity_period
    from events
    where event_at >= dateadd('{grain}', -{lookback}, current_date)
    group by user_id, activity_period
),

joined as (
    select
        c.user_id,
        c.cohort_period,
        a.activity_period,
        datediff('{grain}', c.cohort_period, a.activity_period) as period_n
    from cohort_anchor c
    left join activity a using (user_id)
    where a.activity_period >= c.cohort_period
)

select
    cohort_period,
    count(distinct user_id)                                                  as cohort_size,
    count(distinct case when period_n = 0  then user_id end)                  as p0,
    count(distinct case when period_n = 1  then user_id end)                  as p1,
    count(distinct case when period_n = 2  then user_id end)                  as p2,
    count(distinct case when period_n = 4  then user_id end)                  as p4,
    count(distinct case when period_n = 8  then user_id end)                  as p8,
    count(distinct case when period_n = 12 then user_id end)                  as p12,
    count(distinct case when period_n = 24 then user_id end)                  as p24
from joined
group by cohort_period
order by cohort_period;
