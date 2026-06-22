# TRACK 15.61 — Recommendations (Phase 12) · DO NOT IMPLEMENT

The 10 prioritised fixes derived from Phases 1–11. Each carries an impact / risk / complexity / field-value scoring with Six-Pillar assessment.

## Priority key

| Tier | Meaning |
|---|---|
| P0 | Production trust gap — fix first. |
| P1 | High operational benefit, moderate complexity. |
| P2 | Quality-of-life and observability. |

---

### **R-UX-NARRATIVE (P0)** · Unify the narrative surface

**Problem.** Two parallel narrative fields (`activities[]` and `general_notes`) confuse operators. 40 % use `general_notes`, 26 % use `activities[]`, 46.8 % use neither. PDF reads both; PM dashboards read neither.

**Evidence.** Phase 2 + Phase 9.

**Proposed solution.** Single "What happened today?" prompt at the top of the report with a story-template scaffold ("Work performed · Completed · Delays · Next steps") rendering both an editable paragraph AND a structured row mode behind a tab. Downstream PDF + DB shape unchanged.

**Six-Pillar score:** Powerful 9 · Simple 10 · Beautiful 9 · Trusted 9 · Proven 7 · Deployable 9 → **53/60**

**Effort:** medium (1 new component, ~150 LOC frontend; backend schema additive only)

**Estimated benefit:** lift median Activity-Log word count from 0 → 30+ words; lift Phase-4 job-story median from 4 → 6.

---

### **R-HAUL (P0)** · Make outbound trucking a first-class field

**Problem.** 2.6 % of reports capture outbound material despite active hauling. Free-text hauler + free-text material + free-text unit. No truck-roster picker.

**Evidence.** Phase 5.

**Proposed solution.** Replace the outbound row inputs with: (a) material dropdown from a canonical vocabulary (~20 items); (b) hauler dropdown bound to `db.asset_mappings` (truck-roster + Motive); (c) destination dropdown that remembers per-project recent destinations; (d) ticket photo upload prompt.

**Six-Pillar score:** Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 8 · Deployable 8 → **55/60**

**Effort:** medium (3 dropdowns, 1 photo prompt, 1 backend canonical-material endpoint)

**Estimated benefit:** outbound capture rate 2.6 % → 30 %+. Enables R-PMCC roll-up.

---

### **R-PMCC (P0)** · Aggregate Daily Report hauls into the PM Command Center

**Problem.** `GET /api/pm/command-center/hauls` returns `rows: []` and `loads_today=0` even when Daily Reports have outbound material. The aggregation layer simply doesn't read `db.daily_reports.outbound_materials`.

**Evidence.** Phase 6.

**Proposed solution.** Extend the hauls aggregator (`routes/pm_command_center.py` or equivalent) to UNION `db.daily_reports.outbound_materials` rows scoped by project_number and `report_date == today` into the response. Add a fold over the last 7 days for the overview counter.

**Six-Pillar score:** Powerful 10 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9 · Deployable 9 → **56/60**

**Effort:** small (backend-only · ~50 LOC · single endpoint)

**Estimated benefit:** PM Command Center counters become honest. Closes the "your work disappears" perception gap that is teaching operators not to bother.

---

### **R-DEAD-FIELDS (P1)** · Hide / remove the never-used surfaces

**Problem.** `schedule_delays_notes`, `weather_impact_notes`, `linked_excavation_ids` are 0 % populated. Their presence on the form trains operators to skip-and-scroll.

**Evidence.** Phase 10.

**Proposed solution.** Move behind progressive-disclosure ("Add additional context") and replace the three with one prompt: "Anything slow you down today?".

**Six-Pillar score:** 10 · 10 · 9 · 9 · 9 · 10 → **57/60**

**Effort:** tiny (1 file, ~30 LOC).

**Benefit:** shorter form · higher completion rate on remaining fields.

---

### **R-EXEC (P1)** · Build the missing executive aggregation endpoint

**Problem.** No `/api/admin/executive-dashboard` endpoint exists. Executives cannot answer cross-job questions.

**Evidence.** Phase 7.

**Proposed solution.** Add a read-only `/api/admin/daily-roll-up?from=&to=` endpoint that aggregates: total reports submitted · loads moved · materials delivered · open constraints · safety incidents · per-project last-update timestamp. Render in Admin Command Center as a new tab.

**Six-Pillar score:** 10 · 9 · 9 · 10 · 8 · 9 → **55/60**

**Effort:** medium (one endpoint + one tab).

**Benefit:** transforms the platform from record-keeping into operational intelligence.

---

### **R-IDENTITY (P1)** · Bind `prepared_by` and `superintendent` to canonical identities

**Problem.** 11 reports have "Superintendent" as `prepared_by`. "Joe spiker" + "JOE SPIKER" = same person, 37 reports under two names. 18.8 % of reports leave `superintendent` blank.

**Evidence.** Phase 1.

**Proposed solution.** Replace the free-text inputs with `EmployeeCombo` (already shared, already has Request-to-Add per 15.60). Capture both the free-text label AND the canonical `employee_id`.

**Six-Pillar score:** 9 · 10 · 9 · 10 · 9 · 9 → **56/60**

**Effort:** small (2 field swaps, ~30 LOC).

**Benefit:** enables per-foreman / per-super aggregation in Phase 7 exec endpoint.

---

### **R-MOTIVE (P1)** · Wire `asset_mappings` into the Daily Report equipment + hauler pickers

**Problem.** 190 asset mappings exist; 0 are consulted at Daily-Report submit. No haul row references a Motive vehicle_id.

**Evidence.** Phase 8.

**Proposed solution.** Existing `EquipmentCombo` already pulls from the asset master; surface Motive `unit_number` / `motive_truck_id` on the picked row so the outbound `hauler` field carries a structured truck reference. Cross-join in the PM Command Center hauls aggregator to count Motive load events.

**Six-Pillar score:** 9 · 8 · 9 · 9 · 8 · 8 → **51/60**

**Effort:** medium-high (picker change + aggregator change + backend join).

**Benefit:** unlocks "loads completed today" from real Motive telemetry, not just operator memory.

---

### **R-UX-PROMPT (P2)** · Add real-time completeness coaching

**Problem.** The form has no in-form feedback that warns "you haven't said anything about hauling today even though you have 3 trucks assigned".

**Evidence.** Phase 11.

**Proposed solution.** A small completeness chip in the header similar to `DraftStatusPill` that scores the report against the Phase-4 rubric and surfaces "3 of 8 sections still needed".

**Six-Pillar score:** 9 · 9 · 10 · 9 · 8 · 10 → **55/60**

**Effort:** small (1 new component + scoring lib).

**Benefit:** lifts the median score from 4 → 5 over time.

---

### **R-PHOTO-CAPS (P2)** · Per-photo captions in the PDF

**Problem.** 97.4 % of reports have photos. The photos render in the PDF without per-image captions.

**Evidence.** Phase 9.

**Proposed solution.** Allow per-photo caption entry on upload; render the caption under the photo in the PDF.

**Six-Pillar score:** 9 · 9 · 10 · 9 · 7 · 8 → **52/60**

**Effort:** small.

**Benefit:** turns 97 % of the corpus from "5 photos" into "5 captioned photos that narrate the day".

---

### **R-MATERIAL-VOCAB (P2)** · Canonical material vocabulary on incoming + outgoing

**Problem.** Outbound material vocabulary = literally one word ("Dirt"). Free-text typing prevents roll-up.

**Evidence.** Phase 5.

**Proposed solution.** Add a small admin-managed vocabulary list (10–20 canonical materials) and bind both `materials[].description` and `outbound_materials[].material` to the dropdown with a free-text fallback.

**Six-Pillar score:** 9 · 10 · 9 · 9 · 8 · 9 → **54/60**

**Effort:** small (one collection + one dropdown).

**Benefit:** unlocks executive-tier "how much of X did we move this month" answers.

---

## Implementation order (proposed)

1. **R-PMCC** (P0 · backend only · fastest unlock of "your work appears" trust)
2. **R-HAUL + R-MATERIAL-VOCAB** together (P0 · form-side investment)
3. **R-UX-NARRATIVE** (P0 · the largest behavioural lift)
4. **R-DEAD-FIELDS + R-IDENTITY** (P1 · cleanup pass)
5. **R-EXEC** (P1 · the executive roll-up endpoint)
6. **R-MOTIVE + R-UX-PROMPT + R-PHOTO-CAPS** (P2 · polish and integration)

## What the Track does NOT recommend

- No V2 Daily Report system.
- No new database / new schema beyond an additive material-vocab collection.
- No removal of validation, signature, or photo gates.
- No bypass of HR / approval workflows.
- No abandonment of the existing `pdf_render` pipeline.

The fixes above are surgical and stay within the existing architectural envelope.
