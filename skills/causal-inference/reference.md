# Causal Inference — Reference

## The fundamental problem

For each unit, we observe outcome under only one treatment status (the "factual"). The counterfactual is missing. Causal inference = estimating the missing counterfactual.

```
Effect on unit i = Y_i(treated) - Y_i(untreated)
We never observe both. Methods estimate the average.
```

## Potential outcomes framework

```
ATE = E[Y(1) - Y(0)]    Average Treatment Effect (population)
ATT = E[Y(1) - Y(0) | T=1]  Effect on the Treated
ATC = E[Y(1) - Y(0) | T=0]  Effect on the Controls (counterfactual)
LATE = ITT / first-stage     Local Average Treatment Effect (IV)
```

PSM/IV estimate ATT or LATE. RCTs estimate ATE.

## DiD math

```
Effect_DiD = (Y_treated_post - Y_treated_pre) - (Y_control_post - Y_control_pre)
```

In regression form:
```
Y = β₀ + β₁·treated + β₂·post + β₃·(treated × post) + ε
```
`β₃` is the DiD estimate.

### Cluster-robust SEs
Standard errors must account for serial correlation within units:
```python
model.fit(cov_type='cluster', cov_kwds={'groups': df['unit_id']})
```

### Event study (dynamic DiD)
Interact treated with each period to see effect over time:
```python
# pseudo
formula = "outcome ~ treated + " + " + ".join([f"C(period)[T.{p}]:treated" for p in periods])
```
- Pre-period coefficients should be ~0 (parallel trends check)
- Post-period coefficients show effect evolution

### Synthetic control method
When you have one treated unit (e.g., one state, one country) and multiple controls:
- Build a synthetic "control" as a weighted combo of donor units that best matches pre-treatment trajectory
- Post-treatment gap = causal effect estimate

## PSM details

### Choosing match method
| Method | When |
|---|---|
| 1:1 nearest neighbor | Default; throws away unmatched controls |
| 1:k nearest neighbor (k=2-5) | Larger sample, slightly more bias |
| Caliper matching | Reject matches farther than threshold (e.g., 0.1 SD) |
| Kernel matching | Smooth weighting instead of discrete match |
| Stratification | Group by propensity quintile, compare within |
| IPTW (weighting) | Use 1/propensity as weight in regression; uses all data |

IPTW is often preferred over discrete matching for unbiased estimation:
```python
df['weight'] = np.where(
    df['treated'] == 1,
    1 / df['propensity'],
    1 / (1 - df['propensity']),
)
# Then weighted regression of outcome on treated + confounders
```

### Balance diagnostics
After matching, every confounder should have **standardized mean difference** < 0.10:
```python
def std_diff(treated_vals, control_vals):
    pooled_std = np.sqrt((treated_vals.var() + control_vals.var()) / 2)
    return (treated_vals.mean() - control_vals.mean()) / pooled_std
```

If any confounder has |std_diff| > 0.10 after matching, the match isn't tight enough — re-specify or try a different method.

### Common support
Plot propensity score distribution for treated vs control. They must overlap. If treated users have propensity 0.7-0.9 and no controls do, you can't estimate the effect for that range.

## IV details

### Two-stage least squares (2SLS)

Stage 1: Regress treatment on instrument(s) + controls:
```
T = α₀ + α₁ Z + α₂ X + u
```

Stage 2: Regress outcome on PREDICTED treatment + controls:
```
Y = β₀ + β₁ T̂ + β₂ X + ε
```

`β₁` is the IV estimate (LATE).

### Validity checks
1. **Relevance**: First-stage F-stat > 10 (rule of thumb). Stock-Yogo critical value > 16.38 for one instrument.
2. **Exclusion**: Z affects Y only through T. Untestable — must defend with theory.
3. **Independence**: Z uncorrelated with unobserved confounders.

### Sargan/Hansen test
For over-identified models (more instruments than treatments): test whether instruments are jointly valid.

## Practical method selection

| You have… | Best method |
|---|---|
| Random assignment to treatment | RCT — A/B test |
| Random assignment to encouragement, with imperfect compliance | IV (intent-to-treat as instrument) |
| Geographic or time-based rollout | DiD or synthetic control |
| User self-selected into feature; rich observable data | PSM / IPTW |
| No clean variation | Don't make causal claims; use correlation + qualitative evidence |

## Sensitivity analysis

Always ask: how strong would an unobserved confounder need to be to overturn the result?

### Rosenbaum bounds (for PSM)
Gamma = how much more likely treatment was for one unit vs another with the same observed covariates due to an unobserved confounder. If your effect survives gamma = 2, the result is robust.

### Oster (2019) bound (for OLS)
Compare R² with and without observables. If coefficient on treatment moves a lot when you add controls, there's likely more bias from unobservables.

## Common mistakes

1. **Controlling for a mediator**: if X causes M causes Y, controlling for M removes the X→Y effect you're trying to estimate.
2. **Including future variables as confounders**: a confounder must be pre-treatment.
3. **Using ATT as if it were ATE**: PSM estimates the effect on the treated, not the whole population.
4. **Reporting OLS as causal**: OLS with controls is correlation unless you can defend ignorability.
5. **Treating DiD as automatic**: parallel trends is testable; test it.
6. **Bad instrument**: if your instrument's exclusion restriction is questionable, IV gives confident-sounding wrong answers.

## When to call it and use a correlational analysis

If none of the methods cleanly apply:
1. Run linear/logistic regression
2. Report associations honestly: "X is associated with +δ in Y, but we cannot establish causation because…"
3. Recommend an experimental design if action depends on causation

This is more honest than dressing up correlation as causation.
