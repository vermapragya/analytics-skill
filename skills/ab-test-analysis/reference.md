# A/B Test Analysis — Reference

## Sample Ratio Mismatch (SRM)

A χ² goodness-of-fit test on observed vs expected variant counts.

```
χ² = Σ (observed - expected)² / expected
```

With 1 degree of freedom (for 2 variants), the critical value at p=0.001 is **10.83**.

If χ² > 10.83 (or equivalently p < 0.001), assignment is broken. Common causes:
- Bot filtering applied unevenly
- Variant assignment cached for some users but not others
- Trigger condition differs between variants
- Logging dropped events for one variant

**Do not analyze the primary metric if SRM fails.** Fix the assignment problem first.

## Confidence intervals

### Proportion (Wilson interval, more robust than normal)

```
center = (p + z²/2n) / (1 + z²/n)
half_width = (z × sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)
CI = [center - half_width, center + half_width]
```

### Difference in proportions

```
SE = sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)
CI = (p1 - p2) ± z × SE
```

### Difference in means (Welch's)

```
SE = sqrt(s1²/n1 + s2²/n2)
df = (s1²/n1 + s2²/n2)² / ((s1²/n1)²/(n1-1) + (s2²/n2)²/(n2-1))
CI = (x1 - x2) ± t_{df,α/2} × SE
```

### Ratio metric (delta method)

For R = X / Y:

```
SE(R) ≈ R × sqrt(Var(X)/X² + Var(Y)/Y² - 2 Cov(X,Y)/(XY))
```

Or use bootstrap (more robust for small samples).

## Bootstrap (general purpose)

```python
import numpy as np

def bootstrap_ci(data1, data2, statistic_fn, n_iter=10000, alpha=0.05):
    diffs = []
    for _ in range(n_iter):
        s1 = np.random.choice(data1, size=len(data1), replace=True)
        s2 = np.random.choice(data2, size=len(data2), replace=True)
        diffs.append(statistic_fn(s2) - statistic_fn(s1))
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)
```

## Winsorization for heavy-tailed metrics

```python
def winsorize(series, lower_pct=0.01, upper_pct=0.99):
    lo = series.quantile(lower_pct)
    hi = series.quantile(upper_pct)
    return series.clip(lower=lo, upper=hi)
```

Apply consistently across variants. Pre-register the percentiles.

## CUPED variance reduction

```python
def cuped_adjust(y, x):
    """y = outcome, x = pre-period covariate"""
    theta = np.cov(x, y)[0, 1] / np.var(x)
    return y - theta * (x - np.mean(x))
```

Apply to both variants before computing means/CIs. Reduces variance proportional to correlation² between `x` and `y`.

## Subgroup analysis rules

1. **Only analyze pre-specified subgroups.** Post-hoc subgroup mining inflates false positives.
2. **Apply Bonferroni correction** across subgroups.
3. **Report all pre-specified subgroups**, not just the significant ones (avoids cherry-picking).
4. If you find an interesting post-hoc subgroup, mark it as **hypothesis-generating** and require a follow-up experiment to confirm.

## Multiple metric correction

For K primary metrics:

```
α_corrected = α / K   (Bonferroni — conservative)
α_corrected via Benjamini-Hochberg (FDR — less conservative)
```

Prefer single primary metric with secondaries clearly labeled.

## Cross-warehouse SQL

### Variant counts (Snowflake)

```sql
select
    variant,
    count(distinct user_id) as users,
    count(distinct user_id) * 1.0
        / sum(count(distinct user_id)) over () as share
from experiment_exposures
where experiment_id = 'exp_123'
group by variant;
```

### Primary metric (proportion)

```sql
with exposures as (
    select user_id, variant, min(exposed_at) as first_exposure
    from experiment_exposures
    where experiment_id = 'exp_123'
    group by user_id, variant
),
conversions as (
    select user_id, max(converted) as converted
    from conversion_events
    where event_at <= dateadd('day', 7, first_exposure)
    group by user_id
)
select
    e.variant,
    count(distinct e.user_id) as n,
    sum(coalesce(c.converted, 0)) as conversions,
    sum(coalesce(c.converted, 0)) * 1.0 / count(distinct e.user_id) as rate
from exposures e
left join conversions c using (user_id)
group by e.variant;
```
