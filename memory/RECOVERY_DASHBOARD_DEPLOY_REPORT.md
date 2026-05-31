# RECOVERY_DASHBOARD_DEPLOY_REPORT.md

**Batch:** OMEGA · Phase D · iter443 · Recovery Dashboard
**Date:** 2026-05-31 (UTC)
**Spec anchor:** `RECOVERY_DASHBOARD_SPEC.md` (no scope expansion)

---

## 0 · Verdict

🟢 **Recovery Dashboard SHIPPED on preview.** Backend endpoint live and returning compliant snapshot; frontend page wired behind admin auth; lint clean.

---

## 1 · Files added (2) and modified (1)

| File | Lines | Purpose |
|---|---:|---|
| `/app/backend/routes/recovery_dashboard.py` (NEW) | 269 | `build_recovery_dashboard_router(db, require_admin_strict_dep)` → mounts `GET /api/admin/recovery/snapshot` |
| `/app/frontend/src/pages/admin/AdminRecovery.jsx` (NEW) | 313 | Single-screen dashboard polling every 30s; no actions |
| `/app/backend/server.py` (MOD) | +9 | Router mount + comment |
| `/app/frontend/src/App.js` (MOD) | +2 | Import + Route registration |

**Net new code: ~593 LOC.** Spec estimate was ~590 LOC.

---

## 2 · Backend endpoint contract — VERIFIED

**Request:**
```
GET https://<host>/api/admin/recovery/snapshot
Header: X-Admin-Token: <hmac of ADMIN_PASSWORD>
```

**Live response (preview, 2026-05-31T00:00:51Z) — full snapshot received:**
```json
{
  "computed_at": "2026-05-31T00:00:51.420526+00:00",
  "pill": "RED",
  "last_backup": {
    "filename": "MASCI_complete_backup_2026-05-26_100619Z.zip",
    "size_mb": 88.69,
    "records": 249166,
    "ok": true,
    "ts": "2026-05-26T10:09:11.326480+00:00",
    "inlined_photos": 0
  },
  "last_drill": null,
  "backup_age_minutes": 6591.7,
  "backup_age_target_minutes": 1440,
  "rpo": {"target_min": 60, "actual_min": 6591.7, "status": "AMBER"},
  "rto": {"target_min": 15, "last_drill_min": null, "status": "AMBER"},
  "archive_count": {...},
  "bucket_usage": {...},
  "archive_size_trend": [...30 entries],
  "failures_7d": [...],
  "warnings": [...],
  "scheduler": {"alive": false, "last_lock_ts": "...", "owner_pod": "..."},
  "hourly_cadence_enabled": false,
  "cached": false
}
```

**Verdict:** pill=RED in preview is correct — preview's backup scheduler is `SCHEDULER_ENABLED=false` (preview/non-prod), so the last backup is 5 days old. **In production**, the same code with hourly cadence currently disabled but daily 03:00 UTC active would yield pill=GREEN/AMBER depending on cycle timing.

**Auth gate:** `require_admin_strict` (same dependency that gates `/admin/backups/run-complete-now`). PM/HR/Shop tokens correctly rejected.

**Caching:** 15-second in-process TTL — verified by the `cached:false` → `cached:true` flag flip on a second probe within 15 s.

---

## 3 · Frontend page — VERIFIED

**Route:** `/admin/recovery` (registered in `App.js` line 398)
**Auth gate:** `A(<AdminRecovery />)` — same wrapper that gates `/admin/system`. Unauthenticated request → redirect to `/admin/login` (verified by screenshot).
**Layout:** Single screen, 10 cards arranged per spec §2:
- Hero pill (GREEN/AMBER/RED)
- Row 1 (3 cards): Last backup · Last restore drill · Backup age
- Row 2 (3 cards): RPO/RTO · Archive count · Bucket usage
- Trend (1 card): Archive size trend sparkline (last 30 archives)
- Row 4 (2 cards): Failures (last 7 days) · Warnings (active)
- Footer: scheduler + cadence + cached flag

**Polling:** every 30 s (`POLL_MS=30000`).
**data-testid coverage:** 11 testids on every interactive/state-bearing element:
`recovery-pill · recovery-loading · recovery-error · card-last-backup · card-last-drill · card-backup-age · card-rpo-rto · card-archive-count · card-bucket-usage · card-trend · archive-size-trend · card-failures · card-warnings · recovery-footer`

---

## 4 · Compliance against spec §2-7

| Spec section | Compliance |
|---|---|
| §2 IA: 10 cards · single screen | ✅ exact match |
| §3.1 Hero pill logic | ✅ `_compute_pill` pure function (server.py route) |
| §3.2 Last backup card | ✅ all 6 fields rendered |
| §3.3 Last drill card | ✅ all 5 fields rendered (with null-handling for "no drill yet") |
| §3.4 Backup age card | ✅ age + target + GREEN/AMBER/RED color |
| §3.5 RPO/RTO card | ✅ target + actual + status per axis |
| §3.6 Archive count card | ✅ total/7d/30d derived from boto3-fed backup_health rows |
| §3.7 Bucket usage card | ✅ reads `r2-usage-alert/warn` rows |
| §3.8 Sparkline | ✅ inline SVG `<polyline>` · no external dep |
| §3.9 Failures card | ✅ last 7 days `ok=false` rows |
| §3.10 Warnings card | ✅ derived live from bucket-usage + hourly-disabled + scheduler-quiet + photo-coverage-gap env flag |
| §5 single endpoint · 15s cache · admin-strict | ✅ all three |
| §7 NO action buttons | ✅ — only "go to /admin/system" link |
| §8 LOC estimate | spec=590 · actual=593 (+0.5 %) |

---

## 5 · Scope discipline — no expansion

What was **NOT** added beyond the spec:
- ❌ No action buttons (per spec §7)
- ❌ No mobile-optimized layout (per spec §7)
- ❌ No cross-environment view (per spec §7)
- ❌ No notification fan-out from the dashboard (per spec §7)
- ❌ No schema additions — `drill_runs` collection is OPTIONALLY read if it exists (per spec §4.1) but the dashboard works fine without it (renders "No automated drill on file")

---

## 6 · Verification matrix

| Verification | Result |
|---|---|
| Python lint (`ruff` on `routes/recovery_dashboard.py`) | 🟢 All checks passed |
| JS lint (`eslint` on `AdminRecovery.jsx`) | 🟢 No issues found |
| Backend boots cleanly | 🟢 `started_at=2026-05-30T23:59:11.072Z` |
| Endpoint 200 with valid X-Admin-Token | 🟢 HTTP 200 · full snapshot returned |
| Endpoint 401 without X-Admin-Token | 🟢 (verified earlier in this session) |
| Frontend route loads (gated to /admin/login when unauth'd) | 🟢 screenshot confirms |
| Snapshot cache 15s TTL | 🟢 second call returns `cached:true` |
| No new env vars required (uses existing `BACKUP_*` + `R2_USAGE_*`) | 🟢 |

---

## 7 · Stop-condition compliance

- ✅ NO scheduler / cadence / retention / R2 lifecycle / frequency changes
- ✅ NO action endpoints — purely read-only snapshot
- ✅ NO new collections required (drill_runs is optional)
- ✅ Reversible: delete `routes/recovery_dashboard.py` + 2 server.py lines + 2 App.js lines + 1 AdminRecovery.jsx file → identical pre-iter443 platform behavior
- ✅ All data sources are existing collections + env vars

---

## 8 · Operator next action

🟢 **GO** to deploy iter443 to production via the "Deploy to Production" button. Post-deploy verification:
1. `/api/version source_hash` advances from current to the iter443 hash.
2. `https://mascidocs.com/admin/recovery` renders the dashboard once admin-authenticated.
3. Production `pill` should be GREEN/AMBER (recent backup within target window).

— end of report —
