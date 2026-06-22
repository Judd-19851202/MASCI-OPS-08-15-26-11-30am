# TRACK 15.60 — HR Linking Workflow (Phase 4)

The HR linking workflow already exists end-to-end. Track 15.60 **does NOT create a new HR system**; it certifies that the existing one is healthy and correctly receives every request submitted by the inline Request-to-Add fix.

## Backend (already in place)

`/app/backend/routes/employee_requests.py`:

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/employee-requests` | any portal token OR public (rate-limited) | Submit a `new_hire` or `termination` request. Writes to `db.employee_requests` with `status=pending`. Fans out an in-app notification to every active HR user via `_notify_hr_queue_pending` with `link_url=/hr/employee-requests?id=<rid>`. |
| `GET /api/hr/employee-requests` | HR-or-admin | Lists pending / approved / rejected requests. Filters: `status`, `kind`, `q`. |
| `GET /api/hr/employee-requests/{rid}` | HR-or-admin | Full request detail incl. `audit_log`. |
| `POST /api/hr/employee-requests/{rid}/approve` | HR-or-admin | For `new_hire`: creates the canonical `db.employees` row (via the same constructor `/api/admin/employees` uses) and flips the request to `status=approved`. For `termination`: applies the target status change. Appends an audit-log entry. |
| `POST /api/hr/employee-requests/{rid}/reject` | HR-or-admin | Sets `status=rejected` with reason. Appends audit-log. |

## Frontend (already in place)

`/app/frontend/src/pages/HrEmployeeRequestsQueue.jsx` — the HR-only operator screen mounted at `/hr/employee-requests`. Features:

- Tabs: Pending · Approved · Rejected · All
- Per-request card with: kind pill, name, submitter context, source workflow (e.g. "employee_combo_inline"), requested_at, requester role/IP
- "Approve" opens a dialog that creates the `db.employees` row using the canonical constructor (no duplicate employee system).
- "Reject" opens a dialog that captures the rejection reason.
- "Open in roster" link after approval routes to the new `db.employees` profile.
- Audit log inline so HR can see every state transition.

The bell click-through path from any portal goes straight to `/hr/employee-requests?id=<rid>` with the new request highlighted (per the iter-HR-READINESS contract validated by `test_hr_readiness_certification.py`).

## Linking Safety-Meeting attendees to the canonical employee

After HR approves a request, the Safety Meeting that triggered the Request-to-Add **does not auto-link** the attendee row's `employee_id` because the meeting was already submitted as free-text. This is intentional and matches the pre-15.60 behaviour:

- The attendee row carries `_pending_hr_review: true` and `request_id: <rid>` in the in-form state during data entry; these flags do not persist to `db.meetings` (they are FE-only display flags).
- The Safety Meeting record stores the attendee with `employee_id=""` (the legacy "not in roster" attendee pattern).
- HR's approval mints a fresh `db.employees` row. The historical meeting record is **not** retroactively updated — preserving the audit trail of what the foreman wrote at the time.
- Future meetings will pick up the new employee via `EmployeeCombo` searching `GET /api/employees`.

This is the correct posture for a Safety Meeting (which is a legal record of what was discussed at a point in time). Retroactive linking would corrupt the audit trail.

## Duplicate-employee prevention

The approve endpoint:
1. Looks up `db.employees` for an existing row matching `name` (case-insensitive) AND, if provided, `employee_id`. If found, returns 409 with `{code: "duplicate", existing_id: ...}`.
2. HR's UI catches this and offers to **link** the request to the existing employee instead of creating a new row. Tested by `test_employee_governance_alpha.py`.

## Audit trail

Every request carries an `audit_log: [...]` array with the timeline:
- `submitted` (with actor role / label / IP / timestamp)
- `approved` or `rejected` (HR actor + reason if reject)
- `linked_to_existing` (when HR chose to dedupe)

Auditors can read the full HR queue including resolved requests via the `Approved` / `Rejected` tabs.

## Certification

| Check | Result |
|---|---|
| `POST /api/employee-requests` accepts the inline submission | ✅ verified by Phase 3 stress test scenario C |
| Backend creates the `db.employee_requests` row | ✅ verified during preview test runs |
| HR notification bell fires with correct `link_url` | ✅ covered by `test_hr_readiness_certification.py` |
| HR queue page renders at `/hr/employee-requests` | ✅ existing route (`HrEmployeeRequestsQueue.jsx`, 524 LOC) |
| Approve endpoint creates `db.employees` row | ✅ covered by `test_employee_governance_alpha.py` test_approve_creates_employee |
| Duplicate detection on approve | ✅ same test file, dupe case |
| Audit log preserved | ✅ same test file |
| Reject path | ✅ same test file, test_reject_path |

**No code changes required in Phase 4.** The HR linking workflow is healthy as-is and correctly receives the now-resilient inline Request-to-Add submissions.
