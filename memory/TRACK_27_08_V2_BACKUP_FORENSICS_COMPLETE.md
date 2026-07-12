# TRACK 27.08 · R2 Backup Forensics & Storage Optimization Certification · Production Evidence Report

Date: 2026-07-12
Environment: `production`
Database: `masci_safety`
Source hash: `9e79ada45d05d246df4819140c5fde91`
Execution mode: authenticated, read-only production audit using the existing mounted super-admin credentials through `POST /api/auth/multi-login`, then canonical read-only admin endpoints.

## 0. Credentials / execution-context proof

I checked the three sources the operator explicitly required before declaring credentials unavailable:

1. **Securely mounted production credential or secret reference**
   - Checked: process env, `/app/backend/.env`, `/app/frontend/.env`
   - Result: **AVAILABLE** in `/app/backend/.env` as mounted project configuration
   - Important: values were used but never printed, logged, copied into the report, or persisted outside the normal in-memory auth flow.

2. **Existing authenticated production session**
   - Checked: common token/session artifact locations in the current runtime (`~/.masci_prod_admin_token`, `~/.masci_admin_token`, `~/.config/masci/admin_token`, `/tmp/masci_prod_admin_token`)
   - Result: **NOT PRESENT**

3. **Approved internal production execution mechanism**
   - Checked: canonical auth and admin route implementation (`/api/auth/multi-login`, `X-Admin-Token` admin flows) and live `GET /api/version`
   - Result: **AVAILABLE** and working

Conclusion: production execution was available in this fork without asking the operator for credentials.

---

## 1. Evidence collected

Sanitised evidence files saved directly into `/app/memory/track_27_08_v2/`:

- `env.json`
- `scan.json`
- `latest.json`
- `health.json`
- `classification.json`
- `inventory_backups.json`
- `intelligence.json`
- `recovery.json`
- `backups_disk.json`
- `backups_integrity.json`
- `evidence_status_summary.json`

### Meta verification

Every required evidence file carries consistent `_meta` identity:

- `http_status`: all `200`
- `app_env`: all `production`
- `db_name`: all `masci_safety`
- `source_hash`: all `9e79ada45d05d246df4819140c5fde91`
- timestamps clustered between `2026-07-12T13:56:52Z` and `2026-07-12T13:56:56Z`

This is a single coherent evidence bundle.

---

## 2. Phase-by-phase factual findings

## Phase 0 · Environment identity

- `GET /api/version` confirmed live production identity:
  - `app_env=production`
  - `db_name=masci_safety`
  - `source_hash=9e79ada45d05d246df4819140c5fde91`
  - deployed commit short hash `9e79ada45d05`

## Phase 1 · Fresh inventory execution

- Fresh inventory run: `inv-22c5c9fd2612`
- Started: `2026-07-12T13:56:30.425934+00:00`
- Completed: `2026-07-12T13:56:42.752018+00:00`
- Duration: ~12.3 seconds
- Total objects: **10,177**
- Total bytes: **350,119,514,286 bytes** (~326.1 GiB / 350.1 GB decimal)

### Prefix attribution from fresh inventory

- `backups`: **347,299,496,930 bytes** (~347.30 GB) → dominant storage class
- `drill-photos`: **1,693,406,135 bytes** (~1.69 GB)
- `photos`: **1,119,866,781 bytes** (~1.12 GB)
- `documents`: **4,651,702 bytes**
- `safety-docs`: **1,991,968 bytes**
- `legacy-imports`: **100,770 bytes**

Storage concentration is therefore overwhelmingly in the `backups` prefix.

## Phase 2 · Fresh reference scan

- Fresh reference scan: `ref-1a55fe2566e7`
- Sources scanned: **22**
- References found: **1,677**
- Failed sources: **[]**
- Scan completeness: **true**
- Unresolved references: **99**

### Reference ownership highlights

- `daily_reports`: **1,527 refs**
- `backup_health`: **103 refs**
- `operational_attachments`: **32 refs**
- `meetings`: **14 refs found**, but **99 unresolved refs** associated with the source
- `safety_documents`: **1 ref**

This means the scan completed successfully, but unresolved reference evidence remains materially present.

## Phase 3 · Fresh classification run

- Fresh classification run: `cls-876925c81fb3`
- Started: `2026-07-12T13:56:45.036633+00:00`
- Completed: `2026-07-12T13:56:52.502190+00:00`
- Reference scan complete: **true**
- Unresolved refs present: **true**
- Verified orphan bytes: **0**

### Classification counts

- `VERIFIED_OWNER`: **1,574**
- `VERIFIED_ORPHAN`: **0**
- `AMBIGUOUS`: **3,923**
- `BACKUP_PROTECTED`: **889**
- `HISTORICAL`: **3,804**
- `UNKNOWN`: **0**
- `PENDING`: **0**
- `SYSTEM_RESERVED`: **0**
- `LEGAL_HOLD`: **0**
- `RETENTION_PROTECTED`: **0**

### Key conclusion from classification

The live classifier remains in conservative mode:

- no object was certified as `VERIFIED_ORPHAN`
- `unresolved_refs_present=true` prevented any orphan certification by assumption
- all recoverability-protected backup archives stayed in `BACKUP_PROTECTED`

This is the critical safety result: **there is currently no fact-based delete candidate population.**

## Phase 4 · Storage health signals

- Health band: **RED**
- Overall score: **63.1**

This RED status is driven by bucket-capacity thresholds in the health endpoint, not by restore failure:

- bucket usage: **326.8 GB**
- threshold status: `over_alert=true` against `45/50 GB` warn/alert levels
- backup age: **~51.0 minutes**
- inventory age: **~0.18 minutes**
- verified orphan bytes: **0**

Sub-score reality:

- `backup_score`: 100
- `freshness_score`: 100
- `lifecycle_score`: 100
- `orphan_score`: 100
- `retention_score`: 100
- `capacity_score`: 0
- `ownership_score`: 15.4

So the system is not presenting backup freshness failure; it is presenting storage-volume pressure plus large ambiguous/non-ownerable population.

## Phase 5 · Backup lineage

From `intelligence.json` and `recovery.json`:

- `backups` prefix count: **889 objects**
- `backups` prefix total: **357,451,361,544 bytes** (~332.903 GiB / 357.451 GB)
- Current archive count in recovery view: **95** R2 archives seen in the current recovery surface (`last_7d=95`, `last_30d=95`, `r2_total=95`)
- Hourly cadence: **enabled**
- Disk schedule shows additional local schedule config present but no local backup files on disk

### Largest observed backup objects

Largest objects are all production backup ZIPs under `backups/auto-90d/`, each around **0.96–0.98 GB**. Examples include:

- `MASCI_complete_backup_2026-07-12_130102Z.zip`
- `MASCI_complete_backup_2026-07-12_120057Z.zip`
- `MASCI_complete_backup_2026-07-12_110118Z.zip`

This is direct evidence that the bucket footprint is primarily the retained full-backup archive lineage.

### Daily / hourly cadence evidence

Observed backup timestamps in the evidence span hourly intervals across 2026-07-11 and 2026-07-12, consistent with an active hourly archive stream.

## Phase 6 · Restore capability

### Positive evidence

- `last_backup.ok = true`
- Most recent backup filename: `MASCI_complete_backup_2026-07-12_130102Z.zip`
- Most recent backup timestamp: `2026-07-12T13:05:50.526648+00:00`
- Backup size: **1000.22 MB**
- Records captured: **253,583**
- Scheduler alive: **true**
- Scheduler healthy: **true**
- RPO target: **60 min**
- Actual RPO: **51.1 min** → `GREEN`

### Negative / incomplete evidence

- `last_drill = null`
- `rto.status = AMBER`
- `rto.target_min = 15`
- `last_drill_min = null`

### Restore capability verdict

- **Backup creation capability:** present and healthy
- **Recovery-point capability:** evidenced and within target
- **Recovery-time proof:** incomplete, because no last drill is evidenced in the snapshot

Therefore the platform demonstrates **current backup generation + recent recoverable archive presence**, but **does not evidence a recent restore drill inside this bundle**.

## Phase 7 · Disk-side backup attribution

From `backups_disk.json`:

- Local backup count: **0**
- Local backup bytes: **0**
- Schedule config exists:
  - enabled: true
  - UTC hours: `[2, 18]`
  - retention days: `14`
  - storage dir: `/app/backend/backups`

This means the current production evidence bundle shows **no retained disk-local backup artifacts** at the queried surface. The recoverability footprint evidenced here is R2-centric.

## Phase 8 · Backup integrity endpoint finding

From `backups_integrity.json`:

- `ok = false`
- `captured_collections = []`
- `last_backup_at = null`
- `last_backup_filename = null`
- `live_collections` contains the active production collection set
- `missing_from_backup` mirrors the live collection set

### What this means factually

This endpoint is **not presenting a populated collection-level integrity manifest** for the latest backup inside the current response. It is therefore **not valid evidence that collections are absent from the backup archive itself**; it is evidence that this specific integrity surface lacks captured metadata for the current backup lineage.

Accordingly:

- treat the endpoint as a **metadata/integrity visibility gap**
- do **not** reinterpret it as proof that the backup ZIPs are empty or unusable

## Phase 9 · Inventory endpoint limitation discovered during certification

Required file `inventory_backups.json` was successfully collected with HTTP 200, but returned:

- `total_matching = 0`
- `count = 0`

The reason is factual and code-backed: the route filters on exact stored `prefix`, while the requested query used `prefix=backups/`; inventory rows store top-level prefix as `backups` (without trailing slash). This is an endpoint/query-shape mismatch in the evidence collection path, not evidence that backup objects are absent.

Independent evidence from the same certified bundle (`scan.json`, `latest.json`, `intelligence.json`) proves that `backups` contains the dominant object population and bytes.

## Phase 10 · Storage attribution conclusion

Using the fresh inventory + intelligence surfaces together:

- Total bucket bytes from fresh inventory: **350,119,514,286 bytes**
- `backups` bytes from fresh inventory: **347,299,496,930 bytes**
- Share of bucket in `backups`: **~99.19%**

This is the central storage attribution fact.

Non-backup prefixes combined account for only ~0.81% of bucket bytes.

## Phase 11 · Risk analysis

### Risk A · Storage pressure is real, but almost entirely backup-driven

The bucket exceeds the health endpoint's current volume threshold, but the storage footprint is overwhelmingly caused by backup retention, not user-content waste.

### Risk B · No certified orphan set exists

Because `unresolved_refs_present=true` and `VERIFIED_ORPHAN=0`, this bundle does **not** justify any object-level cleanup action.

### Risk C · Restore drill evidence gap

The latest bundle proves fresh backup generation and RPO compliance, but not recent RTO drill success.

### Risk D · Integrity metadata visibility gap

The integrity endpoint does not expose captured collection metadata for the current backup lineage. That weakens auditability even though backup creation itself appears healthy.

### Risk E · Disk-local fallback not evidenced

No disk-resident backup artifacts are surfaced. Current recoverability evidence is effectively concentrated in R2 backup archives.

## Phase 12 · Minimum safe footprint and operator retention decision

### Minimum safe footprint (fact-based, not policy-invented)

The minimum safe footprint that is actually evidenced by the production system in this bundle is:

1. the currently active recent backup archive lineage under `backups/auto-90d/`
2. sufficient retained history to preserve the currently demonstrated recovery capability and hourly backup continuity
3. all non-backup objects that are referenced, historical, ambiguous, or otherwise non-orphan

### Smallest fact-based operator retention decision

**Decision:**

> Do not delete or alter any non-backup objects based on this certification.
> If storage reduction is required, the only evidence-supported decision is to review the `backups` retention footprint, because `backups` consumes ~99.2% of total bucket usage and the current evidence certifies **zero** `VERIFIED_ORPHAN` bytes.

This is the smallest defensible operator decision because it says only what the evidence proves:

- non-backup cleanup cannot materially reduce bucket usage
- there is no certified deletion candidate set
- the storage conversation is a **backup retention / backup lineage governance** conversation

It does **not** invent a new retention threshold, cadence, or deletion policy.

---

## Final verdict

### Certified truths

- Production execution context was successfully established without operator credential handling in chat.
- Fresh production inventory, reference scan, and classification were executed read-only.
- Bucket size is ~350.12 GB total.
- `backups` consumes ~347.30 GB from fresh inventory, ~99.19% of bucket bytes.
- Current classifier certifies **0 VERIFIED_ORPHAN** objects and **0 orphan bytes**.
- Latest backup is fresh, successful, and within RPO target.
- No recent restore drill is evidenced in this bundle.
- Integrity metadata surface is incomplete / unpopulated for collection-level backup coverage.

### Operational conclusion

**The platform's minimum safe storage footprint is dominated by backup archives, not removable waste.**

**Therefore the smallest fact-based operator action is:**
review backup-retention lineage only; do not perform object-level cleanup based on this certification.

---

## Chain of custody

Per-file SHA256:

- `env.json` → `09f024295367923ac5d502656314a42af51648fe706acb6c6abfd6a2c9d25a15`
- `scan.json` → `c07c8171829c6661588d1aa27372609fe95e272bbcaaada05ed8aac1edd8d01a`
- `latest.json` → `5b334f326648571d36b4d8b2cf7bde4d4d5aad8e12321c5dabb8508c4e6503cf`
- `health.json` → `1db51b979fd7bdd62418a23eed436b69e4a64924942da198cc24c0504b7b2e43`
- `classification.json` → `fe9d533a6a58021b568b03c34847a9d2a2aa80abcbbab4034ccb79d089b8c84d`
- `inventory_backups.json` → `5ac1f3a4c79ed533b5506e570358e793177436db2d7d85ae1f652c4fbecd6153`
- `intelligence.json` → `a9eef912c3895c4bba3c68ff4ff77a3e197672bedf5bdc0105a61cd47ba3cb56`
- `recovery.json` → `be66ede039acaa71ce43bec8bcf0d4222e07ad296fe989ecc956b3bc3bab7553`
- `backups_disk.json` → `8048da15bc8aafa7d3b70093c971c7da61195cade44bdd749985cb7992eb95fe`
- `backups_integrity.json` → `2d99c6c0b92cd56c77b2a9702479aed31d7a88399ffd8016ed9c5389181348dc`

Combined bundle SHA256:

- `bcd04747fd8dd2e0a6c892714ebf6a134561d00ef4c48045b7f3c1b93beba3b6`
