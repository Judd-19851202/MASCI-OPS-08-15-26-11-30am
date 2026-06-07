# FIELD TRIAL EXECUTION PLAN
## Excavation Operations · Final Gate to PROVEN

**Status**: NOT STARTED · ready to run.
**Authorization**: OMEGA Directive FV-7.1A
**Pre-requisite**: ✅ Asset metadata backfill complete · ✅ FV-7 rules verified end-to-end against real inventory.

---

## OBJECTIVE

Move Excavation Operations from **TRUSTED ✅** to **PROVEN ✅**
through a 3-foreman × 3-job × 3-day live operational trial — using
the platform exactly as it stands today, no last-minute changes.

This trial is the **final gate**. If it succeeds → PROVEN. If it
fails → identify the gap, close it, re-run.

---

## STRUCTURE — 3 × 3 × 3

| Axis | Count | Selection rule |
|---|---|---|
| Foremen | 3 | One veteran (5+ yr MASCI), one mid-tenure (2–5 yr), one rookie (<2 yr). Spanish-primary at least 1. |
| Jobs | 3 | One utility, one roadway, one structure/box-culvert. Active production schedule, not training jobs. |
| Days | 3 | Three CONSECUTIVE working days per foreman. Same week. |

**Total field record target**: 9 excavations minimum (3 foremen × 3 days × ≥1 excavation/day).
**Expected upper bound**: ~27 if every crew runs multiple excavations/day.

---

## DATA TO CAPTURE — PER EXCAVATION RECORD

Each foreman submission contributes to the trial log. Capture (one row per submitted record):

| Field | How captured |
|---|---|
| **EX-ID** | platform-assigned (EX-2026-###) |
| **Foreman** | from form |
| **Job** | from form |
| **Day index** (1·2·3) | day in trial |
| **Time to complete record** | foreman self-reports start / submit times in field notes |
| **Number of user questions** | foreman tally — how many times they had to ask Safety/Super what to do |
| **Number of corrections** | foreman counts back-and-forth edits before final submit |
| **Number of OSHA flags triggered** | from `flags[]` on the record |
| **Severity breakdown** | Action Required / Needs Review / Info |
| **Mobile device issues** | freeform — broken layouts, slow loads, keyboard issues |
| **Spanish translation issues** | freeform — wrong word, missing label, EN bleed-through |
| **Asset linkage issues** | did the foreman find the right TB / RP? Was scan to QR successful? |
| **Reinspection workflow issues** | did the foreman use the FV-7.3 trigger? Did Safety + Super receive? |

Aggregate per foreman + per day + per job + per excavation type.

---

## STAKEHOLDER FEEDBACK CAPTURE

End-of-day phone (≤ 10 min) with each foreman, end-of-trial with Super + Safety.

### Foreman feedback (each day, each foreman)
* Did the form feel field-safe? (Y/N + why)
* Anything you wanted to do but couldn't?
* Anything that was wrong?
* What would you change with one decision?

### Superintendent feedback (end of trial)
* Could you answer the 30-second audit in <30s from the Oversight chips?
  * How many excavations are open?
  * Which are non-compliant?
  * Which need reinspection?
  * Which have no CP?
  * Which use trench boxes?
  * Which use road plates?
* Did the Emergency chip surface every emergency excavation?
* Did the chip filter work on a phone (not just desktop)?

### Safety feedback (end of trial)
* Did the FV-7.6 rollup chips give you the right priorities?
* Was the rated-depth override workflow usable in the field with Safety dispatched mid-day?
* Did the Spanish translation override hold up on real ES submissions?

---

## SUCCESS CRITERIA

The trial **PASSES** when ALL of the following hold:

1. **Completion**: 9 × excavation records successfully submitted across 3 foremen × 3 days.
2. **Time to complete**: median time per record ≤ 7 minutes; P95 ≤ 12 minutes.
3. **Foreman questions**: median questions per record ≤ 2.
4. **Corrections**: median corrections per record ≤ 1.
5. **Mobile**: zero broken layouts; zero submissions blocked by mobile UI.
6. **Spanish**: zero Spanish records where original-language preservation failed.
7. **Asset linkage**: every Trench Box / Road Plate used was linkable via the asset picker.
8. **Reinspection**: at least one foreman-triggered reinspection executed and observed by Safety + Super.
9. **Oversight 30-second audit**: Superintendent answers all 6 audit questions in **< 30 seconds combined** from the chip row.
10. **No P0 platform bug** observed by any stakeholder.

If 8 of 10 hold → CONDITIONAL PROVEN. Identify the 1–2 gaps and re-run only those.
If <8 → identify root cause, fix, restart the trial.

---

## SCHEDULE

| Day | Activity |
|---|---|
| **T-1** | Authorize 3 foremen + 3 jobs. Notify Safety + Super. Confirm device prep (each foreman has the mobile URL bookmarked). |
| **D-1** | Run day 1. Capture phone debrief 4–5 PM. |
| **D-2** | Run day 2. Capture phone debrief 4–5 PM. |
| **D-3** | Run day 3. Capture phone debrief 4–5 PM. |
| **T+1** | Compile trial log. Tally feedback. Produce verdict. |

Total elapsed: **5 calendar days**.

---

## TRIAL LOG TEMPLATE

A single CSV is the authoritative output:

```
ex_id,foreman,job_number,day,start_time,submit_time,duration_min,
questions_count,corrections_count,flag_count,action_required_count,
mobile_issues,spanish_issues,asset_issues,reinspection_issues,
foreman_notes
```

Filename: `/app/memory/field_trial_log_<YYYY-MM-DD>.csv`.

---

## ROLES

| Role | Responsibility |
|---|---|
| Foremen (×3) | Submit excavation records during normal work. Phone debrief end-of-day. |
| Superintendent | Watch Oversight chips daily. Provide end-of-trial 30-second audit. |
| Safety | Review submissions in real time. Use FV-7.1 Safety override at least once. Provide end-of-trial feedback. |
| Field Trial Lead | Maintain the trial log. Run debriefs. Compose verdict document. |

---

## DELIVERABLE

At end of T+1:
* `field_trial_log_<date>.csv` — every record + metrics.
* `FIELD_TRIAL_VERDICT.md` — Pass / Conditional Pass / Fail, with evidence.

If PASS → Excavation Operations is **PROVEN ✅** and the OMEGA directive
gate closes for Excavation Operations.

If FAIL → identify gap, address in a targeted sprint (FV-7.2A, FV-7.3A,
etc.), re-run the failing axis only.

---

## OUT OF SCOPE FOR THIS TRIAL

* No new features built during the trial window
* No mid-trial UI changes
* No "let's improve this while we're testing" — improvements go in the post-trial verdict
* Strict OMEGA discipline — verify, capture, then decide

---

## VERDICT TRIGGER

Once this trial completes successfully → Excavation Operations status:

**PROVEN ✅**

Until then → **TRUSTED ✅ · READY FOR FIELD TRIAL**.
