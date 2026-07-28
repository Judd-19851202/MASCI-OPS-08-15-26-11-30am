# OPPC Production Confidence Score Certification

## Scope
- Work Package: WP-OPPC-12
- Objective: deliver a transparent 0–100 production confidence score from canonical operational signals.

## Certified Implementation
- Added shared scoring engine: `backend/services/cost_codes/oppc_confidence.py`.
- Added canonical input assembler: `backend/services/cost_codes/oppc_confidence_data.py`.
- Extended:
  - `backend/routes/project_health.py`
  - `backend/routes/ods_intelligence.py`
- Added confidence history persistence on `jobs_master.oppc_confidence_history`.

## Score Components
- Planning
- Production
- Labor
- Variance
- Resource readiness
- Data trust

## Explainability
- Each component returns score, max score, reason, metrics, warnings, freshness, and governance flags.
- `manual_forecast_fields_used` remains `false`.

## Persistence & Audit
- Confidence snapshots are versioned + hashed.
- Trust Spine workflow: `oppc-production-confidence` on snapshot persistence.

## Regression Evidence
- Local regression: `pytest -q /app/backend/tests/test_oppc_confidence.py` → passed
- Local regression: `pytest -q /app/backend/tests/test_wp12_confidence_api.py` → passed
- Independent verification: `/app/test_reports/iteration_67.json` → clean

## Certification Result
**CERTIFIED** — the production confidence score is canonical, explainable, persisted, and surfaced through existing project health and ODS paths.