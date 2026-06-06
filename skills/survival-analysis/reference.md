# Survival Analysis — Reference

## Core concepts

### Survival function
```
S(t) = P(T > t)
```
Probability a subject "survives" (no event) beyond time t.

### Hazard function
```
h(t) = lim_{Δt→0} P(t ≤ T < t + Δt | T ≥ t) / Δt
```
Instantaneous event rate at time t, conditional on survival to t.

### Hazard ratio
```
HR(X) = h(t | X = x+1) / h(t | X = x) = exp(β)
```
- HR = 1 → no effect
- HR > 1 → increased risk (faster event)
- HR < 1 → reduced risk (slower / less event)

## Kaplan-Meier estimator

```
S(t) = ∏_{t_i ≤ t} (1 - d_i / n_i)
```

Where at each event time `t_i`:
- `d_i` = number of events
- `n_i` = number at risk

Confidence interval via Greenwood's formula.

## Censoring types

| Type | Description |
|---|---|
| Right censoring | Subject still at risk at end of observation (most common) |
| Left censoring | Event happened before observation began (rare; need different method) |
| Interval censoring | Event happened between two known times, exact time unknown |
| Left truncation | Subject entered observation after start (delayed entry) |

For most product DS work: right censoring + occasional left truncation.

## Log-rank test

Non-parametric test for whether two or more survival curves differ:
```
χ² = Σ (O - E)² / Var
```
Where O is observed events in group and E is expected under null of no difference.

```python
from lifelines.statistics import logrank_test
result = logrank_test(durations_A, durations_B, event_A, event_B)
print(result.p_value)
```

## Cox PH model

```
h(t | X) = h_0(t) × exp(β₁X₁ + ... + βₖXₖ)
```

Key property: hazard ratios are **constant over time** (the PH assumption).

### Fitting with lifelines

```python
from lifelines import CoxPHFitter

cph = CoxPHFitter(penalizer=0.01)
cph.fit(df, duration_col='duration', event_col='event', formula='plan + tenure + tickets')
cph.print_summary()
```

### Checking PH assumption

```python
cph.check_assumptions(df, p_value_threshold=0.05, show_plots=True)
```

Or examine Schoenfeld residuals — if they have a time trend for a covariate, that covariate violates PH.

### Fixing PH violations

| Issue | Fix |
|---|---|
| Covariate effect declines over time | Add `covariate * log(time)` interaction |
| Covariate effect is categorical and shifts | Stratify by covariate (no longer get HR for it) |
| Generally complex non-PH | Use accelerated failure time (AFT) model instead |

```python
# Stratification
cph.fit(df, duration_col='duration', event_col='event',
        formula='tenure + tickets', strata=['plan'])

# Time interaction (requires long-format data)
df_long = to_long_format(df, duration_col='duration')
df_long['tickets_x_log_t'] = df_long['tickets'] * np.log(df_long['stop'])
```

## Concordance index (C-index)

Survival analog of AUC. Probability that for a random pair of subjects, the one with higher predicted hazard had the earlier event.

- 0.5 = random
- 0.7-0.8 = good
- > 0.85 = suspect (check for leakage)

## Visualizations

### KM curves
```python
from lifelines import KaplanMeierFitter
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
for segment, group_df in df.groupby('plan'):
    kmf = KaplanMeierFitter()
    kmf.fit(group_df['duration'], group_df['event'], label=segment)
    kmf.plot_survival_function(ax=ax, ci_show=True)
plt.ylabel("S(t)")
plt.xlabel("Days since signup")
```

### Hazard ratio forest plot
```python
cph.plot()  # built-in forest plot of HRs with CIs
```

## Time-varying covariates

When a covariate changes during observation (e.g., support ticket count grows), use long-format data:

| subject_id | start | stop | event | tickets |
|---|---|---|---|---|
| 1 | 0 | 30 | 0 | 0 |
| 1 | 30 | 60 | 0 | 2 |
| 1 | 60 | 90 | 1 | 5 |
| 2 | 0 | 45 | 0 | 1 |
| ... | | | | |

```python
from lifelines import CoxTimeVaryingFitter

ctv = CoxTimeVaryingFitter()
ctv.fit(df_long, id_col='subject_id', event_col='event',
        start_col='start', stop_col='stop', formula='tickets + tenure')
```

## Competing risks

When events are mutually exclusive (churn vs upgrade), standard Cox treats one event as "censoring" the other, which biases estimates.

Use Fine-Gray subdistribution hazard model:
```python
from lifelines import AalenJohansenFitter
# or use statsmodels / R's `cmprsk` for full Fine-Gray
```

## Parametric alternatives

| Model | When |
|---|---|
| Cox PH | Default. Non-parametric baseline hazard. |
| Weibull AFT | Parametric. Easier extrapolation beyond observed time. |
| Log-normal AFT | When time-to-event is log-normally distributed. |
| Exponential | Constant hazard (rarely realistic). |

```python
from lifelines import WeibullAFTFitter
aft = WeibullAFTFitter()
aft.fit(df, duration_col='duration', event_col='event', formula='plan + tenure')
```

## Common product DS questions

| Question | Approach |
|---|---|
| When do users churn? | KM curve + median survival |
| What factors predict early churn? | Cox PH |
| Are annual plans stickier than monthly? | KM by plan + log-rank |
| Does intervention X delay churn? | Cox with intervention as covariate (causal: see `causal-inference`) |
| When do users do their second purchase? | KM with second purchase as event |
| How long does activation take? | KM with activation as event |

## Lifelines vs statsmodels

| Need | Tool |
|---|---|
| KM, Cox PH, AFT, log-rank | `lifelines` (recommended) |
| Cox PH with cluster errors | `statsmodels.duration.hazard_regression` |
| Parametric AFT, complex models | `statsmodels` or R |
