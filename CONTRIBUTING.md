# Contributing

Thanks for considering a contribution to `analytics-skills`. This library succeeds when skills are **specific, opinionated, and trigger reliably**. Vague skills are worse than no skill.

---

## What makes a good skill here

A skill belongs in this library if:

1. A product data scientist uses the workflow **at least monthly**.
2. The workflow has a **clear input, output, and decision** Claude can drive.
3. The skill produces **stakeholder-ready** artifacts (not just code).
4. There is **one obvious method** to recommend (or a clear branching rule).

A skill does **not** belong if:

- It's a generic LLM task ("summarize this CSV") with no analytics depth.
- It's a code snippet that doesn't need a workflow.
- It's a niche method used once a year.

---

## Skill anatomy

Every skill is a folder under `skills/<skill-name>/` with this layout:

```
skills/<skill-name>/
├── SKILL.md           # Required — frontmatter + workflow
├── reference.md       # Optional — deep technical reference
├── examples.md        # Optional — 2-3 concrete worked examples
└── scripts/           # Optional — reusable Python/SQL
    └── <script>.py
```

### Required: `SKILL.md`

```markdown
---
name: <kebab-case-name>          # max 64 chars, lowercase + hyphens
description: <what + when>        # max 1024 chars, third person, trigger keywords
---

# <Skill Name>

## When to use this skill
<1-3 sentence trigger description>

## Required inputs
- ...

## Workflow
1. ...

## Output format
<template the agent should produce>

## Validation checks
- ...

## Edge cases & failure modes
- ...

## Related skills
- ...
```

### `description` is the discovery contract

Claude uses the `description` field to decide when to invoke the skill. Include both **what** and **when**.

Good:

```yaml
description: Analyzes A/B test results with significance testing, confidence intervals, and stakeholder readout. Use when the user mentions A/B test, experiment, test results, lift, significance, or treatment vs control.
```

Bad:

```yaml
description: Helps with experiments
```

---

## Naming conventions

- Skill folder: `kebab-case`, descriptive, max 30 chars (`ab-test-analysis`, not `analyze-experiments-helper`)
- Scripts: `snake_case.py` (Python) or `kebab-case.sql` (SQL)
- One primary method per skill (split if you'd write "or" in the description)

---

## Scripts policy

Scripts beat regenerated code. Include a script when:

- The logic is non-trivial (>30 lines) and used identically each time
- Reproducibility matters (statistical tests, sample size calc)
- The skill calls out to a CLI-style tool (`python scripts/sample_size.py --baseline 0.1 --mde 0.02`)

Don't include a script when:

- The logic is heavily project-specific
- Claude can write it correctly each time from a 5-line spec

---

## Submission checklist

- [ ] Skill folder follows naming convention
- [ ] `SKILL.md` has valid frontmatter (`name`, `description`)
- [ ] Description includes trigger keywords
- [ ] Workflow has numbered steps
- [ ] Output format is templated
- [ ] At least one validation check listed
- [ ] If scripts included: scripts are executable and documented
- [ ] If new dependency: added to `INSTALL.md`
- [ ] Added entry to `manifest.json`
- [ ] PR description includes a test prompt that should trigger the skill

---

## Local validation

```bash
# Lint frontmatter (basic check)
python scripts/validate_skills.py     # If we add this later

# Test trigger discovery in Claude Code
"Help me <test prompt here>"
```

---

## Style

- Write in third person ("Analyzes…", not "I help you analyze…")
- Be opinionated. Don't list 5 options — pick one.
- No marketing language. Skills are tools, not products.
- Prefer concrete numbers, percentages, thresholds over vague guidance.
- Snowflake SQL by default; note BigQuery/Postgres alternatives in `reference.md`.

---

## Adding to `manifest.json`

```json
{
  "name": "your-skill-name",
  "category": "experimentation | modeling | sql | analysis | communication",
  "description": "Short description matching SKILL.md frontmatter",
  "path": "skills/your-skill-name",
  "stack": ["python", "snowflake"]
}
```
