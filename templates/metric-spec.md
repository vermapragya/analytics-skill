# Metric Spec: <Metric Name>

## Identifier
- **Canonical name:** <snake_case_name>
- **Display name:** <Human Readable>
- **Owner:** <name / team>
- **Last updated:** <YYYY-MM-DD>
- **Status:** <draft | active | deprecated>

## Definition
**Business question:** <what decision does this support?>

**Plain English:** <one sentence anyone can understand>

**Formula:**
```
<pseudo-math or English>
```

**Grain:** <per user | per session | per day | per order>

## Source
- **Primary table:** `<warehouse.schema.table>`
- **Event(s):** `<event_name>`
- **Refresh cadence:** <daily | hourly | streaming>
- **Latency:** <e.g., T+1 day>

## Canonical SQL (Snowflake)
```sql
-- canonical query
```

## Inclusions / Exclusions
- **Includes:** <e.g., paid + free users>
- **Excludes:** <e.g., internal users, bots>

## Edge cases
- <e.g., refunded transactions handling>
- <e.g., timezone>

## Guardrails
- <guardrail metric 1>: <threshold>
- <guardrail metric 2>: <threshold>

## Known caveats
- <e.g., schema change cutoff>

## Canonical visualization
<e.g., 12-week rolling line, weekly snapshot>

## Anti-patterns
- Do NOT <...>
- Do NOT <...>

## Related metrics
- <metric>: <relationship>

## Change log
- <YYYY-MM-DD> — <change>
