# FIELD TRIAL — FINAL VERDICT TEMPLATE
## Excavation Operations · Human Field Validation

**Trial dates**: __________ to __________
**Trial lead**: ____________________
**Foremen**: _______________________________________ (3 names)
**Jobs**: ____________________________________________ (3 jobs)

---

## VERDICT FRAMEWORK

The verdict must be **one of these three**. Do not invent a fourth.

| Verdict | Definition | Trigger |
|---|---|---|
| **NOT READY** | Critical defects observed · foremen cannot complete workflows · or wrong data is being submitted · or safety risk is increased | P0 > 0 · OR · ≥1 foreman cannot complete the workflow loop · OR · false-positive or false-negative OSHA flag observed |
| **CONDITIONALLY READY** | Workflows completable · most success criteria met · 1–2 notable issues that require targeted fix but do not block deployment | P0 = 0 · P1 ≤ 2 · 12+ of 14 success criteria met |
| **PROVEN** | Field-verified · foremen would use it again · superintendent + safety satisfied · zero P0 / zero P1 critical defects | All 14 success criteria met · zero P0 / zero P1 · all 3 foremen answer Q7 ("would you use again?") with YES (or qualified YES with documented condition) |

---

## SUCCESS CRITERIA — CHECKLIST

Tick every criterion that is independently observed during the trial. Anything ambiguous → leave blank.

- [ ] **1.** Foremen complete workflows without major help (no more than 2 questions per foreman per day).
- [ ] **2.** No critical mobile issues (no broken layouts, no submissions blocked by mobile UI).
- [ ] **3.** Daily Report normal workflow remains unaffected (excavation = NO behaves exactly like pre-trial).
- [ ] **4.** Daily Report + Excavation linkage works (excavation = YES requires Create/Link before submit).
- [ ] **5.** Excavation record creation works on first try.
- [ ] **6.** Trench box selection works (asset visible, selectable, reflected in record).
- [ ] **7.** Road plate selection works (asset visible, selectable, reflected in record).
- [ ] **8.** Competent Person validation works (only designated CPs in picker; undesignated triggers flag).
- [ ] **9.** OSHA flags fire correctly (zero false positives, zero false negatives during trial).
- [ ] **10.** TRENCH_BOX_DEPTH soft-gate works (action required · acknowledgement downgrades · never blocks).
- [ ] **11.** ROAD_PLATE_DIMENSION sanity check works.
- [ ] **12.** Reinspection request works (no Safety approval; all 7 reasons available; Safety + Super notified).
- [ ] **13.** **Safety can review in under 60 seconds** (timed test on Day 3 by trial lead).
- [ ] **14.** **Superintendent can identify open issues in under 30 seconds** (timed test on Day 3 by trial lead).

**Foreman Q7 ("would you use this again?")** answers:
* Foreman A: YES / QUALIFIED YES / NO · condition: ____________________
* Foreman B: YES / QUALIFIED YES / NO · condition: ____________________
* Foreman C: YES / QUALIFIED YES / NO · condition: ____________________

---

## TIMED AUDITS — REQUIRED EVIDENCE

### Superintendent · 30-second audit
Trial lead times the Superintendent answering all 7 questions from the Oversight chip row. **Stop the clock at 30 seconds.**

| Question | Answered? | Time |
|---|---|---|
| How many excavations are open? | Y/N | _____ s |
| Which need reinspection? | Y/N | _____ s |
| Which have no CP? | Y/N | _____ s |
| Which have no protective system? | Y/N | _____ s |
| Which use trench boxes? | Y/N | _____ s |
| Which use road plates? | Y/N | _____ s |
| Which have OSHA action flags? | Y/N | _____ s |
| **Total elapsed** | | _____ s |

PASS if all 7 answered in < 30 s.

### Safety · 60-second audit
Same procedure for Safety's 7 questions.

| Question | Answered? | Time |
|---|---|---|
| What excavation risks today? | Y/N | _____ s |
| What inspections/reinspections required? | Y/N | _____ s |
| What CP issues? | Y/N | _____ s |
| What trench box rating issues? | Y/N | _____ s |
| What road plate issues? | Y/N | _____ s |
| What records need review? | Y/N | _____ s |
| What needs coaching? | Y/N | _____ s |
| **Total elapsed** | | _____ s |

PASS if all 7 answered in < 60 s.

---

## ISSUE ROLL-UP

| Severity | Count | Examples (IDs) |
|---|---|---|
| P0 | _____ | __________________________ |
| P1 | _____ | __________________________ |
| P2 | _____ | __________________________ |
| P3 | _____ | __________________________ |

---

## VERDICT MATRIX

| Condition | Verdict |
|---|---|
| ≥1 P0 OR any foreman cannot complete the workflow loop OR false flag observed | **NOT READY** |
| P0 = 0 AND P1 ≤ 2 AND 12+ of 14 success criteria met AND foreman Q7 majority YES | **CONDITIONALLY READY** |
| P0 = 0 AND P1 = 0 AND all 14 success criteria met AND 3/3 foreman Q7 = YES (or qualified YES with documented & acceptable condition) | **PROVEN** |

---

## FINAL VERDICT

# This trial concludes with:

[ ] **NOT READY**
[ ] **CONDITIONALLY READY**
[ ] **PROVEN**

---

## SIGNATURES

* Trial lead: ____________________   Date: __________
* Safety lead: ____________________   Date: __________
* Superintendent: ____________________   Date: __________

---

## NEXT STEP

| Verdict | Next step |
|---|---|
| NOT READY | Halt deployment. File targeted fix sprint per top issue. Re-run trial. |
| CONDITIONALLY READY | Deploy to limited rollout. Address open P1s in a targeted sprint (max 2-week window). Re-run trial after fix. |
| PROVEN | Deploy. Move on to Phase 11 Final Certification. |
