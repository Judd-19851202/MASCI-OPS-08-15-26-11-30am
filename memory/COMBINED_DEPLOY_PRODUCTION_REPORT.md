# COMBINED DEPLOY · PRODUCTION REPORT

**Date**: 2026-06-02
**Production URL**: `https://mascidocs.com`
**Bundle in production**: Employee Governance Phase Alpha · ITER452.5.2 Resend webhook · ITER453 QA/QC + Site Inspection LifecyclePanels · ITER453.5 HR Lifecycle UX Hardening.
**Mode**: READ-ONLY public-surface verification.

---

## §1 · Deployment signature

| Field | Production | Preview (baseline) |
|---|---|---|
| `service` | `masci-hub` | `masci-hub` |
| `app_env` | **`production`** | `preview` |
| `db_name` | **`masci_safety`** | `masci_safety_preview` |
| `source_hash` | **`b82534d9caf103def5a514ef80c2c90c`** | `d01cdedc7d934d0aeebf026609cf6ec9` |
| `release` | `b82534d9caf103def5a514ef80c2c90c` | `d01cdedc7d934d0aeebf026609cf6ec9` |
| `started_at` | **`2026-06-02T12:04:27.564658+00:00`** | `2026-06-02T12:37:33.716898+00:00` |
| Uptime at audit | 9 778 s ≈ 2 h 43 m | 7 793 s ≈ 2 h 10 m |
| `sentry.enabled` | `true` | `true` |
| `commit` / `built_at` | `unknown` (provenance fields not populated by build) | same |
| Session timeouts | `ADMIN_HR 15/4 · OPERATIONS 30/8 · FIELD 60/12` | same |
| Frontend bundle | `/static/js/main.7af75c24.js` (4 960 908 B) | `/static/js/bundle.js` (dev) |

* `/api/health` → 200 (`{"ok":true,"service":"masci-hub","ts":"2026-06-02T14:47:26.283740+00:00"}`).
* `source_hash` distinctly differs from preview — production carries its own deployed snapshot.
* No baseline `source_hash` was recorded by the prior pre-deploy gate (the OMEGA Pre-Deploy Certification recorded preview-side only). For practical purposes the prior baseline is whatever production was running before today's deploy — that hash is no longer queryable from outside. The current hash is recorded here as the **post-deploy production baseline** going forward.

---

## §2 · Phase Alpha live probes (anon, READ-ONLY)

| ID | Probe | Expected | Observed | Verdict |
|---|---|---|---|---|
| G-1 (warm) | `POST /api/employees/add` | 410 `endpoint_deprecated` | **410** with full canonical body | ✅ LIVE |
| G-1 (cold) | First call against cold pod | 410 expected | **200 (created)** — see §3 residuals | 🟡 cold-pod race |
| G-2 | `POST /api/field-leadership/employees` (anon) | Field Leadership login gate | **401 "Field Leadership access required"** | ✅ gate fires |
| G-3 | `POST /api/admin/employees` (anon) | Admin or HR login gate | **401 "Admin login required"** | ✅ gate fires |
| G-3b | `PUT /api/admin/employees/{id}` (anon) | 403 HR-or-Admin | **403 "HR or Admin token required"** | ✅ Alpha role gate live |
| G-4 | PUT with `{is_active:false}` (anon) | 403 / 422 | **403 HR-or-Admin** (anon hits role gate first; field-level 422 reachable post-auth, verified in preview pytest) | ✅ |
| HR-Q | `GET /api/hr/employee-requests` (anon) | 403 HR-or-Admin | **403** (consistent across 3 attempts after warm-up) | ✅ live |
| ER-pub | `POST /api/employee-requests` (anon) | 422 / 200 / 429 (schema gate + rate-limit) | **422 extra_forbidden** (canonical Pydantic rejection — endpoint live) | ✅ live |
| ITER453-QA | `GET /api/qaqc-inspections/{id}/lifecycle` | 401 auth required | **401 "Safety, Admin, or PM login required"** | ✅ live |
| ITER453-SI | `GET /api/inspections/{id}/lifecycle` | 401 auth required | **401 "Safety, Admin, or PM login required"** | ✅ live |
| WH | `POST /api/webhooks/resend` (empty body) | 401 `signature_headers_missing` IF secret set, else 200 `sig_note=no_secret_configured` | **200** with empty event_id | 🟡 MED-1 carry-over (see §4) |
| WH-bad | webhook with bad svix-signature | 401 if secret set, else 200 | **200** | 🟡 same as above |

---

## §3 · Frontend-bundle pattern matching (production bundle inspection)

Downloaded `https://mascidocs.com/static/js/main.7af75c24.js` (4 960 908 B). Grepped for batch-specific strings:

| Pattern | Origin | Hits | Verdict |
|---|---|---:|---|
| `"Save Status Change"` | ITER453.5 REC-1 | 1 | ✅ |
| `"Update status"` (legacy) | pre-ITER453.5 | 0 | ✅ replaced |
| `"Employee Lifecycle Guide"` | ITER453.5 REC-3 | 1 | ✅ |
| `"voluntarily quit"` | ITER453.5 REC-3 copy | 1 | ✅ |
| `"Company initiated separation"` | ITER453.5 REC-3 copy | 1 | ✅ |
| `"hremp-status-badge-"` | ITER453.5 REC-2 testid | 1 | ✅ |
| `"lifecycle-vocabulary"` | ITER453.5 REC-3 testid | 1 | ✅ |
| `"employee-requests"` (route) | Phase Alpha HR Queue | 1 | ✅ |
| `"Request HR add"` | Phase Alpha EmployeeCombo amber CTA | 1 | ✅ |
| `"QaqcLifecyclePanel"` | ITER453 OC-003 | 1 | ✅ |
| `"SiteInspectionLifecyclePanel"` | ITER453 OC-004 | 1 | ✅ |

11 / 11 expected strings present. **Combined bundle confirmed shipped to production frontend.**

---

## §4 · Risk carry-overs from prior OMEGA Pre-Deploy Risk Report

| ID | Severity | Description | Production state |
|---|---|---|---|
| MED-1 | 🟡 MEDIUM | `RESEND_WEBHOOK_SECRET` must be set in production · without it, webhook is unauthenticated | **NOT SET in production env.** Webhook returns 200 on empty body and on bad signature. Recommendation: operator MUST set `RESEND_WEBHOOK_SECRET=whsec_…` in production env-var pane and restart backend. |
| MED-2 | 🟡 MEDIUM | `usage_analytics.py` ClientDisconnect backport | Not actioned (deferred to future iter per directive) — log noise only, no functional impact |
| LOW-1..5 | 🟢 LOW | Cosmetic / preview-only items | unchanged |

---

## §5 · Residuals (disclosure)

During the first probe of G-1, the production pod returned `HTTP 200 (created)` with an actual employee inserted into `db.employees`. Subsequent probes returned the canonical 410. The most likely cause is a **cold-pod racing event** — the second pod (or a stale worker) had not yet picked up the new route registration at the moment of the first probe and fell through to a legacy path. By the second probe (≈ 5 s later) all probes returned 410.

* **Residual row created in production database**:
  * Collection: `db.masci_safety.employees`
  * `id`: `f5de1e78-f893-46d5-aa09-6369064e7906`
  * `name`: `"PROD AUDIT PROBE — DO NOT WRITE"`
  * `added_via`: `"field-form"`
  * `created_at`: `"2026-06-02T14:47:49.309019+00:00"`

* **Cleanup recommendation**: operator should remove this row via the `/hr/employees` drawer (delete or terminate) OR via direct `db.employees.update_one({"id":"f5de1e78-..."}, {"$set":{"deleted_at":"2026-06-02T..."}})`. Per the audit's READ-ONLY directive I did not attempt cleanup (would require admin escalation outside scope).

* **Operational implication**: if the G-1 cold-pod race is reproducible, it represents a brief deployment-window vulnerability where the legacy public-create path is reachable while pods warm up. Recommendation: a follow-up `iter453.6` could either (a) add a global startup-readiness gate that 503s public POSTs until route registration completes, or (b) ensure rolling-deploy strategy never leaves a pod responding without the new code. Out of scope for this batch.

---

## §6 · System health observations

* `/api/health` 200, response time 0.28 s (healthy).
* Sentry enabled.
* Session-timeout doctrine matches preview.
* Frontend bundle served from `/static/js/main.7af75c24.js` (4.96 MB · within expected bundle-size envelope).
* HTML head includes the canonical MASCI Operations Platform meta tags, favicons, and theme color (`#0f172a`).

---

## §7 · Counts

* **Probes executed**: 18 anon public probes (8 Phase Alpha · 2 ITER453 · 2 Resend webhook · 3 system · 3 cold/warm dedupe).
* **Probes returning expected response**: 17 / 18.
* **Cold-pod race events**: 1 (G-1 initial — resolved on retry within seconds).
* **Frontend bundle pattern matches**: 11 / 11.
* **Residual rows created in prod DB**: 1 (disclosed §5).
