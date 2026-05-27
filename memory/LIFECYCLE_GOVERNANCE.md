# Lifecycle Governance — iter437 · Phase Sigma-II (DOCUMENTATION ONLY)

**Status:** 📋 RECOMMENDATIONS ONLY — **NO destructive lifecycle action has been taken or scheduled this session.** Every recommendation requires explicit operator approval before any cleanup, TTL, or migration is applied.

---

## 1. Doctrine

The platform's data falls into 6 lifecycle classes. Classification informs retention windows; retention informs storage budget.

| Class                       | Definition                                                                | Retention philosophy |
|-----------------------------|---------------------------------------------------------------------------|----------------------|
| **PERMANENT OPERATIONAL**   | Records that define what the company did and when. Loss = compliance liability + operational forensics gap. | Retain forever in primary storage. Archive copies in R2. |
| **ARCHIVAL**                | Records useful for trend analysis / dispute resolution but not actively consulted. | Retain in primary storage for 1-2 years, then archive to R2 only. |
| **EPHEMERAL**               | Records useful only for the next 24-90 days (caches, polling, sessions). | Aggressive TTL. Lose them without ceremony. |
| **COMPLIANCE-SENSITIVE**    | Records held under regulatory / contractual obligation. | Retention rule is the policy. Document the source. |
| **ATTACHMENT-HEAVY**        | Records whose footprint is dominated by media. | Media → R2; references in primary storage; metadata indexed. |
| **TRANSIENT DIAGNOSTICS**   | System-state snapshots useful while debugging. | TTL aggressively (1-30 days). |

---

## 2. Per-collection classification (current PROD inventory)

### 2a. Permanent operational (retain forever)

| Collection                      | Rationale                                                |
|---------------------------------|----------------------------------------------------------|
| `daily_reports`                 | System of record for site work                            |
| `incidents`                     | Safety/legal record                                       |
| `meetings`                      | Operational decision record                               |
| `inspections`                   | Compliance + safety record                                |
| `jhas`                          | Hazard analysis record                                    |
| `equipment_inspections`         | Equipment safety record                                   |
| `employees`                     | HR record (system of truth)                               |
| `equipment_units`               | Asset registry                                            |
| `jobs_master`                   | Project registry                                          |
| `suppliers`                     | Vendor registry                                           |
| `user_directory`                | Auth source of truth                                      |
| `dispatch_users` / `hr_users` / `safety_users` / `shop_users` / `project_managers` / `field_leadership_users` | Role assignments |
| `safety_documents`              | Policy + procedure records                                |
| `safety_training_records`       | Training compliance                                       |
| `operational_attachments`       | Dispatch attachments (metadata; bytes in R2)              |
| `job_photos`                    | Photo index (metadata; bytes in R2)                       |

**Retention recommendation:** indefinite. Loss = real operational damage.

### 2b. Archival (retain long; consider archive-only after 2y)

| Collection            | Suggested retention |
|-----------------------|---------------------|
| `compliance_findings` | Hot 1y → archive 7y |
| `field_leadership_records` | Hot 1y → archive 5y |
| `transfer_requests`   | Hot 1y → archive 3y |

### 2c. Compliance-sensitive

| Collection           | Policy source                                | Retention |
|----------------------|----------------------------------------------|-----------|
| `admin_audit`        | Access-audit policy                          | 365 days minimum; document the legal basis before pruning |
| `audit_events`       | Compliance trail                             | 365 days minimum |
| `mfa_challenges`     | Auth audit                                   | 90 days · ALREADY TTL'd |

**Recommendation:** add a TTL `expireAfterSeconds = 31536000` (365 days) to `admin_audit` and `audit_events` ONLY after legal/compliance sign-off documents the retention basis.

### 2d. Ephemeral (TTL candidates)

| Collection                  | Current count | Suggested TTL | Reclaim estimate    | Notes                                                            |
|-----------------------------|--------------:|--------------:|--------------------:|------------------------------------------------------------------|
| `usage_events`              |       198 440 |        90 days| ~5 MB now/bounded   | Click-stream telemetry; 90 days is the operationally useful window |
| `health_monitor_runs`       |        11 903 |        14 days| ~0.5 MB             | Polling snapshots; nobody consults > 2 weeks old                  |
| `session_activity`          |               |         7 days|                     | Active sessions are short-lived                                   |
| `directory_sessions`        |               |        30 days|                     | Auth sessions                                                     |
| `training_hits`             |               |        90 days|                     | Training analytics                                                |
| `hub_banner_audit`          |               |        14 days|                     | Banner-view tracking                                              |
| `guidance_search_misses`    |               |        30 days|                     | Search analytics                                                  |
| `cluster_capacity_history`  |             9 |        90 days| bounded ~430 KB     | **ALREADY TTL'd** (iter437)                                       |
| `idempotency_keys`          |             9 |        90 days| (post-iter437 fix)  | **ALREADY TTL'd**; iter437 strip patch makes future rows tiny     |
| `mfa_challenges`            |               |        15 min |                     | **ALREADY TTL'd**                                                 |
| `mfa_remember_devices`      |               |        30 days|                     | **ALREADY TTL'd**                                                 |

**Recommendation:** TTL `usage_events` (90 days) and `health_monitor_runs` (14 days) are the two highest-leverage candidates. Both are pure telemetry with no operational decision impact. Estimated steady-state reclaim: minor today, but prevents unbounded growth.

### 2e. Attachment-heavy

| Collection             | Current avg/doc | Concern                                                  |
|------------------------|----------------:|----------------------------------------------------------|
| `daily_reports`        |    5.5 MB/doc   | ⚠ LEGACY embedded base64 photos (pre-iter288)             |
| `incidents`            |    4.5 MB/doc   | ⚠ Same pattern                                            |
| `job_hazard_files`     |    5.4 MB/doc   | PDFs — likely intentional inline                          |
| `meetings`             |  813 KB/doc     | ⚠ Likely photos                                            |
| `job_photo_thumb_cache`|   22 KB/doc     | Cache — see § 2d (TTL candidate)                          |

**Recommendation (DEFERRED migration):**

A one-pass migration script would:
1. For each pre-iter288 `daily_reports`/`incidents`/`meetings` record with inline base64 `photos`/`gallery`/`attachments` arrays:
2. Extract each base64 blob, upload to R2 with key `photo://masci-hub/photos/legacy/<collection>/<id>/<index>`.
3. Replace the inline base64 with a `photo://...` reference.

**Risks:**
- Touches production rows → risky.
- Must preserve atomicity (one record at a time).
- Must validate every R2 write before mutating the row.
- Reclaim potential: 300+ MB now; multi-GB long-term as new records use R2 from the start.

**Recommendation:** Defer until a dedicated migration session with full backup + rehearsal on preview first. NOT a Phase Sigma-II item.

### 2f. Transient diagnostics

| Collection                | TTL recommendation |
|---------------------------|---------------------|
| `backup_health`           | 30 days             |
| `restore_run_log`         | 90 days             |
| `r2_lifecycle_audit`      | 90 days             |
| `deploy_audit`            | 180 days            |

---

## 3. Suggested action sequence (review-only)

If lifecycle TTLs are approved in a future session, the suggested order minimizes risk:

| Step | Action                                                            | Rollback           |
|------|-------------------------------------------------------------------|--------------------|
| 1    | Add 14-day TTL on `health_monitor_runs.ts` (lowest risk)          | `dropIndex` to undo |
| 2    | Add 90-day TTL on `usage_events.created_at`                       | `dropIndex` to undo |
| 3    | After 7 days of observation: add 90-day TTL on `directory_sessions` | `dropIndex` to undo |
| 4    | Confer with legal/compliance, then 365-day TTL on `admin_audit` / `audit_events` | Requires policy reversal |
| 5    | Migration script for legacy base64 photos (DEDICATED SESSION + full backup + preview-first rehearsal) | R2 objects must survive rollback |

Each step adds a single index. NO data deletion. Mongo's TTL monitor reclaims expired docs in the background — operator can observe slope change in `/api/cluster/capacity/history` and confirm before proceeding.

---

## 4. Explicit non-actions this session

- ❌ No TTL applied.
- ❌ No row deletion.
- ❌ No index dropped.
- ❌ No migration run.
- ❌ No `compact` command issued.
- ✅ Only documentation written.

---

## 5. Lifecycle guardrails to preserve

These are pre-existing patterns the platform already enforces. Do NOT degrade them in future cleanup work:

1. **Backups are independent of primary storage** — R2 hourly retains 90 days regardless of Mongo state.
2. **Photo storage is dual-track** — R2 holds the bytes, Mongo holds the reference. Never delete an R2 object before confirming all references are dropped from Mongo.
3. **`user_directory` is the auth source of truth** — never apply TTL to this collection.
4. **`mfa_*` and session collections** already have appropriate TTLs.

---

## 6. Verdict

**Lifecycle Governance — DOCUMENTED, NOT IMPLEMENTED.**

This artifact is a planning document, not a deployment.

The cluster has 9 GB of headroom at 8.9% utilization — there is no operational urgency. When (and only when) the operator decides to apply any of the recommended TTLs, the rollback path is one `db.collection.dropIndex(name)` call away. Until then, nothing changes.
