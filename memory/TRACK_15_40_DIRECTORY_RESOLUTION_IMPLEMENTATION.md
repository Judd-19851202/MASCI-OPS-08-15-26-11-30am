# TRACK 15.40 · Directory Resolution Implementation

**Date:** 2026-06-19
**Track:** 15.40 · Objective 1 — Directory Resolution Fix
**Status:** 🟢 COMPLETE & CERTIFIED
**Scope discipline:** Read-only enrichment hardening · no auth changes · no schema changes · no new endpoints.

---

## 1 · Problem (operator-facing)

Roster rows on `/admin/jobs/{project_number}/team` rendered the assignee
as `"Unknown person — Admin review required"` even when the platform
already had the person on file. The recurring reproducer was
Alec Perkins (`user_id=backup-forensics`) on
project `20-07`, where he holds two active assignments
(foreman + safety_rep). The audit drawer suffered the same problem.

This violated **Powerful · Simple · Trusted** because operators had to
hunt by email/ID to identify who was actually assigned.

---

## 2 · Root cause

`_enrich_row_with_directory()` in `backend/routes/project_team_assignments.py`
only consulted the `employees` collection when the assignment row had
a non-null `employee_id`. Alec's rows carry only `user_id`, and his
record lives in `employees` (keyed by `id == user_id`) but NOT in
`user_directory` (no portal login yet). The fallback path was therefore
unreachable for him and for every operator-only employee in the same
position.

---

## 3 · Fix

### 3.1 · Resolver — `_enrich_row_with_directory`

Added three additional `employees`-collection lookups, attempted in
order until a match is found:

| Order | Query | Purpose |
|---|---|---|
| 1 | `employees.find_one({"id": row["user_id"]})` | Canonical case (Alec) |
| 2 | `employees.find_one({"id": row["employee_id"]})` and `employees.find_one({"employee_id": row["employee_id"]})` | Existing payroll-id pathway |
| 3 | `employees.find_one({"email": row["email"].lower()})` | Email-only legacy rows |

The projection pulls `name`, `first_name`, `last_name`, `preferred_name`,
`email`. The resolver call now passes sources in priority order
`(ud_row, emp_row, row)` so the canonical directory wins, the employees
record is the second-best authority, and the row's cached display_name
is only used when both lookups miss.

### 3.2 · Audit endpoint — `GET /api/admin/jobs/{pn}/team/audit`

Added a name-cache + per-row enrichment pass:

```python
for r in rows:
    uid   = r.target_user_id or r.after.user_id or r.before.user_id
    email = r.target_email   or r.after.email   or r.before.email
    r.target_display_name = await _resolve_audit_name(uid, email)
    for snap_key in ("before", "after"):
        snap = r.get(snap_key)
        if isinstance(snap, dict) and snap.get("user_id"):
            snap["display_name"] = await _resolve_audit_name(snap.user_id, snap.email)
```

The cache means N audit rows for the same human → 1 DB call.

### 3.3 · Frontend — `AssignmentHistoryDrawer.jsx`

Updated the `who` fallback chain to prefer the new
`target_display_name` (and snapshot `display_name`s) before falling
back to email / user_id / "(unknown)".

---

## 4 · Files changed

| File | Change |
|---|---|
| `backend/routes/project_team_assignments.py` | `_enrich_row_with_directory` — employees fallback expanded · resolver source order corrected (`ud_row, emp_row, row`). `admin_team_audit` endpoint — enriches `target_display_name` + snapshot `display_name`. |
| `frontend/src/components/team/AssignmentHistoryDrawer.jsx` | `who` fallback chain now prefers `target_display_name` then snapshot `display_name`. |
| `backend/tests/test_track_15_40_directory_resolution.py` **(new)** | 5 pytest cases — employee fallback by user_id, by email, sentinel fallback, Alec fixture, source-order pure-function smoke. |

No schema changes. No new collections. No new endpoints.

---

## 5 · Test surface (data-testid · code)

| Surface | data-testid |
|---|---|
| Foreman row | `row-role-9a9bfc3d-c740-4ef8-9f58-9afad29b3e8c` |
| Safety Rep row | `row-role-453e5110-2b6b-4a5c-aa33-130cce3b33fd` |
| History trigger | `open-history-drawer` |
| History drawer | `assignment-history-drawer` |
| History row by action | `history-row-{assign\|role_change\|update\|remove}` |

---

## 6 · How to verify (manual, ≤ 30 seconds)

```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
ADMIN=$(curl -sS -X POST "$API/api/auth/multi-login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['admin'])")
curl -sS "$API/api/admin/jobs/20-07/team" -H "X-Admin-Token: $ADMIN" \
  | python3 -c "import sys,json;[print(r['assignment_role'],'·',r['display_name']) for r in json.load(sys.stdin)['items'] if r.get('active')]"
```

Expected:
```
co_pm · PM Demo (Preview Fixture)
foreman · Alec Perkins
safety_rep · Alec Perkins
```

---

## 7 · Five Pillars after fix

| Pillar | Score | Note |
|---|---|---|
| Powerful  | 10 | Operators know who is assigned at a glance — no hunting by email. |
| Simple    | 10 | No new flow; the resolver just tries one more collection. |
| Beautiful | 9 | Audit drawer now shows the actual name on every row. |
| Trusted   | 10 | Sentinel only appears when nothing exists anywhere. |
| Proven    | 10 | 5/5 pytest PASS + Iter527 + smoke cert PASS. |

🟢 **Objective 1 complete.**
