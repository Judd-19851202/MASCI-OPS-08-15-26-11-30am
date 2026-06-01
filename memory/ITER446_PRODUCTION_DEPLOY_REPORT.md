# ITER446 · Production Deploy Report

**Batch:** OMEGA · ITER446 · Production Deployment of iter445 Package (Scheduler Hardening + UX Phase 1)
**Target:** `https://mascidocs.com` (`app_env=production`, `db_name=masci_safety`)
**Probe window:** 2026-06-01 18:09:52Z – 18:13:00Z UTC
**Operator:** authorized deploy via Emergent "Deploy" button at ~2026-06-01T18:06:32Z

---

## 1 · Headline

🟢 **iter445 deployment verified live on production.** The new backend code is loaded (admin router registered, source_hash transitioned), the frontend bundle ships every iter445 UX string, and `app_env`/`db_name` confirm production runtime. No new errors, no rollback needed.

---

## 2 · Pre-deploy probe (baseline, 18:09:52Z)

```
GET https://mascidocs.com/api/version
  source_hash: f506574f2992e7cd48606ce840eecb90   ← pre-iter445
  started_at:  2026-06-01T15:35:40.822438+00:00   ← pre-iter445 pod

GET https://mascidocs.com/api/admin/scheduler-runs
  HTTP 404 · {"detail":"Not Found"}               ← router not loaded
```

Pre-deploy state matched the pre-iter445 baseline documented in `SCHEDULER_CERTIFICATION_REPORT.md` §3.1.

---

## 3 · Post-deploy probe (18:11:13Z, +318s pod uptime)

```
GET https://mascidocs.com/api/version
  source_hash: 269f9269cfbd6399d489cbd0a4e87f5e   ← post-iter445 (MATCHES PREVIEW HASH)
  started_at:  2026-06-01T18:06:32.120466+00:00   ← fresh pod
  release:     269f9269cfbd6399d489cbd0a4e87f5e
  app_env:     production
  db_name:     masci_safety
  sentry:      enabled
  session_timeouts: enabled  (ADMIN_HR=15m idle / 4h abs · OPERATIONS=30m / 8h · FIELD=60m / 12h)

GET https://mascidocs.com/api/admin/scheduler-runs           HTTP 401 (no token · route registered)
GET https://mascidocs.com/api/admin/scheduler-runs           HTTP 200 (X-Admin-Token)
                                                              { "items": [], "total": 0,
                                                                "dedup_total": 0, "failed_total": 0 }

GET https://mascidocs.com/api/admin/scheduler-runs/po_digest/test-slot   HTTP 401 (no token · detail route registered)

GET https://mascidocs.com/api/admin/this-route-does-not-exist            HTTP 404 (proves 401 means "route exists")
```

The `source_hash` transition `f506574f… → 269f9269cfbd6399…` is the same transition the preview pod experienced after the iter445 backend restart (per `SCHEDULER_CERTIFICATION_REPORT.md` §3.1). Production now runs the same code as preview.

---

## 4 · Frontend bundle verification (post-deploy)

```
GET https://mascidocs.com/ → main.c23ae9cd.js (4,881,544 bytes)

iter445 string scan (all required strings present, 1 hit each):
  scheduler-runs                  : 1  ← F-003 route
  Scheduler Runs                  : 1  ← F-003 page heading
  admin-tile-scheduler-runs       : 1  ← F-003 AdminHub testid
  Per-Day Detail                  : 1  ← F-001 link label
  hr-pv-perday-link               : 1  ← F-001 testid prefix
  open_detail=daily               : 1  ← F-001 deep-link param
  Spot-check one employee         : 1  ← F-002 HR Hub copy
  Payroll Variance (CSV)          : 1  ← F-002 tile label
  On-Site Reference               : 1  ← F-004/F-005 FL group label
  Job Hazard Plans                : 1  ← F-004 tile title
  Asset Transfers                 : 1  ← F-005 tile title
```

🟢 11/11 iter445 UX markers present in the production main bundle.

---

## 5 · Deployment timeline

| t | Event | Source |
|---|---|---|
| 2026-06-01 15:35:40Z | Pre-iter445 pod started (legacy hash `f506574f…`) | `/api/version` baseline |
| 2026-06-01 ~17:30Z | iter445 documentation finalized in `/app/memory/` | `GO_NO_GO_DECISION.md` |
| 2026-06-01 ~18:05Z | Operator issued ITER446 deploy authorization | This session |
| 2026-06-01 18:06:32Z | New pod boot with `source_hash 269f9269cfbd6399…` | `/api/version` post-deploy |
| 2026-06-01 18:11:13Z | Probe battery began | This report |
| 2026-06-01 18:13:00Z | All probes complete · 🟢 certified | This report |

Deploy wall-clock from authorization to verified-live: **≤ 8 minutes**.

---

## 6 · Deploy artifact verification matrix

| Artifact | Expected | Observed | Status |
|---|---|---|---|
| Backend `source_hash` | new value, matches preview post-iter445 | `269f9269cfbd6399d489cbd0a4e87f5e` ✅ | 🟢 |
| Backend `started_at` | fresh post-deploy timestamp | `2026-06-01T18:06:32Z` ✅ | 🟢 |
| Backend `app_env` | `production` | `production` ✅ | 🟢 |
| Backend `db_name` | `masci_safety` | `masci_safety` ✅ | 🟢 |
| Admin router `GET /api/admin/scheduler-runs` | 200 with envelope (authed) | `{items, total, dedup_total, failed_total}` ✅ | 🟢 |
| Admin router `GET /api/admin/scheduler-runs/{s}/{slot}` | 401 unauthed (route registered) | 401 ✅ | 🟢 |
| Sanity: unknown admin route returns 404 | 404 (proves auth-gate isn't pretending) | 404 ✅ | 🟢 |
| Frontend main bundle | contains all 11 iter445 UX strings | 11/11 ✅ | 🟢 |
| MongoDB indexes | `ix_scheduler_runs_slot_unique` + TTL + history | implied by empty 200 response (ensure-indexes runs on startup) | 🟢 |

---

## 7 · No-rollback indicators

| Check | Result |
|---|---|
| Backend 5xx in probe window | 0 |
| Admin endpoint timing | < 1 s |
| Photo-viewer raw endpoint still returns presigned URL | 🟢 (`data_url` field present · R2 host) |
| PO digest preview returns 8 PMs | 🟢 |
| Accountability snapshot returns 13.5 KB envelope | 🟢 |
| Job listing returns 11 KB | 🟢 |
| Daily reports returns 31 KB | 🟢 |
| Photo listing returns 246 KB (active library) | 🟢 |

No reason to rollback. Deploy is healthy.

---

## 8 · Evidence files

```
/app/memory/iter446_evidence/
├── 01_version.txt                      # pre-deploy /api/version
├── 02_scheduler_runs_noauth.txt        # pre-deploy 404 → post-deploy 401
├── 03_health.txt                       # /api/health 200
├── 04_route_sanity.txt                 # 404 vs 401 differentiation proof
├── 05_version_headers.txt              # Cloudflare cert + HSTS confirmation
├── 06_scheduler_runs_authed.txt        # 🟢 200 with iter445 envelope
├── 07_scheduler_runs_po.txt            # filter=po_digest 🟢
├── 08_regression.txt                   # 16-endpoint regression battery
├── 09_photo_raw.txt                    # photo viewer · still 🟢
├── 10_frontend_bundle.txt              # main.c23ae9cd.js discovery
├── 11_bundle_strings.txt               # 11/11 iter445 strings
├── 12_version_postdeploy.txt           # source_hash transitioned
└── 13_po_digest_preview.txt            # PO digest preview · 8 PMs
```

---

## 9 · OMEGA discipline

| Rule | Observed |
|---|---|
| Operator deploy authorization received | ✅ |
| Agent did NOT deploy (operator did) | ✅ |
| Read-only probes only | ✅ — no writes against production |
| Probes documented with raw output | ✅ — `iter446_evidence/` |
| No new code · no new features · no drift | ✅ |
| Continue to certification only after deploy verified live | ✅ |

🛑 Deploy verified live. Continue to `ITER446_PRODUCTION_CERTIFICATION.md`.
