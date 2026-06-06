# Causal Inference — Examples

## Example 1: DiD for a feature rollout

**User prompt:** "We rolled out the new dashboard to enterprise customers on March 1. Did it increase their weekly active users?"

**Skill walkthrough:**

```markdown
# Causal Inference: Dashboard rollout → WAU

## Question
Did the new dashboard cause an increase in weekly active users among enterprise customers?

## Why not RCT
Already rolled out to all enterprise customers on 2026-03-01. No control group of enterprise customers without the dashboard.

## Method: Difference-in-Differences
- Treated group: enterprise customers (got the new dashboard)
- Control group: SMB customers (did not get the new dashboard)
- Pre-period: 2026-01-01 to 2026-02-28
- Post-period: 2026-03-01 to 2026-04-15
- Outcome: WAU (weekly active users per account)

## Critical assumption: parallel trends
- Plotted average WAU per account for both segments, weekly, Jan-Feb 2026
- Both trends look roughly linear with similar slope; no obvious divergence pre-rollout
- Pre-trend coefficient (from event study) p=0.31 → assumption defensible

## Estimation
```python
model = smf.ols(
    'wau ~ enterprise * post_rollout + week_fe',
    data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['account_id']})
```

| Coefficient | Estimate | 95% CI | p |
|---|---|---|---|
| enterprise | +18.4 | [+15.2, +21.6] | <0.001 |
| post_rollout | +2.1 | [+0.4, +3.8] | 0.014 |
| **enterprise × post_rollout** | **+8.3** | [+5.1, +11.5] | **<0.001** |

**Effect:** The new dashboard caused an estimated +8.3 WAU per enterprise account (95% CI: +5.1 to +11.5), a +21% lift relative to pre-period enterprise baseline (39 WAU).

## Sensitivity checks
- Event study: pre-period coefficients all close to 0, not significant → parallel trends hold
- Robust to dropping the largest 5% of accounts (effect: +7.9)
- Robust to placebo test: shifting the rollout date to 2026-02-01 (placebo effect: -0.2, p=0.84, as expected)

## Caveats
- SMB customers may not be a perfect control if other product changes happened to one segment but not the other in the post-period. No such changes identified.
- Effect estimate is for the "average enterprise account" — heterogeneity across plans not analyzed.
- Some enterprise users may have heard about the dashboard via marketing before March 1 (anticipation effect would bias estimate upward; likely small).

## Decision implications
The new dashboard increases enterprise WAU by ~21%. If similar effect holds for SMB (untested), recommend rolling out to SMB next. Estimate the value at ~$X/quarter using ARPU × WAU lift.
```

---

## Example 2: PSM for self-selected feature adoption

**User prompt:** "Some users opted into our new beta feature. Compared to similar users who didn't, did they retain better?"

**Skill walkthrough:**

```markdown
# Causal Inference: Beta feature adoption → 90-day retention

## Question
Among users who could have adopted the beta feature, does adoption cause higher 90-day retention?

## Why not RCT
Beta opt-in was self-selected. Can't randomize after the fact.

## Method: Propensity Score Matching (PSM)
- Treated: 4,210 users who opted into beta
- Pool of controls: 38,400 users who were eligible but didn't opt in
- Confounders observed: signup_channel, plan_tier, tenure_at_opt_in, last_30d_sessions, last_30d_purchases, support_tickets_30d

## Critical assumption: no unmeasured confounders
Beta opt-in likely driven by:
- Observable: engagement, plan tier, channel (all in our list)
- **Unobservable**: latent interest, willingness to try new things ← we CAN'T fully adjust for this

This is the main caveat. Effect estimate likely upper bound.

## Procedure
1. Fit propensity model: `P(opted_in) ~ 6 confounders`
2. 1:1 nearest neighbor match with caliper = 0.1 (drop matches outside)
3. Match quality:
   - 4,210 treated → 4,058 matched (152 dropped, no good control)
   - Std mean diff < 0.10 on all confounders after matching ✓
   - Common support: scores overlap [0.05, 0.85] ✓

## Estimated effect (ATT)
| Outcome | Treated | Matched Control | Effect | 95% CI |
|---|---|---|---|---|
| Retained 90d | 72.3% | 68.1% | +4.2pp | [+2.7pp, +5.7pp] |

**Interpretation:** Beta adoption is associated with a +4.2pp higher 90-day retention rate, after adjusting for observable factors. If we believe the no-unmeasured-confounders assumption, this is the causal effect of adoption.

## Sensitivity check (Rosenbaum bounds)
Effect remains significant up to gamma = 1.6. Meaning: an unobserved confounder would need to make treatment 1.6× more likely (controlling for observables) to overturn the result. **Plausible** for "user enthusiasm" → effect is moderately robust but not bulletproof.

## Caveats
- The 4.2pp effect likely includes ~1-2pp from unobserved enthusiasm. True causal effect may be closer to +2-3pp.
- Effect is ATT (effect on the treated). If we ramp beta to all users, effect on non-self-selectors may be smaller.
- 152 treated users with no comparable control are excluded — their effect is unestimable.

## Decision implications
Even taking the lower bound (+2pp), beta adoption appears to causally improve retention. Recommend:
1. Roll out as default for new signups (where self-selection isn't possible) and measure retention as a quasi-experiment.
2. Don't conclude the same effect would hold for all users — the ATT may overstate the population effect.
```

---

## Example 3: When IV is the right call

**User prompt:** "Does receiving a discount email increase purchases? Some users get the email, some don't, but the targeting wasn't random."

**Skill response:**

> Pure observational comparison is biased: users targeted for discount emails were probably already at higher (or lower) purchase intent.
>
> If you had random A/B assignment to RECEIVING the email, that would be the gold standard.
>
> If not, look for a natural instrument:
> - **Email server outage**: some randomly-selected users had their email blocked by their provider. This is a natural instrument for receiving = 0, uncorrelated with the user's purchase intent.
> - **Random emailing schedule**: if emails go out in a randomized order over the day and you can observe time-of-send, the time may instrument for opening.
>
> Without an instrument, the honest answer is: "We can't separate the email's effect from the targeting." Recommend running a hold-out experiment going forward (randomly exclude 5% from emailing) for future estimation.
```
