# Logistic Regression — Examples

## Example 1: Churn prediction

**User prompt:** "Build a churn model for our SaaS product. I have user behavior data with a churn label."

**Skill walkthrough:**

```markdown
# Logistic Regression: 30-day churn prediction

## Setup
- Outcome: churned_30d (1 = user did not log in for 30+ consecutive days after as_of_date)
- Observation unit: user_id snapshotted at as_of_date
- Sample size: 84,200 train (as_of < 2026-02-01), 24,100 test (as_of in Feb 2026)
- Base rate: 8.4% positive class
- Features: 32 (engagement, billing, support, demographic)

## Performance (test set)
| Metric | Value | Notes |
|---|---|---|
| AUC-ROC | 0.812 | Strong |
| AUC-PR | 0.41 | Random baseline = 0.084 (~5× lift) |
| Brier score | 0.064 | |
| Calibration | Well-calibrated up to 0.5, slight overprediction above | See plot |
| Threshold @ 0.25 | Precision 0.38, Recall 0.62, F1 0.47 | Chosen: FN cost 5× FP |

## Top coefficients (standardized, sorted by |effect|)
| Feature | β (std) | Odds Ratio | Interpretation |
|---|---|---|---|
| days_since_last_login | +0.61 | 1.84 | 1σ more days → +84% odds |
| failed_login_attempts_7d | +0.34 | 1.40 | 1σ more failures → +40% odds |
| support_tickets_30d | +0.28 | 1.32 | 1σ more tickets → +32% odds |
| sessions_30d | -0.45 | 0.64 | 1σ more sessions → -36% odds |
| has_team_plan | -0.39 | 0.68 | team plan → -32% odds |
| billing_failures_lt | +0.52 | 1.68 | 1σ more failures → +68% odds |

## Calibration check (deciles of predicted probability)
| Decile | Predicted | Observed | n |
|---|---|---|---|
| 1 | 0.008 | 0.011 | 2,410 |
| 5 | 0.067 | 0.072 | 2,410 |
| 9 | 0.241 | 0.218 | 2,410 |
| 10 | 0.412 | 0.376 | 2,410 |

## Operational impact at threshold 0.25
- ~3,800 users flagged this month
- Precision: 38% (1,444 will actually churn)
- Recall: 62% of churners caught
- If a retention email recovers 12% of contacted churners: expect ~173 retained users

## Caveats
- Trained on data through Feb 2026. Model may degrade if user base demographics shift.
- "support_tickets_30d" requires the support system to be polled in production scoring pipeline.
- Calibration drifted ~3pp between training and test — recalibrate quarterly.

## Next steps
- A/B test retention email on flagged users to measure intervention lift
- Re-train monthly until stable
- Consider gradient boosting once we have ≥ 6 months of stable feature pipelines
```

---

## Example 2: Leakage caught and fixed

**User prompt:** "My churn model has 0.98 AUC. Pretty good?"

**Skill response (process):**

> 0.98 AUC on a churn problem is **almost certainly leakage**. Walking through:
>
> Top coefficients revealed `days_since_last_session` was the dominant feature. But check: when is that feature computed?
>
> If `days_since_last_session` is computed at *prediction time* and a churner has 30+ days since last session by definition, the feature IS the label.
>
> **Fix:** snapshot features at `as_of_date`, not "now." Define:
> - `days_since_last_session_as_of_X` = days between as_of_date and last session before as_of_date
> - Observation window: as_of_date - 90 days to as_of_date - 1 day
> - Outcome window: as_of_date to as_of_date + 30 days
>
> After fix: AUC drops to 0.79. This is the real number.

---

## Example 3: Conversion model for a checkout funnel

**User prompt:** "Predict which users will complete checkout, given their first 5 minutes of behavior."

**Skill walkthrough (key callouts):**

> - Observation unit: session (not user)
> - Cutoff: feature computed in first 5 minutes; outcome = checkout_completed within 1 hour of session start
> - Class balance: 7% positive (mildly imbalanced); use class_weight='balanced'
> - Features: items_viewed, cart_adds, time_on_product_pages, prior_purchases, referrer
> - Top finding: `cart_value` and `prior_purchases` dominate. Without these, AUC is 0.62; with them, 0.78.
> - Recommendation: deploy as a real-time scoring service for cart-abandonment intervention; threshold at p=0.15 sends an in-page nudge.
> - Counter-question for stakeholder: "Are we OK with 12% false-positive rate on the nudge, given it's a low-cost intervention?"
```
