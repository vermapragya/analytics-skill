# Metric Definition — Reference

## Common DS metric categories

| Category | Examples | Typical grain |
|---|---|---|
| Volume | Signups, orders, sessions | per period |
| Reach | DAU, MAU, WAU | per period |
| Engagement | Sessions/user, actions/session | per user per period |
| Conversion | Signup→activation rate | per cohort |
| Revenue | GMV, ARPU, MRR | per user per period |
| Retention | D7, W4 retention | per cohort |
| Quality | NPS, CSAT, error rate | per response / per session |

## DAU/WAU/MAU pitfalls

- **DAU**: "users active in a single day". Choose a definition of "active" (any event vs key action).
- **WAU**: "users active in the trailing 7 days". A user counts once even if active all 7 days.
- **MAU**: "users active in the trailing 28 or 30 days" — pre-specify which.

DAU/MAU ratio = engagement quality indicator (closer to 1.0 = more habitual users).

## Stickiness metrics

| Name | Formula |
|---|---|
| DAU/MAU | Daily active / monthly active |
| L7/28 | "L-of-N": # days active in last 28 days, distribution rather than ratio |
| Lx/T | x days active in T days (e.g., L5/7 = "active 5 of last 7 days") |

L-of-N is often more diagnostic than DAU/MAU.

## Revenue metric definitions

| Metric | Definition | Gotchas |
|---|---|---|
| GMV | Gross merchandise value, before refunds/cancellations | Excludes vs includes shipping, tax, fees? |
| Net revenue | GMV - refunds - cancellations | Period of refund recognition? |
| MRR | Monthly recurring revenue from active subscriptions | Annual plans amortized monthly? |
| ARR | MRR × 12 | Includes one-time fees? |
| ARPU | Revenue / active users | Active = paying or all? Period? |
| LTV | Customer lifetime value | Calculation method varies wildly |

Always specify the **revenue recognition rule** (booking vs billing vs cash).

## Cross-team disagreement playbook

When two teams report different numbers for "the same" metric:

1. Pull both queries side by side
2. Identify the first line where they diverge
3. Common divergence points:
   - **Filter on internal users**: one filters, one doesn't
   - **Timezone**: UTC vs PST will shift daily numbers by ~5-15%
   - **Refund treatment**: gross vs net
   - **Deduplication**: count(*) vs count(distinct user_id)
   - **Date boundary**: < vs <= on the end date
4. Pick one as canonical, update both teams' dashboards, deprecate the other

## Guardrail metric recipes

### For engagement metrics
- Quality guardrail: error_rate, p95_latency
- Business guardrail: revenue_per_user
- Reach guardrail: active users (so you don't optimize engagement by shedding users)

### For revenue metrics
- Customer satisfaction (NPS, CSAT)
- Refund rate
- Engagement (so you don't optimize revenue by burning users)

### For conversion metrics
- Downstream retention (don't convert users who churn immediately)
- Lifetime value (don't optimize signup by sacrificing LTV)

## Naming conventions

- snake_case
- prefix by category: `revenue_`, `dau_`, `conversion_`, `retention_`
- include grain: `dau_b2b`, `mrr_total`, `retention_d7`
- avoid generic names: not `users` — `dau_new_signups`

## Metric "versioning"

When definition changes meaningfully:

- Don't silently change. Create v2.
- Run both side-by-side for a transition period (≥ 1 month)
- Migrate dashboards
- Mark v1 deprecated with sunset date
- Update change log

## Tool integration

| Tool | Where the spec should live |
|---|---|
| dbt | As a model description + columns docs |
| Looker | LookML measure description |
| Mode / Hex | Linked README per query |
| Notion / Confluence | Centralized metric registry |

The repo-of-record should be a single source. Sync to BI tools, don't duplicate authoritatively.
