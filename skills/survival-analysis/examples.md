# Survival Analysis — Examples

## Example 1: Time to subscription churn

**User prompt:** "Analyze time to cancellation for our subscription product. We want to know what predicts churn and how monthly vs annual plans differ."

**Skill walkthrough:**

```markdown
# Survival Analysis: subscription cancellation

## Setup
- Event: explicit subscription cancellation (`canceled_at IS NOT NULL`)
- Start: `subscription_started_at`
- Censoring: still active as of 2026-04-15
- Sample: 38,400 subscribers, 9,820 cancellations (25.6%)
- Duration unit: days
- Median follow-up: 287 days

## KM summary
| Segment | N | Events | Median survival | S(30d) | S(90d) | S(365d) |
|---|---|---|---|---|---|---|
| All | 38,400 | 9,820 | 412 days | 96% | 87% | 56% |
| Monthly | 22,400 | 7,920 (35%) | 219 days | 93% | 78% | 38% |
| Annual | 16,000 | 1,900 (12%) | not reached | 99% | 97% | 85% |

Log-rank monthly vs annual: χ² = 3,872, p < 0.0001

## Cox PH model
| Covariate | HR | 95% CI | p |
|---|---|---|---|
| plan = annual (ref: monthly) | 0.31 | [0.28, 0.34] | <0.001 |
| support_tickets_30d (per ticket) | 1.22 | [1.18, 1.26] | <0.001 |
| has_team_admin | 0.61 | [0.55, 0.68] | <0.001 |
| billing_failures_lt (per failure) | 1.84 | [1.71, 1.98] | <0.001 |
| acquisition_channel = paid (ref: organic) | 1.48 | [1.36, 1.61] | <0.001 |
| age_days (per 30 days) | 0.92 | [0.91, 0.93] | <0.001 |

Concordance: 0.78

## PH assumption check
- All p-values > 0.05 except `support_tickets_30d` (p = 0.012)
- Time interaction: support_tickets has slightly stronger effect in early periods. Either accept with caveat or refit with `support_tickets × log(t)` interaction.

## Decision implications
1. Annual plans reduce instantaneous churn hazard by ~70% (HR 0.31). Even after accounting for self-selection, this is the strongest lever.
2. Billing failures double the hazard. Improving payment retry logic is high-leverage.
3. Paid-channel users churn 48% faster than organic. Channel quality should be a signup-quality KPI.

## Caveats
- Annual plans haven't reached median — true median is somewhere > observation window
- Cox HR for support tickets is averaged; effect is stronger in first 60 days
- Self-selection: users who choose annual are likely more committed regardless of plan effect. To estimate causal plan effect, use `causal-inference` skill.

## Next steps
- A/B test billing retry strategy on failed-payment users (would expect ~30% hazard reduction)
- Test annual plan discount campaign on monthly cohort
- Build early-warning score: hazard above p90 triggers retention outreach
```

---

## Example 2: Time to first purchase (activation)

**User prompt:** "We define activation as first purchase within 30 days of signup. What does the time-to-activation distribution look like?"

**Skill response:**

> Time to first purchase is the event; "no purchase by end of observation" is censoring.
>
> Useful KM outputs:
> 1. Survival curve = probability of NOT having purchased by time t. Inverse (1 - S(t)) = cumulative activation curve.
> 2. Hazard curve = activation rate per day. Where is the peak? Often day 0-1 (high intent), then drops sharply.
>
> Findings to look for:
> - **Bimodal distribution**: some users activate within hours, others not for weeks. Suggests two segments needing different onboarding.
> - **Cliff at 30 days**: if the user feedback cycle is monthly, activations cluster around payday or invoice date.
> - **Long tail**: if 30% of users still activate after 90 days, your 30-day activation metric is undercounting.
>
> Recommendation: present both 30-day activation rate AND median time-to-activation. The two together tell a richer story than either alone.

---

## Example 3: Time-varying covariate — accumulating support tickets

**User prompt:** "Does the number of support tickets a user files affect churn?"

**Skill response (key callouts):**

> Support tickets accumulate over time, so this is a **time-varying covariate**. Using a static "tickets in last 30 days" as a snapshot at signup biases the estimate.
>
> Correct approach: long-format data with intervals.
>
> Long-format example for user 1:
> | subject_id | start | stop | event | tickets_cum |
> |---|---|---|---|---|
> | 1 | 0 | 30 | 0 | 0 |
> | 1 | 30 | 60 | 0 | 2 |
> | 1 | 60 | 90 | 0 | 4 |
> | 1 | 90 | 105 | 1 | 7 |
>
> Fit with `CoxTimeVaryingFitter`. HR per ticket can be interpreted as "instantaneous churn hazard increases by Xpp for each additional ticket accumulated."
>
> Common finding: HR ~1.15-1.25 per ticket. The effect is real but small per-ticket; large effects come from cumulative 5+ tickets.
```
