# Logistic Regression — Reference

## The model

```
P(Y=1 | X) = 1 / (1 + exp(-(β₀ + β₁X₁ + ... + βₖXₖ)))

log(odds) = β₀ + β₁X₁ + ... + βₖXₖ

odds_ratio(Xⱼ) = exp(βⱼ)
```

## Choosing regularization

| Penalty | When | Effect |
|---|---|---|
| L2 (`penalty='l2'`) | Default | Shrinks all coefficients smoothly |
| L1 (`penalty='l1'`) | High-dim, want feature selection | Drives some coefficients to zero |
| Elastic Net | Mix of both | Balance |
| None | Rare, only for ≤ 5 features | High variance |

`C` is the **inverse** of regularization strength. Larger C = less regularization. Default sklearn `C=1.0` is reasonable; tune with cross-validation if performance matters.

## Class imbalance strategies

| Approach | Pros | Cons |
|---|---|---|
| `class_weight='balanced'` | Simple, no data manipulation | Coefficients are weighted-loss optimized |
| Downsample majority | Faster training | Throws away data; calibration suffers |
| Upsample minority (SMOTE) | Preserves data | Synthetic samples can mislead |
| Threshold adjustment | No model change | Doesn't help underfit minority class |

**Default recommendation:** `class_weight='balanced'` + threshold tuned to business cost. Re-calibrate after.

## Calibration

A model is well-calibrated if, among predictions of probability `p`, the observed positive rate is also `p`.

### Diagnose with reliability plot
```python
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10)
plt.plot(prob_pred, prob_true, marker='o')
plt.plot([0, 1], [0, 1], '--')  # perfect calibration
```

### Fix miscalibration
```python
from sklearn.calibration import CalibratedClassifierCV

calibrated = CalibratedClassifierCV(base_estimator=model, method='isotonic', cv='prefit')
calibrated.fit(X_calibration, y_calibration)
```

`'isotonic'` for monotonic miscalibration; `'sigmoid'` (Platt) for small samples.

## Feature engineering for logistic regression

### Numeric features
- **Standardize** if comparing coefficients across features (sklearn: `StandardScaler`)
- **Log-transform** heavy-tailed features (revenue, counts)
- **Cap outliers** at 99th percentile

### Categorical features
- One-hot for low-cardinality (≤ 10 levels)
- Target encoding for high-cardinality (use with cross-validation to avoid leakage)
- Merge rare levels (< 1% of data) into "other"

### Interactions
- Logistic doesn't capture interactions automatically
- Add explicit interaction terms (`X1 * X2`) when domain knowledge suggests it
- If you need many interactions, consider gradient boosting

### Time features
- Days since last X (decay)
- Count of X in last N days
- Day-of-week / month / hour as categoricals (one-hot or cyclic)

## Leakage detection

Common leakage patterns:

| Pattern | Example | Fix |
|---|---|---|
| Future feature | "Lifetime value" used to predict month-1 churn | Use only features available at prediction time |
| Target proxy | "Number of customer support tickets after churn" | Filter to events before `as_of_date` |
| Conditional feature | "Days until cancellation" only defined for churned users | Replace with bounded "days since signup" |
| Lookup table refresh | Static "user_segment" recomputed monthly using outcome | Snapshot features at `as_of_date` |

**Sanity check:** if test AUC > 0.95 on a non-trivial problem, suspect leakage.

## Threshold selection

```python
from sklearn.metrics import precision_recall_curve

precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
f1 = 2 * precision * recall / (precision + recall + 1e-10)
best_idx = f1.argmax()
threshold = thresholds[best_idx]
```

For **business cost** optimization:
```python
# False negative costs 10x false positive
expected_cost = fn_count * 10 + fp_count * 1
# Find threshold minimizing expected cost
```

## Interpreting coefficients

### Odds ratio
```
exp(0.5) = 1.65  →  1-unit increase → +65% odds
exp(-0.5) = 0.61 →  1-unit increase → -39% odds
```

### Standardized coefficients
For comparing feature importance:
```python
from sklearn.preprocessing import StandardScaler
X_std = StandardScaler().fit_transform(X)
# Coefficients of model fit on X_std are directly comparable
```

### Marginal effects (alternative to odds)
For binary X: `P(Y=1 | X=1) - P(Y=1 | X=0)` is the absolute change in probability.

## Cross-validation strategy

| Use case | Strategy |
|---|---|
| Exploratory, IID | Random 5-fold |
| Production model | Temporal: train on past, test on future |
| Imbalanced | Stratified k-fold |
| Grouped data (users w/ many sessions) | GroupKFold by user |

## sklearn vs statsmodels

| Need | Use |
|---|---|
| Production model | sklearn (`LogisticRegression`) |
| Coefficient confidence intervals + p-values | statsmodels (`Logit`) |
| Robust standard errors | statsmodels with `cov_type='HC3'` |
| Quick fitting | sklearn |
| Comprehensive output table | statsmodels |
