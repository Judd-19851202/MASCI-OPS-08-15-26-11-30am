# WP16 Wave 4 — 8-Gate Inspection Executive Package

Date: 2026-07-30

## Executive scope statement

- Wave: **4 — HR Certification**
- Phase executed: **Phase 2 — 8-Gate Inspection**
- Production code changes made: **None**
- Repairs made: **None**
- Inspection methods used: browser verification on preview, direct API verification by curl, and targeted source-contract review

## Final denominator inspected

- **Wave 4 denominator:** `26`
- **Inspected:** `26 / 26`
- **Hidden/detail routes explicitly exercised first:**
  - `/hr/driver-qualification/import`
  - `/hr/motive-drivers`
  - `/hr/daily-reports/:id`
  - `/hr/employees/:id/accountability`
  - `/hr/employees/:id/thread`
  - `/hr/employees/:empId/profile`
  - `/hr/historical-records/batches/:batchId`
  - `/hr/driver/:driverKey` (placeholder deep-link path only; valid discovery path blocked upstream)

## Gate summary

### Gate 1 — Routing & Navigation
- All 26 inventoried routes are still registered in `AppRoutes.jsx`.
- Public redirect `/hr/forgot` correctly resolves to `/hr/login`.
- Hidden/detail routes for daily reports, employees, profile, thread, accountability, driver, and historical batches all resolve at runtime.
- Two hidden/detail discovery paths are materially degraded by open defects:
  - `/hr/motive-drivers` cannot supply a valid HR-safe driver path because it mounts admin cleanup infrastructure.
  - `/hr/historical-records/*` discovery is constrained by shared `500` failures in the employee-records foundation.

### Gate 2 — User Experience
- No broad route-shell blank-screen failure was observed across the denominator.
- Mobile spot checks on `/hr/time-off`, `/hr/employee-requests`, `/hr/employees/:id/profile`, and `/hr/historical-records/batches` showed **no horizontal overflow**.
- Active UX defects are concentrated in unauthorized helper calls and raw server error leakage:
  - unauthorized `401/403` degradation on HR-owned subworkflows
  - raw `internal_server_error` surfaced on historical-record and employee-record views
  - indefinite loading risk on batch detail when the shared batch fetch fails

### Gate 3 — CRUD Operations
- Read flows worked on: Field Leadership, Time Verification, Payroll Variance load shell, Training Records, Qualifications, Daily Reports list/detail, Safety Records, Employee Requests, Accountability detail, and Incidents.
- CRUD / governed workflow failure clusters:
  - Field Leadership Users management blocked by admin-scoped panel wiring
  - Employee Lifecycle roster management blocked by HR-permission mismatch
  - Driver Qualification dashboard/import blocked by HR-permission mismatch
  - Historical intake / batch workflows blocked by shared `500` foundation failures

### Gate 4 — API & Data Integrity
- Verified `200` responses for:
  - `/api/hr/me`
  - `/api/hr/field-leadership`
  - `/api/hr/time-verification`
  - `/api/hr/training-records`
  - `/api/hr/daily-reports`
  - `/api/hr/employee-requests`
  - `/api/hr/incidents`
- Verified open API failures:
  - `401` on `/api/admin/field-leadership-users` from the HR route
  - `401` on `/api/admin/integrations/cleanup/*` from the HR route
  - `403` on `/api/hr/employees*` for a valid HR token
  - `403` on `/api/hr/driver-qualification*` for a valid HR token
  - `401` on `/api/daily-reports/{id}/lifecycle` from HR detail view
  - `401` on `/api/operational-intelligence/summary` from HR employee thread
  - `500` on `/api/employee-records/vocabulary`
  - `500` on `/api/employee-records/batches*`
  - `500` on `/api/employee-records/employees/{empId}/records`

### Gate 5 — Permissions & Security
- **Positive finding:** `RequireHr` fail-closed behavior is working. An admin-only fixture deep-linked to `/hr/field-leadership`, `/hr/employees`, and `/hr/driver-qualification` received `403 · ACCESS RESTRICTED` in the UI.
- **Positive finding:** admin-token API attempts against HR endpoints returned `401` when no HR grant was present.
- **No unauthorized cross-portal PII exposure was observed in this pass.** Failures were predominantly fail-closed `401/403` and `500` conditions.
- **Gate 8-linked concern:** the HR owner itself is being blocked from HR-owned record and qualification workflows on multiple routes, which is a high-severity ownership/compliance failure even though it is fail-closed.

### Gate 6 — Shared Components
- Shared component / foundation defects were confirmed in this wave:
  - HR routes embedding admin-scoped panels (`AdminFieldLeadershipUsersPanel`, `MappingCleanupTab`)
  - employee-lifecycle shared permission bridge denying valid HR sessions
  - shared Employee Thread OI summary helper calling an unavailable summary feed for HR
  - shared employee-records / historical-records API foundation returning `500`

### Gate 7 — Operational Workflow
- Working or materially reachable HR workflows:
  - Field Leadership records review
  - Time Verification review
  - Training Records review
  - Qualifications registry review
  - Daily Reports list and read-only report detail
  - Safety Records review
  - Employee Requests queue review
  - Accountability detail review
  - Incidents review
- Broken or blocked HR workflows:
  - Field Leadership account management
  - Driver qualification review
  - Driver qualification import audit / apply path
  - Employee roster maintenance
  - Motive driver cleanup
  - Employee Thread guidance / OI section
  - Employee 360 document history lane
  - Historical records intake / queue / batches / batch detail

### Gate 8 — Data Integrity & Privacy (HR-Specific)
- No unauthorized PII leak was observed to non-HR actors during this inspection.
- Gate 8 failures confirmed:
  - HR record owner blocked from employee lifecycle and qualification maintenance (`WP16-W4-002`)
  - HR-sensitive historical/document record foundation returning `500` and leaking raw internal error text (`WP16-W4-005`)
- These failures are treated as **High/Critical** because they directly affect qualification accuracy, record ownership, compliance handling, and trustworthy HR document review.

## Route-by-route inspection ledger

| W4 ID | Route | Result | Gate outcome | Issue / note |
|---|---|---|---|---|
| W4-001 | `/hr/forgot` | PASS | Redirect verified | — |
| W4-002 | `/hr/field-leadership` | PASS | Route + data load verified | — |
| W4-003 | `/hr/field-leadership-users` | FAIL | Route loads, governed panel fails | `WP16-W4-001` |
| W4-004 | `/hr/employee-accountability` | PASS | Empty-state path verified | — |
| W4-005 | `/hr/time-verification` | PASS | Route + API load verified | — |
| W4-006 | `/hr/time-off` | PASS | Route shell + stats verified | — |
| W4-007 | `/hr/payroll-variance` | PASS | Route shell verified | — |
| W4-008 | `/hr/training-records` | PASS | Table + API load verified | — |
| W4-009 | `/hr/qualifications` | PASS | Registry view verified | — |
| W4-010 | `/hr/driver-qualification` | FAIL | Core compliance API returns `403` to HR | `WP16-W4-002` |
| W4-011 | `/hr/driver-qualification/import` | FAIL | Import audit API returns `403` to HR | `WP16-W4-002` |
| W4-012 | `/hr/daily-reports` | PASS | List + API load verified | — |
| W4-013 | `/hr/daily-reports/:id` | FAIL | Read-only detail still invokes unauthorized lifecycle helper | `WP16-W4-003` |
| W4-014 | `/hr/motive-drivers` | FAIL | Route embeds admin cleanup infrastructure | `WP16-W4-001` |
| W4-015 | `/hr/driver/:driverKey` | LIMITED | Placeholder deep-link only; parent discovery path blocked | dependent on `WP16-W4-001` |
| W4-016 | `/hr/safety-records` | PASS | Route + records panel verified | — |
| W4-017 | `/hr/employees` | FAIL | Core HR roster API returns `403` to HR | `WP16-W4-002` |
| W4-018 | `/hr/employee-requests` | PASS | Queue + API load verified | — |
| W4-019 | `/hr/employees/:id/accountability` | PASS | Live detail path verified | — |
| W4-020 | `/hr/employees/:id/thread` | FAIL | Shared OI summary helper returns `401` | `WP16-W4-004` |
| W4-021 | `/hr/employees/:empId/profile` | FAIL | Employee documents lane returns `500` | `WP16-W4-005` |
| W4-022 | `/hr/historical-records/intake` | FAIL | Vocabulary foundation returns `500` | `WP16-W4-005` |
| W4-023 | `/hr/historical-records/queue` | FAIL | Shared historical queue leaks raw server error | `WP16-W4-005` |
| W4-024 | `/hr/historical-records/batches` | FAIL | Shared batches foundation returns `500` | `WP16-W4-005` |
| W4-025 | `/hr/historical-records/batches/:batchId` | FAIL | Batch detail remains in broken loading/error state | `WP16-W4-005` |
| W4-026 | `/hr/incidents` | PASS | Route + API load verified | — |

## Final defect ledger

| Issue ID | Severity | Operational risk | Scope | Impacted Wave 4 experiences | Root cause | Evidence | Smallest safe repair |
|---|---|---|---|---|---|---|---|
| WP16-W4-001 | High | Operations, Administrative | Shared Component | W4-003, W4-014, dependent W4-015 discovery path | HR routes mount admin-scoped shared components without HR-safe adapters / endpoint shaping. | Playwright 401s on `/api/admin/field-leadership-users` and `/api/admin/integrations/cleanup/*`; code review of `HrFieldLeadershipUsers.jsx` and `HrMotiveDrivers.jsx`. | Replace the admin-mounted panel usage on HR routes with HR-scoped adapters or HR-approved wrappers. |
| WP16-W4-002 | Critical | Data Integrity, Compliance, Operations, Administrative | Shared Foundation | W4-010, W4-011, W4-017 | Employee-lifecycle permission bridge rejects a valid HR owner on HR-owned workflows. | Curl + browser 403s on `/api/hr/employees*` and `/api/hr/driver-qualification*`; code review `employee_lifecycle.py:927-933`. | Correct HR actor normalization / permission mapping for the HR-owned lifecycle and qualification endpoints. |
| WP16-W4-003 | Medium | User Experience, Operations | Single Experience | W4-013 | HR read-only detail still invokes unauthorized lifecycle helper. | Playwright 401 on `/api/daily-reports/{id}/lifecycle` with `Lifecycle controls unavailable for this session.` | Suppress the lifecycle helper for HR, or replace it with an HR-safe read-only lifecycle summary. |
| WP16-W4-004 | Medium | User Experience, Operations | Shared Component | W4-020 | Employee Thread fetches an OI summary feed that the HR session cannot access. | Playwright 401 on `/api/operational-intelligence/summary`; code review `HrEmployeeThread.jsx:223-234`. | Remove or replace the OI summary dependency for HR thread sessions. |
| WP16-W4-005 | Critical | Data Integrity, Compliance, User Experience, Operations | Shared Foundation | W4-021, W4-022, W4-023, W4-024, W4-025 | Shared employee-records / historical-records backend contract is failing server-side, and the UI leaks raw internal errors or indefinite loading. | Curl/browser 500s on `/api/employee-records/vocabulary`, `/api/employee-records/batches*`, `/api/employee-records/employees/{id}/records`. | Repair the shared employee-records backend contract first, then add bounded route-level error states. |

## Issues by severity

- **Critical:** `2`
- **High:** `1`
- **Medium:** `2`
- **Low:** `0`

## Issues by operational risk

- **Operations:** `5`
- **Data Integrity:** `2`
- **Compliance:** `2`
- **User Experience:** `3`
- **Administrative:** `2`
- **Security:** `0 direct unauthorized-access exposures observed`
- **Safety:** `0 direct route-specific safety-control failures opened in this wave`
- **Performance:** `0 standalone performance defects opened`

## Shared foundation findings

1. **Admin-scoped shared components hosted inside HR routes** caused HR workflow degradation on Field Leadership Users and Motive Drivers.
2. **Employee-lifecycle permission bridge** is failing the HR system owner on core HR-owned endpoints.
3. **Employee-records / historical-records foundation** is returning shared `500` failures across document and historical-record workflows.

## Top three risks

1. **HR cannot operate core employee roster and qualification workflows** because valid HR sessions are being denied on HR-owned endpoints.
2. **Sensitive historical/document record workflows are not operationally trustworthy** because the shared employee-records foundation is failing with raw internal-server-error leakage.
3. **Hidden HR routes are depending on admin-only shared components** that are not safe for the HR portal context, creating brittle route-by-route degradation behind otherwise valid HR sessions.

## Overall operational readiness assessment

Wave 4 HR is **not operationally ready for executive lock**. The fail-closed portal guard itself is working, and a meaningful subset of read-only HR review surfaces is healthy. However, multiple core HR workflows remain blocked or degraded across employee lifecycle, qualification management, employee document history, historical records, and hidden/detail route families. The highest-risk failures are concentrated in shared permission and shared record-foundation layers rather than isolated cosmetic defects.

## Executive recommendation

**READY FOR WAVE 4 REPAIR AUTHORIZATION**