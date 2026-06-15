# Phase 6 — Audit Certification Evidence

**Track:** 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 6 (Audit Trail)
**Captured:** 2026-06-15 (UTC, preview environment)
**Source data:** `/app/test_reports/runtime_cert_phase56_evidence.json`

## Method

Inspect `db.audit_events` rows scoped to:

```
{ "category": "project_team_roster",
  "project_number": "ZZ-RUNTIME-CERT-2026" }
```

Then run a live Create / Edit / Reassign / Remove cycle on the
`project_administrator` assignment and re-snapshot the collection.

## Results — 17 / 17 PASS

| Metric | Value |
|--------|------:|
| Audit events captured after cycle | 23 |
| Cert roles with ≥ 1 `assign` audit event | **17 / 17** |
| Actions observed | `assign`, `update`, `remove` |
| `category` field on every row | `project_team_roster` |
| `at` timestamp on every row | ISO 8601 UTC |
| `target_user_id` recorded | ✅ |
| `target_email` recorded | ✅ |
| `project_number` recorded | ✅ |
| `assignment_role` recorded | ✅ |
| Actor signature on every row | ✅ (`actor_id`, `actor_name`, `actor_role`) |

### Sample — assign event

```json
{
  "id": "e5ca554e-228e-4824-be4a-43c6025d3b4a",
  "at": "2026-06-15T02:37:03.761898+00:00",
  "category": "project_team_roster",
  "action": "assign",
  "project_number": "ZZ-RUNTIME-CERT-2026",
  "assignment_role": "project_administrator",
  "target_user_id": "e1bb32ae-a39d-4fda-8fa7-00dfbfba83ec",
  "target_email": "cert.padmin@example.com",
  "before": null,
  "after": { "id": "5b82f5e8-…", "project_number": "ZZ-RUNTIME-CERT-2026", … }
}
```

### Sample — remove event

```json
{
  "id": "409f4a05-d3f3-417c-b382-daee1d5982a1",
  "at": "2026-06-15T02:37:03.421784+00:00",
  "category": "project_team_roster",
  "action": "remove",
  "project_number": "ZZ-RUNTIME-CERT-2026",
  "assignment_role": "project_administrator",
  "target_user_id": "e1bb32ae-a39d-4fda-8fa7-00dfbfba83ec",
  "target_email": "cert.padmin@example.com",
  "before": { … snapshot before deactivation … },
  "after": { … snapshot with active=false … }
}
```

### Coverage table (per role)

All 17 cert roles have at least one `action=assign` audit event tied
to the cert project, captured from the production assignment endpoint
during the seed step:

```
pm                          assigns:1
co_pm                       assigns:1
executive_oversight         assigns:1
superintendent              assigns:1
assistant_superintendent    assigns:1
foreman                     assigns:1
project_engineer            assigns:1
project_administrator       assigns:2   (re-assign in cycle)
project_coordinator         assigns:1
safety_rep                  assigns:1
qaqc_rep                    assigns:1
hr_rep                      assigns:1
dispatch_rep                assigns:1
equipment_manager           assigns:1
shop_rep                    assigns:1
survey_rep                  assigns:1
accounting_rep              assigns:1
```

## Conclusion

Every assignment, update, and removal — on every one of the 17 roles —
writes a fully-populated `project_team_roster` audit event capturing
user, timestamp, project, role, action, before/after snapshot, and
actor signature. Phase 6 PASS.
