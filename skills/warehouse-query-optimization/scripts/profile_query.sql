-- Snowflake query profiling helpers.
--
-- 1) Get profile stats for a specific query
-- 2) Find slow / expensive queries on a warehouse
-- 3) Find queries with remote spill (warehouse too small or query too big)
-- 4) Top tables by bytes scanned in last 7 days

-- 1) Profile a single query
select
    query_id,
    user_name,
    warehouse_name,
    warehouse_size,
    total_elapsed_time / 1000 as runtime_s,
    bytes_scanned / pow(1024, 3) as gb_scanned,
    bytes_spilled_to_local_storage / pow(1024, 2) as mb_local_spill,
    bytes_spilled_to_remote_storage / pow(1024, 2) as mb_remote_spill,
    partitions_scanned,
    partitions_total,
    partitions_scanned * 1.0 / nullif(partitions_total, 0) as pct_partitions_scanned,
    credits_used_cloud_services,
    query_text
from snowflake.account_usage.query_history
where query_id = '<paste query_id here>';

-- 2) Top 20 slow queries on a warehouse in the last 24h
select
    query_id,
    user_name,
    total_elapsed_time / 1000 as runtime_s,
    bytes_scanned / pow(1024, 3) as gb_scanned,
    bytes_spilled_to_remote_storage / pow(1024, 2) as mb_remote_spill,
    left(query_text, 200) as query_preview
from snowflake.account_usage.query_history
where warehouse_name = '<warehouse_name>'
  and start_time >= dateadd('hour', -24, current_timestamp)
  and execution_status = 'SUCCESS'
order by total_elapsed_time desc
limit 20;

-- 3) Queries with remote spill (last 7d)
select
    query_id,
    user_name,
    warehouse_size,
    bytes_spilled_to_remote_storage / pow(1024, 3) as gb_remote_spill,
    total_elapsed_time / 1000 as runtime_s,
    left(query_text, 200) as query_preview
from snowflake.account_usage.query_history
where bytes_spilled_to_remote_storage > 0
  and start_time >= dateadd('day', -7, current_date)
order by bytes_spilled_to_remote_storage desc
limit 50;

-- 4) Top tables by bytes scanned (last 7d) — finds high-traffic tables
select
    regexp_substr(query_text, 'from\\s+([\\w\\.\\"]+)', 1, 1, 'i', 1) as table_name,
    count(*) as query_count,
    sum(bytes_scanned) / pow(1024, 3) as total_gb_scanned,
    avg(total_elapsed_time) / 1000 as avg_runtime_s
from snowflake.account_usage.query_history
where start_time >= dateadd('day', -7, current_date)
  and execution_status = 'SUCCESS'
  and bytes_scanned > 0
group by 1
order by total_gb_scanned desc
limit 50;
