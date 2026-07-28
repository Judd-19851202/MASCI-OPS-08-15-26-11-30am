# OPPC Survivability Validation

## Persistent Objects Introduced / Extended
- `jobs_master.oppc_forecast_history`
- `jobs_master.oppc_forecast_overrides`
- `jobs_master.oppc_confidence_history`
- `oppc_monday_briefings`

## Validation Evidence
- `pytest -q /app/backend/tests/test_oppc_survivability.py` → pass
- `pytest -q /app/backend/tests/test_oppc_execution.py` → pass

## Survivability Controls
- **Backup inclusion**
  - forecast + confidence histories live on `jobs_master`
  - briefing documents live in `oppc_monday_briefings`
- **Restore compatibility**
  - records are JSON-safe and versioned (`version: 1`)
- **Audit integrity**
  - forecast snapshots, overrides, confidence snapshots, and briefings are hashed
  - briefing approvals/freeze actions retain append-only history
- **Version compatibility**
  - all new persisted records carry explicit version metadata
- **Retry / idempotency**
  - briefing documents are upserted by scope + week
  - frozen briefings block unsafe regeneration/re-approval
- **Corruption detection**
  - content hashes allow post-restore integrity checks

## Decision
**VALIDATED** — new persisted WP-11/12/13 records have explicit versioning, integrity metadata, restore-safe structure, and tested lifecycle controls.