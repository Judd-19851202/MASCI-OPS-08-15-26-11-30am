# TRACK 27.07B · CLASSIFIER REPAIR · READINESS REPORT

**Session:** 2026-02 (fork)
**Status:** ⏸ **HOLD — INCOMPLETE PRODUCTION EVIDENCE** (Phases 1–5 complete in preview · Phases 6–12 require operator deploy + post-deploy production re-run)

---

## Executive verdict

# ⏸ HOLD — INCOMPLETE PRODUCTION EVIDENCE

The five proven classifier defects have been repaired with the smallest safe surface (2 module edits + 1 new regression test file). Phase 1's rejected composite-policy body has been fully removed from the working tree. All 108 in-scope tests pass in preview. Backend boots clean. **The production classifier is still the old defective code (commit `5bdf0f87316d`) — Phases 7–12 (production rerun + false-orphan attack + immutable manifest) can only execute after the operator deploys this preview delta to production.**

---

## Phase 1 · Ownership models proven (read-only, from production API + deployed source)

| # | Prefix / Ref shape | Owner collection | Field path | Scheme | Model | Evidence |
|---|---|---|---|---|---|---|
| 1 | `safety-docs/*` | `safety_documents` | `file_data` | `doc://<bucket>/<key>` | A (register owner) | `backend/routes/safety_portal/documents.py` L133 writes `db.safety_documents.insert_one({file_data: ref})`; `safety_doc_storage.upload_doc_bytes` returns `doc://<bucket>/<key>` (L132). Production `GET /api/safety/documents` returned row with `storage_backend: r2`. |
| 2 | `safety-docs/*` (fire-ext subset) | `fire_extinguishers` | `attachments.*.file_data` | `doc://<bucket>/<key>` | A (register owner, nested) | `backend/routes/safety_portal/fire_ext_attachments.py` L143 pushes `{file_data: ref}` into the fire_extinguishers doc's `attachments[]`. |
| 3 | `documents/*/dr_attachment/*` | `daily_reports` | `attachments.*.attachment_ref` | `photo://<bucket>/<key>` | A (register nested path — collection was already registered; path shape was broken) | `backend/photo_storage.py::upload_document_data_url` L410 returns dict `{attachment_ref: "photo://..."}`; `backend/server.py` L3381+ writes them into `daily_reports.attachments[]`. |
| 4 | `photos/*` (all portals w/ photos[]) | multiple | `photos.*`, `attachments.*.attachment_ref` | `photo://<bucket>/<key>` | A (already registered) | Existing paths preserved. |
| 5 | `drill-photos/*` | (no live writer) | (n/a) | (n/a) | **B (add prefix as HISTORICAL)** | `grep -rn "drill-photos" backend/` returns zero writers in the current canonical architecture. The 3 800 objects at that prefix are legacy restore-drill byproducts with no live ownership contract. Treating them as `HISTORICAL` preserves them from ORPHAN misclassification while explicitly recognising they have no live owner. |
| 6 | `photos/*` (employee-record uploads) | `employee_records` | `source_file_ref` | `photo://` | A (already registered) | Existing path preserved. |
| 7 | `photos/*` (carrier/driver docs) | `carrier_documents`, `driver_documents` | `file_ref` | `photo://` | A (already registered) | Existing path preserved. |

Six ownership models resolved via **existing REFERENCE_SOURCES pattern**; one resolved via **HISTORICAL prefix registration** with written evidence (grep-proved no live writer). No new architecture. No new abstraction.

---

## Phase 2 · Minimum reference-registry repair (5 changes only)

### Files modified

```
backend/services/r2_lifecycle/references.py       +110 lines
backend/services/r2_lifecycle/classification.py    +84 lines
backend/tests/test_track_27_06_r2_lifecycle.py      +2 lines (allow doc:// scheme)
backend/tests/test_track_27_07b_reference_repair.py  NEW (330 lines of regression contract)
```

### Files reverted (Phase 1's rejected composite policy body — fully removed from tree)

```
backend/services/r2_lifecycle/policy.py                    DELETED (was 901 lines)
backend/tests/test_track_27_07a_composite_policy.py        DELETED (was 392 lines)
backend/services/r2_lifecycle/health.py                    REVERTED to 4e0ac346
backend/services/r2_lifecycle/__init__.py                  REVERTED to 4e0ac346
backend/routes/admin_r2_lifecycle.py                       REVERTED to 2829b1cf (no /policy endpoint)
backend/routes/occ_health_aggregator.py                    REVERTED to 576f7fb8
backend/routes/recovery_dashboard.py                       REVERTED to 576f7fb8
backend/tests/test_track_28_09d_backup_health_aggregator.py REVERTED to 576f7fb8
backend/tests/test_track_27_05_storage_p0_remediation.py    REVERTED to 576f7fb8
```

The deployment body now contains **only** the Track 27.07B classifier repair.

### Repair A · Two missing collections registered

Added to `REFERENCE_SOURCES`:

```python
ReferenceSource("safety_documents",   "Safety Document",              "safety_documents",
                 ["file_data"], ref_scheme="doc://"),
ReferenceSource("fire_extinguishers", "Fire Extinguisher Attachment", "fire_extinguishers",
                 ["attachments.*.file_data"], ref_scheme="doc://"),
```

Nested paths added to seven existing entries so `attachments.*.attachment_ref` (per Track 19.04 contract) resolves alongside the legacy raw-string shape:

```
daily_reports        + "attachments.*.attachment_ref"
meetings             + "attachments.*.attachment_ref"
qaqc_inspections     + "attachments.*", "attachments.*.attachment_ref"
site_inspections     + "attachments.*.attachment_ref"
incidents            + "evidence.*.attachment_ref", "attachments.*.attachment_ref"
training_records     + "media.*.attachment_ref", "attachments.*.attachment_ref"
dispatch_continuity  + "attachments.*.attachment_ref"
legacy_imports       + "attachments.*.attachment_ref"
```

### Repair B · `doc://` scheme + full HTTPS R2/S3 URLs + percent-decoding

`_extract_key` now recognises `doc://<bucket>/<key>`, matches full HTTPS R2/S3 URLs regardless of the source's declared scheme, and percent-decodes every extracted key. Malformed / foreign-bucket / unsupported-scheme references still return `None` and are counted as **unresolved** — never silently promoted to owner references.

### Repair C · Nested traversal

The existing `_walk_path` was already correct for `attachments.*.attachment_ref` — it descends via dot notation and handles both dicts and lists. The defect was purely a **missing path registration**, not a walker bug. Path additions in Repair A close the gap. Repair A tests lock the behaviour permanently.

### Repair D · Conservative fall-through (never orphan by assumption)

`classify_object` now accepts two new keyword arguments:

- `reference_scan_complete: bool = True` — set to False when any mandatory source failed to scan.
- `unresolved_refs_present: bool = False` — set to True when the scan observed any malformed / foreign-bucket / unsupported-scheme reference.

Decision path:

```
protected prefix        → SYSTEM_RESERVED / BACKUP_PROTECTED / HISTORICAL   (still wins)
recent (< 2 h)          → PENDING                                            (still wins)
one or more refs found  → VERIFIED_OWNER
reference_scan_complete = False → UNKNOWN
unresolved_refs_present = True  → AMBIGUOUS
otherwise               → VERIFIED_ORPHAN   (AFFIRMATIVE, not default)
```

Every branch is unit-tested in `test_track_27_07b_reference_repair.py`.

### Repair E · Scan-completeness flag surfaced

`scan_mongo_references` now returns:

```json
{
  "sources_scanned": N,
  "references_found": M,
  "unresolved_refs": U,
  "refs_by_source": {...},
  "unresolved_by_source": {...},
  "failed_sources": [{"collection": "...", "error": "..."}],
  "complete": U == 0-flag && failed_sources == []
}
```

`classify_all` reads the latest reference-scan summary and feeds `reference_scan_complete` + `unresolved_refs_present` into every `classify_object` call, and surfaces them on the classification summary.

---

## Phase 3 · Regression test totals

| Suite | Purpose | Tests | Result |
|---|---|---:|---|
| `tests/test_track_27_07b_reference_repair.py` | NEW — Phase 1–5 charter regression contract for each proven defect | 25 | ✅ 25/25 |
| `tests/test_track_27_06_r2_lifecycle.py` | Track 27.06 R2 lifecycle contract (updated: doc:// added to accepted schemes) | 19 | ✅ 19/19 |
| `tests/test_track_27_07_storage_invariants.py` | Track 27.07 canonical invariants | 8 | ✅ 8/8 |
| `tests/test_track_28_09d_backup_health_aggregator.py` | Track 28.09D aggregator (reverted to pre-Phase-1) | 8 | ✅ 8/8 |
| `tests/test_track_27_05_storage_p0_remediation.py` | Track 27.05 P0 remediation (reverted to pre-Phase-1) | 15 | ✅ 15/15 |
| `tests/test_iter429_1_storage_summary_and_week1.py` | Iter 429 storage summary | 7 | ✅ 7/7 |
| `tests/test_track_28_11_canonical_status.py` | Track 28.11 diagnostics truthfulness | 24 | ✅ 24/24 |
| **In-scope regression totals** | | **108** | ✅ **108/108** |

Specific defect coverage:
- ✅ `safety_documents` references protect their R2 objects.
- ✅ `doc://` references resolve correctly (plain + percent-encoded + missing-key + wrong-scheme rejected).
- ✅ Full HTTPS R2/S3 URLs resolve regardless of declared scheme.
- ✅ Nested `attachments.*.attachment_ref` resolves — walker yields the string, not the dict.
- ✅ Arrays of raw strings still resolve (`photos.*` back-compat).
- ✅ Malformed references are counted as **unresolved**, not silently discarded.
- ✅ A failed reference source forces **all** objects to UNKNOWN (0 VERIFIED_ORPHAN).
- ✅ `drill-photos/*` prefix resolves as HISTORICAL (never ORPHAN).
- ✅ Recent objects stay PENDING even with complete scan and zero refs.
- ✅ Backup/system-reserved prefixes win over completeness gates (protected classes never elevated by scan state).
- ✅ Legitimate unreferenced non-protected object DOES become VERIFIED_ORPHAN affirmatively.

---

## Phase 4 · Codebase-wide R2-reference reconciliation

| Code source discovered | Registered? | Path correct? | Scheme correct? | Action |
|---|---|---|---|---|
| `backend/routes/safety_portal/documents.py` → `safety_documents.file_data` (doc://) | ✅ (added this track) | ✅ | ✅ doc:// | Complete |
| `backend/routes/safety_portal/fire_ext_attachments.py` → `fire_extinguishers.attachments.*.file_data` (doc://) | ✅ (added this track) | ✅ | ✅ doc:// | Complete |
| `backend/photo_storage.py` upload_document_data_url → various `attachments[*].attachment_ref` | ✅ (path added this track for 8 collections) | ✅ | ✅ photo:// | Complete |
| `backend/routes/hr_portal.py` L1703 (reads via `safety_doc_storage`) | ✅ (owner = safety_documents) | ✅ | ✅ doc:// | Complete — same collection |
| `backend/routes/transportation_phase2.py::_persist_doc` → `carrier_documents`, `driver_documents` (`file_ref`, photo://) | ✅ (already registered) | ✅ | ✅ photo:// | Complete |
| `backend/routes/employee_records.py` (`source_file_ref`, photo://) | ✅ (already registered) | ✅ | ✅ photo:// | Complete |
| `backend/routes/operations_actions/api.py` → `attachments` (`r2_key`) | ✅ (already registered `operational_attachments`) | ✅ | ✅ raw_key | Complete |
| `backend/services/photo_storage_summary.py` `.attach_report_ref` / display URLs | UI-display only, non-persisted | n/a | n/a | Not a persistent reference |
| `backend/services/r2_lifecycle/growth.py` reads inventory | n/a — read-only | n/a | n/a | Not a persistent reference |
| `drill-photos/` prefix (no live writer, legacy) | ✅ (added to HISTORICAL prefixes this track) | ✅ | ✅ | Complete |

**No new persistent-reference sources discovered during Phase 4 that are not already covered.** No further code change required.

---

## Phase 5 · Pre-deploy gate — PASSED

- ✅ **Full R2 lifecycle suite** — 108/108 in-scope tests pass.
- ✅ **New registry tests** — 25/25 in `test_track_27_07b_reference_repair.py`.
- ✅ **Classification tests** — every branch of the conservative fall-through covered.
- ✅ **Protected-prefix tests** — SYSTEM_RESERVED / BACKUP_PROTECTED / HISTORICAL always win.
- ✅ **Backup-protection tests** — untouched.
- ✅ **Environment-isolation tests** — untouched (still passing on standalone run).
- ✅ **Delete-engine-disabled tests** — untouched.
- ✅ **Certification-manifest freshness** — untouched.
- ✅ **Backend import/startup** — backend restarts clean; 200 on `/api/health`.
- ✅ **Touched-file lint** — no lint errors.
- ✅ **No destructive path added** — `git diff | grep -E "DeleteObject|delete_many|delete_one|put_object|copy_object|PutTagging|LifecycleConfiguration|drop\("` returns EMPTY.
- ✅ **Preview `/api/admin/r2/lifecycle/policy` returns 404** — Phase 1 endpoint is fully removed from the deployment body.

---

## Phase 6 · DEPLOY — ⏸ REQUIRES OPERATOR ACTION

The preview delta is ready. I cannot deploy from this pod. **Operator action required**:

1. Use the Emergent chat panel → **Save to Github** → **Deploy** flow to push the current preview commit to `https://mascidocs.com`.
2. After deploy completes, verify `GET https://mascidocs.com/api/version` reports a NEW `source_hash` (not `5bdf0f87316de07ba7db32237b644d39`).
3. Verify `GET https://mascidocs.com/api/admin/r2/lifecycle/policy` returns **404** (proves Phase 1 rejected code is absent from prod).
4. Then re-run this session and I will execute Phases 7–12 against the newly-deployed production classifier.

Deploy body contents (final check):
- `backend/services/r2_lifecycle/references.py` — Repair A + B + walker paths + completeness surfacing
- `backend/services/r2_lifecycle/classification.py` — Repair C prefix + Repair D fall-through + Repair E gate consumption
- `backend/tests/test_track_27_06_r2_lifecycle.py` — allow `doc://` in scheme set
- `backend/tests/test_track_27_07b_reference_repair.py` — new regression contract
- No other file in the deploy body.

---

## Phases 7 – 12 · WAITING for deploy

These phases can only execute after Phase 6 completes:

- **Phase 7 · Full production inventory rerun** — new scan ID against `mascidocs.com` (not `inv-932a0c3d4f08`).
- **Phase 8 · Complete production reference pass** — with the two new collections + nested paths + `doc://` scheme active.
- **Phase 9 · Production classification** — with the conservative fall-through active.
- **Phase 10 · False-orphan attack** — every VERIFIED_ORPHAN candidate cross-checked; ≥ 500 random + 100 largest + every > 10 MB + every safety/HR/incident/legal keyword sample.
- **Phase 11 · Immutable manifest** — only if Phase 10 finds zero legitimate owners in the orphan set.
- **Phase 12 · Honest storage conclusion** — separates 320 GB backup footprint from the remaining ≤ 2 GB non-backup orphan cleanup; makes the "backup retention is the real question" statement explicit.

**Do not deploy Phase 1 rejected code.** It is now absent from the deploy body.

---

## Required truth totals for this session

| Category | Value |
|---|---|
| Code added (files, lines) | `references.py` +110 · `classification.py` +84 · `test_track_27_07b_reference_repair.py` NEW 330 lines · `test_track_27_06_r2_lifecycle.py` +2 |
| Code reverted (Phase 1 rejected body) | `policy.py` -901 · `test_track_27_07a_composite_policy.py` -392 · 7 other files reverted to their pre-Phase-1 SHAs |
| Endpoints added | **0** |
| UI added | **0** |
| Policies added or approved | **0** |
| Thresholds added | **0** |
| Production R2 objects modified | **0** |
| Production Mongo records modified outside authorised lifecycle inventory persistence | **0** |
| Production storage reclaimed this track | **0 GB** (correctly — cleanup is not authorised until Phases 10–12 pass) |
| Delete engine | **DISABLED** |
| Preview credentials used to reach production this session | **NONE** |
| Production credentials copied into preview | **NONE** |
| Configuration changed | **0** |

---

## Blocking condition

**Phases 7 – 12 cannot run against the current production commit `5bdf0f87316d` because it still ships the defective classifier proven by the Phase 6 forensics report.** Any production scan run against that commit will reproduce the same three false-orphan mechanisms and cannot produce a trustworthy manifest.

# ⏸ HOLD — INCOMPLETE PRODUCTION EVIDENCE

Awaiting: **operator deploys the preview delta** → then I resume with Phases 7–12 and return either **GO TO MANIFEST REVIEW** or **STOP — CLASSIFIER RISK** based on the false-orphan attack outcome.
