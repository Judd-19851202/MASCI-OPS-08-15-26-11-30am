# TRACK 15.52A · Backup Architecture Map

**Status:** Read-only inventory · captured 2026-06-19 ~20:45 UTC from live code, live env, and live API responses.
**Premise tested:** "Multiple backup systems may be running, the cadence may not match intent."
**Verdict:** **ONE backup-creator path · ZERO duplicates · ZERO orphans.**

## 1 · The single backup-creator pipeline

```
                ┌────────────────────────────────────────────────────┐
                │  _backup_scheduler_loop(db)   [server.py:7624]     │
                │  · 5-min tick · gated by SCHEDULER_ENABLED env     │
                │  · wrapped by run_with_singleton_lock              │
                └─────────────────────────┬──────────────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  │                       │                       │
                  ▼                       ▼                       ▼
        ┌────────────────┐     ┌─────────────────────┐   ┌───────────────────┐
        │ Local-disk path│     │  R2 path            │   │  Watchdog         │
        │ BACKUP_HOURS_UTC│     │ _run_complete_      │   │ _backup_watchdog_ │
        │ default = 2,18 │     │ archive_to_r2()     │   │ check()           │
        │ writes to      │     │ writes to R2 bucket │   │ alerts when stale │
        │ /app/backend/  │     │ s3://masci-hub/     │   │                   │
        │ backups/       │     │ backups/auto-90d/   │   │                   │
        │                │     │ MASCI_complete_..   │   │                   │
        │ daily ×2       │     │ HOURLY when         │   │ runs every tick   │
        │                │     │ BACKUP_R2_HOURLY=   │   │                   │
        │                │     │ true; daily at hour │   │                   │
        │                │     │ BACKUP_R2_FULL_HOUR_│   │                   │
        │                │     │ UTC (default 03) if │   │                   │
        │                │     │ HOURLY off          │   │                   │
        └────────────────┘     └─────────────────────┘   └───────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────────┐
                              │ Tiered retention         │
                              │ _run_r2_tiered_retention │
                              │ 14d hourly · 90d daily · │
                              │ 365d monthly · then del  │
                              └──────────────────────────┘
                                          │
                                          ▼
                              ┌──────────────────────────┐
                              │ Audit row written         │
                              │ _record_backup_health     │
                              │ → db.backup_health        │
                              │ mode=complete-r2 ok=true  │
                              └──────────────────────────┘
```

## 2 · Adjacent (non-backup-creator) machinery

| System | File | Function | Cadence | Verdict |
|---|---|---|---|---|
| Weekly heartbeat report | `backend/backup_verification.py` | Cross-checks `backup_health` + R2 bucket; emails PASS/FAIL summary | Monday 14:00 UTC | Health probe · NOT a backup creator |
| Manual restore drill | `scripts/automated_drill.py` | Pulls latest R2 zip into isolated drill DB; reports verification axes A1-A10 | Operator-triggered (`No cron, no scheduler integration`) | Restore exerciser · NOT a backup creator |
| Manual single-file restore | `scripts/restore_drill.py` | Same flow, single archive | Operator-triggered | Restore exerciser · NOT a backup creator |
| Recovery dashboard route | `backend/routes/recovery_dashboard.py` | Admin-only diagnostic surface | Polled by admin UI only | Read-only · NOT a backup creator |

**Conclusion:** Only ONE machine creates backups (`_run_complete_archive_to_r2`). The rest READ or DRILL. There is no V2 system, no duplicate scheduler, no orphan worker.

## 3 · GitHub workflows

| Workflow | File | Triggers | Probes | Backups touched? |
|---|---|---|---|---|
| `production-health-probe` | `.github/workflows/production-health-probe.yml` | `cron */15 * * * *` + workflow_dispatch | `/api/health` · `/api/passkeys/login/options` · `/api/admin-strict/diag/persistence-health` · `/api/field-memory/recent` · `/api/dispatch/operational-moments/by-assignment/test` | **No** — read-only, never calls `/api/health/full` |
| `sigma3-deploy-gate` | `.github/workflows/sigma3-deploy-gate.yml` | push to main/master · workflow_dispatch | ruff + python compileall + governance artefact existence check | No |
| `MASCI Hub CI Gate` (`ci.yml`) | `.github/workflows/ci.yml` | push/PR/workflow_dispatch | ruff + python compile + frontend lint+build | No |

None of the workflows creates backups. None of the workflows even probes `/api/health/full`. The only external consumer of `/api/health/full` is **UptimeRobot** (per `backend/tests/test_iter183_health_full_endpoint.py` doc-string and `backend/server.py` body comment).

## 4 · OS-level scheduling

- `/etc/cron.d` → only `e2scrub_all` (Debian disk hygiene). **No backup cron.**
- `/etc/cron.daily` → `apt-compat`, `dpkg`. **No backup cron.**
- `crontab -l` (root) → none. **No backup cron.**
- `systemd timers` → none. **No backup cron.**
- `/etc/supervisor/conf.d/supervisord.conf` → ONE uvicorn worker `--workers 1 --reload`. **No multi-worker exposure.**

## 5 · No-duplicate audit

| Concern | Verified |
|---|:---:|
| Multiple backup schedulers? | ✅ NO. Single `_backup_scheduler_loop`. |
| Multiple R2-upload paths? | ✅ NO. Single `_run_complete_archive_to_r2`. |
| Multiple workers firing in parallel? | ✅ NO. Singleton-lock via `scheduler_locks` collection (`lib/singleton_scheduler.py`). |
| Cron + scheduler racing? | ✅ NO. No OS cron creates backups. |
| GitHub Actions firing backups? | ✅ NO. All 3 workflows are read-only / static-check. |
| Cloudflare Workers? | ✅ NO. None configured. |
| Atlas Triggers? | ✅ NO. Not referenced in any code path. |

**Architecture confidence: HIGH.**
