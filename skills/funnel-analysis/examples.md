# Funnel Analysis — Examples

## Example 1: 5-step signup funnel

**User prompt:** "Build a funnel from landing page through first action for the last 14 days."

**Skill output (abbreviated):**

```markdown
# Funnel Analysis: New user activation

## Definitions
- Unit: user
- Cohort: first landing in last 14 days
- Ordering: strict
- Window: same-session for landing→signup (30 min); same-day for signup→verify; 7 days for verify→first action
- Range: 2026-04-01 to 2026-04-14

## Funnel
| Step | Users | Step CR | E2E CR | Median time |
|---|---|---|---|---|
| 1. Landing | 102,400 | — | 100% | — |
| 2. Signup | 31,840 | 31.1% | 31.1% | 1.8 min |
| 3. Email verify | 22,288 | 70.0% | 21.8% | 4.2 min |
| 4. Profile complete | 16,716 | 75.0% | 16.3% | 2.3 min |
| 5. First action | 10,030 | 60.0% | 9.8% | 18 min |

## Biggest drop-offs
1. Landing → Signup: -68.9pp (largest absolute)
2. Profile → First action: -40pp + 18 min median (suggests post-onboarding friction)

## Segment breakdowns: mobile vs desktop
| Segment | L→S | S→V | V→P | P→F |
|---|---|---|---|---|
| Mobile | 27.5% | 68% | 73% | 51% |
| Desktop | 37.2% | 76% | 79% | 71% |

Mobile underperforms desktop at every step; biggest gap (20pp) at first action.

## Decision-grade insights
1. The signup form is the highest-volume lever — even +2pp here = ~2,000 extra weekly signups
2. The mobile first-action gap is the highest-leverage post-signup issue
3. The 18-min median wait before first action suggests users are confused, not lazy — likely a UX issue
```

---

## Example 2: Non-strict feature adoption

**User prompt:** "How many users adopted features A, B, and C in their first 30 days?"

**Skill response:**

> Non-strict funnel. User must do all three features within 30 days of signup, in any order.
>
> Output:
> | Combo | Users | % of cohort |
> |---|---|---|
> | None | 4,200 | 42% |
> | A only | 1,800 | 18% |
> | B only | 1,100 | 11% |
> | C only | 600 | 6% |
> | A + B | 1,200 | 12% |
> | A + C | 500 | 5% |
> | B + C | 300 | 3% |
> | A + B + C | 300 | 3% |
>
> Top patterns:
> - 42% of new users don't touch any of the three core features. Strong signal that onboarding doesn't surface them.
> - A is by far the most-discovered (35% touched it). B and C trail.
> - The "all three" rate (3%) is the activation gold standard but very rare. Consider whether the bar is realistic.

---

## Example 3: Drop-off where the issue is a bug

**User prompt:** "We saw a 15pp drop in our checkout funnel last Tuesday. What happened?"

**Skill response (process):**

> 1. Confirm the drop is real (not a data pipeline issue) — check upstream event volumes
> 2. Identify which step shows the drop — likely a single step, not the whole funnel
> 3. Segment by:
>    - Device → if mobile-specific, it's likely a layout bug
>    - Browser → if Chrome-specific, JS error
>    - Geography → if a single region, CDN issue
>    - Time-of-day → if specific hours, server load
> 4. Cross-reference with engineering deploys for that day
>
> Output a "drop-off forensics" readout with the most likely root cause and the evidence. Recommend immediate hotfix vs scheduled fix based on revenue impact.
