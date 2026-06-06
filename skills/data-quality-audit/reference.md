# Data Quality Audit — Reference

## Common DQ failure modes (by source)

### Event pipelines (e.g., Segment, Kafka, Snowplow)
- Duplicate events from retries
- Schema drift (new properties added silently)
- Late-arriving events (events from days ago suddenly appear)
- Missing events from one client (mobile crashed, web outage)

### Application database replicas (CDC)
- Lag between source and replica
- Schema migrations not reflected
- Deleted rows still present (soft-delete vs hard-delete confusion)

### Vendor APIs (e.g., Stripe, Salesforce)
- Pagination dropping records
- Rate-limit pauses
- API version changes
- Currency / amount-in-cents inconsistencies

### Manual uploads (CSV from finance, ops)
- Encoding issues (Excel mangles dates)
- Trailing whitespace
- Free-text fields that should be enums
- Inconsistent naming across uploads

## Thresholds (reasonable defaults)

| Check | Pass | Warn | Fail |
|---|---|---|---|
| PK uniqueness | 0 dupes | — | Any dupes |
| Critical nulls | 0% | — | > 0% |
| Non-critical nulls | < 1% | 1-5% | > 5% |
| Freshness | within SLA | 1-1.5× SLA | > 1.5× SLA |
| Day-over-day volume | ±25% | 25-50% | > 50% |
| Orphan FKs | 0 | 0.01-0.1% | > 0.1% |

Tune to context — these are defaults, not laws.

## Detecting silent schema drift

```sql
-- Snapshot column list and compare
with current_schema as (
    select column_name, data_type, ordinal_position
    from information_schema.columns
    where table_name = 'EVENTS'
),
expected_schema as (
    select * from (values
        ('USER_ID', 'VARCHAR', 1),
        ('EVENT_NAME', 'VARCHAR', 2),
        ('EVENT_AT', 'TIMESTAMP_NTZ', 3)
        -- ...
    ) as t(column_name, data_type, ordinal_position)
)
select
    coalesce(c.column_name, e.column_name) as col,
    c.data_type as actual_type,
    e.data_type as expected_type,
    case
        when c.column_name is null then 'MISSING'
        when e.column_name is null then 'EXTRA'
        when c.data_type != e.data_type then 'TYPE_DRIFT'
        else 'OK'
    end as status
from current_schema c
full outer join expected_schema e using (column_name)
where status != 'OK';
```

## Sampling for large tables

```sql
-- Snowflake: 1% sample for fast distribution checks
select * from huge_events sample (1) where ...;

-- BigQuery
select * from `proj.dataset.huge_events` tablesample system (1 percent) ...;
```

## Anomaly detection (lightweight)

For metric history, flag days outside `mean ± 3σ` of the trailing 14-day window:

```sql
with daily as (
    select event_date, count(*) as n
    from events
    group by event_date
),
windowed as (
    select
        event_date,
        n,
        avg(n) over (order by event_date rows between 14 preceding and 1 preceding) as mean_14d,
        stddev(n) over (order by event_date rows between 14 preceding and 1 preceding) as std_14d
    from daily
)
select
    event_date,
    n,
    mean_14d,
    std_14d,
    abs(n - mean_14d) / nullif(std_14d, 0) as z_score
from windowed
where abs(n - mean_14d) / nullif(std_14d, 0) > 3
order by event_date desc;
```

## Audit cadence recommendations

| Table type | Audit cadence |
|---|---|
| Production fact tables | Daily, automated |
| Source raw tables | Weekly + on any pipeline change |
| Vendor API extracts | Daily |
| Manual uploads | On every upload |

Automate via dbt tests, Great Expectations, or a scheduled run of this skill's script.

## Communicating DQ findings

When reporting issues:

1. **Severity first** (FAIL / WARN)
2. **Specifically what** (numbers, not "looks off")
3. **Specifically where** (table, partition, date)
4. **Hypothesis** (what likely caused it)
5. **Blast radius** (which downstream models / dashboards are affected)
6. **Recommended action** (block / coerce / investigate)
