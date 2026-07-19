# ARCHIVE POLICY

Date: 2026-07-19  
Checkpoint: C (draft)

## Canonical archive structure

The repository will use one coherent archive structure:

- `docs/archive/deployments/`
- `docs/archive/certifications/`
- `docs/archive/incidents/`
- `docs/archive/testing-evidence/`
- `ops/archive/migrations/`
- `ops/archive/operator-tools/`
- `assets/source/`

## Archive rules

1. Archived material must remain searchable and retain original filenames where practical.
2. Archived scripts must not remain in active execution paths.
3. Runtime/imported code must not read archive-only files.
4. Legal/audit/recovery evidence is preserved, not deleted by default.
5. Generated reports belong in evidence archives, not in canonical product docs.
6. Source artwork belongs under `assets/source/`, not public runtime directories.

## Current intended mapping

- `deploy_reports/**` → `docs/archive/deployments/`
- `test_reports/**` and root process evidence → `docs/archive/testing-evidence/`
- stale tracked backups like `backend/data/*.bak.json` → `docs/archive/incidents/` or `ops/archive/migrations/` after per-file preservation check
- current Checkpoint C implementation path: `docs/archive/incidents/backend-data-backups/`
- `scripts/source/**` and underscore-prefixed public master assets → `assets/source/`

## Safety constraints

- No archive move may break active runtime, CI, or test references.
- No active migration script is archived during Checkpoint C unless evidence proves it is historical and non-active.
- No archive action is final until clean-checkout build/test verification passes.
