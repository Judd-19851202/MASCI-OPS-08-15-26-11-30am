# ITER453.6 · PRODUCTION DEPLOY REPORT

**Date**: 2026-06-02
**Production URL**: `https://mascidocs.com`
**Mode**: READ-ONLY public-surface verification.
**Authority**: OMEGA AUTHORIZATION · 2026-06-02.

---

## 1 · Deployment signature

| Field | Pre-deploy (post-deploy audit) | Post-deploy (this audit) |
|---|---|---|
| `source_hash` | `b82534d9caf103def5a514ef80c2c90c` | **`d01cdedc7d934d0aeebf026609cf6ec9`** |
| `app_env` | `production` | `production` ✅ |
| `db_name` | `masci_safety` | `masci_safety` ✅ |
| `started_at` | `2026-06-02T12:04:27Z` | **`2026-06-02T14:44:14Z`** |
| Uptime at audit | ≈ 2 h 43 m | **≈ 43 m** |
| `sentry.enabled` | true | true ✅ |
| Frontend bundle | `main.7af75c24.js` | **`main.037e8fa1.js`** |

**A redeploy did occur** — `started_at` advanced ≈ 2 h 40 m forward, `source_hash` changed, and the frontend bundle hash changed. The pod is fresh.

## 2 · `source_hash` ⇄ commit reconciliation

I cross-checked the deployed `source_hash` against every recent preview commit by running the same `_compute_source_hash()` logic from `backend/server.py:779-795` against `git show <commit>:backend/{server,training_pdf,pdf_render}.py` for each recent commit:

| Commit | When | Hash | Description |
|---|---|---|---|
| HEAD (preview, current — includes iter453.6) | now | `7a6c669f9e9212286e3850fae6a0b78e` | ITER453.6 startup gate present |
| `4f1e112` | same as HEAD | `7a6c669f9e9212286e3850fae6a0b78e` | ITER453.6 startup gate present |
| **`80927d0`** | 3 h ago | **`d01cdedc7d934d0aeebf026609cf6ec9`** | **end of ITER453.5 batch · BEFORE iter453.6** |
| `aa0cb04` | 5 h ago | `b82534d9caf103def5a514ef80c2c90c` | first production deploy |

# 🔴 **Production `source_hash = d01cdedc` = commit `80927d0`**

This is the state **at the end of the ITER453.5 batch** — i.e., **BEFORE** the HOTFIX BUNDLE A Part C iter453.6 startup readiness gate work landed in preview.

**Conclusion: The operator deployed the PRE-hotfix snapshot. iter453.6 startup readiness gate is NOT in production.**

## 3 · What IS in production (verified by anon probes)

| Surface | Endpoint | Expected | Observed | Verdict |
|---|---|---|---|---|
| Health | `GET /api/health` | 200 | 200 | ✅ |
| Version | `GET /api/version` | 200 + new hash | 200 + `d01cdedc` | ✅ |
| G-1 | `POST /api/employees/add` (anon) | 410 | 410 `endpoint_deprecated` | ✅ |
| G-1 burst | 8 sequential POSTs | uniform 410 | 8/8 = 410 | ✅ |
| G-2 | `POST /api/field-leadership/employees` (anon) | 401 | 401 `Field Leadership access required` | ✅ |
| G-3 | `POST /api/admin/employees` (anon) | 403 | 403 `HR or Admin token required` | ✅ Phase Alpha gate |
| G-3b/G-4 | `PUT /api/admin/employees/{id}` (anon) | 403 | 403 `HR or Admin token required` | ✅ Phase Alpha gate |
| HR Queue GET | `GET /api/hr/employee-requests` (anon) | 403 | 403 `HR or Admin token required` | ✅ |
| HR Queue POST | `POST /api/employee-requests` (anon, malformed) | 422 schema | 422 `kind required` | ✅ |
| ITER453 QA/QC | `GET /api/qaqc-inspections/{id}/lifecycle` (anon) | 401 | 401 `Safety, Admin, or PM login required` | ✅ |
| ITER453 SI | `GET /api/inspections/{id}/lifecycle` (anon) | 401 | 401 same | ✅ |
| Webhook empty | `POST /api/webhooks/resend -d '{}'` | 401 if secret set, else 200 ack | **200 ack** | 🟡 secret not set |
| Webhook bad sig | same with bad svix-signature | 401 if secret set, else 200 ack | **200 ack** | 🟡 secret not set |

## 4 · Frontend bundle pattern matching

`main.037e8fa1.js` (4 960 908 B). Grep results:

| Pattern | Hits | Verdict |
|---|---:|---|
| `"Save Status Change"` (ITER453.5 REC-1) | 1 | ✅ live |
| `"Update status"` (legacy) | 0 | ✅ replaced |
| `"Employee Lifecycle Guide"` (REC-3) | 1 | ✅ live |
| `"hremp-status-badge-"` (REC-2) | 1 | ✅ live |
| `"Request HR add"` (Phase Alpha) | 1 | ✅ live |
| `"QaqcLifecyclePanel"` / `"SiteInspectionLifecyclePanel"` | 0 | — names minified; endpoint live verification used instead |

## 5 · What is NOT in production

* 🔴 **iter453.6 startup readiness gate** — code not present (source_hash mismatch with HEAD).
* 🟡 **RESEND_WEBHOOK_SECRET** — env var not set (webhook accepts unsigned events).
* 🟡 **Audit-probe employee row** `f5de1e78-f893-46d5-aa09-6369064e7906` — soft-delete not performed yet.

## 6 · Pod / deploy hygiene observations

* No split-pod evidence — all anon probes returned consistent results across 8 sequential bursts.
* No stale-build evidence — `source_hash` is internally consistent with `started_at` (newer than pre-deploy).
* No deployment-loop evidence — pod has been stably up for 43 min at audit.
* No startup-exception evidence — public surface responds normally; `/api/health` 200 with healthy timestamps.

## 7 · Probe counts

* Anon public probes: **15**
* Frontend bundle pattern checks: **6**
* `source_hash`/commit reconciliations: **4**
* **Total verification points**: **25**
* Hard failures: **0**
* Discrepancies vs operator-intended deploy: **1** (commit `80927d0` deployed instead of `4f1e112`)
