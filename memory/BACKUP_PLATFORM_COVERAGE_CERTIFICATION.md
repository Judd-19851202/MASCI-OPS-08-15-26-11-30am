# BACKUP · Platform-Wide Coverage Certification

**Sprint:** BACKUP-FIX-001 (coverage half)
**Status:** ✅ GREEN — all platform collections captured by auto-discovery; new collections inherit coverage automatically.
**Date:** 2026-02-09

---

## 1. Coverage model — auto-discovery (not allowlist)

The production R2 archive pipeline (`server.py::_build_complete_archive_on_disk`, lines 6062-6215) **enumerates every collection in the live MongoDB** via `sync_db.list_collection_names()` and writes a JSON-per-document into the archive zip.

```python
# server.py:6113
all_collections = sorted(sync_db.list_collection_names())
for coll_name in all_collections:
    if coll_name in BACKUP_EXPLICIT_EXCLUSIONS or coll_name.startswith("system."):
        excluded_logged.append(coll_name)
        continue
    ...
    cursor = sync_db[coll_name].find({}, projection)
    for doc in cursor:
        zf.writestr(f"{kind}/json/{safe_id}.json", _json.dumps(doc, indent=2, default=str))
```

**Implication:** ANY new collection added to MASCI's MongoDB is **automatically backed up** without manual maintenance. The only way a collection can be silently excluded is if a developer adds its name to `BACKUP_EXPLICIT_EXCLUSIONS` (currently 4 items, all documented).

This is confirmed by the iter425 comment block (server.py:6099-6112): "AUTO-DISCOVERY (replaces EXPORTABLE_KINDS allowlist) … so NEW collections inherit R2 coverage automatically with zero allowlist maintenance."

---

## 2. Explicit exclusion list (only 4 items)

```python
# server.py:4560-4565
BACKUP_EXPLICIT_EXCLUSIONS = {
    "system.indexes",          # MongoDB internal
    "usage_events",            # regenerable API telemetry (iter441)
    "health_monitor_runs",     # regenerable scheduler health series (iter441)
    "job_photo_thumb_cache",   # regenerable derivative photo cache (iter441)
}
```

Every exclusion is:
- Documented (`R2_BACKUP_CONTINUITY_AUDIT.md §9` + `BACKUP_CRASH_ROOT_CAUSE_REPORT.md`)
- Regenerable from scratch (telemetry / health metrics / derived cache)
- Logged on every backup run (server.py:6176-6180 — never silent)

**Zero business records are excluded.**

---

## 3. Live coverage matrix (audit moment 2026-06-09 ≈ 11:14 UTC)

| DB | Total non-system collections | Captured | Excluded (intentional) | Coverage % |
|---|---|---|---|---|
| `masci_safety` (production) | **155** | **152** | 3 | **98.1%** |
| `masci_safety_preview` (preview) | **161** | **158** | 3 | **98.1%** |

The 3 intentionally-excluded collections are the 3 listed in §2 (excluding `system.indexes` which Mongo never returns through `list_collection_names()`).

Full per-collection census lives in `BACKUP_COLLECTION_COVERAGE_MATRIX.md`.

---

## 4. Critical platform-area coverage (per directive)

Every category from the directive's "MUST VERIFY COVERAGE FOR" list, confirmed against the live audit:

### Core Platform
| Collection | Captured? | Doc count (prod) |
|---|---|---|
| `users` | ✅ | 5 |
| `user_directory` (multi-portal auth) | ✅ | 42 |
| `pm_users` / `hr_users` / `safety_users` / `dispatch_users` / `shop_users` / `field_leadership_users` / `admin_users` (if present) | ✅ | 3 / 3 / 2 / 3 / 2 / 27 / — |
| `role_templates` | ✅ | 31 |
| `admin_audit` | ✅ | 1,934 |
| `admin_audit_log` | ✅ | 142 |
| `audit_events` | ✅ | 10,971 |
| `workflow_state_events` | ✅ | 2 |
| `integration_sync_logs` | ✅ | 31,999 |
| `integration_error_logs` | ✅ | 0 |
| `mfa_audit_events` | ✅ | 0 (preview: 153) |
| `passkeys` / `user_passkeys` (if present) | ✅ | (auto-included) |

**Sensitive-field redaction** (server.py:4533-4543) strips `password_hash`, `mfa.secret`, `mfa.recovery_codes` from `user_directory` rows during backup — credentials never leave the cluster in backup form, but identity continues to back up.

### Daily Reports
| Collection / Field | Captured? |
|---|---|
| `daily_reports` (112 prod / 741 preview) | ✅ |
| `production[]` rows (Wave-1B) | ✅ (embedded in `daily_reports`) |
| `constraints[]` rows | ✅ (embedded) |
| `materials[]` inbound | ✅ (embedded) |
| `outbound_materials[]` | ✅ (embedded · MM-ENTRY-002 field) |
| `signatures` | ✅ (collection + embedded `prepared_by_signature` ref) |
| Photos / `photo://` refs | ✅ (walked by `_iter_photo_refs`, inlined as actual bytes into the archive) |
| Audit envelope / SHA256 (Wave-1C audit footer) | ✅ (rendered into PDFs from source data; PDF is regenerable from JSON) |
| PDFs themselves | ⚠ Not stored — **regenerated on demand** via `pdf_render.render_record_pdf` from the JSON source. Restore + render yields the same bytes up to the audit footer SHA. |

### Safety
| Collection | Captured? | Doc count (preview) |
|---|---|---|
| `meetings` (Safety meetings) | ✅ | 37 |
| `jhas` | ✅ | 1 |
| `jha_acknowledgements` | ✅ | 1 |
| `inspections` | ✅ | 18 |
| `incidents` | ✅ | 42 |
| `trench_excavations` | ✅ | 710 |
| `trench_safety_assets` | ✅ | 104 |
| `trench_safety_certifications` | ✅ | 64 |
| `trench_safety_deployments` | ✅ | 225 |
| `trench_safety_holds` | ✅ | 1,019 |
| `trench_safety_inspections` | ✅ | 402 |
| `trench_safety_photos` | ✅ | 75 |
| `trench_safety_repairs` | ✅ | 284 |
| `trench_safety_qr_scans` | ✅ | 110 |
| `trench_safety_pulses` | ✅ | 72 |
| `trench_safety_leadership_digests` | ✅ | 8 |
| `safety_training_records` | ✅ | 8 |
| `qaqc_inspections` | ✅ | 12 |
| `signatures` (safety) | ✅ | 107 |
| Attendees, signatures, safety photos | ✅ (embedded in `meetings`/`incidents`/`jhas`, photos walked + inlined) |
| Safety PDFs | ⚠ Regenerable from JSON (same regen pattern as DR PDFs) |

### Operations Actions
| Field | Captured? |
|---|---|
| `operations_actions` collection (77 docs preview) | ✅ |
| Notes, history, status lifecycle | ✅ (embedded in row) |
| Photos / `photo://` refs | ✅ (walked + inlined) |
| Ownership (cross-portal owner pool) | ✅ (stored as structured ref in row) |
| `operational_attachments` | ✅ (32 prod / 48 preview) |

### Material Movement
| Source | Captured? |
|---|---|
| `daily_reports.materials[]` (inbound) | ✅ |
| `daily_reports.outbound_materials[]` (K-MM-1 surface) | ✅ |
| `dispatch_assignments` (true outbound source) | ✅ (1 prod / 368 preview) |
| `daily_reports.production[]` (intentionally NOT mis-classified as outgoing — F1 doctrine) | ✅ (still backed up under daily_reports) |
| Derived endpoint (`/api/material-movement/daily/{proj}/{date}`) | n/a — pure derivation; no separate store to back up |

### Motive / Verification Stack
| Collection | Captured? |
|---|---|
| `asset_mappings` (M-1 + M-DR-1 + MOTIVE-DATA-001) | ✅ (0 prod / 191 preview) |
| `asset_mapping_proposals` (MOTIVE-DATA-001) | ✅ (0 / 0 — newly introduced) |
| `motive_events` | ✅ (0 / 376) |
| `motive_geofences` | ✅ (0 / 67) |
| `motive_users` (if persisted) | ✅ (auto-included if collection ever appears) |
| `operational_locations` (M-3) | ✅ (0 / 67) |
| `operational_events` (M-2 router) | ✅ (0 / 4) |
| `operational_links` | ✅ (0 / 211) |
| `operational_constraints` | ✅ (0 / 0) |
| VER-1 outputs | n/a — Trust State is **derived on read** per VER-1 doctrine; not persisted |
| MOTIVE-DATA-003 operational impact output | n/a — derived on read |

### Documents / Files
| Surface | Captured? |
|---|---|
| Uploaded files (`operational_attachments` + embedded `data_b64`) | ✅ (inline base64 stays inside the JSON dump) |
| Photos (any collection) — `photo://` refs | ✅ via `_iter_photo_refs` walker (iter441 + iter442) — bytes inlined into archive |
| Generated PDFs | ⚠ Regenerable from JSON (no separate storage for PDFs) |
| R2 objects | See `BACKUP_R2_PREFIX_COVERAGE_MATRIX.md` — `photos/` walked through Mongo→R2 path; `safety-docs/`, `legacy-imports/` walked through `operational_attachments` |
| Signed-reference metadata | ✅ (stored in row, captured by JSON dump) |

### Admin / Configuration
| Collection | Captured? | Prod docs |
|---|---|---|
| `jobs_master` | ✅ | 28 |
| `equipment_master` | ✅ | 596 |
| `field_leadership_equipment_catalog` | ✅ | 30 |
| `field_leadership_equipment_makes` | ✅ | 9 |
| `field_leadership_records` | ✅ | 0 |
| `employees` (HR · personnel) | ✅ | 255 |
| `employee_mappings` (Motive↔personnel) | ✅ | 0 |
| `employee_lifecycle_events` | ✅ | 1 |
| `employee_requests` | ✅ | 4 |
| `document_expirations` | ✅ | 1 |
| `po_requests` | ✅ | 1 |
| `integration_settings` (Motive/Twilio/Resend/R2 keys metadata) | ✅ | 2 |
| `integration_wizard_runs` | ✅ | 0 |
| i18n dictionaries | n/a — code-level (`lib/i18n.js`, `guidance/tips_es.py`) — versioned via git, not DB |
| Environment config | n/a — `.env` (out of DB scope; covered by Emergent secrets) |

---

## 5. Future-proof requirement — proof

**Auto-discovery proof:** new collections do not require any code change to be included in the next R2 archive.

**Evidence:**

1. Sprint MOTIVE-DATA-001 introduced the collection `asset_mapping_proposals` today. It is **present in the preview backup_health snapshot's would-be-captured set** without anyone touching backup code. Confirmed by enumeration.
2. The MOTIVE-DATA-001 schema also implicitly extends `asset_mappings`, `operational_locations`, `operational_events`, `operational_links`, `operational_attachments`, `operational_constraints` — all auto-discovered.
3. `_backup_drift_watch` (server.py:6398-6446, iter426) compares each run's `captured_collections` to the previous run and **logs a WARNING** if any collection disappears between runs. Drift surface is `[complete-archive] DRIFT` in supervisor logs. Calm log-only — never silent.

**Failure mode coverage:**
- New collection appears → auto-included. ✅
- New collection ADDED to `BACKUP_EXPLICIT_EXCLUSIONS` → logged on every run; visible in archive `MANIFEST.json` under `explicit_exclusions`. ✅
- Existing collection disappears → drift watcher emits log WARNING. ✅
- New `photo://` reference path (new JSON shape) → MUST be added to `_iter_photo_refs` (server.py:6218). Currently covers: `photos[]`, `items[].photos`, `items[].return_photos`, `items[].original_photos`, `materials[].ticket_photos`, `subcontractors[].photos`, top-level signature fields. If a future schema stores a photo ref at a new JSON path, photos would not be inlined into the archive — but the `photo://` reference STRING is still in the JSON dump, so the R2 photo file remains the source of truth.

This last point is a **known, documented residual risk** captured in `PHOTO_COVERAGE_CERTIFICATION.md`. iter442 closed the previously-known gap. No new gap was introduced by today's sprints.

---

## 6. Known coverage gaps (audit-time inventory)

| Gap | Severity | Status |
|---|---|---|
| Generated PDFs not stored — regenerated from JSON | LOW (deliberate, audit footer is reproducible from JSON + git SHA1) | ACCEPTED per doctrine |
| `usage_events` / `health_monitor_runs` / `job_photo_thumb_cache` not backed up | LOW (regenerable, documented in iter441) | ACCEPTED |
| MFA secrets, password hashes, recovery codes redacted from backups | INTENTIONAL (bearer-equivalent credentials must not leave cluster) | ACCEPTED |
| Restore script is preview-only — production restore would require a documented operator step (clone DB_NAME suffix) | LOW (safety feature) | ACCEPTED |
| New `photo://` path additions in future schemas require updating `_iter_photo_refs` | LOW (R2 source-of-truth remains; JSON dump captures ref) | DOCUMENTED in `_iter_photo_refs` docstring |

**No HIGH or MEDIUM gaps observed.**

---

## 7. Verdict

🟢 **PASS.** Every platform collection is covered by the auto-discovery backup. Today's new MOTIVE / Daily-Report / Operations-Action surfaces inherit coverage automatically with zero allowlist maintenance.

🛑 **STOP CONDITION ENFORCED.** No drift into related work.
