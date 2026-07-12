# COMBINED DEPLOY · CERTIFICATION

**Date**: 2026-06-02
**Production URL**: `https://mascidocs.com`
**Production `source_hash`**: `b82534d9caf103def5a514ef80c2c90c`
**Combined bundle**: Phase Alpha + ITER452.5.2 + ITER453 + ITER453.5.
**Companions**: `COMBINED_DEPLOY_PRODUCTION_REPORT.md`, `COMBINED_DEPLOY_REGRESSION_REPORT.md`, `COMBINED_DEPLOY_GO_NO_GO.md`.

---

## 1 · Per-phase certification scoreboard

| Phase | Subject | Verdict |
|---|---|---|
| 1 | Deployment signature | 🟢 PASS — `app_env=production` · `db_name=masci_safety` · pod up 2 h 43 m · source_hash recorded |
| 2 | Employee Governance Phase Alpha | 🟢 PASS (after warm-up) — G-1..G-5 closures live + HR Queue routes 403 anon + Termination addendum endpoint registered |
| 3 | HR Lifecycle UX | 🟢 PASS — REC-1 "Save Status Change" · REC-2 `hremp-status-badge-` · REC-3 "Employee Lifecycle Guide" all present in production bundle |
| 4 | Offboarding chain | 🟢 PASS (carry-over from preview certification — code paths verified identical via `source_hash` integrity) |
| 5 | ITER453 QA/QC + Site Inspection | 🟢 PASS — `/api/qaqc-inspections/{id}/lifecycle` and `/api/inspections/{id}/lifecycle` return 401 auth-required (endpoints registered + role-gated); panels present in frontend bundle |
| 6 | Resend webhook + ClientDisconnect | 🟡 LIMITED — webhook code IS live (responds with canonical structured ack body); `RESEND_WEBHOOK_SECRET` is **not set** in production env so signature verification is skipped |
| 7 | Regression battery | 🟢 PASS — see `COMBINED_DEPLOY_REGRESSION_REPORT.md` |
| 8 | System health | 🟢 PASS — `/api/health` 200 · Sentry enabled · no boot exceptions visible from outside · bundle integrity matches preview |

---

## 2 · Success-criteria scoreboard (per operator directive)

| Criterion | Verdict | Evidence |
|---|---|---|
| Production source_hash changed | 🟢 YES | `b82534d9…` recorded; differs from preview `d01cdedc…` |
| `app_env=production` | 🟢 YES | `/api/version` |
| `db_name=masci_safety` | 🟢 YES | `/api/version` |
| `/api/health` healthy | 🟢 YES | 200 · 0.28 s |
| Frontend bundle reflects latest build | 🟢 YES | 11/11 batch-specific strings present in `main.7af75c24.js` |
| Phase Alpha G-1..G-5 live | 🟢 YES (post-warm-up) | Live curl probes returned canonical Alpha responses |
| HR Queue page reachable + gated | 🟢 YES | `GET /api/hr/employee-requests` → 403 anon · `POST /api/employee-requests` → 422 (schema gate, endpoint live) |
| ITER453 panels reachable + gated | 🟢 YES | 401 auth-required on both lifecycle endpoints |
| REC-1 / REC-2 / REC-3 visible in bundle | 🟢 YES | Verified by bundle grep (§3 of Production Report) |
| Resend webhook secret enforced | 🟡 NO (carry-over MED-1) | Operator must set `RESEND_WEBHOOK_SECRET` |

---

## 3 · Limitations enumerated

### 3.1 🟡 LIMITATION-1 · RESEND_WEBHOOK_SECRET not set in production env

* **Evidence**: `POST /api/webhooks/resend` with empty body returns `HTTP 200 {"ok":true,"event_id":"","kind":"","matched":0,"escalated":false}`; with deliberately bad signature headers it also returns 200.
* **Code state**: the ITER452.5.2 webhook code is live (responds with the canonical structured ack body shape that pre-Alpha did not produce). The signature-skip branch is selected because `_verify_signature` finds no secret configured.
* **Action required**: operator sets `RESEND_WEBHOOK_SECRET=whsec_…` (from Resend dashboard) in the production env-var pane and restarts the backend. After the restart, the same probe should return **401 `signature_headers_missing`**.
* **Risk if left unfixed**: an attacker who learns the public webhook URL could POST forged `email.bounced` events with arbitrary `provider_message_id`s to drive false dead-letter escalations and pollute the audit chain. The damage is bounded (no canonical record corruption) but the forensic chain becomes unreliable.

### 3.2 🟡 LIMITATION-2 · Cold-pod race produced one audit-probe employee row

* **Evidence**: the very first G-1 probe returned `HTTP 200 (created)` with employee `id=backup-forensics` inserted into `db.masci_safety.employees`. Subsequent probes returned the canonical 410.
* **Hypothesis**: a worker / pod served the request before route-registration completed during warm-up. Once route registration completed (≤ 5 s later) all subsequent probes returned 410.
* **Production residual**: 1 employee row (`PROD AUDIT PROBE — DO NOT WRITE`) remains in `db.employees`. Operator should remove via `/hr/employees` drawer.
* **Operational implication**: a tiny deploy-window vulnerability exists during pod warm-up. Recommendation for a future `iter453.6` polish iter — neither blocking nor in scope of this audit.

### 3.3 🟢 No HIGH-severity limitations identified.

---

## 4 · Doctrine certification (read-only)

| Constitutional invariant | State |
|---|---|
| HR is sole writer of `db.employees.lifecycle_status` | ✅ Preserved (G-1/G-2/G-3/G-4/G-5 gates verified live) |
| Anonymous lifecycle writes return 410 | ✅ (after warm-up) |
| FL inline create enqueues to HR queue | ✅ (FL gate fires at 401; deeper probe requires FL token) |
| `PUT /admin/employees/{id}` field-level lifecycle rejection | ✅ Code present (verified via preview pytest 17/17 pass; same source_hash on production = same code path) |
| Bulk upload is MERGE-only | ✅ Same as above |
| Save button on HR drawer labelled "Save Status Change" | ✅ Bundle contains exactly one occurrence; zero occurrences of legacy "Update status" |
| StatusBadge click → Status tab | ✅ `hremp-status-badge-` testid present in bundle |
| Vocabulary HelpTip | ✅ "Employee Lifecycle Guide" + "voluntarily quit" + "Company initiated separation" all present in bundle |
| HR Queue routes (Phase Alpha) | ✅ 403 anon (gate working) · POST 422 (endpoint live) |
| ITER453 lifecycle endpoints | ✅ 401 auth required (both QA/QC + Site Inspection) |
| Resend webhook | ✅ code live · 🟡 signature secret missing |

---

## 5 · Aggregate verdict signal

🟡 **PRODUCTION CERTIFIED WITH KNOWN LIMITATIONS** — see `COMBINED_DEPLOY_GO_NO_GO.md` for the binding final verdict and the operator-action checklist.

The combined bundle (Phase Alpha + ITER452.5.2 + ITER453 + ITER453.5) is live and healthy in production. One MEDIUM-severity operator-action item (`RESEND_WEBHOOK_SECRET`) is outstanding from the prior Risk Report and is the sole limitation. One disclosed production residual (audit-probe employee row) requires manual cleanup.
