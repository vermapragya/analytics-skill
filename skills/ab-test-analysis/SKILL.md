---
name: ab-test-analysis
description: Analyzes A/B test results with significance testing, confidence intervals, sample ratio mismatch check, guardrail evaluation, and a stakeholder-ready readout. Use when the user mentions A/B test results, experiment readout, test analysis, lift, significance, p-value, treatment vs control, or asks "did the experiment work."
---

# A/B Test Analysis

## When to use this skill

The experiment has **finished** (or has reached planned sample size) and the user needs to interpret the results. Triggers:

- "Analyze this experiment…"
- "Did the test win?"
- "Was the lift significant?"
- "Write a readout for experiment X"
- "Compare treatment vs control on…"

If the experiment is still being planned, use `ab-test-design`.

## Required inputs

| Input | Format |
|---|---|
| Per-unit assignment data | `unit_id, variant, metric_value` (or aggregate) |
| Variant labels | Which is control |
| Primary metric definition | From the pre-registration |
| Guardrail metrics | From the pre-registration |
| Test design | Sample size targets, MDE, allocation |

If pre-registration is missing, **flag it loudly** in the readout. Post-hoc analysis without a pre-reg should be labeled exploratory.

## Workflow

1. **Sanity check the data.**
   - Verify variant labels match the design
   - Confirm there's exactly one record per unit per variant
   - Check date range matches the experiment window
   - Strip any users who appeared in multiple variants (assignment errors)

2. **Run Sample Ratio Mismatch (SRM) check.**
   - Compute observed vs expected ratio
   - χ² test against design allocation
   - If p < 0.001, **stop**. SRM means broken assignment — results are invalid.

3. **Compute primary metric per variant.**
   - Point estimate
   - 95% confidence interval (use bootstrap for ratio metrics)
   - Absolute lift and relative lift vs control

4. **Test significance.**
   - Proportion: two-proportion z-test
   - Mean: Welch's t-test
   - Ratio: delta method or bootstrap
   - Report p-value AND CI (CI is more useful than p-value alone)

5. **Evaluate guardrails.** Each guardrail gets one of three statuses:
   - **PASS** — within threshold with 95% confidence
   - **WATCH** — point estimate breaches but CI overlaps zero
   - **FAIL** — CI clears the threshold in the wrong direction

6. **Decision recommendation.** Apply this matrix:

| Primary | Guardrails | Recommendation |
|---|---|---|
| Significant win | All PASS | **Ship** |
| Significant win | Any WATCH | **Ship + monitor** the WATCH metric |
| Significant win | Any FAIL | **Hold** — investigate guardrail tradeoff |
| Not significant, CI excludes MDE | All PASS | **No ship** — effect smaller than MDE |
| Not significant, CI includes MDE | All PASS | **Inconclusive** — extend or kill |
| Negative significant | — | **Kill** the treatment |

7. **Write the readout** using the template below.

## Output format

```markdown
# Experiment Readout: <name>

## TL;DR
**Recommendation:** <Ship | Hold | Kill | Inconclusive>

<Primary metric> changed by <X%> ([<low>, <high>] 95% CI, p=<value>) over <N> days.

## Sample Ratio Mismatch
| Variant | Expected | Observed | Delta |
|---|---|---|---|
| Control | 50.0% | 49.8% | -0.2pp |
| Treatment | 50.0% | 50.2% | +0.2pp |

χ² p-value: <value> — **<PASS|FAIL>**

## Primary metric: <name>
| Variant | N | Value | 95% CI |
|---|---|---|---|
| Control | <N> | <val> | [<low>, <high>] |
| Treatment | <N> | <val> | [<low>, <high>] |

- Absolute lift: <X> ([<low>, <high>])
- Relative lift: <X%> ([<low>, <high>])
- Test: <z-test | t-test | bootstrap>, p = <value>

## Guardrails
| Metric | Threshold | Result | Status |
|---|---|---|---|
| <metric> | <threshold> | <delta + CI> | <PASS|WATCH|FAIL> |

## Subgroup analysis (pre-specified only)
<table or "No pre-specified subgroups">

## Decision
<Ship | Hold | Kill | Inconclusive>, because <reason>.

## Caveats
- <pre-registration deviations if any>
- <data quality notes>
- <known confounds>

## Next steps
- <action 1>
- <action 2>
```

## Validation checks

- [ ] Total sample reached the pre-registered target
- [ ] SRM check ran and passed
- [ ] Confidence interval reported (not just p-value)
- [ ] All pre-registered guardrails evaluated
- [ ] Any subgroup analysis flagged as pre-specified vs exploratory
- [ ] Recommendation matches the decision matrix

## Edge cases & failure modes

- **Peeking**: if the user asks for an analysis before planned sample size, refuse to make a ship decision. Compute confidence intervals only and label "interim — do not act on this."
- **One-sided tests**: convert to two-sided unless pre-registered as one-sided. Two-sided is the default.
- **Multiple primary metrics**: if there are more than one, you cannot ship on "any" being significant. Either pick one or apply Bonferroni correction.
- **Heavy-tailed metrics** (revenue): trimmed mean (winsorize at 99th percentile) is often more robust than raw mean. Note this in caveats.
- **Day-of-week effects**: if runtime isn't a multiple of 7 days, day-of-week imbalance can bias results. Note in caveats.

## Scripts

- `scripts/analyze_experiment.py` — End-to-end analysis from a CSV of `unit_id, variant, metric_value`.

```bash
python scripts/analyze_experiment.py \
    --input results.csv \
    --metric-type proportion \
    --control-label control \
    --treatment-label treatment
```

## Related skills

- `ab-test-design` — pre-experiment planning
- `metric-definition` — clarify guardrail thresholds
- `stakeholder-readout` — for non-experiment analyses needing similar structure
- `causal-inference` — when randomization is broken or unavailable
