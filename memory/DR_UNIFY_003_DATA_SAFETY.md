# DR-UNIFY-003 · Data Safety

## Non-destructive by design

DR-UNIFY-003 **does not delete any Mongo document, collection, or
index**. The migration script explicitly avoids destructive drop
operations; live migration itself is deliberately deferred to
DR-UNIFY-004 (deployment certification).

## Baseline counts (preview DB · captured 2026-02)

| Legacy collection            | Docs |
| ---------------------------- | :--: |
| `dr_v2_drafts`               |  18  |
| `dr_v2_ai_cache`             |  27  |
| `dr_v2_ai_audit_entries`     |   3  |
| `dr_v2_ai_approvals`         |   7  |
| `dr_v2_photo_intelligence`   |   1  |
| `dr_v2_bilingual_audit`      |   0  |
| **Total**                    |  **56** |

Canonical `daily_report_*` collections all empty pre-migration.

Dry-run reports 0 collisions on `_id`.

## Guarantees

### 1. Source docs never modified
The migration script iterates over source docs and calls
`insert_one` on the target. Source docs are never touched. Rollback
= delete inserted docs by `_id` from the target; source is
byte-identical throughout.

### 2. `_id` preserved
`dict(doc)` is used to spread the source doc, preserving `_id` and
every other field verbatim.

### 3. Idempotent on `_id` collision
Duplicate-key inserts are caught and counted as
`skipped_existing_or_error`. Re-running produces zero incremental
writes when the migration is already complete.

### 4. Refuses production without opt-in
The script exits with code 2 if `APP_ENV=production` and no
`--allow-prod` flag is supplied.

### 5. Preserves cross-references
Any collection that referenced a `dr_v2_*` `_id` (e.g. `operational_facts`
via `source_id`) continues to resolve because the `_id` in the
canonical collection matches the legacy value.

### 6. No cascading deletes
The script has no `delete_many`, `drop`, or `rename` calls. Text
grep of `scripts/migrate_dr_v2_collections_to_daily_report.py`:

```
$ grep -E "delete|drop|rename" scripts/migrate_dr_v2_collections_to_daily_report.py
# No hits inside execution paths — the word "delete" appears only
# inside comments and the --rollback informational plan.
```

## Backup procedure (documented for DR-UNIFY-004)

Before running `--live --allow-prod` against the production Mongo:

1. Take a Mongo Atlas snapshot of the `masci_safety` database
   (Atlas UI → Snapshots → "Take on-demand snapshot").
2. Verify snapshot ID is recorded in the deployment log.
3. Confirm APP_ENV, DB_NAME, and MONGO_URL match the intended target
   before executing.
4. Execute `--dry-run --allow-prod` first; inspect the JSON output.
5. Execute `--live --allow-prod`.
6. Execute `--verify --allow-prod` immediately after. Non-zero exit
   is a fail; roll back per the rollback plan below.
7. Monitor `operational_facts` and `daily_reports` reads for 30 days.

## Rollback

Because sources are untouched:

- **Instant rollback:** revert application reads to legacy names
  (`resolve_read_collection_name` handles this transparently by
  returning the legacy name when the canonical is empty). No data
  action needed.
- **Full rollback:** delete matching `_id`s from the canonical
  collections. See `--rollback` script output for the one-line plan.
- **Emergency:** restore the Mongo snapshot taken in step 1.

## What could go wrong (and how we mitigate)

| Risk                                              | Mitigation                                                                   |
| ------------------------------------------------- | ---------------------------------------------------------------------------- |
| `_id` collision between legacy and canonical      | Script counts collisions in dry-run; live mode skips them.                    |
| Application still reads legacy after cutover      | Read-compat helper handles it transparently until callsites are migrated.    |
| Production traffic during migration               | Copy is idempotent; source is not locked. New writes go to canonical.        |
| Rollback needed mid-migration                     | Source collection is intact; delete matching `_id`s from canonical to reverse. |
| Someone runs `--live` against prod by accident    | `APP_ENV=production` refusal + explicit `--allow-prod` flag required.        |
