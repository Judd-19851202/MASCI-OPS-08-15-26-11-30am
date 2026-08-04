# Final Release Database and Migration Audit

## Scope
This audit covers all code that could write to production during app startup, runtime requests, scheduled work, or manually-invoked scripts.

## Production-impacting database surfaces in delta
- `backend/server.py`
- `backend/routes/daily_reports.py`
- `backend/routes/admin_persistence_health.py`
- `backend/routes/enterprise_governance.py`
- `backend/routes/qaqc.py`
- `backend/services/cost_codes/foundation.py`
- `backend/services/enterprise_hierarchy_foundation.py`
- `backend/services/project_budget_authority.py`
- `backend/services/project_controls_authority.py`
- `backend/services/project_operational_intelligence.py`
- `backend/services/project_schedule_actuals_spine.py`
- `backend/services/project_schedule_authority.py`
- `backend/scripts/field_trial_runner.py`
- `backend/scripts/iter348_fl_bulk_create.py`

## Startup / auto-executed concerns
### server.py startup hooks
- Adds/ensures Mongo indexes at boot.
- This is **additive** but production-impacting.
- Risk: index build time/write amplification on large collections.
- Interruption behavior: index builds resume/retry per Mongo/driver behavior; not ideal to first discover on live deploy.

### Daily Report runtime writes
- `daily_reports.py` persists Daily Reports and now also persists downstream notification failure state.
- This is **additive** and **idempotent at the report level only if duplicate-submit guards hold**.
- User-visible protection exists, but integrated bundle still requires live deploy proof before production promotion.

### Background schedulers / workers
- Production runtime already shows multiple long-running schedulers.
- Mixed-version overlap during deploy is a real risk if web/API, scheduler, and worker code do not roll atomically.

## Manual / script-based operations
### `backend/scripts/field_trial_runner.py`
- Operational script; not expected to auto-run on deploy.
- Treat as **manual only**.

### `backend/scripts/iter348_fl_bulk_create.py`
- Bulk-create script; not expected to auto-run on deploy.
- Treat as **manual only**.
- Must not be executed in production without explicit record-count plan and rollback strategy.

## Data-safety conclusions
- No destructive schema migration was directly identified in the current delta.
- The biggest deployment data risks are:
  1. **startup index creation on large live collections**
  2. **mixed-version worker/scheduler overlap**
  3. **operator-facing workflow changes across 339 frontend files without exact-bundle runtime parity in preview**
- Explicit preview/test fixture risk:
  - No evidence was found that `ZZ-RUNTIME-CERT-2026`-style preview fixtures would be auto-seeded into production by startup.
  - Manual scripts still require explicit operator restraint.

## Audit decision
- **No destructive migration blocker found.**
- **Integrated live deployment remains blocked by certification/parity, not by a proven destructive migration.**
