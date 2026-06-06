-- Strict-ordered funnel template (Snowflake).
--
-- Replace {step1_event}, {step2_event}, etc. with your event names.
-- Adjust {window_N} for max time between step N-1 and step N.

with base as (
    select user_id, event_name, event_at
    from events
    where event_at >= dateadd('day', -{lookback_days}, current_date)
      and event_at <  current_date
),

s1 as (
    select user_id, min(event_at) as t1
    from base
    where event_name = '{step1_event}'
    group by user_id
),

s2 as (
    select s1.user_id, min(b.event_at) as t2
    from s1
    join base b on b.user_id = s1.user_id
    where b.event_name = '{step2_event}'
      and b.event_at >= s1.t1
      and b.event_at <= dateadd('minute', {window_2_minutes}, s1.t1)
    group by s1.user_id
),

s3 as (
    select s2.user_id, min(b.event_at) as t3
    from s2
    join base b on b.user_id = s2.user_id
    where b.event_name = '{step3_event}'
      and b.event_at >= s2.t2
      and b.event_at <= dateadd('minute', {window_3_minutes}, s2.t2)
    group by s2.user_id
),

s4 as (
    select s3.user_id, min(b.event_at) as t4
    from s3
    join base b on b.user_id = s3.user_id
    where b.event_name = '{step4_event}'
      and b.event_at >= s3.t3
      and b.event_at <= dateadd('minute', {window_4_minutes}, s3.t3)
    group by s3.user_id
)

select
    (select count(*) from s1) as step_1_users,
    (select count(*) from s2) as step_2_users,
    (select count(*) from s3) as step_3_users,
    (select count(*) from s4) as step_4_users,
    (select count(*) from s2) * 1.0 / nullif((select count(*) from s1), 0) as step_1_to_2_cr,
    (select count(*) from s3) * 1.0 / nullif((select count(*) from s2), 0) as step_2_to_3_cr,
    (select count(*) from s4) * 1.0 / nullif((select count(*) from s3), 0) as step_3_to_4_cr,
    (select count(*) from s4) * 1.0 / nullif((select count(*) from s1), 0) as end_to_end_cr,
    (select median(datediff('second', t1, t2)) from s2 join s1 using (user_id)) as median_s_1_2,
    (select median(datediff('second', t2, t3)) from s3 join s2 using (user_id)) as median_s_2_3,
    (select median(datediff('second', t3, t4)) from s4 join s3 using (user_id)) as median_s_3_4
;
