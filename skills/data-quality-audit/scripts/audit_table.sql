-- Data Quality Audit — Snowflake template.
--
-- Replace placeholders with your context:
--   {schema}            : analytics
--   {table}             : fct_orders
--   {pk_cols}           : order_id (or "order_id, line_item_id" for composite)
--   {time_col}          : order_at
--   {critical_cols}     : order_id, user_id, order_at, amount
--   {freshness_sla_hr}  : 24
--   {parent_table}      : dim_users  (or NULL to skip FK check)
--   {parent_pk}         : user_id
--   {fk_col}            : user_id

-- 1. Row count + freshness
select
    count(*) as row_count,
    min({time_col}) as earliest_ts,
    max({time_col}) as latest_ts,
    datediff('hour', max({time_col}), current_timestamp) as hours_since_latest,
    case
        when datediff('hour', max({time_col}), current_timestamp) > {freshness_sla_hr} * 1.5 then 'FAIL'
        when datediff('hour', max({time_col}), current_timestamp) > {freshness_sla_hr} then 'WARN'
        else 'PASS'
    end as freshness_status
from {schema}.{table};

-- 2. PK uniqueness
select
    {pk_cols},
    count(*) as dupes
from {schema}.{table}
group by {pk_cols}
having count(*) > 1
limit 100;

-- 3. Null check on critical columns
select
    {critical_cols_null_check_block}  -- generated per column
from {schema}.{table};

-- 4. Schema
select column_name, data_type, ordinal_position
from {schema}.information_schema.columns
where table_name = upper('{table}')
order by ordinal_position;

-- 5. Day-over-day volume sanity (last 14 days)
with daily as (
    select
        date_trunc('day', {time_col}) as d,
        count(*) as cnt
    from {schema}.{table}
    where {time_col} >= dateadd('day', -14, current_date)
    group by d
)
select
    d,
    cnt,
    lag(cnt) over (order by d) as prev_cnt,
    case
        when lag(cnt) over (order by d) is null then null
        else (cnt - lag(cnt) over (order by d)) * 1.0 / lag(cnt) over (order by d)
    end as pct_change_vs_prev_day
from daily
order by d;

-- 6. Referential integrity (skip if {parent_table} is null)
select count(*) as orphan_rows
from {schema}.{table} c
left join {schema}.{parent_table} p
  on c.{fk_col} = p.{parent_pk}
where p.{parent_pk} is null;
