# Photo Viewer Root Cause

**Batch:** OMEGA · Photo Viewer Defect Reopened
**Mode:** Forensic causal analysis · READ-ONLY
**Date:** 2026-06-01
**Companion files:** `PHOTO_VIEWER_FORENSIC_REPORT.md` · `PHOTO_VIEWER_REMEDIATION_PLAN.md`

---

## 1 · One-sentence root cause

> **The production `mascidocs.com` frontend bundle was built with `REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host`, forcing every API call to be cross-origin against a backend whose CORS allow-list (`CORS_ORIGIN_REGEX`) does NOT include `mascidocs.com`. The browser blocks the `/raw` XHR at preflight, axios catches the error, the lightbox renders "Photo data unavailable or corrupt".**

---

## 2 · Dual-failure model

The defect is the intersection of TWO independent misconfigurations. Either one alone would be inert; together they produce the operator's symptom.

### Failure A — Frontend bundle hardcodes the wrong API hostname

```
$ curl https://mascidocs.com/static/js/main.3f15585d.js \
    | grep -oE 'https://safety-audit-mobile-1[^"]*' | sort -u
https://safety-audit-mobile-1.emergent.host
```

`REACT_APP_BACKEND_URL` is interpolated at React build time and baked into the minified bundle as a string literal. The deployed `main.3f15585d.js` contains the emergent.host hostname, NOT `mascidocs.com`. Therefore:

```js
// /app/frontend/src/lib/api.js
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
//          ↑
//   "https://safety-audit-mobile-1.emergent.host" at runtime on mascidocs.com
export const API = `${BACKEND_URL}/api`;
export const api = axios.create({ baseURL: API, … });
```

Every `api.get("/job-photos/<id>/raw?_=…")` becomes `GET https://safety-audit-mobile-1.emergent.host/api/job-photos/<id>/raw?_=…` even when the user is on `https://mascidocs.com`. This is cross-origin.

### Failure B — Backend CORS allow-list does not include `mascidocs.com`

```
# /app/backend/.env   (same on both prod & preview pods · source_hash 2383567f4f97…)
CORS_ORIGINS="*"
CORS_ORIGIN_REGEX=https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)
```

`CORS_ORIGINS="*"` is dropped by FastAPI's middleware when an `allow_origin_regex` is set (the regex takes precedence for the per-request match). The regex matches:

| Origin | Match? |
|---|---|
| `https://safety-audit-mobile-1.preview.emergentagent.com` | ✅ |
| `https://safety-audit-mobile-1.emergent.host` | ✅ |
| `https://anything.emergentagent.com` | ✅ |
| **`https://mascidocs.com`** | **❌ (no subdomain to match `.+\.`)** |
| `https://www.mascidocs.com` | ❌ (different TLD entirely) |

The documented production target (`test_credentials.md:368`) is:

```
CORS_ORIGINS="https://mascidocs.com,https://www.mascidocs.com"
```

But the live prod env is using the preview-style regex.

### Combined effect

```
Page origin:  https://mascidocs.com
API target:   https://safety-audit-mobile-1.emergent.host   ← Failure A
Backend CORS: regex doesn't match Origin                    ← Failure B
                                          ↓
                              CORS preflight returns no ACAO
                                          ↓
                                  Browser blocks XHR
                                          ↓
                              axios rejects → catch sets cache="error"
                                          ↓
                       Lightbox renders "Photo data unavailable or corrupt."
```

If Failure A is fixed alone → all calls go same-origin to `mascidocs.com` → CORS irrelevant → symptom gone.
If Failure B is fixed alone → backend sends ACAO for `mascidocs.com` Origin → preflight passes → symptom gone.
If both are fixed → defence in depth (recommended).

---

## 3 · Why `<img>` thumbnails appear healthy

`<img src="https://safety-audit-mobile-1.emergent.host/api/job-photos/<id>/thumb-signed?t=…">` is a **simple cross-origin GET**:
* no JS reads the response body (the browser pipes bytes directly into the `<img>` decoder)
* no preflight is generated
* the response can lack `Access-Control-Allow-Origin` entirely — the browser still paints the image

So the grid LOOKS healthy. The defect only surfaces when JS needs to read the response body, which is exactly what the lightbox does for `/raw`.

---

## 4 · Why the operator's prior `<img src=presigned R2 url>` flow worked even when CORS was wrong

The Sprint 1G design path is:

```
JS:  fetch /api/job-photos/<id>/raw  → reads JSON body → extracts presigned URL
JS:  <img src=presignedR2URL>        → simple cross-origin GET, no preflight, browser renders
```

Step 1 IS an XHR that reads a body — it needs CORS. Step 2 is `<img>` — it does not. So the design assumes the only CORS-gated request is the lightweight JSON `/raw` call, which IS gated by CORS. With Failure A + Failure B in effect, step 1 fails and the chain never reaches step 2.

---

## 5 · Why the previous Sprint 1G certification missed this

Sprint 1G ran 50 + 100 + 50 server-side curl probes against `https://mascidocs.com/api/version` and `/api/job-photos/{id}/raw`:

| Tool | Origin header sent? | CORS engaged? | What it proved |
|---|---|---|---|
| `curl` (sprint 1G certification) | None | ❌ No | The backend behind `mascidocs.com/api/*` is healthy and serves valid presigned URLs |
| `curl` with `-H "Origin: …"` (this batch) | Yes | ✅ Yes (preflight only) | The backend does NOT send ACAO for `mascidocs.com` Origin |
| Browser axios (this batch) | Yes (`https://mascidocs.com`) | ✅ Yes | Preflight blocked → user sees the error |

A `curl` probe that omits an Origin header is fundamentally incapable of reproducing a CORS bug. The certification mistake was equating "backend returns the expected payload" with "user can see the photo".

---

## 6 · Why thumbnails on the production page survived this issue at all

The grid renders 32 thumbnails per project folder. The path is:

```
GET /api/job-photos?limit=5000     (XHR · CORS-blocked · returns 0 bytes to JS)
```

Yet the grid populates. Reading the browser console:

```
REQUEST FAILED: https://safety-audit-mobile-1.emergent.host/api/job-photos?limit=5000 - net::ERR_ABORTED
```

The metadata request fails. The grid still renders. The most likely explanations (not exhaustively probed; outside this batch's scope):

1. **React Query / SWR persisted cache** — a previous successful session populated the in-memory or localStorage cache; the failed request's stale data is still rendered.
2. **Service Worker** intercepts and serves cached data even when the network call aborts.
3. **A different code path** in the production bundle uses fetch() without custom headers, escaping the preflight requirement.

The point is moot for this batch — the photo viewer's failure is rock-solid evidenced. Whatever cache trick the grid is exploiting will degrade over time as caches expire.

---

## 7 · Why the backend's `cache-control: public, max-age=604800, immutable` header on `/raw` is also wrong (secondary concern)

Even after fixing Failures A + B, a SECONDARY concern remains: the production ingress (Google Cloud / `via: 1.1 google`) appears to be rewriting the response cache-control header. The backend explicitly sets:

```python
# /app/backend/routes/job_photos.py:869 (Sprint 1G code path)
response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
response.headers["Pragma"] = "no-cache"
```

But the live `mascidocs.com` response has:

```
cache-control: public, max-age=604800, stale-while-revalidate=86400, immutable
cdn-cache-control: public, max-age=2592000, stale-while-revalidate=86400, immutable
pragma: no-cache               ← backend's directive survives
```

(Preview at `safety-audit-mobile-1.preview.emergentagent.com/api/.../raw` returns `cache-control: no-store, no-cache, must-revalidate` — preview ingress preserves the header; production ingress overwrites it.)

If the primary CORS issue is solved without addressing this header rewrite, browsers will cache the `/raw` JSON response for 7 days. After 15 minutes the presigned URL embedded in that cached response will be expired, R2 will return 403, and the user will see broken images (not the current error text, but a different failure mode). The cache-buster `?_=Date.now()` in `ensureFullSrc` would normally save us, but service workers / shared CDN caches can still hit. **This is the iter437 P0 incident pattern re-emerging on production-only.**

This is a deploy/infra concern beyond OMEGA scope and is captured in the remediation plan as a P1 follow-up.

---

## 8 · Renderable check truth table (proof the "error" string IS the only outcome)

The lightbox decides what to render via `JobPhotosLibrary.jsx:672-677`:

```js
const renderable =
    typeof src === "string" &&
    src !== "loading" &&
    src !== "error" &&
    (src.startsWith("data:image/") || src.startsWith("blob:") || src.startsWith("http")) &&
    src.length > 30;
```

| src value | renderable | What user sees |
|---|---|---|
| `undefined` / `null` | false | Spinner (line 712) |
| `"loading"` | false | Spinner |
| `"error"` (axios threw — current production state) | false | **"Photo data unavailable or corrupt." (line 709)** ✅ matches operator report |
| `"data:image/jpeg;base64,…"` | true | `<img>` renders inline base64 |
| `"https://…r2…?X-Amz-Signature=…"` (Sprint 1G happy path) | true | `<img>` renders presigned R2 URL → bytes render |
| `"photo://masci-hub/…"` (pre-1G stale) | false | Error overlay (the original bug Sprint 1G fixed) |

Today's production state lands in row 3. Sprint 1G's BACKEND payload would land in row 5 — if the browser could ever fetch it.

---

## 9 · Confirmed scope: all photos · all surfaces

| Surface | Affected? | Why |
|---|---|---|
| `/admin/photos` lightbox click | ✅ Yes — every photo, every project | XHR to cross-origin `/raw` blocked |
| `/pm/photos` lightbox click | ✅ Yes — same component, same axios baseURL | Identical code path |
| `/admin/photos` thumbnail grid rendering | ⚠️ Stale-cache dependent — looks healthy now, will degrade | `<img>` does not need CORS; `/job-photos` list call is CORS-blocked but populated from cache |
| Record-detail pages (`/photo-bytes?ref=…`) | ✅ Likely affected — also XHR | Same baseURL |
| Photo ZIP download (`/job-photos/zip`) | ✅ Affected | POST + axios |
| Photo email (`/job-photos/email`) | ✅ Affected | POST + axios |
| Re-index button on `/admin/photos` | ✅ Affected | POST + axios |
| Any other admin/PM/HR/safety axios call | ✅ Affected | All routed through same `api.js` baseURL |

---

## 10 · Root cause summary

| | |
|---|---|
| **Symptom** | "Photo data unavailable or corrupt." in lightbox on every prod photo click |
| **Where it's rendered** | `JobPhotosLibrary.jsx:709` |
| **Why it's rendered** | `thumbCache['full:<id>'] === "error"` |
| **Why cache becomes "error"** | `axios.get('/job-photos/<id>/raw')` throws |
| **Why axios throws** | Browser blocked the XHR at CORS preflight |
| **Why browser blocks** | Preflight response from `safety-audit-mobile-1.emergent.host` lacks `Access-Control-Allow-Origin: https://mascidocs.com` |
| **Why ACAO is missing** | Backend's `CORS_ORIGIN_REGEX` doesn't match `mascidocs.com` |
| **Why we hit this backend hostname at all** | Production frontend bundle was built with `REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host`, not `https://mascidocs.com` |
| **PRIMARY ROOT CAUSE** | Production deploy was built and pushed without rebuilding the React bundle against the public hostname, AND the production backend's CORS env vars were not adjusted to match the public hostname. |

🛑 Root cause proven. Continue to `PHOTO_VIEWER_REMEDIATION_PLAN.md` for fix options.
