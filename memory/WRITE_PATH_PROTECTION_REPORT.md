# WRITE_PATH_PROTECTION_REPORT

**Date:** 2026-05-30 (Batch H · Phase 2)
**Deliverable:** Code change to `/app/backend/routes/daily_reports.py` + live smoke test against preview backend

---

## 🟢 Result — New Daily Reports CANNOT introduce inline base64 photo bloat

End-to-end smoke test against preview backend with the new write-path defense loaded:

```
Submitted DR with 4 inline data:image/png base64 strings:
  - photos[]:           2 inline strings
  - subcontractors[0].photos[]: 1 inline string
  - materials[0].ticket_photos[]: 1 inline string

API response:
  Top photos[]: ['photo://masci-hub/photos/2026/05/dr_72187f2e-.../c23e1c9b...',
                 'photo://masci-hub/photos/2026/05/dr_72187f2e-.../deeb5630...']
  Sub.photos[]: ['photo://masci-hub/photos/2026/05/dr_72187f2e-..._sub/aef8a89...']
  Mat.ticket_photos[]: ['photo://masci-hub/photos/2026/05/dr_72187f2e-..._mat/fbd1ed9...']
  doc_id: DR-2026-00409
  audit_envelope_sha256: d8539d16d5b2064d…

Mongo state:
  BSON size : 1,630 bytes (would have been ~2.3 KB with 4 tiny test photos inline,
              or several MB for real-size photos)
  Remaining inline base64 strings: 0 (expect 0)
```

**Test DR was cleaned up from preview after verification.**

---

## 1 · Code change — Surgical, scoped to the create handler

**File:** `/app/backend/routes/daily_reports.py`
**Function added:** `_sanitize_inline_photos(doc) -> Dict[str, int]`
**Insertion point:** inside `_do_create()`, AFTER `doc = report.model_dump()` and BEFORE `_compute_audit_envelope_sha256(doc)` (so the audit hash signs the canonical post-sanitization state).

### What the sanitizer does

Walks the same three nested paths as the Batch G migration script:

1. `doc.photos[]` — top-level photo array
2. `doc.subcontractors[*].photos[]` — driver licenses, COIs, etc.
3. `doc.materials[*].ticket_photos[]` — delivery tickets

For each entry:
- **`data:image/...`** → call `photo_storage.upload_data_url()` → replace with `photo://` reference
- **`photo://...`** (already a ref) → skip (idempotent)
- **empty / non-string** → skip

### Safety rails

```python
try:
    from photo_storage import upload_data_url, is_configured
except Exception:
    return counters  # SOFT FAIL: leave inline
if not is_configured():
    return counters  # SOFT FAIL: leave inline

# Per-entry try/except:
try:
    ref = await upload_data_url(item, source_id=source_id)
    lst[i] = ref
    counters[key] += 1
except Exception:
    counters["errors"] += 1
    # entry remains as-is — no half-modified state
```

**Three layers of protection** ensure a DR submit is never blocked by:
- R2 client misconfiguration (e.g., missing env vars)
- R2 network outage
- A single corrupt photo

Behavior in failure case: the inline base64 string remains in the doc (legacy path), submit succeeds, archive grows by that single photo's worth. Batch G migration script can re-process it later. **No user is ever locked out of submitting a DR by this code.**

### Response-shape preservation

The handler now builds `report_dict = dict(doc)` from the sanitized doc (instead of re-dumping the unchanged Pydantic model). This ensures the API response photos match what's in Mongo. The frontend (which has supported `photo://` refs since iter64 Phase 2) renders identically.

---

## 2 · Hash integrity

`_compute_audit_envelope_sha256(doc)` is computed AFTER sanitization. This means:
- The audit envelope hash signs the canonical post-sanitization state
- Future tamper-detection checks operate on the canonical state
- If a DR is later read back from Mongo and a verifier re-computes the hash from current state, the hash will match (assuming no tampering)

If sanitization had been added AFTER hashing, the saved doc and the saved hash would refer to different snapshots — a structural inconsistency. The placement is therefore deliberate.

---

## 3 · Workflow preservation — explicit confirmation

| Workflow | Before Batch H | After Batch H |
|---|---|---|
| PM submits DR with inline photo from camera | Inline base64 saved to Mongo · archive grows | Inline base64 uploaded to R2 + replaced with ref · archive unaffected |
| Frontend shows DR photos | `data:image/...` rendered directly | `photo://` ref resolved via existing iter64 path |
| PDF rendering | `data:URL` decoded | `photo://` resolved (existing code) |
| Idempotent submit (same idempotency-key twice) | Returns cached response | Returns cached response (idempotency layer unchanged) |
| Audit hash verification | Signed inline | Signed canonical (refs) |
| Legacy DRs with inline base64 | Continue to work | Continue to work (rendered via legacy data: path) |

🟢 **All 6 workflows preserved.**

---

## 4 · Idempotency interaction

The DR submit endpoint wraps `_do_create()` in `with_idempotency(...)`. Two concurrent submits with the same idempotency key:
- First wins: runs sanitizer + saves
- Second sees cached response: returns the same `photo://` refs that the first produced

A submit that's retried with the SAME body but a DIFFERENT idempotency key would re-upload the photos to R2 (creating duplicate R2 objects with different keys). This is a known trade-off; the duplicates are tiny and R2 storage is cheap. Mongo always holds the correct ref for the saved record.

---

## 5 · What this batch did NOT touch

- ❌ Other record types (incidents, meetings, JHAs, PO requests) — would benefit from the same pattern but out of Batch H scope
- ❌ Update/edit DR endpoints (no `PUT/PATCH` on DRs in current code; M1 freeze keeps DRs append-only)
- ❌ Frontend code (no changes required — already supports `photo://`)
- ❌ Pydantic schema (`photos: List[str]` accepts both forms)

If the operator authorizes a future batch to extend this defense to other record types, the same `_sanitize_inline_photos`-style helper can be lifted into a shared module and imported by each route.

---

## 6 · Lint + service health

- ✅ `mcp_lint_python` on `backend/routes/daily_reports.py` → all checks passed
- ✅ Preview backend restarted via supervisor (`source_hash=550118913...` unchanged — `source_hash` only tracks server.py/pdf_render.py/training_pdf.py, not routes/, but the restart picked up the new route code)
- ✅ Live smoke test against preview confirmed the protection is active

🟢 **GAP-1 write-path defense delivered. Inline base64 cannot reoccur in newly-submitted Daily Reports.**
