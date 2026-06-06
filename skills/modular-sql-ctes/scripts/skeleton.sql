-- =========================================================
-- Model: <fct_name>
-- Grain: <one row per X>
-- Primary key: <columns>
-- Sources:
--   <source_table_1>
--   <source_table_2>
-- Refresh: <cadence>
-- Owner: <@handle>
-- =========================================================

with stg_<source1> as (
    select
        -- cast and rename only
    from <source_table_1>
    where <minimal early filters>
),

stg_<source2> as (
    select
        -- cast and rename only
    from <source_table_2>
    where <minimal early filters>
),

int_<concept> as (
    -- one business concept at a time
    select
        ...
    from stg_<source1>
    group by ...
),

fct_<name> as (
    select
        -- explicit columns only
    from int_<concept>
    inner join stg_<source2> using (<join_key>)
)

select * from fct_<name>;
