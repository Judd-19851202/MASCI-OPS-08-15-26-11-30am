# FIELD TRIAL · FINAL CERTIFICATION

**Subject**: Excavation Operations · MASCI Trench Safety Platform
**Trial type**: AUTOMATED PROXY (no real human field validation conducted)
**Date**: 2026-02-11
**Authority**: OMEGA DIRECTIVE — Field Trial Authorization

---

## VERDICT

# CONDITIONALLY READY ✅

**NOT PROVEN.** Real human field validation by 3 real foremen on 3 real
jobs over 3 real consecutive working days has NOT been conducted. The
directive itself states: *"Do not claim PROVEN unless field evidence
supports it."*

Excavation Operations is **CONDITIONALLY READY** — the platform passes
the strongest automated proxy possible (100% workflow PASS · zero P0
bugs · real backfilled assets · real API · real mobile viewports · real
EN/ES toggle) but the **human axis of the trial has not been run**.

---

## HONEST DISCLOSURE

An AI agent cannot:
* Hand a phone to a real foreman.
* Have a real foreman dig a real trench.
* Capture a real foreman's exact verbatim complaint.
* Validate physical asset linkage on a real job site.

The directive contemplates real humans. This proxy trial is the
strongest automated substitute — every measurable dimension was
exercised against the real production platform — but it is **NOT a
substitute for the human trial**. PROVEN ✅ remains gated on the
real human trial.

---

## WHAT THE AUTOMATED PROXY DID PROVE

### 1 · Workflow correctness
* 90 / 90 structured workflow runs PASS across 3 simulated foremen × 3 days × 10 workflows.
* 10 / 10 edge-case probes PASS on Day 3.
* **Total: 100 / 100 (100.0%).**

### 2 · Flag accuracy against REAL backfilled assets
| Rule | Real Asset | Result |
|---|---|---|
| FV-7.1 ACTION REQUIRED | TB-03 (rated 6 ft) @ 9 ft | ✅ Fires |
| FV-7.1 Compliant | TB-04 (rated 10 ft) @ 9 ft | ✅ Silent |
| FV-7.1 Acknowledgement downgrade | TB-03 @ 9 ft + reason | ✅ Needs Review |
| FV-7.4 Road plate undersize | RP-901 5×8 on 12×10 opening | ✅ Action Required |
| FV-7.4 Road plate compliant | RP-901 on 4×4 opening | ✅ Silent |
| FV-7.3 Foreman reinspection · 7 reasons | All accepted no auth | ✅ 7/7 |
| FV-7.5 / FV-7.6 Chip counts (real data) | flag_depth=3 · flag_road_plate=2 | ✅ Non-zero from real assets |

### 3 · Latency
| Metric | Value | Field acceptable? |
|---|---|---|
| Average | 201.9 ms | ✅ |
| P95 | 445.7 ms | ✅ |
| P99 | < 500 ms | ✅ |

### 4 · Mobile viewport rendering
* iPhone 14 Pro (393×852): all critical elements present ✅
* Pixel 6 (412×915): all critical elements present ✅
* iPad Air (820×1180): all critical elements present ✅
* ⚠️ Headless `body.scrollWidth=1920` on all profiles — flagged FT-D1-001 for human-device verification.

### 5 · EN/ES toggle
* Page-level translation works ✅
* Status card translates ✅
* Section labels translate ✅
* Form pickers translate ✅
* ⚠️ Emergency Excavation block remains English-only — flagged FT-D1-002.

### 6 · Test suite regression
* `tests/test_fv7_safety_gaps.py`: **20 / 20 GREEN** (all 5 prior environmental skips eliminated by real backfilled assets).
* `tests/test_trench_safety_phase10ab_integration.py`: **16 / 16 GREEN.**

---

## PASS / FAIL CRITERIA — DIRECTIVE CHECKLIST

| # | Criterion | Automated Proxy | Human Trial Required |
|---|---|---|---|
| 1 | Foremen can complete workflows without training | n/a | ✅ Real foreman observation |
| 2 | Daily Report excavation=No behaves normally | ✅ (regression suite) | confirm in field |
| 3 | Daily Report excavation=Yes requires Create/Link | ✅ (test_daily_report) | confirm in field |
| 4 | Autosave works | not exercised in proxy | ✅ Required in human trial |
| 5 | Device draft recovery works | not exercised in proxy | ✅ Required in human trial |
| 6 | Excavation record creation works | ✅ 30/30 | confirm in field |
| 7 | Asset lookup works | ✅ 30/30 | confirm in field |
| 8 | Road plate lookup works | ✅ 30/30 | confirm in field |
| 9 | Competent person validation works | ✅ 30/30 | confirm in field |
| 10 | OSHA flags fire correctly | ✅ 30/30 zero false flags | confirm in field |
| 11 | No critical mobile issues | unclear — overflow metric needs human verify | ✅ Required |
| 12 | Safety can review issues quickly | endpoint latency 71 ms · UI rendered | ✅ Real Safety user audit |
| 13 | Superintendent can see operational status quickly | 12 chip keys · 425 ms · single-tap | ✅ 30-second audit by real Super |
| 14 | Spanish workflow has no critical blockers | one non-critical translation gap | ✅ Required with ES foreman |

**14 criteria · 9 verified by automated proxy · 5 require real human trial.**

---

## SUPERINTENDENT 30-SECOND AUDIT — proxy verification

| Question | Answer path | Verified |
|---|---|---|
| How many excavations open? | `Open Excavations` chip → 490 | ✅ |
| Which need reinspection? | `Reinspection Required` chip → 56 | ✅ |
| Which have no CP? | `No Competent Person` chip → 469 | ✅ |
| Which have no protective system? | `No Protective System` chip → 155 | ✅ |
| Which use trench boxes? | `Trench Boxes Deployed` chip → 55 | ✅ |
| Which use road plates? | `Road Plates Deployed` chip → 14 | ✅ |
| Which have OSHA action flags? | `Safety OSHA Rollup` chip row 5 chips with counts | ✅ |

**All 7 answers single-tap from one page** — proxy confirms the surface
supports the 30-second audit. Final verification requires real
Superintendent timing in real use.

---

## SAFETY 60-SECOND AUDIT — proxy verification

| Question | Answer path | Verified |
|---|---|---|
| What excavation risks today? | Safety chip row 5 chips with severity priority | ✅ |
| What inspections/reinspections required? | `Reinspection Required` chip + Reinspection Queue tab | ✅ |
| What CP issues? | `flag_no_cp` chip | ✅ |
| What trench box rating issues? | `flag_depth` chip → opens record with rated-depth override panel | ✅ |
| What road plate issues? | `flag_road_plate` chip | ✅ |
| What records need review? | `Submitted` / `Needs Review` status filter | ✅ |
| What needs coaching? | All flags use coaching language; "Coaching, not punishment" copy block | ✅ |

**All 7 answers single-page** — proxy confirms surface supports the
60-second audit.

---

## RECOMMENDATIONS

### 1 · RUN THE REAL HUMAN TRIAL
This is the only path to PROVEN ✅. The platform is ready. Schedule
3 foremen × 3 jobs × 3 consecutive working days per
`FIELD_TRIAL_EXECUTION_PLAN.md`.

### 2 · TWO MINOR ITEMS TO TRACK (do not block trial)
* **FT-D1-001** (P2) — verify mobile horizontal-overflow on a physical phone during the trial. If real, file a small UI sprint. If not, close.
* **FT-D1-002** (P3) — add ES translation strings for the Emergency Excavation block. Two-line i18n bundle update. Low priority.

### 3 · DURING THE HUMAN TRIAL
Capture exactly per `FIELD_TRIAL_FOREMAN_FEEDBACK.md` template — verbatim
quotes, not summaries. Compile to CSV. Issue a
`FIELD_TRIAL_HUMAN_VERDICT.md` at the end.

---

## CHANGELOG SAFEGUARDS (PER STOP CONDITION)

Code changes made during this trial: **NONE.**

The trial was strictly observational against the locked production
state. The only artifacts produced are:

* `/app/backend/scripts/field_trial_runner.py` (NEW · observation tool · does not modify product)
* `/app/memory/field_trial_results.json` (NEW · raw output)
* `/app/memory/FIELD_TRIAL_DAY_1_REPORT.md`
* `/app/memory/FIELD_TRIAL_DAY_2_REPORT.md`
* `/app/memory/FIELD_TRIAL_DAY_3_REPORT.md`
* `/app/memory/FIELD_TRIAL_FOREMAN_FEEDBACK.md`
* `/app/memory/FIELD_TRIAL_ISSUE_LOG.md`
* `/app/memory/FIELD_TRIAL_FINAL_CERTIFICATION.md` (this file)

No source files touched. No platform behaviour modified.

---

## FINAL VERDICT

# Excavation Operations status: **CONDITIONALLY READY ✅**

* ✅ Backend, frontend, rules, chips, asset metadata, audit trail, EN/ES — automated proxy GREEN.
* ⏳ Real human trial outstanding · the platform is ready to host it.
* 🚫 PROVEN ✅ is **NOT YET** claimed and **will not be** claimed by an AI proxy.

Hand this off to the real 3-foreman trial. That trial — and only that
trial — closes the PROVEN gate.
