# Rule: dbt Conventions

Always-follow conventions for dbt projects.

## File and folder structure

```
models/
├── staging/
│   ├── <source>/
│   │   ├── stg_<source>__<table>.sql
│   │   ├── stg_<source>__<table>.yml
│   │   └── _<source>__sources.yml
├── intermediate/
│   └── int_<concept>.sql
└── marts/
    ├── <domain>/
    │   ├── fct_<event>.sql
    │   ├── dim_<entity>.sql
    │   └── _<domain>__models.yml
```

## Naming

- `stg_<source>__<table>` — staged from raw (double underscore separates source and table)
- `int_<concept>` — intermediate transformations
- `fct_<event>` — fact tables (events, transactions, occurrences)
- `dim_<entity>` — dimension tables (users, products, accounts)
- All lowercase, snake_case

## Materialization

| Layer | Default materialization |
|---|---|
| Staging | view |
| Intermediate | view or ephemeral |
| Fact (large, append-only) | incremental |
| Fact (small, full refresh) | table |
| Dimension | table |

## Testing (minimum bar)

For every model:
- `not_null` on primary key columns
- `unique` or `dbt_utils.unique_combination_of_columns` on primary key

For dimensions:
- `relationships` test to source/fact tables

For facts:
- `accepted_values` test on enum columns
- Volume tests where applicable

## Documentation

- Model description in `<model>.yml`
- Column descriptions for all PK columns and metric columns
- Source freshness defined for staging sources
- README in each marts subdirectory explaining the domain

## Refs and sources

- Always use `{{ ref() }}` for cross-model dependencies (never raw table names)
- Use `{{ source() }}` for raw / external data
- Configure source freshness for monitoring

## Style

- 4 spaces for indentation
- One column per line in SELECT
- CTEs at same indent level as the `with` keyword
- Final `select * from <last_cte>` at the bottom

## Macros

- Reusable logic → macros in `macros/`
- Snake_case naming
- Docstring at top of macro file

## See also
- `rules/snowflake-sql-style.md`
- `skills/modular-sql-ctes/` for SQL structure
- `skills/metric-definition/` for documenting metrics in dbt
