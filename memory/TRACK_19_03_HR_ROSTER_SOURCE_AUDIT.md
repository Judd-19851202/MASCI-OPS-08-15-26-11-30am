# Track 19.03 · HR Roster Source Audit

## Verdict

**Root cause identified.** Two independent lifecycle indicators were
allowed to drift:

* `is_active` (boolean) — legacy lifecycle flag
* `lifecycle_status` (string · `Active` / `Pending Hire` / `Seasonal`
  / `Leave of Absence` / `Inactive` / `Terminated` / `Resigned` /
  `Retired`) — modern HR lifecycle field

The canonical public roster endpoint `/api/employees` filtered ONLY on
`is_active != False`. The modern HR write path (`employee_lifecycle.py`)
writes both fields synchronously, but historical / legacy / re-imported
rows could carry one without the other.

**Impact:** if HR sets `lifecycle_status="Active"` but `is_active=False`
remained from a legacy data path, the employee was hidden from every
field-form picker even though HR considered them active. Conversely,
if `lifecycle_status="Terminated"` but `is_active=True` (legacy row
not migrated), the terminated employee leaked into pickers.

## Sources of truth in scope

| Collection | Role | Verified single SoT? |
| --- | --- | :-: |
| `db.employees` | HR employee identity (the Golden Record) | ✓ |
| `db.field_leadership_roster` | derived (foreman / superintendent layer) | ✓ derived from `db.employees` |
| `db.transport_persons` | Transportation operational overlay (links via `employee_id`) | ✓ Track 19.00 contract |
| `db.training_assignments`, `db.certifications`, etc. | reference `employee_id` only — do not duplicate name/status | ✓ |

No competing employee databases were found.

## Endpoints inventoried (employee list)

| Endpoint | Source | Status |
| --- | --- | --- |
| `GET /api/employees` (public picker contract) | `db.employees` | **FIXED in 19.03** — now uses canonical lifecycle clause |
| `GET /api/hr/employee-roster` (NEW) | `db.employees` | **ADDED in 19.03** — canonical HR roster contract |
| `GET /api/hr/employees` (HR portal full record) | `db.employees` | already used canonical lifecycle clause (employee_lifecycle.py:925-927) |
| `GET /api/admin/employees/status` | `db.employees` count | counts only |
| `GET /api/admin/employees/archive` | soft-deleted rows | archive viewer |
| `GET /api/pm/directory/users` | `db.employees` | PM-only directory |
| `GET /api/employees/competent-persons` | filtered subset | Trench Safety competent-person list |

## Hidden filters audit

Every employee query is now documented:
* `ACTIVE_FILTER`: excludes soft-deleted (`deleted_at != null`).
* `canonical_active_clause`: `lifecycle_status in _ACTIVE_STATUSES`
  OR (legacy: no `lifecycle_status` AND `is_active != False`).
* No project, crew, supervisor, certification, or role filters applied
  by default. Operator must opt-in via query params.

## Live data drift (preview DB)

| Property | Count |
| --- | ---: |
| Total employees | 396 |
| `lifecycle_status=Active` | 149 |
| `lifecycle_status=Inactive` | 3 |
| `lifecycle_status=Terminated` | 9 |
| `lifecycle_status=None` (legacy) | 235 |
| `is_active=True` | 383 |
| `is_active=False` | 12 |
| Drift cases on preview (Active but is_active=False) | 0 (after fix) |
| Drift cases on preview (Terminated but is_active=True) | 0 (after fix) |

Production drift requires the same audit script post-deployment. The
fix is **defensive** — even if production has drift, the canonical
endpoint will surface lifecycle_status truth, not the legacy
is_active boolean.
