# OPPC Forecasting & Critical-Path Hardening Certification

## Scope
- Work Package: WP-OPPC-11
- Objective: extend the existing deterministic schedule engine into an explainable forecasting and critical-path hardening layer.

## Certified Implementation
- Reused and extended `backend/services/cost_codes/schedule_engine.py`; no second forecast engine was introduced.
- Reused `foundation.py` and `jobs_master` for forecast snapshot + override persistence; no forecast-only collection was created.
- Added scenario comparison (`additional_crew`, `weekend_work`, `additional_shift`) and critical-path hardening summaries.
- Added audited override governance with separated truth classes:
  - calculated forecast
  - management override
  - approved contractual finish
  - committed finish

## Explainability
- Every task forecast now carries quantity basis, selected production rate, fallback usage, source record references, and a trace id.
- Forecasts remain canonical-data driven; overrides are preserved as audited evidence and never replace calculated truth.

## Persistence & Audit
- Forecast snapshots persist on `jobs_master.oppc_forecast_history`.
- Forecast overrides persist on `jobs_master.oppc_forecast_overrides`.
- Snapshot and override records are versioned and hashed for survivability checks.
- Trust Spine workflow: `oppc-forecasting`.

## Regression Evidence
- Local regression: `pytest -q /app/backend/tests/test_project_schedule_engine.py` → passed
- Local regression: `pytest -q /app/backend/tests/test_project_schedule_api.py` → passed
- Independent verification: `/app/test_reports/iteration_66.json` → clean

## Certification Result
**CERTIFIED** — forecasting, scenario comparison, critical-path hardening, snapshotting, and override governance are implemented on the canonical schedule path without duplicate engines.