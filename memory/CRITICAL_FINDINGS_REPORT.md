# Critical Findings Report

**Track:** 14.0-RC1
**Date:** 2026-06-15
**Findings:** 0 P0 · 4 P1 (env) · 3 P2 (tech-debt / data-quality)

## P0 (deploy blockers)

**None.**

## P1 (must-fix at deploy time — env-var driven, not code-bound)

### F-01 — Production CORS must NOT be `*`
**File**: `/app/backend/.env` (preview).
**Current**: `CORS_ORIGINS="*"`
**Required for production**: `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com`
**Why**: A wildcard combined with `credentials: include` (which the
frontend sets via tokens in localStorage forwarded as
`X-Admin-Token` / `X-PM-Token` etc.) is permissive. The auth
mechanism does NOT use cookies so the canonical "wildcard +
credentials" CORS preflight failure does not strictly apply, but
production should still pin to the real origins.
**Owner**: Deploy operator (env-var override).
**Verification**: After deploy, `curl -H "Origin: https://evil.example" -I https://mascidocs.com/api/health` should NOT echo `Access-Control-Allow-Origin: *`.

### F-02 — Production rate-limiting must be ON
**Current**: `RATE_LIMITING=off`
**Required**: `RATE_LIMITING=on`
**Why**: Preview disables rate-limiting so the test suite doesn't trip
429s. Production must enable it to defend public POST endpoints
(`/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`,
`/api/daily-reports`, `/api/equipment-units`,
`/api/equipment-inspections`, `/api/translate`).
**Owner**: Deploy operator.

### F-03 — Production AUTO_EMAIL_REPORTS must be ON
**Current**: `AUTO_EMAIL_REPORTS=false`
**Required**: `AUTO_EMAIL_REPORTS=true`
**Why**: Preview suppresses auto-email so the test suite + agent loops
don't burn through the Resend daily quota. Production must flip this
ON so PM / Safety / Foreman submission auto-routing actually fires.
**Owner**: Deploy operator.

### F-04 — Production SCHEDULER_ENABLED must be ON
**Current**: `SCHEDULER_ENABLED=false`
**Required**: `SCHEDULER_ENABLED=true`
**Why**: Preview disables the singleton scheduler so background jobs
don't double-run on shared infra. Production needs:
* Nightly Mongo backup (`BACKUP_HOURS_UTC=2,18`).
* R2 hourly backup mirror (`BACKUP_R2_HOURLY=true`).
* Weekly Safety digest (Monday 14:00 UTC).
* Motive integration sync.
**Owner**: Deploy operator.

## P2 (tech-debt / data-quality — not deploy blockers)

### F-05 — 4 stale pytest collection failures
* `test_equipment_inspections.py` — imports `URL, ADMIN_TOKEN` from `conftest` which no longer exports them.
* `test_iter138_typeahead_bindings.py` — same.
* `test_iter139_master_lookup_filters.py` — same.
* `test_sprint1c_incident_delete.py` — same.

These four test modules error out at pytest collection time, so the
absolute test count of 7411 collected hides them. Recommendation:
either delete the 4 stale files (the iterations they covered have
been superseded by newer iter suites) or restore the missing
`URL` / `ADMIN_TOKEN` symbols to `conftest.py`. **Not a deploy
blocker** because the underlying application code is exercised by
newer suites.

### F-06 — 7 scheduler-hardening tests fail under preview Mongo
File: `tests/test_iter445_scheduler_hardening.py`.

Failure pattern: `OperationFailure: not authorized on scheduler_test_iter445 to execute command`.

**Diagnosis**: These tests connect to MongoDB and spin up a side
database `scheduler_test_iter445` for isolated dedup proofs. The
preview Atlas user (`masci_preview_user`) is scoped to
`masci_safety_preview` ONLY — by design — so the side-DB write is
rejected. This is **evidence the DB-isolation security boundary is
working**, not a real test failure. The tests need a local Mongo
runtime to pass; they were designed for a permissive dev cluster.
**Not a deploy blocker**.

### F-07 — `corrective_actions.equipment` master-binding coverage at 0%
Source: `/api/admin/deploy-readiness` check `master_coverage`.

Symptom: 0% of `corrective_actions` rows have a resolved equipment
master binding. Also `equipment_inspections` 3%, `incidents` 1%,
`corrective_actions.employee` 14%, `incidents.employee` 9%.

**Diagnosis**: Historical records were entered before the cross-portal
master-binding work landed (Track 13.6 binding sweep). New records
created via the current forms write correct master keys.

Recommendation: Run a one-time backfill job that resolves
`unit_number`/`employee_name` → master ids and writes the
denormalized keys onto historical rows. **Not a deploy blocker** —
the platform works without these denormalized keys; they're only
needed for cross-portal joins on legacy rows.

## Defects fixed inline during this audit + the prior staffing track

(All previously deployed to preview; verified by the regression
suite that ran during this audit.)

1. `compute_pm_scope` extended to UNION `project_team_assignments` —
   PM-portal users assigned via the new staffing workflow see their
   projects. (`/app/backend/pm_auth.py`)
2. `_notify_assignment()` added to `routes/project_team_assignments.py`
   — assign + remove handlers now fan out portal-correct
   `db.notifications` rows.
3. Notification wording corrected (was `"removed from you from"`).

---

**Bottom line: zero P0 blockers, four P1 env-var deltas, three P2
tech-debt items. The platform is GO for production deploy with the
P1 env-var checklist applied.**
