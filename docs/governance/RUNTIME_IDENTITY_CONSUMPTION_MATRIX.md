# Runtime Identity Consumption Matrix

Checkpoint D2 authoritative governance record.

Purpose:
- Enforce the One Body Rule.
- Record every runtime truth surface and whether it consumes only the canonical Runtime Identity Authority.
- Eliminate independent environment or database inference.

Approved status vocabulary for all runtime truth surfaces:
- `VERIFIED`
- `MISMATCH`
- `UNVERIFIABLE`
- `DEGRADED`
- `NOT_APPLICABLE`

## Matrix

| Surface Name | File | Canonical Runtime Identity Consumer | Contains Independent Environment Logic | Status Vocabulary Normalized | Independently Verified | Owner | Evidence/Test |
|---|---|---:|---:|---:|---:|---|---|
| API Health | `backend/routes/health_routes.py` | YES | NO | YES | YES | Platform Runtime | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| System Health | `backend/routes/admin_ops.py` | YES | NO | YES | YES | Platform Operations | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| OCC Trust Health | `backend/routes/occ_health_aggregator.py` | YES | NO | YES | YES | Operations Control Center | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| Integration Truth | `backend/routes/integration_truth.py` | YES | NO | YES | YES | Integrations Governance | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| Platform Status | `backend/lib/platform_status.py` | YES | NO | YES | YES | Platform Governance | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| Platform Data Truth | `backend/routes/platform_data_truth.py` | YES | NO | YES | YES | Trust Surface Governance | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| Canonical Status Mapper | `backend/lib/canonical_status.py` | YES | NO | YES | YES | Platform Governance | `backend/tests/test_checkpoint_d2_runtime_truth_normalization.py` |
| Runtime Identity Authority | `backend/lib/runtime_identity.py` | YES | NO | YES | YES | Platform Runtime | `backend/tests/test_runtime_identity_contract.py`, `backend/tests/test_runtime_identity_startup_enforcement.py` |

## D2 decision record

- Runtime identity authority remains `backend/lib/runtime_identity.py`.
- Preview startup fail-closed behavior from D1 remains intact and unchanged.
- No surface in this matrix may parse `APP_ENV`, `DB_NAME`, or `MONGO_URL` to determine runtime identity independently.
- Any future truth surface must be added to this matrix before D3+ work proceeds.