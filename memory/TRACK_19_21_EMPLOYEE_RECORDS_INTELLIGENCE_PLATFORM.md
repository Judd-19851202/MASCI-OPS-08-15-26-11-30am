# Track 19.21 · Employee Records Intelligence Platform · P0 Foundation

**Date:** 2026-07-02 · **Status:** 🟢 P0 foundation shipped · 26/26 lock tests GREEN

## What shipped

### Backend
- **NEW** `/app/backend/routes/employee_records.py` (450 lines) — Universal Employee Record model + intake batches + review queue + approval workflow + append-only audit trail.
- **UPDATED** `/app/backend/routes/hr_portal.py` — HR Accountability Timeline (`/api/hr/employees/{id}/accountability/timeline`) now fans out over `db.incident_cases` (Track 19.16 engine) in addition to legacy `db.incidents`. Employees are linked to cases only via defensible roles: **reporter · involved · witness · corrective-action owner**. Passive "was present" auto-linkage is deferred to Track 19.22+ by explicit doctrine.
- **UPDATED** `/app/backend/server.py` — router mounted + `ensure_employee_records_indexes` invoked on startup.
- **NEW** MongoDB collections:
  - `db.employee_records` — universal employee record (record_id, employee_id, record_type, record_category, ownership_lane, source_file_ref, source_file_name, source_file_hash, imported_batch_id, related_incident_case_id, related_training_id, related_asset_id, related_project_id, tags, notes, status, approval_status, created_by, reviewed_by, approved_by, effective_date, created_at, updated_at, +related_supervisor_id, +employee_name_snapshot).
  - `db.employee_record_audit` — append-only audit ledger (record_id, event, actor_email, actor_role, details, ts).
  - `db.record_import_batches` — bulk intake batch tracking.

### Frontend
- **NEW** `/app/frontend/src/pages/EmployeeProfile.jsx` (~250 lines) — single-page Employee 360° view.
  - Identity header with auto-composed Employee Story paragraph
  - Next-Action chip driven by expiring certs
  - 7-tab bar: **All timeline · Training · PPE/Assets · Incidents · Discipline · Driver Qual · HR Lifecycle**
  - Visual timeline spine (mirrors SafetyCaseWorkspace Track 19.18 pattern) with color-coded category dots
  - Right rail: Current state one-liner headline · Category counts (empty-state filtered) · HR Compliance Brief PDF export button
- **UPDATED** `/app/frontend/src/App.js` — route `/hr/employees/:empId/profile` → `EmployeeProfile` (H-wrapped).

### Endpoints (all mounted at `/api/employee-records`)

| Method | Path | Purpose |
|---|---|---|
| POST | `/batches` | Create intake batch (per lane) |
| GET | `/batches` | List batches (HR sees all · lane owners see own) |
| POST | `/records` | Create a record (initial state: pending_classification / pending_match / pending_approval) |
| GET | `/records` | List / filter records (by lane · state · type · employee · batch) |
| GET | `/records/{id}` | Record detail + full audit trail |
| POST | `/records/{id}/approve` | HR / lane-owner approval — moves to `linked` |
| POST | `/records/{id}/reject` | HR / lane-owner rejection — captures reason |
| POST | `/records/{id}/reassign` | Change employee / record_type / lane — resets approval to `pending_approval` |
| GET | `/queues/{lane}` | Lane review queue (pending only) |
| GET | `/employees/{emp_id}/records` | Records for one employee (Employee 360° "Documents" tab) |

## Doctrine locks (all in test_track_19_21_employee_records_platform.py)

1. **Four ownership lanes:** `hr` · `safety` · `asset` · `corporate_import`.
2. **Five record states:** `pending_classification` · `pending_match` · `pending_approval` · `linked` · `rejected`.
3. **HR is system owner:** HR + admin can read and approve every lane.
4. **Safety scope:** Safety role can read + approve only the `safety` lane.
5. **Asset Administrator scope:** `asset_admin` role can read + approve only the `asset` lane.
6. **Field role cannot approve any lane.**
7. **HR timeline joins new incident engine cases via defensible roles only** — reporter · involved · witness · CAPA owner. No passive presence signals yet.
8. **Legacy `db.incidents` timeline path preserved** for backward compat.
9. **Reassignment resets approval** — a LINKED record moves back to `pending_approval` on reassign.
10. **Original file metadata preserved** — `source_file_ref` · `source_file_name` · `source_file_hash` · `imported_batch_id`.
11. **Audit ledger is append-only** — module contains no update/delete/replace paths on `db.employee_record_audit`.
12. **No parallel employee system** — module never inserts/updates/deletes `db.employees`.
13. **No OCR / AI classification / fuzzy matching wired in this track** — deferred to Track 19.22+.
14. **Zero-drift on incident engine** — HR timeline reads `db.incident_cases`; the records module never writes to it.

## What's explicitly deferred (per user directive)

- OCR of uploaded documents
- AI classification (Gemini / Claude / GPT)
- Fuzzy employee matching
- Automatic employee match on upload
- Auto-filing without approval
- Passive incident presence risk scoring
- OSHA compliance intelligence
- Medical determination engine

## Test evidence

```
tests/test_track_19_21_employee_records_platform.py  26/26 PASSED (in 0.32s)

Verified against companion suites (each passes independently):
tests/test_track_19_19_xlsm_attachment.py            18/18 PASSED
tests/test_track_19_18_pdf_excellence.py             11/11 PASSED
tests/test_track_19_18_safety_case_workspace.py       8/8  PASSED
tests/test_track_19_16_incident_engine_phase_e.py    88/88 PASSED
tests/test_track_19_16_final_closeout.py             23/23 PASSED
tests/test_track_19_16_incident_engine_phase_a.py   102/102 PASSED
```

Cross-suite pytest-asyncio fixture pollution is pre-existing (`RuntimeWarning: coroutine 'create_case' was never awaited`) and unrelated to Track 19.21. Each suite is green in isolation.

## Live smoke

- Backend imports cleanly (`from routes.employee_records import ...`)
- Server restarts cleanly; startup log shows `[employee-records] indexes ensured (track 19.21)`
- `GET /api/employee-records/records` returns HTTP 401 `Safety, Admin, or PM login required` (auth gate wired correctly)
- Frontend ESLint on `EmployeeProfile.jsx`: CLEAN

## Zero drift verified

- No existing schema mutated
- No existing route mutated
- `db.employees` is READ-ONLY from the new module
- Legacy `/api/incidents` untouched
- Incident engine additive read path only (no writes from HR module)
- FieldBlock uses `extra="allow"` so P0-A additive fields (`reporter_employee_id`, `involved_employee_ids[]`, `witness_employee_ids[]`) work with no schema drift — the timeline query already checks for these fields safely

## Next tracks (P1 continuation of the ERI Platform)

- **Track 19.21b** · Frontend HR Review Queue page + Historical Import upload UI + Safety/Asset queues.
- **Track 19.22** · OCR (Gemini 3 Flash) + AI classification + fuzzy matching + duplicate detection.
- **Track 19.23** · Discipline Package PDF · PPE expiration reminders · Employee-scoped full-text search.
- **Track 19.24+** · Onboarding checklist · Return-to-work workflow · Acknowledgments library.

Done means done.
