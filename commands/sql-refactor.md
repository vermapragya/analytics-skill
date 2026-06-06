---
name: sql-refactor
description: Refactor a SQL query into modular CTE structure with reviewer agent feedback
---

# /sql-refactor

Refactor a SQL query into a maintainable, layered CTE structure.

## Usage

```
/sql-refactor
```

Then paste the SQL or provide a path.

## Workflow

1. Load `skills/modular-sql-ctes/SKILL.md`
2. Identify grain and primary key
3. Split into staging / intermediate / fact layers
4. Add header comment block (grain, PK, sources, refresh, owner)
5. Invoke `agents/sql-reviewer.md` to validate the refactored version
6. If `skills/warehouse-query-optimization` is relevant (slow query), include perf notes

## Output

- Refactored SQL with proper structure
- Summary of changes
- Reviewer agent feedback
