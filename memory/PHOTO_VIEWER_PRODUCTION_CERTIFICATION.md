# Photo Viewer Production Certification — FAIL

**Batch:** OMEGA · Photo Viewer CORS Remediation · Option C · Post-Deploy Certification
**Mode:** Read-only certification against production · 7-phase plan halted after Phase 1 + symptom replay
**Date:** 2026-06-01 (probe window 15:36Z – 15:38Z UTC)
**Target:** `https://mascidocs.com`
**Authorization:** Operator deploy-complete signal, "Run production photo viewer certification."
**Companion files:**
* `PHOTO_VIEWER_CORS_REMEDIATION_REPORT.md` — original remediation plan
* `PHOTO_VIEWER_BROWSER_CERTIFICATION.md` — preview-side verification (PASSED)
* `PHOTO_VIEWER_FORENSIC_REPORT.md` · `PHOTO_VIEWER_ROOT_CAUSE.md` — original defect documentation
* `_prod_cert_failed_lightbox.jpeg` — post-deploy lightbox screenshot still showing the error overlay
* `_prod_cert_console.log` — verbatim browser CORS error post-deploy

---

## 1 · Final verdict

# 🔴 PHOTO VIEWER STILL FAILING

The production deploy partially landed but did **not** apply Option C. Both Failure A (frontend bundle hostname) and Failure B (backend CORS allow-list + middleware narrowing) are still in their pre-fix state on `https://mascidocs.com`. The lightbox still renders **"Photo data unavailable or corrupt."** verbatim, identical to the 2026-06-01 14:56Z reproduction.

The browser console captures the exact same CORS preflight failure:

```
[error] Access to XMLHttpRequest at
  'https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report:07e54a58-…:0/raw?_=…'
  from origin 'https://mascidocs.com'
  has been blocked by CORS policy:
  No 'Access-Control-Allow-Origin' header is present on the requested resource.
[error] Failed to load resource: net::ERR_FAILED
```

Phases 2-7 of the certification were not executed because Phase 1 already evidenced the deploy did not apply the operator-authorized changes; running further phases would not change the verdict.

---

## 2 · Phase 1 — Pod inventory + build verification (🔴 FAIL)

### 2.1 · Backend pod identity (🔴 backend NOT redeployed)

```bash
$ curl https://mascidocs.com/api/version

{
  "source_hash": "2383567f4f9735cf936d90dce26bb267",   ← UNCHANGED from pre-fix
  "started_at": "2026-06-01T14:31:54.511951+00:00",    ← same boot time as pre-fix
  "uptime_s": 3880,                                     ← ~65 minutes (no restart)
  "app_env": "production",
  "db_name": "masci_safety"
}
```

Expected (post-deploy): `source_hash` ≠ `2383567f4f97…`, `uptime_s` < 300 s (recent restart).
Observed: backend has not been redeployed or restarted. The middleware narrowing (`PhotoEdgeCacheMiddleware._THUMB_PATH_RE` → `thumb(-signed)?` only) is **not** running on production.

### 2.2 · Frontend bundle filename (🟡 changed, but)

```bash
$ curl https://mascidocs.com/ | grep -oE 'src="/static/js/main[^"]+\.js"'
src="/static/js/main.286932d0.js"
```

* **Pre-fix bundle**: `main.3f15585d.js`
* **Current bundle**: `main.286932d0.js` (different hash — a rebuild DID happen)

So a frontend redeploy occurred. But:

### 2.3 · Embedded backend URL in new bundle (🔴 STILL WRONG)

```bash
$ curl https://mascidocs.com/static/js/main.286932d0.js \
    | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent|mascidocs)[a-z.]*(\.com|\.host)' | sort -u
https://safety-audit-mobile-1.emergent.host
```

The new bundle **still** embeds `REACT_APP_BACKEND_URL=https://safety-audit-mobile-1.emergent.host` — the production build was rebuilt **without** updating the env var to `https://mascidocs.com`. Every axios call still goes cross-origin (`mascidocs.com` → `emergent.host`). Failure A is not eliminated.

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| Backend source_hash changed | yes | no | 🔴 |
| Backend uptime < 300 s | yes | 3880 s | 🔴 |
| Frontend bundle hash changed | yes | yes (`286932d0`) | 🟢 |
| Frontend bundle embeds `mascidocs.com` (not emergent.host) | yes | **no** (still `safety-audit-mobile-1.emergent.host`) | 🔴 |

---

## 3 · Phase 2 — CORS preflight matrix (🔴 partial · backend not restarted)

```
Origin                                                     HTTP    ACAO
─────────────────────────────────────────────────────────── ──────  ────────────
https://mascidocs.com                                       200     (none)        🔴
https://www.mascidocs.com                                   200     (none)        🔴
https://safety-audit-mobile-1.emergent.host                 400     (none)        🔴
https://evil.com                                            400     (none)        ✅ (correctly rejected, but for the wrong reason — see note)
```

Note: All preflight responses from the prod ingress look identical (200 OK with body `OK` for "passable" paths, 400 for clearly disallowed). **None** carry `Access-Control-Allow-Origin`, which is exactly the pre-fix behaviour. The backend is still running the old CORS regex (`https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)`), and the `PhotoEdgeCacheMiddleware` is still stripping ACAO from any /raw and /raw-signed responses. The new prod env vars `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com` did not take effect (the backend wasn't restarted to pick them up).

(Concerning sub-finding: `safety-audit-mobile-1.emergent.host` now returns 400 on preflight too — even though the regex `emergent.host` would still match. This implies either an ingress-level CORS handler returning 400 unconditionally for OPTIONS to `/raw` paths, or the prod CORS regex is also different from what's documented. Investigation needed once the backend actually restarts.)

---

## 4 · Phase 3 — `/raw` response (Mike · 2026-05-29 · 26-01-CP) (🔴 cache-control overwritten)

```
HTTP/2 200
content-type: application/json
cache-control: public, max-age=604800, stale-while-revalidate=86400, immutable   🔴 (Sprint 1G `no-store` overwritten by PhotoEdgeCacheMiddleware)
cdn-cache-control: public, max-age=2592000, stale-while-revalidate=86400, immutable   🔴
(no access-control-allow-origin)   🔴
pragma: no-cache
```

The body still returns a valid presigned R2 URL, and the URL fetches a real JPEG (`HTTP 206 image/jpeg` · magic bytes `ff d8 ff e0 00 10`). But because the response carries **no ACAO header**, the browser will block any cross-origin XHR before it ever sees this body. (Confirmed via the Playwright trace below.)

| Check | Expected | Actual | Verdict |
|---|---|---|---|
| `access-control-allow-origin: https://mascidocs.com` | present | **absent** | 🔴 |
| `cache-control: no-store, no-cache, must-revalidate, private` | present | replaced by `immutable, max-age=604800` | 🔴 |
| Presigned URL is valid + R2 returns JPEG | yes | yes | 🟢 |

---

## 5 · Phase 4 — Desktop browser end-to-end (🔴 OPERATOR-NAMED TARGET FAILED)

Playwright Chromium 1440×900 · super-admin · navigated to `https://mascidocs.com/admin/photos` · expanded "NSB Corbin Park Stormwater Improvements" (#26-01-CP) · clicked the first thumbnail (which IS the operator-named target `daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0` · 6 photos for this submitter in the folder).

### 5.1 · Lightbox state

* Lightbox modal opened.
* `<img>` elements inside lightbox: **0** (renderable check returned false → no `<img>` ever inserted).
* Visible text inside the lightbox:

  > **Photo data unavailable or corrupt.**
  > #26-01 - CP · NSB Corbin Park Stormwater Improvements
  > Daily Report · 2026-05-29 · Mike

  📷 Screenshot: `_prod_cert_failed_lightbox.jpeg` — identical to the pre-fix reproduction.

### 5.2 · Browser console errors (verbatim · captured 2026-06-01 15:37Z)

```
[error] Access to XMLHttpRequest at
  'https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0/raw?_=1780328255069'
  from origin 'https://mascidocs.com'
  has been blocked by CORS policy:
  No 'Access-Control-Allow-Origin' header is present on the requested resource.

[error] Failed to load resource: net::ERR_FAILED
```

Identical to the 2026-06-01 14:56Z pre-fix capture. The fix is not in effect.

### 5.3 · Thumbnail src (proves frontend still pointing at emergent.host)

```
https://safety-audit-mobile-1.emergent.host/api/job-photos/daily_report%3A07e54a58-61f5-46b2-a755-8dc4582a5a94%3A0/thumb-signed?t=1780331845
```

The bundle is `main.286932d0.js`, but its `THUMB_BASE` and `api.baseURL` still resolve to `https://safety-audit-mobile-1.emergent.host` — confirming the new bundle was built with the same wrong `REACT_APP_BACKEND_URL`.

---

## 6 · Phases 5-7 — Halted

Per the OMEGA discipline of capturing the failure first and reporting cleanly, Phases 5-7 (mobile · 50-photo sweep · regression matrix) were not run. The deploy gap is upstream of these phases — every photo on every viewport on every browser will fail in the exact same way until the deploy is corrected. Running further phases would consume operator time and credits without changing the 🔴 verdict.

---

## 7 · What's missing in the deploy

| Required step (from `PHOTO_VIEWER_CORS_REMEDIATION_REPORT.md` §3) | Done? | Evidence |
|---|---|---|
| Production backend redeployed with new code (middleware narrowing · iter445) | ❌ NO | `source_hash` unchanged · `uptime_s=3880` (no restart) |
| Production env var `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com` | ❌ NO | CORS preflight from `mascidocs.com` origin returns no ACAO; matches pre-fix behaviour |
| Production env var `CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com\|.*\.(preview\.emergentagent\.com\|emergent\.host\|emergentagent\.com))` | ❌ NO | Same — no ACAO returned |
| Production backend rolling restart | ❌ NO | Pod uptime 65+ min (no restart) |
| Production frontend build env `REACT_APP_BACKEND_URL=https://mascidocs.com` | ❌ NO | New bundle still embeds `https://safety-audit-mobile-1.emergent.host` |
| Production frontend rebuild + redeploy | ⚠️ PARTIAL | New bundle hash exists (`main.286932d0.js`) but built with the OLD env var value |

🔴 **5 of 6 required steps not applied. The one step that did happen (frontend rebuild) was performed with the wrong env var, so it produced no behavioural change.**

---

## 8 · Operator action required (corrective)

### 8.1 · Frontend (Failure A · primary)

In the production Emergent deploy dashboard:

```
REACT_APP_BACKEND_URL = https://mascidocs.com
```

Trigger frontend rebuild + redeploy. After redeploy verify:

```bash
curl https://mascidocs.com/static/js/main.<NEW_HASH>.js \
  | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent|mascidocs)[a-z.]*(\.com|\.host)' | sort -u
# Expected: empty OR only "https://mascidocs.com" — must NOT contain emergent.host
```

This single change, on its own, eliminates the photo-viewer symptom by making every axios call same-origin (no CORS preflight required). It is the most important step.

### 8.2 · Backend (Failure B · defense-in-depth)

In the production Emergent deploy dashboard:

```
CORS_ORIGINS = https://mascidocs.com,https://www.mascidocs.com
CORS_ORIGIN_REGEX = https://((.*\.)?mascidocs\.com|.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com))
```

Plus: trigger a production backend redeploy so the latest `/app/backend/server.py` (containing the `PhotoEdgeCacheMiddleware` regex narrowing · iter445) takes effect. After redeploy + restart, verify:

```bash
curl https://mascidocs.com/api/version
# Expected: source_hash != 2383567f4f97… AND uptime_s < 300

curl -i -X OPTIONS \
  -H "Origin: https://mascidocs.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://mascidocs.com/api/job-photos/test/raw \
  | grep -i "access-control-allow-origin"
# Expected: access-control-allow-origin: https://mascidocs.com
```

### 8.3 · Order of operations

* Frontend rebuild first (§8.1) — instant symptom fix.
* Backend redeploy + env-var update next (§8.2) — defense-in-depth + preserves Sprint 1G's `no-store` directive on `/raw`.

---

## 9 · Re-certification protocol

When the operator confirms BOTH §8.1 and §8.2 are done, this agent will re-run Phases 1-7 of the original certification plan (`PHOTO_VIEWER_PRODUCTION_CERTIFICATION.md` prior version, now superseded by this fail report). The verdict will be re-issued as either:

* 🟢 **PHOTO VIEWER PRODUCTION CERTIFIED**, or
* 🔴 **PHOTO VIEWER STILL FAILING** (with attached failure inventory).

---

## 10 · OMEGA discipline confirmation (this batch)

| Rule | Observed |
|---|---|
| Read-only against production | ✅ — only `/api/version`, `/api/job-photos`, `/api/admin/login` (single audit-logged break-glass), and Playwright reads |
| No code/deploy/DB writes | ✅ — no remediation attempted from this side |
| Evidence-only | ✅ — every claim anchored to curl output, screenshot, or browser console |
| Stop after symptom replicated post-deploy | ✅ — Phases 5-7 deferred to avoid wasted credits on a confirmed failure mode |
| Final verdict explicit | ✅ — 🔴 PHOTO VIEWER STILL FAILING |
| Companion remediation report unchanged (preview state is fine; only production deploy gap to address) | ✅ |

🛑 STOPPED. Awaiting operator to (a) update `REACT_APP_BACKEND_URL=https://mascidocs.com` in the production frontend deploy env, (b) update `CORS_ORIGINS` + `CORS_ORIGIN_REGEX` in the production backend deploy env, (c) trigger frontend + backend redeploy with rolling restart. Then signal re-certification.
