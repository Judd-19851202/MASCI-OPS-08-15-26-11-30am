# Photo Viewer Remediation Plan

**Batch:** OMEGA · Photo Viewer Defect Reopened
**Mode:** Plan only · READ-ONLY · NOTHING EXECUTED in this batch
**Date:** 2026-06-01
**Companion files:** `PHOTO_VIEWER_FORENSIC_REPORT.md` · `PHOTO_VIEWER_ROOT_CAUSE.md`

> Per operator directive: this batch STOPS after the root cause is proven. The fix options below are documented for the operator to authorize via a follow-up Batch. **Zero remediation has been executed.**

---

## 1 · Fix options summary

| Option | Effort | Operator action required | Defence in depth | Recommended? |
|---|---|---|---|---|
| **A · Production-env CORS_ORIGINS update + backend env-only deploy** | ~5 min ops change · backend restart | Yes — production env vars + rolling restart | Single layer (only Failure B addressed) | ✅ Immediate band-aid |
| **B · Rebuild frontend with `REACT_APP_BACKEND_URL=https://mascidocs.com` + redeploy** | ~10 min ops change · frontend build + redeploy | Yes — frontend rebuild + deploy | Single layer (only Failure A addressed) | ✅ Permanent fix |
| **C · Both A and B together** | ~15 min ops change | Yes — both | Defence in depth (either layer alone now suffices) | ✅ STRONGLY RECOMMENDED |
| D · Switch the prod frontend to a relative `/api` baseURL | Code change · 1 LOC in `lib/api.js` + frontend redeploy | Yes — code + deploy | Eliminates Failure A by removing the build-time hostname dependency entirely | Future hardening |
| E · Add a server-side CORS-allow-list audit-log + alarm | Code change · ~30 LOC | Yes — code change | Catches future regressions of this exact class | Future hardening |

**Recommended sequence**: A → B → (later) E.

---

## 2 · Option A · Backend CORS env-var update (band-aid · 5 minutes)

**Goal:** Make the production backend send `Access-Control-Allow-Origin: https://mascidocs.com` so the existing prod frontend's cross-origin XHR succeeds.

### A.1 · Operator change (in Emergent production env-var dashboard)

```
# Replace existing CORS_ORIGIN_REGEX value:
CORS_ORIGIN_REGEX=https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)

# With:
CORS_ORIGIN_REGEX=https://(.*\.)?(preview\.emergentagent\.com|emergent\.host|emergentagent\.com|mascidocs\.com)

# AND set:
CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com
```

* `(.*\.)?` lets the regex match both `mascidocs.com` (no subdomain) and `www.mascidocs.com` (subdomain).
* Keeping the explicit `CORS_ORIGINS` allow-list provides redundant matching for the two public hostnames.

### A.2 · Restart

Rolling restart of the production backend after env-var update. The Emergent platform does this automatically when env vars change.

### A.3 · Verification protocol (post-deploy · operator-runnable)

```bash
# 1. CORS preflight from mascidocs.com origin must now succeed
curl -X OPTIONS \
  -H "Origin: https://mascidocs.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://safety-audit-mobile-1.emergent.host/api/job-photos/.../raw -i \
  | grep -i "access-control-allow-origin"

# Expected: access-control-allow-origin: https://mascidocs.com
```

```
# 2. End-to-end browser repro (Playwright)
- Login as super-admin at https://mascidocs.com/admin/login
- Open /admin/photos · expand any project · click any thumbnail
- Lightbox must render the actual photo (no error overlay)
```

### A.4 · Risk

🟢 Low. Env-var-only change. No code modified. Rollback = revert env-var. No data touched.

### A.5 · Limitations

* Does NOT fix Failure A — the frontend bundle still points at `emergent.host`, so every request still does an unnecessary cross-origin round-trip.
* If at any future point the public hostname is rotated again (e.g. white-labelled to a customer domain), the same misconfiguration will reproduce.

---

## 3 · Option B · Rebuild frontend with correct `REACT_APP_BACKEND_URL` (permanent · 10 minutes)

**Goal:** Make the production frontend talk to `https://mascidocs.com/api/*` (same-origin) so CORS is irrelevant.

### B.1 · Operator change (in Emergent production deploy config)

```
REACT_APP_BACKEND_URL=https://mascidocs.com
```

Trigger a frontend rebuild + redeploy. The new bundle (`/static/js/main.<newhash>.js`) will have `https://mascidocs.com` baked in at every `process.env.REACT_APP_BACKEND_URL` site, including:

* `api.js:14` → `axios.create({ baseURL: "https://mascidocs.com/api", … })`
* `JobPhotosLibrary.jsx:132` → `THUMB_BASE = "https://mascidocs.com/api/job-photos"`
* Every other `${process.env.REACT_APP_BACKEND_URL}/api/…` template literal in the bundle

### B.2 · Cache invalidation

The new bundle filename hash (different from `main.3f15585d.js`) will force every browser to fetch the new JS. The old bundle stays cached on existing devices but will never be requested again. **No user action required.**

Service worker (`/sw-thumbs.js`) only caches `/api/job-photos/*/thumb(-signed)?` URLs — it does not cache the app shell or `/raw` responses, so it does not need to be cleared.

### B.3 · Verification protocol

```bash
# 1. Confirm the new bundle uses the correct hostname
curl https://mascidocs.com/ | grep -oE 'src="/static/js/main[^"]+\.js"'
# → /static/js/main.<NEW_HASH>.js
curl https://mascidocs.com/static/js/main.<NEW_HASH>.js \
  | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent)[a-z.]*(\.com|\.host)' | sort -u
# Expected: empty (no stale emergent.host references — only mascidocs.com)
```

```
# 2. End-to-end browser repro identical to A.3.2
```

### B.4 · Risk

🟢 Low. Standard deploy. Rollback = redeploy previous bundle. No data touched. Same-origin XHR is the long-term correct architecture.

### B.5 · Limitations

* Operator must verify the deploy pipeline actually picks up the env-var change. If the build container reads from a different source (e.g. a `.env.production` checked into git), the env-var alone may not be enough.
* If the operator later adds a new public hostname (white-label scenarios), the bundle must be rebuilt again or served from a relative path (see Option D).

---

## 4 · Option C · A + B together (RECOMMENDED · defence in depth · 15 minutes)

Apply Option A first (instant relief for any device whose cached old bundle still hits `emergent.host`), then Option B (new bundle eliminates the cross-origin call entirely).

After A is live, the operator should also wait ~15 minutes between A and B so that any users mid-session get the band-aid before the rebuild forces them onto a new bundle.

---

## 5 · Option D · Switch frontend to relative `/api` baseURL (future hardening)

**Goal:** Eliminate the build-time hostname dependency entirely.

### D.1 · Code change · `/app/frontend/src/lib/api.js:14-15`

```diff
-const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
-export const API = `${BACKEND_URL}/api`;
+// Use a relative baseURL so the page's current origin is always
+// the API origin. Works on mascidocs.com, on white-label customer
+// domains, and on the preview environment without rebuilds.
+export const API = "/api";
```

Plus the same change in `JobPhotosLibrary.jsx:132`, `JobPhotosLibrary.jsx:108` (photo-bytes ref), and any other `${process.env.REACT_APP_BACKEND_URL}` template literal in the source tree.

### D.2 · Side effects to investigate before adopting

* Preview environment: today the preview frontend is served on `*.preview.emergentagent.com` and the API on the same host — relative `/api` would still work. ✅
* Any tooling / mobile shell / WebView that loads the bundle from a different origin will break — needs a survey.
* SSR / pre-render paths (if any): N/A for this codebase (CRA SPA).

### D.3 · Risk

🟡 Medium. Touches the central API client. Must be QA'd end-to-end against all 12 portals (admin · pm · shop · hr · safety · dispatch · field-leadership · dev · safety-forms · field-leadership-portal · leadership · multi-portal sign-in) before deploy.

### D.4 · Recommended timing

After Option C ships and the immediate symptom is resolved. Not part of this incident response.

---

## 6 · Option E · Add server-side CORS-allow-list audit (future hardening)

**Goal:** Detect future regressions of this exact bug at server startup, not in production.

### E.1 · Code change · `/app/backend/server.py` (~30 LOC)

```python
# At startup, log the resolved CORS allow-list and warn if APP_ENV=production
# and the public hostname isn't in it.

PROD_PUBLIC_ORIGINS = [
    "https://mascidocs.com",
    "https://www.mascidocs.com",
]

def _audit_cors_config(allow_origins: list[str], allow_origin_regex: str | None):
    import re
    app_env = os.environ.get("APP_ENV", "production").lower()
    if app_env != "production":
        return
    missing = []
    for origin in PROD_PUBLIC_ORIGINS:
        in_list = origin in allow_origins
        in_regex = bool(allow_origin_regex and re.fullmatch(allow_origin_regex, origin))
        if not (in_list or in_regex):
            missing.append(origin)
    if missing:
        logger.critical(
            f"[cors-audit] PRODUCTION CORS misconfig: "
            f"the following public origins are NOT covered by the allow-list "
            f"or regex: {missing}. Public-facing axios calls will be blocked. "
            f"Fix CORS_ORIGINS or CORS_ORIGIN_REGEX in the production env."
        )
        # Don't kill the pod — log loudly so the operator's monitor catches it.

# Wire into the CORSMiddleware setup
_audit_cors_config(parsed_origins, regex_value)
```

This converts the current silent-misconfiguration mode into a startup log line the operator can monitor / alarm on.

### E.2 · Risk

🟢 Low. Pure logging. No behavioural change.

### E.3 · Timing

After Option C ships. Not part of this incident response.

---

## 7 · Sprint 1G cache-control header rewrite (secondary concern · P1)

A separate, secondary issue surfaced during the forensic sweep: the production ingress (the `via: 1.1 google` layer between Cloudflare and the FastAPI backend) is **overwriting** the `Cache-Control: no-store, …` header that Sprint 1G sets on every `/raw` response, replacing it with `public, max-age=604800, immutable`.

**This becomes user-visible only once Options A or B unblock the lightbox.** After the unblock, every browser will cache the JSON response (with embedded presigned R2 URL) for 7 days. After the URL's 900-second TTL expires, R2 will return 403 and the user will see a broken `<img>` (not the error string — a different mode).

The cache-buster `?_=Date.now()` in `JobPhotosLibrary.jsx:150` keeps the BROWSER cache from biting in practice (each click is a unique URL). The remaining exposure is the CDN edge cache, which keys by URL too, so the cache-buster also disarms that. **In current code the iter437 P0 pattern is mostly mitigated by the cache-buster**, but the ingress's behaviour is still architecturally wrong and should be investigated/fixed as P1 hardening:

* Investigate which middleware layer is injecting `cache-control: public, max-age=604800, immutable`. Likely candidates:
  * Emergent production deployment template applies a default `Cache-Control` header on all JSON responses.
  * Google Cloud Load Balancer config.
  * A Cloudflare worker (we can rule out CF cache, since `cf-cache-status: DYNAMIC`).
* Once located, override or remove the rewrite for any path under `/api/job-photos/.../raw` and `/api/job-photos/.../raw-batch`.

This is outside the photo-viewer-defect incident scope and is logged here for future authorization.

---

## 8 · Verification matrix for the chosen remediation

For whichever option (A, B, or C) is authorized:

| Test | Expected result |
|---|---|
| CORS preflight from `mascidocs.com` origin | ACAO header returned with the requesting origin |
| In-browser lightbox click (Playwright) | Photo image renders; no "Photo data unavailable or corrupt." text |
| Console log during lightbox interaction | No `Access-Control-Allow-Origin` / CORS errors |
| 50-photo sweep from Playwright | 50/50 lightboxes render images |
| Mobile reproduction (operator's iPhone or iPad) | Photo image renders; no error text |
| Re-check `_photo_viewer_repro_console.log`-style failure list | All previously-failing axios calls (`/api/employees`, `/api/inspections`, etc.) now succeed |

A consolidated re-certification report (`PHOTO_VIEWER_POSTFIX_CERTIFICATION.md`) should be produced after the fix is deployed, mirroring the OMEGA cadence.

---

## 9 · Rollback plan

| Option | Rollback action |
|---|---|
| A · CORS env change | Revert `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` to their prior values in the deploy dashboard · backend restart |
| B · Frontend rebuild | Redeploy the previous bundle (`main.3f15585d.js`) from the Emergent build history. No DB / R2 / collection changes — purely build artifact. |
| C · A+B | Combine the above. Independent rollbacks possible. |

No data writes are involved in any option, so no DB rollback is ever required.

---

## 10 · Pre-execution gate (per OMEGA)

🛑 **NOTHING IN THIS PLAN HAS BEEN EXECUTED.** This document is for operator review and authorization. Per the reopened-batch directive: "Do NOT fix anything in this batch."

When ready, the operator may issue a new OMEGA Batch authorizing one of:

* `OMEGA BATCH · Photo Viewer Remediation · Option A only (CORS env-var update + backend restart)`
* `OMEGA BATCH · Photo Viewer Remediation · Option B only (frontend rebuild against mascidocs.com)`
* `OMEGA BATCH · Photo Viewer Remediation · Option C (A + B, defence in depth)` ← recommended
* Or a custom Batch combining the above with the P1 cache-header investigation.

Until then: 🛑 STOPPED.
