---
name: causal-inference
description: Estimates causal effects when RCTs aren't feasible — using difference-in-differences, propensity score matching, or instrumental variables — with a decision framework for which method fits. Use when the user mentions causal inference, DiD, difference-in-differences, propensity matching, IV, instrumental variable, "estimate the impact of X without an A/B test", quasi-experiment, or natural experiment.
---

# Causal Inference

## When to use this skill

Use when the question is "**what is the causal effect of X on Y**" but a clean A/B test isn't possible. Triggers:

- "Estimate the impact of <feature/policy/launch> without an A/B test"
- "We can't randomize. How do we measure effect?"
- "DiD analysis"
- "Propensity score matching"
- "Instrumental variable"
- "Did the launch of X cause Y to change?"

If a clean A/B test IS possible, use `ab-test-design` + `ab-test-analysis` — they always beat quasi-experimental methods.

If the question is "predict Y" not "what causes Y," use `linear-regression` or `logistic-regression`.

## Decision framework: which method?

Answer these questions in order:

```
1. Is there a clear before/after time and a comparison group not affected by the change?
   YES → Difference-in-Differences (DiD)
   NO  → continue

2. Did some users opt into a feature/treatment based on observable characteristics?
   YES → Propensity Score Matching (PSM) or weighting
   NO  → continue

3. Is there a "lever" that affects treatment but doesn't directly affect outcome?
   YES → Instrumental Variable (IV)
   NO  → none of these will work cleanly; recommend RCT or accept correlational evidence with explicit caveats.
```

## Required inputs

| Input | Why it matters |
|---|---|
| Treatment definition | Who/what gets the intervention |
| Outcome definition | The metric you want to estimate the effect on |
| Pre/post time periods (DiD) | When did the change occur? |
| Comparison/control group | Who isn't treated? |
| Confounders | Variables that affect both treatment and outcome |
| Mechanism story | Why might treatment cause outcome? |

## Method 1: Difference-in-Differences (DiD)

### Setup
- A change happened at a specific time (e.g., new feature rolled out 2026-03-01).
- One group experiences the change; another doesn't (or experiences it later).
- You have pre-period AND post-period data for both groups.

### Assumption (critical): Parallel trends
The treated and control groups would have followed parallel trends in the outcome absent the treatment. Show this by plotting both groups' outcome over time in the pre-period.

### Estimation
```python
import statsmodels.formula.api as smf

# panel data: one row per (unit, period)
model = smf.ols(
    formula='outcome ~ treated * post',
    data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['unit_id']})

# The coefficient on `treated:post` is the DiD estimate
```

### When DiD fails
- Parallel trends violated (treated group was already trending up before treatment)
- Spillover: control group is affected indirectly by treatment
- Confounding shock: another event hit one group at the same time
- Anticipation: treated units changed behavior before the treatment

## Method 2: Propensity Score Matching (PSM)

### Setup
- Some users opted into / received a feature; others didn't.
- The decision was driven by observable factors (not random).
- You want to compare "similar" treated and control users.

### Steps
1. Fit a logistic regression: P(treated = 1 | confounders).
2. Get propensity scores for all users.
3. Match treated users to control users with similar scores.
4. Compare outcomes between matched pairs.

```python
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

# Step 1: fit propensity
p_model = LogisticRegression().fit(df[confounders], df['treated'])
df['propensity'] = p_model.predict_proba(df[confounders])[:, 1]

# Step 2: 1:1 match (treated → nearest control)
treated = df[df['treated'] == 1]
control = df[df['treated'] == 0]
nn = NearestNeighbors(n_neighbors=1).fit(control[['propensity']])
distances, indices = nn.kneighbors(treated[['propensity']])
matched_control = control.iloc[indices.flatten()].reset_index(drop=True)

# Step 3: compute ATT (average treatment effect on the treated)
att = (treated['outcome'].values - matched_control['outcome'].values).mean()
```

### Assumption (critical): No unmeasured confounders
Anything affecting both treatment selection AND outcome must be in the confounders list. This is unfalsifiable — you must defend it with domain knowledge.

### Diagnostics
- **Common support**: propensity score distributions overlap between treated and control. If they don't, can't match.
- **Balance check**: after matching, treated and control should have similar means on all confounders.

## Method 3: Instrumental Variable (IV)

### Setup
- Treatment is endogenous (correlated with unobserved confounders).
- There exists an "instrument" Z that:
  1. Affects treatment (relevance)
  2. Doesn't directly affect outcome except through treatment (exclusion)
  3. Isn't correlated with unobserved confounders

Examples:
- Random assignment to receiving an offer (instrument) → actually using it (treatment) → outcome
- Distance from store (instrument) → store usage (treatment) → spend (outcome)
- Encouragement design experiments

### Two-stage least squares
```python
import statsmodels.formula.api as smf
from linearmodels.iv import IV2SLS

# Treatment = f(instrument, controls)
# Outcome = f(predicted_treatment, controls)
model = IV2SLS.from_formula(
    'outcome ~ 1 + control_x + [treatment ~ instrument]',
    data=df
).fit()
```

### Why IV is hard
- Finding a valid instrument is rare — exclusion restriction is unfalsifiable.
- Weak instruments (low correlation with treatment) inflate SEs and bias estimates.
- Estimates apply only to "compliers" — users who change treatment status because of the instrument.

## Workflow (any method)

1. **Force the causal question.** "What is the effect of X on Y?" — not "is X associated with Y."

2. **Argue for a method using the decision framework** above. State which method, why, and what assumption is being made.

3. **Show the data structure.** Pre/post + control? Selection on observables? Instrument?

4. **Run the method.**

5. **Run sensitivity checks:**
   - DiD: plot parallel trends pre-treatment
   - PSM: balance table + common support
   - IV: first-stage F-statistic > 10

6. **Compute the effect with CI.** Cluster errors at the appropriate level.

7. **State counterfactual clearly.**
   - DiD: "Had the policy not been implemented, treated group would have moved X% instead of X+δ%"
   - PSM: "If untreated users had been treated, their outcome would have improved by δ"
   - IV: "For compliers (those induced by the instrument), the effect is δ"

8. **Write the readout** with explicit caveats about what this evidence can and cannot support.

## Output format

```markdown
# Causal Inference: <treatment> → <outcome>

## Question
What is the causal effect of <treatment> on <outcome>?

## Why not a randomized experiment?
<e.g., feature is already launched, can't randomize at this point>
<e.g., regulatory constraint>
<e.g., ethical reason>

## Method: <DiD | PSM | IV>
- **Rationale:** <why this method fits this question>
- **Critical assumption:** <parallel trends | no unmeasured confounders | exclusion restriction>
- **Defense of assumption:** <evidence and domain reasoning>

## Setup
- Treatment: <definition + when>
- Outcome: <definition + grain>
- Comparison group: <who, why valid>
- Sample: N treated, N control
- Confounders adjusted for: <list>

## Estimated effect
- **Point estimate:** <δ> (units: <e.g., $ per user>)
- **95% CI:** [<low>, <high>]
- **Interpretation:** <plain English what this means>

## Sensitivity checks
- <parallel trends plot — pre-trends look parallel>
- <propensity balance table — covariates balanced after match>
- <first-stage F-stat > 10 for IV>
- <robust to alternative specifications?>

## Caveats
- <causal claim limited to ...>
- <effect estimate applies to ...>
- <what could overturn this finding>

## Decision implications
- <recommendation based on effect size and uncertainty>
```

## Validation checks

- [ ] Method choice is justified using the decision framework
- [ ] Critical assumption is named and defended
- [ ] Sensitivity check ran and is reported
- [ ] CI reported, not just point estimate
- [ ] Counterfactual stated in plain English
- [ ] Caveats include what the evidence can NOT support

## Edge cases & failure modes

- **DiD with non-parallel pre-trends**: don't use DiD. Try synthetic control method or accept evidence is weak.
- **PSM with poor common support**: large treated regions have no comparable controls. Don't match those; report effect for the overlapping region only.
- **IV with weak instrument**: F-stat < 10 → IV estimates are biased toward OLS, with inflated SEs. Don't use the instrument.
- **Confounders that change WITH treatment**: don't include as covariates (they're mediators). Including them removes the effect you're trying to measure.
- **Treatment effect heterogeneity**: average effects may hide important variation. Report by subgroup if pre-specified.
- **External validity**: effect estimated on observed population may not generalize. Note explicitly.

## Scripts

- `scripts/did.py` — Difference-in-differences with cluster-robust SEs.
- `scripts/psm.py` — Propensity score matching with balance diagnostics.

## Related skills

- `ab-test-design` / `ab-test-analysis` — gold standard; use whenever feasible
- `linear-regression` — non-causal modeling
- `logistic-regression` — propensity scoring underlies PSM
- `stakeholder-readout` — package the result with clear caveats
