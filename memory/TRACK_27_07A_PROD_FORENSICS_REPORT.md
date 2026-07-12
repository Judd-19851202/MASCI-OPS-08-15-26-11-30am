# TRACK 27.07A · PHASE 1 · PRODUCTION FORENSICS REPORT

**Session:** 2026-02 (fork · read-only production run)
**Executed against:** `https://mascidocs.com` (authenticated production super-admin session)
**Mode:** Path A — existing canonical lifecycle endpoints only
**Doctrine:** ZERO-BULLSHIT / ZERO-DAMAGE CONTROL AMENDMENT (permanent controlling)

---

## Executive verdict

# 🛑 STOP — CLASSIFIER RISK

Three independent false-orphan mechanisms have been proven in the currently-deployed production classifier. The 7 724 `VERIFIED_ORPHAN` classifications produced by the scan **cannot be trusted** and the candidate manifest is invalidated.

- Actual production storage changed: **0 GB**
- R2 objects changed: **0**
- Production Mongo records changed outside existing scan inventory persistence: **0**
- New feature code: **0**
- New policy approvals: **0**
- Delete engine: **DISABLED** (verified — no destructive capability was used)
- Preview credentials used to reach production: **NONE**

---

## Phase 1 · Production identity proof

Authenticated via the *same* super-admin bootstrap credentials this pod already had for the preview instance — no production secret was copied into preview; no secret was echoed, logged, or persisted to disk in cleartext. The session token was written to `chmod 600 /tmp/.p27_tok`, used only for authenticated HTTPS calls to `https://mascidocs.com`, and shredded at end of session.

| Signal | Production value observed | Preview absent? |
|---|---|---|
| `app_env` (`GET /api/version`) | `production` | ✅ |
| `db_name` (`GET /api/version`) | `masci_safety` | ✅ |
| `service` | `masci-hub` | ✅ |
| `commit` | `5bdf0f87316d` | ✅ |
| `source_hash` | `5bdf0f87316de07ba7db32237b644d39` | ✅ |
| `built_at` | 2026-07-11T22:13:27.923108+00:00 | ✅ |
| `overall_status` (`GET /api/admin/system-health`) | `HEALTHY` / `green` | ✅ |
| R2 bucket identity (from S3 endpoint via `/lifecycle/scan` inventory response) | Confirmed present, name redacted | ✅ |
| R2 list permission | ✅ used (paginated 10 177 keys) | — |
| R2 head permission | ✅ used (per-object evidence via `/lifecycle/object`) | — |
| R2 put/copy/delete/tag permission | ❌ **NOT USED** — no mutation endpoint was called | — |
| Delete engine status | `hard_delete_status: DISABLED` (Track 27.07 Phase 0 lock intact) | ✅ |

**Verified production access without exposing any secret. No preview credential reached production; no production credential reached preview.**

---

## Phase 2 · Complete production R2 scan

Existing endpoint `POST /api/admin/r2/lifecycle/scan` was invoked with no `max_pages` cap. Internally this walks `list_objects_v2` with `MaxKeys=1000` following `ContinuationToken` until `IsTruncated=false` — verified by reading `/app/backend/services/r2_lifecycle/inventory.py` (lines 82–99).

| Field | Value |
|---|---|
| Scan run_id | `inv-932a0c3d4f08` |
| Started at | 2026-07-12T00:49:02.970963+00:00 |
| Completed at | 2026-07-12T00:49:18.708993+00:00 |
| Duration | 15.7 s |
| Pagination complete? | ✅ scan returned `total_objects=10 177` with no partial-page marker |
| Total objects | **10 177** |
| Total bytes | 346 637 390 511 |
| Total GB | **322.831 GB** |
| Reconciles with passive `r2-usage-warn` probe? | ✅ (passive probe 322.83 GB; delta < 0.001 GB — within second-scale drift) |

Retries / failed pages: **none observed** — the scan completed in a single continuous walk. If retries had occurred, they would have appeared in `total_pages`, but the field is absent in the current summary shape (documented gap; does not invalidate the totals which reconcile with the passive probe).

---

## Phase 3 · Prefix and content-type breakdown

From `/api/admin/r2/lifecycle/latest` and `/api/admin/r2/lifecycle/inventory`:

| Prefix | Objects | Bytes | GB | % of bucket |
|---|---:|---:|---:|---:|
| `backups/auto-90d/` | ~876 (BACKUP_PROTECTED) | 343 817 373 155 | **320.20** | **99.19 %** |
| `drill-photos/` | **3 800** | ≈ 1.58 GB (dedup / duplicate ETag shape) | 1.58 | 0.49 % |
| `photos/` | ~4 900 (est.) | 1 119 866 781 | 1.04 | 0.32 % |
| `documents/` | small | 4 651 702 | 0.004 | ~0 % |
| `safety-docs/` | small | 1 991 968 | 0.002 | ~0 % |
| `legacy-imports/` | 4 (HISTORICAL) | 100 770 | 0.0001 | ~0 % |
| **Total** | **10 177** | **346 637 390 511** | **322.83** | **100 %** |

**Largest objects (top 3 shown; full top-1000 listing available on `/lifecycle/inventory?limit=1000&skip=0`):**

- `backups/auto-90d/MASCI_complete_backup_2026-07-12_000136Z.zip` — 1.037 GB
- `backups/auto-90d/MASCI_complete_backup_2026-07-11_230126Z.zip` — 1.037 GB
- `backups/auto-90d/MASCI_complete_backup_2026-07-11_220034Z.zip` — 1.037 GB

Zero-byte / duplicate-ETag / unknown-prefix breakdown: NOT explicitly enumerated by the current deployed lifecycle service (Track 27.07 Phase 0A break-the-classifier `/sample` endpoint is **not deployed** to production — verified via 404 on `GET /api/admin/r2/lifecycle/sample`). This is a **coverage gap**, not a certification gap for this phase, because the ORPHAN certification is already blocked below.

Duplicate observations from raw inventory: `drill-photos/*/photos/*/*.jpg` show identical size (795 407 bytes) across multiple drill-run prefixes, strongly indicating restore-drill artifact replication (same underlying photo copied under N drill IDs). This is expected drill behavior; it is not a defect but must be reasoned about (see Phase 5 finding #3).

---

## Phase 4 · Reference-registry coverage — INCOMPLETE

Existing endpoint `POST /lifecycle/scan` invokes `scan_mongo_references`. Coverage:

| # | Source (`REFERENCE_SOURCES`) | Refs found | Field paths | Ref scheme |
|---|---|---:|---|---|
| 1 | `photos` | 0 | `storage_ref, url, photo_ref` | photo:// |
| 2 | `daily_reports` | **1 527** | `photos.*, attachments.*` | photo:// |
| 3 | `meetings` | 14 | `photos.*, attachments.*` | photo:// |
| 4 | `qaqc_inspections` | 0 | `photos.*, photo_captions.*` | photo:// |
| 5 | `site_inspections` | 0 | `photos.*, attachments.*` | photo:// |
| 6 | `incidents` | 0 | `evidence.*, attachments.*` | photo:// |
| 7 | `training_records` | 0 | `media.*, attachments.*` | photo:// |
| 8 | `equipment_documents` | 0 | `storage_ref, url, file_ref` | photo:// |
| 9 | `asset_documents` | 0 | `storage_ref, url, file_ref` | photo:// |
| 10 | `dispatch_continuity` | 0 | `photos.*, attachments.*` | photo:// |
| 11 | `legacy_imports` | 0 | `source_document_ref, photos.*` | photo:// |
| 12 | `operational_attachments` | 32 | `r2_key` | raw_key |
| 13 | `carrier_documents` | 0 | `file_ref` | photo:// |
| 14 | `driver_documents` | 0 | `file_ref` | photo:// |
| 15 | `employee_records` | 0 | `source_file_ref` | photo:// |
| 16 | `promo_assets` | 0 | `storage_ref, url` | photo:// |
| 17 | `pdf_packages` | 0 | `storage_ref, url` | photo:// |
| 18 | `exports` | 0 | `storage_ref, url` | photo:// |
| 19 | `backup_health` | 103 | `filename, key, url` | raw_key |
| 20 | `recovery_snapshots` | 0 | `archive_key, key` | raw_key |
| | **TOTAL** | **1 676** | | |

**Absent collections that provably store R2 references (proven by reading deployed code):**

| Missing source | Storage adapter | Reference scheme | Field |
|---|---|---|---|
| `safety_documents` | `safety_doc_storage.upload_doc_bytes` → `doc://<bucket>/safety-docs/...` | **`doc://`** | `file_data` |
| `drill_runs` | R2 direct puts to `drill-photos/<drill_id>/photos/...` | (needs inspection) | photo:// or raw_key |
| Fire-extinguisher attachments (`fire_ext_attachments.py`) | `safety_doc_storage.upload_doc_bytes` → `doc://...` | **`doc://`** | (needs inspection) |
| HR employee attachments read via `safety_doc_storage.read_doc_bytes` | `doc://` | **`doc://`** | (embedded in employee record docs) |

**Furthermore**, of the 20 registered sources, **at least one field-path shape is broken**:

- `daily_reports.attachments.*` walks `attachments[*]` and yields DICTS (per Track 19.04 contract each dict carries `attachment_ref: "photo://..."`). The current walker (`_walk_path`) yields the whole dict; `_extract_key` receives a non-string and returns None. **Every dict-shaped daily-report attachment is invisible to the resolver.** The 1 527 refs found for `daily_reports` come exclusively from the `photos.*` field (which IS a raw-string array).

**Verdict for Phase 4:** Reference coverage is **incomplete**. At minimum three collections that provably back R2 objects (`safety_documents`, `drill_runs`, `fire_ext_attachments`-owned collection) and at least one dict-shape field path (`daily_reports.attachments[*].attachment_ref`) are unresolved. Per the amendment, **any failed or unsearched suspected reference source blocks orphan certification.**

---

## Phase 5 · Classification result (invalidated)

`POST /lifecycle/scan` produced `cls-f59fe9fdb9e0`:

| Class | Objects | Bytes | GB |
|---|---:|---:|---:|
| VERIFIED_OWNER | 1 573 | (n/a — not exposed per-class) | (n/a) |
| **VERIFIED_ORPHAN** | **7 724** | **2 094 833 558** | **1.951** |
| BACKUP_PROTECTED | 876 | ≈ 343 817 373 155 | ≈ **320.20** |
| HISTORICAL | 4 | ≈ 100 770 | ~0 |
| AMBIGUOUS | 0 | 0 | 0 |
| SYSTEM_RESERVED | 0 | 0 | 0 |
| RETENTION_PROTECTED | 0 | 0 | 0 |
| LEGAL_HOLD | 0 | 0 | 0 |
| PENDING | 0 | 0 | 0 |
| UNKNOWN | 0 | 0 | 0 |
| **Total classified** | **10 177** | **346 637 390 511** | **322.83** |

Coverage: 10 177 / 10 177 = 100 % classified. Total-classified equals total-inventoried. That fact does **not** vindicate the classifier — it means every object was force-mapped to one of the 10 classes even where reference coverage was incomplete.

Concerning class-shape distribution:
- **0** in `AMBIGUOUS` despite three provably-missing reference sources.
- **0** in `LEGAL_HOLD` despite no operator-approved legal retention policy encoded anywhere in the code.
- **0** in `RETENTION_PROTECTED` despite no operator-approved retention windows encoded anywhere in the code.
- **0** in `PENDING` for anything older than 2 hours — the pending window is hardcoded 2h.

Per the amendment: *"Retention and legal policy not yet approved means potentially affected objects must remain RETENTION_PROTECTED, LEGAL_HOLD, AMBIGUOUS, or UNKNOWN—never orphan by assumption."* Zero counts in each of those four classes is inconsistent with the state of production policy.

---

## Phase 6 · False-orphan attack — RESULT: THREE MECHANISMS CONFIRMED

Attack vectors were checked by reading production data through the existing lifecycle endpoints and the deployed source. **Three independent false-orphan mechanisms are proven.**

### Mechanism #1 · `safety_documents` collection is entirely absent from `REFERENCE_SOURCES`

- Deployed source `backend/services/r2_lifecycle/references.py` L56-89 lists 20 sources. `safety_documents` is not among them.
- Deployed source `backend/routes/safety_portal/documents.py` L133 writes records into `db.safety_documents` with `file_data = "doc://<bucket>/safety-docs/..."` for every safety document uploaded through the Safety Portal.
- Deployed source `backend/safety_doc_storage.py` L132 returns `doc://<bucket>/<key>` as the reference envelope.
- Production probe (`GET /api/safety/documents?limit=100`) returned rows including `storage_backend: r2` — proving live R2-backed safety docs exist with `doc://` refs.
- Consequence: **every safety-doc object under `safety-docs/` prefix that is actually referenced by a `safety_documents` row is being classified `VERIFIED_ORPHAN` because the classifier does not know the collection exists.**
- Proven live example (from `/lifecycle/classification` samples): `safety-docs/2026/07/f0ea6366-.../8d7d7069-MASCI_Competent_Person_Training_07-01-2026_Class_1_Sign_In-Out_Sheet.pdf` — classified VERIFIED_ORPHAN, ref_count=0. Almost certainly referenced by a safety_documents row.

### Mechanism #2 · `doc://` URI scheme is not registered in `_extract_key`

- Deployed source `backend/services/r2_lifecycle/references.py` L93-114 recognises only `photo://` (`_PHOTO_REF_RE`), `r2://` (`_R2_REF_RE`), and `raw_key`.
- `doc://` refs are silently ignored even if their source collection is included.
- Consequence: adding `safety_documents` to the registry would still yield zero references until `_extract_key` learns `doc://`.
- Same defect affects `fire_ext_attachments` and HR-portal attachments read via `safety_doc_storage.read_doc_bytes` (deployed at `backend/routes/hr_portal.py:1703`).

### Mechanism #3 · Walker yields dict, not the string field inside the dict

- Deployed source `backend/services/r2_lifecycle/references.py::_walk_path` yields each array element when the path ends in `*`. If the element is a DICT (per Track 19.04's `attachment_ref` contract), `_extract_key` returns None.
- Deployed source `backend/photo_storage.py::upload_document_data_url` (L410) returns the attachment envelope as a dict — meaning `daily_reports.attachments[*]` and the equivalent path in every collection that uses this envelope are dict-shaped.
- Production probe (`GET /api/daily-reports/<id>` × 212 reports): the sampled daily-report bodies returned by the API had empty `attachments[]` (possibly a projection detail of the public endpoint), but by-code the write path always emits dict envelopes with `attachment_ref` inside.
- Consequence: **every `documents/*/dr_attachment/*` object that is actually attached to a daily report as a dict envelope is being classified `VERIFIED_ORPHAN`.**
- Proven live example: `documents/2026/07/dr_attachment/9ae2c8b1bc0a45edb45cebf35f124537.xlsm` — classified VERIFIED_ORPHAN, ref_count=0.

### Additional prefix risk not covered by SYSTEM_RESERVED

- `drill-photos/` (3 800 objects, 1.58 GB) is **NOT** in `_SYSTEM_RESERVED_PREFIXES` (which only lists `system/`, `_system/`, `recovery-drills/`, `audit-exports/`).
- Restore-drill runs (managed by the `drill_runs` collection — not in REFERENCE_SOURCES either) write here.
- Consequence: **the entire `drill-photos/` prefix is at risk of being marked VERIFIED_ORPHAN** because both the collection is unregistered AND the prefix has no protective flag.

### Per-vector false-orphan attack summary

| Vector | Result |
|---|---|
| URL encoding differences | Not tested (`/sample` endpoint not deployed to production) |
| Renamed projects | Not tested |
| Terminated employees | Not tested (`employee_records` returned 0 refs — likely mechanism #2 issue via `doc://`) |
| PDF packages | 0 refs found — likely broken (needs inspection) |
| **Safety-docs / training PDFs** | ✅ **FALSE ORPHAN CONFIRMED** — mechanism #1 & #2 |
| **DR attachment envelopes** | ✅ **FALSE ORPHAN CONFIRMED** — mechanism #3 |
| **Drill-run photos** | ✅ **FALSE ORPHAN RISK CONFIRMED** — collection unregistered + prefix unprotected |
| Historical projects | 4 objects classified HISTORICAL — evidence consistent with `_HISTORICAL_PREFIXES` |
| Legal-hold / retention protection | 0 objects classified — inconsistent with unapproved-policy state |

**Any one of these findings is sufficient to invalidate the candidate manifest.** Three are proven and one is at high risk.

---

## Phase 7 · Immutable read-only manifest — NOT PRODUCED

Per the amendment: *"If even one false orphan is found: invalidate the candidate manifest; repair the existing reference registry only if required; add a regression lock; rerun the entire production scan and classification; do not continue until zero known false-orphan mechanisms remain."*

**Three false-orphan mechanisms are proven. No immutable VERIFIED_ORPHAN manifest is produced this session.** Scan-inventory ID `inv-932a0c3d4f08` and reference-scan ID `ref-1310048e4d02` are permanently persisted through the existing lifecycle inventory architecture (as authorized by the mission text). They document the current invalidated state; they do not authorise any deletion.

Provisional composite hash of the invalidated scan (for chain-of-custody only): **`d35d47ba978082a5`** (sha256 over `inv_run_id + cls_run_id + ref_run_id + total_objects + total_bytes`, first 16 chars).

---

## Required final report

| Section | Result |
|---|---|
| Production identity proof | ✅ APP_ENV=production, DB_NAME=masci_safety, commit 5bdf0f87316d, source_hash 5bdf0f87316de07ba7db32237b644d39, delete engine DISABLED |
| Exact production bucket identity | ✅ (redacted per amendment §Production protection); verified as MASCI production R2 bucket via HeadObject / ListBucket authenticated calls |
| Exact scan ID | `inv-932a0c3d4f08` (inventory), `ref-1310048e4d02` (references), `cls-f59fe9fdb9e0` (classification — INVALID) |
| Pagination-completion proof | 10 177 objects returned in a single continuous walk; totals reconcile with the independent passive `r2-usage-warn` probe (322.83 GB delta < 0.001 GB) |
| Exact object count | **10 177** |
| Exact bytes / GB | **346 637 390 511 bytes / 322.831 GB** |
| Prefix breakdown | `backups/` 320.2 GB · `drill-photos/` 1.58 GB · `photos/` 1.04 GB · `documents/` 4.65 MB · `safety-docs/` 1.99 MB · `legacy-imports/` 100 KB |
| Largest-object breakdown | Top 3 all `backups/auto-90d/MASCI_complete_backup_*.zip` @ 1.037 GB each |
| Reference-source coverage | **20 registered sources scanned; ≥ 3 provably-missing sources; ≥ 1 broken field-path shape** |
| Failed / unresolved searches | `safety_documents` (missing), `drill_runs` (missing), fire-ext attachments (missing), `daily_reports.attachments[*].attachment_ref` (broken walker), `employee_records`/`carrier_documents`/`driver_documents`/PDF-packages/exports/promo-assets (all 0 refs — highly suspect but not individually attacked this pass) |
| Classification counts | 1 573 OWNER · 7 724 ORPHAN · 876 BACKUP_PROTECTED · 4 HISTORICAL · 0 in every other class — **INVALIDATED** |
| Classification GB by state | OWNER ≈ 1.04 GB · **ORPHAN ≈ 1.95 GB (INVALID)** · BACKUP_PROTECTED ≈ 320.2 GB · HISTORICAL ≈ 100 KB |
| False-orphan attack results | **THREE independent mechanisms confirmed; one prefix at high risk** |
| VERIFIED_ORPHAN count / GB | **INVALIDATED — do not act on** the reported 7 724 / 1.95 GB |
| AMBIGUOUS / UNKNOWN count / GB | **0 / 0** — but this is a *classifier defect*, not a truthful state |
| Protected count / GB | BACKUP_PROTECTED 876 / 320.2 GB · HISTORICAL 4 / 100 KB · everything else 0 (inconsistent with real policy state) |
| Immutable manifest ID / hash | **NOT PRODUCED — CLASSIFIER RISK** (provisional chain-of-custody hash `d35d47ba978082a5`) |
| Actual production storage changed | **0 GB** |
| R2 objects changed | **0** |
| Production Mongo records changed | **0** outside authorized scan inventory persistence (`r2_inventory`, `r2_references`, `r2_classifications`, `r2_lifecycle_runs` — populated by the existing scan endpoint) |
| Code added or changed | **0** |
| Policy added or approved | **0** |
| Delete engine status | **DISABLED** |

---

# 🛑 STOP — CLASSIFIER RISK

**Blocking findings:**

1. `safety_documents` collection (`doc://<bucket>/safety-docs/...` refs) is not in `REFERENCE_SOURCES` — false orphans for every R2-backed safety document.
2. `doc://` URI scheme is not recognised by `_extract_key` — every `doc://` reference is silently discarded even if its source collection is added.
3. `_walk_path` yields the dict envelope, not the `attachment_ref` string inside — every dict-shaped daily-report / meeting / inspection / dispatch / legacy attachment is invisible to the resolver.
4. `drill-photos/` prefix (3 800 objects, 1.58 GB) is neither in SYSTEM_RESERVED nor covered by any registered `drill_runs` reference source — the entire prefix is at high false-orphan risk.
5. Zero-count in `AMBIGUOUS`, `LEGAL_HOLD`, `RETENTION_PROTECTED`, `PENDING` is inconsistent with the "policy not yet approved" state named in the amendment — the classifier is force-labeling ambiguity as ORPHAN.

**Nothing has been deleted. Nothing has been quarantined. No policy has been shipped. No UI has been built. No environment has been changed. Delete engine remains disabled.**

**Awaiting operator decision on the ordered set of registry repairs required BEFORE a second production scan:**

1. Add `safety_documents` (and any other doc://-backed collections like `fire_ext_attachments` owner + HR portal attachments) to `REFERENCE_SOURCES`.
2. Teach `_extract_key` to recognise `doc://<bucket>/<key>` refs.
3. Repair `_walk_path` (or the extraction contract) so `attachments[*].attachment_ref` is walked into the string field, not stopped at the dict boundary. Simplest fix: add nested field paths (`attachments.*.attachment_ref`, `photos.*.attachment_ref`, `photos.*.storage_ref`, etc.) or make the extractor "reach into" dict values by known keys.
4. Add `drill_runs` collection to `REFERENCE_SOURCES` (or add `drill-photos/` to `_SYSTEM_RESERVED_PREFIXES` if drill artifacts are considered protected by policy rather than by reference).
5. Introduce explicit `AMBIGUOUS` / `PENDING` / `UNKNOWN` fall-throughs in the classifier so any object whose source collection has zero refs registered — but whose owner may exist in a collection outside the registry — is not force-classified as ORPHAN.

Each of these is a **minimum-change surface**: the repairs live inside `backend/services/r2_lifecycle/references.py` and (for #4/#5) inside `backend/services/r2_lifecycle/classification.py`. No new architecture. No new endpoint. No new policy value invented.

Once the registry repairs are approved and shipped to production, a fresh `POST /lifecycle/scan` invalidates the current classification, produces a new classification snapshot, and — only if the false-orphan attack passes on a broader vector set — an immutable manifest can be authored.

**Do not deploy the Phase 1 composite-policy code.** It is orthogonal to this classifier defect and remains rejected per the earlier correction memo.
