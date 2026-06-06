---
name: sample-size
description: Compute A/B test sample size and runtime
---

# /sample-size

Compute the sample size and runtime needed for an A/B test.

## Usage

```
/sample-size
```

Then provide:
- Metric type (proportion / mean)
- Baseline (rate or mean)
- MDE (absolute or relative)
- Daily exposure per arm (optional, for runtime)

## Workflow

1. Load `skills/ab-test-design/SKILL.md`
2. Run `skills/ab-test-design/scripts/sample_size.py` with the provided inputs
3. Report:
   - Required sample per arm
   - Runtime at given daily exposure
   - Warning if runtime < 14 days (insufficient weekly cycle coverage)
4. If multiple variants, apply Bonferroni correction

## Output

Sample size + runtime + warnings, in plain text.
