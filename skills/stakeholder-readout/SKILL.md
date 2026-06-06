---
name: stakeholder-readout
description: Structures a stakeholder-ready analysis writeup with TL;DR, evidence, decision, and next steps. Use when the user asks for a readout, analysis writeup, insight doc, exec summary, "share this with the team", "make this stakeholder-friendly", or "summarize the findings."
---

# Stakeholder Readout

## When to use this skill

Use whenever an analysis output needs to be communicated to a non-DS audience (PM, eng, exec, sales). Triggers:

- "Write a readout for…"
- "Summarize the findings"
- "Make this stakeholder-friendly"
- "Exec summary of…"
- "Share this with the team"

Pair with any analysis-producing skill (`ab-test-analysis`, `cohort-analysis`, `survival-analysis`, etc.). This skill is the **packaging layer**.

## Required inputs

| Input | Why it matters |
|---|---|
| Question being answered | The decision this informs |
| Audience | PM / Exec / Eng / Mixed — affects depth |
| Key finding | The 1-2 sentence headline |
| Evidence (data / charts) | Numbers backing the finding |
| Confidence level | How sure are we? |
| Recommended decision | What you'd do if it were your call |

## The readout structure

Every readout has exactly five sections, in this order:

1. **TL;DR** — One sentence, one decision recommendation
2. **Context** — What question + why now
3. **Findings** — 2-5 key facts with evidence
4. **Decision** — What to do, by whom, by when
5. **Caveats & next steps** — What we don't know

## Workflow

1. **Write the TL;DR first.** If you can't summarize in one sentence, you don't understand it yet. The TL;DR must contain:
   - The answer to the question
   - The recommended action
   - Confidence indicator ("strong evidence" / "directional" / "preliminary")

2. **List 2-5 findings**, each with:
   - The fact (one sentence)
   - The data behind it (number + comparison + context)
   - Why it matters (decision relevance)

3. **State the decision explicitly.** Not "this suggests we might want to consider…" — but "Ship the change" / "Hold and investigate" / "No action needed."

4. **List caveats**, sorted by how much they should change the decision. If a caveat would change the recommendation, surface it at the top.

5. **End with next steps** — concrete, owned, time-bound.

## Output format

```markdown
# <Analysis Title>

**Author:** <name>  
**Audience:** <PM / Exec / Eng / Mixed>  
**Date:** <YYYY-MM-DD>  
**Status:** <Final | Draft for review | Preliminary>

---

## TL;DR
<One sentence. Includes finding + recommendation + confidence.>

**Recommendation:** <Specific action, e.g., "Ship the new onboarding flow to 100%">  
**Confidence:** <Strong | Moderate | Directional / preliminary>

---

## Context
- **Question:** <The decision this analysis informs>
- **Why now:** <The trigger — leadership ask, opportunity sized, problem detected>
- **What we did:** <Method in one paragraph — no jargon, name the technique>

---

## Findings

### Finding 1: <one-sentence headline>
<2-3 sentences expanding the fact, with the specific number and a comparison>

> Evidence: chart, table, or query result

### Finding 2: <one-sentence headline>
<...>

### Finding 3: <one-sentence headline>
<...>

---

## Decision

**Recommended:** <Specific action>

**Owner:** <Name(s)>

**Timeline:** <When>

**Why this and not alternatives:**
- Considered: <alternative 1> — rejected because <reason>
- Considered: <alternative 2> — rejected because <reason>

---

## Caveats & next steps

### What we don't know
- <Caveat 1, ordered by how much it could change the decision>
- <Caveat 2>

### Next steps
1. **<Action>** — <owner> — <by when>
2. **<Action>** — <owner> — <by when>
3. **<Action>** — <owner> — <by when>

---

## Appendix
<Optional: methodology details, charts, secondary findings — only for those who want the depth>
```

## Validation checks

- [ ] TL;DR is ONE sentence
- [ ] TL;DR includes a specific recommendation
- [ ] Each finding has a number AND a comparison (vs prior period, vs benchmark, vs alternative)
- [ ] Decision is unambiguous (not "could be valuable to explore")
- [ ] Owner and timeline named for every next step
- [ ] Caveats include the worst-case "this could be wrong because…"
- [ ] Length appropriate for audience (exec = 1 page; team = up to 3 pages)
- [ ] No statistical jargon without translation (p-value → "very strong evidence")

## Edge cases & failure modes

- **No clear recommendation.** If the data doesn't support a decision, the recommendation is "do X to get a clearer answer" — not silence. Common phrasings: "Run a follow-up experiment to disambiguate," "Defer for 4 weeks pending more data."

- **Findings contradict the asker's hypothesis.** Lead with the contradiction, don't bury it. Stakeholders trust analyses that confirm their priors AND ones that don't — they don't trust analyses that hedge.

- **Insufficient sample size / inconclusive.** Mark TL;DR as "Inconclusive — recommend X to get a definitive answer." Don't pretend uncertainty is certainty.

- **Stakeholder asks for a specific framing.** Push back if the framing distorts the finding. The job is accurate, not flattering.

- **Multiple audiences with different needs.** Default to the highest-stakes audience (exec). Optional: write 2 versions — 1-page exec, 3-page team.

## Writing style rules

| Don't | Do |
|---|---|
| "It seems like…" | "Conversion rose 8%." |
| "Could potentially be valuable…" | "Ship this." |
| "p < 0.05" | "Strong evidence (well below the noise threshold)." |
| "Statistically significant" | "Real, not noise." |
| Verbose throat-clearing | Get to the point in the first sentence. |
| Charts without titles | Every chart has a title that states the takeaway. |
| Numbers without comparison | "$1.2M, up 18% vs last quarter." |

## Templates by analysis type

See `templates/` directory in the parent repo for:
- `ab-test-readout.md`
- `cohort-readout.md`
- `model-readout.md`
- `insight-doc.md`

## Related skills

- `ab-test-analysis` — produces the analysis; this skill packages it
- `cohort-analysis`, `funnel-analysis` — same
- `metric-definition` — provides the precise definitions readouts reference
- Any modeling skill — wrap its output in this structure
