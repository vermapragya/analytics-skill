---
name: logistic-regression
description: Fits, evaluates, and interprets logistic regression for binary outcomes (churn, conversion, fraud, adoption). Use when the user mentions logistic regression, binary outcome, churn modeling, conversion prediction, propensity model, odds ratio, classification, AUC, or asks "what predicts X" where X is yes/no.
---

# Logistic Regression

## When to use this skill

Use for **binary outcome prediction** where interpretability matters as much as accuracy. Triggers:

- "Model churn / conversion / fraud / adoption"
- "Predict probability of X"
- "Build a propensity model"
- "What predicts <binary outcome>?"
- "Logistic regression for…"

For complex non-linear interactions, suggest a tree-based model after fitting logistic as the baseline. For continuous outcomes, use `linear-regression`. For time-to-event, use `survival-analysis`.

## Required inputs

| Input | Why it matters |
|---|---|
| Binary target | What you're predicting (must be 0/1 or boolean) |
| Feature set | Predictors, with clear definitions |
| Observation grain | Per user / per session / per opportunity |
| Time cutoffs | Feature window must end BEFORE outcome window starts (leakage check) |
| Train/test strategy | Temporal split for production models, random split for exploratory |

## Workflow

1. **Audit the data first** (use `data-quality-audit` skill).

2. **Check class balance.**
   ```python
   print(y.value_counts(normalize=True))
   ```
   - Balanced (40-60%): standard logistic
   - Mild imbalance (10-40%): use `class_weight='balanced'` and look at PR-AUC, not ROC-AUC alone
   - Severe (< 5%): consider downsampling, but always evaluate calibration on the original distribution

3. **Verify no leakage.** The most common DS bug. Ask:
   - Is any feature derived from data *after* the prediction time?
   - Is the target ever used to build features?
   - Are there features that are only defined for positives?

4. **Split data temporally.**
   ```python
   train = df[df['as_of_date'] < cutoff]
   test  = df[df['as_of_date'] >= cutoff]
   ```
   Random splits are only acceptable for exploratory analysis.

5. **Fit baseline.** Start with regularized logistic (`LogisticRegression(C=1.0, penalty='l2')` in sklearn).

6. **Evaluate on holdout:**
   - **AUC-ROC** (ranking quality)
   - **AUC-PR** (for imbalanced classes)
   - **Brier score** (calibration)
   - **Calibration curve** (visualize predicted vs observed probability)
   - **Confusion matrix** at the operating threshold

7. **Choose threshold based on business cost.**
   - If false negatives cost 10× false positives → lower threshold
   - Plot precision-recall vs threshold to find the inflection
   - Default to 0.5 only if cost is symmetric (rare in practice)

8. **Interpret coefficients as odds ratios.**
   ```
   odds_ratio = exp(beta)
   "A 1-unit increase in X multiplies the odds of Y by <odds_ratio>"
   ```

9. **Write the readout** with the structure below.

## Output format

```markdown
# Logistic Regression: <outcome>

## Setup
- **Outcome:** <binary_target> (positive class = <description>, base rate = <X%>)
- **Observation unit:** <user_id> as of <as_of_date>
- **Sample size:** <N_train> train, <N_test> test (temporal split at <date>)
- **Features:** <N> features (<categories>)

## Performance (test set)
| Metric | Value | Notes |
|---|---|---|
| AUC-ROC | 0.78 | Solid ranking |
| AUC-PR | 0.34 | Base rate 0.08 (random baseline = 0.08) |
| Brier score | 0.072 | |
| Calibration | well-calibrated below 0.4, slight underprediction above | see plot |
| Threshold @ 0.30 | precision 0.42, recall 0.61, F1 0.50 | chosen for business cost |

## Top coefficients (sorted by absolute effect)
| Feature | Coef (β) | Odds Ratio | Interpretation |
|---|---|---|---|
| days_since_last_login | +0.082 | 1.085 | +1 day → +8.5% odds of churn |
| support_tickets_30d | +0.610 | 1.840 | +1 ticket → +84% odds |
| has_active_subscription | -1.420 | 0.242 | active sub → -76% odds |
| ... | | | |

## Calibration check
<observed vs predicted probability table, by decile>

| Decile | Predicted | Observed | n |
|---|---|---|---|
| 1 (lowest) | 0.012 | 0.014 | 1,240 |
| 5 (middle) | 0.103 | 0.108 | 1,240 |
| 10 (highest) | 0.612 | 0.587 | 1,240 |

## Operational impact at chosen threshold
- Flag rate: <X%> of users
- Precision: <X%> (of flagged, correctly identified)
- Recall: <X%> (of true positives, caught)
- Estimated business impact: <e.g., "If we contact all 5,200 flagged users this month, we expect to retain 460 (lift over no-action: +180 retained)">

## Caveats
- <e.g., model trained on stable period; performance may degrade if user base shifts>
- <e.g., features 1-3 require real-time computation; ensure pipeline supports>
- Calibration may drift; re-evaluate quarterly.

## Next steps
- <e.g., A/B test intervention on flagged users>
- <e.g., monitor model performance over next 30 days>
- <e.g., consider tree-based model if interaction terms become important>
```

## Validation checks

- [ ] No leakage: every feature is provably computed before the outcome window
- [ ] Temporal split used (or justified random split)
- [ ] Calibration checked, not just AUC
- [ ] Threshold chosen based on stated business cost
- [ ] Odds ratios reported (more interpretable than raw β)
- [ ] Operational impact estimated, not just statistical metrics

## Edge cases & failure modes

- **Perfect separation**: one feature perfectly predicts outcome. Coefficient explodes. Usually a leakage bug.
- **Multicollinearity**: correlated features inflate individual coefficient variance. Use VIF check or regularization.
- **Very rare class** (< 1%): AUC-ROC is misleading. Use AUC-PR. Consider gradient boosting instead.
- **Categorical with many levels**: one-hot encoding explodes dimensions. Use target encoding or merge rare categories into "other."
- **Calibration drift**: model AUC stable but threshold-based decisions degrading. Re-calibrate with Platt scaling or isotonic regression every 3-6 months.

## Scripts

- `scripts/fit_logistic.py` — End-to-end fit + evaluate + report from a CSV.

```bash
python scripts/fit_logistic.py \
    --input training_data.csv \
    --target churned \
    --features feature_list.txt \
    --split-by signup_date \
    --split-date 2026-03-01
```

## Related skills

- `data-quality-audit` — always run on inputs first
- `linear-regression` — for continuous outcomes
- `survival-analysis` — when timing matters
- `causal-inference` — if you need to estimate intervention effect, not just predict
- `stakeholder-readout` — for packaging the model output
