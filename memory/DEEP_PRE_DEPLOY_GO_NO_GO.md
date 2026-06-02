# DEEP PRE-DEPLOY · GO / NO-GO

**Date**: 2026-06-02
**Build**: Employee Governance Phase Alpha · ITER453 (OC-003 + OC-004) · ITER452.5.2 Resend webhook.
**Reviewer**: E1 fork agent (read-only audit).
**Companions**: `DEEP_PRE_DEPLOY_CODE_REVIEW.md`, `DEEP_PRE_DEPLOY_CERTIFICATION.md`, `DEEP_PRE_DEPLOY_RISK_REPORT.md`.

---

## FINAL VERDICT

# 🟢 **GO TO DEPLOY**

Deploy is authorized **conditional on the production environment carrying the 4 mandatory env vars listed in §1 below.** The gate itself is binding — the deploy procedure must confirm all four before exposing the new endpoints to public traffic.

---

## §1 · Production env-var checklist (gate)

Operator must confirm each before clicking deploy:

| # | Variable | Required value | Why |
|---|---|---|---|
| 1 | `APP_ENV` | `production` (or unset) | Backend refuses to start with preview-vs-prod DB misalignment |
| 2 | `DB_NAME` | `masci_safety` | Same |
| 3 | `RATE_LIMITING` | **`on`** | Protects the new public `POST /api/employee-requests` from abuse |
| 4 | `RESEND_WEBHOOK_SECRET` | `whsec_…` from Resend dashboard | Without this, the webhook is unauthenticated → forged bounce events possible (MED-1 in Risk Report) |

Standing-policy vars already in `test_credentials.md` (`ADMIN_HMAC_SECRET`, `MFA_ENCRYPTION_KEY`, `AUTO_EMAIL_REPORTS=true`, `CORS_ORIGINS`, `SUPER_ADMIN_*`) remain unchanged.

---

## §2 · Summary metrics

| Metric | Value |
|---|---|
| Code files changed | **19** (10 backend + 9 frontend) |
| Config files changed | 1 (`.gitignore` additive) |
| Governance docs added/modified | 23 |
| Pytest pass / fail | **50 / 0** |
| Lint errors (changed files) | **0** |
| Blocker count | **0** |
| 🔴 HIGH-risk items | **0** |
| 🟡 MEDIUM-risk items | **2** (both addressed by checklist) |
| 🟢 LOW-risk items | **5** (all cosmetic / preview-only) |
| Live curl probes pass | **11 / 11** |
| `db.employees` rows | 249 (1 deleted, 8 via hr-queue-approval, 1 frozen legacy) |
| `db.employee_requests` rows | 29 (13 pending · 8 approved · 8 rejected) |
| New endpoints exposed | 12 (5 employee-requests · 3 qaqc-lifecycle · 3 site-inspection-lifecycle · 1 webhook) |

---

## §3 · Production deploy checklist (operational)

Run sequentially:

* [ ] **Pre-flight 1** — Confirm production env carries the 4 vars in §1.
* [ ] **Pre-flight 2** — Confirm `MFA_ENCRYPTION_KEY`, `ADMIN_HMAC_SECRET`, `AUTO_EMAIL_REPORTS=true`, `CORS_ORIGINS` match the doctrine in `test_credentials.md`.
* [ ] **Deploy** — promote the preview build to `mascidocs.com` via Emergent deploy flow.
* [ ] **Smoke 1** — `curl https://mascidocs.com/api/health` → 200.
* [ ] **Smoke 2** — `curl -X POST .../api/employees/add` (anon) → **410** `endpoint_deprecated`.
* [ ] **Smoke 3** — HR login at `/hr/login` (`hrmanager@mascigc.com`) → tile "Employee Requests" visible with pending badge.
* [ ] **Smoke 4** — Public POST `/api/employee-requests` with `kind=new_hire` → 200; HR Queue lists it.
* [ ] **Smoke 5** — HR approves → employee created with `added_via=hr-queue-approval`.
* [ ] **Smoke 6** — Open a QA/QC inspection → LifecyclePanel shows current state + legal next-states.
* [ ] **Smoke 7** — `curl -X POST .../api/webhooks/resend -d '{}'` → **401** `signature_headers_missing` (proves MED-1 secret is live).

Each smoke item is independently scoped; failure of any rolls back via Emergent platform rollback (zero-cost, instant).

---

## §4 · Rollback

* Code rollback: `git revert aa0cb04..ca3d11a` (or equivalent platform rollback). Restores the prior production code.
* Data rollback: **none required**. No schema migration shipped. New collections (`employee_requests`, `employee_lifecycle_events`, `resend_webhook_events`) are append-only and orphan cleanly.
* Blast radius: new endpoints become 404; HR Queue tile becomes empty; existing record CRUD is untouched. Acceptable.

---

## §5 · Out-of-scope (explicit)

The following are **NOT authorized** by this verdict and must wait for separate operator authorization:

* `iter454` BUILD · OC-005 JHP Acknowledgement Ledger.
* `iter455.1` · Phase 1B Accountability Chain Status.
* `usage_analytics.py` ClientDisconnect backport (MED-2 follow-up).
* Any janitorial sweep on the 1 legacy `field_leadership_inline` row (LOW-1).
* White Label, ForgedOps Operations Center, Customer #2 work.

---

## §6 · STOP

Audit complete. No code was modified. No data was modified. No deploy was performed.

Awaiting explicit operator authorization to proceed with production deployment.

— E1 · 2026-06-02 · READ-ONLY mode preserved throughout.
