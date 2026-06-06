# Cohort Analysis — Examples

## Example 1: Weekly signup cohorts, any-activity retention

**User prompt:** "Build a weekly cohort retention table for signups over the last 12 weeks."

**Skill output (abbreviated):**

```markdown
# Cohort Analysis: New signup weekly retention

## Definitions
- Cohort anchor: signup event, week of (Mon-Sun)
- Retention event: any logged event in week N
- Denominator: cohort-fixed
- Lookback: 12 weeks

## Summary
- Latest cohort (W12) W1 retention: 38.2% (vs 35.1% in W1, +3.1pp)
- W8 retention asymptote: ~14%
- Retention "stabilizes" around W6

## Cohort table (% retained)
| Cohort | Size | W1 | W2 | W4 | W8 | W12 |
|---|---|---|---|---|---|---|
| W1 (Jan 1) | 8,420 | 35.1% | 22.0% | 16.4% | 13.5% | 13.0% |
| W2 (Jan 8) | 9,100 | 36.4% | 22.5% | 16.8% | 13.9% | — |
| W3 (Jan 15) | 9,500 | 37.0% | 23.0% | 17.2% | 14.2% | — |
| ... |
| W11 | 11,200 | 38.5% | 23.8% | 17.5% | — | — |
| W12 | 11,800 | 38.2% | — | — | — | — |

## Interpretation
W1 retention is trending up 3.1pp over 12 weeks — likely the onboarding redesign that shipped W4 is working. Long-term retention (W8) is also up slightly (+0.7pp), suggesting the improvement is sticking rather than just shifting the curve.

## Caveats
- W11 and W12 cohorts have incomplete data through W8/W12 (marked —)
- Late-arriving event pipeline has a 12-24h lag; W1 retention for the most recent cohort may be undercounted by ~0.5pp

## Next steps
- Segment by acquisition channel to confirm the onboarding lift isn't isolated to one source
- Re-check in 4 weeks once W11/W12 reach W8
```

---

## Example 2: Eligible-base for a subscription product

**User prompt:** "Build monthly cohort retention for our subscription product."

**Skill response (key callouts):**

> Subscription product → cohort-fixed denominator is misleading because users who downgrade or pause can't take retention action. Recommend eligible-base.
>
> Definitions:
> - Cohort anchor: subscription_start_at, month
> - Retention event: at least one logged_in_event during month N
> - Denominator: users whose subscription was active for ≥ 14 days of month N (eligible-base)
>
> This produces a higher and more honest retention curve, because users who churned mid-month aren't penalized for not logging in afterward.

---

## Example 3: Re-engaging users

**User prompt:** "How do I handle users who come back after months of dormancy?"

**Skill response:**

> Define re-anchor rule before the analysis. Three common options:
>
> 1. **Original cohort only** (default): user always belongs to their first cohort. Reactivation shows up as a spike in late-period retention.
> 2. **First + reactivation as separate cohorts**: user appears in two cohorts. Useful for distinguishing first-time vs returning behavior.
> 3. **Latest anchor wins**: user always belongs to their most recent activation cohort. Erases reactivation signal, so only use if reactivation is rare.
>
> Default to (1). Document the choice in the readout's "Definitions" section.
