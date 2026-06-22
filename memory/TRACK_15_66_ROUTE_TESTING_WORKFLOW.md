# TRACK 15.66 — Route Testing Workflow (Phase 2)

**Date:** 2026-06-22

## 1. Dry-run mode (default · safe)

Operator clicks **"Dry-run test"** on any route row:
1. UI calls `POST /api/admin/email-routing/v2/routes/{KEY}/test` with `{"dry_run": true}`.
2. Backend reads the route doc from `email_routes`.
3. Backend writes one row to `email_routing_audit_v2` with:
   * `status = "dry_run"`
   * `dry_run = true`
   * `source = "db"`
   * `resolved_to_count`, `resolved_cc_count`, `resolved_bcc_count` derived from the route doc.
4. Backend updates `email_routes.last_tested_at` and `last_test_status = "dry_run"`.
5. **Resend API is NOT called.** No real email is sent.
6. UI toast: `"<ROUTE_KEY> dry-run · resolved N recipients · audit row written"`.

This is the path used by automated regression tests so they never hit a real inbox.

## 2. Controlled real test (admin-supervised)

Operator types a test inbox address (e.g., `qa-inbox@yourcompany.com`) then clicks **"Controlled send"**:
1. UI calls `POST .../test` with `{"dry_run": false, "test_recipient": "<addr>"}`.
2. Backend validates the address (`@` and basic format).
3. Backend builds an HTML email saying *"This is a controlled probe — production recipients were intentionally NOT contacted"*.
4. Backend sends via Resend to **the single test_recipient** — NEVER to the route's `to/cc/bcc` lists.
5. On success, the Resend message ID is recorded in the audit row with `status="sent"` and `dry_run=false`.
6. On failure, `status="failed"` + the Resend error is captured.
7. `email_routes.last_tested_at` and `last_test_status` are updated.

**The route's production recipient list is never used as the `to` for a test send.** This is the structural guarantee that prevents accidental production blasts.

## 3. UI affordances

* The "Controlled send" button is disabled until the operator has typed an address containing `@`.
* The address input has `type="email"` so the browser blocks obvious garbage.
* If the address is missing, the UI shows `"Enter a valid test inbox address"` instead of attempting the send.

## 4. Why this satisfies the safety rules

| Rule | How it's enforced |
|---|---|
| "Tests must not send to production route recipients" | Backend ignores `route.to/cc/bcc`; uses `test_recipient` only |
| "Critical route test must prove resolution and audit logging" | Both dry-run and controlled paths write an audit row with the resolved counts |
| "Failed tests must show the exact reason" | 502 from backend includes the Resend error string; UI toast displays it |
| "Audit row created" | Both paths write to `email_routing_audit_v2` |
| "Resend message ID recorded if a real send happens" | Controlled path captures `resend_message_id` in the audit row and in the UI response |

## 5. Operator workflow examples

**Scenario A — verifying a recipient change**
1. Edit `SAFETY_FORMS_TO` to add `new-supervisor@yourcompany.com`.
2. Save (cache flushes, resolver picks up edit immediately).
3. Click "Dry-run test" — toast confirms the resolved list now contains the new supervisor.
4. Click "Audit" — the dry-run row is at the top of the list with all three resolved counts.

**Scenario B — verifying Resend connectivity for a critical route**
1. On `HEALTH_ALERTS`, type `oncall-personal@yourcompany.com` in the controlled-send input.
2. Click "Controlled send".
3. Inbox receives a single email labeled `[ROUTE TEST · HEALTH_ALERTS] Controlled probe`.
4. Audit drawer shows the row with `status="sent"`, the Resend message ID, and `dry_run=false`.
5. Production recipients of `HEALTH_ALERTS` were NOT contacted.

## 6. Hard-rule compliance (Phase 2 testing workflow)
* ✅ Dry-run is the default.
* ✅ Real sends require an explicit test_recipient.
* ✅ Production distribution lists never blasted by tests.
* ✅ Every test writes an audit row.
* ✅ Failure messages surface the exact reason.
