# EXCAVATION OPERATIONS · CLICK COUNT REPORT

**OMEGA Phase FV-2 — Real-World Scenario Click Audit**
**Date:** 2026-02-07

Counts assume: foreman is signed in (or anonymous public submit), MASCI Job already exists in `jobs_master`, Daily Report draft is open. "Tap" = one click / one touch. "Type" = one keystroke per character of meaningful input.

---

## Scenario A — 4 ft trench, no box, no plate

**Path:** Daily Report → Excavation = Yes → Create New → Public Excavation Form.

| Step | Action                                                           | Taps  | Typed |
|------|------------------------------------------------------------------|-------|-------|
| 1    | Daily Report Section 03 → Excavation Activity = Yes              | 1     | 0     |
| 2    | Tap "Create New Excavation Record"                               | 1     | 0     |
| 3    | Form opens with project_number, date, source pre-filled          | —     | 0     |
| 4    | Section 1 Job picker — already pre-filled (verify)               | 0     | 0     |
| 5    | Section 1b — Foreman picker (other roles optional)               | 2     | 0     |
| 6    | Section 1b — Submitted By                                         | 1     | ~10   |
| 7    | Section 2 — Depth 4 → triggers chip                              | 1     | 1     |
| 8    | Section 3 — Work Type select                                     | 1     | 0     |
| 9    | Section 4 — Soil = Type B                                        | 1     | 0     |
| 10   | Section 5 — Protective = Sloping (suggested chip 1-tap)          | 1     | 0     |
| 11   | Section 7 — Access/Egress installed = Yes                        | 1     | 0     |
| 12   | Section 9 — Spoils 2 ft from edge = Yes                          | 1     | 0     |
| 13   | Section 12 — CP confirmation checkbox                            | 1     | 0     |
| 14   | Submit                                                            | 1     | 0     |
| **Total** |                                                              | **12**| **~11**|

**OSHA flags triggered:** ACCESS_EGRESS (Info chip — auto-cleared by step 11).

---

## Scenario B — 6 ft trench with trench box

| Step | Action                                                     | Taps | Typed |
|------|------------------------------------------------------------|------|-------|
| 1–6  | Same as Scenario A through Submitted By                    | 6    | ~10   |
| 7    | Depth 6                                                    | 1    | 1     |
| 8    | Work Type                                                  | 1    | 0     |
| 9    | Soil = Type B                                              | 1    | 0     |
| 10   | Protective = Trench Box (suggested 1-tap)                  | 1    | 0     |
| 11   | Section 6 — Asset picker open → search "TB" → pick 1 box   | 3    | 2     |
| 12   | Section 7 — Access Yes                                     | 1    | 0     |
| 13   | Section 9 — Spoils Yes                                     | 1    | 0     |
| 14   | Section 12 — CP picker → pick                              | 2    | 0     |
| 15   | CP confirmation checkbox                                   | 1    | 0     |
| 16   | Submit                                                     | 1    | 0     |
| **Total** |                                                         | **20**| **~13**|

---

## Scenario C — 10 ft Type C with trench box

Adds: smart suggestion for Type C is "Sloping (1.5H:1V) or Trench Box / Shoring". Adds 1 tap to override the auto-suggest. Adds explanation reading time (~10 sec).

| **Total** | **~22 taps**, ~13 typed. **OSHA flags:** SOIL_TYPE_C (Needs Review), depth ≥ 5 ft. |

---

## Scenario D — Road crossing with plates

Adds Section 6b. Tap "Road Plates Used = Yes". Pick 2 plates from filtered picker.

| **Total** | **~17 taps**, ~13 typed. |

---

## Scenario E — Rain event triggering reinspection

**Foreman cannot self-trigger** today. Reinspection trigger is admin-only.
- Safety path: Oversight → click record → Review dialog → Reinspection panel → pick reason "Rain" → Trigger.
- **Total for Safety:** 5 taps after they get to the Oversight page (~10 taps total).
- **Total for Foreman:** **0** (cannot trigger). Workflow gap.

---

## Scenario F — Utility conflict

Adds Section 8 visibility (auto-shown when work_type is Utility/Sanitary/Storm/Water Main/Electrical/Drainage). 4 extra Y/N + ticket number entry + locate status select + utility notes.

| **Total** | **~22 taps**, ~25 typed (locate ticket + notes). |

---

## Scenario G — Emergency excavation

**No dedicated path.** Foreman submits a normal excavation record marked Submit. There is no "emergency" status, no priority flag, no leadership-paging mechanism.

**Total:** same as Scenario A. **Workflow gap** — emergency excavations look identical to routine ones in the queue.

---

## Scenario H — Multiple trench boxes (e.g. 2 stacked / side-by-side)

`assigned_asset_ids` is a multi-select array. Foreman picks 2 boxes in Section 6.

| **Total:** +2 taps over Scenario B (~22 taps). |
| **Risk:** no validation that combined rated depth ≥ excavation depth. |

---

## Scenario I — Multiple road plates

Same as Scenario D with extra picks. ~3 extra taps per additional plate.

---

## Scenario J — Crew creates excavation directly from Daily Report

This is the certified Phase 10A-B path. Measured in Scenario A above.

**Notable:** the "Create New" button opens a new tab. Foreman must:
1. Submit the excavation in the new tab.
2. Switch back to the Daily Report tab.
3. Either:
   - Trust the auto-link (Phase 10A-B looks up by project_number+date — confirmed via `daily_report_links`), OR
   - Manually link via the "Link Existing Excavation Record" panel.

**Concern:** if step 3 auto-link fails (e.g., Daily Report date and excavation date don't match), the foreman must paste the EX-ID manually. Not a 5:30-AM-friendly fallback.

---

## SUMMARY TABLE

| Scenario                              | Taps  | Typed | OSHA flags | Notes                                  |
|---------------------------------------|-------|-------|------------|----------------------------------------|
| A — 4 ft, no box, no plate            | ~12   | ~11   | 1 (auto-cleared) | Cleanest happy path |
| B — 6 ft + trench box                 | ~20   | ~13   | 0 once box linked | Box rated-depth NOT validated |
| C — 10 ft Type C + box                | ~22   | ~13   | SOIL_TYPE_C, depth ≥ 5 | Auto-suggest helps |
| D — Road crossing + plates            | ~17   | ~13   | 0 once plates linked | Size not validated |
| E — Rain reinspection                 | 0/10  | 0     | RAIN_REINSPECTION | Foreman cannot self-trigger |
| F — Utility conflict                  | ~22   | ~25   | UTILITY_LOCATE | Most typed |
| G — Emergency excavation              | ~12   | ~11   | (same as A) | No emergency designation |
| H — Multiple trench boxes             | ~22   | ~13   | 0 | Combined depth NOT validated |
| I — Multiple road plates              | ~20   | ~13   | 0 | Combined width NOT validated |
| J — From Daily Report (Phase 10A-B)   | ~13   | ~11   | (same as A) | New-tab UX is the friction |

**Conclusion:** Click counts are reasonable for happy paths. The friction lives in the **gaps** (Scenarios E and G) and the **unvalidated** asset-fit logic in B/D/H/I.
