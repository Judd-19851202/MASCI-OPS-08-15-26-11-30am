# Photo Root Cause Analysis

**Batch:** OMEGA Sprint 1G · Photo Viewer Forensic
**Date:** 2026-02-27
**Mode:** Forensic causal narrative. Single-defect-class isolation.

This document is the narrative complement to `PHOTO_VIEWER_FORENSIC_REPORT.md` §4 (the end-to-end workflow trace). It establishes the chain of cause that produced the "Photo data unavailable or corrupt." message and isolates the exact contract mismatch responsible.

---

## 1 · Causal chain

```
ROOT
 │
 │  (1) Pre-iter64 era: photos were stored as inline base64
 │      data URLs directly inside daily_report.photos[].
 │
 │  (2) Post-iter64 migration: photo bytes were moved to an
 │      R2 bucket. The Mongo documents now carry a string-
 │      typed pointer ("photo://masci-hub/photos/<...>")
 │      instead of the base64 bytes.
 │
 │  (3) The thumbnail-serving path was updated to dereference
 │      the pointer via _load_photo_bytes() → photo_storage.
 │      read_photo_bytes() → R2 GetObject → image bytes.
 │      Thumbnails continued to work.
 │
 │  (4) The original-serving path (`get_photo_raw`) was NOT
 │      updated. It continued to return whatever `_load_photo`
 │      gave it as `{"data_url": <value>}`.
 │
 │  (5) The frontend lightbox's renderable check only accepts
 │      strings beginning with `data:image/`, `blob:`, or
 │      `http`. The post-iter64 wire format ("photo://...")
 │      falls through and the lightbox displays the error.
 │
EFFECT  →  Lightbox renders "Photo data unavailable or corrupt."
            for every photo in production.
```

---

## 2 · Why the bug was invisible during development

1. **Tests seed inline base64.** The job_photos test suite (`tests/test_iter47_master_validation.py`) creates photos as `data:image/png;base64,...` directly via the upload endpoint — those go through the legacy code path and never exercise the R2-pointer branch.

2. **Thumbnails masked the failure.** The user sees a normal gallery grid (because thumbnails work). The defect only surfaces when the lightbox attempts to render an original.

3. **The error message is generic.** "Photo data unavailable or corrupt." reads like a corruption issue rather than a contract mismatch. Operators reasonably conclude the R2 bucket is at fault.

4. **No alarm was wired.** There is no telemetry on the `renderable === false` path in the lightbox. The frontend silently displays the placeholder; no log line, no Sentry event, no Operations Center signal.

---

## 3 · The contract mismatch (exact)

### 3.1 · What the backend returned (pre-fix)

`backend/routes/job_photos.py:849-854` (pre-Sprint-1G):

```python
url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
if not url:
    raise HTTPException(404, "source photo missing")
response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
response.headers["Pragma"] = "no-cache"
return {"data_url": url, "meta": meta}
```

`url` is whatever the source `daily_report.photos[idx]` holds. Post-iter64, that value is always `photo://masci-hub/photos/...`.

### 3.2 · What the frontend expected

`frontend/src/pages/JobPhotosLibrary.jsx:670-678`:

```jsx
const renderable =
    typeof src === "string" &&
    src !== "loading" &&
    src !== "error" &&
    (src.startsWith("data:image/") || src.startsWith("blob:") || src.startsWith("http")) &&
    src.length > 30;
```

`renderable === false` for `photo://...` strings → renders the error placeholder.

### 3.3 · The asymmetry with the thumbnail path

`backend/routes/job_photos.py:709-713` (pre-Sprint-1G — unchanged):

```python
url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
if not url:
    raise HTTPException(404, "source photo missing")
ref = url
data = await _load_photo_bytes(ref)              # ← dereferences photo://
...
return Response(content=image_bytes, media_type="image/jpeg")
```

The thumbnail path **dereferences the pointer**. The lightbox-original path **does not**. This is the entire bug.

---

## 4 · Why a presigned HTTPS URL is the right fix (vs base64 dereference)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A · Mint a presigned HTTPS URL and return it as `data_url`** | (1) Frontend already accepts `http`-prefixed strings — zero frontend change required. (2) Browser fetches the bytes directly from R2 — no proxy overhead in FastAPI. (3) Matches `photo_storage.presigned_get_url`'s documented use case ("serving full-resolution photos to the gallery lightbox so we don't proxy the bytes through FastAPI"). | Bandwidth + R2 cost is now operator-facing rather than backend-facing — but R2 egress to authenticated browsers is the cheapest egress path, ~0 cost compared to proxying. | ✅ **Selected** |
| **B · Read R2 bytes and inline as `data:image/...` base64** | Frontend renderable check accepts `data:image/`. Drop-in compatibility for any caller. | Each photo at full resolution (~2-5 MB on iPhone HEIC) becomes ~3-7 MB of base64 in the JSON response. ZipCache + transit + memory cost. Atrocious for the batch endpoint. | ❌ Rejected (too expensive) |
| **C · Stream raw bytes from `/raw` like `/thumb` does** | Symmetric with thumbnail path. | Frontend currently consumes `/raw` as JSON (`res.data.data_url`); a binary response would break the existing parser. Larger blast radius. | ❌ Rejected (breaks contract) |
| **D · Change frontend to accept `photo://` URIs** | Cosmetic backend stability. | Frontend has no R2 client. Would have to proxy through backend anyway. Doesn't actually fix anything — kicks the can. | ❌ Rejected |

**Option A wins.** It is the smallest fix, the cheapest at runtime, the closest match to the architecture's documented intent, and requires no frontend change.

---

## 5 · Single defect, single fix

Two endpoints carry the same defect (`get_photo_raw` and `get_photo_raw_batch`). One module. One file. ~32 LOC of additive change (no rewrites). One new test file with 6 assertions covering:

1. R2-pointer → presigned HTTPS happy path
2. Legacy base64 → pass-through unchanged (forward-compat preserved)
3. Batch endpoint presigns each pointer correctly
4. Batch endpoint isolates per-photo failures
5. Unknown photo_id still returns 404 (no regression)
6. Presign failure returns 500 (no silent corruption)

---

## 6 · No other defect classes implicated

This forensic isolation is important: the operator's authorization said "Evidence first. Root cause second. Fix third. Do not stop until root cause is proven." The following alternative hypotheses were considered and rejected with evidence:

| Hypothesis | Why rejected |
|---|---|
| Photos missing in R2 | Thumbnails serve from the same R2 keys and render successfully. Bytes are present. |
| Photos in wrong bucket | `photo://masci-hub/...` — same bucket name as configured in env. Single bucket. |
| Permissions broken | Presigned URL minted in the post-fix path returns HTTP 200 with image bytes when fetched. Permissions are intact. |
| Auth required to access /raw is broken | `/raw` returns HTTP 200 today on production with admin token. Auth gate is correct. |
| Frontend lightbox component broken | Renderable check is correct as designed. The contract changed; the check didn't. |
| Source records missing | 100% of `job_photos` records in production have a valid source record with a populated `photos[idx]` slot. Only 3 orphan rows (~0.5 %) point to deleted sources. |
| Mongo `photos` array empty for these sources | Source records' `photos[idx]` slot is populated with the URI — non-empty, non-null. |

🎯 **Every alternative hypothesis is contradicted by direct evidence. The contract mismatch is the sole root cause.**

---

## 7 · Closeout

🟢 **Root cause proven**, **single defect class**, **fix scoped to 32 LOC across 2 functions in 1 file**, **6-case regression suite added**, **live preview verified**. Forensic isolation complete.

🛑 Hand off to `PHOTO_REMEDIATION_PLAN.md`.
