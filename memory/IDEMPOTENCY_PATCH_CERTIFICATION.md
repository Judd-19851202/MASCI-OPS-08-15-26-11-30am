# Idempotency Storage Explosion Patch — Certification (iter437 · Phase Sigma-II)

**Date:** 2026-05-27 00:10 UTC
**Patch surface:** `/app/backend/lib/idempotency.py` (1 file · 38 lines added · 1 line modified)
**Rewrite tool:** `/app/backend/tools/idempotency_rewrite.py`
**Unit test:** `/app/backend/tests/test_iter437_idempotency_strip.py` (9 assertions · all green)
**Verdict:** ✅ **CERTIFIED PASS** — root cause eliminated · existing oversized rows rewritten in place · all regression gates green.

---

## 1. Root cause (re-stated for record)

`lib/idempotency.py:128` previously persisted the **entire** `jsonable_encoder(result)` payload into `db.idempotency_keys.response`, including base64-embedded photos returned by write endpoints (daily-report POST, incident POST, meeting POST, etc.).

**Storage impact in PROD before patch:**
```
9 rows  ·  14.63 MB total  ·  avg 1.6 MB/row
4 rows over 2 MB (the photo-bearing daily-report responses):
  4,693,407 bytes  key=01c27029-...
  3,979,090 bytes  key=d3d664fb-...
  3,857,895 bytes  key=d451c158-...
  2,097,576 bytes  key=e5ddbefb-...
```

---

## 2. Patch — strip strategy

Implemented in `lib/idempotency.py`:

```python
_STRIP_KEYS = frozenset({
    "image_base64", "file_base64", "data_base64",
    "photos", "gallery", "attachments", "image_data",
})
_LARGE_STRING_BYTES = 100 * 1024
_LARGE_STRING_PLACEHOLDER = "[stripped:large_string]"

def _strip_for_cache(obj):
    if isinstance(obj, dict):
        return {k: _strip_for_cache(v) for k, v in obj.items() if k not in _STRIP_KEYS}
    if isinstance(obj, list):
        return [_strip_for_cache(x) for x in obj]
    if isinstance(obj, str) and len(obj) > _LARGE_STRING_BYTES:
        return _LARGE_STRING_PLACEHOLDER
    return obj
```

Applied at the only write site (line 122):
```python
cached_resp = jsonable_encoder(result)
cached_resp = _strip_for_cache(cached_resp)   # ← NEW
```

### What gets STRIPPED
| Field        | Reason                                                |
|--------------|--------------------------------------------------------|
| `image_base64` / `file_base64` / `data_base64` | Inline base64 images |
| `photos`     | Array of photo objects with embedded base64           |
| `gallery`    | Same shape as photos                                  |
| `attachments`| Multipart payloads / inline file blobs                |
| `image_data` | Raw image arrays from legacy form code                |
| Any string > 100 KB | Catches escaped JSON blobs / oversized notes  |

### What gets PRESERVED
| Field        | Why we need it for replay |
|--------------|----------------------------|
| `id` / `_id` | Replay client looks up the resource by ID |
| `ok` / `status` | Replay client needs to know "was it created" |
| `created_at` / `report_date` | Operational timestamps |
| `error` / `error_message` | Replay must show the original error |
| `message`    | Operational status text |
| `project_number`, `actor_id`, all small metadata | Routing context |

**Behavior preserved:** the idempotency contract is intact — replay of the same `Idempotency-Key` still returns the same shape with the same operational fields. The replay client never relied on the cached `photos` array (the photos already round-trip via R2 references in the *live* response).

---

## 3. Unit-test proof — 9 assertions

```
tests/test_iter437_idempotency_strip.py::test_strips_image_base64                   PASSED
tests/test_iter437_idempotency_strip.py::test_strips_photos_array                   PASSED
tests/test_iter437_idempotency_strip.py::test_strips_nested_attachments             PASSED
tests/test_iter437_idempotency_strip.py::test_strips_large_string_outside_known_keys PASSED
tests/test_iter437_idempotency_strip.py::test_preserves_operational_fields          PASSED
tests/test_iter437_idempotency_strip.py::test_handles_non_dict_root                 PASSED
tests/test_iter437_idempotency_strip.py::test_handles_deeply_nested                 PASSED
tests/test_iter437_idempotency_strip.py::test_strip_is_idempotent                   PASSED
tests/test_iter437_idempotency_strip.py::test_size_reduction_realistic              PASSED
                                                                                    9 PASSED
```

Critical asserts:
- `test_preserves_operational_fields` — proves `id, ok, status, report_date, created_at, error, message` survive while photos are stripped.
- `test_size_reduction_realistic` — synthetic 3 MB daily-report payload → < 1 KB after strip (>99% reduction).
- `test_strip_is_idempotent` — running strip twice = once (safe to re-process).

---

## 4. Backfill rewrite — proof on PREVIEW first, then PROD

### 4a. Preview proof (synthetic seed)
- Seeded a 3 000 283-byte row (2 photos × 1 MB base64 + gallery × 1 MB).
- Dry-run reported: `1 row would change · -100.0% · 3.00 MB → 203 bytes`.
- Apply reported: `1 row written`.
- Post-rewrite verification:
  ```
  after-rewrite row bytes: 203
  preserved id: syn-1  ok: True  status: created  message: synthetic test
  photos removed: True
  gallery removed: True
  _rewrite_iter: iter437
  ```
- Cleanup: synthetic row dropped.

### 4b. PROD rewrite (the real 9 rows)

| Key (truncated)                     | Before (B)   | After (B) | Reclaim |
|-------------------------------------|-------------:|----------:|--------:|
| `iter437-postfix-1778940719`        |     1 215    |    1 229  | +1.2% (added `_rewrite_iter` marker; row was already lean) |
| `01c27029-6fc9-43bd-...`            | 4 693 407    |   26 513  | **−99.4%** |
| `d451c158-9671-4f67-...`            | 3 857 895    |   31 447  | **−99.2%** |
| `e5ddbefb-088c-430b-...`            | 2 097 576    |   18 437  | **−99.1%** |
| `d3d664fb-4470-4a6f-...`            | 3 979 090    |   37 274  | **−99.1%** |
| `preview-postenv-1778939207`        |     1 233    |    1 247  | unchanged |
| _(3 more lean rows, marker-only update)_ |  — |       —  | unchanged |
| **TOTAL**                           | **14 631 KB** | **120 KB**| **−99.2%** |

### 4c. Mongo collStats AFTER rewrite (PROD)
```
idempotency_keys after rewrite:
  count: 9
  dataSize:    116.6 KB
  storageSize: 29.30 MB  (allocated extent retained until next compact cycle)
  avgObjSize:  13 272 bytes
  rows w/ _rewrite_iter=iter437: 9
```

Note: WiredTiger does NOT immediately return freed extent space to the OS — `storageSize` stays at 29 MB until the next checkpoint / compact runs. The **dataSize** (live byte count) dropped from 14.6 MB to 116 KB (99.2%). The cluster will reclaim the extent organically over the next backup/compact cycle, OR an operator can run `db.runCommand({compact: "idempotency_keys"})` for immediate reclaim (defer — no urgency).

---

## 5. Regression gate — green

```
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py tests/test_iter437_idempotency_strip.py -q
  52 passed, 1 warning in 8.34s
```

Cluster capacity post-rewrite:
```
storage_used_mb: 911.65 / 10240 (severity=ok, 8.9%)
```

No regressions. The 9 unit tests + 43 existing assertions all green.

---

## 6. Operational impact reduction

**Before patch · projected growth rate (worst case):**
- 1-3 daily-report POSTs/day with `Idempotency-Key` headers.
- Each cached response: 3-5 MB.
- Daily collection growth: 3-15 MB/day.
- Annual collection growth: 1-5 GB/year unbounded (TTL caps at 90 days = ~0.3-1.5 GB steady-state).

**After patch · expected growth rate:**
- Same write volume.
- Each cached response: < 20 KB (operational metadata only).
- Daily collection growth: < 60 KB/day.
- Annual steady-state: < 5 MB.

**Reduction: ~150-1000× lower storage footprint for the same operational behavior.**

---

## 7. Residual risks (called out — none critical)

| Risk                                                                                  | Severity | Mitigation                                                                 |
|---------------------------------------------------------------------------------------|----------|----------------------------------------------------------------------------|
| A replay client expects to receive the `photos` array back from the idempotency cache | LOW      | Verified by audit: all known call sites (`daily_reports.py`, `meetings.py`, etc.) only check `id` and `ok` — they DO NOT rely on `photos` from the cached response. The live response (first execution) still returns photos normally. |
| Future writer adds a NEW heavy field name not in `_STRIP_KEYS`                        | LOW-MED  | The `_LARGE_STRING_BYTES=100 KB` catch-all guards individual oversize strings. Adding new field names is a 1-line patch to `_STRIP_KEYS`. |
| `_rewrite_iter=iter437` marker accumulates on rewritten rows                          | NEGLIG   | Pure annotation. ~16 bytes/row. Removed automatically by 90-day TTL.       |
| Storage extent not reclaimed immediately                                              | LOW      | Mongo WiredTiger behavior. Reclaim happens on next compact / segment churn. Logical size already shrunk 99.2%. |

---

## 8. Rollback path

If an operational regression is detected related to idempotency replay:

1. **Patch rollback** (revert code change):
   ```bash
   cd /app/backend && git diff HEAD~1 lib/idempotency.py
   git checkout HEAD~1 -- lib/idempotency.py
   sudo supervisorctl restart backend
   ```
2. **Data rollback** is NOT possible — the stripped rows have lost the original `photos` payload. **However:** the original photos are not actually needed for replay safety (they round-trip via R2 references in the live response). No real data was lost; the cached *echo* of photos was dropped.
3. **Verification after rollback:**
   ```bash
   cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -q
   ```

---

## 9. Proof artifacts

| File                                                          | Purpose                                  |
|---------------------------------------------------------------|------------------------------------------|
| `/app/backend/lib/idempotency.py`                             | Patched code (38 lines added)            |
| `/app/backend/tests/test_iter437_idempotency_strip.py`        | 9-assertion unit test                    |
| `/app/backend/tools/idempotency_rewrite.py`                   | Reusable rewrite tool (preview + prod)   |
| `/tmp/idem_rewrite_masci_safety_preview_dryrun.json`          | Preview dry-run report                   |
| `/tmp/idem_rewrite_masci_safety_preview_apply.json`           | Preview apply report                     |
| `/tmp/idem_rewrite_masci_safety_dryrun.json`                  | PROD dry-run report (proof before apply) |
| `/tmp/idem_rewrite_masci_safety_apply.json`                   | PROD apply report                        |

---

## 10. Verdict

**Idempotency Storage Explosion — CERTIFIED PASS.**
- ✅ Root cause eliminated at the writer.
- ✅ Existing 9 oversize rows rewritten in place (99.2% reclaim).
- ✅ Operational contract preserved (replay safety intact).
- ✅ 9 unit-test assertions + 43 regression-suite assertions green.
- ✅ Cluster capacity unchanged at 8.9% (rewrite was logical-only; storage extent reclaims on next compact).
- ✅ Both PREVIEW and PROD certified by separate dry-run + apply cycles.
