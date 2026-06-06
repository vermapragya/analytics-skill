---
name: metric-definition
description: Writes precise metric specs with grain, owner, source, formula, guardrails, and known caveats. Use when the user mentions metric definition, metric spec, KPI definition, "what is a session", "define X", North Star metric, or needs to disambiguate a metric across teams.
---

# Metric Definition

## When to use this skill

Use whenever a metric is being created, re-defined, or disputed. Triggers:

- "Define our North Star metric"
- "What counts as an active user?"
- "Write a spec for revenue per user"
- "Why is finance's revenue number different from ours?"
- "Document this metric"

Most metric arguments are actually definition arguments. Force the question into a spec.

## Required inputs

| Input | Why it matters |
|---|---|
| Metric name | What stakeholders call it |
| Business question | What decision the metric supports |
| Owner | Who is accountable for accuracy |
| Source tables | Where the underlying data lives |
| Grain | Per user / session / day / order |

## Workflow

1. **Force the business question.** "Why does this metric exist?" If the user can't answer, the metric shouldn't exist yet.

2. **Pin down the grain.** "Active users per *what*?" — per day, per week, per month. The same metric name with different grains is three different metrics.

3. **Define the SQL.** Even if the user doesn't ask for it, write the canonical query. Vague definitions become inconsistent dashboards.

4. **Identify edge cases up front.** For each metric, ask:
   - What about deleted/banned users?
   - Internal/test users?
   - Refunded transactions?
   - Multiple devices per user?
   - Timezone (event time vs reporting time)?

5. **Define guardrails.** A primary metric without guardrails will get gamed. List 1-3 metrics that must not regress when this one moves.

6. **Pick the canonical visualization.** A line chart of weekly values? A cohort table? Specify so dashboards stay consistent.

7. **Write the spec** in the format below.

## Output format

```markdown
# Metric Spec: <Metric Name>

## Identifier
- **Canonical name:** <snake_case_name>
- **Display name:** <Human Readable>
- **Owner:** <name / team>
- **Last updated:** <YYYY-MM-DD>
- **Status:** <draft | active | deprecated>

## Definition
**Business question:** <What decision does this support?>

**Plain English:** <One sentence anyone in the company can understand.>

**Formula:**
```
<pseudo-math or English formula>
```

**Grain:** <per user | per session | per day | per order>

## Source
- **Primary table:** `<warehouse.schema.table>`
- **Event(s):** `<event_name>`
- **Refresh cadence:** <daily | hourly | streaming>
- **Latency:** <e.g., T+1 day>

## Canonical SQL (Snowflake)
\`\`\`sql
select
    date_trunc('week', event_at) as week,
    count(distinct user_id) as <metric_name>
from <table>
where event_name = '<event>'
  and is_internal_user = false
  and event_at >= '<start>'
group by 1
order by 1;
\`\`\`

## Inclusions / Exclusions
- **Includes:** <e.g., paid + free users>
- **Excludes:** <e.g., internal users, bots, soft-deleted accounts, test orgs>

## Edge cases
- <e.g., refunded transactions are excluded if refund occurred within reporting period>
- <e.g., multi-device users counted once via user_id>
- <e.g., all timestamps in UTC>

## Guardrails
- <guardrail_metric_1>: must not drop > <threshold>
- <guardrail_metric_2>: must not exceed <threshold>

## Known caveats
- <e.g., pre-2026 data uses a different event schema; do not compare>
- <e.g., mobile clients have a 24h sync delay>

## Canonical visualization
<e.g., 12-week rolling line chart, weekly snapshots, with prior-year overlay>

## Anti-patterns (do NOT do this)
- Do not redefine this metric in dashboards without updating this spec
- Do not aggregate this metric across teams that filter for different segments
- Do not present this metric without its guardrails

## Related metrics
- <metric>: related but distinct, defined as <how>
- <metric>: composes with this one for <decision>

## Change log
- 2026-04-01 — Excluded test_org_ids per data-quality audit
- 2026-01-15 — Initial definition
```

## Validation checks

- [ ] One canonical SQL query exists and runs
- [ ] Owner is a specific person, not a team alias
- [ ] Grain is unambiguous (no "daily/weekly" or "user/account" hedging)
- [ ] Inclusions and exclusions are explicit
- [ ] At least one guardrail is listed
- [ ] Spec is linked from the dashboards that show this metric

## Edge cases & failure modes

- **Two teams need different filters.** Don't fork. Add a parameter to the canonical metric (e.g., `dau_b2b` and `dau_b2c` both derive from `dau_base`).
- **The metric is calculated differently in different tools.** Pick the canonical query, deprecate the others, migrate dashboards.
- **The metric was wrong yesterday.** Flag in the change log immediately. Backfill if possible. Add a banner in dashboards if not.
- **A new event changes the definition.** This is a v2 metric, not a redefinition. Run both for a transition period.
- **Vanity metrics.** If the business question is "looks good on a slide," reject. Push for a metric tied to a decision.

## Related skills

- `data-quality-audit` — verify source table quality before finalizing
- `modular-sql-ctes` — structure the canonical SQL cleanly
- `stakeholder-readout` — communicate metric definitions to stakeholders
