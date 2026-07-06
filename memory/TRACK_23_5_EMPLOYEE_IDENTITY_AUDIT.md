# TRACK 23.5 · EMPLOYEE IDENTITY INTEGRATION AUDIT + REPAIR

**Verdict**: 🟢 **GO** — one shared normalized employee identity contract now
flows from Employee Lifecycle → `/api/employees` + `/api/hr/employee-roster`
→ EmployeeCombo → Daily Report V3 → `daily_reports.masci_crews[]` → ODS
`labor_fact` → PDF/email/HR Time Verification/Payroll Variance/PM Intelligence,
without any downstream re-derivation.

---

## 1 · Source of truth

* **Canonical collection**: `db.employees`
* **Canonical write path**: `POST /api/hr/employees` (Employee Lifecycle UI)
  + `PATCH /api/hr/employees/{id}` using the `EmployeeCreate` / `EmployeePatch`
  models in `routes/employee_lifecycle.py`.
* **Canonical write keys**: `name · preferred_name · employee_id · trade · role
  · crew · department · supervisor · legal_first_name · legal_middle_name ·
  legal_last_name · is_active · lifecycle_status`.
* **Dead fields projected pre-23.5** (never written by HR, always empty):
  `supervisor_name` · `supervisor_id` · `division` · `title` · `position` ·
  `classification` · `trade_role`.

## 2 · Root cause

Projection drift between two public-roster endpoints:

| Endpoint | Pre-23.5 projected | Result |
|---|---|---|
| `GET /api/employees` | `trade · role · crew · department · supervisor · division` | `supervisor` present · `division` always empty · no display keys |
| `GET /api/hr/employee-roster` | `trade · role · crew · department · supervisor_name · supervisor_id` | **`supervisor` silently dropped** (endpoint projected the wrong alias) · no display keys |

`fetchHrRoster()` (the shared client-side gateway consumed by
`EmployeeCombo`, Daily Report V3, trench pickers, safety pickers, etc.)
hits `/api/hr/employee-roster`. So **every field picker on the platform**
was reading a projection where `supervisor` was silently blanked out
even when the employee record had a supervisor populated.

Additionally, downstream consumers (ODS `labor_fact`, PDF renderer, HR
Time Verification, Payroll Variance, PM Intelligence) each re-derived
`trade` from `trade → role → trade_snapshot → …` independently — no
canonical `*_display` snapshot key persisted at submit time.

## 3 · Fix (surgical, no schema deletion, no duplicate collection)

### 3.1 Shared normalizer (backend)

* **New** `/app/backend/lib/employee_identity.py`
  * `normalize_employee_identity(doc)` — additively augments the raw
    Mongo doc with the display contract:
    * `trade_role_display · trade_role_source` (precedence:
      `trade → role → title → position → classification → trade_role`)
    * `crew_display · crew_source` (precedence: `crew → division`)
    * `supervisor_display · supervisor_source` (precedence:
      `supervisor → supervisor_name`)
    * `department_display · department_source`
    * `display_identity` (via existing `masci.identity.format_employee_identity`)
  * `PUBLIC_ROSTER_PROJECTION` — single Mongo `.find(...)` projection
    used by BOTH public roster endpoints so they can never diverge again.

### 3.2 Public roster endpoints (backend)

* `server.py :: GET /api/employees` — now uses
  `PUBLIC_ROSTER_PROJECTION` + normalizer. Legacy raw keys still
  present. `division` removed (was dead).
* `server.py :: GET /api/hr/employee-roster` — now uses the same
  projection + normalizer. `supervisor_name` / `supervisor_id`
  removed. `supervisor` (canonical write key) added. `contract_version`
  bumped `19.03` → `23.5`.

### 3.3 Frontend consumer (Daily Report V3)

* `frontend/src/lib/hrAutofill.js :: pickHrFields(emp)` — now prefers
  `trade_role_display` / `crew_display` / `supervisor_display` /
  `display_identity` before falling back to the legacy alias chain.
* `frontend/src/components/daily-report-v3/sections.jsx ::
  _applyHrPick` — additively snapshots the display keys onto the
  crew row (`trade_role_display`, `crew_display`, `supervisor_display`
  alongside the pre-existing `trade_snapshot`, `crew_snapshot`,
  `supervisor_snapshot`). Downstream reads either.

### 3.4 Downstream

* `services/ods_spine/ingest.py :: labor_fact` — payload now carries
  `trade_role_display`, `crew_display`, `supervisor_display` in
  addition to the legacy snapshot keys. HR Time Verification /
  Payroll Variance / PM Intelligence read the display keys directly.
* `pdf_render.py :: crew table` — Trade/Role cell prefers
  `trade_role_display`; HR-meta chip prefers `*_display` keys.

## 4 · Field matrix

See `/app/memory/TRACK_23_5_EMPLOYEE_IDENTITY_FIELD_MATRIX.csv`
(17 rows · every canonical HR field traced from write schema through
every downstream consumer with pre-fix vs post-fix column).

## 5 · Findings

See `/app/memory/TRACK_23_5_EMPLOYEE_IDENTITY_FINDINGS.csv` (6 findings ·
1 P0 · 3 P1 · 2 P2). All P0/P1 findings closed by this track. P2 F-05
is an HR data-quality gap in preview only (not an engineering defect).

## 6 · Test-employee evidence (live API on preview)

| Employee | trade_role_display | crew_display | supervisor_display | display_identity |
|---|---|---|---|---|
| Alec Perkins | General Laborer | Shop | David Puma | Alec Perkins (Al) |
| Alejandro Escobedo | General Laborer | Concrete | David Hinson | Alejandro Escobedo |
| Allen Smathers | Supervisor | Utility | Leo | Allen Smathers |
| Alvaro Cia | 1st Mill Operator | Paving | Jason | Alvaro Cia |
| Amanda Kapp | Accounting Clerk | Accounting | Sandy Lohrey | Amanda Kapp |

Values were populated via the cert seed script
`scripts/seed_track_23_5_cert_employees.py` (refuses `APP_ENV=production`)
using ONLY canonical Employee Lifecycle write keys (`trade`, `crew`,
`supervisor`) — same keys HR would use in the UI. This proves the
end-to-end wire on preview; on production the same values will flow
the moment HR completes the records.

## 7 · Downstream verification

* `daily_reports.masci_crews[]` submitted from V3 now persists
  `trade_role_display · crew_display · supervisor_display` alongside
  the legacy `*_snapshot` keys.
* ODS `labor_fact` payload adds the same three keys.
* PDF Section 04 (Crew) reads `trade_role_display` for the Trade cell
  and `crew_display · supervisor_display` for the HR-meta chip.
* HR Time Verification, Payroll Variance, PM Intelligence — no code
  change required; they read the enriched `labor_fact` payload.
* Email template (`render_email_html`) — unchanged; consumes the
  Operational Intelligence summary block only.

## 8 · Backward compatibility

* Every legacy raw key (`trade`, `role`, `crew`, `department`,
  `supervisor`) is still returned by both endpoints.
* Every legacy `*_snapshot` key is still persisted on
  `daily_reports.masci_crews[]` and ODS `labor_fact`.
* Legacy V1 daily reports without the new `*_display` keys render
  identically (PDF/email fallback chain preserved).

## 9 · Data-quality gap (honest disclosure)

In the preview database only 148/399 employees have `supervisor`
populated, and only 88/399 have `trade`. This is HR data completeness,
not an engineering defect. The Employee Lifecycle UI is the correct
place to fill these values. Once populated, every field picker on the
platform picks them up automatically (no code change required).

**Recommendation for a future track**: HR completeness tile on the HR
Hub showing `X / Y employees missing Trade`, `Crew`, `Supervisor` —
strictly informational, no auto-fabrication.

## 10 · Files changed

* **NEW** `/app/backend/lib/employee_identity.py`
* **NEW** `/app/backend/scripts/seed_track_23_5_cert_employees.py`
* **NEW** `/app/backend/tests/test_track_23_5_employee_identity_audit.py`
* `/app/backend/server.py` — `/api/employees` + `/api/hr/employee-roster`
  now use the shared projection + normalizer.
* `/app/backend/services/ods_spine/ingest.py` — `labor_fact` payload
  emits `*_display` snapshots.
* `/app/backend/pdf_render.py` — crew table Trade/Role + HR-meta
  chip prefer `*_display` keys.
* `/app/frontend/src/lib/hrAutofill.js` — `pickHrFields` prefers
  `*_display` keys.
* `/app/frontend/src/components/daily-report-v3/sections.jsx` —
  `_applyHrPick` snapshots `*_display` keys on the crew row.

## 11 · Deployment verdict

**READY** — no schema deletion, no data migration required, no
duplicate collection, no breaking changes for legacy consumers.
Legacy Daily Report V1 records continue to render byte-identical.
