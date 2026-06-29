# HR Employee Roster Contract (v19.03)

> HR is the single source of truth for employee identity across the
> entire MASCI Operations Platform. HR Save is the authoritative
> commit event. The instant HR clicks Save, every operational
> employee picker reflects the change on its next query.

## 1 · Source

* **Collection:** `db.employees` (the Golden Record).
* **Soft-delete:** rows with `deleted_at != null` are hidden everywhere.

## 2 · Active sets

```
_ACTIVE_STATUSES   = { Active, Pending Hire, Seasonal, Leave of Absence }
_OFFBOARDING_SET   = { Terminated, Resigned, Retired, Inactive }
```

## 3 · Visibility rule (default for ALL operational pickers)

An employee appears on a new-form picker if and only if:

```python
(deleted_at in (None, ""))
AND (
    lifecycle_status in _ACTIVE_STATUSES
    OR (lifecycle_status missing/None AND is_active is not False)
)
```

Legacy rows without `lifecycle_status` fall back to the boolean.
Modern rows with `lifecycle_status` set use that — the boolean is
ignored.

## 4 · Inactive lookup (operator-gated)

Investigations, corrections, audits, and historical review may request
inactive employees by setting:

```
GET /api/hr/employee-roster?include_inactive=true
```

The roster contract clearly flags each row with `active: <bool>`.

## 5 · Safe projection (what pickers receive)

Pickers get only these fields:

| Field | Purpose |
| --- | --- |
| `id` | Stable internal identifier |
| `name` | Display name |
| `preferred_name` | Optional preferred name (rendered when present) |
| `employee_id` | HR-issued employee number |
| `role`, `trade` | Operator filter |
| `crew`, `department` | Operator filter |
| `lifecycle_status` | Allows UI to render "(Inactive)" chip if surfaced |
| `is_active` | Legacy compatibility |
| `active` | Derived boolean (matches the contract above) |
| `supervisor_name`, `supervisor_id` | Foreman / supervisor lookups |
| `updated_at` | Freshness indicator |

## 6 · Private fields (NEVER returned to operational pickers)

`email`, `phone`, `ssn`, `dob`, `medical_card`, `cdl_number`,
`cdl_expiration`, `password*`, `address`, full status_history,
private HR notes.

## 7 · Canonical endpoints

| Endpoint | Audience | Caching |
| --- | --- | --- |
| `GET /api/hr/employee-roster` | every picker, anonymous-ok | **none — live read** |
| `GET /api/employees` | legacy public picker (now reads same contract) | none |
| `GET /api/hr/employees` | HR portal (full record, gated) | none |

## 8 · Write events

* Only HR portal endpoints (`/api/hr/employees`, …) write to
  `db.employees`.
* HR write paths set BOTH `lifecycle_status` AND `is_active` (via
  `_is_active_for_status`) — kept synchronously consistent.
* HR Save → next read of any roster endpoint sees the change.

## 9 · Historical snapshot

When an operational form (Daily Report, Safety Meeting, Pre-Op, JHP,
QA/QC, Incident, etc.) is **submitted**, the form payload must
snapshot the selected employee's `name`, `preferred_name`,
`employee_id`, and `role/trade` at that moment.

Selection always uses current HR truth. Submitted records preserve
the historical snapshot forever — they never re-derive from
`db.employees` on read.

## 10 · Search / sort / pagination

* `q` — case-insensitive regex over `name`, `preferred_name`,
  `employee_id`, `role`.
* Sort: `name` ascending.
* Pagination: `limit` (default 5000, max 5000).
* No additional filtering by project / crew / supervisor at the
  contract level — pickers do that client-side.

## 11 · Versioning

Contract version `19.03`. Future contract changes must bump this
version in `/api/hr/employee-roster` response and update this
document.
