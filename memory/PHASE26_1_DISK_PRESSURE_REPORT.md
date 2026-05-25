# PHASE26_1_DISK_PRESSURE_REPORT.md
## MASCI Operations Platform · Phase 26.1 · Real Disk Pressure Measurement
## iter427 · 2026-05-25

---

## Measurement methodology

All numbers below are **real measurements** (`df`, `du`, MongoDB
`collstats`) — no estimation. Captured 2026-05-25 13:42 UTC during
the Phase 26.1 audit.

---

## 1 · Filesystem snapshot

| Mount | Size | Used | Avail | Use % |
|---|---|---|---|---|
| `/` (overlay) | 107 GB | 19 GB | 88 GB | 18% |
| `/app` (preview pod data) | 9.8 GB | 9.1 GB | 715 MB | **93 %** ⚠ |

### Inode usage

| Mount | Inodes | Used | Use % |
|---|---|---|---|
| `/app` | 655,360 | 135,319 | **21 %** (healthy) |

---

## 2 · /app top-level breakdown

| Path | Size | Risk |
|---|---|---|
| `/app/backend/backups` | **3.1 GB** | 🟡 dominant disk consumer |
| `/app/frontend/node_modules` | 1.6 GB | ⚪ stable build dependency |
| `/app/.git` | 1.3 GB | ⚪ stable repo history |
| `/app/backend/storage/project_docs` | 533 MB | ⚪ operational PDFs |
| `/app/backend/static/training-videos` | 281 MB | ⚪ training assets |
| `/app/backend/static/safety-cards` | 14 MB | ⚪ stable |
| `/app/backend/tests` | 15 MB | ⚪ test suite |
| `/app/backend/routes` | 4.0 MB | ⚪ |
| `/app/memory` | 3.8 MB | ⚪ Phase docs |
| `/app/test_reports` | 3.1 MB | ⚪ |
| MongoDB data (`/data/db`) | 858 MB | ⚪ separate volume |

---

## 3 · MongoDB sizing (real)

| Metric | Value |
|---|---|
| Collections | 121 |
| Data size | 67.8 MB |
| Storage size | 313.7 MB |
| Indexes | 341 (28.1 MB) |
| Total size | 341.8 MB |

### Top 10 collections by data size

| Collection | Size | Docs | Has TTL? |
|---|---|---|---|
| `usage_events` | 29.0 MB | 179,739 | ✅ 90 days |
| `job_hazard_files` | 15.2 MB | 7 | n/a |
| `notifications` | 3.6 MB | 5,516 | ✅ per-doc `expires_at` |
| `dispatch_assignments` | 3.2 MB | 2,043 | n/a (operational) |
| `tasks` | 2.7 MB | 3,476 | n/a (operational) |
| `dispatch_state_events` | 2.6 MB | 5,472 | ⚠ none — consider TTL |
| `audit_events` | 2.3 MB | 10,244 | ✅ 30 days |
| `health_monitor_runs` | 1.0 MB | 9,135 | ✅ 30 days |
| `field_leadership_records` | 0.9 MB | 936 | n/a (operational) |
| `compliance_findings` | 0.8 MB | 1,130 | n/a (operational) |

### TTL coverage summary

| Coverage status | Collections |
|---|---|
| ✅ TTL armed | `usage_events`, `notifications`, `session_activity` (30 d), `admin_audit` (365 d), `audit_events`, `r2_degraded_events`, `digest_runs`, `health_monitor_runs`, `system_health_events`, `webauthn_challenges` |
| ⚠ no TTL · low-volume so not urgent | `dispatch_state_events` (5,472 docs), `directory_sessions` (1,748 docs), `operations_events` (1,007 docs), `hub_banner_audit` (1,127 docs) |
| ⚪ N/A — operational permanent record | `dispatch_assignments`, `tasks`, `field_leadership_records`, `compliance_findings`, `equipment_master`, `employees`, `incidents`, `safety_meetings`, `daily_reports`, `jhas`, etc. |

---

## 4 · Backups directory (root-cause analysis)

### Before iter427 cleanup

| Pattern | Count | Total size |
|---|---|---|
| `MASCI_full_backup_*.zip` (iter425+) | 2 | 3.10 GB |
| `MASCI_complete_backup_*.zip` (pre-iter425) | 3 | 512 KB |
| `MASCI_lite_backup_*.zip` (legacy) | 318 | 26 MB |
| `.zip.tmp.*` orphans | 0 | 0 |
| **Total** | **323** | **3.12 GB** |

### After iter427 cleanup

| Pattern | Count | Total size |
|---|---|---|
| `MASCI_full_backup_*.zip` | 2 | 3.10 GB |
| `MASCI_complete_backup_*.zip` | 0 | 0 |
| `MASCI_lite_backup_*.zip` | 0 | 0 |
| `.zip.tmp.*` orphans | 0 | 0 |
| **Total** | **2** | **3.10 GB** |

Freed: ~26 MB · 321 file inodes. Disk pressure: 94 % → 93 %.

### Why two 1.6 GB full backups?

Both created 2026-05-24, 22 minutes apart (`001532Z` + `003635Z`). The
iter425 backfill triggered two successive backups during validation.
Per the configured `BACKUP_KEEP_MAX=3`, keeping both is correct (the
next nightly archive will fit within the 3-archive ceiling).

### Why are full backups 1.6 GB?

The R2 archive includes `/app/backend/storage` (533 MB) and
`/app/backend/static` (300 MB) — those are PDFs / images / videos that
do not compress further. Mongo `dataSize` is only 67.8 MB and
compresses to a few MB. The disk-tree assets dominate.

This is **architecturally correct** — those are operational continuity
files (project docs · training videos · branding) that must round-trip
through the disaster-recovery archive.

---

## 5 · Disk-pressure root cause

| Root cause | Status | Fix shipped |
|---|---|---|
| `_emergency_prune_backups` only globbed `MASCI_full_backup_*.zip`, never touched legacy `lite/complete` patterns | 🟡 → 🟢 | iter427: prune now also sweeps legacy patterns past retention |
| Pre-flight prune in `_run_scheduled_backup` same gap | 🟡 → 🟢 | iter427 same fix in pre-flight block |
| `usage_events` could grow unbounded | 🟢 | 90-day TTL armed at startup |
| `webauthn_challenges` orphans | 🟢 | TTL armed in `passkeys.py` |

---

## 6 · Projected growth

### Backups

| Driver | Daily growth | Monthly | Yearly |
|---|---|---|---|
| Hourly + nightly archives (R2-uploaded, local copy pruned) | ~3 × 1.6 GB = 4.8 GB peak local | bounded by `BACKUP_KEEP_MAX=3` | bounded · steady-state |
| R2 cumulative (24 archives × 30 days × ~1.6 GB) | — | ~1.1 TB | TODO Phase 26.2 — verify R2 lifecycle policy at object-level |

### Storage tree

| Path | Today | Monthly growth estimate | Action |
|---|---|---|---|
| `/app/backend/storage/project_docs` | 533 MB | +50 MB/mo (typical PDF additions) | safe |
| `/app/backend/static/training-videos` | 281 MB | rare additions only | safe |
| `/app/backend/static/safety-cards` | 14 MB | minimal | safe |

### MongoDB

| Driver | Current | Monthly growth |
|---|---|---|
| `usage_events` (90-day TTL) | 29 MB | stable (steady-state ≈ 90 d window) |
| `dispatch_assignments` | 3.2 MB | ~0.5 MB/mo (operational growth) |
| `operational_attachments` (real photos) | 0.02 MB (test data) | **see PHASE26_1_ATTACHMENT_STORAGE_ANALYSIS** |

---

## 7 · GO / WATCH / ACTION REQUIRED status

| Concern | Status |
|---|---|
| `/app` disk at 93 % | 🟡 **WATCH** · prune logic now handles legacy patterns going forward · automatic prune armed at 75 % watermark and on boot |
| Mongo size | 🟢 GO · 67.8 MB / 313.7 MB storage · ample headroom |
| Backup retention coverage | 🟢 GO · iter427 surgical fix shipped |
| Inode pressure | 🟢 GO · 21 % use |
| /tmp growth | 🟢 GO · 2.2 MB only |
| MongoDB-in-container redeploy risk | 🟡 **ACTION REQUIRED** · see `PHASE26_1_MONGO_DURABILITY_PLAN.md` (Atlas migration recommended) |

---

## 8 · Permanent recommended next step

Migrate production MongoDB to **MongoDB Atlas free tier** — eliminates
the container-DB-destroyed-on-redeploy class of risk and the disk
pressure pattern of growing local archives. See
`PHASE26_1_MONGO_DURABILITY_PLAN.md`.

---

End of Phase 26.1 Disk Pressure Report.
