# OMEGA · Public-Gate Notification Architecture

**Date:** 2026-06-01
**Mode:** Design / architecture research. No code.

---

## 1 · Today's architecture (forensic baseline)

```
              ┌──────────────────────┐
              │ Field user (Safari   │
              │ on iPad · no portal  │
              │ session)             │
              └──────────┬───────────┘
                         │ public form
                         ▼
              ┌──────────────────────┐
              │ POST /api/<workflow> │
              │   (rate-limit only)  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Server inserts row   │
              │  · prepared_by (txt) │
              │  · project_number    │
              │  · NO email/phone/   │
              │     device           │
              └──────┬───────────────┘
                    │
        ┌───────────┴─────────────┐
        ▼                         ▼
┌──────────────────┐    ┌────────────────────────┐
│ emit_notification│    │ schedule_auto_email    │
│  delivery.       │    │  → PM + co-PMs +       │
│  internal=true   │    │    ALWAYS_CC           │
│  push=false      │    │  (one-shot on submit)  │
│  email=false     │    └─────────┬──────────────┘
│  sms=false       │              │
└───────┬──────────┘              ▼
        │                  ┌────────────────┐
        ▼                  │ PM inbox (SES) │
┌──────────────────┐       └────────────────┘
│ notifications.   │
│ Bell shows in    │
│ authenticated UI │
└──────┬───────────┘
       │
       ▼ portal user only
┌──────────────────┐
│ Admin/PM/Safety  │
│ sees bell        │
└──────────────────┘

FIELD USER never sees any reply from the platform.
The kickback / correction loop is invisible to them.
```

**Conclusion:** notifications today flow PM-ward via email, and Office-ward via the bell. There is no return channel to the field user.

---

## 2 · Target architecture (research / proposal)

Three additive channels, all feeding into the existing `delivery` envelope:

```
                  ┌─────────────────────────────┐
                  │   PUBLIC-GATE SUBMISSION    │
                  │                              │
                  │   binds at submit time:      │
                  │     · employee_id (dropdown) │
                  │     · contact (email/phone)  │
                  │     · device_id              │
                  │     · push_subscription      │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  field_submitter_bindings    │
                  │  (NEW collection)            │
                  │    submission_id, channels[] │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  notification dispatcher     │
                  │  reads delivery envelope    │
                  └─┬──────┬──────┬──────┬──────┘
                    │      │      │      │
                    ▼      ▼      ▼      ▼
                INTERNAL  PUSH  EMAIL   SMS
                 (bell)  (VAPID)(SES)(Twilio)
                    │      │      │      │
                    ▼      ▼      ▼      ▼
                  bell  iOS/PWA mail  text
                        Android        msg
                        Chrome
                        Edge
```

### Channel matrix

| Channel | Inbound prerequisite | Outbound prerequisite | Field reach |
|---|---|---|---|
| Internal bell | none | portal session | ❌ field user not logged in |
| Web Push | user grants `Notification.requestPermission()` on PWA-installed app | `VAPID_*` keys + service worker + `pywebpush` | ✅ if standalone install completed |
| Email | submission carries an email | `EMAIL_FROM` + SES/SendGrid | ✅ if mailbox checked |
| SMS | submission carries a US phone | Twilio acct + `FROM_NUMBER` | ✅ near-real-time |

### Binding contract

A new `field_submitter_bindings` collection stores per-submission delivery channels:

```jsonc
{
  "id": "<uuid>",
  "workflow": "daily_report" | "qaqc_inspection" | ...,
  "submission_id": "<workflow record id>",
  "submission_doc_id": "DR-2026-00123",
  "channels": [
    {"kind": "push", "endpoint": "...", "keys": {...}, "ua_hint": "iOS 17.4 PWA"},
    {"kind": "email", "address": "alec.perkins@masci.example"},
    {"kind": "sms", "phone": "+15555550100"}
  ],
  "device_id": "<localStorage uuid>",
  "employee_id": "<dropdown selection>",
  "consent_at": "2026-06-01T10:00:00Z",
  "consent_text_version": "v1",
  "expires_at": "+90d"
}
```

This collection is **separate from the workflow row** to keep PII isolated and TTL-managed independently.

---

## 3 · Dispatcher upgrade contract

The existing `emit_notification(db, payload)` would gain a `target_field_submitter: bool` flag. When true, the dispatcher:

1. Looks up `field_submitter_bindings.submission_id == payload.linked_source_record_id`.
2. Iterates `channels[]`.
3. For each channel kind, calls the appropriate driver (`push_driver.send`, `email_driver.send`, `sms_driver.send`).
4. Records per-channel delivery outcome in `notifications.delivery_log[]`:
   ```
   "delivery_log": [
     {"channel": "push", "attempted_at": "...", "outcome": "delivered", "endpoint_hash": "..."},
     {"channel": "email", "attempted_at": "...", "outcome": "bounced", "error": "..."}
   ]
   ```

The legacy `delivery = {internal, email, push, sms}` boolean envelope becomes derived: `true` if any successful entry of that kind exists in `delivery_log[]`.

---

## 4 · Privacy / retention contract

Per the iter452 risk register and the iter451 OSHA retention model:

| Item | Retention | Justification |
|---|---|---|
| `field_submitter_bindings` row | 90 days post-submission-close | Long enough to support reopen / revision; not long enough to be a long-term profile |
| `notifications.delivery_log` | Lifetime of the notification + 7 years | Audit-equivalent to `workflow_state_events` |
| Push subscription endpoint | Until revoked OR 90 days inactivity | Match browser-side subscription lifecycle |
| User-initiated unsubscribe | Cascade-delete all bindings + push subscriptions for that user_id within 24h | GDPR / CCPA compliance |
| Right-to-be-forgotten | All bindings purged; audit rows retain `actor_id_hash` only | Compliance-baseline |

---

## 5 · Failure-mode catalogue

| Failure | Impact | Mitigation |
|---|---|---|
| Push subscription expired (UA cleared) | Push delivery silent fail | Email / SMS fallback within 5min if no push ACK |
| User uninstalled PWA | Same | Same |
| User changed phone number | SMS bounces | Bounce → email tier |
| User changed email | Email bounces | Bounce → SMS tier · then PM phone-call escalation |
| Shared tablet — wrong recipient | Delivery succeeds, wrong human | Channel binding scoped to `employee_id` + `consent_at` — re-prompt on submit for new employee_id |
| Browser permission revoked silently by OS | Push silent fail | Server-side `pushManager.permissionState` heartbeat on next form load |
| Twilio outage | SMS unavailable | Email + PM escalation |
| SES outage | Email unavailable | SMS + push + PM escalation |
| All 3 channels fail | PM-only fallback | Notification logged with all 3 failures + flag |

---

## 6 · Integration touchpoints (research-only)

This architecture would touch / extend:

* **NEW** `backend/routes/push_subscriptions.py` — `POST /api/push/subscribe` (public-rate-limited), `DELETE /api/push/subscribe/<id>` (self-managed)
* **NEW** `backend/drivers/push_driver.py` — VAPID + pywebpush wrapper
* **NEW** `backend/drivers/sms_driver.py` — Twilio wrapper
* **NEW** `backend/drivers/email_driver.py` — SES wrapper (replaces / augments the existing `schedule_auto_email`)
* **NEW** `backend/lib/field_submitter_bindings.py` — Mongo helpers, retention sweeper
* **NEW** `backend/lib/signed_revision_links.py` — JWT-issuer for single-use revision URLs
* **NEW** `frontend/public/sw-push.js` — second service worker, scope `/`, push event listener
* **EXTEND** `frontend/src/lib/api.js` — `subscribePush()` helper
* **EXTEND** `frontend/src/pages/NewDailyReport.jsx`, `NewQaqcInspection.jsx`, etc. — pre-submit contact-capture + employee-dropdown + permission-request flow
* **EXTEND** existing `emit_notification` to use the new dispatcher
* **NEW** `notifications.delivery_log` migration
* **NEW** environment variables: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`, `TWILIO_*`, `SES_*`

**Estimated touched files: ~20 backend, ~15 frontend, ~6 NEW collections / indexes.**

This is a significant architectural addition. Operator must explicitly authorize.

---

## 7 · Architecture verdict

🟢 **Architecturally sound. Patterns proven. Schema forward-compatible (the `delivery.{internal,email,push,sms}` envelope already exists in `notifications` rows).**

The platform is structurally ready for this addition — the gap is implementation, not foundation. Operator must decide:

* **whether** to fund the engineering cost
* **when** to schedule it (pre-iter453 vs Phase 1A.5 vs Phase 2)
* **how** to phase the channel rollout (push-first vs email-first vs SMS-first)

No design proposal commits to a specific scheduling answer. Awaiting operator authorization.
