# TRACK 19.08 · Duplicate Logic Report

Every observable duplication in the operational forms ecosystem, with root cause.

---

## 1 · Duplicate helper systems (highest-impact finding)

**Observation**: Equipment Pre-Op renders THREE overlapping helper systems simultaneously.

| Helper | Where added | Purpose | LOC on the page |
| --- | --- | --- | --- |
| `<LifecycleGuide>` blocks | iter194 (crew linkage) & iter360 (guidance polish) | Educational cards with sections[] | ~40 LOC |
| `<HelpTipBlock>` blocks (per section) | iter305 (contextual coaching) | Contextual per-formKey guidance panels loaded from `guidance/` | ~10 LOC per section × 4 sections |
| Section-header prose | iter194 & iter305 | Free-form paragraphs describing what to fill | ~15 LOC per section × 5 sections |

**Root cause**: Three iterations added guidance without consolidating the previous system. Nobody removed the older layer because it was reinforcing existing operator training. Over time, redundancy stacked.

**Evidence**: `grep -c "LifecycleGuide\|HelpTipBlock" /app/frontend/src/pages/NewEquipmentInspection.jsx` and same on `NewDailyReport.jsx`. Both files carry the full stack.

**Impact**: Operators scroll past helper text without reading. Coaching that once helped now creates cognitive noise.

**Not fixed** — Track 19.08 is audit-only. Preserved for redesign as P1 in `16_EXECUTIVE_RECOMMENDATIONS.md`.

---

## 2 · Duplicate submit routes (deliberate historical compatibility)

Every operational form has 2-3 route aliases:

| Canonical | Aliases | Reason |
| --- | --- | --- |
| `/daily/new` | `/daily/submit` · `/reports/daily/new` | Legacy links in older field-leadership emails |
| `/incidents/new` | `/incidents/submit` | Same |
| `/equipment/new` | `/equipment/submit` | Same |
| `/fleet/dvir/new` | `/fleet/dvir/submit` | Same |
| `/meetings/new` | `/meetings/submit` | Same |
| `/inspections/new` | `/inspections/submit` · `/inspect/new` | Multi-generation link tokens still in circulation |
| `/jha` | `/jha/new` · `/jha/submit` | Same |
| `/qaqc` | `/qa-qc` · `/qaqc/:slug/new` | Hyphen/no-hyphen public-link ambiguity |
| `/cheatsheet` | `/cheat-sheet` | Same |

**Root cause**: Emailed submission links are historic and immortal — every alias exists because *some* link out there references it. Removing them would break real-world flows.

**Verdict**: MUST PRESERVE. This isn't drift, it's a live compatibility layer.

---

## 3 · Duplicate collections / polymorphic collections

| Collection | Content | Duplicate surface |
| --- | --- | --- |
| `inspections` | QA-QC · generic · JHA (some) · legacy imports | Filtered by `inspection_type` |
| `jhas` (dedicated) vs. `inspections.subtype=jha` | JHA templates + submits | Two paths; migration incomplete |
| `equipment_master` vs. `equipment_units` | Fleet vehicle catalog | Distinct — `equipment_master` is catalog, `equipment_units` is instance |
| `notifications` (in-app) vs. `email_routing_audit_v` (email dispatch log) | Same event, two surfaces | By design; different consumers |
| `daily_reports.masci_crews[]` vs. `job_hazard_files.crew_names[]` | Attendance | Separate — one is Daily Report, one is JHA acknowledgement |

**Root cause**: Iterative growth. `jhas` collection came later; the earlier `inspections` collection kept JHA records for backward compat with pre-Track-18 imports.

**Verdict**: `inspections` polymorphism is fragile but not currently broken. See `14_REDESIGN_PROTECTION_MATRIX.md`.

---

## 4 · Duplicate UI shells (highest redesign opportunity)

Each `New*.jsx` page re-implements:
* Draft-restore banner
* Autosave hook wiring
* Sticky submit footer + hint text
* Photo upload wiring
* Attachment upload wiring
* Signature pad wiring
* Job-picker + prepared-by pattern
* Language toggle
* GPS use button

**Per-form shell LOC (estimate)**: ~120 LOC × 8 forms = ~960 LOC of duplicated wiring.

**Root cause**: Each new form was built by copy-pasting the previous. No shared `<FormShell>` primitive ever emerged. Track 19.06 introduced `<PresenceGate>` for the Daily Report — the first cross-cutting primitive in a while.

**Verdict**: This is the single biggest simplification opportunity. See `16_EXECUTIVE_RECOMMENDATIONS.md`.

---

## 5 · Duplicate JHA surfaces

Three surfaces for the same intent:
* `NewInspection.jsx` (JHA subtype) — form submission for a one-off JHA.
* `JhaPlansAdmin.jsx` — admin CRUD of JHA templates.
* `JhaPlansHub.jsx` / `JhaPlansPoster.jsx` — browse + print.

Plus an *acknowledgement* endpoint family:
* `POST /api/jha-acknowledgements`
* `GET /api/jha-acknowledgements/compliance`
* `GET /api/jha-acknowledgements/by-employee/{id}`
* `GET /api/jha-acknowledgements/by-project/{project_number}`
* `GET /api/jha-acknowledgements/me`

**Root cause**: JHA workflow has three phases (author → publish → acknowledge) with distinct actor sets. The surfaces reflect the workflow, not accidental duplication.

**Verdict**: Preserve. Naming can be clearer, but the split is intentional.

---

## 6 · Duplicate hub pages (V1 / V2)

`SafetyHub` + `SafetyHubV2` · `HrHub` + `HrHubV2` + `HrV2Preview` · `DispatchHub` + `DispatchHubV2` · `ShopHub` + `ShopHubV2` · `AdminHub` + `AdminHubV2` · `PmHub` (V2 rollout).

**Root cause**: Progressive rollout of the Hub V2 design. Legacy V1 pages remain mounted so users can fall back.

**Verdict**: This is the second-largest simplification opportunity — retire V1 hubs once V2 adoption is proven. Out of scope for redesign track (needs product decision).

---

## 7 · Duplicate DVIR variants

`/fleet/dvir/new` · `/fleet/weekly-lead/new` · `/fleet/weekly-emergency/new` — three routes, same `NewFleetDVIR.jsx` component with different `dvir_type` param.

**Root cause**: Route-based param routing. The three DVIR types share 90% of the UI. Route split makes each surface bookmarkable and analytics-trackable.

**Verdict**: Preserve — no duplication in code, only in perception.

---

## 8 · Duplicate coaching content

Static training content lives in:
* `frontend/src/data/training.js` + `training_es.js`
* `backend/guidance/content.py` + `translations_es.py` + `tips.py`
* `backend/training_pdf.py` (PDF-embed strings)
* Per-form `LifecycleGuide.sections[]` prose

Some topics (e.g., "Why linkage matters") appear in three of these locations.

**Root cause**: Different consumers (in-form coaching · PDF training packet · guidance search index) — but no single source-of-truth.

**Verdict**: Consolidation opportunity, low urgency.

---

## 9 · Duplicate "photo required" logic

Photo minimums appear in:
* `NewDailyReport.jsx` — `photoMin = 6` (client-side)
* `routes/daily_reports.py` — asserts min 6 on submit
* `pdf_render.py` — expects `photos[]` non-empty
* `test_track_19_06_*.py` — locks `photoMin` constant

**Root cause**: Defense in depth.

**Verdict**: Preserve — this is intentional multi-layer validation.

---

## 10 · Summary — Duplication scorecard

| Duplicate class | Root cause | Verdict | Priority |
| --- | --- | --- | --- |
| Helper system stacking | Iterative accretion | Consolidate on redesign | P1 |
| Route aliases | Live compat | Preserve | — |
| `inspections` polymorphism | Migration incomplete | Preserve; monitor | P3 |
| Form-shell wiring | Copy-paste growth | Extract shared primitive | P0 |
| JHA surfaces | Workflow phases | Preserve | — |
| Hub V1/V2 | Rollout | Retire V1 (product decision) | P2 |
| DVIR variants | Route-based analytics | Preserve | — |
| Coaching content | Multi-consumer | Consolidate SoT | P3 |
| Photo-required | Defense in depth | Preserve | — |
