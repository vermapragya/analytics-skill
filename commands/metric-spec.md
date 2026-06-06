---
name: metric-spec
description: Generate a metric specification document
---

# /metric-spec

Generate a metric specification document following the standard format.

## Usage

```
/metric-spec <metric_name>
```

Then answer prompts for:
- Business question
- Source table(s)
- Grain
- Owner
- Inclusions/exclusions
- Guardrails

## Workflow

1. Load `skills/metric-definition/SKILL.md`
2. Ask clarifying questions until all required fields are filled
3. Generate the canonical SQL (Snowflake)
4. Format the full spec following the standard template
5. Suggest where to store it (dbt model description, metric registry, etc.)

## Output

A complete metric spec markdown file ready to commit or publish.
