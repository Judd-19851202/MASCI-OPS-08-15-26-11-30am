# BACKUP-AUDIT-001 · ARCHITECTURE MAP

**Sprint:** BACKUP-AUDIT-001 (AUDIT ONLY)
**Date:** 2026-02-09

---

## Component inventory (read-only walk of /app/backend)

### 1. Disk-based scheduled backup
- **File:** `server.py`
- **Function:** `_run_scheduled_backup(db, lite_mode=False)` — lines 5380-5615
- **Trigger:** called from `_backup_scheduler_loop` (line 6924) on each scheduler tick
- **Behaviour:**
  - Pre-flight prune of orphan `.zip.tmp*` files older than 10 min
  - Drop archives past `BACKUP_RETENTION_DAYS` and over `BACKUP_KEEP_MAX`
  - OOM watermark preflight: if newest existing `MASCI_full_backup_*.zip` ≥ `BACKUP_FULL_OOM_WATERMARK_MB` (default 600 MB), auto-downgrade THIS run to lite (line 5459-5482)
  - Disk high-water-mark check: abort if disk ≥ 90% after emergency prune (line 5489-5505)
  - Stream-write `MASCI_full_backup_{stamp}.zip` (or `MASCI_lite_backup_{stamp}.zip`)
  - Best-effort email via `_email_backup_zip_from_path`
- **Writes:** `backup_health` row with `mode="full"` (line 5591) or `mode="lite"` (line 5549) or `mode="error"` (line 5612)
- **Storage:** `/app/backend/backups/` on the container disk

### 2. R2 complete archive (the hourly producer)
- **File:** `server.py`
- **Function:** `_run_complete_archive_to_r2(db)` — lines 6448-6552
- **Trigger:** called from `_backup_scheduler_loop` (line 7161) when `BACKUP_R2_HOURLY=true` and the current `YYYY-MM-DDTHH` bucket hasn't been fired yet (line 7149-7158). Falls back to once-per-day at `BACKUP_R2_FULL_HOUR_UTC` otherwise.
- **Behaviour:**
  - Skips if R2 (`photo_storage.is_configured`) not set up
  - Builds `MASCI_complete_backup_{stamp}.zip` on local disk into `/app/backend/backups/`
  - Calls `_backup_drift_watch` (iter426) to whisper-log collection drift
  - Uploads to `r2://{S3_BUCKET}/backups/auto-90d/{filename}` via `photo_storage.upload_local_file`
  - Generates a 7-day presigned URL
  - **Deletes the local copy** to keep disk clean (line 6511)
  - Background-spawns `_log_r2_usage_warning` (line 6530)
- **Writes:** `backup_health` row with `mode="complete-r2"` (line 6515) or `mode="complete-r2-error"` (line 6549)
- **Storage:** Cloudflare R2, prefix `backups/auto-90d/`

### 3. R2 bucket usage probe
- **File:** `server.py`
- **Function:** `_log_r2_usage_warning()` — lines 6305-6388
- **Trigger:** spawned by Component 2 after each successful upload
- **Behaviour:**
  - Sums R2 bucket size with `list_objects_v2` paginator
  - Logs OK / WARN / ALERT by GB thresholds `R2_USAGE_WARN_GB` (default 45) and `R2_USAGE_ALERT_GB` (default 50)
- **Writes:** `backup_health` row with `mode="r2-usage-warn"` or `mode="r2-usage-alert"` (line 6383) — these rows are written even though they represent a probe, NOT a backup
- **Side-effect on verifier:** these rows count toward the verifier's 20-row window, eating capacity that could otherwise hold lite/full rows

### 4. Backup watchdog
- **File:** `server.py`
- **Function:** `_backup_watchdog_check(db)` — lines 5722-5779
- **Trigger:** called from scheduler loop
- **Behaviour:**
  - Reads `find_one({"ok": True}, sort=[("ts", -1)])` — **NO MODE FILTER** so it correctly sees `complete-r2` rows
  - If newest ok-row is older than `BACKUP_WATCHDOG_HOURS` (default 25), fire alarm email (subject + body via `_send_watchdog_alarm`)
  - Cooldown: don't re-fire within `BACKUP_WATCHDOG_COOLDOWN_HOURS` (default 12), marker doc `_watchdog_last_alarm`
- **Writes:** marker doc only; doesn't write health rows

### 5. Weekly verification report ⚠ FAULTY COMPONENT
- **File:** `backup_verification.py`
- **Functions:**
  - `verification_scheduler_loop(db)` — lines 525-601 — Monday 14:00 UTC scheduler
  - `send_verification_email(db)` — lines 472-519 — builds + emails
  - `build_verification_report(db)` — lines 147-281 — assembles report dict
  - `list_r2_backup_archives(prefix="backups/")` — lines 95-141 — paginated R2 listing
  - `render_verification_email_html(report)` — lines 315-466 — HTML chrome
- **Trigger:** runs once per week at `BACKUP_VERIFICATION_DAY` × `BACKUP_VERIFICATION_HOUR_UTC` (default Mon 14:00 UTC = 10:00 AM ET)
- **Behaviour:**
  - Cross-checks R2 archive list against `backup_health` ledger
  - **Verdict = "pass" iff `r2_status == "ok"` AND `ledger_status == "ok"`**
  - **`ledger_status = "warn"` iff `last_full is None`**
  - **`last_full` ONLY set when `mode in ("full","lite")`** ← **THE BUG**
- **Writes:** marker doc `_verification_last_run` on each weekly fire (line 583)
- **Storage:** emails to `BACKUP_VERIFICATION_TO` → `BACKUP_EMAIL_TO` → `SAFETY_EMAIL_TO`

### 6. Restore tooling (manual, on-demand)
- **Files:**
  - `/app/scripts/restore_drill.py` (404 lines) — top-level operator entry
  - `/app/backend/tools/restore_drill.py` (287 lines) — preview-safety-gated restore engine
  - `/app/scripts/automated_drill.py` (544 lines) — orchestrates full drill including post-restore verification
- **Trigger:** manually invoked by operator (`python tools/restore_drill.py /tmp/archive.zip`)
- **Safety:**
  - Refuses unless `APP_ENV=preview` AND `DB_NAME` ends in `_preview`
  - Never touches `masci_safety` (prod)
  - Skips system collections
  - Uses ordered=False bulk writes — one bad doc cannot abort a collection
- **Writes:** creates / populates a separate `masci_restore_drill_*` database on the same cluster
- **Storage:** restored docs in dedicated drill DBs

### 7. Recovery / Persistence-health dashboards
- **Files:**
  - `/app/backend/routes/recovery_dashboard.py` — `/api/admin/recovery-dashboard`
  - `/app/backend/routes/admin_persistence_health.py` — `/api/admin/persistence-health`
  - `/app/backend/routes/admin_ops.py` — `/api/admin/ops/*`
  - `/app/backend/routes/backup_verification_routes.py` — `/api/admin/backup-verify`
- **Behaviour:** read-only summaries that reuse the same `backup_health` collection
- **Failure mode propagation:** these dashboards reuse the verifier's vocabulary, so any UI surface relying on `last_full` semantics inherits the same labeling defect

---

## Singleton scheduler / orchestration layer

- **File:** `/app/backend/lib/singleton_scheduler.py`
- **Mechanism:** every scheduler loop in the codebase is wrapped in a `run_with_singleton_lock` that uses a Mongo-document lock keyed by name (e.g., `backup_scheduler`, `safety_digest`, `operator_digest`, etc.). This guarantees that even when multiple uvicorn workers run, only one process executes the loop body.
- **Effect on backup scheduling:** `_backup_scheduler_loop` (server.py:6924) is invoked under `singleton-lock:backup_scheduler` (lib/singleton_scheduler.py:232). One worker per cluster owns the scheduler tick. R2 hourly cadence depends on this loop staying alive.

---

## Data stores

| Store | What | Role in pipeline |
|---|---|---|
| `backup_health` collection (200-row capped, FIFO) | history of backup events | source of truth for verifier + watchdog |
| `backup_drift_history` collection (30-row capped) | per-archive collection set | iter426 drift watcher |
| `/app/backend/backups/` (container disk) | local zips | transient — `complete-r2` deletes after upload; `full`/`lite` retained per `BACKUP_RETENTION_DAYS` × `BACKUP_KEEP_MAX` |
| `r2://{S3_BUCKET}/backups/` (Cloudflare R2) | archive at-rest | long-term backup store. Subdivided into `backups/auto-90d/` (lifecycle-managed by `scripts/r2_lifecycle_apply.py`) and legacy `backups/` prefix |
| `masci_restore_drill_*` DBs (Atlas) | restored archives | proves restoreability |

---

## Environment variables (live in `/app/backend/.env`)

| Variable | Default | Role |
|---|---|---|
| `BACKUP_R2_HOURLY` | `false` | Switches Component 2 from daily to hourly cadence (set `true` in production) |
| `BACKUP_R2_FULL_HOUR_UTC` | `3` | Daily-mode firing hour (only used when `BACKUP_R2_HOURLY=false`) |
| `BACKUP_LITE_MODE_ONLY` | `false` | Forces Component 1 into lite-mode permanently |
| `BACKUP_FULL_OOM_WATERMARK_MB` | `600` | If newest full zip ≥ this MB, auto-downgrade next run to lite. Set `0` to disable. |
| `BACKUP_DISK_HIGH_WATERMARK` | (?) | Disk pct that triggers emergency prune |
| `BACKUP_RETENTION_DAYS` | (?) | Local-disk retention window |
| `BACKUP_KEEP_MAX` | (?) | Local-disk file-count ceiling |
| `BACKUP_WATCHDOG_HOURS` | `25` | Component 4 firing threshold |
| `BACKUP_WATCHDOG_COOLDOWN_HOURS` | `12` | Component 4 cooldown |
| `BACKUP_VERIFICATION_ENABLED` | `true` | Component 5 master switch |
| `BACKUP_VERIFICATION_DAY` | `0` (Mon) | Component 5 weekday |
| `BACKUP_VERIFICATION_HOUR_UTC` | `14` | Component 5 hour |
| `BACKUP_VERIFICATION_MAX_AGE_HOURS` | `36` | Component 5's stale-archive threshold |
| `BACKUP_VERIFICATION_TO` → `BACKUP_EMAIL_TO` → `SAFETY_EMAIL_TO` | (cascaded) | Component 5 recipients |
| `R2_USAGE_WARN_GB` | `45` | Component 3 WARN threshold |
| `R2_USAGE_ALERT_GB` | `50` | Component 3 ALERT threshold |
| `S3_BUCKET` | (set) | R2 target bucket |
| `S3_ENDPOINT_URL` | (set) | R2 S3-compatible endpoint |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | (set) | R2 credentials |

---

## Where the bug lives

```python
# /app/backend/backup_verification.py, lines 192-204
async for r in db.backup_health.find({}, {"_id": 0}).sort("ts", -1).limit(20):
    recent_runs.append(r)
    if r.get("ok"):
        mode = (r.get("mode") or "").lower()
        if last_full is None and mode in ("full", "lite"):      # ← line 196
            last_full = r
        if last_r2 is None and "r2" in mode:                    # ← line 198 (collected, never used to gate the warning)
            last_r2 = r
    else:
        if last_failure is None:
            last_failure = r

# Lines 208-210
if last_full is None:
    ledger_status = "warn"
    ledger_issues.append("No successful full backup recorded in last 20 runs.")
```

**The mode whitelist `("full", "lite")` is the single source of the labeling defect.** `mode="complete-r2"` (the actual production R2 cadence) is excluded.

---

## What "the right answer" looks like (description only — NO CODE)

Three orthogonal, mutually-exclusive ways an operator can resolve the labeling defect with explicit OMEGA authorization. Listed here for situational awareness; **none implemented**:

- **Option α:** widen the verifier's whitelist to include `"complete-r2"` (and optionally `"r2"` as a substring) in the `last_full` test.
- **Option β:** rename `mode="complete-r2"` in `_run_complete_archive_to_r2` to `mode="full-r2"` so the substring `"full"` already in the whitelist via prefix-style match would catch it. (Would break audit comparability with historical 95 `complete-r2` rows unless coupled with a migration.)
- **Option γ:** introduce a tier-aware ledger doctrine (`tier in ("disk","r2","probe")`) and update both the writers and the verifier accordingly.

🛑 **Audit-only.** Do not implement.
