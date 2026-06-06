# Install Guide

`analytics-skills` works across harnesses. Pick your install path below.

---

## Option 1: Claude Code (recommended)

### Personal install (all projects)

```bash
git clone https://github.com/<your-org>/analytics-skills.git
cd analytics-skills

mkdir -p ~/.claude/skills/analytics
cp -r skills/* ~/.claude/skills/analytics/
```

### Project install

```bash
cd /path/to/your/project
mkdir -p .claude/skills/analytics
cp -r /path/to/analytics-skills/skills/* .claude/skills/analytics/
```

### Add agents, commands, rules, hooks (optional)

```bash
cp -r agents/* ~/.claude/agents/
cp -r commands/* ~/.claude/commands/
cp -r rules/* ~/.claude/rules/
cp hooks/hooks.json ~/.claude/hooks/hooks.json
```

> Claude Code v2.1+ auto-loads `hooks/hooks.json` from any installed plugin. If you copy hooks manually, do not also enable them via plugin to avoid duplicate execution.

---

## Option 2: Cursor

### Project-local (recommended for teams)

```bash
cd /path/to/your/project
mkdir -p .cursor/skills
cp -r /path/to/analytics-skills/skills/* .cursor/skills/
```

### Personal (all Cursor projects)

```bash
mkdir -p ~/.cursor/skills
cp -r /path/to/analytics-skills/skills/* ~/.cursor/skills/
```

Cursor will auto-discover skills based on their YAML frontmatter `description`.

---

## Option 3: Use the installer script

```bash
# Claude Code, all skills
bash install.sh --target claude

# Cursor, project-local
bash install.sh --target cursor --project-dir /path/to/your/project

# Selective: only specific skills
bash install.sh --target claude --skills ab-test-analysis,cohort-analysis,stakeholder-readout
```

---

## Option 4: Manual copy (single skill)

If you only want one skill:

```bash
mkdir -p ~/.claude/skills/analytics
cp -r skills/ab-test-analysis ~/.claude/skills/analytics/
```

---

## Verifying install

After installing, ask Claude:

```
"What analytics skills are available?"
```

Claude should list the skills from `~/.claude/skills/analytics/` (or `.cursor/skills/`).

Test trigger discovery:

```
"Help me analyze the results of an A/B test."
```

Claude should automatically reference the `ab-test-analysis` skill.

---

## Updating

```bash
cd /path/to/analytics-skills
git pull
bash install.sh --target claude   # re-run install to sync
```

---

## Uninstalling

```bash
rm -rf ~/.claude/skills/analytics
rm -rf .cursor/skills/analytics   # if project-local
```

---

## Troubleshooting

**Claude doesn't pick up the skill automatically.**  
Check the `description` field in `SKILL.md` — descriptions must include trigger keywords (e.g., "A/B test", "cohort", "churn").

**Skill scripts fail to run.**  
Most scripts require Python 3.10+, pandas, scikit-learn, statsmodels, and lifelines. Install:

```bash
pip install pandas scikit-learn statsmodels lifelines snowflake-connector-python
```

**Snowflake-specific SQL fails on another warehouse.**  
See each skill's `reference.md` for cross-warehouse notes (BigQuery, Postgres, Redshift).
