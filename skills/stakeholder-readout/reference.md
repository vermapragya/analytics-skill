# Stakeholder Readout — Reference

## Audience calibration

| Audience | Length | Depth | Visualization |
|---|---|---|---|
| C-suite / VP | 1 page | One chart, one decision | Big number, single chart |
| Director / Senior PM | 1-2 pages | Methodology gist, decision options | 2-3 charts |
| PM / Eng partner | 2-3 pages | Full method + nuance | 3-5 charts + table |
| DS peers | 5-10 pages | Full method, all assumptions | All charts + code |

If unsure, default to PM-level (2-3 pages).

## TL;DR templates

### A/B test result
> Variant X increased <metric> by <X%> ([<low>, <high>] CI) over <N> days. Recommend shipping to 100%.

### Cohort/retention finding
> Recent cohorts show <X%> improvement in <Y-day> retention, driven by <hypothesized cause>. Recommend doubling down on <action>.

### Model performance
> The churn model achieves <AUC X> on holdout, identifying <X%> of churners with <Y%> precision. Recommend deploying for <use case>.

### Inconclusive
> The analysis didn't reach a definitive answer — the effect, if real, is smaller than we can detect with current sample. Recommend <follow-up> to resolve.

### Negative result
> The change did not improve <metric>; the lift fell within statistical noise. Recommend killing this variant and exploring <alternative>.

## Finding patterns

Every finding should follow this micro-structure:

> **<Headline>.** <Number + comparison>. <Why it matters>.

Example:

> **Mobile users complete checkout 25% less often than desktop.** The mobile completion rate is 9.2% vs 12.3% on desktop, despite mobile making up 58% of traffic. Closing this gap to even half of desktop's rate would add ~$1.4M annualized revenue.

## Chart titles that earn their space

| Bad | Good |
|---|---|
| "Conversion by week" | "Conversion is up 8% since the onboarding redesign" |
| "Retention curves" | "Annual plans retain users 2.4× longer than monthly" |
| "Distribution of session times" | "Half of sessions are under 4 minutes; the top 5% take 90+" |

Title states the takeaway. Body shows the evidence.

## Decision language

| Status | Phrasing |
|---|---|
| Strong evidence, clear action | "Ship X" / "Stop doing Y" / "Invest in Z" |
| Moderate evidence | "Pilot X with N customers / 4 weeks before broader rollout" |
| Uncertain | "Run experiment Y to get a definitive answer" |
| Need more context | "Investigate Z before deciding" |

Never:
- "Could be worth considering…"
- "Might want to think about…"
- "It would be interesting to…"

These signal weak analysis, not nuance.

## Caveat ordering

List caveats from most to least decision-changing:

1. **Things that could flip the recommendation** (top — always surface)
2. **Things that could change the magnitude** (middle)
3. **Methodological gotchas** (bottom — for the technically curious)

## When you must say "we don't know"

- Sample size too small
- Data quality issues block the analysis
- The question can't be answered with available data
- The proposed comparison isn't valid

Always pair with a path to certainty: "We need <X> to answer this confidently. Estimated effort: <Y>."

## Common stakeholder questions to pre-empt

| Question | Preempt by addressing |
|---|---|
| "Is this statistically significant?" | Report CI, not just p-value |
| "What's the magnitude in dollars/users?" | Translate effect to business unit |
| "Is this consistent across segments?" | Report at least one segment cut |
| "What's the downside?" | List guardrail metrics |
| "How sure are we?" | Confidence level in TL;DR |
| "What's next?" | Concrete next steps with owners |

## Visualization principles

1. **One chart, one message.** Don't try to show 5 things in one chart.
2. **Use comparison.** A number alone is meaningless; vs benchmark/prior/control is meaningful.
3. **Label directly, avoid legends.** Less eye movement.
4. **Order categories meaningfully** — by value, by time, or by alphabetical only if no better choice.
5. **Remove chartjunk.** Gridlines, 3D, gradient fills, redundant labels.

## Slack / email format

For Slack:
- TL;DR at the top, link to full doc
- One key chart inline
- Threaded for discussion

For email:
- Subject = the recommendation ("Recommend shipping new onboarding flow")
- TL;DR in body, full doc linked

## Common readout failure modes

1. **Burying the lede** — TL;DR doesn't actually summarize.
2. **Hedging the recommendation** — afraid to commit.
3. **No business translation** — leaves "statistical significance" untranslated.
4. **Charts without takeaways** — looks rigorous but no one can act on it.
5. **Missing caveats** — surprises stakeholders later.
6. **No clear owner for next steps** — readout doesn't lead to action.
