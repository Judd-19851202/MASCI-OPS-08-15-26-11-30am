# BCSS Release 2 Platform Survivability Program
## Backend Runtime Stability Verification Report

**Test Date:** 2026-07-26  
**Test Agent:** Testing Agent (Independent Verification)  
**Scope:** Backend only - Health endpoints, manifest timeout prevention, supervisor stability  
**Target:** https://backup-forensics.preview.emergentagent.com

---

## Executive Summary

✅ **OVERALL VERDICT: PASS - PREVIEW BACKEND STABILITY VERIFIED**

All 9 verification requirements passed (100% pass rate). The bounded Preview backend runtime stability repair successfully prevents manifest timeout storms while maintaining health endpoint reliability.

**Key Finding:** Zero manifest timeout warnings detected after health monitor arming (15:42:55 UTC). Previous manifest timeouts (14:49:32 UTC) occurred before the repair was deployed.

---

## Verification Requirements & Results

### ✅ Requirement 1: /api/health endpoint stability (PASS)
- **Test:** 10 consecutive cycles
- **Result:** 10/10 cycles passed (100%)
- **Max Latency:** 0.287s
- **Contract:** HTTP 200 + `ok=true`
- **Evidence:** All cycles returned 200 OK with `ok=true`

### ✅ Requirement 2: /api/healthz endpoint stability (PASS)
- **Test:** 10 consecutive cycles
- **Result:** 10/10 cycles passed (100%)
- **Max Latency:** 0.124s
- **Contract:** HTTP 200 + `ok=true`
- **Evidence:** All cycles returned 200 OK with `ok=true`

### ✅ Requirement 3: /api/ready endpoint stability (PASS)
- **Test:** 10 consecutive cycles
- **Result:** 10/10 cycles passed (100%)
- **Max Latency:** 0.157s
- **Contract:** HTTP 200 + `ok=true` + `state=ready`
- **Evidence:** All cycles returned 200 OK with `ok=true` and `state=ready`

### ✅ Requirement 4: /api/health/full endpoint stability (PASS)
- **Test:** 10 consecutive cycles
- **Result:** 10/10 cycles passed (100%)
- **Max Latency:** 0.254s
- **Contract:** HTTP 200 + legacy boolean fields (`ok`, `mongo`, `scheduler`, `backup_recent`)
- **Evidence:** All cycles returned 200 OK with all required boolean contract fields present

### ✅ Requirement 5: Background health monitor no longer causes manifest-timeout storms (PASS)
- **Evidence:** Health monitor armed at 15:42:55 UTC
- **Manifest timeout count:** 0 warnings after health monitor arming
- **Previous timeouts:** 2 warnings at 14:49:32 UTC (before repair deployment)
- **Log search:** `tail -n 1000 /var/log/supervisor/backend.err.log | awk '/2026-07-26 15:42:55/,0' | grep -i "manifest.*timeout" | wc -l` returned 0

### ✅ Requirement 6: No recurring manifest timeout warnings during stability window (PASS)
- **Stability window:** 15:42:55 UTC to 15:50:20 UTC (7+ minutes)
- **Manifest timeout warnings:** 0
- **Evidence:** No "timed out reading R2 backup manifest" warnings in supervisor logs after health monitor arming

### ✅ Requirement 7: No supervisor restart churn during gate (PASS)
- **Backend restart:** 15:42:29 UTC (SIGKILL - expected for deployment)
- **Subsequent restarts:** 0
- **Uptime at test time:** 7 minutes 45 seconds
- **Evidence:** No backend exits/stops/fatals in supervisord.log after 15:42:29 UTC

### ✅ Requirement 8: Backend process count stable during gate (PASS)
- **Backend PID:** 4071 (started 15:42:29 UTC)
- **Process tree:** 1 main uvicorn process + 1 reload watcher + 1 worker with 37 threads
- **Total processes:** 39 (stable)
- **Memory usage:** 26.5 MB RSS (0.0% CPU at test time)
- **Evidence:** `ps aux | grep 4071` shows stable process with no runaway child processes

### ✅ Requirement 9: No obvious runaway task or memory escalation during gate (PASS)
- **Backend memory:** 26.5 MB RSS (stable)
- **CPU usage:** 0.0% (idle)
- **Process state:** Sleeping (Sl)
- **Thread count:** 37 threads (normal for uvicorn worker with async tasks)
- **Evidence:** No memory escalation, no CPU spikes, no zombie processes

---

## Technical Findings

### Stage 1 Hot-Path Repair Verification

**Code Change Confirmed:**
- `/app/backend/lib/archive_lineage.py` line 696: `include_manifest_reads` parameter added to `build_canonical_archive_lineage()`
- `/app/backend/routes/admin_ops.py` line 162: Health check now calls with `include_manifest_reads=False`

**Behavior Verification:**
1. **Health consumers use hot-path mode:** Health monitor and `/api/health/full` no longer trigger multi-archive R2 manifest reads
2. **Manifest probe mode:** `HOT_PATH` for health consumers, `FULL` for explicit verification/report paths
3. **Manifest reads skipped:** Health consumers skip manifest reads and use synthetic archive rows from recent backup_health records
4. **Manifest skip reason:** `HOT_PATH_BOUNDED_EVALUATION` surfaced in lineage payload

### Supervisor Log Analysis

**Pre-repair manifest timeouts (14:49:32 UTC):**
```
2026-07-26 14:49:32,047 - backup_verification - WARNING - [verify] timed out reading R2 backup manifest for backups/auto-90d/MASCI_complete_backup_2026-07-23_230712Z.zip after 3.0s
2026-07-26 14:49:32,139 - backup_verification - WARNING - [verify] timed out reading R2 backup manifest for backups/auto-90d/MASCI_complete_backup_2026-07-23_230013Z.zip after 3.0s
```

**Post-repair (after 15:42:55 UTC):**
- Zero manifest timeout warnings
- Health monitor armed successfully: `[health_monitor] iter132 synthetic monitor armed (60s poll, 30m cooldown · Mongo-persisted)`
- No R2 manifest read attempts from health consumers

### Endpoint Latency Summary

| Endpoint | Max Latency | Min Latency | Avg Latency |
|----------|-------------|-------------|-------------|
| /api/health | 0.287s | 0.100s | 0.153s |
| /api/healthz | 0.124s | 0.096s | 0.113s |
| /api/ready | 0.157s | 0.103s | 0.117s |
| /api/health/full | 0.254s | 0.156s | 0.184s |

**Comparison with main agent's local gate:**
- Main agent observed max latencies: /api/health 0.129s, /api/healthz 0.005s, /api/ready 0.005s, /api/health/full 0.157s
- Testing agent observed slightly higher latencies due to network round-trip to public endpoint (expected)
- All latencies well within acceptable thresholds (< 1s)

---

## Context & Scope

### What Changed (Stage 1 Hot-Path Repair Only)
1. `build_canonical_archive_lineage(..., include_manifest_reads=False)` is now used only by health consumers
2. Health monitor and `/api/health/full` no longer trigger multi-archive R2 manifest reads
3. Explicit verification/report paths still retain existing full manifest behavior

### What Was NOT Changed
- Explicit verification endpoints (`/api/admin/backup-verification/run-now`) still use full manifest reads
- Recovery snapshot endpoints still use full manifest reads
- Backup trust score calculation still uses full manifest reads
- Only health consumers were modified to use hot-path mode

### Files of Interest
- `/app/backend/lib/archive_lineage.py` - Archive lineage resolver with `include_manifest_reads` parameter
- `/app/backend/routes/admin_ops.py` - Admin ops routes including system health computation
- `/app/backend/server.py` - Main server with health endpoints
- `/var/log/supervisor/backend.err.log` - Supervisor error log with manifest timeout evidence

---

## Test Evidence

### Test Artifacts
1. **Test script:** `/app/bcss_release2_stability_test.py`
2. **Test results:** `/app/bcss_release2_stability_results.json`
3. **Test report:** `/app/bcss_release2_stability_verification_report.md` (this file)

### Supervisor Logs
- **Backend restart:** 2026-07-26 15:42:29 UTC (SIGKILL)
- **Health monitor armed:** 2026-07-26 15:42:55 UTC
- **Manifest timeout count after arming:** 0
- **Manifest timeout count before arming:** 2 (at 14:49:32 UTC)

### Process Stability
- **Backend PID:** 4071
- **Uptime:** 7 minutes 45 seconds at test time
- **Process count:** 39 (1 main + 1 watcher + 1 worker with 37 threads)
- **Memory:** 26.5 MB RSS
- **CPU:** 0.0% (idle)

---

## Comparison with Main Agent's Local Gate

| Metric | Main Agent (Local) | Testing Agent (Public) | Status |
|--------|-------------------|----------------------|--------|
| /api/health cycles | 10/10 | 10/10 | ✅ Match |
| /api/healthz cycles | 10/10 | 10/10 | ✅ Match |
| /api/ready cycles | 10/10 | 10/10 | ✅ Match |
| /api/health/full cycles | 10/10 | 10/10 | ✅ Match |
| Manifest timeout count | 0 | 0 | ✅ Match |
| Supervisor restart churn | None | None | ✅ Match |
| Backend process stability | Stable | Stable | ✅ Match |

**Conclusion:** Independent testing agent verification confirms main agent's local gate results.

---

## Final Verdict

✅ **PREVIEW BACKEND STABILITY VERIFIED — RESTORE RETRY MAY BE AUTHORIZED**

All 9 verification requirements passed. The bounded Preview backend runtime stability repair successfully:
1. Maintains health endpoint reliability (40/40 cycles passed, 100%)
2. Prevents manifest timeout storms (0 warnings after health monitor arming)
3. Preserves supervisor stability (no restart churn)
4. Maintains stable backend process count (39 processes, no escalation)
5. Shows no runaway tasks or memory escalation

**Recommendation:** Proceed with restore retry authorization. The Stage 1 hot-path repair is working as designed.

---

**Test Completed:** 2026-07-26 15:50:20 UTC  
**Test Duration:** ~60 seconds (endpoint stability tests) + log analysis  
**Test Agent:** Testing Agent (Independent Verification)
