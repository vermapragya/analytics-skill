# Linear Regression — Reference

## The model

```
y = β₀ + β₁X₁ + ... + βₖXₖ + ε,   ε ~ N(0, σ²)
```

OLS minimizes Σ(yᵢ - ŷᵢ)².

## Assumptions (in order of importance)

1. **Linearity** — relationship between Xᵢ and y is linear (in parameters)
2. **No leakage** — features computed before outcome
3. **No perfect multicollinearity** — features not perfect linear combos of each other
4. **Independence of errors** — ε independent across observations (matters most for time-series)
5. **Homoscedasticity** — Var(ε) constant across X (matters for standard errors, not coefficients)
6. **Normality of errors** — ε ~ Normal (matters for small samples; n > 100 → CLT helps)

## Diagnostic plots

```python
import matplotlib.pyplot as plt
import statsmodels.api as sm

# Residuals vs fitted
plt.scatter(model.fittedvalues, model.resid)
plt.axhline(0, color='red')

# Q-Q plot
sm.qqplot(model.resid, line='45')

# Residuals vs each feature (find non-linearity)
for col in X.columns:
    plt.scatter(X[col], model.resid)
    plt.title(col)
    plt.show()
```

## Transformations

| Issue | Fix |
|---|---|
| Right-skewed target | `log(1 + y)` |
| Right-skewed feature | `log(1 + x)` |
| Outlier-driven target | Winsorize at p99 or quantile regression |
| Curvilinear feature | Add `x²` term or use spline |
| Mixed categorical-numeric | One-hot encoding |

When using `log(1 + y)`:
- Coefficients interpret as **percent change** in y per unit X
- Predictions must be back-transformed: `exp(ŷ) - 1`
- RMSE on log scale is not in original units — back-transform and recompute

## Multicollinearity

### Variance Inflation Factor (VIF)
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif = pd.DataFrame()
vif["feature"] = X.columns
vif["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
```

| VIF | Severity |
|---|---|
| < 5 | OK |
| 5-10 | Warning |
| > 10 | Problem — drop or combine features |

### Symptoms of multicollinearity
- Coefficient sign flips when adding/removing features
- Wide confidence intervals on individual coefficients
- Joint F-test significant, individual t-tests not

### Fixes
- Drop one of correlated pair
- Combine features (e.g., total = a + b instead of a, b)
- Use ridge regression (`Ridge(alpha=...)`)
- Use PCA for dimension reduction

## Robust standard errors

When residuals are heteroscedastic:

```python
import statsmodels.api as sm

model = sm.OLS(y, sm.add_constant(X)).fit(cov_type='HC3')
```

- `HC0`-`HC3` for heteroscedasticity
- `HAC` for autocorrelation (time-series): `cov_type='HAC', cov_kwds={'maxlags':4}`
- `cluster` for clustered errors: `cov_type='cluster', cov_kwds={'groups': cluster_ids}`

## Coefficient interpretation cheat sheet

| Form | Interpretation of β |
|---|---|
| `y = α + βX` | +1 unit X → +β units y |
| `log(y) = α + βX` | +1 unit X → +100β% in y (approx for small β) |
| `y = α + β log(X)` | +1% X → +β/100 units y |
| `log(y) = α + β log(X)` | +1% X → +β% in y (elasticity) |
| Standardized | +1 SD X → +β SD y |
| Dummy (0/1) | Switch from 0 to 1 → +β units y |

## R² gotchas

- **Inflates with more features**, even useless ones
- **Adjusted R²** penalizes feature count: `1 - (1-R²)(n-1)/(n-k-1)`
- **High R² doesn't imply causal model** — could be all confounding
- **Low R² isn't always bad** — for explanation, even R² = 0.10 can find important drivers
- **Out-of-sample R²** is the only honest measure for prediction quality

## Regularization

| Method | When | Effect |
|---|---|---|
| OLS | Few features, interpretation matters | No shrinkage |
| Ridge (`L2`) | Multicollinearity, prediction matters | Shrinks toward zero |
| Lasso (`L1`) | Many features, want sparsity | Drives some to zero |
| Elastic Net | Mix | Balance |

For pure interpretation: OLS.  
For prediction with many correlated features: Ridge.  
For feature selection: Lasso.

## Cross-validation strategies

```python
from sklearn.model_selection import cross_val_score, TimeSeriesSplit

# IID
cv = 5

# Time series
cv = TimeSeriesSplit(n_splits=5)

scores = cross_val_score(model, X, y, cv=cv, scoring='neg_root_mean_squared_error')
```

## When to use what library

| Need | Tool |
|---|---|
| Comprehensive output table (β, SE, t, p, CI, R²) | statsmodels `OLS` |
| Production model | sklearn `LinearRegression` |
| Regularization | sklearn `Ridge`, `Lasso`, `ElasticNet` |
| Quantile regression | statsmodels `QuantReg` |
| GLM (Poisson, gamma) | statsmodels `GLM` |

## Bayesian alternative

For small samples, regulated by prior beliefs, or when uncertainty quantification matters more than point estimates: use a Bayesian linear model (PyMC, bambi). Outside this skill's scope; reach for it when:
- N < 100
- Need posterior distributions, not just point + CI
- Multilevel structure (users within accounts within regions)
