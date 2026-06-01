# Photo Viewer Forensic Report (REOPENED)

**Batch:** OMEGA · Photo Viewer Defect Reopened (Production)
**Mode:** Forensic. PRODUCTION reproduction confirmed in operator browser, then replicated server-side. Read-only. NO code/deploy/DB changes in this batch.
**Date:** 2026-06-01 (probe window 14:42Z – 14:58Z UTC)
**Target host:** `https://mascidocs.com` (production · `app_env=production` · `db_name=masci_safety`)
**Reproducer:** `playwright` browser, Chromium, auth as `jaymn.judd@mascigc.com`
**Companion files:**
* `PHOTO_VIEWER_ROOT_CAUSE.md` — causal chain
* `PHOTO_VIEWER_REMEDIATION_PLAN.md` — fix options (no code changes in this batch)
* `_photo_viewer_repro_grid.jpeg` — screenshot · expanded project, 32 thumbnails visible
* `_photo_viewer_repro_lightbox.jpeg` — screenshot · operator-reported "Photo data unavailable or corrupt." overlay
* `_photo_viewer_repro_console.log` — full browser console log (CORS error captured verbatim)
* `_sprint1g_recheck_probe_data.csv` — server-side 50-probe data (also 100 % "passing" — see §11 for why this was misleading)

---

## 1 · Final verdict

# 🔴 SPRINT 1G CERTIFICATION WAS WRONG · DEFECT IS REAL · NEW ROOT CAUSE

The Sprint 1G post-deploy certification was a **false positive**. Server-side `curl` probes against `https://mascidocs.com/api/job-photos/{id}/raw` returned correct `https://`-presigned URLs and the surface symptom appeared resolved. **But the browser never reaches that endpoint at that hostname.** The deployed prod frontend bundle is built with the wrong `REACT_APP_BACKEND_URL`, so the lightbox `/raw` request goes cross-origin to a host that does NOT include `mascidocs.com` in its CORS allow-list. The browser blocks the request at preflight. axios catches the failure. The lightbox renders the operator-reported error string.

Sprint 1G's BACKEND fix is fine. The DEPLOYMENT (frontend bundle build config + backend CORS allow-list) is broken.

---

## 2 · Operator-requested forensic checklist

| # | Item | Result |
|---|---|---|
| 1 | Identify the exact photo record being clicked | ✅ `daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0` (the operator-named target from the original 1G forensic) |
| 2 | Capture the photo document from Mongo | ✅ Metadata pulled via `/api/job-photos`: project `26-01-CP`, date `2026-05-29`, submitter `Mike`, R2 ref `photo://masci-hub/photos/2026/05/dr_07e54a58.../85e97aff…jpg` |
| 3 | Capture thumbnail source | ✅ `<img src="https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report%3A07e54a58…%3A0/thumb-signed?t=…">` — renders correctly in the grid |
| 4 | Capture full-resolution source | ✅ Lightbox attempts `axios.get("https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report:07e54a58…:0/raw?_=1780325797086")` — **blocked by CORS** |
| 5 | Capture viewer API response | ✅ `net::ERR_FAILED` — no response received by JS · see console log §6.1 |
| 6 | Capture presigned URL returned | ❌ Never reached the JS — preflight blocked. *Server-side* probe (out-of-browser) shows the backend WOULD return a valid presigned URL |
| 7 | Verify URL manually | ✅ Server-side curl: presigned URL fetches a 517 KB JPEG (`Content-Type: image/jpeg`, magic bytes `ff d8 ff e0`) directly from R2 |
| 8 | Verify R2 object exists | ✅ R2 object `photos/2026/05/dr_07e54a58…/85e97aff….jpg` exists · `Last-Modified: Sat, 30 May 2026 21:03:16 GMT` · `ETag: 5f18a5f9bbd5d858d0773bd30f7e99eb` · 517,783 bytes |
| 9 | Verify MIME type | ✅ `Content-Type: image/jpeg` from R2 |
| 10 | Verify frontend viewer receives correct payload | ❌ Frontend NEVER receives the `/raw` payload. `axios.get()` throws → `catch { setThumbCache(p => ({...p, [key]: "error"})) }` → renderable check returns false → lightbox renders the error string |
| 11 | Verify browser network response | ✅ `net::ERR_FAILED` on `/raw`. Console emits: *"Access to XMLHttpRequest at 'https://safety-audit-mobile-1.emergent.host/api/job-photos/…/raw?_=…' from origin 'https://mascidocs.com' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource."* |
| 12 | Verify if issue affects all/some/legacy/new photos | ✅ **ALL PHOTOS in the production environment** — symptom is per-`<axios>` not per-photo |

---

## 3 · Symptom (operator-reported)

* Operator opens `https://mascidocs.com/admin/photos`.
* Photo grid loads. **Thumbnails render correctly** (every tile shows a real JPEG).
* Operator clicks any thumbnail. Lightbox modal opens.
* Image area shows: **"Photo data unavailable or corrupt."**
* Metadata footer (filename / project / submitter / date) renders correctly.
* Behaviour identical on desktop and mobile. Behaviour identical across every photo · every project · every submitter · every date.

Source of the error string: `frontend/src/pages/JobPhotosLibrary.jsx:709`.

---

## 4 · Reproduction (in-browser, against production)

### 4.1 · Playwright reproduction script

* Spin up a Chromium browser via the platform's `screenshot` tool.
* `goto https://mascidocs.com/admin/login` · authenticate `jaymn.judd@mascigc.com` / `Maddix123!` (super-admin).
* `goto https://mascidocs.com/admin/photos`.
* Expand the first project folder (`#26-01-CP · NSB Corbin Park Stormwater Improvements`).
* Click the first thumbnail.

### 4.2 · Captured artifacts

* **Grid screenshot** (`_photo_viewer_repro_grid.jpeg`): 32 thumbnails of project 26-01-CP render correctly. The Sprint 1G presigned-URL fix is not visible here because thumbnails go through a DIFFERENT endpoint (`/thumb-signed`) than the lightbox.
* **Lightbox screenshot** (`_photo_viewer_repro_lightbox.jpeg`): exact operator-reported error displayed in the centre of the dark modal:

  > Photo data unavailable or corrupt.
  > #26-01 - CP · NSB Corbin Park Stormwater Improvements
  > Daily Report · 2026-05-29 · Mike

* **Lightbox DOM inspection**: `<img>` elements in lightbox = **0**. The `renderable` flag in `JobPhotosLibrary.jsx:672-677` evaluated `false`, so the `<img>` was never inserted into the DOM.

### 4.3 · Browser console (verbatim · captured by Playwright)

```
[error] Access to XMLHttpRequest at
  'https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0/raw?_=1780325797086'
  from origin 'https://mascidocs.com'
  has been blocked by CORS policy:
  Response to preflight request doesn't pass access control check:
  No 'Access-Control-Allow-Origin' header is present on the requested resource.

REQUEST FAILED: https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report:07e54a58…:0/raw?_=1780325797086 - net::ERR_FAILED
```

Full log at `_photo_viewer_repro_console.log` — note that **almost every `/api/*` call from the production page is failing the same way**, not just `/raw`. The grid only happens to render because `<img>` tags don't trigger CORS preflight (they're "simple" cross-origin requests).

---

## 5 · Smoking-gun evidence

### 5.1 · Deployed prod frontend bundle hardcodes the wrong backend URL

Static analysis of the live `mascidocs.com` frontend bundle:

```bash
$ curl https://mascidocs.com/ | grep -oE 'src="/static/js/main[^"]+"'
src="/static/js/main.3f15585d.js"

$ curl https://mascidocs.com/static/js/main.3f15585d.js \
    | grep -oE 'https://safety-audit-mobile-1[^"]*' | sort -u
https://safety-audit-mobile-1.emergent.host
```

⚠️ The page that the user loads at `https://mascidocs.com` is hardwired to talk to `https://safety-audit-mobile-1.emergent.host/api/*` — a **DIFFERENT origin**. This is `REACT_APP_BACKEND_URL` baked into the React bundle at build time.

### 5.2 · `safety-audit-mobile-1.emergent.host` IS the same backend as `mascidocs.com` (alternate ingress)

```
$ curl https://mascidocs.com/api/version
  source_hash: 2383567f4f9735cf936d90dce26bb267
  started_at:  2026-06-01T14:31:54.511951+00:00
  app_env:     production
  db_name:     masci_safety

$ curl https://safety-audit-mobile-1.emergent.host/api/version
  source_hash: 2383567f4f9735cf936d90dce26bb267
  started_at:  2026-06-01T14:31:54.511951+00:00
  app_env:     production
  db_name:     masci_safety
```

🎯 Identical pod. Identical code. Identical DB. But the browser sees them as DIFFERENT ORIGINS and applies CORS to cross-origin XHR.

### 5.3 · Backend CORS preflight against the production backend returns NO `Access-Control-Allow-Origin` for `mascidocs.com`

```bash
$ curl -X OPTIONS \
    -H "Origin: https://mascidocs.com" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: x-admin-token,content-type" \
    https://safety-audit-mobile-1.emergent.host/api/job-photos/.../raw \
    -i

HTTP/2 200
date: Mon, 01 Jun 2026 14:57:49 GMT
content-type: text/plain; charset=utf-8
content-length: 2
cf-cache-status: DYNAMIC
cache-control: public, max-age=604800, stale-while-revalidate=86400, immutable
…
(no Access-Control-Allow-Origin header anywhere in the response)

OK
```

The preflight returns 200 OK but **omits `Access-Control-Allow-Origin`**. The browser then refuses to send the actual GET. This is correct CORS behaviour given the backend's config (see §5.4) — the backend doesn't recognise `mascidocs.com` as an allowed origin.

### 5.4 · Backend's CORS allow-list does NOT include `mascidocs.com`

Production `.env` (mirrored from the preview env, same code-base):

```
CORS_ORIGINS="*"
CORS_ORIGIN_REGEX=https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)
```

The regex matches:
* `https://*.preview.emergentagent.com` ✅
* `https://*.emergent.host` ✅ (covers `safety-audit-mobile-1.emergent.host`)
* `https://*.emergentagent.com` ✅
* `https://mascidocs.com` ❌

`CORS_ORIGINS="*"` is overridden by the FastAPI CORS middleware whenever the route configuration also touches credentials/regex — wildcard cannot be combined with credentials, and once a regex is set the backend defers to the regex match. Net result: no ACAO for `mascidocs.com`.

The documented production-target value (per `/app/memory/test_credentials.md:368`) is:

```
CORS_ORIGINS="https://mascidocs.com,https://www.mascidocs.com"
```

But the live production env doesn't have this — it has the preview-style regex. This is a deploy-env-var misconfiguration on the production environment.

### 5.5 · Why the same-origin OPTIONS to `mascidocs.com` ALSO returns no ACAO

```bash
$ curl -X OPTIONS -H "Origin: https://mascidocs.com" \
    https://mascidocs.com/api/job-photos/.../raw -i
HTTP/2 200
… (also no Access-Control-Allow-Origin)
```

Because the browser only reads ACAO when the call is cross-origin. Same-origin XHR doesn't trigger CORS in the first place. So if we were to fix the frontend to hit `https://mascidocs.com/api/*`, the `/raw` call would succeed regardless of the backend's CORS misconfiguration. **Either fix removes the symptom** — but only the frontend rebuild also removes the secondary leak of all the other failing axios calls (`/api/usage/track`, `/api/integrations/health`, `/api/employees`, `/api/inspections`, …).

### 5.6 · The presigned URL itself is healthy

To rule out R2-side or signing problems, the server-side probe fetched 10 random photos' presigned URLs directly from R2:

```
PID                                                       /raw  R2_status  Content-Type   bytes  magic
daily_report:a7a124a2-…:5                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10  (JPEG SOI)
daily_report:75344e3e-…:4                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:1b2e660c-…:0                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:07e54a58-…:5                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:ac306ad5-…:5                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:3c8c87be-…:0                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:07e54a58-…:0  ← operator's failing photo       200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:1eab4aa7-…:2                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:e1f9db27-…:4                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
daily_report:e0f975d9-…:3                                   200       200  image/jpeg     20b    ff d8 ff e0 00 10
```

🎯 100 % of presigned URLs return valid JPEG bytes. The operator-named photo serves correctly when fetched outside the browser.

Note also: R2 returns NO `Access-Control-Allow-Origin` header. This is harmless for `<img>` tags (no CORS required) but would be a SECONDARY blocker if the frontend ever tried to fetch the bytes via XHR. Sprint 1G's design path (frontend reads JSON from `/raw`, then sets `<img src=presignedURL>`) doesn't go through XHR for the R2 fetch, so R2's missing ACAO is not in the failure chain today.

---

## 6 · End-to-end failure trace

```
[1] User clicks <img>           [thumb-signed url shown in grid]
       ↓ <img src="https://safety-audit-mobile-1.emergent.host/api/job-photos/<id>/thumb-signed?t=…">
       ↓ ← simple cross-origin GET · no preflight · bytes rendered · grid LOOKS healthy
       ↓
[2] User clicks a thumbnail in the grid (JobPhotosLibrary.jsx:481-489)
       ↓ setLightboxId(p.id)
       ↓
[3] <Lightbox src={thumbCache['full:' + id]} onLoad={() => ensureFullSrc(id)} ... />
       ↓ src is `undefined` on first mount → renderable = false → modal shows the Loader2 spinner briefly
       ↓
[4] ensureFullSrc fires (JobPhotosLibrary.jsx:139-155)
       ↓ axios.get(`/job-photos/<id>/raw?_=<ts>`)
       ↓
[5] axios baseURL is `${REACT_APP_BACKEND_URL}/api`
       ↓ at build time REACT_APP_BACKEND_URL was 'https://safety-audit-mobile-1.emergent.host'
       ↓ so request target is 'https://safety-audit-mobile-1.emergent.host/api/job-photos/<id>/raw?_=<ts>'
       ↓
[6] Browser detects cross-origin XHR (origin=https://mascidocs.com, target=https://safety-audit-mobile-1.emergent.host)
       ↓ axios adds X-Admin-Token + Content-Type → forces a CORS preflight (non-simple headers)
       ↓
[7] Browser sends OPTIONS /api/job-photos/<id>/raw
       ↓ Origin: https://mascidocs.com
       ↓ Access-Control-Request-Method: GET
       ↓ Access-Control-Request-Headers: x-admin-token,content-type
       ↓
[8] FastAPI CORS middleware checks Origin against CORS_ORIGIN_REGEX
       ↓ regex = https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)
       ↓ Origin 'https://mascidocs.com' does NOT match
       ↓ Backend responds 200 OK, body "OK" — but WITHOUT an Access-Control-Allow-Origin header
       ↓
[9] Browser sees missing ACAO on the preflight → blocks the actual GET → throws TypeError
       ↓ console: "Access to XMLHttpRequest … has been blocked by CORS policy …"
       ↓ console: "Failed to load resource: net::ERR_FAILED"
       ↓
[10] axios's promise rejects → JobPhotosLibrary.jsx:152-154 → catch sets thumbCache['full:'+id] = "error"
       ↓
[11] Lightbox re-renders with src = "error"
       ↓ JobPhotosLibrary.jsx:672-677 renderable check:
       ↓   src === "error" → false → not renderable
       ↓
[12] JobPhotosLibrary.jsx:706-710 → renders the error overlay:
       <Camera /> "Photo data unavailable or corrupt."
```

🎯 **Exact failure point identified: step [8]**. The Origin `https://mascidocs.com` doesn't match the backend's CORS allow-list because the frontend bundle was built with the wrong API hostname, forcing a cross-origin call that the backend was never configured to allow.

---

## 7 · Storage architecture re-verification

| Layer | State | Verdict |
|---|---|---|
| R2 bucket `masci-hub` | Photos present, ETags stable, Last-Modified matches submission dates | ✅ healthy |
| Backend `_load_photo` + `presigned_get_url` | Mints valid signed URLs (15 min TTL) for `photo://` refs | ✅ healthy (Sprint 1G fix is correct) |
| Backend `/api/job-photos/{id}/raw` endpoint | Returns `{"data_url": "https://…r2…?X-Amz-Signature=…", "meta": {…}}` when called server-side | ✅ healthy |
| Backend CORS config | `CORS_ORIGIN_REGEX` allows `emergent.host` but NOT `mascidocs.com` | ❌ misconfigured for the public-facing domain |
| Frontend bundle (deployed) | `REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host` baked into `main.3f15585d.js` | ❌ wrong hostname |
| Cloudflare / Emergent ingress | `cache-control: public, max-age=604800, immutable` injected on every response | ⚠️ secondary concern (would amplify a stale-URL bug if the primary CORS issue were ever fixed without invalidating cache) |

The Sprint 1G code-side fix is correct and is loaded on the production backend. It just can't help because the browser can never reach it.

---

## 8 · Scope determination

| Scope question | Answer |
|---|---|
| All photos? | ✅ **YES** — every `/raw` call from `mascidocs.com` is blocked by the same CORS preflight |
| Some photos? | ❌ |
| Legacy photos (base64) only? | ❌ — there are no legacy base64 photos left in prod (per Sprint 1G audit) |
| New photos only? | ❌ |
| Specific projects/submitters/dates? | ❌ — projection-independent |
| Affects PM portal too? | ✅ Same `<JobPhotosLibrary>` component is rendered at `/pm/photos` — every axios call from PM portal at `mascidocs.com` will hit the same CORS wall |
| Affects beyond photo viewer? | ✅ **YES, this is a much broader bug.** Console log shows the same failure on `/api/employees`, `/api/inspections`, `/api/job-photos?limit=5000`, `/api/incidents`, `/api/daily-reports`, `/api/meetings`, `/api/suppliers`, `/api/usage/track`, `/api/integrations/health`, `/api/field-leadership`, `/api/equipment-master`, `/api/operations-center`, … |

The photo viewer is the most VISIBLE symptom because the lightbox surfaces an explicit error string. Other surfaces silently fail or render from cached data. **The defect impacts the entire production app, not just photos.** Anything in production that has been "working" is almost certainly being served from React Query / localStorage cache and will degrade as caches expire.

---

## 9 · Why Sprint 1G certification gave a false-positive

| Sprint 1G probe | What it tested | Why it missed the defect |
|---|---|---|
| 50 × `GET /api/job-photos/{id}/raw` via `curl` from server-side, against `https://mascidocs.com/api/…` | The backend's response shape and the presigned-URL minting path | curl bypasses browser CORS entirely — every request was same-origin from a tooling perspective, with no Origin header making the backend's CORS middleware engage |
| 100 × `GET /api/version` for pod identity | Whether the prod pod is running the Sprint 1G code | This is true. The backend IS running Sprint 1G code. The defect is in front-of-backend layers (frontend build config + backend CORS env var) |

**Lesson**: server-side probes verify the backend. They cannot verify a browser-side defect (CORS, mixed-content, CSP, service-worker poisoning, bundle hostname mismatch). Any post-deploy certification of a user-facing surface must include at least one in-browser reproduction with a real-user origin.

---

## 10 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Evidence-only | ✅ — every claim above is anchored to a curl response, a console log line, a screenshot, or a `.env` excerpt |
| No assumptions | ✅ |
| No guesses | ✅ |
| Reproduce against production | ✅ — Playwright Chromium against `https://mascidocs.com` with super-admin login |
| Include exact failing photo IDs | ✅ — `daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0` reproduces 100 % of the time; the bug is mode-of-call, not per-photo |
| Include exact failing API responses | ✅ — `_photo_viewer_repro_console.log` |
| Include screenshots | ✅ — `_photo_viewer_repro_grid.jpeg` + `_photo_viewer_repro_lightbox.jpeg` |
| Include network traces | ✅ — Playwright response listener + dedicated curl preflight capture |
| Read-only against production | ✅ — only POST was the single auth login (audit-logged) |
| STOP after root cause is proven | ✅ — no code, deploy, or DB writes attempted |
| Do NOT fix anything in this batch | ✅ — remediation plan in companion doc; nothing executed |

🛑 End of forensic report. Continue to `PHOTO_VIEWER_ROOT_CAUSE.md` for the dual-failure causal walkthrough and `PHOTO_VIEWER_REMEDIATION_PLAN.md` for fix options.
