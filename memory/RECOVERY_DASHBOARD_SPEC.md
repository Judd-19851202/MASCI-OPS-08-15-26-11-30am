# RECOVERY_DASHBOARD_SPEC.md

**Batch:** OMEGA · Operational Perfection Track · Priority 3
**Date:** 2026-05-30 (UTC)
**Mode:** Design specification. **NO implementation in this batch.**
**Audience:** Admin (sole consumer of recovery posture). Read-only surface — no actions; all data sourced from existing collections.

---

## 0 · Goal & constraints

**Goal:** A single Admin-only page that answers in <5 seconds: "Is our recoverability posture green right now, and if not, what's wrong?"

**Constraints (inherited from OMEGA directive):**
- ⛔ No new scheduler cadence
- ⛔ No new retention logic
- ⛔ No new R2 lifecycle changes
- ⛔ No backup frequency changes
- ✅ Read-only · purely a visibility surface
- ✅ All data from collections that already exist (no schema additions)
- ✅ Polls existing endpoints (no SSE / WebSocket)

---

## 1 · Surface

- **Route:** `/admin/recovery` (new top-level Admin Hub tile; gated by `require_admin_strict`).
- **Authorization:** Admin only. PM / HR / Shop / Dispatch / Safety do not see the tile (recovery is an org-level concern owned by Admin).
- **Implementation framework:** React + Shadcn (consistent with `/admin/system`).
- **Polling:** Page polls `/api/admin/recovery/snapshot` every 30 s on the front; backend cached for 15 s to minimize Mongo load.

---

## 2 · Information architecture (one-screen layout)

```
┌────────────────────────────────────────────────────────────────────────┐
│  Recovery Posture   [hero pill: 🟢 GREEN / 🟡 AMBER / 🔴 RED]          │
│                                                                        │
│  ┌── Last backup ───────┐ ┌── Last restore drill ┐ ┌── Backup age ─┐ │
│  │ MASCI_complete...    │ │ Batch G · 2026-05-30 │ │  2h 14m       │ │
│  │ 326.0 MB · 23,911 r  │ │ 283K records · ok    │ │ (target ≤ 24h)│ │
│  │ ok=true · 23:15Z     │ │ photo rehydration ok │ │ status: 🟢    │ │
│  └──────────────────────┘ └──────────────────────┘ └───────────────┘ │
│                                                                        │
│  ┌─ RPO / RTO ─────────┐ ┌── Archive count ─┐ ┌── Bucket usage ──┐  │
│  │ RPO target: ≤ 60 m   │ │ 7 in R2 (90-d)   │ │ 82.0 GB / 100 GB │  │
│  │ RPO actual: 134 m 🟡 │ │ Last 7d: 6        │ │ ALERT ≥ 50 GB 🟡 │  │
│  │ RTO target: ≤ 15 m   │ │ Last 30d: 47     │ │ Lifecycle: 90d   │  │
│  │ RTO drill: 9 m  🟢   │ └──────────────────┘ └──────────────────┘  │
│  └────────────────────────┘                                            │
│                                                                        │
│  Archive size trend (last 30 archives)                                 │
│   ┌─────────────────────────────────────────────────────────────────┐  │
│   │   ▁▂▃▃▄▄▅▅▅▆▆▆▇▇▇█▇█    ▇▅▅▄          ← iter441 -29.9 %         │  │
│   │   ─────────────────────────────────────────────────────────     │  │
│   │   May 25       May 27       May 30 (NOW)                        │  │
│   └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  Failures (last 7 days)                                                │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  ts                    mode             error                       ││
│  │  2026-05-25T15:18Z     complete-r2-err  OperationFailure: …sort…    ││
│  │  2026-05-25T15:16Z     complete-r2-err  OperationFailure: …sort…    ││
│  │  (resolved by iter428 sort removal)                                 ││
│  └────────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  Warnings (active)                                                     │
│  ┌────────────────────────────────────────────────────────────────────┐│
│  │  🟡 R2 bucket usage 82.0 GB above 50 GB ALERT threshold             ││
│  │  🟡 63 photo refs at uncovered JSON paths (iter442 pending)         ││
│  │  🟢 Hourly cadence DISABLED (operator decision)                     ││
│  └────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3 · Card-by-card data contract

Each card maps 1-to-1 with already-existing collections. **No schema additions.**

### 3.1 · Hero pill (overall posture)

| Source | `backup_health` + `backup_drift_history` + computed |
|---|---|
| GREEN if | `last(backup_health).ok=true` AND `now - last(backup_health).ts ≤ 24h` AND no `ok:false` in last 24h AND R2 bucket usage < ALERT |
| AMBER if | last backup older than 24h OR one warning active OR bucket usage ≥ ALERT |
| RED if | last `ok=false` is the most recent backup_health row OR no backup in 72h |
| Code site | new pure function `_compute_recovery_pill(snapshot) -> 'GREEN'|'AMBER'|'RED'` |

### 3.2 · Last backup card

| Field | Source | Example |
|---|---|---|
| filename | `backup_health.filename` (latest `mode:complete-r2` `ok:true`) | `MASCI_complete_backup_2026-05-30_231056Z.zip` |
| size_mb | `size_bytes / (1024*1024)` | 326.0 |
| records | `backup_health.records` | 23,911 |
| ok | `backup_health.ok` | true |
| ts | `backup_health.ts` | `2026-05-30T23:15:25Z` |
| presigned download | `_run_complete_archive_to_r2` already mints; add to snapshot endpoint | (link) |

### 3.3 · Last restore drill card

| Field | Source | Example |
|---|---|---|
| label | document tag (e.g. "Batch G · iter441 drill") | "Batch G · iter441 drill" |
| ts | most recent `drill_runs.ts` (NEW COLLECTION — optional, see §4.1) | 2026-05-30T20:00Z |
| records_restored | from drill report | 283,000 |
| photos_rehydrated | from drill report | 1,517 |
| outcome | ok / failed | ok |

### 3.4 · Backup age card

| Field | Source | Example |
|---|---|---|
| age | `now - last(backup_health).ts` | 2h 14m |
| target | constant `BACKUP_AGE_TARGET_HOURS=24` (operator-tunable env, no scheduler change) | 24h |
| status | 🟢 if age ≤ target; 🟡 if 1-2x target; 🔴 if > 2x target | 🟢 |

### 3.5 · RPO/RTO card

| Field | Source | Notes |
|---|---|---|
| RPO target | env `BACKUP_RPO_TARGET_MINUTES=60` | display only |
| RPO actual | `now - last(backup_health.ts)` (in minutes) | live |
| RTO target | env `BACKUP_RTO_TARGET_MINUTES=15` | display only |
| RTO drill | last `drill_runs.duration_minutes` (or null if no drill on file) | drill-derived |

### 3.6 · Archive count card

| Field | Source |
|---|---|
| R2 archives | live `/api/admin/backups-list-r2` (paginated boto3) — already exists at server.py:6930 |
| Last 7d | filter list by `LastModified >= now-7d` |
| Last 30d | filter list by `LastModified >= now-30d` |

### 3.7 · Bucket usage card

| Field | Source | Notes |
|---|---|---|
| Bucket size (GB) | `backup_health.find({mode: 'r2-usage-alert' OR 'r2-usage-warn'}, sort=-1, limit=1).size_bytes` (already written by `_log_r2_usage_warning` at server.py:5745) | reads existing row, no new probe |
| WARN threshold | env `R2_USAGE_WARN_GB=45` | |
| ALERT threshold | env `R2_USAGE_ALERT_GB=50` | |
| Lifecycle rule | static "90 days on `backups/auto-90d/`" | |

### 3.8 · Archive size trend (sparkline)

| Field | Source |
|---|---|
| Series | `backup_health.find({mode: 'complete-r2', ok:true}, sort=ts).size_bytes[-30:]` |
| Annotation | dotted vertical at iter441 deploy ts (2026-05-30T22:58Z) and label "-29.9 %" |

### 3.9 · Failures (last 7 days) card

| Field | Source |
|---|---|
| Rows | `backup_health.find({ok:false, ts >= now-7d}, sort=-1)` |
| Fields displayed | ts · mode · error (truncated to 120 chars) |
| Empty-state | "No failures in the last 7 days · 🟢" |

### 3.10 · Warnings (active) card

| Source signal | Stored where |
|---|---|
| Bucket usage above ALERT | `backup_health.find({mode: 'r2-usage-alert'}, sort=-1, limit=1)` — auto-clears if newer row falls below |
| Coverage gap (63 photos) | static flag in env `PHOTO_COVERAGE_GAP_OPEN=true` until iter442 ships and operator clears |
| Hourly cadence status | env `BACKUP_R2_HOURLY` (read-only display) |
| Scheduler liveness | `scheduler_locks.find({owner_id starts with 'backup_scheduler_'}, sort=-1)` + age check |

---

## 4 · Optional persistence additions (operator decision — minimal)

The dashboard works **TODAY** by reading existing collections (`backup_health`, `scheduler_locks`, `usage_events` for delivery stats), with two tiny additions worth considering:

### 4.1 · `drill_runs` collection (proposed, ~50 LOC)

| Field | Type | Source |
|---|---|---|
| `id` | UUID4 string | generated |
| `ts` | ISO datetime | `scripts/restore_drill.py` writes one row per run |
| `archive_filename` | str | from drill input |
| `target_db` | str | from drill input |
| `records_restored` | int | from drill validation |
| `photos_rehydrated` | int | from drill `--restore-photos` |
| `outcome` | "ok"/"failed" | drill exit code |
| `duration_minutes` | float | drill wall time |
| `notes` | str | freeform |

**Why optional:** the dashboard can derive "last drill" from the most recent Memory doc whose name matches `*RECOVERY_DRILL*` or `*BATCH_G*`. The collection is cleaner but not strictly required.

### 4.2 · `backup_warnings` collection (proposed, ~30 LOC · operator decision)

Single document `warnings_singleton` with an array of active warnings each having `{id, kind, severity, opened_at, message, dismissed_at?}`. The dashboard reads this; admins can dismiss warnings via a POST. Without this, warnings are derived live from `backup_health` + env vars (works, but admin can't snooze).

---

## 5 · API surface (one new endpoint, all reads)

### 5.1 · `GET /api/admin/recovery/snapshot`

Returns a single JSON document with everything the dashboard needs in one round-trip:

```json
{
  "computed_at": "2026-05-30T23:30:00Z",
  "pill": "GREEN",
  "last_backup": {
    "filename": "MASCI_complete_backup_2026-05-30_231056Z.zip",
    "size_mb": 326.0,
    "records": 23911,
    "ok": true,
    "ts": "2026-05-30T23:15:25Z",
    "presigned_url": "https://...r2.cloudflarestorage.com/..."
  },
  "last_drill": { "ts": "2026-05-30T20:00:00Z", "outcome": "ok", "records": 283000, "duration_min": 9.0 },
  "backup_age_minutes": 14.6,
  "backup_age_target_minutes": 1440,
  "rpo": {"target_min": 60, "actual_min": 14.6, "status": "GREEN"},
  "rto": {"target_min": 15, "last_drill_min": 9.0, "status": "GREEN"},
  "archive_count": {"r2_total": 47, "last_7d": 6, "last_30d": 47},
  "bucket_usage": {"gb": 82.0, "warn_gb": 45, "alert_gb": 50, "status": "AMBER"},
  "archive_size_trend": [{"ts":"...","size_mb":91.0}, ...30 entries],
  "failures_7d": [{"ts":"...","mode":"...","error":"..."}, ...],
  "warnings": [
    {"kind": "bucket-usage", "severity": "amber", "message": "..."},
    {"kind": "photo-coverage-gap", "severity": "amber", "message": "63 refs at materials/subcontractors/signature paths"},
    {"kind": "hourly-disabled", "severity": "info", "message": "BACKUP_R2_HOURLY=false (operator deferred)"}
  ],
  "scheduler": {"alive": true, "last_lock_ts": "2026-05-30T23:06:36Z", "owner_pod": "safety-audit-mobile-1-5596c4696c-mdrrn"}
}
```

| Auth | Caching | Cost |
|---|---|---|
| `require_admin_strict` | 15-second in-memory TTL | <40 ms · ~6 Mongo reads · 1 boto3 list (paginated) |

---

## 6 · Failure modes & how the dashboard surfaces them

| Failure | Dashboard signal |
|---|---|
| Backup builder OOM-killed (no `backup_health` row) | Backup-age clock keeps climbing past target → pill goes AMBER → RED at 2x target |
| `ok=false` row written | "Failures (last 7 days)" card populates immediately · pill goes RED |
| R2 bucket usage crosses ALERT | "Bucket usage" card status → AMBER; warning row appears |
| Scheduler dies (no locks renewed) | "Scheduler" line: `alive=false` · pill goes AMBER |
| Photo coverage gap open | Warning row "63 refs at uncovered paths"; dismissible after iter442 ships |

---

## 7 · Out of scope (explicit)

- ❌ Action buttons to trigger backup, restore, prune — Admin must navigate to `/admin/system` (existing surface)
- ❌ Modifying scheduler / cadence / retention / R2 lifecycle from the dashboard
- ❌ Cross-environment view (preview vs prod) — single environment per dashboard instance
- ❌ Notification fan-out from dashboard alerts — Admin Hub bell remains the notification surface
- ❌ Mobile-optimized layout — desktop only (operator role)

---

## 8 · Build-effort estimate (for future implementation batch · NOT this batch)

| Surface | LOC | Notes |
|---|---:|---|
| Backend `routes/recovery_dashboard.py` (1 endpoint) | ~150 | Read-only, all sources already exist |
| Backend `_compute_recovery_pill` pure function | ~30 | Trivially unit-testable |
| Frontend `src/pages/AdminRecovery.jsx` | ~250 | Shadcn cards + Recharts sparkline |
| Admin Hub tile addition | ~10 | One link card in existing AdminHub.jsx |
| `drill_runs` collection write hook in `restore_drill.py` (optional §4.1) | ~50 | only if operator wants persisted drill log |
| Tests | ~100 | Snapshot endpoint shape + pill logic edge cases |
| **Total** | **~590 LOC** | **single, scoped batch** |

---

## 9 · Stop-condition compliance

- ✅ NO implementation in this batch — pure design spec
- ✅ NO scheduler / retention / R2 lifecycle / cadence / frequency changes proposed
- ✅ Every data point traces to an existing collection or env var
- ✅ Reversible: if implementation later ships and operator dislikes it, delete the route file + frontend page; zero migration debt

---

_End of RECOVERY_DASHBOARD_SPEC.md_
