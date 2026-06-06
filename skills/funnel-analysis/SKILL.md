---
name: funnel-analysis
description: Builds step-by-step funnel analyses with conversion rates, drop-off diagnosis, and segmentation. Use when the user mentions funnel, conversion rate, drop-off, signup-to-activation, step-by-step conversion, onboarding flow, or "where are users falling off."
---

# Funnel Analysis

## When to use this skill

Use when measuring **sequential step-by-step conversion** through a defined flow. Triggers:

- "Build a signup funnel"
- "Where are users dropping off?"
- "Conversion from step A to step B"
- "Analyze the checkout flow"
- "Activation funnel"

For lifecycle behavior over weeks/months → `cohort-analysis`. For experiments → `ab-test-analysis`.

## Required inputs

| Input | Why it matters |
|---|---|
| Funnel steps (ordered) | The sequence to measure |
| Unit of analysis | User, session, or visit |
| Time window | Conversion deadline between steps |
| Strict vs non-strict order | Must steps occur in order, or just all eventually? |
| Cohort filter | Which users to include (e.g., new signups only) |

## Workflow

1. **Define the steps explicitly.** Each step is an event name + filter conditions. Avoid vague steps like "engaged."

2. **Decide strict vs non-strict ordering.**
   - **Strict (sequential)**: step N must follow step N-1 in time. Standard for onboarding/checkout flows.
   - **Non-strict (any order)**: user must have done all steps eventually. Use for feature adoption funnels where order doesn't matter.

3. **Set the conversion window.** Between step N and N+1, what's the max time to convert? Common defaults:
   - Same session: ~30 min
   - Same day: 24h
   - Same week: 7 days
   - Lifetime: open-ended (but inflates conversion artificially)

4. **Compute the funnel using `scripts/build_funnel.sql`**, which produces:
   - Step counts (users reaching each step)
   - Step-to-step conversion rate
   - End-to-end conversion rate
   - Median time between steps

5. **Diagnose biggest drop-offs.** The largest absolute drop is usually the highest-leverage fix. Compare:
   - vs benchmark (industry, prior period)
   - vs segments (channel, device, plan)

6. **Segment to find the right bucket.** Compare the funnel by:
   - Acquisition channel
   - Device (mobile vs desktop)
   - User type (new vs returning)
   - Country / locale

   Look for steps where conversion **diverges** between segments. These are the actionable insights.

7. **Write the readout.**

## Output format

```markdown
# Funnel Analysis: <name>

## Definitions
- Unit: <user | session>
- Cohort filter: <e.g., new signups in last 14 days>
- Ordering: <strict | non-strict>
- Conversion window: <e.g., same session, max 30 min between steps>
- Date range: <start> to <end>

## Funnel (overall)
| Step | Users | Step CR | End-to-end CR | Median time from prev |
|---|---|---|---|---|
| 1. Landing | 100,000 | — | 100% | — |
| 2. Signup | 32,000 | 32.0% | 32.0% | 1.2 min |
| 3. Email verify | 22,400 | 70.0% | 22.4% | 4.5 min |
| 4. Profile complete | 16,800 | 75.0% | 16.8% | 2.1 min |
| 5. First action | 10,080 | 60.0% | 10.1% | 14 min |

## Biggest drop-offs
1. **Landing → Signup**: -68pp drop (32% conversion). Largest absolute loss.
2. **Profile complete → First action**: -40pp drop, slowest median time (14 min) — suggests confusion or friction.

## Segment breakdowns
| Segment | Landing→Signup | Signup→Verify | Verify→Profile | Profile→First |
|---|---|---|---|---|
| Mobile | 28% | 65% | 73% | 52% |
| Desktop | 38% | 78% | 78% | 68% |
| Paid search | 35% | 72% | 76% | 64% |
| Organic | 24% | 68% | 73% | 55% |

**Key finding:** Mobile users underperform desktop at every step. Largest mobile gap is at "first action" (52% vs 68%) — suggests post-signup mobile experience friction.

## Interpretation
- The single biggest leverage point is landing → signup (-68pp). Even a 2pp improvement = 2,000 more weekly signups.
- However, the most actionable opportunity is **mobile first-action** because the gap vs desktop is large and the cohort is high-intent (already signed up).

## Caveats
- "First action" definition: <event spec>
- Users counted at most once per step (deduplicated by user_id)
- Mobile = iOS + Android combined; gap may differ by OS

## Next steps
- Run heatmap analysis on mobile post-signup screens
- Pre-register an A/B test on the signup form (see `ab-test-design`)
```

## Validation checks

- [ ] Each step has a single, unambiguous event definition
- [ ] Conversion window stated and consistent
- [ ] Deduplication rule stated (1 user = 1 row per step)
- [ ] Date range stated and excludes incomplete most-recent day
- [ ] Step counts monotonically non-increasing in strict funnels

## Edge cases & failure modes

- **Skipped steps**: in non-strict funnels, a user might skip step 3 and do step 4. Decide if they "count" for step 3. Default: no, they don't.
- **Re-entries**: user does step 1, abandons, comes back next day and does step 1 again. Count first instance only (use min event timestamp).
- **Lifetime windows inflate conversion**: a 30-day window will show higher conversion than 1-day, but the trailing days are mostly "users who eventually got around to it" rather than directly attributable to the funnel design.
- **Survivorship at later steps**: late steps have small N — small absolute changes look like big percentage shifts. Show absolute counts alongside rates.
- **Step granularity**: too granular (10+ steps) makes drop-off diagnosis impossible. Roll up. 4-6 steps is the sweet spot.

## Scripts

- `scripts/build_funnel.sql` — Snowflake template for strict-ordered funnel with time-bounded steps.

## Related skills

- `cohort-analysis` — for lifecycle behavior over weeks/months
- `metric-definition` — pin down each step's event definition
- `ab-test-design` — test a fix to the biggest drop-off
- `data-quality-audit` — sanity-check the event sources before trusting the funnel
