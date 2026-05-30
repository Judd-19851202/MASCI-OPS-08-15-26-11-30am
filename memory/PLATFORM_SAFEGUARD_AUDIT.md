# PLATFORM_SAFEGUARD_AUDIT

**Date:** 2026-05-30 (Batch F · Phase 5)
**Method:** Code/runtime evidence audit of the 10 named safeguard categories.

---

## 1 · 10-category audit

### 1.1 — Backup creation
| Status | 🟢 OPERATIONAL |
|---|---|
| Code | `_run_scheduled_backup`, `_build_complete_archive_on_disk`, `_run_complete_archive_to_r2` |
| Runtime | Batch D proved scheduler creates archives. Batch E proved archives are well-formed. |
| Single point of failure | Worker process (single `asyncio.Task`). Supervisor respawns if it dies. |
| Improvements | Move build to a separate worker dyno isolated from request traffic (Phase 4 hardening · deferred) |

### 1.2 — Backup storage
| Status | 🟢 OPERATIONAL |
|---|---|
| Code | R2 (S3-compatible) via boto3 at `server.py:5566+` |
| Runtime | 1 517 objects in `masci-hub` bucket. 442 MB latest. 90-day lifecycle TTL on `backups/auto-90d/` prefix. |
| SPOF | R2 region (Cloudflare). No cross-region replication of the bucket today. |
| Improvements | Configure R2 cross-region replication OR mirror archives to S3 Glacier nightly |

### 1.3 — Backup validation
| Status | 🟡 PARTIAL |
|---|---|
| Code | `_backup_drift_watch` at `server.py:5930` — log-only collection-disappear detector |
| Runtime | Drift watch silent today (no drift). No manifest hash verification step at upload time. No automated post-upload "can this be opened" check. |
| SPOF | A corrupt-but-uploaded archive would not be detected until restore time. |
| Improvements | Add post-upload "open and walk first JSON" sanity check. Add periodic restore-drill cron (next-quarter ops). |

### 1.4 — Backup restore
| Status | 🟢 PROVEN (Batch E + Batch F) |
|---|---|
| Code | `scripts/restore_drill.py` (custom for complete-R2 format) · `/api/exports/restore` (for `/api/exports/full-backup` format only) |
| Runtime | Batch E confirmed end-to-end restore of complete-R2 archive in ~80 s. |
| SPOF | The drill script. If it bit-rots, restore fails. |
| Improvements | Add CI smoke test that runs `restore_drill.py` against a fixture archive on every backend deploy |

### 1.5 — Scheduler
| Status | 🟢 OPERATIONAL (post-Batch-D) |
|---|---|
| Code | `_backup_scheduler_loop` + supervisor at `server.py:11328 / 11399` |
| Runtime | Batch D proved alive after env-var flip. Healthy at T+0 and T+5. |
| SPOF | Single env-var (`SCHEDULER_ENABLED`) gates the entire system. Defensive supervisor respawns within 5 min. |
| Improvements | Self-monitoring email (Phase 3 hardening, deferred) — emit alarm to operator if no backup_health row in last 25 h |

### 1.6 — Recovery testing
| Status | 🟢 INITIAL CERTIFICATION (Batch E + Batch F) |
|---|---|
| Code | Manual via `restore_drill.py` |
| Runtime | First end-to-end drill executed today. No prior history. |
| SPOF | Drill is a one-shot human-initiated event. No periodic re-validation. |
| Improvements | Weekly automated restore drill into a side database with verdict email (would catch backup-format drift early) |

### 1.7 — Alerting
| Status | 🟡 PARTIAL |
|---|---|
| Code | Watchdog email at `server.py:5226` (after 25-h silence) · Sentry exception capture · backup-failure rows in `backup_health` |
| Runtime | Watchdog email path NOT yet exercised in production. Sentry active. |
| SPOF | The Resend integration (single email provider) |
| Improvements | Test watchdog email path (force 25-h silence in preview); add Slack/Telegram secondary channel |

### 1.8 — Monitoring
| Status | 🟢 OPERATIONAL |
|---|---|
| Code | `/api/admin/backups-scheduler-state` · `/api/admin/backups-complete-r2-state` · `/api/admin/backups-list-r2` · `/api/version` · `health_monitor_runs` collection · Sentry |
| Runtime | All endpoints functional. Sentry release fingerprint correct. |
| SPOF | Sentry dependency. |
| Improvements | Add an admin dashboard tile that exposes the scheduler's `boot_step` and recent `recent_health[]` rows directly in the UI |

### 1.9 — Retention
| Status | 🟡 PARTIAL |
|---|---|
| Code | R2 lifecycle rule on `backups/auto-90d/` prefix (90 days) · scheduler keeps last 14 days of LOCAL lite zips on worker disk |
| Runtime | Lifecycle rule applied. Oldest R2 archive in current sample is 5 days old (well within 90-day TTL). |
| SPOF | Lifecycle rule depends on Cloudflare. If misconfigured silently, archives never expire and bucket grows unbounded. |
| Improvements | Periodically validate the lifecycle rule is still applied to the bucket (1-line monthly cron) |

### 1.10 — Capacity planning
| Status | 🔴 GAP |
|---|---|
| Code | `cluster_capacity_history` collection logs Atlas cluster metrics over time |
| Runtime | Logging active (102 rows over time). NO automated forecasting or alerting on growth trends. |
| SPOF | Manual review of capacity trends. |
| Improvements | Add a "projected days to OOM/disk-full" calculation to `/api/admin/backups-scheduler-state` and surface to operator weekly digest. |

---

## 2 · "What single points of failure still exist?"

| Layer | SPOF |
|---|---|
| Backup creation | Single async task in main backend worker |
| Backup storage | Single R2 region (no cross-region replication) |
| Restore validation | One human-curated `restore_drill.py` script |
| Auth recovery | One `ADMIN_PASSWORD` env var (the only path in after restore) |
| Email alerts | One Resend account |
| Photo binaries | Single R2 bucket (same region as primary backup storage) |
| MongoDB | Single Atlas cluster (Atlas does internal redundancy; cross-cluster replication absent) |

The dominant SPOF concern: **all storage (Mongo Atlas + R2 backup + R2 photos) lives in geographically-co-located regions.** A regional outage that affects Cloudflare or Atlas's region could affect both primary and backup simultaneously.

---

## 3 · "What data can still be lost?"

| Data class | Worst-case loss window |
|---|---|
| Writes after the most recent archive | ≤ 60 min (hourly cadence) · ≤ 24 hr (recommended nightly) |
| Writes during a partial archive failure | up to 1 full archive cycle if the failure repeats |
| Sub-archive write traffic during the snapshot itself (race condition) | Minor — typically <1 minute of writes can be inconsistent across collections |
| Photos uploaded since the last complete-archive build (in `photos/` archive prefix) | Same as above, but ALSO depends on R2 photo path being live |
| `idempotency_keys`, `webauthn_challenges`, `admin_step_ups` | These are TTL-bound and intentionally not preserved |
| User authentication state (current sessions) | Always lost — `directory_sessions` typically expire in <1 day anyway |
| In-flight upload chunks (`temp_upload_chunks`) | Always lost — by design |

---

## 4 · "What recovery paths are not yet proven?"

| Path | Proven? | Last verified |
|---|---|---|
| Complete-R2 → Mongo restore | 🟢 YES | Batch E + Batch F (2026-05-30) |
| Complete-R2 → Mongo + backend boot | 🟢 YES | Batch F (today) |
| Complete-R2 → Mongo + backend + frontend | 🟡 LOGICAL ONLY | Frontend boot not exercised against restored DB |
| Complete-R2 → photo re-upload to R2 | ❌ NOT PROVEN | No automated path exists today |
| Lite-ZIP → restore | ❌ NOT PROVEN | `/api/exports/restore` would consume them; never drilled |
| Cross-region failover | ❌ NOT PROVEN | No cross-region infrastructure today |
| User reseed via admin UI post-restore | ❌ NOT PROVEN | Workflow plausible but never end-to-end demonstrated |
| Atlas cluster provisioning automation | ❌ NOT PROVEN | Manual today |

---

## 5 · Recommendations (prioritized)

| Priority | Recommendation | Effort | Closes |
|---|---|---|---|
| P0 | Toggle `BACKUP_R2_HOURLY=false` + `BACKUP_R2_FULL_HOUR_UTC=4` IMMEDIATELY | 0 (env-var) | GAP-3 trajectory |
| P0 | Photo offload from `daily_reports.subcontractors` + `daily_reports.photos` arrays into R2 references | 1-2 days | GAP-1 |
| P0 | Extend `_seed_hash` re-seed to cover `user_directory` | 1 hour | GAP-2 |
| P1 | Add `--restore-photos` flag to `restore_drill.py` | 2-4 hours | GAP-4 |
| P1 | Frontend end-to-end exercise against restored DB (one-shot) | 30 min | GAP-6 |
| P1 | Post-upload archive sanity check (open + first JSON walk) | 2 hours | §1.3 improvement |
| P2 | Weekly automated restore drill (preview) | 1 day | §1.6 improvement |
| P2 | Watchdog email path proof | 30 min | §1.7 improvement |
| P2 | "Days to OOM" projection in scheduler-state endpoint | 1 hour | §1.10 improvement |
| P3 | R2 cross-region replication / S3 Glacier mirror | 4+ hours of Cloudflare config | §1.2 improvement |
| P3 | Atlas provisioning automation (Terraform) | days | Manual recovery step #1 |

---

## 6 · Headline answer

**MASCI's backup-and-recovery posture is PROVEN at the data-and-application layer with documented gaps at the photo-payload and auth-reseed layers. The biggest immediate risk is `BACKUP_R2_HOURLY=true` + `daily_reports` photo bloat conspiring to OOM the worker within ~3 days. That's a single env-var flip away from neutralized.**
