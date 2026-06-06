---
name: ab-readout
description: Generate a stakeholder-ready A/B test readout from results data
---

# /ab-readout

Generate a complete A/B test readout following the pre-registered analysis plan.

## Usage

```
/ab-readout
```

Then provide:
- Path to results data (CSV or query result)
- Pre-registration details (primary metric, MDE, guardrails)
- Target audience (PM, exec, etc.)

## Workflow

1. Load `skills/ab-test-analysis/SKILL.md` for the analysis workflow
2. Load `skills/stakeholder-readout/SKILL.md` for the readout structure
3. Run the analysis (SRM check, primary metric significance + CI, guardrails)
4. Format the output using the readout template
5. Invoke `agents/experiment-reviewer.md` to sanity-check before finalizing

## Output

A complete readout with TL;DR, primary metric table, guardrail table, decision, and caveats.
