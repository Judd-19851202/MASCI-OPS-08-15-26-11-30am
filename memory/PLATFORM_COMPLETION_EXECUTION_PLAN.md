# PLATFORM COMPLETION · EXECUTION PLAN

**Authority**: FOCP WAR ROOM · Phase 4
**Mode**: READ-ONLY engineering plan · one block per ACTIVE finding
**Date**: 2026-06-02T23:22 UTC

---

## TR-0001 · JHP Acknowledgement Ledger build

### Scope
* New collections: `jhp_documents`, `jhp_acknowledgements`
* 7 backend endpoints (per `JHP_LEDGER_SPECIFICATION.md`)
* 3 frontend surfaces: operator ledger · employee ack · (optional Phase-2 kiosk)
* RBAC: Safety + Admin write; employee write own ack
* Bilingual EN/ES on the employee-facing flow
* Audit-log integration
* PDF export

### Risk
* **Medium**. New module · new collections · cross-references existing `employee_master` + `projects` + audit log.
* Bilingual content gating depends on TR-D004 unblocking; can ship monolingual first.
* Mitigation: ship operator-side ledger first (week 3-4) to validate query shape before exposing employee flow.

### Effort
* Backend: 5 – 7 days
* Operator UI: 4 days
* Employee UI: 3 days
* Bilingual + i18n: 2 days
* Tests + integration: 3 days
* **Total: 17 – 19 days · ~ 3.5 working weeks**

### Dependencies
* `employee_master` collection schema stable ✅
* `projects` collection schema stable ✅
* Audit-log infrastructure ✅
* Signature capture component ✅ (already used on incident/inspection forms)
* (Optional) TR-D004 Spanish reviewer for ES content — DEFERRED dependency · ship EN-only first if unavailable

### Build order
1. Backend collections + indexes (day 1)
2. Backend endpoints `POST /api/jhp/documents` + `GET /api/jhp/documents/active` (day 2)
3. Backend endpoints `POST /api/jhp/acknowledgements` + `GET /api/jhp/acknowledgements` (day 3-4)
4. Backend endpoints `GET /api/jhp/ledger/project/{id}` + `GET /api/jhp/ledger/employee/{id}` (day 5-6)
5. Operator ledger UI · skeleton + project picker + table (day 7-9)
6. Operator drill-down + bulk re-ack reminder + CSV/PDF export (day 10)
7. Employee ack UI · list + read + signature + submit (day 11-13)
8. Bilingual content integration (day 14-15)
9. Integration tests (day 16-17)
10. Smoke + operator review + retire (day 18-19)

### Success criteria
* All 7 endpoints respond per spec · RBAC verified · audit log captures every event
* Operator can produce an audit PDF for any (project, jhp_version, date_range)
* Employee can ack a JHP from in-app within 60 seconds end-to-end
* Re-ack required when JHP version increments — verified by automated test
* Operator ledger refresh < 5 s for 200-crew projects
* Zero cross-tenant leakage (single-tenant verification: only MASCI data)

### Retirement criteria
* TR-0001 moves to RETIRED when:
  * 8 endpoints implemented + green tests
  * 2 UI surfaces shipped
  * Operator captures `verified_ui_date`
  * Operator captures `verified_production_date` (post-deploy)
  * Commit message includes `Closes TR-0001`

---

## TR-0002 · Universal undo / status reversal verb

### Scope
* New backend endpoint pattern: `POST /api/{collection}/{id}/undo-last-status`
* Per-collection wiring: Incident · Daily Report · QA/QC · Site Inspection · Employee · PO · Time-Off · Asset Transfer · Payroll Variance · Dispatch · Equipment · Field Leadership (≈12 collections)
* Backend logic: read `status_history[-1]`, write inverse transition with `undo: true` flag in audit, set `lifecycle_state` to previous value, increment `undo_count`
* 30-day TTL on undo eligibility (`status_history[-1].at` must be within 30 days)
* Frontend: top-level "Undo Last Status Change" button on the canonical detail page · gated by RBAC + TTL
* Confirmation dialog with required note ("Why are you undoing this?")
* Audit log entry capturing actor + reason + before/after state

### Risk
* **Medium-high**. Cross-cutting · touches 12 collections · introduces a new audit-log event type.
* Edge case: undoing an undo (infinite chain) — limit to 1 level deep · subsequent undos require manual correction.
* Edge case: undoing a state change that triggered side-effects (notifications already sent · PDFs already generated) — document doctrine: side-effects do NOT roll back, only the state field rolls back.

### Effort
* Backend core: 3 days
* Per-collection wiring (12 × 0.25 day): 3 days
* Frontend universal-undo button component + per-page integration: 3 days
* Confirmation dialog + reason capture + audit log: 1 day
* Tests (must include "side-effects don't roll back" assertion): 2 days
* **Total: 12 days · ~ 2 working weeks**

### Dependencies
* Audit-log schema can accept a `parent_event_id` field to link the undo to the undone event (small migration)
* `status_history` must be present on every targeted collection — verified in `ACCOUNTABILITY_MATRIX.md`
* TR-0005 helps with displaying the "previous state" in the confirmation dialog, but is not blocking

### Build order
1. Backend core logic + audit-log schema extension (day 1-3)
2. Wire 4 collections (Incident · Daily Report · QA/QC · Site Inspection) for first ship (day 4)
3. Wire 4 collections (Employee · PO · Time-Off · Asset Transfer) (day 5)
4. Wire 4 collections (Payroll Variance · Dispatch · Equipment · Field Leadership) (day 6)
5. Frontend universal-undo button component (day 7)
6. Per-page integration · 12 detail pages (day 8-9)
7. Confirmation dialog · reason capture · doctrine doc on side-effects (day 10)
8. Tests + smoke (day 11-12)

### Success criteria
* All 12 lifecycle-bearing detail pages expose Undo Last Status Change
* Undo button gates correctly on TTL · RBAC · undo-of-undo
* Audit-log captures actor + reason + before/after for every undo
* Doctrine doc `UNDO_DOCTRINE.md` shipped explaining side-effect non-rollback

### Retirement criteria
* TR-0002 moves to RETIRED when all 12 detail pages verified + doctrine doc shipped + `Closes TR-0002` commit message.

---

## TR-0003 · Sub/Vendor archive workflow

### Scope
* Add `is_archived` (bool) + `archived_at` + `archived_by` + `archive_reason` fields to vendor/sub collection
* Backend endpoint `POST /api/{vendor-route}/{id}/archive` with reason
* Backend endpoint `POST /api/{vendor-route}/{id}/restore` (paired)
* Frontend: top-level "Archive" verb on vendor/sub detail · list-page filter chip Active / Archived

### Risk
* **Low**. Standard CRUD-adjacent · soft-delete pattern already used elsewhere.

### Effort
* Backend: 2 days (route + RBAC + audit)
* Frontend: 2 days (list filter + detail button + dialog with reason)
* Tests: 1 day
* **Total: 5 days · ~ 1 working week**

### Dependencies
* Identify the actual vendor/sub source-of-truth collection (likely under `admin_lookups.py` or a new file) — needs a 30-min source pass at sprint start

### Build order
1. Locate vendor/sub collection + page (day 1 morning)
2. Add fields · expose endpoints (day 1-2)
3. Wire list-page filter (day 3)
4. Wire detail-page Archive verb + reason dialog (day 4)
5. Tests + smoke (day 5)

### Success criteria
* Admin can archive any sub/vendor with a required reason
* Archived subs do not appear in default list views · appear under Archived filter
* Restore button on archived detail page returns to Active
* Audit log captures both events

### Retirement criteria
* Endpoints + UI verified · `Closes TR-0003` commit.

---

## TR-0005 · Status canonical dictionary

### Scope
* New helper `frontend/src/lib/statusDisplay.js` exporting `statusDisplay(workflow, backendStatus) → { label, color, icon }`
* Per-workflow mapping table covering all 38 distinct status words → 7 canonical labels (per `STATUS_CANONICAL_DICTIONARY.md`)
* Status-badge component adoption across list-page rows + detail-page state pills
* Inline migration: replace raw `<Badge>{backendStatus}</Badge>` with `<CanonicalStatusBadge workflow="qaqc" status={record.status} />`

### Scope · what NOT to do
* Do NOT rename backend status names. Backend keeps workflow-specific state-machine vocabulary.
* Do NOT touch HR `5-statuses` storage doctrine; only display.

### Risk
* **Low**. Pure-display refactor · zero backend change · per-page sweep is mechanical.

### Effort
* Helper + mapping table: 2 days
* Component (`CanonicalStatusBadge`): 1 day
* Per-page sweep (~ 25 list pages + 15 detail pages): 3 days
* Tests + storybook + i18n hookup: 2 days
* **Total: 8 days · ~ 1.5 working weeks** (estimate widened from prior 1-week for the per-page sweep)

### Dependencies
* TR-0001 ships first to surface any new statuses introduced by JHP
* Phase 12 interviews (TR-D002) ideally inform the mapping table before sweep — at minimum, the operator should review the proposed mapping in `STATUS_CANONICAL_DICTIONARY.md` § Canonical Mapping before sweep starts

### Build order
1. Operator review of canonical mapping (day 0 · operator-led)
2. Helper + mapping table (day 1-2)
3. `CanonicalStatusBadge` component (day 3)
4. Per-page sweep · batch 1 (Incident / Daily Report / QA/QC / Site Inspection) (day 4)
5. Per-page sweep · batch 2 (Employee / HR Queue / PO / Time-Off) (day 5)
6. Per-page sweep · batch 3 (Asset Transfer / Dispatch / Equipment / Driver Qual / FleetDVIR) (day 6)
7. Tests + storybook (day 7-8)

### Success criteria
* Every status pill on the platform shows a canonical label + color + icon
* Operator reviews 10 random pages and confirms vocabulary consistency
* No raw backend status string visible to a non-admin user

### Retirement criteria
* All ~ 40 pages swept · screenshot evidence in `verified_ui_date` · `Closes TR-0005` commit.

---

## Cross-cutting governance

For each TR above:

* Every commit message includes `Closes TR-####`
* Every PR description references the corresponding `*_SPECIFICATION.md` or this execution plan
* Every retirement entry in `TRUTH_REGISTER.md` cites file + line numbers
* Every UI-facing retirement captures `verified_ui_date` (screenshot)
* Operator captures `verified_production_date` post-deploy

---

End of Phase 4 execution plan.
