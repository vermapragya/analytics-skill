# A/B Test Analysis — Examples

## Example 1: Clear winner with all guardrails passing

**User prompt:** "Analyze our checkout button color test. Treatment was green vs control blue. Data is in `/data/exp_412.csv`."

**Skill output (abbreviated):**

```markdown
# Experiment Readout: Checkout button color (exp_412)

## TL;DR
**Recommendation: Ship**

Checkout completion rate increased from 12.0% to 12.9% (+0.9pp, [+0.4pp, +1.4pp] 95% CI, p=0.0008) over 14 days.

## Sample Ratio Mismatch
| Variant | Expected | Observed | Delta |
|---|---|---|---|
| Control | 50.0% | 50.1% | +0.1pp |
| Treatment | 50.0% | 49.9% | -0.1pp |

χ² p-value: 0.62 — PASS

## Primary metric: checkout_completion_rate
| Variant | N | Value | 95% CI |
|---|---|---|---|
| Control | 16,540 | 12.0% | [11.5%, 12.5%] |
| Treatment | 16,488 | 12.9% | [12.4%, 13.4%] |

- Absolute lift: +0.9pp [+0.4pp, +1.4pp]
- Relative lift: +7.5% [+3.3%, +11.7%]
- Test: two-proportion z-test, p = 0.0008

## Guardrails
| Metric | Threshold | Result | Status |
|---|---|---|---|
| revenue_per_user | not down > 2% | +1.1% [-0.4%, +2.6%] | PASS |
| page_error_rate | not up > 0.5pp | +0.1pp [-0.1pp, +0.3pp] | PASS |
| p95_latency_ms | not up > 100ms | -8ms [-22ms, +6ms] | PASS |

## Decision
Ship, because primary metric is significantly improved and all guardrails passed.

## Next steps
- Ramp treatment to 100% over 7 days
- Monitor revenue_per_user weekly for 30 days post-ship
```

---

## Example 2: SRM failure (do not analyze)

**User prompt:** "Read out this test."

**Skill output:**

```markdown
# Experiment Readout: <name>

## CRITICAL: Sample Ratio Mismatch detected
| Variant | Expected | Observed | Delta |
|---|---|---|---|
| Control | 50.0% | 47.2% | -2.8pp |
| Treatment | 50.0% | 52.8% | +2.8pp |

χ² p-value: <0.001 — **FAIL**

Assignment is broken. Do not interpret the primary metric until the root cause is identified.

## Common SRM causes to investigate:
1. **Bot filtering applied unevenly** — check if control's bot filter is stricter
2. **Trigger condition asymmetry** — verify both variants trigger on the same event
3. **Logging differences** — confirm both variants log exposure to the same table
4. **Sticky assignment + redirect loop** — check if some users are being re-bucketed

## Next steps
- Pull raw assignment logs for the first 1000 users per variant
- Compare exposure-event funnel between variants
- Re-launch the experiment only after SRM root cause is fixed
```

---

## Example 3: Mixed result — significant lift but guardrail FAIL

**User prompt:** "Did our new recommendations algo win?"

**Skill output (abbreviated):**

```markdown
## TL;DR
**Recommendation: Hold — investigate guardrail tradeoff**

Click-through rate on recommendations increased +12% [+8%, +16%], significant at p < 0.0001. However, revenue_per_user dropped -3.1% [-5.4%, -0.8%] (guardrail threshold: not down > 2%), which crosses the threshold with 95% confidence.

## Interpretation
The new algorithm drives more clicks but to lower-value items. The CTR lift is real, but it's cannibalizing high-AOV purchases.

## Decision
Hold. Two paths forward:
1. **Reweight the model** toward higher-AOV items and re-test
2. **Accept the tradeoff** if leadership prioritizes engagement over short-term revenue (requires explicit sign-off, not a DS call)

## Caveats
- 14-day window is shorter than typical purchase cycle (28 days). Revenue impact may be muted.
- Pre-registered analysis. No post-hoc subgroups explored.
```
