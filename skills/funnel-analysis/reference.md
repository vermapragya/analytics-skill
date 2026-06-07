# Funnel Analysis — Reference

## Strict vs non-strict funnels

### Strict (sequential)

```sql
with step1 as (select user_id, min(event_at) as t1 from events where event_name = 'landing' group by user_id),
step2 as (
    select s1.user_id, min(e.event_at) as t2
    from step1 s1
    join events e on e.user_id = s1.user_id
    where e.event_name = 'signup'
      and e.event_at > s1.t1
      and e.event_at < dateadd('hour', 1, s1.t1)
    group by s1.user_id
),
...
```

Each step depends on the previous step's timestamp. Event must occur **after** the prior step within the conversion window.

### Non-strict (any order)

```sql
select
    count(distinct case when event_name = 'a' then user_id end) as did_a,
    count(distinct case when event_name = 'b' then user_id end) as did_b,
    count(distinct case when event_name = 'c' then user_id end) as did_c,
    count(distinct case when event_name in ('a','b','c')
        and user_id in (subquery for users with all 3)
    then user_id end) as did_all
from events;
```

Use when measuring feature adoption combinations rather than a flow.

## Conversion window pitfalls

Choosing too long a window:
- Inflates conversion to artificial highs
- Hides drop-off (users still "converting" in week 4 dilute the signal)
- Makes the funnel insensitive to product changes

Choosing too short a window:
- Misses legitimately converting users
- Penalizes slow-but-real conversion paths

**Default heuristic:** match the window to the natural user intent timeframe:
- Single session (30 min) — fast flows like checkout, signup
- Same day (24h) — onboarding requiring email check, etc.
- Week — multi-touch purchase or activation
- Month — sales-led / enterprise flows

## Time-between-steps measurement

```sql
select
    median(datediff('second', t1, t2)) as median_s_step1_to_step2,
    avg(datediff('second', t1, t2))    as avg_s_step1_to_step2,
    percentile_cont(0.95) within group (order by datediff('second', t1, t2)) as p95_s
from funnel_table;
```

`p50` is more useful than `avg` because funnel times are heavily right-skewed.

## Drop-off diagnosis decision tree

```
Is the drop-off concentrated in a segment?
├── Yes
│   ├── Is the segment a meaningful share (> 10%)? → fix the segment
│   └── No → segment-specific bug, lower priority
└── No (uniform across segments)
    ├── Is the step technically reliable? (no errors, fast load)
    │   ├── No → engineering fix
    │   └── Yes → UX/design fix
```

## Canonical visualizations

Every funnel readout should include these three charts. Generate them with `scripts/visualize_funnel.py`. When responding inline (chat-only, no images), produce the markdown-table fallbacks shown below.

### 1. Waterfall — end-to-end conversion from step 1

**What it shows:** users remaining at each step (solid bar) plus the cumulative loss since the previous step (gray overlay). Reads top-down through the funnel and makes the absolute size of each drop-off obvious.

**Conventions:**
- Headline metric in title: end-to-end CR + absolute counts (`step 1: N → final: M`).
- Each bar annotated with `count` and `% of step 1`.
- Gray overlay annotated with `−lost` (the absolute users lost since the previous step).
- Y-axis = users (linear). Do **not** start at zero only if you also annotate the truncation.

**Inline markdown fallback (when you can't render a PNG):**

```markdown
### Waterfall (step 1 → each step)
| Step | Users | % of step 1 | Lost since prev |
|---|---|---|---|
| Landing | 100,000 | 100.0% | — |
| Signup | 32,000 | 32.0% | −68,000 |
| Email verify | 22,400 | 22.4% | −9,600 |
| Profile complete | 16,800 | 16.8% | −5,600 |
| First action | 10,080 | 10.1% | −6,720 |
```

### 2. Step-to-step conversion

**What it shows:** the per-transition conversion rate (step N → step N+1). This is the *marginal* rate — what the waterfall hides because it's compounded. The worst transition is your biggest leverage point.

**Conventions:**
- Horizontal bar chart, one bar per transition.
- Color thresholds: green ≥ 80%, amber ≥ 50%, red < 50%.
- Label each bar with both the rate and the absolute users lost.
- Sort in funnel order (not by rate) — preserves the flow.

**Inline markdown fallback:**

```markdown
### Step-to-step conversion
| Transition | Step CR | Users lost | Health |
|---|---|---|---|
| Landing → Signup | 32.0% | 68,000 | 🔴 red |
| Signup → Email verify | 70.0% | 9,600 | 🟡 amber |
| Email verify → Profile complete | 75.0% | 5,600 | 🟡 amber |
| Profile complete → First action | 60.0% | 6,720 | 🟡 amber |
```

(If emoji aren't desired, use plain text: `low / medium / high`.)

### 3. Monthly cohort heatmap

**What it shows:** rows = cohort (signup month), columns = funnel step, cell = % of that cohort that reached the step. Reveals whether the funnel is **improving, flat, or degrading over time** — something the static funnel can't tell you.

**Conventions:**
- Cohort definition = month of step-1 event (consistent across rows).
- Cell value = end-to-end CR (% of cohort reaching that step), not step CR. End-to-end is comparable across columns; step CR is not.
- Row label includes cohort size `n=…` so reader can spot small/noisy cohorts.
- Sequential color scale (light → dark) keyed to 0–100%.
- Annotate every cell with the % (no hover required).
- Sort cohorts chronologically (oldest at top).

**How to read it:**
- Reading **down a column** shows trend over time at that step. A column going lighter = degradation.
- Reading **across a row** shows the funnel shape for one cohort.
- A diagonal pattern (later cohorts lighter at later steps) = a leak introduced recently.

**Inline markdown fallback:**

```markdown
### Cohort heatmap (% of cohort reaching each step)
| Cohort (n) | Landing | Signup | Verify | Profile | First action |
|---|---|---|---|---|---|
| 2025-12 (n=24,300) | 100% | 33% | 24% | 18% | 11% |
| 2026-01 (n=27,800) | 100% | 32% | 23% | 17% | 10% |
| 2026-02 (n=29,100) | 100% | 30% | 21% | 15% |  9% |
| 2026-03 (n=18,800) | 100% | 28% | 20% | 14% |  8% |
```

Then call out the trend in prose (e.g. "Signup CR has dropped 5pp over 4 cohorts — investigate the landing page changes shipped in late January.").

### Other useful but optional visualizations

- **Sankey diagram**: shows where users *go* after dropping off (e.g. did they bounce, or do a different action?). Most useful for non-strict funnels with multiple downstream paths.
- **Time-to-convert histogram**: distribution of step N → N+1 latency. Useful when a step is gated by an external action (email, payment).

Avoid the literal "funnel" trapezoid — it's harder to read than a bar chart and the visual width carries no information beyond the count.

## Snowflake template

```sql
-- 4-step strict funnel with same-session window (30 min between steps)
with base as (
    select user_id, event_name, event_at
    from events
    where event_at >= dateadd('day', -14, current_date)
      and event_at <  current_date
),
s1 as (
    select user_id, min(event_at) as t1
    from base where event_name = 'landing'
    group by user_id
),
s2 as (
    select s1.user_id, min(b.event_at) as t2
    from s1 join base b on b.user_id = s1.user_id
    where b.event_name = 'signup'
      and b.event_at >= s1.t1
      and b.event_at <= dateadd('minute', 30, s1.t1)
    group by s1.user_id
),
s3 as (
    select s2.user_id, min(b.event_at) as t3
    from s2 join base b on b.user_id = s2.user_id
    where b.event_name = 'email_verify'
      and b.event_at >= s2.t2
      and b.event_at <= dateadd('day', 1, s2.t2)
    group by s2.user_id
),
s4 as (
    select s3.user_id, min(b.event_at) as t4
    from s3 join base b on b.user_id = s3.user_id
    where b.event_name = 'first_action'
      and b.event_at >= s3.t3
      and b.event_at <= dateadd('day', 7, s3.t3)
    group by s3.user_id
)
select
    (select count(*) from s1) as n_landing,
    (select count(*) from s2) as n_signup,
    (select count(*) from s3) as n_verify,
    (select count(*) from s4) as n_first_action;
```

## Pre-aggregated event store optimization

If running funnels frequently on large data, pre-compute a user-event matrix:

```sql
create or replace table user_first_event_times as
select
    user_id,
    min(case when event_name = 'landing' then event_at end)      as t_landing,
    min(case when event_name = 'signup' then event_at end)       as t_signup,
    min(case when event_name = 'email_verify' then event_at end) as t_verify,
    min(case when event_name = 'first_action' then event_at end) as t_first
from events
group by user_id;
```

Then funnel queries become single-table scans with `where t_signup is not null and t_signup > t_landing and ...`.
