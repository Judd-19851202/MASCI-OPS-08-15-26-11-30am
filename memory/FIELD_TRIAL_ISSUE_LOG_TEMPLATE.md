# FIELD TRIAL — ISSUE LOG TEMPLATE
## Track issues across the 3-foreman × 3-day trial

**Trial**: Excavation Operations · Human Field Validation
**Trial lead**: ____________________
**Trial dates**: __________________________

---

## SEVERITY RUBRIC

| Severity | Definition | Trial action |
|---|---|---|
| **P0** | Production-blocking · foreman cannot complete a workflow at all OR wrong data submitted OR critical safety bug | STOP trial · escalate to Safety lead immediately · do NOT continue until resolved or authorized to bypass |
| **P1** | Critical confusion / visible error / functional bug that does not block the workflow but seriously degrades it | Continue trial · log fully · address in post-trial verdict |
| **P2** | Minor UI / wording / translation / latency issue | Continue trial · log briefly · post-trial polish |
| **P3** | Cosmetic preference / nice-to-have | Continue trial · log for future backlog |

---

## ISSUE LOG · COLUMNAR FORMAT

Copy this row template for every issue. Submit one issue per row.

```
ISSUE_ID,DATE,DAY,FOREMAN,JOB,DEVICE,WORKFLOW,SEVERITY,TITLE,EXACT_QUOTE,SCREENSHOT_REF,STATUS,RESOLUTION
```

### EXAMPLE ENTRY (do not delete — illustrative only)

```
FT-2026-001,2026-02-15,1,FM-A Carlos Mendoza,FT-JOB-1001,iPhone 14,W6 Trench Box Linkage,P1,"Asset list does not show TB-03 when it should","I can see TB-03 is in the yard but it's not in the list here. I have to type it.",ft-2026-001.png,OPEN,
```

---

## TEMPLATE — ONE PER ISSUE

### Issue ID: FT-2026-___
* **Date**: __________
* **Day** (1·2·3): ____
* **Foreman**: ____________________
* **Job**: __________________________
* **Device**: __________________________ (model / OS / browser)
* **Workflow**: ____________________ (one of W1–W15 from observer checklist)
* **Severity**: P0 / P1 / P2 / P3 (circle)
* **Title** (one line): ____________________________________________
* **Foreman's exact words**:
  > "                                                                                                                "
  > "                                                                                                                "
* **What happened (observer's account)**:
  > 
* **Reproduction steps** (numbered):
  1. 
  2. 
  3. 
* **Expected vs actual**:
  * Expected:
  * Actual:
* **Screenshot reference(s)**: _______________________
* **Frequency**: once / sometimes / every time
* **Workaround used by foreman**: ____________________
* **Status**: OPEN / TRIAGED / IN PROGRESS / RESOLVED / WON'T FIX / NEEDS PRODUCT INPUT
* **Resolution / Notes**:
  > 

---

## ROLL-UP (filled at trial end)

| Severity | Count |
|---|---|
| P0 (blocker) | _____ |
| P1 (critical) | _____ |
| P2 (medium) | _____ |
| P3 (low) | _____ |
| Total | _____ |

If **P0 > 0** → trial verdict is **NOT READY** until resolved.
If **P1 > 2** → trial verdict is **CONDITIONALLY READY** at best.
If **P0 = 0 AND P1 ≤ 2 AND foremen pass all 14 success criteria** → **PROVEN** is admissible.

---

## CROSS-REFERENCE TO PRE-TRIAL ISSUES

These were the two issues open BEFORE the trial started:

* **FT-D1-001** · Mobile horizontal-overflow metric · CLOSED as headless artifact pre-trial. Re-verify on physical device during trial. **If real overflow observed → reopen as P1.**
* **FT-D1-002** · Spanish Emergency Excavation translation gap · FIXED pre-trial. Re-verify during ES foreman trial. **If still untranslated → reopen as P2.**

---

## SUBMISSION

Trial lead compiles all issue rows into `/app/memory/FIELD_TRIAL_ISSUE_LOG_<YYYY-MM-DD>.csv` at trial end.
