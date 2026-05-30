# PHOTO_COVERAGE_CERTIFICATION.md

**Batch:** OMEGA · Operational Perfection Track · Priority 2
**Date:** 2026-05-30 (UTC)
**Mode:** Read-only forensic + design certification. **NO code changes** (per operator: "No implementation yet" elsewhere in directive; analogous here — design + remediation plan only).
**Anchor evidence:** the 326 MB iter441-built production archive (`MASCI_complete_backup_2026-05-30_231056Z.zip`, R2 key `backups/auto-90d/...`) + the `_iter_photo_refs` walker at `server.py:5722-5742`.

---

## 0 · Goal

**100 % photo recoverability** of every operational photo stored in production Mongo via a `photo://` reference, regardless of which JSON path holds the reference.

**Current coverage:** 609 of 672 (90.6 %).
**Gap:** **63 references** at three JSON paths the archive walker does not visit.
**Acceptance criterion for closure:** archive-wide audit returns `unique_keys_referenced == unique_keys_in_archive` (i.e. zero "missing").

---

## 1 · Forensic enumeration of every uncovered reference

Read-only walk of all 86 production `daily_reports` documents (`masci_safety` Atlas, 2026-05-30T23:25Z), all 7 incidents, all 23 meetings, all 25 equipment_inspections, all 40 operational_attachments, all 6 job_hazard_files. `photo://` references collected and classified by JSON path:

### 1.1 · Covered paths (already walked by `_iter_photo_refs` · server.py:5722-5742)

| Collection | JSON path | Refs (prod) | Code coverage |
|---|---|---:|---|
| `daily_reports` | `photos[]` | 598 | ✅ line 5727 |
| `meetings` | `photos[]` | 11 | ✅ line 5727 |
| `incidents` | `photos[]` | 0 (still inline base64) | ✅ line 5727 |
| `equipment_inspections` | `items[].photos[]` | 0 (still inline base64) | ✅ line 5734-5737 (`photos`) |
| `equipment_inspections` | `items[].return_photos[]` | 0 | ✅ line 5737 (`return_photos`) |
| `equipment_inspections` | `items[].original_photos[]` | 0 | ✅ line 5737 (`original_photos`) |
| **Covered subtotal** | — | **609** | — |

### 1.2 · Uncovered paths (NOT walked — the 63-photo gap)

| Collection | JSON path | Refs (prod) | Storage location (R2 bucket) | Backup status | Restore status | Drill validation |
|---|---|---:|---|---|---|---|
| `daily_reports` | `materials[].ticket_photos[]` | **36** | `photo://masci-hub/photos/...` (live R2) | 🟡 ref preserved in JSON dump; binary NOT inlined | 🟡 restore depends on R2 surviving (single-source) | ❌ no drill walks this path |
| `daily_reports` | `subcontractors[].photos[]` | **26** | same | same | same | ❌ |
| `daily_reports` | `prepared_by_signature` (top-level string) | **1** | same | same | same | ❌ |
| **Uncovered subtotal** | — | **63** | — | — | — | — |

**Grand total:** 672 = 609 + 63 (matches archive integrity audit in `COMPLETE_BACKUP_VALIDATION_REPORT.md §2.7`).

### 1.3 · Per-reference evidence sample (5 of 63)

| # | Doc id | JSON path | R2 key |
|---|---|---|---|
| 1 | `e000f6a2-a5f1-4d6e-bd2c-1b0c693c…` | `subcontractors[].photos[]` | `photos/2026/05/dr_e000f6a2-a5f1-4d6e-bd2c-1b0c693c_sub/b2f6061e8ac943b095f6324a8e9f3fd5.jpg` |
| 2 | `0fa21157-68e5-42d7-9634-343b61e2…` | `materials[].ticket_photos[]` | `photos/2026/05/dr_0fa21157-68e5-42d7-9634-343b61e2_mat/8cf2499cfb2e4753812f1a7fe14b953e.jpg` |
| 3 | `6cab8b26-76cb-41ae-a241-2f0d2bcf…` | `materials[].ticket_photos[]` | `photos/2026/05/dr_6cab8b26-76cb-41ae-a241-2f0d2bcf_mat/de1dbe8e7c744118bf9e492333370fa2.jpg` |
| 4 | `e1e3c852-5901-42c7-b5c8-155d419c…` | `subcontractors[].photos[]` | `photos/2026/05/dr_e1e3c852-5901-42c7-b5c8-155d419c_sub/62ca26aca9344ebf99fe47778844617f.jpg` |
| 5 | `4cab04c6-a17d-47d6-a02c-29425…` | `prepared_by_signature` | `photos/2026/05/daily_reports-4cab04c6-a17d-47d6-a02c-2942538cfcd5-prepared_by_signature/9cd2394090864dad8e00e8d91917e238.png` |

---

## 2 · Recoverability matrix · per-pillar (today vs after closure)

### 2.1 · Storage path (where the binary lives)

| Field | Today | After closure |
|---|---|---|
| Primary storage | Cloudflare R2 bucket `masci-hub`, key prefix `photos/2026/...` | unchanged |
| Replication | Cloudflare R2 internal redundancy | unchanged |
| Lifecycle | No expiration on `photos/*` (the `auto-90d` lifecycle rule scopes only to `backups/auto-90d/*`) | unchanged |
| Single point of failure? | 🟡 Yes — single bucket | unchanged (separate cross-region mirror = future P3) |

### 2.2 · Backup path (how a binary enters the archive)

| Field | Today (covered paths) | Today (uncovered paths) | After closure |
|---|---|---|---|
| Reference preserved in JSON dump | ✅ yes | ✅ yes (the `photo://` URL is preserved verbatim) | ✅ yes |
| Binary inlined into archive `photos/<key>` | ✅ yes | ❌ no | ✅ yes |
| Manifest reports inlined count | ✅ yes (`inlined_photos`) | counted only for covered paths | ✅ yes (will rise from 609 → 672 in next archive build) |
| Manifest reports failed downloads | ✅ yes (`failed_photos`) | n/a — not attempted | ✅ yes |

### 2.3 · Restore path (how a binary is recovered)

| Field | Today (covered) | Today (uncovered) | After closure |
|---|---|---|---|
| If R2 is alive | Re-fetched via `photo://` resolve in app | Re-fetched via `photo://` resolve in app | unchanged (R2 is primary) |
| If R2 is dead + archive present | Restored from `photos/<key>` in archive | **❌ NOT RECOVERABLE — ref in JSON points nowhere** | ✅ Restored from `photos/<key>` in archive |
| If both R2 and archive lost | ❌ unrecoverable | ❌ unrecoverable | ❌ unrecoverable (out of scope) |

### 2.4 · Drill validation path (how we prove restorability)

| Field | Today | After closure |
|---|---|---|
| `scripts/restore_drill.py --restore-photos` flag | Walks archive `photos/` prefix and re-uploads to R2 | unchanged — relies on archive having all 672 binaries (this is what closure delivers) |
| Drill audit step | Compares Mongo `photo://` refs vs R2 keys post-restore | Should be extended to also assert `mongo_refs == archive_inlined` before R2 push |
| Drill cadence | Manually invoked (Batch G executed; not scheduled) | See `AUTOMATED_RESTORE_DRILL_SPEC.md` (Priority 4) for proposed automation |

---

## 3 · Closure plan (design only · NOT implemented this batch)

### 3.1 · Surgical code change (proposed, ~10 LOC)

**File:** `/app/backend/server.py` — extend `_iter_photo_refs` at lines 5722-5742.

**Diff sketch:**

```python
def _iter_photo_refs(doc):
    """Yield every photo:// reference found anywhere in a Mongo document.
    Covers top-level `photos` arrays AND nested
    items[].photos / items[].return_photos for equipment forms
    AND (iter442) materials[].ticket_photos / subcontractors[].photos
    /signature fields for daily_reports.
    """
    if not isinstance(doc, dict):
        return

    # iter441 covered:
    photos = doc.get("photos")
    if isinstance(photos, list):
        for p in photos:
            if isinstance(p, str): yield p

    items = doc.get("items")
    if isinstance(items, list):
        for it in items:
            if not isinstance(it, dict): continue
            for fld in ("photos", "return_photos", "original_photos"):
                v = it.get(fld)
                if isinstance(v, list):
                    for p in v:
                        if isinstance(p, str): yield p

    # iter442 (proposed) — close the 63-ref gap on daily_reports
    materials = doc.get("materials")
    if isinstance(materials, list):
        for m in materials:
            if not isinstance(m, dict): continue
            v = m.get("ticket_photos")
            if isinstance(v, list):
                for p in v:
                    if isinstance(p, str): yield p

    subs = doc.get("subcontractors")
    if isinstance(subs, list):
        for s in subs:
            if not isinstance(s, dict): continue
            v = s.get("photos")
            if isinstance(v, list):
                for p in v:
                    if isinstance(p, str): yield p

    # Top-level signature fields (string `photo://` refs)
    for fld in ("prepared_by_signature", "reporter_signature", "supervisor_signature", "conductor_signature"):
        v = doc.get(fld)
        if isinstance(v, str) and v.startswith("photo://"):
            yield v
```

**Properties:**
- Reversible (delete the 3 new blocks → identical iter441 behavior).
- No schema change.
- No env change.
- No new endpoint.
- Inherits to both pipelines (Pipeline A `_build_backup_zip_to_path` + Pipeline B `_build_complete_archive_on_disk`) because both call the same function.
- Backward-compatible: if a doc happens to NOT have these fields, the iterators yield nothing (unchanged behavior).

### 3.2 · Memory impact estimate

| Metric | iter441 baseline (prod) | iter442 projection |
|---|---:|---:|
| Inlined photos | 609 | **672** (+63) |
| Inlined photo bytes | 281.76 MB | ~313 MB (+~31 MB, assuming ~500 KB avg per ticket/signature photo) |
| Archive size | 326.0 MB | ~358 MB (+~32 MB; signatures compress well) |
| Build wall time | ~4 min 28 s | ~4 min 50 s (+22 s for 63 extra R2 GetObject + writestr) |
| Peak RSS | ~284 MB (drill) | ~290 MB (peak driven by ZipInfo count and largest single doc, both barely changed) |
| Worker stability | ✅ same | ✅ same |
| `backup_health` ok=True | ✅ | ✅ |

iter442 is **less aggressive** than iter441 from a worker-stability standpoint; the OOM-headroom delivered by iter441 (-383.5 MB peak RSS) absorbs the +6 MB iter442 cost effortlessly.

### 3.3 · Drill closure plan (for `scripts/restore_drill.py`)

Extend `restore_drill.py --restore-photos` audit to assert two invariants:

1. `len(unique_refs_in_archive_json) == len(photos_directory_entries)` — archive self-consistency.
2. Sample of 5 random refs per JSON path (including the 4 new paths) → archive contains the corresponding `photos/<key>` entry.

This proves the iter442 walker change actually inlines what the docs reference. ~30 LOC addition; no new dependencies.

---

## 4 · Acceptance test (post-iter442 deploy)

After authorized deploy of iter442:

1. Trigger one manual complete-archive on prod via `/admin/system` → "Run Complete Backup Now".
2. Read latest `backup_health` row: `inlined_photos` should be ≥ 672 (≈ 633-700 depending on data drift between iter441 build and this build).
3. Download archive from R2 with boto3, walk all `photo://` refs in all JSON entries, compare to `photos/` archive entries. Assert: every unique key referenced has a matching archive entry.
4. Run `scripts/restore_drill.py --backup <new-key> --target-db masci_restore_drill_iter442 --restore-photos` and confirm all 672 unique photo keys round-trip.
5. Update `DISASTER_RECOVERY_VALIDATION_MATRIX.md §1` row #2 (DR Photos) from 🟡 to 🟢 on the "Verified" pillar.

---

## 5 · Risk register · post-closure

| Risk | Severity | Mitigation |
|---|---|---|
| Future schema adds another nested photo path | 🟡 ongoing | Add a unit test that scans random prod docs for any string matching `photo://` not yielded by `_iter_photo_refs` (post-iter442 hardening, ~20 LOC) |
| `photo://` reference points to a key no longer in R2 (deleted out-of-band) | 🟡 unchanged | Already caught by `failed_photos` counter in MANIFEST; nightly archive surfaces drift |
| Inlined photo bytes grow until archive exceeds worker disk | 🟡 monotonic | Compaction strategy: keep 7 daily archives in `auto-90d`; lifecycle prunes the rest at 90 days |

---

## 6 · Recoverability scorecard (current vs target)

| Surface | Current | After iter442 closure | After Priority 4 automated drill |
|---|---|---|---|
| `photo://` refs walked by archive code | 9/12 fields (75 %) | 12/12 fields (100 %) | 100 % + assertion-tested every run |
| Unique R2 keys inlined / referenced | 609 / 672 (90.6 %) | 672 / 672 (100 %) | 100 % verified per drill run |
| Single-zip restore property | partial (R2 must survive for the 63 gap) | **fully self-contained** | unchanged |
| Drill validation cadence | manual (Batch G executed) | manual | automated weekly (proposed) |

---

## 7 · Stop-condition compliance

- ✅ Read-only forensic + design only · NO code committed in this batch
- ✅ Closure plan is reversible, evidence-backed, and scoped to ~10 LOC of `_iter_photo_refs`
- ✅ No touch on scheduler / retention / cadence / frequency / R2 lifecycle / notifications / workflows / UI / DVIR / accountability
- ✅ Production data inspected read-only via Atlas; no writes
- ✅ Operator must explicitly authorize iter442 as a separate batch before any code ships

---

_End of PHOTO_COVERAGE_CERTIFICATION.md_
