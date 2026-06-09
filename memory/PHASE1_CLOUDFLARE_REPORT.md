# PHASE 1A · CLOUDFLARE CACHE — VERIFICATION & OPERATOR RUNBOOK

**Sprint:** PLATFORM-EXCELLENCE · PHASE 1 CLOSEOUT
**Scope:** Phase 1A — Cloudflare cache verification & correction
**Authorization:** Operator chat 2026-06-09
**Date:** 2026-06-09
**Status:** 🟡 **VERIFICATION COMPLETE · CORRECTION REQUIRES OPERATOR CLOUDFLARE ACCESS**

> **Why this report is verification-only:** Cloudflare configuration is managed via the Cloudflare dashboard or REST API, both of which require a Cloudflare API token / account login. The Preview container has no Cloudflare credentials. Per the OMEGA core rule *"production stability is more important than chasing scores · if any action introduces risk to existing workflows, STOP and report"*, the agent stopped at verification and authored this runbook for the operator.

---

## 1 · BEFORE state — production response headers

Captured live against `https://mascidocs.com` on **2026-06-09T23:28:25Z**.

### 1.1 · JavaScript chunk (`/static/js/main.0c1c410f.js`)
```
HTTP/2 200
content-type: application/javascript; charset=utf-8
content-length: 5,704,899
cache-control: public, max-age=300, immutable        ← PROBLEM
etag: "3ad26742ee1fe2ba805ed1851962ac61"
set-cookie: __cf_bm=…; HttpOnly; SameSite=None; Secure; Path=/; Domain=mascidocs.com
server: cloudflare
cf-ray: a093e99ccf77cc1a-ORD
(no cf-cache-status header — see §1.4)
```

### 1.2 · CSS chunk (`/static/css/main.7a3dbc01.css`)
```
HTTP/2 200
content-type: text/css; charset=utf-8
content-length: 163,440
cache-control: public, max-age=300, immutable        ← PROBLEM
etag: "b7249edf642d66545868cbec73ca7f3a"
server: cloudflare
```

### 1.3 · HTML index (`/`)
```
HTTP/2 200
content-type: text/html; charset=utf-8
cache-control: public, max-age=300                   ← CORRECT for HTML (no immutable)
server: cloudflare
```

### 1.4 · Edge-cache probe — three sequential requests for the same JS chunk
| Probe | `cf-ray` (unique per request) | `cf-cache-status` | `age` |
| --- | --- | --- | --- |
| 1 | a093ebc1686135c0-ORD | **MISSING** | missing |
| 2 | a093ebc99fec9bcc-ORD | **MISSING** | missing |
| 3 | a093ebd1898c0010-ORD | **MISSING** | missing |

**Diagnosis:** Cloudflare is **NOT** caching `/static/*` at the edge. Every field-iPad request for a JS chunk hits the origin (Google Cloud Run via Cloudflare). The likely root cause is the `Set-Cookie: __cf_bm=…` (Cloudflare bot management) on the response, which by default disables edge caching unless a Cache Rule explicitly says *Cache Everything*.

### 1.5 · Problems summarised

| # | Finding | Severity |
| --- | --- | --- |
| 1 | `Cache-Control: max-age=300` on immutable JS / CSS chunks (should be `max-age=31536000`) | High |
| 2 | `immutable` directive set with `max-age=300` — internally contradictory | Medium |
| 3 | No `cf-cache-status` header → Cloudflare not edge-caching at all → 100 % requests hit origin | **HIGHEST** — the cache TTL doesn't matter if nothing is cached |
| 4 | Browser caches for 5 minutes only — every LTE iPad re-downloads ~5.7 MB of JS every 5 min | High |

---

## 2 · TARGET state

| Path | `Cache-Control` | Edge Cache TTL | Browser Cache TTL | Cache Level |
| --- | --- | --- | --- | --- |
| `/static/*` | `public, max-age=31536000, immutable` | 1 year | 1 year | **Cache Everything** |
| `/*.js`, `/*.css` (defensive) | same | same | same | same |
| `/` (HTML index) | `public, max-age=300` (unchanged) | bypass | 5 min | Standard |
| `/api/*` | (unchanged — `cf-cache-status: DYNAMIC`) | bypass | bypass | Bypass |

---

## 3 · OPERATOR RUNBOOK — exact steps

### 3.1 · Cloudflare dashboard path (recommended for first run)

1. Log in to **Cloudflare dashboard** → select zone **mascidocs.com**.
2. Sidebar → **Caching → Cache Rules** (new product; replaces legacy *Page Rules*).
3. Click **Create rule**.
4. Configure:
   ```
   Rule name: MASCI static assets · 1y immutable
   When incoming requests match:
     URI Path starts with /static/
   Then:
     ✅ Cache eligibility: Eligible for cache
     ✅ Edge TTL: Override origin → 1 year (31536000)
     ✅ Browser TTL: Override origin → 1 year (31536000)
     ✅ Cache Level: Cache Everything
     ✅ Respect strong ETags: ON (already set on origin)
   ```
5. **Deploy** the rule.
6. (Optional, separate rule) for `/api/*`: explicit **Bypass cache** to make intent clear.

### 3.2 · Verify with curl (operator should run after deploy)

```bash
JS_URL=$(curl -s https://mascidocs.com | grep -oE '/static/js/main\.[a-z0-9]+\.js' | head -1)
echo "Probing: https://mascidocs.com$JS_URL"
for i in 1 2 3; do
  echo "--- Probe $i ---"
  curl -sI "https://mascidocs.com$JS_URL" | grep -iE "cache-control|cf-cache-status|age|cf-ray"
  sleep 1
done
```

**Pass criteria:**
- `cache-control: public, max-age=31536000, immutable` ✓
- `cf-cache-status: HIT` (after first warm-up request) ✓
- `age: <seconds-since-edge-warmup>` ✓

### 3.3 · Rollback (if anything breaks)
Disable the Cache Rule in the Cloudflare dashboard. Edge cache will purge naturally; field devices will resume their previous 5-minute TTL behaviour within minutes.

---

## 4 · Risk assessment

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Stale JS served to users after a deploy | **Low** — Create-React-App writes content-hashed filenames (`main.0c1c410f.js`). A new deploy emits a new filename; the old one is referenced only by users with stale `index.html`, who already re-fetch HTML every 5 min. | Already-correct hashed-bundle pipeline; no change needed |
| Cache poisoning of a chunk | **Low** — CF respects strong `ETag` already on the origin | Keep `Respect strong ETags: ON` |
| Browser pinning a buggy build for a year | **Low** — `index.html` still has `max-age=300`; new deploys produce new hashed filenames; users naturally migrate within 5 min of any deploy | None needed |
| Cache stampede during the first warmup after deploy | **Negligible** — content is static and small | None needed |

---

## 5 · Expected impact

| Metric | Before | After (forecast) |
| --- | ---: | ---: |
| % of `/static/*` requests served from edge | ~0 % (no `cf-cache-status: HIT` seen) | **≥99 %** after warm-up |
| Cold-load JS over LTE for repeat field iPad | ~5.7 MB every 5 min | **~5.7 MB once / year** |
| Origin egress for `/static/*` | full traffic | near-zero |
| Production Readiness pillar | 91 | **92** (+1) |

---

## 6 · Verdict

| Component | Status |
| --- | --- |
| Verification of BEFORE state | ✅ **DONE** (this report) |
| Operator runbook | ✅ **DONE** (§3 above) |
| Validation script (AFTER) | ✅ **DONE** (§3.2) |
| Configuration change | ⏳ **PENDING OPERATOR** — requires Cloudflare zone admin |

**Agent-deliverable portion: 🟢 COMPLETE.**
**Cloudflare configuration change: 🟡 AWAITS OPERATOR EXECUTION.**
