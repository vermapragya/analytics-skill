# Rule: Readout Format

Every analysis communicated to stakeholders follows the 5-section format.

## The 5 sections (always in this order)

1. **TL;DR** — one sentence with finding + recommendation + confidence
2. **Context** — question + why now + method (1 paragraph)
3. **Findings** — 2-5 facts, each with number + comparison + relevance
4. **Decision** — specific recommendation + owner + timeline + alternatives considered
5. **Caveats & next steps** — what we don't know + concrete actions

## TL;DR rules

- ONE sentence (period)
- Includes the answer to the question
- Includes the recommendation
- Includes a confidence indicator (strong / moderate / directional)
- Reader can stop here and make the decision

## Findings rules

- Each finding = 1 sentence headline + 2-3 supporting sentences
- Every number has a comparison (vs prior, vs benchmark, vs alternative)
- No statistical jargon untranslated ("p < 0.05" → "very strong evidence" or "not noise")

## Decision rules

- Specific action: "Ship X" / "Hold" / "Kill Y" / "Run experiment Z"
- Named owner (person, not team alias)
- Named timeline (date or duration)
- "Why this and not alternatives": list 1-2 considered and rejected

## Caveats rules

- Caveats ordered by decision impact (most impactful first)
- Each caveat says: how it could change the recommendation
- "No material caveats" is acceptable if true (rare)

## Next steps rules

- Concrete, owned, time-bound
- 2-5 items max
- Each: `**<action>** — <owner> — <by when>`

## Length by audience

| Audience | Length |
|---|---|
| C-suite / VP | 1 page |
| Director / Senior PM | 1-2 pages |
| PM / Eng partner | 2-3 pages |
| DS peers | 5-10 pages |

## Anti-patterns

- Hedge words: "might," "could potentially," "it seems"
- Charts without takeaway titles
- Numbers without comparison
- Findings ordered by analysis sequence, not importance
- Recommendation missing
- Owner missing on next steps

## See also
- `skills/stakeholder-readout/`
- `agents/ds-readout-reviewer.md`
- `templates/` for readout starter docs
