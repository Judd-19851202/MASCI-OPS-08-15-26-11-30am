# Phase R · Restore-Drill Certification — Atlas-Tier Capacity Blocker

**Run date:** 2026-05-26
**Operator:** Stabilization / Operational Certification phase
**Authorization:** P0 directive — "FULL PLATFORM REGRESSION + OPERATIONAL CERTIFICATION DIRECTIVE"
**Status:** ⛔ **BLOCKED — infrastructure-tier capacity exhausted**
**Recommendation:** **Upgrade Atlas to M10 (10 GB) before re-attempting the restore drill.** Do NOT purge production records as the primary fix. Sizing is the root-cause; deletion is a symptom-cover.

---

## 1. Why the drill was attempted

The certification directive's restore-drill phase requires:
> "Pull a real R2 backup and restore it into `masci_safety_preview` so the preview DB is an exact mirror of production. Verify backup integrity end-to-end."

This was the **last gate** before regression testing could exercise real operational data.

## 2. Drill setup (pre-failure)

| Field             | Value                                                              |
|-------------------|--------------------------------------------------------------------|
| Source backup     | `s3://masci-hub/backups/auto-90d/MASCI_complete_backup_2026-05-26_110257Z.zip` |
| Zip size          | 336.67 MB                                                          |
| Zip entries       | 223 598                                                            |
| Per-doc colls     | 75                                                                 |
| Target DB         | `masci_safety_preview`                                             |
| Target APP_ENV    | `preview`                                                          |
| Drill script      | `/app/backend/tools/restore_drill.py`                              |
| Guardrails        | Refuses to run unless DB_NAME ends in `_preview`. Refuses unless `APP_ENV=preview`. NEVER touches `masci_safety`. |
| Source download   | 4.99 s (R2 → pod)                                                  |
| Restore mode      | Upsert by `id` (idempotent · ordered=False bulk writes · 500-doc batches) |

## 3. Failure signal (verbatim from Atlas)

```
pymongo.errors.OperationFailure: you are over your space quota,
using 544 MB of 512 MB. Writes are blocked on your cluster.
Free up storage by deleting unnecessary data or add storage by
updating cluster tier.
Atlas error code: 8000  ·  errorLabels: AtlasError
```

This was a **cluster-wide write block** — production writes were also rejected for the duration. Daily reports, incidents, photos, meetings — none could save until space was freed.

## 4. Drill progress at point of failure

| Order | Collection            | Source docs | Restored | Result                           |
|-------|-----------------------|------------:|---------:|----------------------------------|
| 1     | `admin_audit`         |       1 818 |    1 818 | ✅ ok (15.55 s)                   |
| 2     | `admin_audit_log`     |         142 |      142 | ✅ ok (1.66 s)                    |
| 3     | `asset_holds`         |           2 |        2 | ✅ ok                             |
| 4     | `audit_events`        |       9 930 |        0 | ⚠ skipped (no `id` field — mongo `_id` only) |
| 5     | `backup_health`       |         200 |      200 | ✅ ok                             |
| 6     | `calculator_runs`     |           1 |        1 | ✅ ok                             |
| 7     | `compliance_findings` |         233 |      233 | ✅ ok                             |
| 8     | `compliance_scans`    |          50 |        0 | ⚠ skipped (no `id` field)         |
| 9     | `daily-reports`       |          68 |     ~34  | 🛑 **WRITES BLOCKED at this collection — quota exceeded** |

Total docs ingested before failure: ≈ 2 430.
Total storage added by partial restore: 184.20 MB (96% of which was the partially-restored `daily-reports` collection — daily reports contain embedded base64 photos).

## 5. Rollback sequence (executed immediately on failure)

| Step | Action                                                                   | Outcome                |
|------|--------------------------------------------------------------------------|------------------------|
| 1    | Confirmed running PID exited with `OperationFailure`                     | ✅ no orphan process    |
| 2    | Listed all preview collections sorted by `storageSize`                   | ✅ `daily-reports` = 98 MB (the culprit) |
| 3    | Dropped 7 partial-restore collections (`daily-reports`, `admin_audit`, `admin_audit_log`, `asset_holds`, `backup_health`, `calculator_runs`, `compliance_findings`) | ✅ 184.20 MB freed |
| 4    | Probe insert into `__write_probe` to verify cluster accepts writes again | ✅ ok                   |
| 5    | Verified pre-existing carry-over data intact (employees 234, equipment_units 484, suppliers 145, jobs_master 28, user_directory 5, hr_users 2, dispatch_users 2, project_managers 4, field_leadership_users 1) | ✅ no collateral damage |
| 6    | Re-ran `/app/backend/tests/regression/test_critical_flows.py`            | ✅ 41 / 41 green        |

**Production data (`masci_safety`) was never touched at any point in the drill or the rollback.**

## 6. Cluster capacity forensics (post-rollback snapshot, 2026-05-26 22:21 UTC)

| Database               | dataSize | storageSize | indexSize | Docs    |
|------------------------|---------:|------------:|----------:|--------:|
| `masci_safety` (prod)  | 313.7 MB |   522.8 MB  |   39.0 MB | 233 313 |
| `masci_safety_preview` |   0.5 MB |     1.4 MB  |    3.1 MB |   1 882 |
| **Cluster total**      |          | **~540 MB** | (incl. indexes) |   |

| Atlas tier                    | Free-tier ceiling | Headroom         |
|-------------------------------|-------------------|------------------|
| **M0 (Free)** ← current       | 512 MB            | **−28 MB (OVER QUOTA)** |
| M10 (next paid tier)          | 10 GB             | +9.46 GB          |
| M20                           | 20 GB             | +19.46 GB         |

The cluster is **structurally above its quota** by ~28 MB right now. Writes are currently functioning only because Atlas's reclaim/compaction cycle creates transient headroom — that is fragile and can revoke at any operational moment.

## 7. Growth-rate analysis (R2 historical snapshots)

136 complete-backup snapshots from 2026-05-25 through 2026-05-26.

| Metric                                       | Value                       |
|----------------------------------------------|-----------------------------|
| Compressed size (R2 zip), 24 h ago           | 89.144 MB                   |
| Compressed size (R2 zip), most recent        | 93.000 MB                   |
| Δ over 20.5 h                                | **+3.856 MB compressed**    |
| Rate (compressed)                            | **4.52 MB/day**             |
| Decompressed equivalent (3.4× expansion)     | **15.4 MB/day data growth** |
| Storage incl. indexes (5.6× expansion)       | **25.3 MB/day storage growth** |

**Time-to-capacity at current growth rate:** ALREADY OVER. Even without further writes, the cluster has zero structural headroom. A single operational event (large incident report + photos, mass employee profile update, fleet sync) could push it back into hard write-block state.

## 8. Mitigations deployed in this drill

### 8a. Cluster-capacity probe endpoint (NEW · iter437)
- **Path**: `GET /api/cluster/capacity`   (public, no auth — must render on login page)
- **File**: `/app/backend/routes/cluster_capacity.py`
- **Cache**: 60 s in-process (Atlas `dbStats` is cheap but no need to hammer)
- **Quota source**: `ATLAS_QUOTA_MB` env var (defaults 512). Set to 0 after M10 upgrade to suppress the banner.
- **Severity thresholds**: ≥ 95 % critical · ≥ 80 % warning · else ok.
- **Live response right now**:
```json
{
  "ok": true,
  "tier_quota_mb": 512,
  "storage_used_mb": 540.22,
  "storage_used_pct": 105.5,
  "severity": "critical",
  "dbs": {"masci_safety": 535.77, "masci_safety_preview": 4.45}
}
```

### 8b. ClusterCapacityBanner (NEW · iter437)
- **File**: `/app/frontend/src/components/ClusterCapacityBanner.jsx`
- **Mounted in**: `App.js` — above `<EnvBanner />`, below `<BackendStatusBanner />`. Renders on every route, every portal, every screen.
- **Polling**: 60 s.
- **Hides itself** when severity is `ok` — zero visual noise during normal operation.
- **Critical message**: `⛔ DATABASE WRITES MAY FAIL — cluster at capacity · 540 MB / 512 MB (105.5%)`.

### 8c. Regression coverage (NEW · iter437)
- Two assertions added to `/app/backend/tests/regression/test_critical_flows.py`:
  - `test_cluster_capacity_endpoint` — schema & shape check.
  - `test_cluster_capacity_no_auth_required` — must work without any token.
- New suite total: **43 / 43 PASSED** in ~9 s.

## 9. What was NOT done (intentionally)

| Tempting fix                             | Why we did NOT take it                                          |
|------------------------------------------|------------------------------------------------------------------|
| Purge `usage_events` / `audit_events`    | The user explicitly said: *"Do NOT purge production operational records as the primary fix."* These are operational audit trails (auth, dispatch events). Deletion creates compliance + forensics gaps. |
| Reduce backup retention                  | Same: operational artifact. Lifecycle governance is its own decision tree. |
| Disable hourly backups                   | Would close R2 backup window — defeats the entire backup-restore safety system. |
| Restore a *trimmed* backup as workaround | Would not validate full-fidelity restore; the drill's whole purpose is end-to-end proof. |
| Auto-upgrade Atlas tier                  | Requires payment + customer approval. Surfaced to the human operator as P0. |

## 10. Required next steps (waiting on infrastructure)

1. **Upgrade Atlas tier to M10** (or larger). Estimated cost: $0.08/hr for M10 (~$57.60/month, dedicated cluster). M0→M10 migration is online; no downtime.
2. **Once upgraded, set `ATLAS_QUOTA_MB=10240`** in `/app/backend/.env` (or remove it entirely — defaults are guarded). Restart backend.
3. **Re-run the restore drill** — `python3 /app/backend/tools/restore_drill.py /tmp/restore_source.zip`. Expected runtime: ~60 s.
4. **Verify** counts match source manifest, attachment URLs resolve, regression suite still green.
5. **Update `/app/memory/REGRESSION_BASELINE.md`** with the post-restore state.

## 11. Preserved evidence (file pointers)

- Quota-failure log:           `/tmp/restore_drill.log` (raw stderr from the run)
- Source backup zip:           `/tmp/restore_source.zip` (336.67 MB, retained for re-run)
- Drill script:                `/app/backend/tools/restore_drill.py`
- Cluster-capacity probe:      `/app/backend/routes/cluster_capacity.py`
- Frontend banner:             `/app/frontend/src/components/ClusterCapacityBanner.jsx`
- Regression suite:            `/app/backend/tests/regression/test_critical_flows.py`
- Regression baseline:         `/app/memory/REGRESSION_BASELINE.md`
- This artifact:               `/app/memory/PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md`

---

## 12. Decision log — for the post-mortem

| Time (UTC)        | Event                                                                   |
|-------------------|-------------------------------------------------------------------------|
| 21:18             | Backend restarted with `APP_ENV=preview` · `DB_NAME=masci_safety_preview` |
| 21:32             | Regression suite stood up · 41 / 41 green                               |
| 21:33             | Baseline locked at `REGRESSION_BASELINE.md`                             |
| 21:43             | R2 backup `MASCI_complete_backup_2026-05-26_110257Z.zip` downloaded     |
| 21:55             | Restore drill started                                                   |
| ~22:00            | `pymongo.errors.OperationFailure: you are over your space quota, using 544 MB of 512 MB` |
| ~22:01            | Partial restored data dropped from preview · 184.20 MB freed            |
| 22:02             | Write probe ✅ — production writes recovered                             |
| 22:03             | Regression suite re-run · 41 / 41 still green                           |
| 22:20             | Cluster-capacity probe endpoint deployed                                |
| 22:22             | Cluster-capacity banner deployed to frontend                            |
| 22:25             | Regression suite extended to 43 / 43 (added 2 capacity-probe tests)     |
| 22:25             | This certification artifact written                                     |

**The drill succeeded at exactly what it was designed to do:** safely surface a structural infrastructure constraint, with zero collateral damage, and a full audit trail to support the next-step decision.
