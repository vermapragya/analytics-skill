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

## Visualizations

### Waterfall — end-to-end conversion
| Step | Users | % of step 1 | Lost since prev |
|---|---|---|---|
| Landing | 102,400 | 100.0% | — |
| Signup | 31,840 | 31.1% | −70,560 |
| Email verify | 22,288 | 21.8% | −9,552 |
| Profile complete | 16,716 | 16.3% | −5,572 |
| First action | 10,030 | 9.8% | −6,686 |

### Step-to-step conversion
| Transition | Step CR | Users lost | Health |
|---|---|---|---|
| Landing → Signup | 31.1% | 70,560 | 🔴 red |
| Signup → Email verify | 70.0% | 9,552 | 🟡 amber |
| Email verify → Profile complete | 75.0% | 5,572 | 🟡 amber |
| Profile complete → First action | 60.0% | 6,686 | 🟡 amber |

### Monthly cohort heatmap (% of cohort reaching each step)
| Cohort (n) | Landing | Signup | Verify | Profile | First action |
|---|---|---|---|---|---|
| 2026-01 (n=24,300) | 100% | 33% | 24% | 18% | 11% |
| 2026-02 (n=27,800) | 100% | 32% | 23% | 17% | 10% |
| 2026-03 (n=29,100) | 100% | 30% | 21% | 15% |  9% |
| 2026-04 (n=21,200) | 100% | 28% | 20% | 14% |  8% |

**Trend:** Landing → Signup has dropped from 33% → 28% over 4 cohorts (−5pp). Every downstream step is also degrading roughly proportionally — suggests the issue is upstream at signup, not in later steps.

## Biggest drop-offs
1. Landing → Signup: -68.9pp (largest absolute) **and degrading over time** (see cohort heatmap)
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
