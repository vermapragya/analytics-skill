# Linear Regression — Examples

## Example 1: Revenue per user (with log transform)

**User prompt:** "What drives revenue per user in our SaaS product?"

**Skill walkthrough:**

```markdown
# Linear Regression: monthly revenue per user (log-transformed)

## Setup
- Outcome: log(1 + revenue_usd) — raw was heavy right-skewed (median $14, p99 $890)
- Observation unit: user × month
- Sample: 184,500 user-months train, 46,200 test (temporal split 2026-03-01)
- Features: 18 (tenure, plan, engagement, demographic)

## Performance (test set, back-transformed)
| Metric | Value | Notes |
|---|---|---|
| RMSE | $42 | (vs naive baseline mean: $68) |
| MAE | $18 | |
| R² (log scale) | 0.51 | |
| R² out-of-time (log) | 0.46 | mild overfitting |

## Coefficients (sorted by |β std|)
| Feature | β | 95% CI | β std | Interpretation |
|---|---|---|---|---|
| has_team_plan | +1.21 | [+1.18, +1.24] | +0.44 | team plan → +235% revenue (back-transformed) |
| tenure_months | +0.043 | [+0.041, +0.045] | +0.31 | +1 month → +4.4% revenue |
| sessions_30d | +0.018 | [+0.016, +0.020] | +0.22 | +1 session → +1.8% revenue |
| is_self_serve | -0.62 | [-0.65, -0.59] | -0.18 | self-serve → -46% revenue |
| device_mobile_pct | -0.008 | [-0.009, -0.007] | -0.11 | +1pp mobile → -0.8% revenue |

## Diagnostics
- Residuals vs fitted: random scatter, no funnel or curvature ✓
- Q-Q: residuals roughly normal, slight heavy tails (OK for n > 100k)
- VIF: max VIF = 4.2 on tenure_months ↔ days_since_signup (correlated, expected) — OK
- Durbin-Watson: 1.97 — no autocorrelation

## Caveats
- log(1 + revenue) transform: predictions reported on original scale via exp(ŷ) - 1
- R² of 0.51 is on log scale; original-scale R² is lower due to back-transform variance
- Self-serve coefficient is large but interpretable: self-serve users skip enterprise upgrades
- Model trained on 2025-2026 data; predictions for new market segments are extrapolation

## Next steps
- Test interaction: has_team_plan × tenure_months (do team plans compound?)
- Re-fit quarterly
- If prediction (not explanation) is the goal: benchmark vs gradient boosting
```

---

## Example 2: Session duration with outliers

**User prompt:** "Model session duration."

**Skill response (key callouts):**

> Session duration is **extremely right-skewed**: median 4 min, p99 220 min, max 1,400 min (someone left a tab open).
>
> Three options:
> 1. **Winsorize at p99**: cap at 220 min before fitting. Loses tail info but preserves linear assumptions.
> 2. **Log-transform**: `log(1 + duration)`. Coefficients interpret as percent change.
> 3. **Quantile regression** (median, p25, p75): more robust, multiple percentiles tell a richer story.
>
> Default recommendation: (2) log-transform for interpretability, (3) median quantile regression as supplementary view.
>
> WARNING: do not fit raw OLS to session duration. The 1,400-min outlier has 350× the leverage of a typical session.

---

## Example 3: Multicollinearity caught

**User prompt:** "I added 5 new features and now the coefficient on `tenure_months` flipped from positive to negative. What happened?"

**Skill response:**

> Sign flip on adding correlated features is the textbook symptom of multicollinearity. Investigation:
>
> 1. Compute VIF for all features
> 2. The new features likely include `days_since_signup`, `lifetime_sessions`, `lifetime_orders` — all heavily correlated with `tenure_months`
>
> When VIF on `tenure_months` exceeds 10, OLS can't reliably attribute variance and the coefficient becomes unstable.
>
> Fixes:
> - Keep the one with strongest theoretical link to outcome (probably `tenure_months`), drop the others
> - Or use ridge regression which handles correlated features
> - Or combine: define `user_maturity_score = (tenure_months + lifetime_sessions/30 + lifetime_orders/3) / 3` and use that
>
> The pre-flip coefficient (positive) is the credible one. The post-flip negative is multicollinearity noise.
```
