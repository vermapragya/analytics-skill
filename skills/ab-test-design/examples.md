# A/B Test Design — Examples

## Example 1: Checkout button color change

**User prompt:** "We want to test changing the checkout button from blue to green. How big should the test be?"

**Skill response:**

```markdown
# Experiment Pre-Registration: Checkout button color (blue → green)

## Hypothesis
Changing the checkout button from blue to green will increase checkout
completion rate by at least 1pp (from 12% to 13%), because higher color
contrast against the page background should reduce visual friction.

## Variants
- Control: Blue button (current)
- Treatment: Green button (#22c55e)

## Randomization
- Unit: user_id
- Allocation: 50/50

## Metrics
- Primary: checkout_completion_rate
  (count of distinct user_id with checkout_completed_at IS NOT NULL
   / count of distinct user_id who reached checkout page)
- Secondary: revenue_per_user (7-day window)
- Guardrails:
  - SRM check (χ² p > 0.001)
  - Page error rate (not up > 0.5pp)
  - p95 page latency (not up > 100ms)

## Power
- Baseline: 12.0%
- MDE: 1pp absolute (relative: ~8.3%)
- Alpha: 0.05 two-sided
- Power: 0.80
- Required sample per arm: ~16,500 users
- Expected daily exposure per arm: ~2,500 users
- Minimum runtime: 14 days

## Stopping rules
- No peeking before day 14
- Stop early only if SRM breached or error rate up > 1pp

## Analysis plan
- Test: two-proportion z-test
- Subgroups (pre-specified): new vs returning users, mobile vs desktop
```

---

## Example 2: Recommendation algorithm with network effects

**User prompt:** "We want to A/B test a new recommendation algorithm on our marketplace."

**Skill response (key callouts):**

> Network effects warning: user-level randomization will leak treatment because users in control will see items influenced by treatment users' behavior. Recommend cluster randomization by geo (city) or use a switchback design (alternating control/treatment by hour).
>
> Suggested design:
> - Unit: city-day
> - 20 cities, randomly assigned 10 to treatment, 10 to control
> - Runtime: 28 days (covers two weekly cycles, allows for adjustment effects)
> - Analysis: difference-in-differences with city fixed effects
>
> Note: this is closer to a quasi-experiment. Use the `causal-inference` skill alongside this one for analysis.

---

## Example 3: Rare event (high-value purchase conversion)

**User prompt:** "Test a new pricing page. Conversion to enterprise plan is the metric. Current rate ~0.3%."

**Skill response (key callouts):**

> Baseline of 0.3% means even a 20% relative lift (to 0.36%) requires ~130k users per arm for 80% power. At 1,000 enterprise-eligible visitors per day, that's 260 days — unrealistic.
>
> Recommend one of:
> 1. Use a proxy metric: "added to comparison cart" instead of "purchased enterprise" — likely 10-20x higher base rate
> 2. Increase MDE to 50% relative (need to confirm with stakeholders this is the smallest effect worth shipping)
> 3. Switch to causal-inference with a longer pre/post window
>
> Default recommendation: ship the proxy-metric design now, with enterprise conversion as a secondary (underpowered, directional only).
