# Track 19.03 · Daily Report Roster Failure Reproduction

## Reproduction in preview (synthetic employee)

```
# Step 1 — Insert a synthetic HR row that mirrors the legacy data drift
db.employees.insert_one({
  "id": "<uuid>",
  "name": "ZZ_TEST_19_03_<uuid>",
  "lifecycle_status": "Active",     # HR says Active
  "is_active": False,               # legacy boolean is False
  "employee_id": "TEST-<id>",
  "role": "Test Role",
  "deleted_at": None,
})

# Step 2 — Read canonical PRE-fix endpoint (before this track)
GET /api/employees     # filter was  is_active != False
→ employee MISSING from list  ← the bug
```

## After Track 19.03 fix

```
GET /api/employees
→ canonical filter:
    lifecycle_status in {Active, Pending Hire, Seasonal, Leave of Absence}
    OR (legacy: no lifecycle_status AND is_active != False)
→ employee APPEARS  ✓

GET /api/hr/employee-roster
→ same canonical filter, plus contract metadata
→ employee APPEARS  ✓
```

## Reverse case (terminated employee leak)

```
db.employees.update_one({"id": "<uuid>"},
  {"$set": {"lifecycle_status": "Terminated"}})    # is_active stays True

PRE-fix:
GET /api/employees  → employee STILL VISIBLE  ← leak

POST-fix:
GET /api/employees  → employee HIDDEN  ✓
GET /api/hr/employee-roster?include_inactive=true
                     → employee VISIBLE (operator-gated)  ✓
```

## Verified by pytest

`tests/test_track_19_03_hr_roster_source_of_truth.py` runs both
scenarios live against the preview API and asserts the post-fix
behaviour. The test fixture creates a synthetic test employee with
the exact data shape that triggered the production report, then
verifies the canonical roster shows them. Cleanup deletes the test
row.

## Real-world implication

After this fix is deployed, any production employee whose
`lifecycle_status` says Active but whose legacy `is_active` was False
(or vice-versa) is correctly reconciled. **HR Save is now gospel** —
the canonical endpoint trusts `lifecycle_status` first, with legacy
fallback only when `lifecycle_status` is genuinely missing.

## Data-quality follow-up

Track 19.03 also recommends an idempotent backfill script (operator
to run post-deployment) that walks production `db.employees` and
ensures `is_active = (lifecycle_status in _ACTIVE_STATUSES)` for any
row where `lifecycle_status` is set. The fix above is correct without
that backfill; the backfill is purely hygienic.
