# DR-UNIFY-003 · Collection Migration Plan

## Scope

Rename six Mongo collections from the legacy `dr_v2_*` prefix to the
canonical `daily_report_*` prefix. Additive copy first; destructive
drop is out of scope for this track (see DR-UNIFY-004).

## Mapping

| Canonical (target)                    | Legacy (source)                | Preview docs today |
| ------------------------------------- | ------------------------------ | :----------------: |
| `daily_report_drafts`                 | `dr_v2_drafts`                 |         18         |
| `daily_report_ai_cache`               | `dr_v2_ai_cache`               |         27         |
| `daily_report_ai_audit_entries`       | `dr_v2_ai_audit_entries`       |          3         |
| `daily_report_ai_approvals`           | `dr_v2_ai_approvals`           |          7         |
| `daily_report_photo_intelligence`     | `dr_v2_photo_intelligence`     |          1         |
| `daily_report_bilingual_audit`        | `dr_v2_bilingual_audit`        |          0         |

Source of truth for the mapping: `lib/daily_report_collections.py`.
The migration script imports the same dict, so no drift is possible.

## Script

Path: `backend/scripts/migrate_dr_v2_collections_to_daily_report.py`

### Modes

| Flag             | Effect                                                                                    |
| ---------------- | ----------------------------------------------------------------------------------------- |
| `--dry-run`      | (default) counts + collision sampling; **no writes**                                     |
| `--live`         | copies legacy → canonical; skips `_id` collisions; **never deletes source**              |
| `--verify`       | asserts every legacy `_id` is present in canonical; exits non-zero on drift              |
| `--rollback`     | prints one-line rollback plan; performs no writes                                        |
| `--allow-prod`   | required in combination with any other flag when `APP_ENV=production`                    |

### Refuse-prod safety

The script exits with code 2 if `APP_ENV=production` and `--allow-prod`
is not passed. This forces an intentional operator decision before any
production write.

### Idempotency

- The script iterates every source doc and calls `insert_one` on the
  target. Duplicate-key errors (matching `_id`) are counted as
  `skipped_existing_or_error` and never fail the run.
- Re-running `--live` after a completed migration produces:
  `copied=0, skipped=<source_count>, target_count_after=<source_count>`.
- Re-running `--verify` after a completed migration returns `ok=true`.

### Preserved fields

- `_id` — retained verbatim so cross-references from other collections
  keep resolving.
- Every document field is copied via `dict(doc)`.
- Indexes are NOT copied by this script — deploying code will re-create
  the required indexes on first access (both `dr_ai/cache.py` and
  `photo_intelligence/store.py` create their own indexes lazily).

### Rollback

Because the source collections are never dropped, rollback is trivial
— restore the read paths to their legacy collection names (or simply
drop the canonical collections if they are undesired). The
`--rollback` mode prints:

```
for each pair in COLLECTION_ALIASES:
    db[canonical].delete_many({'_id': {'$in': [d['_id'] for d in db[legacy].find({}, {'_id':1})]}})
```

## Execution plan

### Phase A — dry-run (this track, DR-UNIFY-003)

- ✅ Done. Preview DB reports 56 source docs, 0 collisions,
  56 would-copy.

### Phase B — preview live (DR-UNIFY-004 preflight)

- Run `--live` against preview.
- Run `--verify`.
- Assert every read path still returns identical results (canonical
  read now dominates; legacy read is fallback-only).
- Manual PM/Admin OI smoke test.
- Take an admin backup of the preview DB before the run.

### Phase C — production (DR-UNIFY-004)

- Take a Mongo Atlas snapshot of `masci_safety`.
- Run `--live --allow-prod`.
- Run `--verify --allow-prod`.
- Monitor `operational_facts` and `daily_reports` reads for 30 days.
- If no regressions, drop the legacy `dr_v2_*` collections in a
  subsequent DR-UNIFY-005 pass.

## Preserved indexes (recap)

- `dr_ai_cache` — unique on `("cache_key",)`, TTL on `cached_at`
  (24 h). Recreated on `daily_report_ai_cache` at first access.
- `photo_intelligence` — unique on `("project_id", "evidence_hash")`,
  hash + project single-field. Recreated on
  `daily_report_photo_intelligence` at first access.

## Read-compat during transition

- `lib/daily_report_collections.resolve_read_collection_name(db, canonical)`
  returns the canonical name when it holds data, else the legacy name,
  else the canonical (default target for fresh writes).
- This lets services adopt the canonical name incrementally without a
  big-bang cutover.

## Deferred to DR-UNIFY-004

- Live migration execution.
- Renaming index names inside `dr_ai/cache.py` and
  `photo_intelligence/store.py` to drop the `dr_v2_` prefix.
- Dropping the legacy collections.
- Renaming the backend module filenames (`routes/dr_v2_*.py` →
  `routes/daily_report_*.py`).
