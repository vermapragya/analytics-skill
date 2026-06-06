# Data Quality Audit — Examples

## Example 1: Clean PASS

```markdown
# Data Quality Audit: analytics.events.fct_orders

## TL;DR
**Status: PASS**

All 7 checks passed. Table is safe to use.

## Checks
| Check | Result | Status | Notes |
|---|---|---|---|
| Row count | 12,418,902 | PASS | |
| Freshness | 1.8h since latest order_at | PASS | SLA: 6h |
| PK uniqueness | 0 dupes on order_id | PASS | |
| Critical nulls | 0 nulls in (order_id, user_id, order_at, amount) | PASS | |
| Schema | 23 cols, matches docs v3 | PASS | |
| Value distributions | amount p99 = $487 (vs $510 last week, OK); 3 currencies (USD, EUR, GBP) | PASS | |
| Referential integrity | 0 orphan user_id vs dim_users (12.4M checked) | PASS | |
| Time-series gaps | No missing days; max daily delta +14% | PASS | |

## Issues found
None.

## Recommended actions
- Safe to use for analysis.
```

---

## Example 2: WARN — non-critical drift

```markdown
# Data Quality Audit: analytics.events.fct_sessions

## TL;DR
**Status: WARN — proceed with caveats**

Schema drift detected (1 new column), and `device_type` null rate increased.

## Checks
| Check | Result | Status | Notes |
|---|---|---|---|
| Row count | 8,302,114 | PASS | |
| Freshness | 0.5h since latest | PASS | |
| PK uniqueness | 0 dupes on session_id | PASS | |
| Critical nulls | 0 in (session_id, user_id, session_started_at) | PASS | |
| Schema | NEW: `device_os_version` column added 2026-04-10 | WARN | not in docs |
| Value distributions | device_type: ios (41%), android (38%), web (16%), NULL (5.2%) | WARN | NULL was 0.8% prior month |
| Referential integrity | 0.02% orphan user_id | PASS | |
| Time-series gaps | No missing days | PASS | |

## Issues found
1. **WARN: device_type null rate jumped from 0.8% → 5.2% on 2026-04-10**, same date as new `device_os_version` column. Likely SDK update changed event schema.
2. **WARN: undocumented column `device_os_version` appeared 2026-04-10.**

## Recommended actions
- Coerce null `device_type` to 'unknown' in downstream models
- Update schema docs to include `device_os_version`
- Notify SDK team to confirm intentional change
- Audit downstream cohort/funnel analyses that filter on device_type

## Caveats
- Last 1h of data may show different distribution due to streaming lag
```

---

## Example 3: FAIL — block usage

```markdown
# Data Quality Audit: raw.events.product_events

## TL;DR
**Status: FAIL — do not use this table until issues are resolved**

Duplicate primary keys detected on 2026-04-13. Pipeline likely double-loaded.

## Checks
| Check | Result | Status | Notes |
|---|---|---|---|
| Row count | 47,892,310 | PASS | |
| Freshness | 14h since latest | PASS | SLA: 24h |
| PK uniqueness | **142,901 dupe rows** on event_id | **FAIL** | |
| Critical nulls | 0 in (event_id, user_id, event_at) | PASS | |
| Schema | matches docs | PASS | |
| Value distributions | Looks normal | PASS | |
| Referential integrity | (not run — abort on PK fail) | — | |
| Time-series gaps | 2026-04-13 has 2.4× normal row count | **FAIL** | matches dupe count |

## Issues found
1. **FAIL: 142,901 duplicate event_id rows, all from 2026-04-13.** Suggests pipeline re-ran without idempotency.
2. **FAIL: 2026-04-13 row count is 2.4× the trailing 14-day average.**

## Recommended actions
- **BLOCK any analysis using data from 2026-04-13 to today.**
- Notify data engineering: `pipeline_log` for 2026-04-13 likely shows duplicate runs.
- Options to remediate:
  - Dedupe via `qualify row_number() over (partition by event_id order by ingested_at desc) = 1`
  - Re-run pipeline with idempotent insert

## Blast radius
Models depending on `raw.events.product_events`:
- `fct_user_daily_activity` (24h refresh) — corrupted
- `fct_user_engagement_30d` — partially corrupted (1 day affected)
- Dashboards: 8 product dashboards show inflated DAU since 2026-04-13
```
