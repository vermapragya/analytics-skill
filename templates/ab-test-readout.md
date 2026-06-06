# Experiment Readout: <name>

**Author:** <name>  
**Audience:** <PM / Exec / Eng / Mixed>  
**Date:** <YYYY-MM-DD>  
**Status:** <Final | Draft for review>

---

## TL;DR
<One sentence: finding + recommendation + confidence>

**Recommendation:** <Ship | Hold | Kill | Inconclusive>  
**Confidence:** <Strong | Moderate | Directional>

---

## Context
- **Question:** <decision this informs>
- **Why now:** <trigger>
- **What we did:** <method, 1 paragraph>

---

## Sample Ratio Mismatch
| Variant | Expected | Observed | Delta |
|---|---|---|---|
| Control | <%> | <%> | <%> |
| Treatment | <%> | <%> | <%> |

χ² p-value: <value> — **<PASS|FAIL>**

> If FAIL, stop here. Do not interpret primary metric.

---

## Primary metric: <name>
| Variant | N | Value | 95% CI |
|---|---|---|---|
| Control | <N> | <val> | [<low>, <high>] |
| Treatment | <N> | <val> | [<low>, <high>] |

- Absolute lift: <X> [<low>, <high>]
- Relative lift: <X%> [<low>, <high>]
- Test: <z-test / t-test / bootstrap>, p = <value>

---

## Guardrails
| Metric | Threshold | Result | Status |
|---|---|---|---|
| <metric> | <threshold> | <delta + CI> | <PASS|WATCH|FAIL> |

---

## Subgroup analysis (pre-specified only)
<table or "No pre-specified subgroups">

---

## Decision

**Recommended:** <specific action>  
**Owner:** <name>  
**Timeline:** <date>

**Why this and not alternatives:**
- Considered: <alt 1> — rejected because <reason>
- Considered: <alt 2> — rejected because <reason>

---

## Caveats & next steps

### What we don't know
- <ordered by decision impact>

### Next steps
1. **<action>** — @<owner> — by <date>
2. **<action>** — @<owner> — by <date>
