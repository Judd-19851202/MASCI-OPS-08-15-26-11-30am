# TRACK 15.36 · Backup Inventory

**Track:** 15.36 · READ-ONLY · do not change anything
**Date:** 2026-02 (probes captured 2026-06-19 ~10:50 UTC against `mascidocs.com` production)

Every backup / recovery mechanism that exists in the running system, with documented evidence.

---

## B-01 · R2 Hourly Complete Backup (Tier-1 active archive)

| Attribute | Value |
|---|---|
| **Name** | R2 Hourly Complete Backup |
| **Purpose** | Disaster recovery + point-in-time recovery for entire Mongo DB + inlined R2 photos |
| **Trigger** | `_backup_scheduler_loop` in `server.py` → `_run_complete_archive_to_r2(db)` |
| **Frequency** | Every UTC hour (top-of-hour bucket via `_BACKUP_SCHEDULER_STATE["last_r2_complete_hour"]`); enabled by `BACKUP_R2_HOURLY=true` |
| **Storage** | `r2://<S3_BUCKET>/backups/auto-90d/` |
| **Naming** | `MASCI_complete_backup_YYYY-MM-DD_HHMMSSZ.zip` |
| **Owner** | `_run_complete_archive_to_r2` (server.py:6938) + `_build_complete_archive_on_disk` (server.py:6510) |
| **Retention** | 14d hourly / 90d daily / 365d monthly / delete via `lib/r2_retention.py:enforce_r2_retention` |
| **Delete mechanism** | `_run_r2_tiered_retention_async()` runs after each backup tick (server.py:7030) |
| **Restore mechanism** | `POST /api/exports/restore` (server.py:8541) — manifest-validated, env-validated, 500 MB upload ceiling |
| **Status** | 🟢 **ACTIVE** |
| **Live evidence** | newest `MASCI_complete_backup_2026-06-19_100315Z.zip` · 632 MB · 138,236 records · ts 2026-06-19T10:06:11Z (production probe) |
| **Cadence verification** | 06:00, 07:00, 08:00, 09:00, 10:00 UTC on 2026-06-19 — exact hourly ticks |

---

## B-02 · Email Backup (nightly · BACKUP_HOURS_UTC)

| Attribute | Value |
|---|---|
| **Name** | Email Backup |
| **Purpose** | Off-site copy in admin inbox; works when Atlas + R2 are both unavailable |
| **Trigger** | `_backup_scheduler_loop` due-hour check |
| **Frequency** | 2× daily at UTC hours from `BACKUP_HOURS_UTC=2,18` (02:00 + 18:00 UTC) |
| **Storage** | Email attachment to `BACKUP_EMAIL_TO` (currently `jaymn.judd@mascigc.com`) |
| **Naming** | Lite backup zip — DB JSON only (no photos) |
| **Owner** | `_run_scheduled_backup(db)` (server.py:7609) |
| **Retention** | Inbox-managed (no programmatic delete) |
| **Restore** | Operator downloads attachment → `POST /api/exports/restore` |
| **Status** | 🟢 **ACTIVE** (`last_run_for_hour: {"2":"2026-06-19"}`) |
| **Watchdog** | `_backup_watchdog_check` — alarm if >25 hours silent |

---

## B-03 · R2 Tiered Retention Pruner

| Attribute | Value |
|---|---|
| **Name** | R2 Tiered Retention (Track 15.28A) |
| **Purpose** | Bound R2 backup storage growth |
| **Trigger** | Fire-and-forget `asyncio.create_task(_run_r2_tiered_retention_async())` (server.py:7030) after each backup |
| **Policy** | Tier 1 (≤14d) keep all · Tier 2 (14-90d) newest/day · Tier 3 (90-365d) newest/month · Tier 4 (>365d) delete |
| **Scope** | ONLY `r2://<bucket>/backups/auto-90d/` prefix |
| **Idempotent** | Yes (pure-function `plan_retention` → batched 1000-key DeleteObjects) |
| **Status** | 🟢 **ACTIVE** (verified by `backups/auto-90d/` prefix has 364 objects — close to expected 336 hourly + 76 daily + 9 monthly) |
| **Gap** | Legacy `r2://<bucket>/backups/<no-subprefix>` is **explicitly out of scope** (~500 stale objects, see B-12) |

---

## B-04 · Backup Verification Cron

| Attribute | Value |
|---|---|
| **Name** | Weekly Backup Verification (`backup_verification.py`) |
| **Purpose** | Positive heartbeat — emails PASS/FAIL summary cross-checking Mongo `backup_health` vs real R2 prefix |
| **Frequency** | Mon 14:00 UTC by default (`BACKUP_VERIFICATION_DAY=0 HOUR=14`) |
| **Recipients** | `BACKUP_VERIFICATION_TO` → fallback `BACKUP_EMAIL_TO` → `SAFETY_EMAIL_TO` |
| **Max-age threshold** | 36 hours (alert if newest R2 archive older than 36h) |
| **Status** | 🟢 **ACTIVE** (`enabled: true`, `last_run_iso: 2026-06-15T14:00:00Z`, `next_fire_iso: 2026-06-22T14:00:00Z`) |

---

## B-05 · Backup Watchdog

| Attribute | Value |
|---|---|
| **Name** | `_backup_watchdog_check` |
| **Trigger** | Runs every 5-min tick inside `_backup_scheduler_loop` |
| **Behavior** | Rate-limited alarm email if hours-silent crosses watchdog threshold (25h) |
| **Status** | 🟢 **ACTIVE** (`last_watchdog: {alarm_fired: false, hours_silent: 0.7, reason: healthy}`) |

---

## B-06 · R2 Usage Probe

| Attribute | Value |
|---|---|
| **Name** | `_log_r2_usage_warning` |
| **Trigger** | Fire-and-forget on every backup tick (server.py:7020) |
| **Behavior** | Sums whole-bucket size; writes `r2-usage-warn` (≥45 GB) or `r2-usage-alert` (≥50 GB) row to `backup_health` |
| **Defaults** | `R2_USAGE_WARN_GB=45` · `R2_USAGE_ALERT_GB=50` |
| **Current state** | 🚨 **ALERT** — bucket = 197.13 GiB · 8,517 objects (live as of 2026-06-19T10:06:16Z) |
| **Action taken** | None — explicitly does NOT email (anti-storm); pure log + DB row only |

---

## B-07 · Soft-Delete Restore Endpoints (per-collection)

Per-collection undo paths for individual records. **Not full-DB restore — record-scoped reversal of `is_deleted=true` toggles.**

| Endpoint | Restores |
|---|---|
| `POST /api/admin/employees/{id}/restore` (server.py:3817) | Single soft-deleted employee |
| `POST /api/admin/jobs/{id}/restore` (server.py:3627) | Single soft-deleted project/job |
| `POST /api/admin/equipment-master/{unit_id}/restore` (server.py:3099) | Single soft-deleted equipment row |
| `POST /api/admin/suppliers/{supplier_id}/restore` (server.py:4227) | Single soft-deleted supplier |

| **Status** | 🟢 **ACTIVE** |
| **Limitation** | Each only undoes ITS collection's soft-delete. Cannot restore documents that were HARD-deleted (no soft-delete flag set). |

---

## B-08 · Full-Backup Restore Endpoint

| Attribute | Value |
|---|---|
| **Endpoint** | `POST /api/exports/restore` (server.py:8541) |
| **Input** | Operator uploads a `.zip` (must include `backup_manifest.json`) · 500 MB ceiling on upload |
| **Validates** | Manifest schema + `environment` field + `database_name` matches current runtime (Track 14.0-I1) |
| **Modes** | `merge=true` (upsert by id) OR `merge=false` (wipe + insert; **destructive**) |
| **Audit** | Logs every restore to `audit_events` with archive origin |
| **Status** | 🟢 **ACTIVE** |
| **Gap** | Upload ceiling = 500 MB · current backups average 600 MB → **cannot upload current backups via this endpoint**. Operator must pull zip from R2, extract relevant collections, repackage. |

---

## B-09 · Atlas Cluster (MongoDB)

| Attribute | Value |
|---|---|
| **Cluster** | `masci-prod.1nduwmg.mongodb.net` |
| **DB name** | `masci_safety` |
| **Engine** | MongoDB 8.0.26 |
| **Collections** | 163 (as of 2026-06-19) |
| **Storage cap (configured)** | `ATLAS_QUOTA_MB=10240` (10 GiB) |
| **Atlas backup tier** | ❓ **OPERATOR REQUIRED** — pod cannot query Atlas Admin API. Verify in Atlas dashboard: |
|  | 1. Is "Continuous Cloud Backup" enabled? |
|  | 2. Snapshot retention window (default 2d / 7d / 30d depending on tier)? |
|  | 3. PITR window (default 24h)? |
|  | 4. Earliest restorable time? |
| **Status** | ❓ **UNKNOWN** (presumed active for production cluster, must verify) |

---

## B-10 · R2 Bucket (Cloudflare)

| Attribute | Value |
|---|---|
| **Endpoint** | `S3_ENDPOINT_URL` (Cloudflare R2) |
| **Bucket** | `S3_BUCKET` |
| **Total bucket size** | 197.13 GiB · 8,517 objects (probe 2026-06-19T10:06:16Z) |
| **Backups prefix only** | 864 objects under `backups/` (363 `auto-90d/` + ~500 legacy) · sampled 500-newest sum = 182 GiB |
| **Versioning** | ❓ **OPERATOR REQUIRED** — pod cannot query R2 bucket settings. Verify in Cloudflare dashboard: |
|  | 1. Is object versioning enabled? (R2 supports it as of late 2025) |
|  | 2. Are deletes recoverable? (depends on versioning) |
|  | 3. Is there a lifecycle policy already? |
|  | 4. Is there object-lock? |
|  | 5. Is audit logging enabled? |
| **Status** | 🟢 **ACTIVE** (writes succeeding hourly) · 🚨 **AT ALERT** (197 GB > 50 GB threshold) |

---

## B-11 · Local Pod Disk Backup (transient)

| Attribute | Value |
|---|---|
| **Location** | `/app/backend/backups/` (`BACKUPS_DIR`) |
| **Lifecycle** | Backup built on disk → uploaded to R2 → local file `unlink()`d |
| **Persistence** | Volatile — pod restart wipes anything not yet uploaded |
| **Emergency brake** | `_emergency_prune_backups(reason=…)` fires when disk >77% before build |
| **Status** | 🟡 **TRANSIENT** (not a real backup — just staging) |

---

## B-12 · Legacy R2 `backups/` Prefix (out-of-scope of retention)

| Attribute | Value |
|---|---|
| **Location** | `r2://<bucket>/backups/MASCI_*.zip` (no `auto-90d/` sub-prefix) |
| **Origin** | Pre-iter184 backups |
| **Object count** | ~500 (864 total `backups/` − 364 `auto-90d/`) |
| **Status** | 🟡 **LEGACY · UNPRUNED** — comment at server.py:6990 explicitly states "legacy backups previously written to `backups/*.zip` are intentionally OUT of scope" |
| **Operator note** | Documented in `R2_RETENTION_AUDIT.md` as "cleaned up manually later with explicit operator approval" |

---

## B-13 · GitHub Source Control

| Attribute | Value |
|---|---|
| **Purpose** | Code recovery (only) |
| **Trigger** | "Save to GitHub" button in Emergent chat |
| **Frequency** | Operator-initiated |
| **Status** | 🟢 **AVAILABLE** but **not a data backup** |

---

## B-14 · Drift Watcher

| Attribute | Value |
|---|---|
| **Name** | `_backup_drift_watch` (server.py:6981) |
| **Purpose** | Calm log warning when a collection silently disappears between archives |
| **Status** | 🟡 **DORMANT** — `drift_watch_active: false, drift_watch_reason: drift watcher heartbeat not seen` |
| **Risk** | If a collection were accidentally dropped, no automatic alert would fire |

---

## What is NOT backed up (by design)

From `BACKUP_EXPLICIT_EXCLUSIONS`:

| Collection | Reason |
|---|---|
| `system.indexes` | MongoDB internal |
| `usage_events` | Regenerable API telemetry (iter441) |
| `health_monitor_runs` | Regenerable scheduler health series (iter441) |
| `job_photo_thumb_cache` | Regenerable derivative photo cache (iter441) |

From `BACKUP_SENSITIVE_FIELD_REDACTION` (data backed up but fields stripped):

| Collection | Stripped fields |
|---|---|
| `users` | `password_hash` |
| `user_directory` | `password_hash`, `mfa.secret`, `mfa.recovery_codes` |

---

## Summary of statuses

| Status | Items |
|---|---|
| 🟢 ACTIVE | B-01, B-02, B-03, B-04, B-05, B-06, B-07, B-08, B-13 |
| 🟡 TRANSIENT/LEGACY/DORMANT | B-11, B-12, B-14 |
| ❓ UNKNOWN (operator must verify) | B-09 (Atlas), B-10 (R2 versioning) |
| 🚨 ALERT (acknowledged, not acted on) | B-06 (R2 bucket at 197 GiB vs 50 GiB threshold) |
