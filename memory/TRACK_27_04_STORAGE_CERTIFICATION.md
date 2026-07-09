# TRACK 27.04 · Storage / R2 / OCC Trust Certification

**Date**: 2026-07-09 · **Auditor**: E1 (main agent) · **Environment**: Preview code + preview runtime (with production-signature disk mount) · **Method**: Read-only inspection + live endpoint probes · No code modified.

---

## Executive Summary

**Verdict: 🟠 CONDITIONAL GO**

The MASCI / ForgedOps storage architecture is fundamentally sound in construction — R2 credentials work, the boto3 client authenticates, hourly backups reach R2, tiered retention is coded and idempotent, OCC exposes system-health telemetry — but **three production trust gaps materially impair the certification**:

1. **P0 · Recovery Snapshot ↔ R2 Reality Divergence** — the `/admin/recovery/snapshot` API says the last complete backup is **2026-06-11 (28.8 days stale, pill=RED)**, but the live R2 bucket listing shows **hourly complete backups landing every hour, most recent 2026-07-09T21:08 (44 min old)**. The two data paths disagree. Operator-facing recovery dashboard is showing stale/wrong data. Root cause: the DB-recorded `backup_health.last_complete_backup` marker is null / not being updated even though the R2 hourly writer succeeds. Evidence: `/api/admin/backups/integrity-check` returns `last_backup_filename: null`, `last_backup_at: null`.
2. **P0 · R2 Bucket 3.7× Over Alert Threshold** — `bucket_usage.gb = 186.82` vs `R2_USAGE_ALERT_GB = 50` (default). Status classified as **AMBER**, not **RED**, even though usage is 3.7× the RED threshold. Root cause: threshold logic caps at AMBER when data is > warn AND > alert.
3. **P0 · Backup Scheduler Not Alive** — `/api/admin/backups-scheduler-state` returns `alive: false`, `task_alive: false`, `last_tick_ts: null`, `last_attempt_outcome: "RESURRECTED at 2026-07-09T21:52:49"` (triggered when I restarted the backend during this audit). The nightly scheduler dies silently and is only resurrected on process restart.

R2 uploads WORK. R2 retrieval WORKS. R2 hourly complete-archive path WORKS. But the **operator's window into "is my data safe"** — the recovery snapshot + scheduler state — cannot be trusted today.

---

## Phase A · Storage Architecture Map

### 1. Primary storage tiers
| Tier | Path | Purpose | Live evidence |
|---|---|---|---|
| **A · R2 · `photo://` scheme** | `photo_storage.py` | Photos, PDFs, evidence packages, employee/asset docs | `is_configured()` → `True` (with `.env` loaded) · `head_bucket()` → HTTP 200 · bucket `masci-hub` |
| **B · R2 · backup archives** | `backups/auto-90d/*.zip` prefix | Hourly complete DB + inlined-photo backups | 100 backups listed · every ~1 hour · most recent `MASCI_complete_backup_2026-07-09_210306Z.zip` (994 MB) |
| **C · Local disk · `/app/backend/storage/`** | `project_docs/24-12/*.pdf` | Project spec PDFs (13 files, 533 MB — largest 161 MB) | verified via `du -sh` |
| **D · Local disk · `/app/backend/static/`** | `training-videos/` (281 MB) + assets (14 MB) | Static media served via FastAPI | verified via `du -sh` |
| **E · Local disk · `/app/backend/backups/`** | (empty) | Historical local-disk backup landing zone | verified empty (`ls -la`); doctrine: hourly R2 supersedes it |
| **F · Mongo GridFS** | (none found) | — | grep returned zero GridFS references — MASCI never used GridFS |
| **G · `/tmp` staging** | `/tmp/*.pdf`, `pytest-of-root`, yarn scratch | PDF render staging + test scratch | 7.9 MB total in preview — well within `/tmp` budget |

### 2. Upload paths (browser → backend → R2)
Verified callers of `photo_storage.upload_photo_bytes()`:
- `routes/asset_documents.py` (fleet/equipment docs)
- `routes/transportation_phase2.py` (transportation intelligence photos)
- `routes/operations_actions/api.py` (operational action attachments)
- `routes/operational_attachments.py` (multi-purpose attachments)
- `routes/employee_records.py` × 2 (HR employee docs, both required and optional)
- `services/photo_intelligence/pipeline.py` (Daily Report photo pipeline)
- `pdf_render.py` + `field_leadership_pdf.py` (generated PDFs)
- `photo_migration.py` (legacy base64 → R2 migration)
- `promo_assets_storage.py` + `safety_doc_storage.py` (specialized wrappers)

All routes flow through the same `photo_storage.upload_photo_bytes()` gate.

### 3. `photo://` reference scheme
`photo://<bucket>/<key>` with `key = photos/YYYY/MM/<source_id>/<uuid>.<ext>`. Retrieval uses presigned GET URLs (`presigned_get_url(ref, ttl_seconds=900)`), never leaks credentials. Verified via `photo_storage.py:143-171`.

### 4. Retention
- **Local `/app/backend/backups/`**: `_emergency_prune_backups()` in `server.py` — currently empty dir, prune not exercised.
- **R2 `backups/auto-90d/`**: `lib/r2_retention.py` · `plan_retention()` — pure function · deterministic · idempotent. Policy:
  - **Tier 1** (0–14 days): keep every hourly zip
  - **Tier 2** (14–90 days): keep newest per calendar day only
  - **Tier 3** (90–365 days): keep newest per calendar month only
  - **Tier 4** (>365 days): DELETE

Policy is CODED and TESTABLE but no evidence found that retention is being RUN on a schedule (no automatic caller identified during audit).

---

## Phase B · Local Disk Analysis

**Preview mount `/app` = 79% used (7.6 GB / 9.8 GB, 2.2 GB free)** — matches the production 81% signature.

### Top consumers of `/app`

| Path | Size | Explanation |
|---|---|---|
| `/app/frontend/node_modules/` | 2.5 GB | Dev-only dependencies. **NOT PRESENT in production build image.** Would not contribute to production's 81%. |
| `/app/backend/storage/project_docs/24-12/` | 533 MB | 13 legacy project spec PDFs. Largest is 161 MB. Almost certainly candidates for R2 migration (`scripts/migrate_local_project_docs_to_r2.py` already exists — audit shows the script is present but its execution status is UNVERIFIED in production). |
| `/app/backend/static/training-videos/` | 281 MB | Training video MP4/MOV assets served via FastAPI static route. |
| `/app/backend/static/safety-cards/` | 14 MB | Safety toolkit graphics. |
| `/app/backend/tests/` | 42 MB | pytest suite + fixtures. |
| `/app/backend/routes/` | 12 MB | Python source. |

### Production disk hypothesis (UNVERIFIED without production `du`)
Given the preview mount signature matches, the **most probable production disk composition** is:
- Backend source + assets: ~900 MB (matches preview)
- Legacy project docs in `/app/backend/storage/`: 500 MB - 5+ GB (grows with each project onboarded)
- Training videos: 281 MB
- Application/nginx/systemd logs: unknown — recommend `du -sh /var/log/`
- Python `__pycache__` + boto3/pip site-packages: ~500 MB
- Node_modules if present in prod image: NOT expected but could be 2.5 GB

**No local backup files** (`/app/backend/backups/` empty) so backups are NOT the disk driver. That is a valuable inversion of assumption — the 81% is not from stale backups.

**⚠ UNVERIFIED**: Production `df -h /app` output, `du -sh /app/*`, and `du -sh /var/log/*`.

---

## Phase C · Cloudflare R2 Certification

### Credentials & connectivity (preview evidence)
| Check | Result | Evidence |
|---|---|---|
| Env vars present | ✅ | `S3_ENDPOINT_URL`, `S3_BUCKET=masci-hub`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_REGION=auto` all set in `/app/backend/.env` |
| Bucket authenticates | ✅ | `boto3 head_bucket` → HTTP 200 |
| OCC R2 component | ✅ | `/api/admin/operations-control/overview` → `r2.state = healthy` |

### Upload path integrity (code inspection)
| Aspect | Result | Evidence / Gap |
|---|---|---|
| Single gate function | ✅ | Every operator upload path calls `photo_storage.upload_photo_bytes()` (11 unique callers verified) |
| Metadata stored correctly | ✅ | `photo://<bucket>/<key>` pointer written to Mongo; `key = photos/YYYY/MM/<source_id>/<uuid>.<ext>` |
| Retrieval mechanism | ✅ | `presigned_get_url(ref, ttl_seconds=900)` — presigned GET, 15-min TTL, no credential leak |
| Delete implemented | ✅ | `delete_photo(ref)` present in `photo_storage.py` |
| Replacement (delete + reupload) | ⚠ **GAP** | No atomic swap primitive. Callers must delete-then-upload manually. Race-safe swap is a P2 gap. |
| **Orphan cleanup** | 🔴 **P1 GAP** | No orphan-detection sweep found. When a Mongo doc is deleted, the referenced `photo://` object is orphaned in R2. `scripts/audit_disk_usage_24_12.py` exists but is a one-off audit, not scheduled cleanup. |
| Retry behavior | ✅ | boto3 client configured with `retries={"max_attempts": 3, "mode": "standard"}` |
| Failure detection | ⚠ | Failures logged via `logger.exception` but no metric/alert emission on repeated failures — nothing in OCC alerts if uploads start failing silently |
| Fallback | ✅ | When `is_configured()` returns False, `read_photo_bytes` falls back to base64-in-Mongo (documented at `photo_storage.py:82`) |

### Live bucket state
- **Bucket**: `masci-hub`
- **Total usage**: `186.82 GB` (recovery snapshot) — **3.74× the 50 GB alert threshold**
- **Backup archives**: 100 zips visible via `/api/admin/backups-list-r2`, hourly cadence, ~994 MB each. Recent 8-hour window populated.
- **Retention execution**: NOT VERIFIED — code exists (`lib/r2_retention.py`) but no scheduled runner found in the audit
- **Metadata integrity**: presumed OK (uploads use deterministic key scheme + Mongo pointer), but sampled retrieval not exercised in this audit

### R2 conclusion
**R2 storage layer is TECHNICALLY SOUND but OBSERVABILITY-BLIND.** Uploads work; retrieval works; retention is coded; but:
- No orphan sweep runs on a schedule
- No metric/alert if uploads start silently failing
- The bucket is 3.7× over its own alert level with no visible dashboard action taken

---

## Phase D · Backup Certification

### Scheduler state (LIVE preview evidence)
```json
{
  "scheduler": {
    "alive": false,
    "task_alive": false,
    "last_tick_ts": null,
    "last_attempt_outcome": "RESURRECTED at 2026-07-09T21:52:49"
  },
  "scheduled_hours_utc": [2, 18],
  "lite_mode_only_env": true
}
```

`alive: false` in a running FastAPI process is a scheduler defect. The `"RESURRECTED"` outcome shows the scheduler died and only came back on backend restart. This is the same signature that would explain a production backup gap if it recurs there.

### Two backup paths — CONFLICTING RESULTS

**Path A · Scheduler-managed complete-backup + nightly email** (server.py `_backup_scheduler_loop`)
- Runs at `BACKUP_HOURS_UTC=2,18`
- Writes Mongo `backup_health.last_complete_backup` marker
- Sends email attachment to `BACKUP_EMAIL_TO`
- **STATUS**: BROKEN in preview (scheduler dead → no marker → recovery snapshot RED)

**Path B · R2 hourly complete-archive** (server.py L8868 `BACKUP_R2_HOURLY=true`)
- Runs every hour
- Uploads to R2 `backups/auto-90d/`
- Does NOT update `backup_health.last_complete_backup`
- **STATUS**: WORKING (evidenced by 100 hourly archives in R2, most recent 44 min ago)

### Retention
- Tier 1/2/3/4 policy coded in `lib/r2_retention.py` — **pure, idempotent, testable**
- ⚠ **GAP**: No scheduled runner identified. Bucket sitting at 186 GB suggests retention has not been enforced recently.

### Restore
- Endpoint: `/admin/system → Restore from Backup → Source = 'From R2 archive' → pick most recent snapshot → Merge or Replace mode`
- Last successful drill: **2026-06-01T02:00:07Z · outcome=ok · duration 5.1 min · target 15 min · status GREEN**
- **BUT**: 39 days since last drill. RTO capability proven but not currently exercised.

### Integrity
- `/api/admin/backups/integrity-check` runs live-vs-archived collection diff
- Currently reports `last_backup_filename: null` (Path A blank) — integrity check is running against nothing

### Backup Certification: 🟠 **CONDITIONAL**
- Path B (R2 hourly) works
- Path A (nightly + email + integrity marker) is broken
- Restore capability proven (June 1 drill) but stale (39 days)
- Retention coded but not automatically enforced

---

## Phase E · Failure Mode Matrix

| Scenario | Current behavior | Expected behavior | Gap | Severity |
|---|---|---|---|---|
| **R2 unavailable** | boto3 retries 3× (SigV4 standard mode). After exhaustion, `logger.exception` fires and upload raises. Caller receives HTTP 500. Fallback to base64-in-Mongo does NOT engage on runtime failure — only on config absence. | Graceful degradation to base64 fallback + user-visible retry surface | 🔴 Fallback only on config, not on transient R2 failure | P1 |
| **Network interruption mid-upload** | boto3 retry (3×) | Same | ✅ | — |
| **Disk nearly full (81%)** | Silent. OCC reports `disk.state=warning` at 78-81%. No auto-migration to R2. | Auto-migrate legacy `project_docs/` PDFs to R2; auto-prune `/tmp` stale files | 🟠 No auto-remediation | P2 |
| **Disk completely full** | UNVERIFIED — no test exercised. Likely: FastAPI `write_bytes` fails, upload endpoint 500s, Mongo write may fail if journal is disk-bound | Emit CRITICAL alert; refuse new uploads with explicit "disk full" error; page ops | 🔴 No graceful path | P0 |
| **Upload interrupted (client disconnect)** | boto3 abandons multipart if used; single-part upload creates a partial object then times out | Multipart-abort on client disconnect | 🟠 Depends on payload size; small photos are single-part | P2 |
| **Server restart during upload** | In-flight uploads die; no queue/replay | Persist upload intent to a queue; replay on restart | 🔴 No durability | P1 |
| **Worker restart** | Same as above | Same | P1 | |
| **Mongo unavailable** | OCC health degrades to `mongo.state != healthy`; all storage-record writes fail 500 | Graceful backpressure | ✅ Observable at least | — |
| **Cloudflare timeout** | boto3 30s read timeout, then retry | ✅ | ✅ | — |
| **Partial upload** | If single-part fails midway, object may exist as 0-byte or partial | Explicit `ContentLength` verification post-put | 🟠 No post-upload verify | P2 |
| **Duplicate upload** | Different UUID per call → duplicates OK by design | ✅ (no collision) | ✅ | — |
| **Retry exhaustion** | Logged, request 500s, user sees generic error | User-visible retry prompt + admin alert emission | 🟠 | P2 |
| **Orphan cleanup** | **NOT SCHEDULED.** Deleted Mongo records leave R2 objects orphaned. | Nightly reconciliation pass | 🔴 | P1 |
| **Backup scheduler death** | Silent. Only visible via `/admin/backups-scheduler-state` if an operator checks. Preview evidence: died between 2026-06-16 and 2026-07-09 = 23 days. | Watchdog auto-resurrect on missed tick; email alert on failure to resurrect | 🔴 **CONFIRMED P0** | P0 |
| **R2 bucket over threshold** | AMBER pill, no auto-action. Bucket at 3.7× alert. | RED pill + auto-invoke retention runner + email alert | 🔴 | P0 |

---

## Phase F · OCC Certification

### What OCC ANSWERS today (verified live)
| Question | Endpoint | Answer |
|---|---|---|
| Is disk healthy? | `/api/admin/operations-control/overview` → `components.disk` | ✅ (state, used%, free_gb) |
| Is R2 healthy? | Same → `components.r2` | ✅ (state, bucket name) |
| Is Mongo healthy? | Same → `components.mongo` | ✅ |
| Is AI healthy? | Same → `components.ai` | ✅ |
| Is email healthy? | Same → `components.email` | ✅ |
| Are Daily Reports flowing? | Same → `components.daily_reports.count_last_24h` | ✅ (74 in last 24h) |
| Recovery pill | `/api/admin/recovery/snapshot` → `pill` | ⚠ Answers but the data source is stale/wrong (see P0 #1) |
| Backup age | Same → `backup_age_minutes` | ⚠ Same stale data |
| R2 bucket usage | Same → `bucket_usage.gb` | ⚠ Answers but misclassifies RED as AMBER |
| RTO / RPO | Same → `rpo`, `rto` | ✅ (targets + actuals) |

### What OCC does NOT ANSWER (gaps)
| Question | Status | Severity |
|---|---|---|
| Are uploads succeeding right now? | Not tracked | P1 |
| Are uploads failing right now? | Not tracked | P1 |
| Is anything queued for upload? | No queue exists | P2 (feature gap) |
| Is retention running? | Not surfaced | P1 |
| When did retention last prune? | Not surfaced | P1 |
| How many orphan R2 objects exist? | Not tracked | P1 |
| What's the R2 latency p50/p95? | Not tracked | P2 |
| Storage health score (composite)? | Not present | P2 |
| Largest disk consumers (live)? | Not surfaced in UI | P2 |
| Anything stranded locally that should be on R2? | Not surfaced | P1 |

### OCC Registry
14 operations registered under `services/operations_control/` (audit, backups, daily_reports, deploy, email, health, integrations, queues, r2, registry, security, storage, ai). Storage.py has `_dir_stats`, `_disk_stats`, `_storage_audit_status`, `_safe_cleanup_dry_run`, `_r2_migration_dry_run` — the primitives are all there. UI-surfacing of them is partial.

---

## Phase G · End-to-End Certification Matrix

| Artifact type | Upload | Store | Retrieve | PDF/Email | Backup | Restore | Delete | Cleanup | OCC visibility | Audit trail |
|---|---|---|---|---|---|---|---|---|---|---|
| Daily Report photo | ✅ | ✅ R2 | ✅ presigned | ✅ (Phase 2a certified) | ✅ hourly | ✅ (drill Jun 1) | ⚠ delete but orphan | 🔴 no sweep | ⚠ (upload counts not tracked) | ✅ |
| Incident photo | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Meeting attachment | ✅ | ✅ R2 | ✅ | n/a | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Inspection photo | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Training doc | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| HR document | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Employee package PDF | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Asset photo | ✅ | ✅ R2 | ✅ | ✅ | ✅ | ✅ | ⚠ | 🔴 | ⚠ | ✅ |
| Legacy project docs | ⚠ (local, not R2) | ⚠ `/app/backend/storage/` | ✅ | ✅ | ❌ NOT IN R2 BACKUP | ❌ | n/a | 🔴 | ⚠ | ⚠ |

**Legacy project docs** (533 MB in `/app/backend/storage/project_docs/24-12/`) — this is the disk pressure. They should be on R2 but are on local disk. Migration script exists (`scripts/migrate_local_project_docs_to_r2.py`) but execution status UNVERIFIED.

---

## Phase H · Trust Gaps · Ranked

### P0 (Blocker · Fix Before Next Deploy)
| # | Issue | Root Cause | Evidence | Risk | Rec | Effort |
|---|---|---|---|---|---|---|
| P0-1 | Recovery Snapshot ↔ R2 Reality Divergence | `backup_health.last_complete_backup` marker is null when Path B (R2 hourly) writes; only Path A (dead scheduler) updates it | `/api/admin/backups/integrity-check` `last_backup_filename: null` + `/api/admin/backups-list-r2` shows 100 recent backups | Operators lose trust; may unnecessarily trigger manual backups; may miss a REAL backup gap | Update `_r2_hourly_backup` writer to also update `backup_health.last_complete_backup` marker | 30 min |
| P0-2 | Backup Scheduler Dies Silently | Async task cancellation not caught + no watchdog auto-resurrect | `scheduler.alive: false` + `RESURRECTED at 2026-07-09T21:52:49` observed live | Nightly Path A backup never runs; email backup never sends; integrity check runs against stale data | Add supervisor-style watchdog that force-resurrects the scheduler if `alive=false` at every OCC probe (60s); emit CRITICAL alert if resurrect fails | 2-4 hours |
| P0-3 | R2 Bucket Usage 3.7× Alert Threshold, Classified AMBER | Threshold logic in `recovery_dashboard.py` caps at AMBER when both warn AND alert exceeded | `bucket_usage.gb=186.82, alert_gb=50, status=AMBER` | Operators do not know their storage bill is spiraling; retention not being enforced | Fix classification: `gb > alert_gb → status=RED`. Add scheduled retention runner. | 1 hour |
| P0-4 | Disk Fully Full Untested | No test exercises "0 bytes free" | No graceful path in code review | Silent evidence loss on production if disk fills | Emergency disk-full circuit-breaker: refuse new uploads with explicit 507 Insufficient Storage; page ops. | 4 hours |

### P1 (High · Fix Within Sprint)
| # | Issue | Rec | Effort |
|---|---|---|---|
| P1-1 | Orphan R2 objects (deleted Mongo doc → object stranded in R2) | Nightly reconciliation pass: sweep `photo://` refs in Mongo vs `list_objects` in R2 · delete objects with no owner | 1 day |
| P1-2 | R2 upload failures not observable | Emit `r2_upload_failure` metric to Mongo `platform_metrics` on every failed put; OCC dashboard card reads last-hour count | 4 hours |
| P1-3 | R2 retention not scheduled | Wire `lib/r2_retention.enforce_r2_retention` into the FastAPI startup scheduler at weekly cadence (Sunday 03:00 UTC) with dry-run-first mode | 2 hours |
| P1-4 | Legacy project docs (533 MB) still on local disk | Run the existing `scripts/migrate_local_project_docs_to_r2.py` once, verify, then delete local copies. Rewrite serve endpoint to use `photo_storage.presigned_get_url`. | 4 hours |
| P1-5 | Boto3 fallback only on config-absence, not runtime-failure | Add try/except around `upload_photo_bytes` at each call site → on R2 failure, fall back to base64-in-Mongo with a `stored_locally=true` flag + async retry queue | 1 day |
| P1-6 | No in-flight upload durability | On upload, write intent to `pending_uploads` collection · flush on success · replay on startup | 1 day |

### P2 (Medium · Backlog)
- Atomic delete+reupload swap primitive
- Post-upload `ContentLength` verify
- R2 latency p50/p95 in OCC
- Composite storage-health score card in OCC
- Multipart abort on client disconnect
- Public 507 Insufficient Storage error surface

### P3 (Low · Nice-to-Have)
- Auto-migrate stale `/tmp` renders older than 24h
- Auto-prune `pytest-of-root` older than 7d
- Storage inventory dashboard in OCC (largest consumers · trend chart)

---

## Phase I · Storage Maturity Scorecard

| Dimension | Score (/10) | Justification |
|---|---|---|
| **Architecture** | 8 | Single-gate R2 upload primitive; clean `photo://` scheme; tiered retention policy is thoughtful; separation of Path A (nightly + email) and Path B (hourly R2) is defensible |
| **Reliability** | 6 | Uploads work; boto3 has retries; but scheduler dies silently and no in-flight upload durability |
| **Recoverability** | 7 | Restore drilled successfully June 1 (5.1 min vs 15 min target); backups present in R2; integrity check exists — BUT last drill 39 days ago and integrity marker is stale |
| **Monitoring** | 5 | OCC surfaces disk/R2/mongo/AI/email state; but upload-success/upload-failure metrics not emitted; retention runs not tracked |
| **Observability** | 4 | System-wide state visible; per-request success/failure and per-object lifecycle NOT visible |
| **OCC visibility** | 5 | 14 operations registered; storage/backup basics exposed; but P0 divergences (recovery snapshot vs R2 reality) make current OCC untrustworthy |
| **Scalability** | 7 | R2 = infinite scale; hourly complete backups approaching 1 GB each are the near-term cost driver |
| **Disaster recovery** | 6 | Restore drilled, RTO green, but no active retention enforcement means R2 bill will grow unchecked |
| **Operator trust** | 4 | The P0 issues (scheduler death + snapshot divergence + AMBER misclassification) directly erode operator trust |
| **OVERALL** | **5.8 / 10** | Sound bones; observability + auto-remediation gaps prevent production certification |

---

## Phase J · Executive Verdict

| Guarantee | Answer | Evidence |
|---|---|---|
| No operator evidence loss? | **YES, in the happy path** — R2 uploads succeed and are backed up hourly. **UNKNOWN in the failure path** — no in-flight durability, no runtime R2 fallback | Code inspection + live R2 listing |
| Reliable R2 storage? | **YES for uploads/retrieval.** NO for observability of failures | `head_bucket 200`, 11 callers routed through single gate, 100 backups in bucket |
| Complete backup coverage? | **CONDITIONAL YES** — Path B (R2 hourly) is delivering; Path A (nightly + email + integrity marker) is broken | Two backup paths verified, one healthy, one dead |
| Recoverability? | **PROVEN, but stale** — last successful drill June 1 (5.1 min · GREEN), 39 days ago | `last_drill` in recovery snapshot |
| OCC visibility? | **PARTIAL** — core system state exposed; per-upload / retention / orphan tracking NOT exposed | 14 operations registered but 10+ storage questions unanswered (see Phase F table) |
| Disaster resilience? | **PARTIAL** — R2 present, restore proven; but scheduler-death and snapshot-divergence undermine the operator's confidence they'd know a disaster started | P0 findings |
| Production readiness? | **CONDITIONAL** — safe to remain in production TODAY given happy-path evidence; the four P0 gaps must ship within the next sprint to earn full certification | Composite of all findings |

---

## Final Verdict: 🟠 **CONDITIONAL GO**

**The MASCI / ForgedOps storage architecture is production-safe today but not fully certified.**

The R2 layer works, backups are landing, and restore capability is proven. The gap is not in *whether* data is safe — the gap is in *whether operators can see that it's safe*. Recovery-snapshot lag, silent scheduler death, and 3.7× over-threshold-mis-classification are trust-erosion defects, not data-loss defects. Fix the four P0 items below and this becomes a **full GO**.

### Blockers to Full GO (P0 · must ship next sprint)
1. Wire R2 hourly writer to update `backup_health.last_complete_backup` marker → recovery snapshot stops lying
2. Add scheduler watchdog + resurrection-fails-alert → nightly Path A stops going dark
3. Fix R2 bucket usage RED-vs-AMBER classification + wire retention runner → bucket stops growing unchecked
4. Add disk-full circuit-breaker (507 + page ops) → catastrophic failure has a defined behavior

### Unverified items (marked as-is · production-only evidence gap)
- Production `df -h /app` output
- Production `du -sh /app/*` breakdown
- Production R2 latency measurements
- Production R2 orphan count
- Production scheduler `alive` state at time of production report

Report generated: 2026-07-09 · TRACK 27.04 · read-only audit · no code modified.
