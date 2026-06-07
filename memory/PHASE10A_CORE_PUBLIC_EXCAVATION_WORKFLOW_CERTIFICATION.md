# PHASE 10A CORE — PUBLIC EXCAVATION OPERATIONS WORKFLOW

**OMEGA DIRECTIVE · G-1 OSHA SUBPART P CLOSURE**

**Status:** ✅ CERTIFIED
**Date:** 2026-02-07
**Sprint:** Phase 10A Core (Public Excavation Operations Workflow + UI Parity Correction)
**Scope discipline:** Phase 10A Core ONLY. No deferred 10A.2 features (PM portal visibility, LLM translation, CSV import, advanced analytics) were touched.

---

## EXECUTIVE SUMMARY

The Public Excavation Operations Workflow is live, certified, and visually consistent with the rest of the MASCI Public Trench Safety surface. Field crews can now submit a complete 14-section excavation record from the Public Safety Tile — coaching-first, EN/ES bilingual, asset-linked, and deterministically OSHA-flagged. Safety and Admin can triage and close submissions from the existing Trench Safety oversight shell. Daily Report cross-references are written on submit (non-invasive, read-only lookup). All notifications and audit writes reuse the certified Phase 7.5C event-fanout / audit infrastructure — no parallel pipelines built.

**Backend regression:** 25/25 Phase 10A pytest cases pass. 50/50 Phase 8–9B cases continue to pass.
**Frontend parity:** Verified by testing_agent_v3_fork (`/app/test_reports/iteration_phase10a_core.json`). 100% of UI parity bullets confirmed after the one-line Spanish-translation patch (see §4).

---

## 1 · UI PARITY CORRECTION (per operator directive)

The Public Excavation Form was refactored to use the **same shared public shell** as the rest of the Public Trench Safety surface.

| Standard element                              | Source pattern                                  | Phase 10A status |
|-----------------------------------------------|--------------------------------------------------|------------------|
| `<PublicTrenchHeader>` (back · MASCI · HOME · LangToggle) | `PublicTrenchSafetyDashboard.jsx` line 119–124 | ✅ Adopted (testid `public-excavation-header`) |
| Caution stripe banner                         | `caution-stripe` className above header          | ✅ Adopted         |
| Title block (icon · eyebrow · h1 · description) | Dashboard line 128–139                          | ✅ Adopted (`public-excavation-title`) |
| Red Stop-Work + amber Coaching strips         | Dashboard line 142–157                           | ✅ Adopted (`public-excavation-stopwork`, `public-excavation-coaching`) |
| Section card style (`bg-white border border-slate-200 rounded-md p-4 mt-3` + cyan-700 font-mono eyebrow) | Dashboard sections | ✅ Adopted (14 sections, `exc-section-1..14`) |
| Submit button (`bg-cyan-700 hover:bg-cyan-800 h-12 px-6 uppercase tracking-[0.12em]`) | Public Report submit button | ✅ Adopted (`exc-submit`) |
| Footer (`MASCI Operations Platform · Field-safe view`) | Dashboard line 269–271 | ✅ Adopted |
| Success state — same shell preserved          | New behavior, parity confirmed                   | ✅ Verified |
| EN/ES toggle in header                        | `LangToggle` inside `PublicTrenchHeader`         | ✅ Inherited |
| Mobile spacing (`max-w-3xl mx-auto px-4 sm:px-6 py-5`) | Dashboard main container | ✅ Adopted |

**Standalone-looking form pattern: ELIMINATED.** The form now feels native to the platform.

---

## 2 · BACKEND DELIVERABLES

### 2.1 Routes (`/app/backend/routes/trench_safety/excavations.py`)

- `POST /api/trench-safety/excavations/public/submit` — public, no auth
- `GET  /api/trench-safety/excavations` — Safety/Admin only, filter by project / supervisor / status / soil / protective system / depth_min / has_action_required
- `GET  /api/trench-safety/excavations/{ex_id}` — detail
- `POST /api/trench-safety/excavations/{ex_id}/review` — actions: `review` · `request_clarification` · `close` · `reopen`
- `GET  /api/trench-safety/excavations/reports/summary` — Safety/Admin oversight roll-up

### 2.2 Data Model — `trench_excavations` collection

Year-scoped permanent IDs: `EX-YYYY-###` (never reused). Status state machine: `Submitted` → `Needs Review` / `Action Required` → `Pending Verification` → `Reviewed` / `Closed` / `Reopened`. Free-text fields preserved verbatim (EN or ES) per directive.

### 2.3 Reused certified infrastructure (no architecture drift)

- **Audit:** every submit and review writes `audit_events` via `write_audit`.
- **Notifications:** `event_fanout.emit_notification(kind="trench_excavation_submitted" | "trench_excavation_{action}")` — same fanout pipeline as Phase 7.5C.
- **Asset linkage:** `assigned_asset_ids` references the certified `trench_safety_assets` registry; no duplicate inventory created.
- **Daily Report tie-in:** on submit, the workflow performs a read-only lookup against `daily_reports` matching `project_name` + `report_date` and stores any matches in `daily_report_links` on the excavation document. The `daily_reports` collection is **not** modified.

---

## 3 · DETERMINISTIC OSHA FLAG ENGINE (10 FLAGS — COACHING LANGUAGE)

Source: `/app/memory/OSHA_SUBPART_P_GAP_ANALYSIS.md`. All flags use coaching language (`Needs Review` or `Action Required`); punitive vocabulary is forbidden and pytest-guarded.

| # | Code                    | Trigger                                                        | Level             |
|---|-------------------------|----------------------------------------------------------------|-------------------|
| 1 | `ACCESS_EGRESS`         | depth ≥ 4 ft AND access/egress not installed                   | Action Required   |
| 2 | `PROTECTIVE_SYSTEM`     | depth ≥ 5 ft AND protective system unset/Not Required          | Action Required   |
| 3 | `SOIL_UNKNOWN`          | soil = "Unknown / Needs Review"                                | Needs Review      |
| 4 | `UTILITY_LOCATE`        | work_type contains "Utility" AND locate_status = "Pending"     | Action Required   |
| 5 | `WATER`                 | water present AND dewatering not active                        | Needs Review      |
| 6 | `ATMOSPHERE`            | atmospheric concern AND testing not completed                  | Action Required   |
| 7 | `TRENCH_BOX_ASSIGNMENT` | Trench Box / Shielding selected with no asset ID linked        | Needs Review      |
| 8 | `ROAD_PLATE_ASSIGNMENT` | Roadway excavation with no asset ID linked                     | Needs Review      |
| 9 | `SPOIL_SETBACK`         | spoils less than 2 ft from edge                                | Action Required   |
| 10 | `REINSPECTION`         | reinspection required AND reinspection not completed           | Action Required   |

Status derivation: `Action Required` overrides `Needs Review`; clean records resolve to `Submitted`. Verified by `test_status_action_required_takes_priority` and `test_clean_record_submitted_status`.

---

## 4 · TESTING EVIDENCE

### 4.1 Backend pytest — 25/25 GREEN

```
tests/test_trench_safety_phase10a.py        ........  (8 passed)
tests/test_trench_safety_phase10a_flags.py  .................  (17 passed)
```

Coverage: public submit (no auth) · EX-YYYY-### ID format + uniqueness · all 10 OSHA flags individually · coaching-language-only guard · status priority · clean-record path · asset-ID persistence · Spanish-text persistence · full review action matrix · reports summary shape · list filter by status.

### 4.2 Regression — 50/50 Phase 8–9B continue to pass

`tests/test_trench_safety_phase8a..9b.py` — 50 tests, 0 failures.

### 4.3 UI parity validation — testing_agent_v3_fork

See `/app/test_reports/iteration_phase10a_core.json`. All directive bullets verified:

| Directive bullet                          | Test agent verdict |
|--------------------------------------------|---------------------|
| Existing public safety header              | ✅ `public-excavation-header` present |
| Back button / Back to Safety navigation    | ✅ `public-excavation-back` routes to `/trench-safety` |
| MASCI/ForgedOps theme consistency          | ✅ Slate-900 / cyan-700 palette adopted |
| EN/ES toggle in same location              | ✅ Inside `PublicTrenchHeader`, identical placement |
| Same button + card styling                 | ✅ |
| Same section header style                  | ✅ font-mono cyan-700 eyebrow |
| Same alert/banner styling                  | ✅ Red Stop-Work + Amber Coaching |
| Same mobile spacing                        | ✅ `max-w-3xl mx-auto px-4 sm:px-6 py-5` |
| Footer/help language                       | ✅ "MASCI Operations Platform · Field-safe view" |
| Public Safety Tile shell consistency       | ✅ Excavation tile lives on `/trench-safety` dashboard |
| End-to-end public submit                   | ✅ EX-2026-### returned with status + flags rendered |
| OSHA flag rendered on success card         | ✅ `exc-flag-PROTECTIVE_SYSTEM` verified |
| Coaching language only                     | ✅ Pytest `test_flag_coaching_language_only` GREEN |

### 4.4 Minor i18n patch applied during certification

The testing agent flagged one detail: the header back-link did not translate to Spanish. Patched by adding three i18n keys to `/app/frontend/src/lib/i18n.js`:
- `"Back to Trench Safety"` → `"Volver a Seguridad de Zanjas"`
- `"Back to Safety"` → `"Volver a Seguridad"`
- `"Cancel · Back to Trench Safety"` → `"Cancelar · Volver a Seguridad de Zanjas"`

---

## 5 · FILES TOUCHED / CREATED THIS SPRINT

| Path                                                                      | Status     |
|---------------------------------------------------------------------------|------------|
| `/app/backend/routes/trench_safety/excavations.py`                       | Hardened (daily-report linkage added) |
| `/app/frontend/src/pages/trench_safety/PublicExcavationForm.jsx`         | **Refactored to parity shell** |
| `/app/frontend/src/pages/trench_safety/ExcavationOversight.jsx`          | Verified (uses `TrenchSafetyShell`) |
| `/app/frontend/src/pages/trench_safety/PublicTrenchSafetyDashboard.jsx`  | Tile tone cleanup (removed invalid `tone="info"`) |
| `/app/frontend/src/lib/i18n.js`                                          | +3 ES keys for back-link |
| `/app/backend/tests/test_trench_safety_phase10a_flags.py`                | New — 17 OSHA + status + persistence tests |
| `/app/memory/PHASE10A_CORE_PUBLIC_EXCAVATION_WORKFLOW_CERTIFICATION.md`  | New — this file |

---

## 6 · OUT OF SCOPE — DEFERRED (per directive)

The following remain on the Phase 10A.2 / Phase 11 backlog and were **intentionally not built** in this sprint:

- PM Portal read-only excavation surface
- Admin advanced configuration (custom flag thresholds, custom statuses)
- Spanish-to-English LLM translation of free-text notes
- CSV import for excavation records
- Advanced analytics dashboards
- Training Center, OSHA Library, Global Search, OCR / Vision

---

## 7 · RECOMMENDATION

✅ **PASS** — Phase 10A Core is certified production-ready. G-1 (Excavation Record gap) of OSHA Subpart P is now closed. Proceed when authorized to:

1. Phase 10A.2 (deferred items above), OR
2. Phase 11 — Final Certification of the Trench Safety Operations System.

The single pre-existing P2 issue (`test_trench_safety_phase2.py::test_dashboard_seed_data` stale fixture) remains untouched per directive — it does not block Phase 10A and is queued for a post-certification fixture-isolation pass.

---

*Certified under the OMEGA Directive · Public Excavation Operations Workflow Sprint · MASCI Operations Platform.*
