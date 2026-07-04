# Production R2 Photo Migration — Cutover Runbook (Iter64 Phase 2)

This is the **production deployment guide** for moving MASCI Hub photos
out of MongoDB and into Cloudflare R2. The preview environment already
has this fully wired and tested (Iter64 Phase 2, 2026-05-11). Run this
runbook on `mascidocs.com` to do the same.

## Why this matters

Production MongoDB had crossed 887 MB of photos. Every full backup zip
was OOM-killing the worker → backup outages and the 3-minute prod
incident that Iter62/63 partially mitigated. The watermark + watchdog
were defense in depth; **this migration is the real cure**.

After cutover, the prod DB shrinks back to <10 MB and the full backup
zip drops to ~10 MB (the JSON envelope). Photos live in R2 (~$0.015 / GB-month),
served via dual-read so legacy + migrated photos render identically.

## Prerequisites

- Admin access to the Emergent platform for the prod deploy
- Admin token for `mascidocs.com`
- Cloudflare R2 dashboard access (account `46400762d3027afbb26819a8de8528e6`,
  bucket `masci-hub`)

## Step-by-step cutover

### 1. Set R2 env vars on production

Add the following to the **prod** `/app/backend/.env` (same values that
already work in preview):

```
S3_ENDPOINT_URL=https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com
S3_BUCKET=masci-hub
S3_ACCESS_KEY=497c8b329e4cc63c4e3b9caf1fb9270e
S3_SECRET_KEY=332a6949d3d55a76a8c389be8625259a2696a0deb4a4816756fb9bb2c360bb03
S3_REGION=auto
```

> ⚠️ Treat the secret key like the bcrypt secret. Anyone with this can
> read every customer photo. Rotate via the R2 dashboard if a leak is
> ever suspected — the backend reads env at boot so a Save to GitHub +
> redeploy rotates them in one cycle.

### 2. Deploy the iter64 Phase 2 code

Push to `mascidocs.com`. The deploy will pull in:

- `boto3` (already in `requirements.txt` from Phase 1)
- The dual-read photo loader in `routes/job_photos.py`
- Photo:// resolver in `pdf_render.py` + `field_leadership_pdf.py` + `safety_forms.py`
- Auto-vacuum tick in `routes/job_photos.py::background_indexer_loop` (every 10 min)
- 4 admin endpoints for migration control

### 3. Verify R2 connectivity (60 seconds)

```bash
TOKEN=$(curl -sX POST https://mascidocs.com/api/admin/login \
  -H "Content-Type: application/json" -d '{"password":"..."}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

curl -sH "X-Admin-Token: $TOKEN" \
  https://mascidocs.com/api/admin/photo-storage/health
```

Expected output:
```json
{"configured":true,"ok":true,"bucket":"masci-hub","endpoint":"..."}
```

### 4. Dry-run the migration (5-30 seconds)

Counts total scope without writing anything to R2 or Mongo:

```bash
curl -sX POST -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run":true,"limit_per_collection":10000,"resume":false}' \
  https://mascidocs.com/api/admin/photos/migrate
```

You'll see `photos_migrated` totaling the full prod photo count (hundreds
to low thousands of photos) and `bytes_migrated` roughly equal to the
size of the photos in Mongo. **Snapshot this number for comparison.**

### 5. Real run — daily_reports first (15-30 min for ~500 photos)

Migrate just one collection first as a canary:

```bash
curl -sX POST -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run":false,"limit_per_collection":1000,"collection":"daily_reports","resume":true}' \
  https://mascidocs.com/api/admin/photos/migrate
```

**Verify** by opening any recent daily report's gallery page on
`mascidocs.com/admin/photos` — every photo should still render.
The thumbs are served via the dual-read path (`_load_photo_bytes`),
so legacy + migrated photos appear identically.

### 6. Real run — every remaining collection

```bash
for COL in inspections qaqc_inspections safety_incidents meetings \
           jha_records equipment_inspections shop_signoffs \
           safety_form_records safety_equipment_trainings \
           safety_equipment_returns field_leadership_records; do
  echo "=== Migrating $COL ==="
  curl -sX POST -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
    -d "{\"dry_run\":false,\"limit_per_collection\":2000,\"collection\":\"$COL\",\"resume\":true}" \
    https://mascidocs.com/api/admin/photos/migrate
done
```

`resume:true` means re-running is safe and picks up where the last
attempt left off. If a run times out, just re-call — already-migrated
photos are skipped on subsequent passes.

### 7. Verify success

```bash
# How much migrated total?
curl -sH "X-Admin-Token: $TOKEN" \
  https://mascidocs.com/api/admin/photos/migrate/progress | python3 -m json.tool

# Confirm dry-run now reports 0 photos to migrate
curl -sX POST -H "X-Admin-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"dry_run":true,"limit_per_collection":10000,"resume":false}' \
  https://mascidocs.com/api/admin/photos/migrate | python3 -m json.tool
```

`photos_migrated` should now report a very small number (any photos
uploaded since the last migration tick). The 10-minute auto-vacuum
hook in `background_indexer_loop` cleans these up automatically.

### 8. Flip lite-mode-only OFF

Once you've confirmed the gallery still works and photos are in R2,
**remove the `BACKUP_LITE_MODE_ONLY=true` env on prod** (or set it to
`false`). The next scheduled backup will be the FULL archive — but
because all photos now live in R2, the archive zip should be <10 MB
instead of 887 MB. No more OOMs.

### 9. (Optional) Wipe the OOM watermark

If you want to push the watermark high since the archive is now small,
set `BACKUP_FULL_OOM_WATERMARK_MB=50` so even a regression past 50 MB
triggers the auto-downgrade. The default 600 MB is now overly generous.

## Rollback (if anything breaks)

The dual-read path means a rollback is "delete the R2 bucket and the
photo:// strings continue to be stored in Mongo." But because the
migration **replaces** the base64 in Mongo with a photo:// ref, you
can't simply unwind the migration. There are two recovery paths:

1. **Halt and observe** — if a single photo doesn't render, every
   read path falls back to `_load_photo_bytes` which logs a clear
   error. The other 99% of photos keep working. Add the failing photo
   to a manual list and investigate.

2. **Restore from a backup zip** — every nightly backup zip contains
   the full Mongo dump including the base64 photo strings (or, after
   migration, the photo:// strings). Importing a pre-migration backup
   restores base64 storage as if the migration never happened.

## What's still on the to-do list

After this cutover succeeds:

- **Wire backup zips to R2** — currently lives on the worker filesystem,
  emailed via Resend. Putting zips at `r2://masci-hub/backups/` means
  retention is decoupled from worker disk and Resend's 40 MB attachment
  cap. Suggested follow-up (Iter64 Phase 3 or Iter65).
- **Wire NEW uploads directly to R2** — currently new photos still go
  to Mongo as base64 and the 10-min vacuum sweeps them out. Direct
  R2 writes from the upload endpoints would skip the round-trip.
  Operationally identical, just faster.

## Files of reference

- `/app/backend/photo_storage.py` — S3 client + sync/async read helpers
- `/app/backend/photo_migration.py` — batch migrator
- `/app/backend/routes/job_photos.py` — dual-read photo loader + auto-vacuum
- `/app/backend/pdf_render.py` — PDF photo embedding (dual-read)
- `/app/backend/field_leadership_pdf.py` — Field Leadership PDF (dual-read)
- `/app/backend/routes/safety_forms.py` — Safety Forms PDF (dual-read)
- `/app/backend/tests/test_iter64_photo_storage.py` — 12 regression tests
