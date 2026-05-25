# PHASE26_1_BACKUP_RETENTION_VERIFICATION.md
## MASCI Operations Platform · Phase 26.1 · Backup Retention Verification
## iter427 · 2026-05-25

---

## Verified configuration

| Env var | Value | Effect |
|---|---|---|
| `BACKUP_RETENTION_DAYS` | 14 | local archives older than this are pruned |
| `BACKUP_KEEP_MAX` | 3 | local archive count ceiling |
| `BACKUP_DISK_HIGH_WATERMARK` | 75 % | when `/app` disk crosses this, emergency prune fires |
| `BACKUP_DISK_WARN_WATERMARK` | (from server.py) | log-only soft warning |
| `BACKUP_HOURS_UTC` | 2, 18 | scheduled archive ticks |
| `BACKUP_R2_HOURLY` | true | hourly R2 archive enabled |
| `BACKUP_LITE_MODE_ONLY` | (off in preview) | escape hatch if full zip > worker memory ceiling |
| `BACKUP_EMAIL_TO` | jaymn.judd@mascigc.com | email recipient for manual backup |

---

## Verified prune behavior

### Pre-iter427

| Pattern | Pruned by `_emergency_prune_backups`? | Pruned by `_run_scheduled_backup` pre-flight? |
|---|---|---|
| `MASCI_full_backup_*.zip` | ✅ | ✅ |
| `MASCI_complete_backup_*.zip` (pre-iter425 legacy) | ❌ | ❌ |
| `MASCI_lite_backup_*.zip` (legacy) | ❌ | ❌ |
| `.zip.tmp.*` orphans > 10 min old | ✅ | ✅ |

→ Pre-existing bug: legacy `lite` + `complete` patterns accumulated
forever once the iter425 archive was renamed to `full_backup`.
Evidence: 318 lite files + 3 complete files lingering since 2026-05-11.

### Post-iter427 (current)

| Pattern | Pruned by `_emergency_prune_backups`? | Pruned by `_run_scheduled_backup` pre-flight? |
|---|---|---|
| `MASCI_full_backup_*.zip` | ✅ | ✅ |
| `MASCI_complete_backup_*.zip` | ✅ (past `BACKUP_RETENTION_DAYS`) | ✅ |
| `MASCI_lite_backup_*.zip` | ✅ (past `BACKUP_RETENTION_DAYS`) | ✅ |
| `.zip.tmp.*` orphans > 10 min old | ✅ | ✅ |

Verified by `test_iter427_legacy_backup_prune.py`:

```
test_iter427_emergency_prune_sweeps_legacy_patterns ............... PASSED
test_iter427_prune_preserves_young_legacy ......................... PASSED
```

Both also pass when combined with the full backup parity-lock subset
(`test_iter425_backup_auto_discovery.py`, `test_iter426_restore_drift_watcher.py`).

---

## Verified manifest fields (iter425 / iter426)

| Manifest key | Verified |
|---|---|
| `captured_collections` | ✅ |
| `explicit_exclusions` | ✅ (currently empty list) |
| `redaction_rules_applied` | ✅ (MFA secret + recovery_codes + password_hash redacted) |
| `disk_files_count` | ✅ |
| `disk_bytes` | ✅ |
| `app_version` | ✅ |
| `captured_at_utc` | ✅ |
| `retention_days` | ✅ (echoed into manifest) |

---

## Local + R2 retention reconciliation

| Surface | Retention | Status |
|---|---|---|
| `/app/backend/backups/*.zip` (local) | ≤14 days × ≤3 archives | 🟢 hardened in iter427 |
| `/app/backend/backups/*.zip.tmp.*` (orphans) | ≤10 min | 🟢 |
| R2 (Cloudflare object store) | depends on R2 lifecycle policy at the bucket level (NOT managed by `server.py`) | 🟡 confirm R2 lifecycle policy on the operator's R2 console |
| `backup_drift_history` (Mongo) | last 30 snapshots | 🟢 FIFO-trimmed in `_backup_drift_watch` |
| `r2_degraded_events` / `digest_runs` / `health_monitor_runs` / `system_health_events` / `audit_events` | 30-day TTL | 🟢 |

---

## Snapshot pipeline integrity (post-iter427)

| Pipeline | Status |
|---|---|
| Hourly R2 archive (`_run_complete_archive_to_r2`) | 🟢 running · drift watcher hook intact |
| Nightly fallback archive (03:00 UTC) | 🟢 same code path |
| Manual `/admin/system` archive button | 🟢 same code path |
| Pre-flight prune | 🟢 sweeps full + legacy patterns now |
| Boot prune (when disk > 75 %) | 🟢 same code path |
| Auto-discovery via `db.list_collection_names()` | 🟢 iter425 verified |
| MFA / password redaction | 🟢 iter425 verified |
| Drift watcher | 🟢 iter426 verified |
| Memory doc inclusion in zip | 🟢 iter426 `DISK_BACKUP_ROOTS` |

---

## Defects found vs fixed

| Defect | Severity | Fix |
|---|---|---|
| Legacy `lite` + `complete` patterns never pruned by `_emergency_prune_backups` | 🟡 Medium · 26 MB + 321 inodes accumulated since 2026-05-11 | 🟢 Shipped iter427: prune now sweeps both patterns past retention |
| Same gap in `_run_scheduled_backup` pre-flight | 🟡 Medium · same root cause | 🟢 Shipped iter427: same fix in pre-flight block |
| No regression test guarding legacy-pattern sweep | 🟡 Medium | 🟢 Shipped iter427: `test_iter427_legacy_backup_prune.py` (2 tests) |

---

## Remaining concerns

| Concern | Status | Plan |
|---|---|---|
| Two 1.6 GB full backups locally (3.1 GB combined) keeping disk at 93 % | 🟡 within configured `BACKUP_KEEP_MAX=3` ceiling · pre-flight prune at next archive tick will drop the oldest if necessary | 🟢 self-healing |
| R2 lifecycle policy not visible from inside the platform | 🟡 R2 console-side concern · NOT in `server.py` scope | 🟡 Operator action: verify R2 lifecycle rule keeps 30 days of `MASCI_full_backup_*.zip` and purges past that |

---

## GO / WATCH / ACTION REQUIRED

| Concern | Status |
|---|---|
| Local backup retention | 🟢 GO · iter427 fix shipped + tested |
| Backup manifest integrity | 🟢 GO · iter425 + iter426 + iter427 all green |
| R2 lifecycle policy (bucket-level) | 🟡 **WATCH** · operator verifies on R2 console |
| Drift watcher continuity | 🟢 GO · iter426 verified |
| Hourly pipeline alive | 🟢 GO · last archive 2026-05-24 (24 min before this audit per /admin/system) |
| Disk reclaim on iter427 cleanup | 🟢 GO · 26 MB + 321 inodes recovered (legacy file purge) |

---

End of Phase 26.1 Backup Retention Verification.
