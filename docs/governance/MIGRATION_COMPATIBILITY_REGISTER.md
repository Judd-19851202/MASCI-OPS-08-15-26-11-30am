# MIGRATION COMPATIBILITY REGISTER

Date: 2026-07-19  
Checkpoint: D6

Production deployment is blocked whenever migration state is unknown or rollback compatibility is unproven. No migrations executed in D5/D6.

| Migration ID | File | Change summary | Backward compatibility | Forward compatibility | Required order | Dry-run | Idempotency | Rollback | Backup prerequisite | Owner | Gate status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MIG-001 | `backend/photo_migration.py` | photo/document data shape migration helper | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |
| MIG-002 | `backend/routes/signature_migration.py` | signature migration route surface | UNKNOWN | UNKNOWN | manual only | unproven | unproven | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |
| MIG-003 | `backend/scripts/track_15_28c_canonicalization_migration.py` | daily-report canonicalization migration | PARTIAL | PARTIAL | explicit operator order | script-level only | unknown | manual only | required | jaymn.judd@mascigc.com | BLOCK_PRODUCTION_UNTIL_OWNER_REVIEW |

## PDC-01B exact-release dispositions

Exact PRE_SAVE_CANDIDATE diff reviewed for this release:
- `backend/server.py`
- `backend/static/runtime-data/DEPLOYMENT_HISTORY.json`
- `backend/tests/test_checkpoint_d5_d6_release_gate.py`
- `backend/tests/test_track_27_09b_integrity_scheduler_closeout.py`
- `backend/tests/test_track_28_09d_backup_health_aggregator.py`
- `docs/governance/BACKUP_RECOVERY_RELEASE_CERTIFICATE.md`
- `docs/governance/MIGRATION_COMPATIBILITY_REGISTER.md`
- `docs/governance/PDC_01B_RELEASE_EVIDENCE.md`
- `docs/governance/release_gate_manifest.json`
- `frontend/yarn.lock`
- `frontend/src/buildVersion.generated.js`
- `memory/PRD.md`
- `scripts/release_gate.py`

Evidence-backed dispositions for this exact release only:

| Migration ID | Exact-release disposition | Basis |
|---|---|---|
| MIG-001 | NOT_APPLICABLE_TO_THIS_RELEASE | No migration file changed, no persisted schema/index/collection/auth shape change introduced by this candidate. |
| MIG-002 | NOT_APPLICABLE_TO_THIS_RELEASE | No signature migration code or runtime read/write contract changed in this candidate. |
| MIG-003 | NOT_APPLICABLE_TO_THIS_RELEASE | No notification canonicalization code, collection name, enum, or serialization contract changed in this candidate. |

Release-level continuity conclusion for PDC-01B:
- Introduces a new migration: no
- Changes a persisted schema: no
- Changes required indexes: no
- Changes auth/user schemas: no
- Changes collection names: no
- Changes serialization or enum contracts: no
- Changes backward/forward compatibility: no
- Makes rollback candidate incompatible: no

Therefore, for this exact release candidate, migration/platform continuity is:
- `COMPATIBLE_NO_MIGRATION_REQUIRED`

This release-specific disposition does **not** erase the standing production owner-review requirements for the migration utilities themselves; it only states they are not exercised or modified by this exact candidate diff.
