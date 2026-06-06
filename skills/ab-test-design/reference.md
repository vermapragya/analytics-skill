# A/B Test Design — Reference

## Sample size formulas

### Proportion (binary outcome)

For a two-sided test with equal allocation:

```
n_per_arm = ((z_{α/2} + z_{β})² × (p1(1-p1) + p2(1-p2))) / (p1 - p2)²
```

Where:
- `p1` = baseline rate
- `p2` = `p1 + MDE` (absolute) or `p1 × (1 + MDE)` (relative)
- `z_{α/2}` = 1.96 for α=0.05 two-sided
- `z_{β}` = 0.84 for 80% power

### Mean (continuous outcome)

```
n_per_arm = 2 × ((z_{α/2} + z_{β}) × σ / MDE)²
```

Where `σ` is the pooled standard deviation.

### Ratio metric

Use the delta method or bootstrap. See `scripts/sample_size.py` for the delta-method implementation.

## Multiple comparisons

For `k` treatments compared to one control, Bonferroni-correct alpha:

```
α_corrected = α / k
```

This inflates required sample size. Prefer fewer treatments over more.

## CUPED (variance reduction)

CUPED (Controlled-experiment Using Pre-Experiment Data) can reduce required sample size by 30-50% when a pre-period covariate is highly correlated with the outcome.

Adjusted metric:
```
Y_cuped = Y - θ × (X - E[X])
```

Where `θ = cov(X, Y) / var(X)` and `X` is the pre-experiment covariate.

Use when:
- You have ≥ 14 days of pre-experiment data
- Pre-period metric correlates ≥ 0.3 with outcome
- The metric is high-variance (revenue, session length)

## Randomization unit decision tree

```
Is treatment delivered per-user?
├── Yes → user-level (default)
│   └── Are there network effects (marketplace, social)?
│       ├── Yes → cluster randomization (geo, cohort)
│       └── No → user-level OK
└── No (e.g., page-level change)
    └── Session-level or pageview-level
```

## Guardrail thresholds (defaults)

| Guardrail | Default threshold |
|---|---|
| Sample ratio mismatch | χ² p-value > 0.001 |
| Revenue/user | Not down > 2% with 95% CI |
| Error rate | Not up > 0.5pp absolute |
| Page latency p95 | Not up > 100ms |

## Cross-warehouse notes

- **Snowflake**: use `RATIO_TO_REPORT` and `APPROX_PERCENTILE` for fast variance estimation
- **BigQuery**: prefer `APPROX_QUANTILES` and `STDDEV_SAMP`
- **Postgres**: `STDDEV` works; for large tables, sample first via `TABLESAMPLE`

## When NOT to run an A/B test

- Decision is reversible and cheap to undo (just ship it)
- Too few users to reach reasonable runtime (< 30 days)
- Strong network effects make user-level randomization invalid → use `causal-inference`
- The change is required (legal, security, parity) → ship without testing
