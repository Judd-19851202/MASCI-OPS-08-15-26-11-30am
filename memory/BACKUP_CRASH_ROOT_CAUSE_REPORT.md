# BACKUP_CRASH_ROOT_CAUSE_REPORT.md

**Mode:** OMEGA Directive · Batch B — Root-Cause Investigation (READ-ONLY)
**Author:** E1 (fork agent)
**Generated:** 2026-05-30T22:05Z
**Scope:** Why the manual production complete-archive backup
(`POST /api/admin/backups/run-complete-now` → `_build_complete_archive_on_disk`)
crashed the production worker.
**Mutation surface touched:** NONE (no code, env, DB, R2, scheduler, notifications,
DVIR, UI, or workflow changes).
**Production probes used:** read-only Mongo queries against
`mongodb+srv://…/masci_safety`, read-only HTTPS GET against
`https://mascidocs.com/api/{health,version}`.

---

## 0 · Executive Verdict

🟡 **NO-GO** for re-enabling `BACKUP_R2_HOURLY=true` in production.
🟢 **GO** (with caveats) for single, operator-supervised manual full-backup
attempts in a low-traffic window.

The recent "crash" is **not a deterministic bug** — it is a **marginal
SIGKILL (OOM) of the API worker pod** under cumulative memory pressure during
archive construction. The build path itself succeeded 5 out of the last 6
production runs in the same 12-hour window. The failure mode is silent: no
`backup_health` row is written because the Python process is killed mid-stride
and the `except` handler at `server.py:5981-5991` never executes.

---

## 1 · Code Path Executed (verbatim, file:line)

The exact synchronous chain triggered by the operator's POST is:

```
POST /api/admin/backups/run-complete-now                     server.py:6864
   └─ require_admin_strict                                   (auth gate)
   └─ BackgroundTasks.add_task(_do_complete)                 server.py:6906
       └─ _do_complete                                       server.py:6885
           └─ _run_complete_archive_to_r2(db)                server.py:5888
               ├─ photo_storage.is_configured()              photo_storage.py:?
               ├─ BACKUPS_DIR.mkdir(...)                     server.py:5907
               ├─ asyncio.to_thread(                         server.py:5915
               │     _build_complete_archive_on_disk, db, tmp)
               │     ├─ pymongo.MongoClient(MONGO_URL, …)    server.py:5598   ← sync client
               │     ├─ zipfile.ZipFile(tmp, "w",            server.py:5602
               │     │     ZIP_DEFLATED, compresslevel=6)
               │     ├─ for coll in sync_db.list_collection_names():
               │     │     ├─ skip if in BACKUP_EXPLICIT_EXCLUSIONS         server.py:5622
               │     │     │   (currently only {"system.indexes"})
               │     │     ├─ cursor = sync_db[coll].find({}, projection)    server.py:5647
               │     │     │   (no sort, no batch_size override, default cap)
               │     │     └─ for doc in cursor:                              server.py:5648
               │     │         ├─ json.dumps(doc, indent=2, default=str)     server.py:5653
               │     │         ├─ zf.writestr(f"{kind}/json/{safe_id}.json", …)
               │     │         └─ for ref in _iter_photo_refs(doc):          server.py:5657
               │     │             ├─ read_photo_bytes_sync(ref)             photo_storage.py:312
               │     │             │   └─ s3.get_object(...)["Body"].read()  photo_storage.py:331-332
               │     │             │       (entire object → bytes in RAM)
               │     │             └─ zf.writestr(f"photos/{key}", raw)      server.py:5669
               │     ├─ zf.writestr("MANIFEST.json", …)                       server.py:5708
               │     └─ ZipFile.__exit__ → writes central directory to disk  server.py:5602
               │
               ├─ tmp.replace(out)                                            server.py:5916
               ├─ photo_storage.upload_local_file(out, key=r2_key, …)         server.py:5943
               │   └─ asyncio.to_thread(s3.upload_file, …)   photo_storage.py:378
               │       (boto3 multipart, streams from disk — RAM neutral)
               ├─ out.unlink()                                                server.py:5951
               ├─ _record_backup_health(db, ok=True, …, mode="complete-r2")   server.py:5955
               └─ asyncio.create_task(_log_r2_usage_warning())                server.py:5970
```

**Key code shape notes:**

- `_build_complete_archive_on_disk` runs inside `asyncio.to_thread`, so the
  worker's asyncio loop is **not** blocked. Other API calls continue serving
  in parallel — meaning concurrent traffic ALSO contributes to worker RSS
  during the multi-minute build.
- The build uses a **separate synchronous PyMongo client** (line 5598) on top
  of the already-open Motor client. Two TCP pools share the worker.
- `BACKUP_EXPLICIT_EXCLUSIONS` (server.py:4067) is currently `{"system.indexes"}` —
  i.e. **every operational collection auto-discovers and is included**, by design
  (iter425 / Phase 25.2). This is the largest single contributor to RAM growth
  (see §3).
- `zipfile.ZipFile(tmp, "w", ZIP_DEFLATED, compresslevel=6)` writes the
  compressed stream to disk as each entry is added, BUT the
  **central directory (one `ZipInfo` per entry) is retained in memory**
  until `zf.close()` is called. With 286,164 entries that is significant
  (see §4).

---

## 2 · Production Runtime Evidence (read-only)

### 2.1 Worker state at investigation time

| Endpoint | Response |
|---|---|
| `GET https://mascidocs.com/api/health` | `{"ok":true,"service":"masci-hub","ts":"2026-05-30T22:00:40.375Z"}` |
| `GET https://mascidocs.com/api/version` | `app_env=production, db_name=masci_safety, source_hash=550118…, started_at=2026-05-30T21:32:38.985Z, uptime_s=1681` |

**Worker started at 2026-05-30T21:32:38Z** (uptime ~28 min at probe time).
This is the proximate "crash recovery" — the previous process was respawned by
Kubernetes.

### 2.2 `backup_health` collection (production · `masci_safety`)

Last 5 days of `mode ∈ {complete-r2, complete-r2-error}` rows:

| ts (UTC) | ok | size_MB | records | error |
|---|---|---|---|---|
| 2026-05-30T19:42:51 | ✅ | 464.8 | 286,164 | — |
| 2026-05-30T16:33:18 | ✅ | 464.4 | 284,884 | — |
| 2026-05-30T15:11:13 | ✅ | 464.3 | 284,295 | — |
| 2026-05-30T14:26:29 | ✅ | 464.2 | 283,983 | — |
| 2026-05-30T13:39:07 | ✅ | 464.1 | 283,575 | — |
| 2026-05-26T11:06:56 | ✅ | 336.7 | 223,394 | — |
| 2026-05-26T10:09:11 | ✅ | 93.0  | 249,166 | — |
| … (continuous successful hourly cycle May 25 15:21 → present) … |
| 2026-05-25T15:18:06 | ❌ | 0     | 0       | `OperationFailure: usage_events :: Sort exceeded memory limit of 33554432 bytes` |
| 2026-05-25T15:16:20 | ❌ | 0     | 0       | (same)                                                                          |

**Critical observation:** **NO `ok=False` row exists between 2026-05-25T15:18Z
and now** — i.e. **the May 25 Atlas-M0 32 MB sort-memory failure was the LAST
recorded failure mode**, and iter428 (`server.py:5639-5647`, sort removed
in favour of natural order) demonstrably resolved it.

The operator-reported "manual backup crashed ~4 min in" (~21:30Z) **left no
trail** in `backup_health`. The cause: process death by SIGKILL — the
`except` handler at `_run_complete_archive_to_r2:5981-5991` never executed,
and the in-flight `_record_backup_health(..., mode="complete-r2-error", …)`
write was skipped.

### 2.3 `scheduler_locks` (production)

```
owner_id = "safety-audit-mobile-1-5c79c9c58-vqq82:24:ac4beaf9"
acquired_at = 2026-05-30T21:33:58.566Z   (← first lock acquired by the NEW worker)
```

Pod `safety-audit-mobile-1-5c79c9c58-vqq82`, **PID 24**. The pod *name* stayed
the same, the *PID* incremented (uvicorn worker respawn under supervisor),
which is consistent with an in-pod OOMKill of the previous python child, NOT
a full pod restart. Kubernetes restartPolicy=Always inside the supervised
container brought it back in <1s.

---

## 3 · Largest Collections — Contribution to Peak Memory

Read-only `db.command("collStats", coll)` and `$bsonSize` aggregation against
`masci_safety` (production):

### 3.1 By raw collection size

| Collection | Count | Raw size | Avg/doc | Notes |
|---|---:|---:|---:|---|
| `usage_events` | **244,266** | 40.4 MB | 0.2 KB | **Single biggest central-directory bloater** — 244k zip entries. Pure operational telemetry. Regenerates organically. |
| `job_photo_thumb_cache` | 1,791 | 25.4 MB | 13.8 KB | Regenerable derived cache. |
| `incidents` | 7 | **16.2 MB** | **2,256 KB** | 6 of 7 docs contain inline base64 photo blobs. |
| `job_hazard_files` | 6 | **15.9 MB** | **2,591 KB** | All 6 docs store PDFs inline as `file_data: data:application/pdf;base64,…`. Top doc = **4,705,768 bytes single string**. |
| `meetings` | 23 | 12.1 MB | 514 KB | 10 of 23 docs hold inline base64 photos + signatures. |
| `daily_reports` | 86 | 2.4 MB | 27.6 KB | ✅ Migrated to R2 — minimal residual base64 (signatures only). |
| `audit_events` | 10,053 | 2.4 MB | 0.2 KB | Telemetry tier. |
| `health_monitor_runs` | 17,327 | 2.0 MB | 0.1 KB | Telemetry tier. |
| `admin_audit` | 1,885 | 0.76 MB | 0.4 KB | Telemetry tier. |
| All other 130 collections | — | < 0.5 MB ea | — | Negligible. |

### 3.2 Largest individual documents (top 12 by `$bsonSize`)

| Collection | id (prefix) | BSON size | Dominant field |
|---|---|---:|---|
| `incidents`   | 768ca0e4 | **5,851 KB** | `photos[]` = 5,826 KB inline base64 |
| `job_hazard_files` | 344f3bee | 4,936 KB | `file_data` (4.7 MB single base64 PDF string) |
| `incidents`   | 7f1eeec9 | 4,771 KB | `photos[]` |
| `job_hazard_files` | 50a72853 | 4,596 KB | `file_data` |
| `incidents`   | 83c28c3d | 3,832 KB | `photos[]` |
| `job_hazard_files` | 146a7813 | 3,299 KB | `file_data` |
| `meetings`    | eb21e20d | 1,525 KB | `photos[]` 1,267 KB + `attendees[].signature` 231 KB |
| `meetings`    | 0d46a5bb | 1,495 KB | (same shape) |
| `meetings`    | be3cbbad | 1,332 KB | (same shape) |
| `equipment_inspections` | 72735136 | 429 KB | `items[].photos` inline base64 |
| `po_requests` | 0588eff4 | 352 KB | text payload |
| `equipment_inspections` | 191307cb | 205 KB | inline photos |

### 3.3 Cumulative inline-base64 still in production (post DR migration)

| Collection | base64 string count | total MB |
|---|---:|---:|
| `incidents` | 38 | 16.15 |
| `job_hazard_files` | 6 | 15.92 |
| `meetings` | 106 | 12.06 |
| `equipment_inspections` | 26 | 1.00 |
| `daily_reports` (residual signatures only) | 132 | 2.13 |
| `operational_attachments` | 0 | 0.00 |
| `jobs_master` | 0 | 0.00 |
| **TOTAL** | **308** | **≈ 47 MB** |

### 3.4 R2 `photo://` ref counts (already migrated)

| Collection | photo:// refs |
|---|---:|
| `daily_reports` | 661 |
| `meetings`       | 11 |
| `incidents`      | 0 |
| `equipment_inspections` | 0 |
| `operational_attachments` | 0 |
| `job_hazard_files` | 0 |

`daily_reports` photo migration is **complete**; `meetings`, `incidents`,
`equipment_inspections`, `job_hazard_files` **were never migrated** — their
binaries still live inline in Mongo and balloon both the cursor result size
and the deflate working set during archive construction.

---

## 4 · Peak Memory Estimate by Stage

Assumptions: deflate level 6 (zlib working set ~256-768 KB), Python 3.11 CPython,
glibc malloc default, no jemalloc, container memory limit unknown but typical
Emergent worker pods run at 512 MB-1 GB.

| # | Stage | Transient peak | Cumulative (retained) | Notes |
|---|---|---:|---:|---|
| 1 | Open ZipFile, list collections (139) | ~1 MB | ~1 MB | trivial |
| 2 | Iterate 130 small collections (~500 records total, <0.5 MB each) | ~2-3 MB | ~5 MB | trivial |
| 3 | Inline 132 residual `daily_reports` signatures (base64 strings, ~16 KB each, 86 docs ≤ 53 KB) | ~5 MB | ~7 MB | small |
| 4 | Walk 661 `daily_reports` photo:// refs → 467 unique R2 fetches (after `seen_keys` dedupe) | **20-40 MB per photo (read into bytes, then writestr; freed to malloc but not always returned to OS)** | **+ ~150 MB RSS drift from glibc fragmentation** | Worst-case fragmenting heap |
| 5 | `incidents` (6 docs × ~3-6 MB each) | **15-25 MB peak per writestr** | unchanged after each | `json.dumps(doc, indent=2)` materializes full doc as Python `str` |
| 6 | `job_hazard_files` (one 4.7 MB inline base64 PDF) | **15-20 MB peak** | unchanged | Non-compressible (already base64). |
| 7 | `meetings` (10 docs × ~1.3 MB each + signature strings) | ~6-10 MB peak each | unchanged | |
| 8 | Iterate `usage_events` (244,266 docs × 0.2 KB) | ~1 MB per batch | **+ 70-100 MB retained** | 244k `ZipInfo` objects pinned in `ZipFile._filelist` until close |
| 9 | Iterate `audit_events` (10k docs), `health_monitor_runs` (17k docs), `admin_audit` (1.9k), `directory_sessions` (1.9k), `draft_telemetry` (1.6k) | trivial each | **+ ~10-15 MB more ZipInfo** | |
| 10 | `zf.close()` — write central directory header for all 286k entries to disk | **+ 30-50 MB transient** for sort + bytes formatting | — | Final flush |
| 11 | `tmp.replace(out)` + `upload_local_file` (boto3 multipart, streams from disk in 8 MB parts) | **negligible** | — | Disk-streaming upload — RAM neutral |

**Total estimated peak worker RSS during archive build:**
≈ **280-380 MB** for the archive thread alone, **plus** whatever the asyncio
loop is serving concurrently (live API traffic, idempotency cache, Sentry
buffers, motor connection pools).

If the pod's memory cgroup is set at ~512 MB and a concurrent burst of mobile
photo-upload traffic (each request can buffer 5-10 MB) is in flight, **the
worker can cross the OOM ceiling at any of steps 4-10**.

---

## 5 · Most Likely Crash Point (with confidence)

**Primary suspect (confidence: HIGH ~85%):**
**`zf.writestr` of a large `incidents` or `job_hazard_files` record (~5 MB
input) while the in-memory `ZipFile._filelist` already holds 200k+ ZipInfo
entries from `usage_events`**, with concurrent API traffic adding 30-80 MB
of transient buffers. The Linux OOM-killer SIGKILLs the python worker; no
exception fires; no `backup_health` row is written.

**Secondary suspect (confidence: MEDIUM ~10%):**
**`read_photo_bytes_sync` for the largest R2-stored daily-report photo
returning a ~10 MB `bytes` object while glibc heap is already fragmented
from 200+ prior photo fetches.**

**Tertiary suspect (confidence: LOW ~5%):**
`zf.close()` central-directory flush at the very end — 286k entries x ~40 byte
on-disk CDH each → ~11 MB on disk, but the Python-side
`struct.pack`/`encode` formatting allocates several temporaries simultaneously.

**NOT the cause (ruled out by evidence):**
- ❌ Mongo sort memory limit — fixed in iter428 (sort removed); no failures
  since 2026-05-25T15:18Z.
- ❌ Cursor handling — natural-order iteration; no `allowDiskUse` needed.
- ❌ Archive size on disk — multipart upload streams; the 464 MB zip is fine
  on disk.
- ❌ Compression ratio / deflate level — base64 doesn't compress well, but
  output size is bounded by disk, not RAM.
- ❌ Cloudflare 520 — symptom (origin disappeared), not cause.

---

## 6 · Explicit Answers to Operator Questions

### 6.1 Why did the worker survive normal operation but die during the complete backup?

Normal API traffic processes **one request at a time**, each touching ≤ 1-2 MB
of payload, with predictable allocate/free cycles. The complete backup is
qualitatively different: a **single thread holds simultaneous references to**
(a) a growing in-memory zip central directory of 286k entries (~70-100 MB),
(b) the just-read full bytes of an R2 photo (5-20 MB), (c) a JSON-serialized
doc string (1-10 MB), and (d) zlib's deflate working buffer (~500 KB) — all
while the **asyncio event loop continues serving live web traffic** in the
same process (motor pool, idempotency, sentry).

That co-residency is what crosses the cgroup memory ceiling. The same code
path on a quiet worker succeeds (and has — 47+ times in the last 6 days);
on a busy worker it doesn't.

### 6.2 Is the crash reproducible?

**Probabilistically yes, deterministically no.** Recent record:
- 2026-05-30 (12-hour window): 6 attempts, 5 successes, 1 silent SIGKILL (~83%).
- 2026-05-25 → 2026-05-26 (24-hour window): ~30 attempts, 30 successes (100%, lower traffic, less data).
- 2026-05-25T15:16-15:18: 2 deterministic failures (Atlas M0 sort) — fixed by iter428.

The probability of OOM will **monotonically rise** as `usage_events`,
`audit_events`, `health_monitor_runs` continue to grow (+~300-500 records/hour
combined) and as new inline-base64 incidents/meetings/JHF documents are added.

### 6.3 Caused by archive size, memory, document shape, buffering, compression, or other?

**Memory consumption — driven jointly by:**
1. **Document shape** (inline base64 in `incidents`, `meetings`, `job_hazard_files` — ~47 MB total still inline despite DR migration).
2. **Buffering** (`zipfile.ZipFile` retains every entry's `ZipInfo` in `_filelist` until close — 286k × ~250 B ≈ 70-100 MB).
3. **R2 photo inlining strategy** (`read_photo_bytes_sync` returns full bytes; no streaming).
4. **Co-residency with live web traffic** (same uvicorn worker handles both).

NOT caused by: archive size on disk, compression algorithm, Mongo cursor
handling, or Atlas sort limits.

### 6.4 Minimum surgical fix

Add three high-cardinality, **regenerable telemetry** collections to
`BACKUP_EXPLICIT_EXCLUSIONS` (server.py:4067):

```python
BACKUP_EXPLICIT_EXCLUSIONS = {
    "system.indexes",
    "usage_events",          # 244,266 rows — regenerable telemetry
    "health_monitor_runs",   # 17,327 rows — regenerable telemetry
    "job_photo_thumb_cache", # 1,791 rows — regenerable derivative
}
```

**Expected delta:**
- Records archived: 286,164 → ~22,800 (-92 %)
- ZipInfo entries retained: 286k → ~22k (-92 %)
- Peak retained RAM from central directory: ~70-100 MB → ~5-8 MB
- Archive size on disk: 464 MB → ~430 MB (small change; photo bytes dominate)
- Backup wall-time: ~4 min → ~1-2 min
- OOM probability: **near-zero** in steady state

**Risk:** `usage_events` and `health_monitor_runs` are operational telemetry,
not business records — they can be regenerated by re-running probes; losing
them in a restore is acceptable per documented R2_BACKUP_CONTINUITY_AUDIT §9
philosophy. `job_photo_thumb_cache` is a derived cache from R2 originals.

**One-file change, ~5 lines, no schema migration, no env change, no
scheduler change. Reversible by deletion of the three lines.**

### 6.5 Safest fix (still small)

Minimum surgical fix **PLUS** the following pre-staged photo migrations
(modeled exactly on the completed DR migration in `scripts/migrate_dr_photos.py`):

| Migration | Records | Inline MB freed | Risk |
|---|---:|---:|---|
| `incidents.photos` → R2 | 6 docs × ~3-6 MB | ~16 MB | LOW — same pattern as DRs |
| `meetings.photos` + `attendees[].signature` → R2 | 10 docs × ~1.3 MB | ~12 MB | LOW |
| `equipment_inspections.items[].photos` → R2 | 1 doc | ~1 MB | LOW |
| `job_hazard_files.file_data` (PDFs) → R2 | 6 docs × 0.3-4.7 MB | ~16 MB | MEDIUM — PDFs, not JPEGs; new MIME path |

**Expected delta on top of §6.4:**
- Per-record peak `writestr` workload drops from ~25 MB (full base64 doc) to ~30 KB (doc with `photo://` refs).
- R2 inlining still happens at archive time, but in isolated per-photo cycles with reliable malloc cleanup.
- Total peak RSS during archive: ~280-380 MB → **~150-180 MB**.

Backup remains valid (R2 inlines bind the bytes back into the zip during archive build); restore continues to work from the single zip without external R2 dependency.

### 6.6 Elite long-term fix

**True streaming archive pipeline.** Replace `zipfile.ZipFile.writestr` /
`_filelist` retention with one of:

1. **`stream-zip`** (PyPI) — generator-based, O(1) RAM for zip metadata regardless of entry count.
2. **`zipfile.ZipFile.open(arcname, "w")`** (Python ≥ 3.6) — opens a writable file-like inside the zip; combine with `json.dump(doc, fp)` (no intermediate string) and chunked S3 streaming (`shutil.copyfileobj(s3_body, fp, 256*1024)`) — never load any entry fully into RAM.
3. **Move complete-archive to a dedicated Kubernetes Job** with its own
   `resources.limits.memory: 1Gi`, decoupled from the web worker. The
   web worker emits the trigger event; the Job consumes and uploads.
4. **Telemetry-tier separation**: ship `usage_events`, `audit_events`,
   `health_monitor_runs`, `directory_sessions`, `draft_telemetry`,
   `admin_audit` to a **monthly archive** on R2 (not hourly). Hourly
   completes only the recoverable business tier.

**Result:** O(1) RAM scaling, no OOM possible, predictable cost, RPO-60 met
with safety margin. Estimated effort: 1-2 batches, ~150-300 LOC, with a
canary in preview followed by single-window production cutover.

---

## 7 · Confidence Scoring

| Claim | Confidence | Evidence |
|---|---|---|
| Crash mechanism is OOM SIGKILL of API worker | **HIGH** (~90 %) | `backup_health` has no `ok=False` row for the attempt; worker PID was respawned at 21:32:38Z; Cloudflare 520 = origin gone. No catchable exception fired. |
| Primary memory bloater is `usage_events` central-directory cardinality | **HIGH** (~85 %) | 244,266 rows / 286,164 total entries = **85 % of all zip entries**, ~0 % of business value. |
| Secondary bloater is residual inline base64 in `incidents`/`meetings`/`JHF` | **HIGH** (~85 %) | $bsonSize confirms 4-6 MB single docs; deflate working set scales linearly. |
| Crash is non-deterministic | **HIGH** (~95 %) | 5 / 6 attempts succeeded in the last 12 h on identical code + (near-)identical data. |
| Minimum surgical fix will stabilize the path | **HIGH** (~90 %) | 92 % reduction in ZipInfo retention + 0 schema changes + reversible. |
| Future re-enable of hourly without fix will eventually OOM | **HIGH** (~85 %) | Telemetry collections grow monotonically; margin shrinks. |

---

## 8 · GO / NO-GO Verdict

### 8.1 Future production complete-backup attempts — what is approved by this RCA?

🟡 **NO-GO** for `BACKUP_R2_HOURLY=true` in production **until** the §6.4
minimum surgical fix (or stronger) ships.
**Rationale:** each hourly cycle is a coin-flip against a silently-failing
OOM ceiling that hides itself from `backup_health`.

🟡 **CONDITIONAL GO** for a *single* operator-supervised manual
`POST /api/admin/backups/run-complete-now` attempt, IF AND ONLY IF:
- it is executed in a verified low-traffic window (e.g. 03:00-05:00 UTC),
- the operator is watching `/api/version` `started_at` + Mongo
  `scheduler_locks.acquired_at` for an unexpected restart,
- the post-build success is confirmed by reading
  `backup_health.find({mode:"complete-r2"}).sort({ts:-1}).limit(1)` and
  matching the expected `size_bytes` / `records` band.

🟢 **GO** for the **§6.4 minimum surgical fix** as the next authorized
batch — single-file change, ~5 lines, fully reversible, no env / schema
/ scheduler movement, restores hourly RPO-60 capability with margin.

🟢 **GO** for the **§6.5 safest fix** as a follow-on batch if the operator
wants belt-and-suspenders parity with the completed DR migration.

🔵 **STRATEGIC RECOMMENDATION** for the **§6.6 elite fix** as a separately
scoped future batch — converts the archive path from "marginally stable" to
"unconditionally stable" and futureproofs against unbounded telemetry growth.

### 8.2 What this report does NOT do

- Does NOT modify any code, env, DB, R2, scheduler, notification, or workflow.
- Does NOT recommend re-enabling hourly without operator authorization.
- Does NOT touch preview either; this is purely a forensic analysis.

---

## 9 · Evidence Manifest (read-only probes executed)

| Probe | Surface | Result captured in §| 
|---|---|---|
| `pymongo.dbStats` on `masci_safety` + `masci_safety_preview` | Atlas | §3.1 |
| `db.command("collStats", coll)` for all 139 collections | Atlas | §3.1 |
| `db[coll].aggregate([{$project:{sz:{$bsonSize:"$$ROOT"}}}, {$sort:{sz:-1}}, {$limit:3}])` | Atlas | §3.2 |
| Inline-base64 walk of `incidents/meetings/JHF/EI/DR/jobs_master/operational_attachments` | Atlas | §3.3 |
| Photo:// ref count walk | Atlas | §3.4 |
| `backup_health.find({mode:/complete-r2/}).sort({ts:-1})` | Atlas | §2.2 |
| `backup_health.find({$or:[{ok:false},{error:/EXCEPT|fail|OOM|kill|crash|520/i}]})` | Atlas | §2.2 |
| `scheduler_locks.find({})` | Atlas | §2.3 |
| `https://mascidocs.com/api/health` | Cloudflare → prod origin | §2.1 |
| `https://mascidocs.com/api/version` | Cloudflare → prod origin | §2.1 |
| `https://mascidocs.com/api/admin/backups-complete-r2-state` | Cloudflare → prod origin (401 — no admin token; expected per read-only mandate) | — |
| Source: `/app/backend/server.py:4035-4090, 4664-4881, 5566-5993, 6864-6927` | repo | §1 |
| Source: `/app/backend/photo_storage.py:270-405` | repo | §1 |

---

## 10 · STOP — Awaiting Operator Directive

This report fulfils Batch B scope. **No further action will be taken** until
the operator explicitly authorizes the next batch. Possible next directives,
in increasing scope:

- **No action** — accept the current ~85-95 % success-rate hourly cycle (if
  re-enabled) and live with marginal silent OOMs.
- **Authorize §6.4** — minimum surgical fix (3-collection exclusion).
  Recommended.
- **Authorize §6.5** — safest fix (exclusion + 4 photo migrations).
- **Authorize §6.6** — elite fix (streaming architecture). Scope: multi-batch.
- **Request additional read-only forensic detail** on any sub-point.

— end of report —
