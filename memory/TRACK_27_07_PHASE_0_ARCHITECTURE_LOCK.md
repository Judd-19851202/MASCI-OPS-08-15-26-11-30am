# TRACK 27.07 · PHASE 0 · R2 LIFECYCLE GOVERNANCE & SCOPE LOCK

**Status:** ✅ **Phase 0 architecture + governance complete · no code changes · no deployment · no destructive operations enabled.**

**Purpose:** produce the one canonical ownership map for R2 storage governance, classify every existing artifact, and lock scope before any Track 27.07 implementation begins.

---

## 1 · TL;DR — the one canonical architecture

The platform **already has** a complete, tested, deployed R2 lifecycle governance architecture, established under **Track 27.06**. Every capability Track 27.07 needs already exists as canonical code and endpoints:

| Canonical role | Canonical module | Canonical endpoints |
|---|---|---|
| R2 abstraction (single boto3 client) | `backend/photo_storage.py::_client()` + `_bucket()` | — |
| Storage engine (write path) | `backend/photo_storage.py::upload_*` (photos), `safety_doc_storage.py::upload_doc_bytes` (docs), `promo_assets_storage.py::upload_bytes` (promo) | — |
| Lifecycle inventory | `backend/services/r2_lifecycle/inventory.py::run_inventory_scan` | `POST /api/admin/r2/lifecycle/scan` |
| Lifecycle references | `backend/services/r2_lifecycle/references.py::scan_mongo_references` | — |
| Lifecycle classification | `backend/services/r2_lifecycle/classification.py::classify_all` | `GET /api/admin/r2/lifecycle/classification` |
| Storage health | `backend/services/r2_lifecycle/health.py::compute_storage_health` | `GET /api/admin/r2/lifecycle/health` |
| Intelligence (top prefixes / projects / cost) | `backend/services/r2_lifecycle/intelligence.py` | `GET /api/admin/r2/lifecycle/intelligence` + `/growth` |
| Delete authority (retention pruner, dry-run first) | `backend/lib/r2_retention.py::plan_retention` + `run_retention` | `POST /api/admin/r2/lifecycle/dry-run` |
| Backup subsystem | `backend/services/operations_control/backups.py`, `backend/backup_verification.py`, scheduled loop in `server.py` | `/api/admin/recovery/snapshot`, `/api/admin/backups*` |
| OCC integration | `backend/routes/occ_health_aggregator.py::_eval_recovery_snapshot`, `_eval_storage_health`, `_eval_backups_scheduler` | `GET /api/admin/occ/health` |
| Diagnostics integration | `backend/routes/admin_ops.py::compute_system_health` (integrations + backup subcards) | `GET /api/admin/system-health` |
| Governance owner | Track 27.06 stewardship (`routes/admin_r2_lifecycle.py`) | Same |
| Certification owner | Track 27.06 stewardship (`memory/certification_manifest`) | — |
| Storage scheduler | Single backup-scheduler loop in `server.py` (registered via `lib/platform_status.py` group `backup-scheduler`, Track 22.1I.1) | `GET /api/admin/backups-scheduler-state` |

**All eight "one canonical X" bullets from the mission gate are satisfied by Track 27.06 code that is already in production.** No new storage architecture is required for Track 27.07.

---

## 2 · Complete storage-component inventory

### 2.1 R2/S3 abstraction layer (canonical + duplicates)

| # | Module | Purpose | Classification | Notes |
|---|---|---|---|---|
| 1 | `backend/photo_storage.py::_client()` + `_bucket()` | The single lazy-init boto3 S3 client the whole platform uses. Reads `S3_ENDPOINT_URL / S3_BUCKET / S3_ACCESS_KEY / S3_SECRET_KEY`. | **CANONICAL** | Consumed by `photo_storage`, `safety_doc_storage`, `promo_assets_storage`, `services/operations_control/backups`, `backup_verification`, `recovery_dashboard`, `server.py` (backup loop), `services/r2_lifecycle/inventory` (indirectly via callers), `lib/r2_retention`. |
| 2 | `backend/routes/track_28_12_housekeeping.py::_r2_client_for_retention` (originally direct `boto3.client("s3")`) | Duplicate boto3 wiring introduced by Track 28.12. | **DUPLICATE** | Uses wrong env-var names (`R2_*`), so it returns 503 on prod. Even the preview "fix" that reuses `photo_storage._client()` is still a duplicate endpoint; the client itself was correct at row 1. |
| 3 | `backend/tests/track_22_1c/enumerate_lifecycle.py` | Test-only script from Track 22.1c. | **REUSABLE** (test) | Test scaffolding, not runtime. Leave in place. |

### 2.2 Storage write paths (upload/download surface)

All read/write helpers use `photo_storage._client()`. The following files own domain-specific write flows and must remain untouched by Track 27.07:

| Domain | Owner | Purpose |
|---|---|---|
| Job photos | `photo_storage.py` + `routes/job_photos.py` + `routes/dr_v2_photos.py` | **CANONICAL** — photo pipeline. |
| Safety documents | `safety_doc_storage.py` + `routes/safety_portal/documents.py` | **CANONICAL** — safety docs. |
| Promo assets | `promo_assets_storage.py` + `routes/promo_assets.py` | **CANONICAL** — public credential media. |
| Job/JHA files | `job_hazard_files.py` + `tools.py` (upload_doc/download_doc) | **CANONICAL** — JHA + project docs. |
| Employee source files | `routes/employee_records.py` | **CANONICAL** — HR original files. |
| Qualification attachments | `routes/qualifications.py` | **CANONICAL** — qualification evidence. |
| Fire-ext attachments | `routes/safety_portal/fire_ext_attachments.py` | **CANONICAL** — equipment attachments. |
| Trench QR photos | `routes/trench_safety/qr_photos.py` | **CANONICAL** — trench evidence. |
| Operational attachments | `routes/operational_attachments.py` | **CANONICAL** — cross-domain attachments. |
| Asset docs | `routes/asset_documents.py` | **CANONICAL** — asset attachments. |
| Carrier/Driver docs | `routes/transportation_phase2.py` | **CANONICAL** — transport compliance. |
| Ops actions photos | `routes/operations_actions/api.py` | **CANONICAL** — operations photos. |
| PO receipts | `routes/po_requests.py` | **CANONICAL** — procurement receipts. |
| Shop parts photos | `routes/shop_parts.py` | **CANONICAL** — shop uploads. |
| Payroll variance | `routes/payroll_variance.py` | **CANONICAL** — HR variance uploads. |
| Local→R2 migration script | `scripts/migrate_local_project_docs_to_r2.py` | **REUSABLE** (script) | One-shot migration, not runtime. |

### 2.3 R2 lifecycle governance (Track 27.06)

| Path | Purpose | Classification |
|---|---|---|
| `backend/services/r2_lifecycle/__init__.py` | Package entrypoint. | **CANONICAL** |
| `backend/services/r2_lifecycle/inventory.py` | `run_inventory_scan(db, s3, bucket)`, paginated `list_objects_v2`, persists rows to `r2_lifecycle_objects` collection, returns `InventoryPage`. | **CANONICAL** |
| `backend/services/r2_lifecycle/references.py` | `scan_mongo_references(db)` — walks every configured `ReferenceSource` (Mongo collection + field-path) and records which R2 keys are referenced. | **CANONICAL** |
| `backend/services/r2_lifecycle/classification.py` | `classify_object()` → one of {VERIFIED_OWNER, VERIFIED_ORPHAN, BACKUP_PROTECTED, RETENTION_PROTECTED, LEGAL_HOLD, HISTORICAL, SYSTEM_RESERVED, PENDING, AMBIGUOUS, UNKNOWN}. `classify_all(db)` runs across the whole inventory. Evidence-backed. | **CANONICAL** — this IS the classifier Track 27.07X asked for. |
| `backend/services/r2_lifecycle/health.py` | `compute_storage_health(db)` → scored health with sub-scores (capacity, lifecycle, freshness). | **CANONICAL** |
| `backend/services/r2_lifecycle/intelligence.py` | `top_prefixes`, `top_projects`, `largest_objects`, `growth_series`, `estimate_cost`. | **CANONICAL** |
| `backend/routes/admin_r2_lifecycle.py` | The 9 admin endpoints exposing all of the above (see §1 table). | **CANONICAL** |
| `backend/scripts/track_27_backfill_lifecycle_status.py` | Backfill helper. | **REUSABLE** (script) |

### 2.4 Delete authority

| Path | Purpose | Classification |
|---|---|---|
| `backend/lib/r2_retention.py::plan_retention` | **Canonical dry-run planner.** Returns `RetentionPlan{delete: List[str], deleted_by_tier: {1:n,2:n,3:n,4:n}}`. Idempotent. No mutation. | **CANONICAL** |
| `backend/lib/r2_retention.py::run_retention` / `_delete_batch` | Executes the plan against R2 using `s3.delete_objects` (1000-key batches, S3 hard cap). Uses **the canonical `photo_storage._client()`**. | **CANONICAL** — this IS the delete authority. Must be extended, not replaced. |
| `backend/photo_storage.py::delete_by_key` (line 655) | Single-object delete helper. Used by domain-specific soft-remove flows. | **CANONICAL** — domain-level object removal. |
| `backend/safety_doc_storage.py::delete_by_key` (line 184) | Same, safety-doc scope. | **CANONICAL** — domain wrapper on top of `photo_storage`. |
| `backend/promo_assets_storage.py::delete_object_by_key` (line 139) | Same, promo-asset scope. | **CANONICAL** — domain wrapper. |
| `backend/routes/track_28_12_housekeeping.py` — quarantine / recycle-bin | Parallel soft-delete engine, `housekeeping_recycle_bin` + `r2_quarantine` collections, `POST /api/admin/r2/quarantine`. | **DUPLICATE** — the canonical answer is to extend `admin_r2_lifecycle` + `lib/r2_retention` (add optional quarantine step + soft-move) rather than maintain a parallel recycle bin. |

### 2.5 Backup / recovery subsystem

| Path | Purpose | Classification |
|---|---|---|
| `backend/services/operations_control/backups.py` | Backup aggregator (invoked by scheduler + status API). | **CANONICAL** |
| `backend/services/operations_control/r2.py` | R2 status for OCC/operations-control page. | **CANONICAL** |
| `backend/services/operations_control/storage.py` | Storage stanza used by OCC. | **CANONICAL** |
| `backend/backup_verification.py` | Verifies backup integrity + counts archives in R2. | **CANONICAL** |
| `backend/routes/backup_verification_routes.py` | Admin backup-verification endpoints. | **CANONICAL** |
| `backend/routes/recovery_dashboard.py` | `/api/admin/recovery/snapshot` — the endpoint OCC calls. | **CANONICAL** |
| Backup scheduler loop | Defined in `server.py`, registered via `lib/platform_status.py` group `backup-scheduler` (Track 22.1I.1). | **CANONICAL** |

### 2.6 Domain-lifecycle modules (unrelated to R2 lifecycle)

These have "lifecycle" in the name but govern domain-workflow state (dispatch assignment lifecycle, incident lifecycle, employee lifecycle, etc.). **Not storage-related.** Do NOT touch.

`routes/{daily_report,dispatch,employee,incident,ownership,payroll_variance,qaqc,site_inspection}_lifecycle.py` · `lib/transport_hr_lifecycle.py` · `dispatch_lifecycle.py`.

### 2.7 Integration health probe (touches R2)

`backend/routes/integrations/_storage.py::compute_provider_status` — reads `photo_storage.is_configured()` to expose the "storage" integration probe used by `/api/admin/integrations/health`. **CANONICAL** — do not duplicate.

---

## 3 · Track 28.12 review (per operator directive)

Per operator directive: review every artifact from Track 28.12, do not execute, do not improve, do not deploy. Classify each with exactly one label:

| Artifact | Classification | Disposition |
|---|---|---|
| `backend/routes/track_28_12_housekeeping.py` — `r2_forensics_inventory()` endpoint | **DUPLICATE** | Track 27.06 already provides `POST /api/admin/r2/lifecycle/scan` + `GET /api/admin/r2/lifecycle/inventory` which do exactly this with better classification and reference resolution. **REMOVE.** |
| `backend/routes/track_28_12_housekeeping.py` — `r2_quarantine_mark()` / `r2_quarantine_list()` endpoints | **DUPLICATE** | Track 27.06's `POST /api/admin/r2/lifecycle/dry-run` + `lib/r2_retention.plan_retention` already provides the certified would-delete list. Any soft-move / operator-approval workflow belongs inside 27.06's flow, not a parallel `r2_quarantine` collection. **REMOVE.** |
| `backend/routes/track_28_12_housekeeping.py` — `legacy_artifacts_inventory()` / `_purge()` / `_restore()` | **REUSABLE** (pattern only) | The soft-move-to-recycle-bin pattern is sound and has value for one-off track-residual cleanup (e.g. Track 15.59). **MERGE** into a small, purpose-scoped `backend/lib/track_residuals.py` if operator later charters a legacy-artifact cleanup track. Otherwise **REMOVE.** |
| `backend/routes/track_28_12_housekeeping.py` — `_r2_client_for_retention` (original R2_* env var wiring) | **REMOVE** | Wrong env-var names; superseded by canonical `photo_storage._client()`. Do not merge. |
| `backend/tests/test_track_28_12_housekeeping.py` | **OBSOLETE** | Tests the duplicate module. Remove when the module is removed. |
| `backend/lib/canonical_status.py` | **CANONICAL** (**not** part of Track 28.12) | This is Track 28.11 code, correctly used by every diagnostics surface. Untouched. |
| `memory/TRACK_28_12_HOUSEKEEPING.md` | **OBSOLETE** | Superseded by `memory/TRACK_28_12_UNAPPROVED_DRAFT.md`. Retain for provenance. |
| `memory/TRACK_28_12_UNAPPROVED_DRAFT.md` | **CANONICAL** (governance record) | Documents scope drift + disposition. Keep. |
| ATT-28.11C-1 fix in `backend/routes/admin_ops.py` | **CANONICAL** (Track 28.11 fix, not 28.12) | Correction of `_STARTED_AT` → `_STARTUP_TS`. Live on prod. Keep. |
| Governance rescan invocation via `POST /api/admin/compliance/scan` | **CANONICAL** (Track 27 governance, not 28.12) | The endpoint pre-existed; the rescan was a one-time operator-authorized data refresh. Keep. |

### Summary of dispositions

* 3 duplicate endpoints → **REMOVE** at next authorized deploy.
* 1 wrong-env-var wiring → **REMOVE**.
* 1 pattern (soft-move recycle bin) → **REUSABLE only if a future track charters legacy-artifact cleanup**; otherwise remove.
* 1 test file → **OBSOLETE** (remove with the module).
* 1 legacy doc → **OBSOLETE** but retained for provenance.
* 2 files → **CANONICAL** (kept — not 28.12).

**Track 28.12 delivers zero net-new capability that Track 27.06 does not already deliver.**

---

## 4 · Decision matrix — applied

| Question | Answer |
|---|---|
| R2 inventory — exists? | Yes, `services/r2_lifecycle/inventory.py`. **Reuse.** |
| Reference discovery — exists? | Yes, `services/r2_lifecycle/references.py`. **Reuse.** |
| Classification with evidence — exists? | Yes, `services/r2_lifecycle/classification.py`. **Reuse.** |
| Dry-run manifest — exists? | Yes, `POST /api/admin/r2/lifecycle/dry-run` + `lib/r2_retention.plan_retention`. **Reuse.** |
| Delete authority — exists? | Yes, `lib/r2_retention.run_retention`. **Reuse.** |
| Storage health — exists? | Yes, `services/r2_lifecycle/health.py`. **Reuse.** |
| Cost + growth intelligence — exists? | Yes, `services/r2_lifecycle/intelligence.py`. **Reuse.** |
| Scheduler for storage — exists? | Yes, backup-scheduler loop in `server.py`. **Reuse.** |
| OCC integration — exists? | Yes, `occ_health_aggregator._eval_storage_health / _eval_recovery_snapshot`. **Reuse.** |
| Diagnostics integration — exists? | Yes, `admin_ops.compute_system_health`. **Reuse.** |
| Quarantine / operator approval workflow — exists? | Partially — Track 27.06's dry-run + operator-approval step is sufficient for a governed cleanup. **Extend Track 27.06** if a formal quarantine holding-window is needed. Do NOT build a parallel quarantine engine. |
| Cross-tenant integration classification (e.g. MaintainX NOT_APPLICABLE) — exists? | Yes, Track 28.11 canonical vocabulary. **Reuse.** |

**No duplicates permitted.** Any Track 27.07 implementation must extend the modules above, not replace or duplicate them.

---

## 5 · Track 27.07 implementation roadmap (extending Track 27.06)

When Track 27.07 is formally chartered, the implementation MUST take exactly this path:

### Phase A — activation of the canonical inventory (no new code)
1. Call `POST /api/admin/r2/lifecycle/scan` on prod to run the full inventory + references + classification cycle. Persists into `r2_lifecycle_objects` (already exists) and `r2_lifecycle_scans` (already exists).
2. Call `GET /api/admin/r2/lifecycle/classification` to review counts by state.
3. Call `GET /api/admin/r2/lifecycle/intelligence` for top prefixes / projects / cost estimates.
4. Call `GET /api/admin/r2/lifecycle/health` for the scored health snapshot.

### Phase B — dry-run manifest (no new code)
5. Call `POST /api/admin/r2/lifecycle/dry-run` for the certified would-delete list. This IS the immutable cleanup manifest the mission requires. Store the returned plan hash in `r2_lifecycle_scans` if not already persisted.

### Phase C — targeted extension to Track 27.06 (small, additive)
6. If a formal quarantine holding-window is required (mission Phase 8-14): add a `POST /api/admin/r2/lifecycle/quarantine` endpoint **inside `admin_r2_lifecycle.py`** that soft-tags approved manifest entries with a 24-72h holding window before the delete authority is authorized to consume them. This is an extension of the existing route file, not a new module.
7. If safety-sampling audit trails are required (mission Phase 7): extend `services/r2_lifecycle/classification.py` to emit sampling evidence per bucket.

### Phase D — execution (existing delete authority)
8. After holding window + operator explicit approval: invoke `run_retention` (existing) scoped to the approved manifest. **Only quarantine-tagged keys** are eligible — the existing tiered pruner respects protected prefixes and won't touch anything outside its plan.

### Phase E — measurement (existing endpoints)
9. Re-run `POST /api/admin/r2/lifecycle/scan` post-cleanup. Diff the sizes. Report reclaimed GB via `GET /api/admin/r2/lifecycle/health`.

### What must NOT happen
- ❌ No new R2 boto3 client wiring anywhere.
- ❌ No new inventory module.
- ❌ No new classification module.
- ❌ No new delete module.
- ❌ No new "housekeeping" or "quarantine" route file.
- ❌ No new Mongo collections outside `r2_lifecycle_objects`, `r2_lifecycle_scans`, `r2_lifecycle_references`, and (if approved in Phase C) a small `r2_lifecycle_quarantine` collection inside the same schema family.

---

## 6 · Gap analysis (post-27.06 vs mission requirements)

The mission text expects a governed cleanup covering 18 phases. Mapping each to Track 27.06 coverage:

| Mission phase | Coverage | Gap |
|---|---|---|
| 1 · Production access | ✅ existing endpoints | none |
| 2 · Full inventory | ✅ `POST /api/admin/r2/lifecycle/scan` | none |
| 3 · Reference discovery | ✅ `services/r2_lifecycle/references.py` with `ReferenceSource` registry | verify all collections in §3.1 of mission are registered |
| 4 · Classification | ✅ `services/r2_lifecycle/classification.py` — 10 states | verify VERIFIED_OWNER / VERIFIED_ORPHAN / BACKUP_PROTECTED etc. are all emitted |
| 5 · Break-the-classifier hunt | 🟡 partial — no explicit false-orphan hunt harness | **small extension in `classification.py`** |
| 6 · Immutable manifest | ✅ `POST /api/admin/r2/lifecycle/dry-run` returns hashed plan | verify hash persistence |
| 7 · Safety sampling | 🟡 partial — no formal 100-largest + 500-random sampler | **small extension in `classification.py`** |
| 8 · Pilot quarantine | 🟡 partial — dry-run works but no holding-window state | **small extension: `POST /api/admin/r2/lifecycle/quarantine`** in `admin_r2_lifecycle.py` |
| 9 · Restore proof | 🟡 partial — quarantine reversal not yet wired | Same file |
| 10-14 · Batch quarantine + validation + holding window + permanent delete | ✅ retention engine handles batches | Add operator-approval + holding-window gate to the existing pipeline |
| 15-16 · Measurement + health recalculation | ✅ existing endpoints | none |
| 17 · Permanent future prevention | ✅ Track 27.06 already exists | none |
| 18 · Regression + closeout | ✅ existing test suite | add tests for new sampling + quarantine states only |

**All gaps are small, focused extensions inside Track 27.06's existing files.** No new module, no new architecture.

---

## 7 · Ownership + operational owner

| Layer | Code owner | Operational owner |
|---|---|---|
| `photo_storage`, domain uploaders | Track 22.1 stewardship (Photo pipeline) | Ops team |
| `services/r2_lifecycle/*` | **Track 27.06 stewardship** | Ops team (executes scans) |
| `routes/admin_r2_lifecycle.py` | Track 27.06 stewardship | Ops team |
| `lib/r2_retention.py` | Track 15.28A stewardship (retention contract) — do not change without operator sign-off | Ops team |
| Backup subsystem | Track 22.1I.1 stewardship | Ops team |
| OCC / Diagnostics integration | Track 28.11 stewardship (canonical status vocabulary) | Ops team |
| Certification manifest impact | Track 27.06 stewardship (extends its rows) | Governance + Ops |
| Track 27.07 execution | Must be a properly-chartered follow-on, extending Track 27.06 only | Operator triggers each phase |

---

## 8 · Success criteria — all satisfied

| Criterion | Status |
|---|---|
| Every storage-related component has a documented owner | ✅ §2, §7 |
| Exactly one approved architecture for lifecycle management | ✅ Track 27.06 (`services/r2_lifecycle/*` + `routes/admin_r2_lifecycle.py` + `lib/r2_retention.py`) |
| Any duplicate / unapproved implementations have a documented disposition | ✅ §3 — Track 28.12 fully classified (REMOVE / OBSOLETE / merged pattern) |
| Future implementation roadmap extends canonical architecture | ✅ §5 — Phases A-E extend Track 27.06 only |
| No production behavior changes made | ✅ zero code changes in this phase |
| No destructive operations enabled | ✅ zero |
| No deployment required | ✅ zero |

---

## 9 · Future-phase gate — canonical answers

| Gate question | Canonical answer |
|---|---|
| The one canonical storage engine | `photo_storage.py` + domain wrappers |
| The one canonical lifecycle engine | `services/r2_lifecycle/*` (Track 27.06) |
| The one canonical delete authority | `lib/r2_retention.py` (Track 15.28A retention contract) |
| The one canonical R2 abstraction | `photo_storage._client()` |
| The one canonical scheduler | Backup-scheduler loop in `server.py` (`backup-scheduler` group, Track 22.1I.1) |
| The one canonical governance owner | Track 27.06 stewardship (extends via `admin_r2_lifecycle.py`) |
| The one canonical diagnostics owner | `admin_ops.compute_system_health` + Track 28.11 canonical vocabulary |
| The one canonical certification owner | `memory/certification_manifest` (Track 27.06 rows) |

---

## 10 · Recommended immediate next step (out of scope for this phase — for operator)

At the next authorized deploy window, **remove** `backend/routes/track_28_12_housekeeping.py` + its `include_router` mount in `server.py` + `backend/tests/test_track_28_12_housekeeping.py`. This eliminates the parallel architecture that Track 28.12 introduced. It is a pure deletion; no behavior change (endpoints are admin-gated and unused).

Then Track 27.07 (proper) can be chartered as extensions to Track 27.06 following §5 above.

---

*Signed off 2026-07-11 · zero code changes · zero deployment · zero destructive operations · scope locked to Track 27.06 canonical architecture.*
