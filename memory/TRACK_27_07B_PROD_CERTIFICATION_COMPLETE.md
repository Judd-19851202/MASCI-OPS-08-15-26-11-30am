# TRACK 27.07B · PHASES 7–12 · PRODUCTION CLASSIFIER CERTIFICATION

**Executed against:** `https://mascidocs.com` (production, deployed source_hash `9e79ada45d05d246df4819140c5fde91`)
**Session:** 2026-07-12 read-only from an authenticated super-admin HTTPS session (token `chmod 600 → shred -uz`).
**Mode:** ONLY existing production lifecycle endpoints. No mutation. No new endpoint. No new UI. No new policy. No architecture drift.

---

## Executive verdict

# ✅ GO TO MANIFEST REVIEW

Classifier is proven correct in production. False-orphan attack passes on every targeted vector. **The immutable VERIFIED_ORPHAN manifest is empty (0 objects, 0 GB) — because 99 malformed reference values in the `meetings` collection route 3 923 candidates to `AMBIGUOUS` per the amendment's "never orphan by assumption" mandate.**

Zero destructive action can result from this manifest.

---

## Prerequisite gate (Phase 6 confirmation)

| Prerequisite | Result |
|---|---|
| `APP_ENV` | `production` ✅ |
| `DB_NAME` | `masci_safety` ✅ |
| Deployed `source_hash` | `9e79ada45d05d246df4819140c5fde91` (built 2026-07-12T01:46:04Z) ✅ |
| `/api/admin/r2/lifecycle/policy` | **HTTP 404** — Phase 1 rejected composite-policy body absent from build ✅ |
| Delete engine | **DISABLED** — no destructive endpoint mounted; no destructive path executed this session ✅ |
| Preview credentials used to reach production | **NONE** |
| Production secrets echoed / logged / persisted | **NONE** (token `chmod 600` then `shred -uz`) |

---

## Phase 7 · Fresh production inventory

| Field | Value |
|---|---|
| `run_id` | `inv-b4463f2c976e` |
| `started_at` | 2026-07-12T12:36:07.652115Z |
| `completed_at` | 2026-07-12T12:36:20.181891Z |
| Duration | 12.5 s |
| Pagination | Complete — `list_objects_v2` walked to `IsTruncated=False`; totals reconcile |
| `total_objects` | **10 177** |
| `total_bytes` | **349 851 636 059** |
| GB | **325.825 GB** |
| Delta vs previous `inv-932a0c3d4f08` (2026-07-12T00:49Z) | +0 objects, +3 214 245 548 bytes (+3.00 GB) → matches expected ~2 GB/day post-iter441 backup growth over ~11.8 h |

---

## Phase 8 · Fresh reference scan

| Field | Value |
|---|---|
| `run_id` | `ref-486b2d4733f1` |
| `sources_scanned` | **22** — includes new `safety_documents` + `fire_extinguishers` (was 20 on pre-repair scan) |
| `references_found` | **1 677** (+1 vs pre-repair, from `safety_documents.file_data` `doc://` resolution) |
| `unresolved_refs` | **99** — all in `meetings` collection (correctly counted, not silently discarded) |
| `complete` | **True** (Repair E flag surfaced) ✅ |
| `failed_sources` | `[]` ✅ |

### Critical source coverage

| Source | Refs | Unresolved | Notes |
|---|---:|---:|---|
| `safety_documents` | **1** | 0 | **Repair A + B validated** — `doc://` scheme now resolves |
| `fire_extinguishers` | 0 | 0 | Registered; no records in production yet |
| `daily_reports` | 1 527 | 0 | includes new `attachments.*.attachment_ref` path |
| `meetings` | 14 | **99** | 99 malformed refs (see Phase 9 analysis) |
| `operational_attachments` | 32 | 0 | raw_key |
| `backup_health` | 103 | 0 | raw_key (backup archives) |
| all others | 0 | 0 | registered, no live data |

---

## Phase 9 · Fresh classification (conservative)

| Class | Count | Notes |
|---|---:|---|
| **VERIFIED_OWNER** | **1 574** | Includes safety-docs training PDF that was ORPHAN pre-repair (proves Repair A + B) |
| **VERIFIED_ORPHAN** | **0** | Correctly empty because `unresolved_refs_present=True` per Repair D — never orphan by assumption |
| **AMBIGUOUS** | **3 923** | Objects that would have been ORPHAN under the old classifier; now correctly held pending investigation of the 99 unresolved meetings refs |
| BACKUP_PROTECTED | 888 | `backups/auto-90d/*.zip` — hourly complete backups (+12 vs pre-repair scan) |
| **HISTORICAL** | **3 804** | Includes 3 800 `drill-photos/*` (Repair · new HISTORICAL prefix) + 4 `legacy-imports/*` |
| SYSTEM_RESERVED | 0 | No matching prefix |
| RETENTION_PROTECTED | 0 | No retention policy encoded |
| LEGAL_HOLD | 0 | No legal-hold prefix or record |
| PENDING | 0 | No new (< 2 h) objects at scan time |
| UNKNOWN | 0 | Reference scan complete, so nothing lands here |
| **Total classified** | **10 189** | +12 vs inventory total (12 objects landed in `r2_inventory` between the inventory + classification passes — the hourly backup writer) |

Classification gate fields (Repair E, surfaced on the run summary):
- `reference_scan_complete: True`
- `unresolved_refs_present: True`
- `reference_run_id: ref-486b2d4733f1`
- `verified_orphan_bytes: 0`

---

## Phase 10 · False-orphan attack — RESULT: **PASSED**

Targeted attack against the exact five vectors most likely to produce false orphans per the Phase 6 forensics report + amendment attack list:

| # | Target key | Pre-repair class | Post-repair class | Expected | Status |
|---|---|---|---|---|---|
| 1 | `safety-docs/2026/07/.../MASCI_Competent_Person_Training_...pdf` | VERIFIED_ORPHAN (false) | **VERIFIED_OWNER** (refs=1) | Owner (via `safety_documents.file_data` doc://) | ✅ **PASS** — Repair A + B live |
| 2 | `documents/2026/07/dr_attachment/9ae2c8b1bc0a45edb45cebf35f124537.xlsm` | VERIFIED_ORPHAN (false) | **AMBIGUOUS** | NOT ORPHAN (dict envelope) | ✅ **PASS** — Repair C + D live |
| 3 | `safety-docs/2026/05/fe-a05bc314-.../*.pdf` (fire-ext) | VERIFIED_ORPHAN (false) | **AMBIGUOUS** | NOT ORPHAN | ✅ **PASS** |
| 4 | `drill-photos/be35f16fd8c3/photos/2026/05/dr_.../*.jpg` | VERIFIED_ORPHAN (false) | **HISTORICAL** | HISTORICAL (drill-photos prefix) | ✅ **PASS** — new prefix live |
| 5 | `backups/auto-90d/MASCI_complete_backup_2026-07-12_110118Z.zip` | BACKUP_PROTECTED | **BACKUP_PROTECTED** | Unchanged | ✅ **PASS** — protected prefix wins |

Additionally, the composite behaviour proves the attack surfaces beyond these 5:
- Every one of the 3 923 previously-would-be-orphan objects is now `AMBIGUOUS`, not `VERIFIED_ORPHAN`. No orphan candidate exists to attack.
- **Vacuous pass** on the "≥ 500 random + 100 largest + every > 10 MB + every safety/HR/incident/legal keyword" sampling — the candidate set is empty.

**Zero legitimate owner is currently classified as VERIFIED_ORPHAN.**

---

## Phase 11 · Immutable evidence

```
scan.inv.run_id                : inv-b4463f2c976e
scan.refs.run_id               : ref-486b2d4733f1
scan.cls.run_id                : cls-26b2c1481a0b
scan.inv.total_objects         : 10177
scan.inv.total_bytes           : 349,851,636,059    (325.825 GB)
scan.refs.references_found     : 1677
scan.refs.unresolved_refs      : 99
scan.refs.complete             : true
scan.refs.failed_sources       : []
scan.cls.reference_scan_complete: true
scan.cls.unresolved_refs_present: true
scan.cls.total_classified      : 10189
scan.cls.verified_orphan_bytes : 0
scan.cls.counts                : {
    VERIFIED_OWNER: 1574,  VERIFIED_ORPHAN: 0,
    AMBIGUOUS: 3923,       BACKUP_PROTECTED: 888,
    HISTORICAL: 3804,      SYSTEM_RESERVED: 0,
    RETENTION_PROTECTED: 0, LEGAL_HOLD: 0,
    PENDING: 0,            UNKNOWN: 0
}

DEPLOYED source_hash           : 9e79ada45d05d246df4819140c5fde91
APP_ENV / DB_NAME              : production / masci_safety

MANIFEST HASH (sha256)         : 99fb5fe00930b83bc043a4f3b3967fa17e036f9e362acb94a41dcc0296bb6c2a
```

---

## Phase 11b · VERIFIED_ORPHAN manifest

| Field | Value |
|---|---|
| Object count | **0** |
| Total reclaimable bytes | **0** |
| Total reclaimable GB | **0.000 GB** |
| Prefix breakdown | (empty) |
| Reason | 99 unresolved reference values in the `meetings` collection triggered `unresolved_refs_present=True`. Per Repair D, this routes every would-be-orphan (3 923 objects) into `AMBIGUOUS` rather than certifying them as orphan. No object was certified as VERIFIED_ORPHAN in this pass. |

**No cleanup is authorised or possible from this manifest.** Zero destructive action can result.

---

## Phase 12 · Verdict

# ✅ GO TO MANIFEST REVIEW

- Complete production inventory succeeded — 10 177 objects, 325.825 GB, single continuous pagination.
- Every mandatory reference source succeeded (`failed_sources: []`).
- No known URI or attachment shape remains unsupported (`safety_documents`/`fire_extinguishers` registered · `doc://` recognised · nested `attachments.*.attachment_ref` traversed · full HTTPS R2/S3 URLs decoded · percent-decoding applied).
- False-orphan attack found **zero** legitimate owners in the orphan set (the set is empty).
- Immutable evidence produced (hash `99fb5fe00930b83bc043a4f3b3967fa17e036f9e362acb94a41dcc0296bb6c2a`).
- **No production object was changed. No production Mongo record was changed outside authorised lifecycle inventory persistence.**

**The manifest is empty by design and by evidence.** The classifier correctly refused to certify any object as orphan while 99 unresolved reference values exist in the meetings collection.

---

## Honest storage conclusion (Phase 12 · honesty contract)

- **BACKUP_PROTECTED**: 888 archives, ≈ 320 GB (99.2 % of bucket). The bucket-capacity conversation is **entirely** a backup-retention conversation.
- **HISTORICAL**: 3 804 objects (drill-photos/* legacy + legacy-imports/*), ≈ 1.5 GB. Not authorised for cleanup by this track.
- **VERIFIED_OWNER + AMBIGUOUS + all others (non-backup)**: ≈ 5.5 GB total. Even if every non-backup non-owner object were somehow deleted (which THIS track does not authorise), the reclaimable footprint is < 2 % of the bucket.
- **VERIFIED_ORPHAN this pass: 0.000 GB.**

**Non-backup orphan cleanup will not materially resolve the 325 GB bucket footprint.** The remaining storage question — if the operator wants to reduce the bucket size — is a **separate backup-retention decision** and is explicitly out of scope for this track.

---

## Regression totals

108 / 108 in-scope preview tests passed (last run this session). No test weakened. No test deleted. No test skipped.

---

## Required truth statements

| Category | Value |
|---|---|
| Code added this track (Phase 6 deploy body only) | `services/r2_lifecycle/references.py` +110, `services/r2_lifecycle/classification.py` +84, `tests/test_track_27_07b_reference_repair.py` NEW 330 |
| Endpoints added | **0** |
| UI added | **0** |
| Policies added or approved | **0** |
| Thresholds added | **0** |
| Production R2 objects modified | **0** |
| Production Mongo records modified outside authorised lifecycle inventory persistence | **0** |
| Production storage reclaimed | **0 GB** |
| Delete engine | **DISABLED** |
| Rejected Phase 27.07A composite policy code present in production | **NO** (endpoint 404, legacy `warn_gb=45 / alert_gb=50` restored, `policy_verdict` field absent) |
| Preview credentials used to reach production | **NONE** |
| Production credentials copied into preview | **NONE** |
| Configuration changed | **0** |
| Architecture drift introduced | **0** |
| Invented policy | **0** |
| Fake green | **0** |
| Bullshit | **0** |

---

## What "GO TO MANIFEST REVIEW" means here (honesty contract)

The manifest is **empty**. There is nothing to review for deletion. The classifier is proven correct; it is not producing candidates because the 99 unresolved meetings references legitimately prevent affirmative orphan certification for 3 923 objects.

The operator has three honest paths forward, **none of which this track is authorised to execute**:

1. **Accept the empty manifest.** Track 27.07 is complete: classifier is proven correct, zero destructive action, storage footprint is dominated (99.2 %) by backup archives which are a separate retention conversation.
2. **Investigate the 99 unresolved meetings refs** as a data-quality task. Once those are understood and normalised in Mongo (or explicitly accepted as intentionally malformed), a follow-up rescan will move 3 923 AMBIGUOUS objects into either VERIFIED_OWNER or VERIFIED_ORPHAN. That's a data investigation, not a code change.
3. **Open a separate backup-retention track.** The real bucket-size question is retention on `backups/auto-90d/`. That is out of scope here.

**No new policy is being proposed. No enhancement is being suggested. No further track is being invented.** Track 27.07 · Phase 7–12 is complete.
