# DANGEROUS SCRIPT REGISTER

Date: 2026-07-19  
Checkpoint: B

## Classification summary

| Path | Classification | Production target possible | Dry-run/default read-only | Explicit production opt-in | Notes |
|---|---|---:|---:|---:|---|
| `backend/scripts/seed_project_memberships.py` | UNSAFE_UNGUARDED | Yes | No | No | Direct Mongo writes, no preview/prod confirmation, no audit row. |
| `backend/scripts/seed_equipment_make_model.py` | UNSAFE_UNGUARDED | Yes | No | No | Writes source JSON + MongoDB, no dry-run or production confirmation. |
| `backend/scripts/migrate_local_project_docs_to_r2.py` | ACTIVE_MIGRATION_PENDING | Yes | Yes | No | Dry-run default and audit present, but production mutation still lacks explicit typed production confirmation. |
| `backend/scripts/purge_synthetic_dailies_24_9.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Partial | Dry-run default + audit exists; `--apply` lacks typed production confirmation phrase / backup ack. |
| `backend/scripts/repair_dr_duplicate_doc_ids.py` | ACTIVE_MIGRATION_PENDING | Yes | Yes | Yes | Preview-safe default, allow-production flag, audit rows; still no backup prerequisite enforcement. |
| `backend/scripts/seed_pm_demo_fixture.py` | TEST_ONLY | No | N/A | N/A | Explicit preview-only guard via `APP_ENV != production` and `_preview` DB name. |
| `backend/tools/restore_drill.py` | RECOVERY_ONLY | No | No | N/A | Hard-refuses unless preview DB + preview env. Safe recovery-only script. |
| `scripts/restore_drill.py` | RECOVERY_ONLY | Yes | Yes | Partial | Side-DB drill requires target DB arg and has safety rails, but uses live credentials and lacks audit trail. |
| `backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py` | ACTIVE_OPERATOR_TOOL | Yes | Yes | Yes | Best-in-class among reviewed scripts: dry-run default + prod confirm + audit. |
| `backend/scripts/track_15_65_seed_email_routes.py` | UNSAFE_UNGUARDED | Yes | Yes | No | Apply mode exists without explicit production opt-in/backup ack. |

## P1 findings requiring action/ownership

1. `backend/scripts/seed_project_memberships.py` — P1  
   Root cause: mutation script with no dry-run, no env guard, no confirmation, no audit.

2. `backend/scripts/seed_equipment_make_model.py` — P1  
   Root cause: dual-write script (repo data + MongoDB) with no explicit safety contract.

3. `backend/scripts/migrate_local_project_docs_to_r2.py` — P1  
   Root cause: migration safety is good but still lacks an explicit production confirmation phrase and backup acknowledgment.

4. `backend/scripts/track_15_65_seed_email_routes.py` — P1  
   Root cause: apply path exists but lacks production-only typed confirmation discipline.

5. `backend/scripts/basecamp_import.py` / `basecamp_import_big.py` — P1  
   Root cause: active import-style mutation tooling detected by write-surface scan; requires full classification before Checkpoint B closes.

6. `backend/scripts/migrate_dr_v2_collections_to_daily_report.py` — P1  
   Root cause: migration tooling with write surfaces detected; requires guard classification.

7. `backend/scripts/track_15_28c_canonicalization_migration.py` — P1  
   Root cause: write-enabled migration detected; requires safety-classification closure.

## Shared doctrine for future repair

- Prefer `lib/operator_safety.py` style shared confirmation/runtime guards.
- Require:
  - typed confirmation token
  - explicit backup acknowledgment
  - target DB/environment assertion
  - dry-run by default where feasible
  - audit row or emitted immutable report

## Execution note

No dangerous script was executed during Checkpoint B.
