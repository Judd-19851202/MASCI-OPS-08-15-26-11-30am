# DEEP PRE-DEPLOY RISK REPORT

**Date**: 2026-06-02
**Audit mode**: READ-ONLY
**Companion docs**: `DEEP_PRE_DEPLOY_CODE_REVIEW.md`, `DEEP_PRE_DEPLOY_CERTIFICATION.md`, `DEEP_PRE_DEPLOY_GO_NO_GO.md`.

---

## Severity legend

| Tier | Meaning |
|---|---|
| 🔴 **HIGH** | Blocks deploy. Must be remediated before authorization. |
| 🟡 **MEDIUM** | Deploy may proceed if mitigation is on the production checklist. Not a blocker. |
| 🟢 **LOW** | Cosmetic / preview-only / non-actionable. Tracked for visibility. |

---

## 🔴 HIGH — count: 0

*No high-severity items.*

---

## 🟡 MEDIUM — count: 2

### MED-1 · `RESEND_WEBHOOK_SECRET` is not yet set in production

* **Surface**: `POST /api/webhooks/resend` (new endpoint).
* **Current behaviour in preview**: `_verify_signature()` returns `(True, "no_secret_configured")` when the env var is absent — signature checking is skipped. This is intentional for preview/dev, but **catastrophic if shipped to production unchanged**: an attacker could POST forged `email.bounced` events with arbitrary `provider_message_id`s to drive false dead-letter escalations and pollute the audit chain.
* **Mitigation (PRE-DEPLOY)**:
  1. In Resend dashboard, generate a webhook signing secret (`whsec_…`).
  2. Set `RESEND_WEBHOOK_SECRET=<value>` in the production `/app/backend/.env` (or platform env-var pane).
  3. Restart backend.
  4. Verify `curl -X POST .../api/webhooks/resend -d '{}'` returns **401** `signature_headers_missing` (proves the gate is live).
* **Owner**: Operator (env-var setting) + E1 (verification on first prod call).
* **Status**: Tracked in §8.1 of the Code Review as a P0 production env-var requirement. Treated as MEDIUM (not HIGH) because the checklist itself is binding policy and the verification step is part of the post-deploy smoke run.

### MED-2 · `usage_analytics` middleware emits `RuntimeError("No response returned.")` on aborted requests

* **Surface**: `backend/routes/usage_analytics.py:201` — the analytics-tracking middleware does not catch `ClientDisconnect`, so when an upstream client aborts mid-response Starlette raises a generic `RuntimeError`.
* **Why this is in scope**: The ITER452.5.2 work shipped the explicit `ClientDisconnect` catch in `resend_webhook.py` precisely to silence this class of noise. The same pattern is NOT YET applied to `usage_analytics.py`.
* **Impact**: Log noise + Sentry false-positives. **No functional impact.** The middleware does not corrupt state; the request simply fails fast.
* **Mitigation**: Backport the `try: await call_next; except ClientDisconnect: return early` pattern to `usage_analytics.py` in a follow-up iteration (NOT this deploy — out of scope).
* **Owner**: Future iter (e.g., `iter454.x` polish).
* **Status**: Operational annoyance only. Does not block deploy.

---

## 🟢 LOW — count: 5

### LOW-1 · 1 legacy `field_leadership_inline` row in `db.employees`

* Created **before** the G-2 closure (now this code path enqueues into `employee_requests` instead). Frozen, no downstream effect.
* No action required. Optional janitorial sweep can backfill `added_via="legacy_field_inline_pre_alpha"` for auditability.

### LOW-2 · Preview backend logs "scheduled-backup scheduler task is DEAD" every 5 minutes

* Expected when `SCHEDULER_ENABLED=false` (preview default per `lib/singleton_scheduler.py`). The respawn-then-disable cadence is by design.
* **In production**: `SCHEDULER_ENABLED=true` flips this; the message disappears.

### LOW-3 · Frontend dev server emitted a historical `ENOSPC` write error

* Found in `/var/log/supervisor/frontend.err.log` from an older pod session. Current disk = **46 %** used. Frontend has been up for 52 min without recurrence. Service is currently healthy.

### LOW-4 · Tailwind ambiguous-class warning `duration-[400ms]`

* Compiler warning only. No visual impact. Already documented as preview-stable noise.

### LOW-5 · iter368 reported "termination 422 extra_forbidden" as a backend bug

* **Not a bug.** The termination schema correctly requires `target_employee_id` (canonical) — the previous testing agent sent `target_employee_name`, which is correctly rejected by `ConfigDict(extra="forbid")`. The current pytest `test_queue_termination_submit_then_reject` passes using the canonical field. Closed.

---

## Risk-totals summary

| Tier | Count |
|---|---:|
| 🔴 HIGH | **0** |
| 🟡 MEDIUM | **2** |
| 🟢 LOW | **5** |
| **TOTAL** | **7** |

**Of the 7 tracked items, ZERO are deploy blockers.** Both MEDIUM items are addressed by the production env-var checklist + a deferred non-urgent backport. The 5 LOW items are cosmetic or preview-environment-bound.

---

## Recommended action ordering

1. **(BEFORE DEPLOY)** Set `RESEND_WEBHOOK_SECRET` in production env. Verify with the smoke probe in §8.4 of the Code Review.
2. **(DEPLOY)** Authorize production deploy of this build.
3. **(POST-DEPLOY ≤ 5 min)** Run the §8.4 smoke checklist.
4. **(FUTURE iter454.x)** Backport `ClientDisconnect` catch into `usage_analytics.py`.
5. **(OPTIONAL)** Backfill `added_via` on the 1 legacy `field_leadership_inline` row for auditability.
