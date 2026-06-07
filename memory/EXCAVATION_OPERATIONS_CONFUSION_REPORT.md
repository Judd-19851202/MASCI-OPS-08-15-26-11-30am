# EXCAVATION OPERATIONS · CONFUSION REPORT

**OMEGA Phase FV-3/FV-4/FV-5 — Persona Confusion Audit**
**Date:** 2026-02-07

---

## FOREMAN (5:30 AM TEST)

| Moment                                                                                   | Confusion level | Why                                                                                                |
|------------------------------------------------------------------------------------------|------------------|----------------------------------------------------------------------------------------------------|
| Lands on `/trench-safety/excavation/new`                                                 | LOW              | Title + Live OSHA Status make purpose clear in <5 sec.                                             |
| Picks MASCI Job                                                                          | LOW              | Same picker he uses on the Daily Report.                                                           |
| Section 1b — five separate Employee dropdowns (Prepared By / Foreman / Leadman / Super / CP) | MEDIUM      | "Why does the platform need both Foreman and Prepared By?" Not field-language.                     |
| Section 4 — Soil Classification                                                          | MEDIUM           | "Type A / B / C / Stable Rock" is OSHA vocabulary. Coaching block explains but adds reading load.   |
| Section 5 — Protective System                                                            | MEDIUM           | Suggested chip is helpful. Still requires the foreman to know the difference between Sloping / Shoring / Shielding / Benching. |
| Section 6 — Asset picker                                                                 | LOW              | Picker is fast. Asset chips are field-readable.                                                    |
| Section 7 — Access/Egress 5 Y/N questions                                                | MEDIUM           | "Within 25 ft lateral travel?" — many foremen do not know what "lateral travel" means.             |
| Section 12 — Competent Person picker                                                     | HIGH             | If no one in the roster has the "competent" role tag, the foreman picks anyone. The system trusts him. |
| Photos                                                                                   | MEDIUM           | Section 13 says "Upload via asset photo workflow after submission" — foreman expects to upload in-form. |
| Submit                                                                                   | LOW              | Live OSHA card tells him exactly what's left.                                                      |

**Foreman 5:30 AM verdict:** Completable with effort. NOT completable without prior orientation. The OSHA terminology in soil / protective / access sections will trip a first-time foreman.

---

## SUPERINTENDENT (30-second test)

> "What excavations are open right now?"

| Question                                          | Answerable in 30 sec? | Path                                                              |
|---------------------------------------------------|-----------------------|-------------------------------------------------------------------|
| What excavations are open?                        | ✅ Yes                | `/safety/trench-safety/excavations` · default tab.                |
| Which need reinspection?                          | ✅ Yes                | "Reinspection Queue" tab — one click.                             |
| Which are non-compliant?                          | ⚠ Partial             | Filter `status = Action Required` — but requires opening filter dropdown. |
| Which have no competent person?                   | ❌ No                  | No filter. Must read flag lists row-by-row.                       |
| Which have no protective system?                  | ⚠ Partial             | Reports summary API has the list. UI does not surface it.         |
| Which involve road plates?                        | ❌ No                  | No filter by asset_type. Must scan each row's asset chips.        |
| Which involve trench boxes?                       | ❌ No                  | Same — no filter.                                                 |

**Superintendent verdict:** 30-second test passes for "what's open" and "what needs reinspection". **Fails** for the 3 operational queries that matter most: protective-system gap, CP gap, road-plate/trench-box deployment view.

---

## SAFETY (60-second test)

| Question                                          | Answerable in 60 sec? | Path                                                              |
|---------------------------------------------------|-----------------------|-------------------------------------------------------------------|
| What OSHA risks exist today?                      | ⚠ Partial             | Filter `Action Required` lists records. No aggregate "risk count by code". |
| What inspections are overdue?                     | ✅ Yes                | Reinspection Queue tab.                                            |
| What excavations require attention?               | ✅ Yes                | Action Required filter.                                            |
| What road plates are deployed today?              | ❌ No                  | Asset registry shows assignment; excavation list does not aggregate. |
| What trench boxes are deployed today?             | ❌ No                  | Same — no aggregate.                                               |
| Who is the competent person on each open job?     | ❌ No                  | Must open each record.                                             |

**Safety verdict:** Reinspection visibility is strong. **Fleet-wide trench-box / road-plate deployment view is missing**. Risk aggregation by OSHA flag code is only reachable via the reports/summary API — no UI surfaces it.

---

## FIRST-TIME USER (any role)

| Moment                                                              | Confusion |
|---------------------------------------------------------------------|-----------|
| Difference between "Excavation Record" and "Daily Report"           | HIGH — they look similar in the navigation. |
| Why "Excavation Activity Today? = Yes" blocks the Daily Report      | MEDIUM — toast text helps but the user has to read it. |
| Where the linked excavation record opens                            | MEDIUM — new tab without explanation. |
| What "Action Required" means vs "Needs Review"                      | MEDIUM — coaching language is good, but the distinction isn't explicit anywhere. |
| Whether a closed excavation can be reopened                         | LOW — Safety oversight surfaces the Reopen action. |

---

## TOP 5 CONFUSION POINTS (ranked by impact)

1. **Competent Person designation has no certification check.** Foreman can pick anyone. (Safety risk.)
2. **Trench-box rated_depth_ft is shown but not validated.** Foreman could link a 6 ft box to a 10 ft excavation. (Safety risk.)
3. **Superintendent cannot answer "who has no CP / no protective system?" without opening each record.** (Operational gap.)
4. **Foreman cannot self-trigger reinspection** after a rain event mid-day. Only Safety can. (Safety risk.)
5. **Photo upload happens "after submission"** — foreman expects inline. (UX gap.)
