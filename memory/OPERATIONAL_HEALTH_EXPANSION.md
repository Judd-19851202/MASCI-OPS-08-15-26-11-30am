# Operational Health Expansion — Certification

**Phase:** SIGMA-III · P1
**Iteration:** iter437
**Status:** 🟢 EXISTING SURFACES INVENTORIED · NO NEW COLLECTION REQUIRED

---

## Why this exists

The directive was: "Operational Health Expansion (lightweight drift/
failure tracking)". The honest answer after inventorying the platform
is that **the drift tracking already exists** across four independent
surfaces. This document certifies that what's there is sufficient and
lists the lightweight expansion that DID land in Sigma-III.

---

## What was already shipped (pre-Sigma-III)

### 1. Backup drift tracking — `backup_drift_history`
- **Writer:** `server.py:_backup_drift_watch` (last 30 runs · capped collection)
- **Reader:** `routes/admin_persistence_health.py` — surfaces
  `drift_watch_active`, `drift_watch_reason`, `last_backup_time`,
  `r2_backup_success`.
- **Coverage:** backup size/record count drift, last-success heartbeat,
  R2 quota probe.

### 2. Cluster storage drift — `cluster_capacity_history`
- **Writer:** server.py hourly snapshot loop (iter437 Phase Sigma-II)
- **Reader:** `routes/cluster_capacity.py::cluster_capacity_history`
  + the new `/admin/database` panel (Sigma-III P1).
- **Coverage:** hourly storage usage · 90-day TTL · two-point linear
  slope · `days_to_quota` projection.

### 3. Service health rollup — `admin/system-health`
- **Writer:** `routes/admin_ops.py` (computed live, no persistence)
- **Reader:** `/admin/system-health` UI (`SystemHealth.jsx`)
- **Coverage:** backups · drift · scheduler · external providers
  (R2, Resend, Sentry) · DB connectivity.

### 4. Production health probe (cross-environment)
- **Writer:** `tools/verify-production.sh` (operator-run + GitHub
  Actions cron every 15 min via `production-health-probe.yml`)
- **Reader:** GitHub workflow failure email → operator
- **Coverage:** 5 critical hub routes against `mascidocs.com`.

### 5. Audit + denial logs — `admin_audit`, `access_denials`, `audit_events`
- Already capture access denials, admin mutations, portal logins,
  impersonation events, MFA enrollment/disablement.

---

## What Sigma-III added (lightweight expansion)

### A. Storage runway visualization
- New `/admin/database` panel with inline-SVG sparkline + runway line.
- Surfaces drift in human terms (`+5.5 MB/day · ~1696d runway`)
  instead of forcing the operator to grep MongoDB.
- File: `frontend/src/pages/admin/AdminDatabase.jsx`,
  `frontend/src/components/admin/StorageObservabilityCard.jsx`.

### B. Deployment-gate failure tracking
- `pre_deploy_check.sh` now logs PASS/FAIL per stage in a fixed format.
- Operator can grep the script output to see WHICH gate blocked a
  deploy (no separate logging surface needed — the script's stdout
  IS the failure record).

### C. Magic-link denial audit trail (carry-over from P0)
- The new `DriverIneligibleError` raised in `driver_sessions.py`
  surfaces structured error codes (`driver_not_found`,
  `driver_disabled`, `driver_inactive`). The dispatch UI logs these
  via the existing `access_denials` collection automatically (no new
  code needed — `record_access_denial` is invoked from the route's
  exception path via FastAPI middleware).

---

## Gaps deliberately NOT filled

| Gap                                          | Rationale for not filling                                       |
|----------------------------------------------|------------------------------------------------------------------|
| Per-route P99 latency tracking               | Sentry + the existing performance audit (`PHASE31_4_PERFORMANCE_AUDIT.md`) already cover this. Adding our own metric pipeline = unjustified complexity. |
| Mongo slow-query log surface                 | Atlas Performance Advisor already provides this; no value in reimplementing. |
| Failure-rate dashboard                       | Doctrine forbids new dashboards. The `system-health` page is the operator's single pane. |
| Real-time push alerts to operator's phone    | Out of scope — covered by `ATLAS_ALERTS_RUNBOOK.md` (email + SMS via Atlas). |

---

## Operator validation (≤ 1 minute)

```bash
# 1. Confirm all 4 drift surfaces respond
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
ADMIN=$(curl -s -X POST "$URL/api/auth/multi-login" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg e "$SUPER_ADMIN_EMAIL" --arg p "$SUPER_ADMIN_BOOTSTRAP_PASSWORD" '{email:$e,password:$p}')" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['portal_tokens']['admin'])")

curl -fsS "$URL/api/cluster/capacity" | python3 -m json.tool
curl -fsS "$URL/api/cluster/capacity/history?days=7" | python3 -c "import sys,json;d=json.load(sys.stdin);print('samples=',d['samples'],'slope=',d['slope_mb_per_day'])"
curl -fsS -H "X-Admin-Token: $ADMIN" "$URL/api/admin/system-health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('overall=',d['overall'])"
curl -fsS -H "X-Admin-Token: $ADMIN" "$URL/api/admin-strict/diag/persistence-health" | python3 -c "import sys,json;d=json.load(sys.stdin);print('drift_active=',d.get('drift_watch_active'),'last_backup=',d.get('last_backup_time'))"
```

Each line should return parsable JSON with the indicated field non-null.

---

## Verdict

🟢 **Operational Health Expansion — RESOLVED VIA INVENTORY + LIGHTWEIGHT WIDGET.**

No new collection. No new dashboard. No new monitoring center. The
storage-runway widget at `/admin/database` is the only NEW surface
added in this iteration; everything else uses existing drift-tracking
infrastructure.

# 🟢 P1 — Operational Health Expansion · CLOSED
