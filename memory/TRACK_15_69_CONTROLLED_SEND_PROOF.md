# TRACK 15.69 · Controlled Test Send Proof

_Generated 2026-06-22_

## Status — DEFERRED · Operator Authorization Required

🛑 **No controlled test send was executed.**

## Why DEFERRED

The directive's hard rule is unambiguous:

> "Run exactly one controlled send. Rules:
>   * send only to **explicitly configured safe inbox**
>   * do not send to production distribution list
>   * do not trigger real safety/incident/backup alert"

The current session does not include:

1. An operator-designated safe inbox (an email address the operator
   explicitly authorizes to receive a probe send).
2. Explicit operator authorization to send any live email — the
   directive's own framework requires the phrases "Proceed with
   production cutover" / "Flip EMAIL_ROUTING_V2" / "Authorize Track
   15.69 cutover" / "Go live with V2 routing" before any
   recipient-touching action is permitted, and none of those phrases
   appeared in the session.

Per the directive: _"If safe controlled test cannot be performed:
Document why and return NO-GO or require operator authorization."_

This deliverable returns **REQUIRE OPERATOR AUTHORIZATION**.

## What WAS Verified Without Sending

- ✅ V2 resolver produces correct recipient lists for every route
  (parity 19/19 — see `TRACK_15_69_V2_DRY_RUN_PARITY.md`).
- ✅ V2 resolver writes a `dry_run` audit row for every resolved route
  (20 rows present in `email_routing_audit_v2`).
- ✅ Sender identity, reply-to, and recipient set match legacy
  expectations.
- ✅ Resend API key is present and valid in pod env.
- ✅ Critical-route empty-guard fires (4/4 critical routes have
  recipients).

## Operator-Driven Controlled Send Procedure (when authorized)

The operator should perform exactly one of the two safe variants:

### Variant A · Inbox-bounded probe (preferred)

1. Set up a dedicated probe route override that points only to a
   single operator-designated safe inbox (e.g., `ops-probe@mascigc.com`).
2. With `EMAIL_ROUTING_V2=true` enabled in production, hit the admin
   route-test endpoint:
   ```
   TOK=<admin_token>
   curl -X POST \
     https://mascidocs.com/api/admin/email-routing/v2/routes/SUPER_ADMIN_TO/test \
     -H "X-Admin-Token: $TOK" \
     -H "Content-Type: application/json" \
     -d '{"recipient_override": "ops-probe@mascigc.com", "subject_prefix": "[TRACK 15.69 PROBE]"}'
   ```
3. Capture Resend message ID from response.
4. Verify safe inbox received the probe.
5. Verify `email_routing_audit_v2` shows `status=sent`,
   `source=db`, `route_key=SUPER_ADMIN_TO`, `message_id=<resend_id>`.
6. Verify Admin UI route drawer shows the new audit row.

### Variant B · Dry-run only (no live email)

If even Variant A is not authorized, the operator may declare V2
sufficiently proven by the existing 20 `dry_run` audit rows already
present in `email_routing_audit_v2` — every route resolves correctly,
no live send needed.

## Audit Trail If Variant A Is Performed

| Field | Expected value |
|---|---|
| `tenant_key` | `masci` |
| `route_key` | the route under test (e.g., `SUPER_ADMIN_TO`) |
| `status` | `sent` |
| `source` | `db` |
| `to` | `["ops-probe@mascigc.com"]` (probe-only override) |
| `cc` | `[]` |
| `bcc` | `[]` |
| `subject` | `[TRACK 15.69 PROBE] …` |
| `provider_message_id` | Resend ID |
| `error` | null |
| `ts` | post-flip timestamp |

## Verdict

🟡 **DEFERRED** — Awaiting operator authorization + safe-inbox
designation. All preconditions are green; the controlled send is
gated only on explicit operator approval.
