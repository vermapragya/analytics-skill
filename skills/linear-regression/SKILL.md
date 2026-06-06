---
name: linear-regression
description: Fits, evaluates, and interprets linear regression for continuous outcomes (revenue, session time, NPS scores) with residual diagnostics and assumption checks. Use when the user mentions linear regression, OLS, continuous outcome, "predict <numeric KPI>", coefficient interpretation, R-squared, or regression diagnostics.
---

# Linear Regression

## When to use this skill

Use for **continuous outcome prediction or explanation** where interpretability matters. Triggers:

- "Predict revenue / session time / NPS"
- "What drives <continuous metric>?"
- "Linear regression for…"
- "OLS"
- "Explain the variation in…"

For binary outcomes use `logistic-regression`. For time-to-event use `survival-analysis`. For pure prediction with non-linear effects, fit linear first as baseline, then suggest gradient boosting.

## Required inputs

| Input | Why it matters |
|---|---|
| Continuous target | What you're predicting (numeric, ideally not heavily skewed) |
| Feature set | Predictors |
| Observation grain | Per user / per session / per geography |
| Train/test strategy | Temporal split for production, random for exploratory |
| Goal | Pure prediction, coefficient interpretation, or both? |

## Workflow

1. **Audit the data** (`data-quality-audit` skill).

2. **Inspect the target distribution.**
   ```python
   import matplotlib.pyplot as plt
   df[target].hist(bins=50)
   df[target].describe()
   ```
   - Symmetric, finite variance → OK for OLS
   - Heavily right-skewed (revenue, time-on-page) → consider `log(1 + target)` transformation
   - Heavy-tailed with extreme outliers → robust regression or winsorize

3. **Check for outliers** at p99 and p99.9. Decide:
   - Cap at p99 (winsorize)
   - Drop with documented justification
   - Keep and use robust regression

4. **Verify no leakage** (same checks as logistic-regression).

5. **Split temporally** (or random for exploratory).

6. **Fit baseline OLS** with all features. Use `statsmodels` for coefficient inference, `sklearn` for production fitting.

7. **Check assumptions** (diagnostics matter more than for logistic):
   - **Linearity**: residuals vs predicted should look random
   - **Homoscedasticity**: residual variance constant across predicted values
   - **Normality of residuals**: Q-Q plot
   - **No multicollinearity**: VIF < 5 (warn at 5-10, fail at > 10)
   - **Independence**: no autocorrelation (for time-series)

8. **Evaluate on holdout:**
   - **RMSE** (in original units — interpretable to stakeholders)
   - **MAE** (more robust to outliers)
   - **R²** (variance explained — but easily inflated, don't worship)
   - **Out-of-time R²** is the real test

9. **Interpret coefficients.**
   - Standardized coefficients to compare features
   - Report 95% CIs (statsmodels gives these)
   - Watch for sign flips when adding/removing correlated features (multicollinearity sign)

10. **Write the readout.**

## Output format

```markdown
# Linear Regression: <outcome>

## Setup
- Outcome: <target> (unit: <e.g., dollars per user>)
- Distribution: mean <X>, median <Y>, p99 <Z> (transformation: <none | log(1+y) | winsorize@p99>)
- Observation unit: <user / session / geo>
- Sample: <N_train> train, <N_test> test (split: <temporal at YYYY-MM-DD | random>)
- Features: <N> features

## Performance (test set)
| Metric | Value | Notes |
|---|---|---|
| RMSE | 18.4 | Target std = 27.1 |
| MAE | 12.1 | |
| R² | 0.47 | |
| R² out-of-time | 0.42 | |

## Coefficients (top by |effect|, standardized)
| Feature | β | SE | t | 95% CI | β std | Interpretation |
|---|---|---|---|---|---|---|
| tenure_months | +1.84 | 0.12 | 15.3 | [+1.60, +2.08] | +0.41 | +1 month → +$1.84 revenue |
| has_team_plan | +24.10 | 1.42 | 16.9 | [+21.3, +26.9] | +0.38 | team plan → +$24.10 revenue |
| device_mobile_pct | -0.32 | 0.04 | -8.0 | [-0.40, -0.24] | -0.18 | 1pp more mobile → -$0.32 revenue |
| ... | | | | | | |

## Diagnostics
- Residuals vs predicted: <looks random | shows funnel pattern (heteroscedasticity) | shows curvature (non-linearity)>
- Q-Q plot: <residuals roughly normal | heavy tails>
- VIF: <max VIF = 3.1 (OK) | max VIF = 12.4 (multicollinearity warning)>
- Autocorrelation: <Durbin-Watson = 1.94 (OK)>

## Caveats
- <e.g., predictions outside the training range of feature X are extrapolation; not reliable>
- <e.g., model assumes effects are linear; non-linear effects detected for feature Y>
- <e.g., R² inflated by 0.07 vs out-of-time R²; mild overfitting>

## Next steps
- <e.g., target seasonal effects with interaction terms>
- <e.g., investigate residual cluster around segment Z>
- <e.g., if pure prediction matters, benchmark vs gradient boosting>
```

## Validation checks

- [ ] Target distribution inspected; transformation decision documented
- [ ] Outliers checked and policy stated
- [ ] No leakage in features
- [ ] Residual diagnostics ran (linearity, homoscedasticity, normality)
- [ ] VIF checked for multicollinearity
- [ ] CIs reported alongside coefficients
- [ ] Out-of-time R² compared to in-sample R²

## Edge cases & failure modes

- **Heavy-tailed target (revenue)**: OLS gives undue weight to outliers. Use log-transform or quantile regression.
- **Zero-inflated target**: many zeros + continuous positives (e.g., revenue with many free users). Use two-part model: P(zero) via logistic, then OLS on positive values.
- **Multicollinearity**: coefficients become unstable. Drop one of correlated pair, or use ridge regression.
- **Non-linear relationships**: residuals show U-shape vs predicted. Add polynomial terms or use a tree-based model.
- **Heteroscedasticity**: residuals fan out at higher predicted values. Coefficient SEs are wrong. Use HC3 robust SEs (`cov_type='HC3'` in statsmodels).
- **Time-series autocorrelation**: residuals from consecutive periods correlated. SEs are too small. Use Newey-West SEs.

## Scripts

- `scripts/fit_linear.py` — End-to-end OLS fit + diagnostics + report.

```bash
python scripts/fit_linear.py \
    --input data.csv \
    --target revenue_per_user \
    --features feature_list.txt \
    --transform log1p \
    --split-by month --split-date 2026-03-01
```

## Related skills

- `data-quality-audit` — run before fitting
- `logistic-regression` — binary outcomes
- `causal-inference` — when you need effect estimation, not just association
- `stakeholder-readout` — for packaging the model output
