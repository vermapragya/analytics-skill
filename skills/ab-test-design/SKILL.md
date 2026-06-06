---
name: ab-test-design
description: Designs A/B tests with power analysis, minimum detectable effect (MDE), sample size estimation, randomization unit selection, guardrail definition, and a pre-registration checklist. Use when the user mentions experiment design, A/B test setup, power analysis, sample size, MDE, pre-registration, randomization, or asks "how should I run this experiment."
---

# A/B Test Design

## When to use this skill

Use when the user is **planning** an experiment, not analyzing one. Triggers include:

- "Design an A/B test for…"
- "What sample size do I need…"
- "How long should I run this test…"
- "Pre-register this experiment"
- "Pick guardrails for…"

If the user already has results, use `ab-test-analysis` instead.

## Required inputs

Collect these before computing anything. If missing, ask.

| Input | Why it matters |
|---|---|
| Primary metric | Determines test type (proportion, mean, ratio) |
| Baseline rate or mean | Required for power calculation |
| Minimum detectable effect (MDE) | Sets sensitivity floor |
| Randomization unit | User, session, account, device |
| Expected daily exposure (units/day) | Determines runtime |
| Variant count (control + N treatments) | Affects multiple-comparison correction |
| Guardrail metrics | What must not regress |

## Workflow

1. **Confirm hypothesis is testable.** A hypothesis has the form: "Changing X will move metric Y by at least Z%, because reason R." If reason R is missing, push back.

2. **Pick the metric type.**
   - Binary outcome (conversion, click) -> proportion test
   - Continuous (revenue per user, session length) -> mean test, log-transform if skewed
   - Ratio (revenue per impression) -> delta method or bootstrap

3. **Set MDE conservatively.** Default to the smallest effect the team would actually act on. Do not optimize MDE to fit the runtime — that's how teams ship noise.

4. **Compute sample size** using `scripts/sample_size.py`. Default to alpha=0.05, power=0.80, two-sided.

5. **Compute runtime** = (sample size per arm × num arms) / daily exposure. Round up to a full business cycle (e.g., 14 days minimum to capture weekday/weekend variance).

6. **Define guardrails.** Minimum three:
   - One business guardrail (e.g., revenue/user must not drop > X%)
   - One quality guardrail (e.g., error rate, latency)
   - One reach guardrail (assignment ratio sanity check, sample ratio mismatch)

7. **Write pre-registration doc** using the template below.

## Output format

Produce a pre-registration block:

```markdown
# Experiment Pre-Registration: <name>

## Hypothesis
Changing <X> will move <Y> by at least <Z>%, because <R>.

## Variants
- Control: <description>
- Treatment 1: <description>
- (Treatment 2: <description>)

## Randomization
- Unit: <user | session | account>
- Allocation: <e.g., 50/50, 33/33/33>

## Metrics
- Primary: <metric name, definition, source table>
- Secondary: <list>
- Guardrails: <list with thresholds>

## Power
- Baseline: <value>
- MDE: <value> (absolute / relative)
- Alpha: 0.05
- Power: 0.80
- Required sample per arm: <N>
- Expected daily exposure per arm: <N/day>
- Minimum runtime: <D days> (≥ 14 days to cover one weekly cycle)

## Stopping rules
- No peeking before <date>
- Stop early only on guardrail breach (specify threshold)

## Analysis plan
- Test: <z-test / t-test / Mann-Whitney / CUPED-adjusted>
- Subgroup analyses (pre-specified): <list or "none">
```

## Validation checks

Before finalizing, verify:

- [ ] Primary metric has a single, unambiguous SQL definition
- [ ] Randomization unit matches the unit at which the treatment is delivered
- [ ] Runtime covers at least one full weekly cycle
- [ ] Sample ratio mismatch (SRM) check is part of the analysis plan
- [ ] Guardrails have explicit thresholds and stop-the-experiment rules
- [ ] No more than 1 primary metric (multiple primaries inflate false positives)

## Edge cases & failure modes

- **Network effects** (marketplaces, social): user-level randomization leaks treatment. Use cluster randomization (geo, cohort) or switchback designs.
- **Very rare events** (< 1% base rate): sample size explodes. Consider proxy metrics or longer runtime.
- **Long conversion windows**: define the observation window explicitly. A "7-day conversion" experiment running 7 days has no fully-observed users yet.
- **Novelty / primacy effects**: plan a 14-day minimum and discard the first 2-3 days from analysis if needed (pre-specify this).

## Scripts

- `scripts/sample_size.py` — Sample size calculator for proportion and mean tests.

```bash
python scripts/sample_size.py --metric-type proportion --baseline 0.12 --mde 0.01 --alpha 0.05 --power 0.80
python scripts/sample_size.py --metric-type mean --baseline-mean 45.2 --baseline-std 18.4 --mde 2.0
```

## Related skills

- `ab-test-analysis` — read out results after the experiment runs
- `metric-definition` — write precise specs for primary and guardrail metrics
- `causal-inference` — for situations where RCT isn't feasible
