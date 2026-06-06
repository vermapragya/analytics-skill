# Model Readout: <model name / problem>

**Author:** <name>  
**Date:** <YYYY-MM-DD>  
**Status:** <Final | Draft>

---

## TL;DR
<One sentence: model performance + business impact + recommendation>

---

## Setup
- **Outcome:** <target variable + definition>
- **Observation unit:** <user / session / opportunity>
- **Sample:** <N_train> train, <N_test> test (split: <temporal at YYYY-MM-DD | random>)
- **Features:** <count and brief categories>

---

## Performance (test set)
| Metric | Value | Notes |
|---|---|---|
| AUC / R² | <val> | |
| PR-AUC / RMSE | <val> | |
| Calibration | <good / drift> | |
| Threshold | <val> | precision <X>, recall <Y> |

---

## Top drivers (by effect)
| Feature | Effect | 95% CI | Interpretation |
|---|---|---|---|
| <feature> | <coef / HR / odds ratio> | <CI> | <plain English> |

---

## Operational impact
- Flag rate: <X%> of population
- Precision @ threshold: <X%>
- Estimated business impact: <e.g., $X annualized>

---

## Caveats
- <ordered by decision impact>
- <leakage risk addressed: how?>
- <feature availability in production scoring?>
- <calibration drift schedule?>

---

## Decision

**Recommendation:** <Deploy | Iterate | Park>

**Owner:** <name>

**Timeline:** <date>

---

## Next steps
1. **<action>** — @<owner> — by <date>
