# Stakeholder Readout — Examples

## Example 1: Successful A/B test

```markdown
# Checkout Button Color Test — Final Readout

**Author:** Priya R.  
**Audience:** Product, Growth Leadership  
**Date:** 2026-04-18  
**Status:** Final

---

## TL;DR
The green checkout button increased completion by 7.5% (+0.4 to +1.4pp 95% CI, strong evidence). **Recommend shipping to 100%.**

**Confidence:** Strong (p < 0.001 on 33k users over 14 days, all guardrails passed).

---

## Context
- **Question:** Does changing the checkout button from blue to green improve completion rate?
- **Why now:** Designer hypothesized higher contrast would reduce hesitation; cheap to test.
- **What we did:** 14-day A/B test with 50/50 user-level randomization. Primary metric: checkout completion rate. Sample reached pre-registered target.

---

## Findings

### Finding 1: Completion rate improved 7.5% relative (0.9pp absolute)
Treatment: 12.9% completion vs control 12.0%. Lift: +0.9pp [95% CI: +0.4pp, +1.4pp], p = 0.0008.

### Finding 2: No negative impact on revenue or quality
Revenue per user up 1.1% (not significant but directionally positive). Page error rate flat. p95 latency unchanged.

### Finding 3: Effect consistent across mobile and desktop
Mobile: +0.7pp, Desktop: +1.1pp. Both significant, neither dominant.

---

## Decision

**Recommended:** Ramp green button to 100% of traffic over 7 days.

**Owner:** Eng (engineering manager: Jake L.)

**Timeline:** Begin ramp 2026-04-22, complete by 2026-04-29.

**Why this and not alternatives:**
- Considered: re-test with longer window. Rejected because effect is consistent across all 14 days; CI is tight.
- Considered: hold for more guardrail data. Rejected because no guardrail breach detected in 14 days.

---

## Caveats & next steps

### What we don't know
- Long-term effect: do users desensitize? Plan a 30-day retention check.
- Mobile-specific accessibility: contrast meets WCAG AA but not AAA. Accessibility team should confirm.

### Next steps
1. **Ramp to 100%** — @jake.l — by 2026-04-29
2. **30-day post-ramp retention check** — @priya.r — by 2026-06-01
3. **WCAG AAA review** — @design.access — by 2026-05-15
```

---

## Example 2: Inconclusive result

```markdown
# Pricing Page Redesign Test — Final Readout

**Author:** Marco T.  
**Audience:** Growth Leadership  
**Date:** 2026-04-18  
**Status:** Final

---

## TL;DR
The pricing page redesign did not produce a measurable effect on enterprise conversion — but we can't rule out a real effect smaller than ~25% relative. **Recommend killing this variant; if we want a definitive answer, we need to redesign the test.**

**Confidence:** Inconclusive (underpowered for the actual effect size).

---

## Context
- **Question:** Does the redesigned pricing page increase enterprise-tier conversion?
- **Why now:** Sales feedback that current page is "confusing."
- **What we did:** 28-day A/B test, 50/50 visitor split. Primary: enterprise conversion rate. Baseline 0.3%, MDE 25% relative.

---

## Findings

### Finding 1: No detectable effect on enterprise conversion
Treatment: 0.32% vs control: 0.29%. Lift: +0.03pp [-0.05pp, +0.11pp]. p = 0.42.

### Finding 2: Test was underpowered for typical-sized effects
Even a 50% relative lift would have required >200 days at current traffic. We chose 28 days; sample reached 8,400 visitors per arm vs ~16,500 needed.

### Finding 3: Proxy metric (compare-plans clicks) showed +12%
Compare-plans CTR rose from 4.1% → 4.6%. Significant at p = 0.04. Suggests redesign increases intent, but conversion rate is so low we can't detect downstream impact in 28 days.

---

## Decision

**Recommended:** Kill the test, do NOT roll out based on this data.

**Owner:** @marco.t (analysis); @design (design lead)

**Timeline:** This week.

**Why this and not alternatives:**
- Considered: ship based on proxy metric. Rejected because conversion rate is the metric that matters; proxy can move without conversion moving.
- Considered: extend the test. Rejected because runtime would need to be 6+ months. Pricing page changes likely needed before then.

---

## Caveats & next steps

### What we don't know
- True effect on enterprise conversion (within range -0.05pp to +0.11pp; could be slight up or slight down)
- Whether the +12% compare-plans CTR converts further down the funnel

### Next steps
1. **Re-design test using a higher-base-rate proxy metric** — @marco.t — by 2026-05-01
2. **Identify alternative measurement strategy** (matched-pair geo test? sales-rep feedback?) — @marco.t + @sales.ops — by 2026-05-15
3. **In the meantime: hold pricing page changes** — @design — ongoing
```

---

## Example 3: Surprising negative result

```markdown
# New Recommendation Algorithm — Final Readout

**Author:** Aleksandra K.  
**Audience:** ML, Product, Revenue Leadership  
**Date:** 2026-04-18  
**Status:** Final

---

## TL;DR
The new recommendation algorithm increased clicks by 12% but **reduced revenue per user by 3.1%** — it drives engagement to lower-value items. **Recommend killing this variant and revisiting model objective.**

**Confidence:** Strong (p < 0.001 on both metrics, 21 days, 180k users).

---

## Context
- **Question:** Does the new collaborative-filtering model outperform the existing content-based recommendations?
- **Why now:** ML team's new model showed +15% CTR offline; this validates that gain online.
- **What we did:** 21-day A/B test, 50/50 user-level. Primary: revenue per user; secondary: recommendation CTR.

---

## Findings

### Finding 1: Recommendation CTR improved 12% — as predicted
Treatment users clicked recommendations 12% more often (16.4% vs 14.6%, p < 0.001). Matches the offline evaluation.

### Finding 2: But revenue per user dropped 3.1%
Treatment users generated $42.10 vs control $43.45 (95% CI on lift: -5.4% to -0.8%). Effect is small but statistically real and economically meaningful at scale (~$8M annualized loss if shipped).

### Finding 3: The mechanism is high-AOV cannibalization
The new model recommends more relevant but cheaper items. Average order value dropped from $58 to $52. Order volume was flat. So: more clicks, but the wrong clicks for revenue.

---

## Decision

**Recommended:** Kill the variant. Do not ship.

**Owner:** @aleksandra.k (analysis); @ml-recs-team (model owner)

**Timeline:** Immediate — turn off test today.

**Why this and not alternatives:**
- Considered: ship despite revenue impact ("engagement matters more long-term"). Rejected because long-term studies in similar tests showed engagement gains decay; revenue impact persists.
- Considered: ramp slowly to monitor. Rejected because the negative revenue impact is already at 95% CI; ramping won't change the answer.

---

## Caveats & next steps

### What we don't know
- Whether retraining the model with a revenue-weighted objective recovers the win.
- Long-term effect of higher engagement (we tested 21 days; not enough to see compounding effects).

### Next steps
1. **Kill test** — @ml-platform — today
2. **Re-train with revenue-weighted objective** — @ml-recs-team — by 2026-05-15
3. **Re-test new model with same primary metric** — @aleksandra.k — by 2026-06-01

---

## Appendix
- Full statistical methods, model architecture, segment cuts available in `/notebooks/recs_test_v2.ipynb`
- Discussion of why offline CTR overpredicted online: <thread link>
```
