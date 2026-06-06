---
name: survival-analysis
description: Runs censoring-aware time-to-event analysis using Kaplan-Meier curves and Cox proportional hazards models. Use when the user mentions survival analysis, time-to-event, time-to-churn, time-to-conversion, hazard ratio, Kaplan-Meier, Cox model, censored data, or duration modeling.
---

# Survival Analysis

## When to use this skill

Use when the outcome is "**how long until X happens?**" and some observations haven't experienced X yet (censored). Triggers:

- "Time to churn / cancel / conversion"
- "Survival curve for…"
- "Hazard ratio of feature X"
- "How long do users stay before churning?"
- "Compare retention across segments over time"

If you only care about *whether* an event happens within a fixed window, use `logistic-regression`. If you need fixed-time-point retention rates without timing, use `cohort-analysis`.

## Why not just use logistic regression?

| Question | Right tool |
|---|---|
| Did the user churn within 90 days? | logistic |
| When did the user churn? Distribution? | survival |
| How does plan tier affect churn timing? | survival |
| Users still active — do we throw them out? | survival (treats as censored, not missing) |

Throwing out censored observations biases logistic regression toward early events.

## Required inputs

| Input | Why it matters |
|---|---|
| Subject ID | One row per subject |
| Duration | Time from start to event OR last observation |
| Event indicator (1/0) | 1 = event happened, 0 = censored (still observed without event) |
| Covariates | Features that may affect timing |
| Start time | When observation begins (often signup_at) |

## Workflow

1. **Define event precisely.** "Churn" must have an exact definition:
   - Subscription cancellation date
   - No-activity threshold (e.g., 30 consecutive inactive days)
   - Account deletion

2. **Define censoring clearly.** A subject is censored if:
   - Still active at the end of the observation window (right censoring — most common)
   - Lost to follow-up (e.g., switched accounts, account suspended for unrelated reason)
   - Did not start before observation window (left truncation)

3. **Build the duration table:** one row per subject with `start, duration, event`.
   ```python
   df = pd.DataFrame({
       "subject_id": ...,
       "duration_days": (event_date - start_date).dt.days,
       "event": did_event.astype(int),
       # ... covariates
   })
   ```

4. **Fit Kaplan-Meier (KM) curves overall and by segment.**
   - Plot survival function S(t) = P(T > t)
   - 95% CI bands (Greenwood formula)
   - Median survival time (if reached)

5. **Compare groups with log-rank test** to check if curves differ significantly.

6. **Fit Cox Proportional Hazards model** for multivariable analysis.
   - Hazard ratios with 95% CIs
   - **Check the PH assumption** (Schoenfeld residuals, proportional hazards plot). If violated for a feature, stratify or include time-interaction term.

7. **Communicate in business language:**
   - "Median time-to-churn is 142 days. Users on annual plans have HR = 0.42, meaning ~58% lower instantaneous churn risk at any given time."
   - Visualize KM curves with confidence bands by segment.

## Output format

```markdown
# Survival Analysis: <event>

## Setup
- Event: <e.g., subscription cancellation>
- Start time: <e.g., signup_at>
- Censoring: subjects still active as of <observation_end_date>
- Sample: N = <total>, events = <X (X%)>
- Duration unit: <days | weeks | months>
- Median follow-up: <D days>

## Kaplan-Meier summary
| Segment | N | Events | Median survival | S(30d) | S(90d) | S(180d) |
|---|---|---|---|---|---|---|
| Overall | 24,800 | 6,420 (26%) | 312 days | 92% | 81% | 71% |
| Monthly plan | 12,400 | 4,810 (39%) | 184 days | 88% | 71% | 58% |
| Annual plan | 12,400 | 1,610 (13%) | not reached | 96% | 91% | 84% |

Log-rank test (monthly vs annual): χ² = 2,143, p < 0.0001 — **significantly different**

## Cox proportional hazards model
| Covariate | HR | 95% CI | p | Notes |
|---|---|---|---|---|
| plan = annual (ref: monthly) | 0.42 | [0.38, 0.46] | < 0.001 | annual reduces hazard by 58% |
| tenure_segment = enterprise | 0.31 | [0.25, 0.39] | < 0.001 | |
| support_tickets_30d | 1.18 | [1.14, 1.22] | < 0.001 | each ticket: +18% hazard |
| has_team_admin | 0.67 | [0.61, 0.73] | < 0.001 | |
| age_days (per 30 days) | 0.94 | [0.93, 0.95] | < 0.001 | older accounts more stable |

Concordance index: 0.74

## Proportional hazards assumption check
- Schoenfeld residuals: <p-value per covariate>
- Covariates violating PH: <list, or "none">
- For violators: <stratified by | time-interacted | accepted with caveat>

## Visualization
- KM curves with 95% CI bands (overall + key segments)
- Hazard ratios with CIs as forest plot
- (Optional) Cumulative incidence functions

## Caveats
- <e.g., observation window 18 months; long-term survival beyond ~500 days extrapolated>
- <e.g., Annual-plan users haven't reached median — estimate uncertain>
- <e.g., Right censoring assumption assumes censoring is independent of churn likelihood; verify>

## Decision implications
- <e.g., shifting customers to annual plans should yield ~50% reduction in long-run churn>
- <e.g., support ticket spike is a strong leading indicator — trigger intervention at 3+ tickets in 30 days>

## Next steps
- <e.g., A/B test annual plan upsell campaign>
- <e.g., build early-warning model using ticket count + tenure>
```

## Validation checks

- [ ] Event definition is exact (date or threshold)
- [ ] Censoring rule documented (and not correlated with event)
- [ ] Duration is non-negative
- [ ] KM curves include CI bands
- [ ] Log-rank test reported when comparing groups
- [ ] Cox model: PH assumption checked
- [ ] Concordance index reported (Cox's analog of AUC, typically 0.6-0.85)

## Edge cases & failure modes

- **Informative censoring**: if subjects with higher churn risk are more likely to be censored (e.g., paused accounts), Cox model is biased. Hard to detect. Investigate the censoring mechanism.
- **Competing risks**: a subject can experience multiple mutually exclusive events (churn vs upgrade). Use competing risk models (Fine-Gray), not standard Cox.
- **PH violation**: a covariate's effect changes over time (e.g., new users have higher early churn). Stratify by that variable or add time-interaction term.
- **Time-varying covariates**: feature values change during the observation period (e.g., support tickets accumulate). Use time-dependent Cox model with long-format data.
- **Left truncation**: subjects only enter observation after some time. Use `entry` parameter in lifelines.
- **Heavy ties** (many events at same time): use Efron or exact tie-breaking, not Breslow.

## Scripts

- `scripts/survival_fit.py` — Fit KM by segment + Cox PH model, output readout.

```bash
python scripts/survival_fit.py \
    --input subjects.csv \
    --duration tenure_days \
    --event churned \
    --segment plan_tier \
    --covariates plan_tier,support_tickets_30d,has_team_admin
```

## Related skills

- `cohort-analysis` — for fixed-time-point retention without censoring complexity
- `logistic-regression` — for binary outcome within a fixed window
- `data-quality-audit` — verify start/end dates and event indicators before fitting
- `causal-inference` — if you need to estimate *intervention* effect on survival
