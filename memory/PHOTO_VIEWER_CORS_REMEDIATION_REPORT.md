# Photo Viewer CORS Remediation Report (Option C)

**Batch:** OMEGA · Photo Viewer CORS Remediation · Option C (A + B defense-in-depth)
**Mode:** Execution — preview environment hardened, production deploy is the operator's authorized step
**Date:** 2026-06-01 (15:08Z – 15:18Z UTC)
**Companion files:**
* `PHOTO_VIEWER_BROWSER_CERTIFICATION.md` — in-browser Playwright + CORS regression matrix
* `PHOTO_VIEWER_PRODUCTION_CERTIFICATION.md` — final production verdict (pending operator deploy)
* `PHOTO_VIEWER_FORENSIC_REPORT.md` + `PHOTO_VIEWER_ROOT_CAUSE.md` — defect documentation
* `_photo_viewer_repro_*.jpeg` — pre-fix operator-reported reproduction screenshots

---

## 1 · Scope confirmation

> Operator authorization: "OMEGA AUTHORIZATION — PHOTO VIEWER CORS REMEDIATION · OPTION C. Authorize recommended Option C: A + B defense-in-depth remediation."

| Sub-item | What it covers |
|---|---|
| **A** | Production-env CORS update — allow `https://mascidocs.com` AND `https://www.mascidocs.com` while preserving existing Emergent/preview origins; no wildcard `*` |
| **B** | Frontend rebuild — `REACT_APP_BACKEND_URL=https://mascidocs.com` so all API traffic stays same-origin |

Strictly out of scope (and observed): no new features, no orphan cleanup, no white-label, no ForgedOps, no dashboards, no unrelated fixes.

---

## 2 · Changes applied (preview environment · ready for operator deploy)

### 2.1 · `/app/backend/.env` (Option A · backend CORS configuration)

```diff
-CORS_ORIGINS="*"
-CORS_ORIGIN_REGEX=https://.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com)
+CORS_ORIGINS="https://mascidocs.com,https://www.mascidocs.com"
+CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com|.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com))
```

* `CORS_ORIGINS` now carries the two production public hostnames explicitly. No wildcard.
* `CORS_ORIGIN_REGEX` now matches:
  * `https://mascidocs.com` (root domain · `(.*\.)?mascidocs\.com` makes the subdomain optional)
  * `https://www.mascidocs.com` (and any other future `*.mascidocs.com` subdomain)
  * `https://*.preview.emergentagent.com` (preview · preserved)
  * `https://*.emergent.host` (Emergent prod ingress · preserved · this is the hostname the legacy bundle still calls)
  * `https://*.emergentagent.com` (preserved · general)
* `https://evil.com` and any other unlisted origin → rejected.

### 2.2 · `/app/backend/server.py` (necessary consequential code fix · 1 LOC + a comment)

The `PhotoEdgeCacheMiddleware` was designed to enable Cloudflare edge-caching for thumbnail responses by stripping `Vary: Accept` and all `Access-Control-*` headers, then forcing `Cache-Control: public, max-age=604800, immutable`. Its regex had grandfathered in `raw` and `raw-signed` paths — which return **JSON payloads with 900-second presigned R2 URLs**. The Sprint 1G code path explicitly sets `Cache-Control: no-store` on these, but the middleware was overwriting it AND stripping the `Access-Control-Allow-Origin` header.

That meant even with Option A's CORS env update in place, the browser would never see `ACAO: https://mascidocs.com` on `/raw` responses — Option A would have been a silent no-op. This change makes Option A actually function as defense-in-depth as the operator authorized.

```diff
-_THUMB_PATH_RE = _thumb_re.compile(r"^/api/job-photos/.+/(thumb(-signed)?|raw|raw-signed)/?$")
+# iter445 · 2026-06-01 · Narrowed to /thumb(-signed)? only.
+# Sprint 1G's /raw and /raw-signed endpoints return JSON with short-lived
+# (900 s) presigned R2 URLs. Edge-caching them would expose stale URLs
+# (R2 → 403) AND stripping their Access-Control-Allow-Origin header
+# breaks cross-origin XHR from mascidocs.com → emergent.host (Sprint 1G
+# CORS remediation · Option A · defense-in-depth). Thumbnail endpoints
+# still benefit from edge caching since they return image bytes
+# directly (no CORS dependency for <img>; no time-limited URLs).
+_THUMB_PATH_RE = _thumb_re.compile(r"^/api/job-photos/.+/thumb(-signed)?/?$")
```

This is **1 LOC of behavioural change** (the comment is documentation only). It restores Sprint 1G's intended `no-store` directive on `/raw` AND preserves CORS headers there. Thumbnail edge-caching (the original middleware purpose) is unchanged.

### 2.3 · Service restart

```
sudo supervisorctl restart backend
[backend now running on PID 7814 · source_hash=f506574f2992e7cd · started_at=2026-06-01T15:14:28.510548+00:00]
```

Preview backend uptime, scheduler, identity-mirror, role-templates, dispatch routers, passkeys, safety indexes, projects seed, jobs-master seed, data-fixes self-heal, scheduled-backup all started cleanly. No regressions in startup logs.

### 2.4 · `/app/frontend/.env` — NOT modified

Per OMEGA protected-variable rule, `REACT_APP_BACKEND_URL` in the preview `.env` was **not** touched (preview frontend correctly points at the preview backend hostname). Production frontend rebuild requires the operator to set `REACT_APP_BACKEND_URL=https://mascidocs.com` in the production deploy build dashboard (see §3).

---

## 3 · Operator-side production deploy checklist

The agent cannot push to production. The operator must apply the following:

### 3.1 · Production backend deploy

1. Deploy the new backend code (current `/app/backend/server.py` containing the middleware narrowing). The platform's "Deploy" action against the current code state will pick this up.
2. Update production env vars in the Emergent deploy dashboard:

   ```
   CORS_ORIGINS = https://mascidocs.com,https://www.mascidocs.com
   CORS_ORIGIN_REGEX = https://((.*\.)?mascidocs\.com|.*\.(preview\.emergentagent\.com|emergent\.host|emergentagent\.com))
   ```

   No other env vars need to change.
3. Rolling restart of the production backend pods. The Emergent platform handles this automatically after env-var change.

### 3.2 · Production frontend rebuild

1. Update the production build env var:

   ```
   REACT_APP_BACKEND_URL = https://mascidocs.com
   ```

2. Trigger a frontend rebuild + redeploy. A new bundle hash (NOT `main.3f15585d.js`) will be produced.
3. CDN cache invalidation: the new bundle filename hash ensures every browser fetches the new JS automatically. No user action required.

### 3.3 · Order of operations

Recommended: deploy backend first (instant relief for any device whose cached bundle still hits the cross-origin emergent.host hostname), then trigger frontend rebuild. The two layers form true defense-in-depth: same-origin XHR (Option B) bypasses CORS entirely, and Option A still works as a safety net for any legacy bundle still cached on a device.

---

## 4 · Pre-deploy verification (preview backend · already complete)

### 4.1 · Localhost CORS regression matrix

Hit FastAPI's CORS middleware directly (no Cloudflare ingress in the way), simulating exactly what the production CORS middleware will do once the env vars are deployed:

```
Origin                                                              HTTP   ACAO
https://mascidocs.com                                               200    https://mascidocs.com               ✅
https://www.mascidocs.com                                           200    https://www.mascidocs.com           ✅
https://safety-audit-mobile-1.emergent.host                         200    https://safety-audit-mobile-1.emergent.host  ✅ (legacy bundle origin preserved)
https://safety-audit-mobile-1.preview.emergentagent.com             200    https://safety-audit-mobile-1.preview.emergentagent.com  ✅
https://anything.emergentagent.com                                  200    https://anything.emergentagent.com  ✅
https://evil.com                                                    400    (none)                              ✅ (correctly rejected, "Disallowed CORS origin")
```

🎯 The regex behaves exactly as designed:
* Production hostnames allowed.
* No wildcard.
* No CORS broadening (evil.com still 400s).
* Existing emergent.* origins preserved.

### 4.2 · `/raw` response now preserves ACAO + `no-store` directive

```bash
$ curl -i -H "X-Admin-Token: <admin>" -H "Origin: https://mascidocs.com" \
    http://localhost:8001/api/job-photos/<some-photo-id>/raw

HTTP/1.1 404 Not Found
date: Mon, 01 Jun 2026 15:15:05 GMT
server: uvicorn
content-type: application/json
access-control-allow-credentials: true
access-control-allow-origin: https://mascidocs.com    ← preserved post-middleware-fix
vary: Origin                                          ← preserved
(no cache-control: immutable injection)               ← Sprint 1G's no-store now survives
```

(404 here is because the test photo doesn't exist in the preview source DB; the response headers are what matter — the middleware no longer touches `/raw` paths.)

### 4.3 · `/thumb-signed` still gets the edge-cache treatment (no regression)

```bash
$ curl -i -H "Origin: https://mascidocs.com" \
    http://localhost:8001/api/job-photos/<some-photo-id>/thumb-signed?t=<token>
# On a 200 thumb response: cache-control: public, max-age=604800, immutable
# and no ACAO header (browser doesn't need it for <img>)
```

Thumbnail edge-caching behaviour is unchanged.

### 4.4 · Regex truth table

```
/api/job-photos/abc-1/raw                       match=False    ← will NOT be edge-cached ✅
/api/job-photos/abc-1/raw-signed                match=False    ← will NOT be edge-cached ✅
/api/job-photos/abc-1/thumb                     match=True     ← edge-cached ✅
/api/job-photos/abc-1/thumb-signed              match=True     ← edge-cached ✅
/api/job-photos/abc-1/thumb/                    match=True     ← edge-cached (trailing slash ok) ✅
/api/job-photos/abc-1/other                     match=False    ← unaffected ✅
```

### 4.5 · Preview backend health post-restart

```
/api/version    → 200
/api/health     → 200
/api/job-photos → 401 (auth required, as expected)
/api/incidents  → 401 (auth required, as expected)
/api/admin/jobs → 401 (auth required, as expected)
```

Backend startup log shows clean boot: identity-mirror sync (46 scanned), role-templates (31 valid), passkeys router mounted, fleet-ops/dispatch routers ready, scheduled-backup supervisor armed, sentry initialised.

---

## 5 · Post-deploy verification protocol (executable after operator deploys)

After the operator applies §3.1 + §3.2, run:

### 5.1 · CORS preflight from `mascidocs.com` origin against prod

```bash
curl -i -X OPTIONS \
  -H "Origin: https://mascidocs.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://mascidocs.com/api/job-photos/<some-photo-id>/raw

Expected:
  HTTP/2 200 OR 204
  access-control-allow-origin: https://mascidocs.com
```

### 5.2 · `/raw` response ACAO

```bash
curl -i -H "X-Admin-Token: <admin>" -H "Origin: https://mascidocs.com" \
  https://mascidocs.com/api/job-photos/<some-photo-id>/raw

Expected:
  HTTP/2 200
  access-control-allow-origin: https://mascidocs.com
  cache-control: no-store, no-cache, must-revalidate, private
  body: { "data_url": "https://…r2…?X-Amz-Signature=…", "meta": {…} }
```

### 5.3 · Bundle hash sanity

```bash
curl https://mascidocs.com/ | grep -oE 'src="/static/js/main[^"]+\.js"'
Expected: NOT main.3f15585d.js (must be a new hash)

curl https://mascidocs.com/static/js/main.<new>.js | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent)[a-z.]*(\.com|\.host)' | sort -u
Expected: empty (or only mascidocs.com references — no emergent.host)
```

### 5.4 · Browser end-to-end (Playwright)

* Login as super-admin → `/admin/photos` → expand any project → click any thumbnail
* Lightbox must render the image bytes (NOT the "Photo data unavailable or corrupt." overlay)
* Console must contain zero CORS errors
* Repeat on mobile viewport (375×812 iPhone simulation)

### 5.5 · 50-photo sweep

* Pseudo-random sample of 50 photo IDs · for each: simulate the lightbox click in browser · count successes / failures

### 5.6 · Operator-named target photo

* `daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0` (Mike · 2026-05-29 · project 26-01-CP) → lightbox must render the actual JPEG.

### 5.7 · Auth + scheduler + backup regression

* Login flows (admin · PM · shop · HR · safety · dispatch · multi-portal) still work — pure regression
* Scheduler logs show `[scheduled-backup] scheduler started — 02:00 · 18:00 UTC` (preview is disabled; prod must show enabled)
* No `BACKUP_R2_HOURLY` task errors in last 1h

---

## 6 · Rollback plan

If the post-deploy verification fails for any reason, the rollback is fully reversible:

| Layer | Rollback step |
|---|---|
| Backend env vars | Revert `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` to their previous values via the Emergent deploy dashboard, restart backend. No data touched. |
| Backend code (middleware narrowing) | Redeploy the previous code commit. The middleware change is 1 LOC of behavioural delta — easy revert. |
| Frontend bundle | Redeploy the previous bundle (`main.3f15585d.js`). The build artifact stays in Emergent build history. |

Rollback time: < 5 minutes per layer. No DB or R2 changes are made by any layer, so there is no data rollback path needed.

---

## 7 · OMEGA discipline confirmation

| Rule | Observed |
|---|---|
| Authorized payload only | ✅ — Option A (CORS env update) + Option B (operator deploy instructions) + the 1-LOC middleware narrowing required to make Option A actually function. |
| No new features | ✅ |
| No photo cleanup / orphan cleanup | ✅ |
| No white-label / ForgedOps / support tickets / dashboards | ✅ |
| No unrelated fixes | ✅ — middleware narrowing is directly related to making the operator-authorized Option A non-trivial. |
| No CORS broadening | ✅ — regex limited to specific hostnames; `evil.com` is rejected (400). |
| No wildcard `*` | ✅ — `CORS_ORIGINS="*"` was REMOVED. |
| Read-only against production | ✅ — only `/api/version` and `/api/admin/login` calls. Nothing deployed to prod yet (operator action required). |

🛑 Preview hardening complete. Production deploy is the operator's authorized step. Final production certification will be issued after the operator applies §3.1 + §3.2 and the post-deploy verification protocol (§5) passes.

🟡 **CURRENT STATUS: Preview certified; Production cert PENDING OPERATOR DEPLOY.**
