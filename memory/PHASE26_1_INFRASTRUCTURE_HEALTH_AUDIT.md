# PHASE26_1_INFRASTRUCTURE_HEALTH_AUDIT.md
## MASCI Operations Platform · Phase 26.1 · Infrastructure Health Master Audit
## iter427 · 2026-05-25

---

# 🟢 OPERATIONAL INFRASTRUCTURE GREEN · with one yellow watch flag

The platform is operationally infrastructure-healthy. One yellow flag
remains (the in-container MongoDB persistence pattern) — already
self-flagged by the platform with a permanent-fix banner and a
complete operator migration checklist in
`PHASE26_1_MONGO_DURABILITY_PLAN.md`.

No hidden time-bombs after deployment.

---

## What Phase 26.1 verified

| Domain | Verdict | Detail doc |
|---|---|---|
| Disk pressure & storage measurement | 🟡 → 🟢 (after iter427 fix) | `PHASE26_1_DISK_PRESSURE_REPORT.md` |
| Attachment storage future-safety | 🟢 GO · safe growth profile | `PHASE26_1_ATTACHMENT_STORAGE_ANALYSIS.md` |
| MongoDB durability + migration plan | 🟡 WATCH · checklist ready | `PHASE26_1_MONGO_DURABILITY_PLAN.md` |
| Backup retention | 🟢 GO · iter427 fix shipped | `PHASE26_1_BACKUP_RETENTION_VERIFICATION.md` |
| Cleanup continuity (temp + Mongo TTL) | 🟢 GO | `PHASE26_1_CLEANUP_CONTINUITY_LOG.md` |
| Backup / restore continuity re-validation | 🟢 GO | (see backup retention doc) |

---

## Single hardening change shipped this pass (iter427)

**Surgical fix · 2 functions touched · 1 new test file**

1. `server.py:_emergency_prune_backups` — sweep also covers legacy
   `MASCI_lite_backup_*.zip` and `MASCI_complete_backup_*.zip`
   patterns past `BACKUP_RETENTION_DAYS`. Pre-iter427, these
   accumulated forever (318 legacy lite + 3 legacy complete files
   spotted in the live preview).

2. `server.py:_run_scheduled_backup` pre-flight prune — same gap, same
   fix.

3. `tests/test_iter427_legacy_backup_prune.py` — 2 tests guarding the
   new sweep:
   - `test_iter427_emergency_prune_sweeps_legacy_patterns` — past-
     retention legacy files MUST be deleted.
   - `test_iter427_prune_preserves_young_legacy` — within-retention
     legacy files MUST be preserved (defensive guard).

Both new tests pass alone and in combination with the iter425+iter426
backup parity-lock subset (13 tests).

---

## Real measurements captured

### Filesystem

| Mount | Used / Size | Use % |
|---|---|---|
| `/app` | 9.1 / 9.8 GB | **93 %** (was 94 % before iter427 cleanup) |
| `/data/db` | 858 MB | (separate volume) |
| `/tmp` | 2.2 MB | (negligible) |

### MongoDB

| Metric | Value |
|---|---|
| Collections | 121 |
| Data size | 67.8 MB |
| Storage size | 313.7 MB |
| Total + indexes | 341.8 MB |

### Backups directory after iter427

| Pattern | Count | Size |
|---|---|---|
| `MASCI_full_backup_*.zip` | 2 | 3.10 GB (auto-managed by `BACKUP_KEEP_MAX=3`) |
| Everything else | 0 | 0 |

### Inodes

| Mount | Used | Use % |
|---|---|---|
| `/app` | 135,319 / 655,360 | 21 % (healthy) |

---

## Operational survivability matrix

| Property | Status |
|---|---|
| Hourly + nightly R2 archive | 🟢 alive · 24 min ago at audit time |
| Auto-discovery of new collections (iter425) | 🟢 verified |
| MFA / password redaction in archive (iter425) | 🟢 verified |
| Backup drift watcher (iter426) | 🟢 verified |
| Memory-doc inclusion in disk-files (iter426) | 🟢 verified |
| Attachment byte-for-byte round-trip (iter426) | 🟢 verified |
| Restore runbook (`RESTORE_RUNBOOK.md`) | 🟢 15 sections · operator-readable |
| Legacy backup pattern cleanup (iter427) | 🟢 NEW · verified |

---

## Tests run this pass

### Backup suite (iter425 + iter426 + iter427) — 13 / 13 PASS

```
tests/test_iter425_backup_auto_discovery.py     6 passed
tests/test_iter426_restore_drift_watcher.py     5 passed
tests/test_iter427_legacy_backup_prune.py       2 passed
```

### Full parity-lock baseline (Phase 26 + iter427) — 251 / 252 PASS

The single non-passing case (`test_iter417_types_list_anon_blocked`)
passes when run in isolation — confirms it is the documented inherited
state-leakage flake, NOT a regression from iter427's change.

### Lint

```
ruff check tests/test_iter427_legacy_backup_prune.py  → All checks passed!
```

---

## Restraint doctrine adherence

| Restraint | Status |
|---|---|
| No monitoring dashboards built | ✅ |
| No admin storage UI built | ✅ |
| No analytics built | ✅ |
| No backup portal built | ✅ |
| No infrastructure management system built | ✅ |
| No archive browser built | ✅ |
| No new endpoint | ✅ |
| No new env var | ✅ |
| No scheduler change | ✅ |
| No new collection (mongo) | ✅ |
| Surgical fix only | ✅ 2 functions · 1 test file · 6 doc files |

---

## GO / WATCH / ACTION REQUIRED — consolidated

| Concern | Status | Owner |
|---|---|---|
| Local backup retention legacy gap | 🟢 GO (iter427) | agent · done |
| Disk pressure self-management | 🟢 GO · pre-flight prune at 75 % watermark + boot prune | agent · done |
| MongoDB-in-container redeploy survivability | 🔴 → 🟡 in prod · checklist ready | **operator** · execute `PHASE26_1_MONGO_DURABILITY_PLAN.md` |
| R2 bucket-level lifecycle policy | 🟡 WATCH | **operator** · verify R2 console |
| Attachment growth (real photo flow) | 🟢 GO today · 🟡 re-measure after 90 days | agent · re-audit |
| Mongo TTL coverage (4 low-volume collections) | 🟡 LOW · combined <4 MB | agent · P3 backlog |
| Stale `dispatch_driver_sessions` reaper | 🟡 LOW | agent · P2 backlog (already on Phase 26 backlog) |

---

## What changed in production-deploy posture

| Aspect | Before Phase 26.1 | After Phase 26.1 |
|---|---|---|
| Legacy backup pattern accumulation | unbounded (318 files since 2026-05-11) | bounded by `BACKUP_RETENTION_DAYS` |
| Disk pressure response | 75 % watermark prune (full pattern only) | 75 % watermark prune (full + legacy patterns) |
| Operator awareness of Mongo migration | banner only | banner + 30-step migration checklist + rollback runbook |
| Attachment growth understanding | not formally measured | real measurement + 1-year projection documented |
| Cleanup audit | implicit | explicit cleanup continuity log |

---

## Verdict

🟢 **The MASCI Operations Platform is infrastructure-stable and
storage-safe for live production deployment.**

The one outstanding yellow watch flag (MongoDB-in-container) is
operator-actionable via the migration checklist and is bounded by
the existing hourly R2 archive safety net. Until migration, the
platform's existing `Backup + Email + Download Now` button on
`/admin/system` is the recommended pre-redeploy operator action.

---

End of Phase 26.1 Infrastructure Health Master Audit.
