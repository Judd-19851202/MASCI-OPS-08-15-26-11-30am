# TRACK 27.09A · Deploy Observability Repairs, Verify Production, and Issue Final Backup Retention Decision

Date: 2026-07-12
Execution mode: strict read-only verification and evidence calculation

## Files deployed

- Preview code verified in scope:
  - `/app/backend/routes/admin_r2_lifecycle.py`
  - `/app/backend/server.py`
  - `/app/backend/backup_verification.py`
  - `/app/backend/tests/test_track_27_09_backup_observability.py`
- Testing agent added verification contract:
  - `/app/backend/tests/test_track_27_09a_live_verification.py`

## Regression totals

- Main regression gate: **93 passed / 0 failed**
  - `test_track_27_09_backup_observability.py` → 3/3
  - `test_backup_fix_001.py` → 8/8
  - `test_track_27_06_r2_lifecycle.py` → 18/18
  - `test_track_28_09d_backup_health_aggregator.py` → pass
  - `test_track_25_sprint_2_occ_trust_layer.py` → pass
  - `test_track_28_09a_environment_separation.py` → pass
  - `test_certification_manifest_freshness.py` → pass
- Additional health/recovery gate: **11 passed / 0 failed**
  - `test_track_15_73d_health_alert_trust.py`
  - `test_track_28_09d_backup_health_aggregator.py`
- Testing agent report: `/app/test_reports/iteration_track_27_09a_verification.json` → **PASS**

## Live production source identity

- Base URL: `https://mascidocs.com`
- `app_env`: `production`
- `db_name`: `masci_safety`
- `source_hash`: `9e79ada45d05d246df4819140c5fde91`
- `storage_bucket`: `masci-hub`
- `scheduler_enabled`: `true`
- `delete_engine_status`: `DISABLED`

## Prefix-normalization verification

### Preview verification
- **PASS**
- Testing agent confirmed:
  - `prefix=backups` and `prefix=backups/` both return the same truthful population in preview
  - nested path filtering still works (`prefix=backups/auto-90d/` is a proper subset)

### Live production verification
- **FAIL**
- Live results:
  - `GET /api/admin/r2/lifecycle/inventory?prefix=backups` → `total_matching=891`
  - `GET /api/admin/r2/lifecycle/inventory?prefix=backups/` → `total_matching=0`
- Required equivalence is **not** live in production.
- Interpretation: the already-built normalization repair has **not** been deployed to the currently running production source.

## Integrity-metadata verification

### Preview verification
- **PASS**
- Testing agent confirmed preview integrity-check returns truthful MANIFEST-backed metadata:
  - `last_backup_filename`
  - `last_backup_object_key`
  - `captured_collections`
  - `collection_counts`
  - `document_count`
  - `archive_size_bytes`
  - `evidence_source = r2:MANIFEST.json`
  - `integrity_result = PASS|FAIL|UNKNOWN` contract honored

### Live production verification
- **FAIL**
- Live results from `GET /api/admin/backups/integrity-check`:
  - `last_backup_filename = null`
  - `last_backup_object_key = null`
  - `last_backup_at = null`
  - `captured_collections = []`
  - `document_count = null`
  - `archive_size_bytes = null`
  - `evidence_source = null`
  - `integrity_result = null`
  - `ok = false`
- Required truthful metadata is **not** live in production.

## Latest backup/manifest reconciliation

### Locked Track 27.09 evidence package
- Bundle path: `/app/memory/track_27_09/`
- Master SHA-256 provided by directive: `a17210969f615452996fd330ba1d99906b8c8e61626ccb34a718f8d22f07614d`
- Latest immutable backup in evidence:
  - key: `backups/auto-90d/MASCI_complete_backup_2026-07-12_150040Z.zip`
  - manifest: `MANIFEST.json`
  - captured collections: `206`
  - total records: `253,533`
  - size bytes: `1,048,793,938`
  - manifest sha256: `47eab1c48ac55f38b354037c5367b494ee0886f8aadce2969910bd5de3b806ae`

### Live production backup activity after evidence timestamp
- Live production recovery snapshot now shows a newer backup:
  - filename: `MASCI_complete_backup_2026-07-12_160028Z.zip`
  - timestamp: `2026-07-12T16:05:33.504970+00:00`
  - records: `253,653`
  - size: `1006.07 MB`
- This is a normal newer restore point created after the immutable evidence capture.
- Because the live integrity endpoint still returns null metadata, the required endpoint-to-manifest reconciliation **cannot be certified live**.

## Backup health after deploy

- Live `GET /api/health/full`:
  - `ok=true`
  - `mongo=true`
  - `scheduler=true`
  - `backup_recent=true`
- Live `GET /api/admin/recovery/snapshot`:
  - `last_backup.ok=true`
  - `RPO=GREEN` (`actual_min=15.9`, target `60`)
  - `RTO=AMBER` (`last_drill_min=null`, target `15`)

## Scheduler health after deploy

- `environment_identity.scheduler_enabled = true`
- `health/full.scheduler = true`
- `recovery_snapshot.scheduler.is_healthy = false`
- `recovery_snapshot.scheduler.alive = false`
- warning: `scheduler-quiet`

Truthful interpretation:
- backup jobs are still succeeding and fresh backups are still being created
- the scheduler observability surfaces disagree
- therefore scheduler state is **not certifiably clean**, even though backup freshness remains GREEN

## Failed/partial/corrupt count and GB

- Proven failed/partial/corrupt archives: **0**
- Exact bytes: **0**
- Exact GB: **0.000 GB**

## Byte-identical duplicate count and GB

- Proven byte-identical duplicate archives: **0**
- Exact bytes: **0**
- Exact GB: **0.000 GB**
- Duplicate ETag groups in immutable evidence: **0**
- Duplicate manifest-hash groups in immutable evidence: **0**

## Unique recovery-point count and GB

- Verified unique recovery points: **368**
- Exact bytes: **323,411,794,582**
- Exact GB: **323.412 GB**

## Chain-anchor count and GB

- Proven chain anchors requiring separate protection: **0**
- Exact bytes: **0**
- Exact GB: **0.000 GB**
- Basis: all 376 auto-90d archives observed in immutable evidence are `mode=complete`; no dependency-chain evidence was proven.

## Unknown count and GB

- UNKNOWN archives: **508**
- Exact bytes: **24,423,465,474**
- Exact GB: **24.423 GB**
- These remain protected.

## Legacy-root breakdown

- Cohort count: **500**
- Cohort bytes: **24,168,832,069**
- Cohort GB: **24.169 GB**

Breakdown:
- proven unique: **0** / **0 bytes**
- proven duplicates: **0** / **0 bytes**
- proven failed/partial: **0** / **0 bytes**
- superseded but unique: **0** / **0 bytes**
- unknown: **500** / **24,168,832,069 bytes** / **24.169 GB**

Truth: the immutable evidence does **not** prove legacy-root removability.

## Auto-90d breakdown

- Cohort count: **376**
- Cohort bytes: **323,666,427,987**
- Cohort GB: **323.666 GB**
- Archive type: **independent full archives** (`mode=complete` across cohort)
- Cadence observed in immutable evidence: approximately **24 archives/day** during the steady hourly window
- Dependency/lineage: **no dependent chain proven**
- Verified unique recovery coverage:
  - **368** verified points
  - **323,411,794,582 bytes**
  - **323.412 GB**
- Unknown within auto-90d:
  - **8** archives
  - **254,633,405 bytes**
  - **0.255 GB**

Any reduced cadence beyond the proven evidence is:

**PROPOSED OPERATOR POLICY — NOT AUTHORIZED**

## Oldest/newest recovery points

- Oldest backup object in immutable evidence: `backups/MASCI_complete_backup_2026-05-11_141538Z.zip`
- Oldest **proven recoverable** point: `2026-05-25T23:25:17.732898+00:00`
- Newest **proven recoverable** point in immutable evidence: `2026-07-12T15:05:17.823023+00:00`
- Newest live backup observed after evidence capture: `2026-07-12T16:05:33.504970+00:00`

## Maximum recovery gap

- Maximum proven recovery gap: **389,308.234156 seconds**
- Maximum proven recovery gap: **108.141 hours**
- Gap pair:
  - start: `2026-05-26T11:06:36.375160+00:00`
  - end: `2026-05-30T23:15:04.609316+00:00`

## Final operator decision table

### OPTION A · RETAIN EVERYTHING
- objects retained: **876**
- bytes retained: **347,835,260,056**
- GB retained: **347.835 GB**
- oldest proven recovery point: `2026-05-25T23:25:17.732898+00:00`
- newest proven recovery point (immutable evidence): `2026-07-12T15:05:17.823023+00:00`
- maximum recovery gap: **108.141 hours**
- projected growth: immutable evidence shows steady auto-90d window averaging **~24 archives/day** and **~21.768 GB/day** across `2026-06-29` → `2026-07-11`
- operational risk: **LOWEST** retention risk; **no storage reduction**

### OPTION B · REMOVE ONLY PROVEN FAILED/PARTIAL/CORRUPT ARCHIVES
- immutable candidate manifest ID/hash: **NONE**
- object count: **0**
- exact GB: **0.000 GB**
- proof for each object: **no affirmatively unusable archive proven in immutable evidence**
- recovery impact: **none**
- remaining bucket size: **350,655,277,412 bytes** total bucket; **347,835,260,056 bytes** backups unchanged

### OPTION C · REMOVE ONLY PROVEN BYTE-IDENTICAL DUPLICATES
- immutable candidate manifest ID/hash: **NONE**
- object count: **0**
- exact GB: **0.000 GB**
- duplicate groups: **0**
- retained canonical copy: **N/A**
- recovery impact: **none**
- remaining bucket size: **350,655,277,412 bytes** total bucket; **347,835,260,056 bytes** backups unchanged

### OPTION D · LEGACY-ROOT RETENTION DECISION
- proven unique: **0**
- proven duplicates: **0**
- proven failed/partial: **0**
- superseded but unique: **0**
- unknown: **500** / **24.169 GB**
- exact effect of any evidence-supported reduction: **none proven**
- truthful consequence: any reduction of legacy-root today would act on **UNKNOWN** restore points and is **not authorized by evidence**

### OPTION E · AUTO-90D RETENTION DECISION
- archive type: **376 independent full archives**
- cadence: observed hourly steady-state window with **24 archives/day**
- lineage/dependency: **no dependent chain proven**
- unique recovery coverage: **368 verified** / **323.412 GB** plus **8 UNKNOWN** / **0.255 GB**
- exact consequences of retaining a reduced set: **not evidence-proven in this track** beyond the general truth that fewer retained hourly full archives reduce restore granularity and may widen recovery gaps

**PROPOSED OPERATOR POLICY — NOT AUTHORIZED**

## Candidate manifest IDs/hashes, if any

- Failed/partial/corrupt candidate manifest: **NONE**
- Byte-identical duplicate candidate manifest: **NONE**

## R2 objects changed

- **0**

## Production business records changed

- **0**

## Configuration changed

- **0**

## Storage reclaimed

- **0 GB**

## Delete engine

- **DISABLED**

## Final verdict

**STOP — PRODUCTION RECOVERY RISK**

Reason:
- The authorized observability repair is verified in preview but **not** verified live in production.
- Live production still fails both mandatory truthfulness checks:
  - prefix normalization defect still live
  - integrity metadata defect still live
- Safe low-risk cleanup candidates are exhausted at **zero**, and further reduction would require policy choice over **UNKNOWN** or still-unverified recovery coverage.

Supporting artifacts:
- Live probe: `/app/memory/track_27_09a_live_probe.json`
- Live inventory compare: `/app/memory/track_27_09a_live_inventory_compare.json`
- Computed retention facts: `/app/memory/track_27_09a_computed_facts.json`
- Full live inventory snapshot used for reconciliation: `/app/memory/track_27_09a_inventory_backups_1000.json`
- Testing-agent verification: `/app/test_reports/iteration_track_27_09a_verification.json`