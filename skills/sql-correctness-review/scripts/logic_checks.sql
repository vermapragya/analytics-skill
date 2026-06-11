-- ============================================================
-- SQL Correctness Review — templated evidence queries
-- Replace <placeholders> and run each block independently.
-- Snowflake syntax; portable with minor edits.
-- ============================================================


-- ------------------------------------------------------------
-- 1. GRAIN / DUPLICATE CHECK
-- Zero rows = output grain holds. Any rows = duplicates exist.
-- ------------------------------------------------------------
select <grain_cols>, count(*) as n_rows
from (<query_under_review>)
group by <grain_cols>
having count(*) > 1
order by n_rows desc
limit 20;

-- Inspect one offender: the columns that DIFFER between its rows
-- point at the culprit join or missing dedup.
select *
from (<query_under_review>)
where <grain_col> = '<offending_key>'
order by 1;


-- ------------------------------------------------------------
-- 2. JOIN FANOUT AUDIT (run per join)
-- ------------------------------------------------------------
-- 2a. Is the assumed-"1" side actually unique on the join key?
select <join_key>, count(*) as n
from <right_table>
group by <join_key>
having count(*) > 1
order by n desc
limit 10;

-- 2b. Row count before vs after the join.
-- after > before on an INNER join = fanout, full stop.
select
    (select count(*) from <left_table> where <filters>) as rows_before_join,
    (select count(*)
     from <left_table> l
     join <right_table> r on <join_condition>
     where <filters>)                                   as rows_after_join;

-- 2c. Worst-multiplying keys (where did the explosion come from?)
select l.<join_key>, count(*) as n_rows
from <left_table> l
join <right_table> r on <join_condition>
group by l.<join_key>
order by n_rows desc
limit 10;


-- ------------------------------------------------------------
-- 3. JOIN TYPE / DIRECTION CHECKS
-- ------------------------------------------------------------
-- 3a. How many left-side rows does an INNER join silently drop?
-- If these rows belong in the output, the join must be LEFT.
select count(*) as unmatched_left_rows
from <left_table> l
left join <right_table> r on <join_condition>
where r.<join_key> is null;

-- 3b. LEFT-join-converted-to-INNER detector:
-- count rows where the WHERE predicate on the right table
-- destroys unmatched (NULL) rows.
select count(*) as rows_killed_by_where
from <left_table> l
left join <right_table> r on <join_condition>
where r.<join_key> is null
  -- and these rows FAIL the suspect predicate by being NULL:
  and not (<where_predicate_on_right_table> );  -- e.g. not (r.status = 'completed')

-- 3c. Join key type mismatch — compare data types of both keys.
select table_name, column_name, data_type
from information_schema.columns
where (table_name = '<LEFT_TABLE>'  and column_name = '<JOIN_KEY>')
   or (table_name = '<RIGHT_TABLE>' and column_name = '<JOIN_KEY>');


-- ------------------------------------------------------------
-- 4. NULL HANDLING CHECKS
-- ------------------------------------------------------------
-- 4a. NOT IN trap: does the subquery yield any NULLs?
-- Any rows here + a NOT IN on this column = the outer query returns 0 rows.
select count(*) as null_values_in_subquery
from <subquery_table>
where <subquery_col> is null;

-- 4b. NULL join keys (these rows never match anything)
select
    count_if(<join_key> is null)                  as null_keys,
    count_if(<join_key> is null) / count(*)       as null_key_share
from <table>;

-- 4c. Negative-filter NULL loss: rows dropped by `col != 'x'`
-- because col IS NULL (decide their fate explicitly).
select count(*) as nulls_dropped_by_negative_filter
from <table>
where <col> is null;

-- 4d. count(*) vs count(col) divergence per column
select
    count(*)                        as n_rows,
    count(<col>)                    as n_nonnull,
    count(*) - count(<col>)         as n_null,
    avg(<col>)                      as avg_nonnull_only  -- note the denominator!
from <table>;


-- ------------------------------------------------------------
-- 5. CASE BRANCH COVERAGE
-- Paste the exact CASE expression. Read as a branch histogram:
--   - NULL branch with rows  = missing ELSE or missing NULL branch
--   - expected branch absent = possibly dead code (check branch order)
-- ------------------------------------------------------------
select
    <case_expression> as branch,
    count(*)          as n_rows,
    count(*) / sum(count(*)) over () as share
from <table>
group by 1
order by n_rows desc;

-- 5a. Dead-branch detector: rows matching a LATER branch's condition
-- that were already captured by an EARLIER branch.
select count(*) as rows_stolen_by_earlier_branch
from <table>
where (<later_branch_condition>)
  and (<earlier_branch_condition>);


-- ------------------------------------------------------------
-- 6. RECONCILIATION
-- ------------------------------------------------------------
-- 6a. Against the driving table (1:1 pipeline output can't exceed it)
select
    (select count(*) from <driving_table> where <same_filters>) as anchor_rows,
    (select count(*) from (<query_under_review>))               as output_rows;

-- 6b. Two disagreeing queries: diff populations, then profile the diff.
select 'A_only' as side, <keys>
from (select <keys> from (<query_a>) minus select <keys> from (<query_b>))
union all
select 'B_only' as side, <keys>
from (select <keys> from (<query_b>) minus select <keys> from (<query_a>));
