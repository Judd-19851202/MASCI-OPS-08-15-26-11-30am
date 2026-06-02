# FOCP · COMPLETION RELEASE 2 · TR-0001 BUNDLE
## JHP Acknowledgement Ledger Extension

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE · FOCP RELEASE 2 (user-authorized 2026-06-02)
**Mode**: Implementation + Certification

---

## 1 · Source Certification

**Existing infrastructure extended (not replaced):**

| Surface | File / Endpoint | Behavior |
|---|---|---|
| Storage | `db.job_hazard_files` collection · `/app/backend/job_hazard_files.py` | Per-project, versioned (per upload) file library. Stores PDFs, photos, etc. Inline ≤8 MB, disk-streamed above. **Untouched.** |
| Admin upload | `POST /api/job-hazard-files` · `/app/backend/server.py:2396` | Existing multipart upload. **Untouched.** |
| Public list | `GET /api/job-hazard-files/public/grouped` · `server.py:2378` | Returns per-project file groups. **Untouched.** |
| Public page | `/app/frontend/src/pages/JhaPlansHub.jsx` (route `/jha`) | Mobile-first PDF picker. **Extended** with identity strip + per-file Acknowledge button. |
| Audit log | `db.workflow_state_events` · `/app/backend/lib/workflow_state_events.py` | Already pre-declares `workflow="jha_ack"` (line 11 of docstring). **Reused.** |
| Employee directory | `db.employees` · `GET /api/employees` | Used as the identity source of truth for ack rows. **Untouched.** |

**No replacement systems created.** No parallel JHP storage, no parallel directory, no parallel audit collection.

## 2 · Implementation Certification

### New collection: `db.jha_acknowledgements`

Schema:
```
{ id, project_number, jha_file_id, jha_filename, jha_uploaded_at,
  employee_id, employee_name, employee_email, signature,
  locale: "en"|"es", acknowledged_at: ISO-UTC, ip, user_agent }
```
Unique compound index on `(jha_file_id, employee_id)` → re-acknowledging the same file version replaces the row (the prior signature is preserved in the audit stream).

### New endpoints (`/app/backend/routes/jha_acknowledgements.py`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/jha-acknowledgements` | Public (employee identity proof) | Record an acknowledgement |
| GET | `/api/jha-acknowledgements/me` | Public (email or id) | Surface acked-files for the signed-in employee |
| GET | `/api/jha-acknowledgements/by-project/{pn}` | Admin | Roster × file matrix |
| GET | `/api/jha-acknowledgements/by-employee/{id}` | Admin | Employee acknowledgement history |
| GET | `/api/jha-acknowledgements/compliance` | Admin | Cross-project roll-up |

All wired into `server.py` via `register_jha_acknowledgement_routes(api_router, db, require_admin_dep=require_admin)` at line 2516+.

### New frontend surfaces

| File | Role |
|---|---|
| `/app/frontend/src/components/JhaAcknowledgeButton.jsx` | Reusable employee acknowledgement modal (email + typed signature). Bilingual via `useT()`. |
| `/app/frontend/src/pages/JhaPlansHub.jsx` | Extended with `<JhaAcknowledgeButton/>` per file + identity strip ("Signing as / Not me — clear") + persistent email in `localStorage["masci.jha.email"]`. |
| `/app/frontend/src/pages/admin/AdminJhaAcknowledgements.jsx` | Admin Compliance / Project drill / Employee drill on route `/admin/jha-acknowledgements`. |

### Audit twin

Every POST `/api/jha-acknowledgements` ALSO writes a `workflow_state_events` row with:
- `workflow = "jha_ack"`
- `to_state = "ACKNOWLEDGED"`
- `from_state = null`
- `actor_role = "employee"`, `actor_id`, `actor_name`
- `evidence = { project_number, jha_filename, jha_file_id, signature, locale }`

This means the Universal Recovery Stream (TR-0002) surfaces JHP acknowledgements alongside the 5 other lifecycle workflows without a second integration.

## 3 · UI Certification

- **Acknowledge button**: amber, full-tap-target (h-10 px-4), modal with two required fields (email, typed signature).
- **Identity strip** on `/jha`: shows signing-as email + count of acknowledged plans + "Not me — clear" affordance.
- **Acknowledged pill**: emerald with checkmark, replaces the Acknowledge button when the file is already signed by the current identity.
- **Admin matrix** (`/admin/jha-acknowledgements`): cross-project compliance table + project drill + employee drill, all read-only.

## 4 · Human-Operability Certification

Field-crew flow (no engineering intervention required):
1. Open `/jha` on phone → pick job → expand → tap **Acknowledge**.
2. Enter work email + type full name → tap **Sign and Acknowledge**.
3. Page now shows ✓ "Acknowledged" pill — and remembers email for next plan.

Supervisor flow:
1. `/admin/jha-acknowledgements` → see compliance table.
2. **Drill in** on any project → see every file × every acknowledgement.
3. Paste an employee UUID → see their cross-project history.

Operator can drive both surfaces start-to-end without code changes.

## 5 · Governance Certification

- Bilingual: 20 new EN/ES strings appended to `/app/frontend/src/lib/i18n.js` (canonical English keys, Spanish values verified to be operational-Spanish, no AI-translated marketing language).
- Doctrine: identity proof requires either an `employee_id` or an `employee_email` matching `db.employees`; we never mint new employees from this endpoint.
- Idempotency: re-acknowledging the same file version replaces the prior row; the original is preserved as a `workflow_state_events` row.
- No production secret was created or rotated; no `.env` mutated.

## 6 · Audit Certification

Live trace executed 2026-06-02:
```
POST /api/jha-acknowledgements  → 200
GET  /api/jha-acknowledgements/by-project/FOCP-R2-TEST-PROJ → 1 file, 1 ack
GET  /api/jha-acknowledgements/compliance → totals: 7 files, 1 ack
GET  /api/admin/recovery/transitions?workflow=jha_ack → 1 jha_ack event with full evidence
```

Append-only confirmed: 2nd ack to the same file with a different signature inserts a new `workflow_state_events` row while replacing the `jha_acknowledgements` row.

## 7 · Training / Help Impact Certification

No new help text is required for the employee flow — the modal is self-explanatory:
- "I have read this Hazard Plan and understand the site hazards, PPE requirements, and emergency response."
- "Your acknowledgement is permanent and visible to your supervisor."

The existing `HelpTipBlock formKey="jha"` already coaches employees on what the JHA is for; this remains in place.

## 8 · Spanish Impact Certification

Spanish dictionary entries appended at the canonical Job Hazard Plans block (`i18n.js` line ~1351). Crew-facing phrasing:
- "Confirmar Recibido" / "Confirmado"
- "He leído este Plan de Peligros y entiendo los peligros del sitio, los requisitos de EPP y la respuesta de emergencia."
- "Su confirmación es permanente y visible para su supervisor."

These are operational, not marketing, translations.

## 9 · Production-Readiness Certification

- Indexes: `id` unique · `(project_number, acknowledged_at desc)` · `(employee_id, acknowledged_at desc)` · `(jha_file_id, employee_id)` unique. All idempotent, swallowed on failure, armed at startup via existing `_arm_workflow_state_events_indexes` hook.
- Auth: admin-only on compliance / by-project / by-employee. Public POST requires identity proof (employee row match). Public GET `/me` returns empty when no email passed.
- Error model: stable error codes (`signature_required_min3`, `employee_not_found`, `employee_email_invalid`, `jha_file_not_found`, `jha_file_project_mismatch`) — frontend uses these to render bilingual operator-friendly toasts.

## 10 · Tests

`/app/backend/tests/test_focp_release2.py` — 14 tests passing (asserts endpoint registration, auth gates, validation paths, admin-token success paths). Run via `python -m pytest backend/tests/test_focp_release2.py`.

Frontend lint clean: `/app/frontend/src/components/JhaAcknowledgeButton.jsx`, `/app/frontend/src/pages/admin/AdminJhaAcknowledgements.jsx`, `/app/frontend/src/pages/JhaPlansHub.jsx`.

---

**TR-0001 STATUS: RETIRED**
**Resolution PR**: FOCP Release 2 (this bundle)
**Verified source date**: 2026-06-02
