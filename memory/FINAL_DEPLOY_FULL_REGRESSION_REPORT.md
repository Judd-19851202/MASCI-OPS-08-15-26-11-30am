# FINAL_DEPLOY_FULL_REGRESSION_REPORT

## Primary authoritative suite

- Command: `pytest -q -rs /app/backend/tests/test_c2_deployment_governance.py /app/backend/tests/test_iter58_backup_health_final_verification.py /app/backend/tests/test_wp18c1_hierarchy_foundation.py /app/backend/tests/test_wp18c5_schedule_actuals_api.py /app/backend/tests/test_restore_certification_s1_1.py /app/backend/tests/test_s1_4_notification_delivery_certification.py /app/backend/tests/test_iter133_predeploy.py /app/backend/tests/test_deferred_containment.py`
- Result: `125 passed, 4 skipped, 1 warning, 0 failed, 0 errors`
- Skip ledger: reconciled in `FINAL_DEPLOY_ACTIVE_TEST_RECONCILIATION.csv`

## Independent verification

- `/app/test_reports/iteration_127.json`
  - Deferred containment verified across backend and frontend surfaces
  - Runtime identity parity verified
- `/app/test_reports/iteration_126.json`
  - Earlier release-gate failures for auth/backup classes verified as fixed

## Additional targeted checks

- `pytest -q /app/backend/tests/test_checkpoint_d3_database_authority.py`
  - `7 passed`
- `python - <<<'import server'` from `/app/backend`
  - passed after requirements refresh

## Smoke / runtime checks

- Preview smoke loaded successfully
- `/api/health/full` healthy
- `/api/admin/recovery/snapshot` returned successfully with current scheduler heartbeat and authoritative archive lineage