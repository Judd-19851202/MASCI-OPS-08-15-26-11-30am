# TRACK 19.23 · 24-Hour Live Pilot Plan

## Pilot users (5 real humans + 1 executive shadow)

| Role | Assigned user | Portal | Token localStorage key |
|---|---|---|---|
| HR Administrator | 1 designated HR user | `/hr/login` or `/sign-in` | `masci.hr.token` |
| Safety Director | 1 safety user | `/safety/login` | `masci.safety.token` |
| Asset Administrator | 1 shop user w/ `is_asset_admin=true` | `/shop/login` | `masci.shop.token` |
| Project Manager | 1 designated PM | `/pm/login` | `masci.pm.token` |
| Shop user (non-asset-admin) | 1 mechanic | `/shop/login` | `masci.shop.token` |
| Field foreman | 1 crew lead | `/field` | (public / limited scope) |
| Executive (shadow) | 1 owner | Reads produced PDFs only | — |

## Pilot tasks (24-hour cycle)

### Task 1 · Daily Report .xlsm attachment (Field foreman + PM)
1. Foreman submits Daily Report at end of shift with an `.xlsm` production sheet + 3 photos.
2. PM reviews same day in PM portal; verifies `.xlsm` link opens correctly (Spreadsheet label).
3. Admin verifies historical detail view shows same attachment.
4. **Success criteria:** attachment appears in submitted payload, PM portal, historical detail, email link section. Label reads "Spreadsheet." Download preserves `.xlsm` extension.

### Task 2 · Incident Report (Foreman or Safety)
1. Foreman submits a near-miss incident report.
2. Safety opens Safety Case Workspace; verifies branching, timeline, evidence.
3. Safety generates Executive PDF.
4. **Success criteria:** case renders without ugly empty sections; PDF is one-story narrative; assigned to correct Safety recipient.

### Task 3 · Safety Case review (Safety)
1. Safety opens an existing case in `/safety/cases/:caseId`.
2. Confirms timeline includes any linked Employee 360° events (Track 19.21 fan-in).
3. **Success criteria:** case ↔ employee bidirectional linkage visible from both surfaces.

### Task 4 · Historical HR record upload + approval (HR)
1. HR uploads one termination letter for a real employee via `/hr/historical-records/intake`.
2. HR approves in `/hr/historical-records/queue`.
3. HR opens Employee 360° → Documents tab → verifies the letter appears.
4. HR generates Complete Employee File PDF.
5. **Success criteria:** end-to-end < 4 minutes; PDF includes the new record.

### Task 5 · Historical Safety record upload (Safety)
1. Safety uploads a training certificate via intake with lane=Safety.
2. Safety approves.
3. Safety attempts to approve an HR-lane record from someone else's staging → verifies 403.
4. **Success criteria:** Safety cannot exit their lane; own-lane workflow smooth.

### Task 6 · Historical Asset record upload (Asset Admin)
1. Asset Admin uploads a PPE issuance record with asset link.
2. Asset Admin approves.
3. Asset Admin generates PPE / Asset Package.
4. **Success criteria:** package renders; asset link visible in record card.

### Task 7 · Bulk batch flow (HR)
1. HR creates a bulk batch labeled "2024 Personnel Files."
2. HR uploads 10-20 mixed PDF/xlsm files (real historical files if available; else pilot dummies).
3. HR classifies all as `hr_document`, assigns to a batch employee, sets effective date.
4. HR approves-all.
5. **Success criteria:** 10-20 records land on that employee's 360° in one session; ledger has 10-20 `record_created` + `record_batch_apply` + `record_approved` events per record.

### Task 8 · Export packages (HR + Executive)
1. HR generates all 6 packages for one employee.
2. Executive reviews each PDF for quality.
3. **Success criteria:** professional typography, no N/A spam, footer provenance visible.

### Task 9 · Email routing audit (any user + audit collection observer)
1. After Tasks 1-3 fire real notifications, observer queries `db.email_routing_audit_v2` to verify recipients + dedup keys + no duplicates.
2. **Success criteria:** every dispatch has an audit row with `dry_run=false`, expected recipients, expected subject.

## Monitoring during pilot

| Signal | Where | Stop condition |
|---|---|---|
| `email_routing_audit_v2` | MongoDB collection | Duplicate emails · unexpected recipients |
| Backend Sentry (if enabled) | Sentry dashboard | Any Track 19.19-22 unhandled exception |
| `/api/health` | curl or uptime monitor | 5xx > 30 seconds |
| Upload failures | Backend logs `[employee_records]` | Any 500 on `/uploads` |
| PDF generation failures | Backend logs | Any 500 on `/exports/*` |
| Permission denials | 403s on user actions | Unexpected 403 for a role that should have access |
| Support tickets | Slack / email | Any P0 usability blocker |
| User feedback | Live check-ins hour 6, 12, 24 | Any "I can't do X" report |

## Stop conditions (auto-abort pilot)
- Duplicate email received by same recipient for same event.
- Any `.xlsm` upload failure with 500.
- Wrong recipient on any notification.
- Any permission leak (Safety accessing HR lane, or vice versa).
- Any PDF returning corrupted bytes (magic bytes ≠ `%PDF`).
- Employee 360° missing an approved record.
- Any `db.employees` document modified by a Track 19.21-22 code path.

## Rollback plan (if pilot aborts)
- Backend routes are additive-only. Disable `/api/employee-records/*` router by commenting out `app.include_router(build_employee_records_router(...))` in `server.py`.
- Frontend routes are additive-only. Remove new routes from `App.js`.
- No schema migration needed — `db.employee_records`, `db.record_import_batches`, `db.employee_record_audit` remain in place but unused.
- No employee/incident data was touched; nothing to roll back on the roster or case sides.

## Pilot success declaration (24 hours later)
All 9 tasks completed without a stop condition ⇒ **Production Deploy: GO.**

**Verdict:** Plan is human-scoped, single-cycle, monitored, and reversible.
