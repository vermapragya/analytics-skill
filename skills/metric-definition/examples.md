# Metric Definition — Examples

## Example 1: Weekly Active Users (WAU)

```markdown
# Metric Spec: Weekly Active Users (wau_total)

## Identifier
- Canonical name: wau_total
- Display name: Weekly Active Users
- Owner: @sarah.kim (Data Platform)
- Last updated: 2026-04-15
- Status: active

## Definition
**Business question:** Are we keeping users coming back week over week?

**Plain English:** Count of distinct users who performed any logged action in the trailing 7 days.

**Formula:**
```
count(distinct user_id) where user has ≥1 event in [report_date - 6 days, report_date]
```

**Grain:** Reported daily, value is trailing 7 days.

## Source
- Primary table: `analytics.events.fct_user_events`
- Events: any
- Refresh cadence: daily at 06:00 UTC
- Latency: T+1 day

## Canonical SQL (Snowflake)
```sql
select
    report_date,
    count(distinct user_id) as wau_total
from (
    select
        d.calendar_date as report_date,
        e.user_id
    from analytics.calendar.dim_date d
    join analytics.events.fct_user_events e
      on e.event_at >= dateadd('day', -6, d.calendar_date)
     and e.event_at <  dateadd('day', 1, d.calendar_date)
    where d.calendar_date between '2026-01-01' and current_date - 1
      and e.is_internal_user = false
      and e.is_bot = false
)
group by report_date
order by report_date;
```

## Inclusions / Exclusions
- Includes: all customer-facing users (paid + free, all geographies)
- Excludes: internal users (`is_internal_user = true`), bots, soft-deleted accounts

## Edge cases
- All timestamps in UTC
- A user who created their account but never logged any event does not count
- Soft-deleted users counted historically up to deletion date

## Guardrails
- dau_total: should move in same direction (if WAU up but DAU flat, sessions/user changing)
- session_quality_score: should not drop > 5%

## Known caveats
- Pre-2025-09-01 data used `events_v1` schema; comparisons across that date should use `wau_total_v1`
- Mobile events sync once per session — users with offline mode may appear with delay

## Canonical visualization
12-week rolling line chart, weekly snapshots, with prior-year overlay.

## Anti-patterns
- Do not compute WAU separately from `dim_user_session` (different bot logic)
- Do not aggregate WAU across overlapping weeks (double-counts users)

## Related metrics
- dau_total: same definition, 1-day window
- mau_total: same definition, 28-day window
- l5_28: distribution metric showing days-active-in-28

## Change log
- 2026-04-15 — Added bot filter
- 2025-09-01 — Migrated to fct_user_events
- 2024-11-01 — Initial definition
```

---

## Example 2: Activation rate (cohort-based)

```markdown
# Metric Spec: 14-day Activation Rate (activation_14d)

## Identifier
- Canonical name: activation_14d
- Display name: 14-Day Activation Rate
- Owner: @amir.patel (Growth)
- Status: active

## Definition
**Business question:** Of new signups, what share complete the activation action within 14 days?

**Plain English:** Among users who signed up in week W, what % completed `first_purchase` within 14 days of signup?

**Formula:**
```
count(users with first_purchase within 14 days of signup) / count(users signed up in cohort week)
```

**Grain:** Per signup-week cohort.

## Source
- Cohort: `analytics.users.dim_user` filtered to `signup_at`
- Action: `analytics.events.fct_orders` filtered to `is_first_purchase = true`
- Refresh: daily; cohort weeks finalize 14 days after week end

## Canonical SQL
```sql
with cohort as (
    select user_id, date_trunc('week', signup_at) as cohort_week
    from analytics.users.dim_user
    where signup_at >= '2026-01-01'
      and is_internal_user = false
),
activated as (
    select c.user_id
    from cohort c
    join analytics.events.fct_orders o on o.user_id = c.user_id
    where o.is_first_purchase = true
      and o.order_at <= dateadd('day', 14, c.cohort_week + interval '6 days')
)
select
    c.cohort_week,
    count(distinct c.user_id) as cohort_size,
    count(distinct a.user_id) as activated_users,
    count(distinct a.user_id) * 1.0 / nullif(count(distinct c.user_id), 0) as activation_14d
from cohort c
left join activated a using (user_id)
group by c.cohort_week
order by c.cohort_week;
```

## Inclusions / Exclusions
- Includes: all signup channels
- Excludes: cohort weeks that haven't fully aged 14+ days from week end (mark provisional)

## Edge cases
- Users who purchased before signing up (rare): counted from signup time, not purchase time
- Refunded first purchases still count as activation (intent signal)

## Guardrails
- retention_w4: don't optimize activation by attracting users who churn
- gross_margin_per_new_user: don't activate via heavy discounts that erode margin

## Anti-patterns
- Do not present partial-period activation_14d as final
- Do not compare activation_14d to activation_30d as if they're the same metric
```

---

## Example 3: Resolving cross-team disagreement

**User prompt:** "Finance says we did $4.1M last month, but our dashboard says $4.3M. Why?"

**Skill response (debugging walkthrough):**

> Step 1: Pull both queries. Finance is using `gross_revenue` filtered to `recognized_at` (revenue recognition date), our dashboard uses `order_at`. Difference: orders placed late March but recognized in April are in finance's April, our dashboard's March.
>
> Step 2: Pick canonical. For investor reporting and external comms, use finance's definition (recognition basis). For product analytics (did our pricing change affect order behavior?), use order date.
>
> Step 3: Create two specs:
> - `revenue_gross_recognized` (canonical for finance/reporting)
> - `revenue_gross_booked` (canonical for product analytics)
>
> Step 4: Rename our dashboard's metric from "Revenue" to "Booked Revenue (gross)" so the difference is visible to stakeholders.
>
> Step 5: Update both metric specs and link the relationship in "Related metrics."
