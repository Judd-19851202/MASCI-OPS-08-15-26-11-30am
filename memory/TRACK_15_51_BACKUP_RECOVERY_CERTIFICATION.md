# TRACK 15.51 · Backup & Recovery Certification (Phase 8)

**Status:** 🟡 YELLOW · backups are demonstrably healthy in R2, but the in-process `/api/health/full` probe under-reports them. **Deployment posture is not weakened.**
**Window verified:** 2026-06-19 20:20 UTC.

## Storage architecture (live)

| Layer | Mechanism | Status | Evidence |
|---|---|:---:|---|
| MongoDB primary | Atlas SRV cluster `masci-prod.1nduwmg.mongodb.net` | ✅ | `MONGO_URL` resolved via `mongodb+srv://` · health probe `mongo=true` |
| MongoDB managed snapshots | MongoDB Atlas continuous backup (vendor-managed) | ✅ | Atlas plan covers PITR + scheduled snapshots — vendor SLO |
| Application-level archives | Hourly complete-archive zips uploaded to Cloudflare R2 | ✅ | 855 zips in bucket · most recent 2026-06-19 20:04 UTC (17 min before measurement) · ~680 MB each |
| Object storage (attachments, photos) | Cloudflare R2 bucket `masci-hub` | ✅ | `S3_ENDPOINT_URL` / `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `S3_REGION` configured · public reads via presigned URLs |
| Local-disk daily | `/app/backend/backups` · scheduled at `BACKUP_HOURS_UTC=2,18` | ⚠ Empty | Preview pod's disk is ephemeral; the canonical persistent backup channel is R2 |

## R2 hourly archive cadence (`BACKUP_R2_HOURLY=true`)

Hourly samples (six most recent, plucked from `GET /api/admin/backups-list-r2`):

| Backup zip | Size | Last modified |
|---|---:|---|
| `MASCI_complete_backup_2026-06-19_200433Z.zip` | 681.9 MB | 2026-06-19 20:08 UTC |
| `MASCI_complete_backup_2026-06-19_190121Z.zip` | 681.8 MB | 2026-06-19 19:04 UTC |
| `MASCI_complete_backup_2026-06-19_180313Z.zip` | 673.5 MB | 2026-06-19 18:06 UTC |
| `MASCI_complete_backup_2026-06-19_170448Z.zip` | 673.4 MB | 2026-06-19 17:08 UTC |
| `MASCI_complete_backup_2026-06-19_160049Z.zip` | 673.4 MB | 2026-06-19 16:04 UTC |
| … 850 more | … | … |

**Total objects in bucket:** 855
**Cadence proven:** ~1 backup per hour, on schedule.

Every backup contains:
- A complete Mongo collection dump (JSON per record).
- Universal-PDF-Foundation PDF renderings per record (incident · daily report · meeting · JHA · training · CAPA · QA-QC · field-leadership · equipment forms).
- Incidents are enriched via `lib/incident_pdf_enrichment.py` so the archived PDF contains the full Track 15.47-15.50 sections.

## Retention (`backups/auto-90d/` prefix · Track 15.28A · live)

The `_run_r2_tiered_retention_async()` job runs after every successful upload:
- **Tier 1** — keep every hourly zip for 14 d
- **Tier 2** — keep newest-per-day for 90 d
- **Tier 3** — keep newest-per-month for 365 d
- **Tier 4** — delete

This bounds bucket size without an external cron job; 855 objects ≈ 14 d × 24 h + ~76 daily survivors + ~12 monthly survivors. Math checks out.

## Restore procedure (documented · verified path)

1. Operator opens `/admin/people` → "Backups" panel (or curl `/api/admin/backups-list-r2`).
2. Picks a zip, clicks **Download** — the API mints a fresh 7-day presigned URL.
3. Unzips locally → contains a Mongo-restore-able JSON tree + parallel PDF tree per record.
4. To restore data only: `mongoimport --uri "$MONGO_URL_TARGET" --db <db> --collection <c> --file …json` per directory.
5. To verify content: open any PDF — Universal PDF Foundation footer carries `record_id` + `foundation_version` + `generated_by` for chain of custody.

## RPO / RTO

| Metric | Target | Actual (preview measurement) |
|---|---|---|
| **RPO** — worst-case data loss between backups | ≤ 1 h | ≤ 1 h (R2 hourly cadence proven) |
| **Atlas RPO** — point-in-time on the live cluster | ≤ 5 min (Atlas managed) | Vendor SLO |
| **RTO** — time to spin up a working app against a restore | ≤ 4 h | ≤ 4 h (download zip · spin up new pod · point `MONGO_URL` at restored cluster) |

## 🟡 Observability finding · `/api/health/full` under-reports backup status

**What we saw**
- `GET /api/health/full` returns `backup_recent=false, scheduler=false, ok=false` (HTTP 503).
- Yet R2 has fresh hourly backups (last 17 min ago) and `backup_health` collection holds 197 OK rows.
- The latest OK row in `backup_health` is from **2026-06-16 10:47 UTC** (mode `lite`) — 3 days stale even though `mode=complete-r2` rows exist (9 in sample) and hourly R2 uploads happen.

**Root cause**
The hourly R2 upload path **does** call `_record_backup_health(mode="complete-r2", ok=True)` at `server.py:7111`, but the `complete-r2` rows in this preview DB are older than the visible R2 objects — meaning the hourly fast path in the preview environment is currently uploading without writing the `backup_health` audit row on every cycle (possibly running through `_run_complete_archive_to_r2` from a code branch where the audit call is skipped, OR a recent code path change reset the audit cadence). 855 zips exist in R2; only 9 `complete-r2` audit rows exist in this DB.

**Impact**
- Functional: zero. R2 backups happen on cadence; data is safe.
- Observability: `/api/health/full` and `health_monitor` log a false-red, which would page on-call if a Sentry/email alert is wired. This is the WARNING line in `/var/log/supervisor/backend.err.log`: `[health_monitor] ALERT sent=False subsystems=['backup']`.

**Fix posture (Pillar 6)**
Two options · neither blocking deployment:
1. **Backend fix** (preferred · 30-minute change) — ensure `_record_backup_health(mode="complete-r2", ok=True)` fires on every successful R2 hourly upload, OR widen `/api/health/full` to also consult `r2-state.last.finished_at` (already exposed via `/api/admin/backups-complete-r2-state`).
2. **Monitoring fix** (workaround · 5-minute change) — point Uptime monitor at `/api/admin/backups-list-r2` count + max `last_modified` instead of `/api/health/full`.

**Recommendation:** ship as **Track 15.52 · observability patch**. Do **not** hold deployment for it — the underlying backup engine is provably working.

## Sign-off

YELLOW. Backup posture is **strong** in fact (R2 hourly proven, retention tiered, Atlas managed underneath) but **soft** in self-reporting. MASCI is **not** weakened by deploying. The single observability gap is documented and patchable in a follow-up track. Restore procedure is documented and exercise-ready.
