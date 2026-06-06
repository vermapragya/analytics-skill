# Rule: Experiment Rigor

Always-follow rules for designing and analyzing A/B tests.

## Design rules

1. **Pre-register before launch.** No exceptions. Doc must include: hypothesis, primary metric, MDE, guardrails, sample size, runtime, analysis plan, stopping rules.

2. **One primary metric.** Multiple primaries inflate false positives. If you need two, apply Bonferroni or commit to ranking them.

3. **MDE = smallest effect worth shipping.** Not "the effect we hope for" and not "the effect that fits our runtime." If sample size is impractical, push back on the question, not the MDE.

4. **Runtime ≥ 14 days.** Cover at least one full weekly cycle. Multiple of 7 preferred.

5. **Randomization unit = treatment delivery unit.** If treatment is delivered per-user, randomize per-user. Per-session if per-session.

6. **Define guardrails with thresholds.** "Don't regress revenue" is not a guardrail. "Revenue/user must not drop > 2% with 95% confidence" is.

## Analysis rules

1. **Run SRM check first.** If failed (χ² p < 0.001), STOP. Do not report primary metric.

2. **Report confidence intervals, not just p-values.** Stakeholders need effect magnitude with uncertainty.

3. **All pre-registered guardrails reported.** Even passing ones — don't bury or omit.

4. **No post-hoc subgroup decisions.** Subgroup analyses are hypothesis-generating unless pre-registered.

5. **Don't peek.** No analysis before planned sample size unless guardrail check (and even then, no decisions).

6. **Heavy-tailed metric handling stated.** Winsorize, log, or trimmed mean — pre-specified.

## Reporting rules

1. **Decision is unambiguous.** Ship / hold / kill / inconclusive. No "could explore."

2. **Pre-registration deviations called out.** If you analyzed differently than planned, say so, loudly, in the caveats.

3. **No one-sided p-values unless one-sided was pre-registered.** Default is two-sided.

## When NOT to A/B test

- Decision is reversible and cheap to undo (just ship)
- Sample size too small (< 30 days runtime)
- Strong network effects (use `causal-inference` instead)
- Required change (legal, security, parity)

## See also
- `skills/ab-test-design/`
- `skills/ab-test-analysis/`
- `agents/experiment-reviewer.md`
