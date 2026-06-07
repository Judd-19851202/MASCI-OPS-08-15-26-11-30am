# Resend Usage Audit
**Mode:** READ-ONLY.
**Date:** 2026-02-07

---

## 1 · Configuration
| Env var | Value (preview) | Purpose |
|---|---|---|
| `RESEND_API_KEY` | `re_CfHQ9DjX_PxdxXUJ73owaPVxha5U5A8kW` | Auth to Resend API |
| `RESEND_WEBHOOK_SECRET` | _(empty in preview)_ | HMAC validator for inbound webhook (production-only) |
| `SENDER_EMAIL` | `noreply@mascidocs.com` | `From:` address |
| `REPLY_TO_EMAIL` | `jaymn.judd@mascigc.com` | Reply-to header |
| `AUTO_EMAIL_REPORTS` | `false` | Master kill-switch — when false every wrapper falls back to stub logging |
| `BACKUP_EMAIL_TO` | `jaymn.judd@mascigc.com` | Backup verification + silent alarm + health alerts |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | Cross-portal escalation default |
| `ADMIN_DEAD_LETTER_EMAIL` | `safety@mascigc.com` | Tier 5 dead-letter recipient when Tier 1-4 resolution bounces |

The two-flag gate (`RESEND_API_KEY` + `AUTO_EMAIL_REPORTS`) is enforced inside every house-style wrapper, not at the call sites. Source modules can call `_safety_send_email(...)` without worrying about preview/production drift.

## 2 · Direct uses of Resend SDK

| File | Function | Notes |
|---|---|---|
| `lib/fsi_email_sender.py` | `fsi_send_email` | Shared sender used by FSI dispatcher (daily-report / incident lifecycle). Raises on Resend error so dispatcher can write `notification_dispatch_failed` audit row. |
| `server.py:9266` | `_safety_send_email` | Safety domain wrapper |
| `server.py:9190` | `_hr_send_email` | HR domain wrapper |
| `server.py:10147` | `_po_digest_send_email` | PO digest weekly cron wrapper |
| `server.py:8976` | `_job_photos_send_email` | Photo bundle (multipart, with attachments) |
| `server.py:10856` | `_directory_send_email` | Access directory invitations |
| `server.py:11237-11400` | `_dispatch_auto_email` | Per-record auto-email pipeline (renders PDF, sends via Resend, attaches the PDF) |
| `server.py:5812` area | Backup silent alarm | Direct `resend.Emails.send` for `[MASCI ALARM]` |
| `server.py:7879` area | Outage alerts | Direct `resend.Emails.send` for `🚨 PLATFORM OUTAGE` |
| `health_monitor.py` | health alerts | Direct `resend.Emails.send` for `[MASCI · HEALTH]` and `🚨 HEALTH FAIL` |
| `backup_verification.py` | weekly verification | Direct `resend.Emails.send` for `[MASCI · BACKUP]` |

All non-FSI senders share the same params shape:
```py
params = {
    "from": SENDER_EMAIL,            # or branded "MASCI X Operations <noreply@…>"
    "to": [recipient],
    "subject": subject,
    "html": html,                    # or "text": for plain
    "reply_to": REPLY_TO_EMAIL,      # optional, defaults to SENDER_EMAIL
    # "attachments": [...]           # only for job_photos and _dispatch_auto_email
}
```

## 3 · Inbound webhook
File: `routes/resend_webhook.py` (iter452.5.2 — Constitutional Build Package).

| Resend event | Audit row written | Side effect |
|---|---|---|
| `email.delivered` | `notification_delivery_delivered` | none |
| `email.bounced` (hard) | `notification_delivery_bounced` | Auto-escalate to Tier 5 (`ADMIN_DEAD_LETTER_EMAIL`) when sender resolved through Tier 1-4 |
| `email.complained` | `notification_delivery_complained` | Suppress future sends to that recipient |
| `email.deferred` | `notification_delivery_deferred` | none (transient) |

## 4 · Audit chain (deliverability evidence)
1. `notification_dispatch_attempted` — caller about to invoke wrapper.
2. `notification_dispatch_succeeded` — Resend accepted the send (returns `id`).
3. `notification_dispatch_failed` — Resend rejected (caller exception).
4. `notification_delivery_delivered` — Resend webhook confirmed inbox.
5. `notification_delivery_bounced` / `complained` / `deferred` — Resend webhook.

The chain is complete from caller intent through provider acknowledgement.

## 5 · Quota / Cost posture
- Preview environments: `AUTO_EMAIL_REPORTS=false` → zero quota usage. Logs only.
- Production: each domain wrapper logs to a distinct prefix (`[safety-email-stub]`, `[hr-email-stub]`, etc.) so a quota cliff can be attributed to a domain quickly.
- No retry-on-failure logic inside the wrappers (deliberate; webhook handles deferred retries and bounce escalation).

## 6 · Trench Safety inheritance
Trench Safety today has **zero** Resend calls. The infrastructure above is fully ready to absorb a `_trench_send_email` wrapper without any SDK plumbing — just follow the `_safety_send_email` shape and reuse the existing webhook + audit chain.
