# Photo Viewer Production Certification

**Batch:** OMEGA · Photo Viewer CORS Remediation · Option C (A + B defense-in-depth)
**Mode:** Final production certification (executable after operator deploy)
**Date:** 2026-06-01 (preview hardening complete · production deploy pending operator)
**Companion:** `PHOTO_VIEWER_CORS_REMEDIATION_REPORT.md` · `PHOTO_VIEWER_BROWSER_CERTIFICATION.md`

---

## 1 · Current verdict

# 🟡 PRODUCTION CERTIFICATION PENDING OPERATOR DEPLOY

The preview environment has been hardened with the operator-authorized Option C changes and verified end-to-end (`PHOTO_VIEWER_BROWSER_CERTIFICATION.md`). The same changes must be deployed to the production environment by the operator before final certification can be issued.

Per OMEGA discipline, this agent cannot push to production. The operator's authorized action set is documented in §3 of `PHOTO_VIEWER_CORS_REMEDIATION_REPORT.md` and re-summarized in §2 below.

This certification document is the executable verification plan; when the operator authorizes a follow-up Batch (or signals that production has been deployed), every check below will be run against `https://mascidocs.com` and the final 🟢 or 🔴 verdict will be filled in at §10.

---

## 2 · Operator deploy actions required (one-time)

| Step | Action | Where |
|---|---|---|
| 1 | Deploy current `/app/backend/server.py` (carries the `PhotoEdgeCacheMiddleware` regex narrowing · iter445) | Emergent production deploy |
| 2 | Set `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com` | Emergent production env-var dashboard |
| 3 | Set `CORS_ORIGIN_REGEX=https://((.*\.)?mascidocs\.com\|.*\.(preview\.emergentagent\.com\|emergent\.host\|emergentagent\.com))` | Emergent production env-var dashboard |
| 4 | Rolling restart of production backend pods | Triggered automatically by env-var change |
| 5 | Set production frontend build env: `REACT_APP_BACKEND_URL=https://mascidocs.com` | Emergent production deploy dashboard |
| 6 | Trigger frontend rebuild + redeploy | Emergent production deploy |

After steps 1-6, run the verification protocol below.

---

## 3 · Phase 1 · Pod inventory + build verification

### 3.1 · Production pod identity check

```bash
curl https://mascidocs.com/api/version
```

Expected `source_hash` ≠ `2383567f4f9735cf936d90dce26bb267` (pre-fix). Expected `started_at` ≈ within the deploy window. Expected `app_env=production`, `db_name=masci_safety`.

### 3.2 · Production frontend bundle check

```bash
curl https://mascidocs.com/ | grep -oE 'src="/static/js/main[^"]+\.js"'
```

Expected: bundle filename hash ≠ `main.3f15585d.js`.

```bash
curl https://mascidocs.com/static/js/main.<NEW_HASH>.js \
  | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent|mascidocs)[a-z.]*(\.com|\.host)' | sort -u
```

Expected: only `https://mascidocs.com` (no `emergent.host` baked in).

### 3.3 · Verdict — Phase 1

🟡 To be filled in post-deploy: pod hash ____, bundle hash ____, embedded API URL ____.

---

## 4 · Phase 2 · CORS preflight verification (curl-level)

```bash
# Test 1: mascidocs.com origin must succeed
curl -i -X OPTIONS \
  -H "Origin: https://mascidocs.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://mascidocs.com/api/job-photos/test/raw

Expected: 200 (or 204) WITH access-control-allow-origin: https://mascidocs.com
```

```bash
# Test 2: www.mascidocs.com origin
curl -i -X OPTIONS \
  -H "Origin: https://www.mascidocs.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://mascidocs.com/api/job-photos/test/raw

Expected: 200 (or 204) WITH access-control-allow-origin: https://www.mascidocs.com
```

```bash
# Test 3: emergent.host origin (legacy bundle compatibility)
curl -i -X OPTIONS \
  -H "Origin: https://safety-audit-mobile-1.emergent.host" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://safety-audit-mobile-1.emergent.host/api/job-photos/test/raw

Expected: 200 WITH access-control-allow-origin: https://safety-audit-mobile-1.emergent.host
```

```bash
# Test 4 (NEGATIVE): evil.com origin must be REJECTED
curl -i -X OPTIONS \
  -H "Origin: https://evil.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-admin-token,content-type" \
  https://mascidocs.com/api/job-photos/test/raw

Expected: 400 Bad Request "Disallowed CORS origin" · NO access-control-allow-origin header
```

### Verdict — Phase 2

🟡 Test 1 ___ · Test 2 ___ · Test 3 ___ · Test 4 ___.

---

## 5 · Phase 3 · `/raw` response cache + CORS verification

```bash
TOKEN=<admin>
curl -i -H "X-Admin-Token: $TOKEN" -H "Origin: https://mascidocs.com" \
  "https://mascidocs.com/api/job-photos/daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0/raw?_=$(date +%s%N)"

Expected:
  HTTP/2 200
  access-control-allow-origin: https://mascidocs.com           ← MUST be present
  cache-control: no-store, no-cache, must-revalidate, private  ← Sprint 1G directive preserved
  pragma: no-cache
  content-type: application/json
  body: { "data_url": "https://46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com/masci-hub/photos/2026/05/dr_07e54a58…/85e97aff….jpg?X-Amz-Signature=…", "meta": {…} }
```

Critical absence: NO `cache-control: public, max-age=604800, immutable` (the iter437 P0 pattern must NOT be re-introduced).

### Verdict — Phase 3

🟡 ACAO present ___ · cache-control no-store ___ · presigned URL valid ___.

---

## 6 · Phase 4 · End-to-end browser test (Playwright Chromium · desktop 1440×900)

```python
1. await page.goto("https://mascidocs.com/admin/login")
2. Fill email/password, sign in as jaymn.judd@mascigc.com / Maddix123!
3. await page.goto("https://mascidocs.com/admin/photos")
4. Click project folder "NSB Corbin Park Stormwater Improvements" (#26-01-CP)
5. Click first thumbnail (the operator-named target: daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0)
6. Verify:
   - lightbox modal opens
   - <img> element with naturalWidth > 0 is present
   - "Photo data unavailable or corrupt." string is NOT present
7. Capture browser console: must be free of CORS errors
8. Capture network log: /raw must return 200 with access-control-allow-origin
9. Screenshot the lightbox showing the rendered photo
```

### Verdict — Phase 4 (desktop)

🟡 Operator-named target renders ___ · console clean ___ · screenshot saved ___.

---

## 7 · Phase 5 · End-to-end browser test (Playwright Chromium · mobile 375×812 iPhone 13)

Same as Phase 4 but with mobile viewport:

```python
page.set_viewport_size({"width": 375, "height": 812})
```

### Verdict — Phase 5 (mobile)

🟡 Lightbox renders on mobile ___ · no error overlay ___ · screenshot saved ___.

---

## 8 · Phase 6 · 50-photo random sample sweep

* Pull the full `/api/job-photos` list from production (606 photos).
* `random.seed(20260601)` → sample 50 photo IDs (same seed as Sprint 1G's failed recheck for direct comparison).
* For each: open lightbox in Playwright, verify `<img>` renders with `naturalWidth > 0`, verify no error overlay.
* Tally: target = 50/50 pass.

### Verdict — Phase 6

🟡 Passes ___ / 50. Failure list (if any): ___.

---

## 9 · Phase 7 · Regression matrix

Check that the remediation broke nothing else:

| Surface | Test | Expected | Actual |
|---|---|---|---|
| Thumbnail grid | `/admin/photos` loads with thumbnails rendered | All 606 photos' thumbnails visible | ___ |
| Auth · admin login | `/admin/login` → POST `/api/admin/login` | 200 token issued | ___ |
| Auth · PM portal | `/pm/login` → multi-login | 200 token issued | ___ |
| Auth · HR portal | `/hr/login` | 200 token issued | ___ |
| Auth · safety portal | `/safety-portal/login` | 200 token issued | ___ |
| Auth · dispatch portal | `/dispatch-portal/login` | 200 token issued | ___ |
| Auth · shop portal | `/shop/login` | 200 token issued | ___ |
| Daily Reports list | `GET /api/daily-reports` (admin) | 200, results | ___ |
| Incidents list | `GET /api/incidents` (admin) | 200, results | ___ |
| Inspections list | `GET /api/inspections` (admin) | 200, results | ___ |
| Scheduler · backup cron | Backend startup log shows `[scheduled-backup] scheduler started` | enabled on prod | ___ |
| Scheduler · hourly R2 backup | `BACKUP_R2_HOURLY=true` task running without errors in last hour | no errors | ___ |
| Recovery · most recent backup_runs row | `db.backup_runs.find_one(sort=[('ts',-1)])` returns status="success" within last 25h | success | ___ |
| Sentry events | No new CORS-related Sentry events in last hour | clean | ___ |
| Photo ZIP download | Select 3 photos · click "Download ZIP" · receive valid zip | valid zip | ___ |
| Photo email | Select 1 photo · send to dev account · receive email | email sent | ___ |
| Re-index button | Click `/admin/photos` re-index button | success toast | ___ |

### Verdict — Phase 7

🟡 ___ pass · ___ regressions.

---

## 10 · Final verdict (to be filled in post-deploy)

🟡 **PENDING OPERATOR DEPLOY**

When operator confirms deploy:

* If Phases 1-7 all 🟢 → 🟢 **PHOTO VIEWER PRODUCTION CERTIFIED**
* If any Phase 🔴 → 🔴 **PHOTO VIEWER STILL FAILING** (with attached failure inventory)

---

## 11 · Failure handling

If post-deploy verification fails on any phase:

1. Capture exact phase + error + browser console + network log.
2. Roll back per `PHOTO_VIEWER_CORS_REMEDIATION_REPORT.md` §6 (env-var revert OR frontend bundle revert).
3. Issue a follow-up forensic Batch authorization to re-investigate.

No partial-success workaround is acceptable: either the photo viewer renders 100% of resolvable photos in production, or the verdict is 🔴.

---

## 12 · OMEGA discipline confirmation (for this certification doc)

| Rule | Observed |
|---|---|
| Read-only against production | ✅ — no deploy, no code, no DB writes attempted by the agent |
| Verification plan deterministic | ✅ — each phase has explicit expected values and pass/fail criteria |
| Negative tests included | ✅ — evil.com origin must be rejected (Phase 2 Test 4) |
| Mobile included | ✅ — Phase 5 |
| Auth + scheduler + backup regression included | ✅ — Phase 7 |
| Operator-named target photo included | ✅ — Phase 4 |
| 50-photo sweep included | ✅ — Phase 6 |
| Out-of-scope topics avoided | ✅ — no orphan cleanup, no white-label, no ForgedOps, no dashboards |

🛑 Production certification PENDING. Awaiting operator deploy signal to execute Phases 1-7 and issue the final verdict.

---

## 13 · Quick-run script (for executing this certification post-deploy)

```bash
#!/bin/bash
# Run with: bash post_deploy_cert.sh

set -e
PROD=https://mascidocs.com

echo "Phase 1.1 · pod identity:"
curl -s "$PROD/api/version" | python3 -m json.tool | head -10

echo "Phase 1.2 · frontend bundle:"
BUNDLE=$(curl -s "$PROD/" | grep -oE 'src="/static/js/main[^"]+\.js"' | head -1)
echo "  $BUNDLE"

echo "Phase 1.3 · embedded backend URL in bundle:"
JSURL=$(echo "$BUNDLE" | sed 's/src="//;s/"//')
curl -s "$PROD$JSURL" | grep -oE 'https://[a-z0-9-]+\.(emergent|emergentagent|mascidocs)[a-z.]*(\.com|\.host)' | sort -u

echo "Phase 2 · CORS preflight matrix:"
for O in "https://mascidocs.com" "https://www.mascidocs.com" "https://evil.com"; do
  printf "  Origin %-40s -> " "$O"
  curl -s -o /dev/null -w "%{http_code} ACAO=" -X OPTIONS \
    -H "Origin: $O" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: x-admin-token,content-type" \
    "$PROD/api/job-photos/test/raw"
  curl -s -X OPTIONS -i \
    -H "Origin: $O" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: x-admin-token,content-type" \
    "$PROD/api/job-photos/test/raw" | grep -i "access-control-allow-origin" | head -1
done

echo "Phase 3 · /raw cache + CORS:"
TOKEN=$(curl -s -X POST "$PROD/api/admin/login" -H "Content-Type: application/json" -d '{"password":"MASCI1982!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -s -i -H "X-Admin-Token: $TOKEN" -H "Origin: https://mascidocs.com" \
  "$PROD/api/job-photos/daily_report:07e54a58-61f5-46b2-a755-8dc4582a5a94:0/raw?_=$(date +%s%N)" \
  | grep -iE "(HTTP|access-control-allow-origin|cache-control)" | head -5
```

Then run the Playwright phases 4-7 from the agent.
