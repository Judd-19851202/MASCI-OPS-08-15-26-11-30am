# LIVE PRODUCTION · HEALTH REPORT
## OMEGA Directive · Phase 1 of 10

**Date**: 2026-06-03 (09:23 UTC probe window)
**Target**: https://mascidocs.com (production)
**Probe vector**: External anonymous HTTPS probes from preview pod

---

## 🟢 PHASE 1 VERDICT — PRODUCTION HEALTH CERTIFIED

---

## 1 · Surface health

| Probe | Status | Latency | Notes |
|---|:-:|---:|---|
| `GET /` (homepage) | 200 | 455 ms | HTML 8.3 KB, title `MASCI Operations Platform` |
| `GET /login` | 200 | 379 ms | SPA fallback |
| `GET /hr-login` | 200 | 420 ms | SPA fallback |
| `GET /api/health` | 200 | 258 ms | `{"ok":true,"service":"masci-hub","ts":"2026-06-03T09:23:24Z"}` |
| `GET /static/js/main.737c64e7.js` (bundle) | 200 | 413 ms | Bundle size 5.00 MB, served via Cloudflare |
| `GET /api/version` | 200 | — | release hash `ab213a4955…`, started_at `2026-06-03T09:21:50Z`, uptime 149 s at probe |

**Frontend routes (SPA fallback smoke)** — all returned 200:
- `/` `/login` `/hr-login` `/safety-portal` `/fl-portal` `/dispatch-portal` `/admin` `/recovery`

---

## 2 · Backend configuration (exposed via `/api/version`)

```json
{
  "service": "masci-hub",
  "release": "ab213a495518ae7fac93b60cad6d7c1e",
  "started_at": "2026-06-03T09:21:50.266622+00:00",
  "session_timeouts": {
    "ADMIN_HR":    {"idle_min": 15, "abs_hour": 4},
    "OPERATIONS":  {"idle_min": 30, "abs_hour": 8},
    "FIELD":       {"idle_min": 60, "abs_hour": 12}
  },
  "sentry": {"enabled": true},
  "app_env": "production",
  "db_name": "masci_safety"
}
```

🟢 `app_env=production` · Sentry enabled · session timeout tiers configured · DB name correct.

**Note**: `commit` and `built_at` report `unknown` — version stamping is not wired through the deploy pipeline. Cosmetic LOW; tracked in Stability Review §3.

---

## 3 · Security posture (response headers)

| Header | Value | Verdict |
|---|---|:-:|
| `strict-transport-security` | `max-age=63072000; includeSubDomains; preload` | 🟢 |
| `x-content-type-options` | `nosniff` | 🟢 |
| `server` | `cloudflare` | 🟢 (edge + DDOS protection) |
| `content-security-policy` | not set | 🟡 pre-existing posture; out of delta scope |
| `x-frame-options` | not set | 🟡 pre-existing posture; out of delta scope |
| `CORS preflight` (`OPTIONS /api/health`) | 405 | 🟡 method not enabled — typical FastAPI behaviour for endpoints without CORS preflight; benign for same-origin SPA. |

---

## 4 · Negative checks

| Item | Result |
|---|:-:|
| White-screen / blank HTML on homepage | 🟢 NONE (8.3 KB shell + valid title rendered) |
| Infinite loading on JS bundle | 🟢 NONE (bundle loads in 413 ms) |
| Health endpoint returns 5xx | 🟢 NONE |
| Backend startup failure | 🟢 NONE (uptime stable + health OK) |
| Production console explosions | ⚠️ Cannot probe from outside — operator browser DevTools required |

---

## 5 · Limitations of this probe set

This phase verifies **anonymous surface health only**. The following CANNOT be verified from external probes and require operator-side validation:
- Browser console errors on key pages → operator must open DevTools on `/`, `/login`, `/admin`, `/recovery`, `/fl-portal`.
- Hot-path latency (DB-backed routes that require auth) → operator-side walkthrough.

---

## 6 · Phase 1 outcome

🟢 **PRODUCTION HEALTH CERTIFIED** for all externally probable surfaces.
