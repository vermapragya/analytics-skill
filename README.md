# analytics-skills

A skills library for **product data scientists** working with Claude.

Reusable, opinionated skills you can invoke in Claude Code, Cursor, and other AI coding harnesses for the analytics work you actually do every day — experiments, cohorting, SQL modeling, regression, causal inference, and stakeholder readouts.

Built in the spirit of [affaan-m/ECC](https://github.com/affaan-m/ECC): skills are the primary surface, descriptions trigger discovery, and every skill ships with reference docs, examples, and reusable scripts.

---

## Why this exists

Most "analytics templates" are either generic markdown checklists or one-off notebooks that rot fast. This library treats DS workflows as **first-class skills**:

- Self-contained — each skill is one folder with everything it needs
- Auto-discoverable — Claude picks the right skill based on what you ask
- Stack-opinionated — Snowflake + Python (pandas/scikit-learn) + dbt
- Production-grade — includes scripts, examples, and reviewer agents
- Cross-harness — works in Claude Code, Cursor, and any harness that reads `SKILL.md`

---

## What's inside

```
analytics-skills/
├── skills/                  # Primary surface — 15 day-to-day DS skills
├── agents/                  # Specialized reviewers (experiment, SQL, readout)
├── commands/                # Slash commands for fast invocation
├── rules/                   # Always-follow style guides
├── hooks/                   # Pre/post tool automations
├── templates/               # Notebook & readout templates
├── manifest.json            # Catalog of all skills + metadata
├── INSTALL.md               # Setup for Claude Code, Cursor, manual
└── CONTRIBUTING.md          # Guide for adding new skills
```

---

## The 15 skills

| Skill | What it does | When Claude uses it |
|---|---|---|
| `ab-test-design` | Power, MDE, sample size, design checklist | "Design an A/B test for…" |
| `ab-test-analysis` | Significance testing, CIs, readout | "Analyze this experiment…" |
| `cohort-analysis` | Retention curves, cohort tables | "Show retention by signup cohort…" |
| `funnel-analysis` | Step conversion, drop-off diagnosis | "Build a funnel for signup → activation…" |
| `metric-definition` | Metric specs, guardrails, owner | "Define a North Star for…" |
| `modular-sql-ctes` | Staging/intermediate/fact CTE patterns | "Refactor this SQL…" |
| `data-quality-audit` | Null/dup/freshness/schema checks | "Audit this table for data quality…" |
| `logistic-regression` | Binary outcome modeling, calibration | "Model churn probability…" |
| `linear-regression` | Continuous outcome, coefficient reading | "Predict revenue from…" |
| `survival-analysis` | Time-to-event with censoring | "Model time-to-churn…" |
| `stakeholder-readout` | Insight write-up structure | "Write a readout for…" |
| `warehouse-query-optimization` | Snowflake-specific perf tuning | "This query is slow on Snowflake…" |
| `sql-query-review` | Static anti-pattern check + optimized rewrite | "Review/optimize this query…" |
| `sql-correctness-review` | Logic audit: dupes, fanout, joins, NULLs, CASE | "These numbers look wrong…" |
| `causal-inference` | DiD, matching, IV decision framework | "Estimate causal impact of…" |

---

## Quickstart

```bash
git clone https://github.com/<your-org>/analytics-skills.git
cd analytics-skills

# Install for Claude Code
bash install.sh --target claude

# Install for Cursor (project-local)
bash install.sh --target cursor --project-dir /path/to/your/project
```

See [INSTALL.md](./INSTALL.md) for all install paths, including manual copy and partial installs.

---

## How to use a skill

Once installed, Claude will auto-trigger skills based on intent. You can also invoke directly:

```
"Use the ab-test-analysis skill to read out the experiment in /data/exp_123.csv"

"Apply modular-sql-ctes to refactor this query: <paste>"

"Run a data-quality-audit on fct_orders"
```

Each skill prompts Claude through a consistent workflow:

1. Clarify inputs and assumptions
2. Apply the analytical method
3. Run validation checks
4. Produce stakeholder-ready output

---

## Stack assumptions

Skills are written against this stack. Where logic is stack-specific, alternatives are noted in each skill's `reference.md`.

- **Warehouse**: Snowflake (BigQuery/Postgres/Redshift compatible with minor edits)
- **Python**: pandas, scikit-learn, statsmodels, lifelines
- **Modeling**: dbt
- **Notebooks**: Jupyter

---

## Design principles

1. **One skill = one workflow.** No mega-skills.
2. **Descriptions are the discovery contract.** They tell Claude when to invoke.
3. **Ship scripts, not just prose.** Reusable code beats regenerated code.
4. **Bias toward defaults.** Tell Claude what to do, not all the options.
5. **Stakeholder output is part of the skill.** Analysis without readout doesn't ship.

---

## License

MIT. See [LICENSE](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). New skills welcome — follow the template and quality checklist.
