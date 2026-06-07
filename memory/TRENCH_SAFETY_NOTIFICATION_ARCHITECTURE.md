# Phase 7.5C · Notification Architecture
**Mode:** PRODUCTION BUILD (no new systems).
**Date:** 2026-02-07
**Verdict:** 🟢 GO

## Premise
The forensic audit confirmed Trench Safety only had derived dashboard alerts. Phase 7.5C wires Trench Safety into every existing MASCI notification engine — no parallel systems.

## Reuse map (existing infrastructure → trench safety events)

| Existing engine | Reused for trench-safety |
|---|---|
| `routes/tasks_notifications.py` (db.notifications) | Bell notifications |
| `lib/event_fanout.py` (`emit_notification`) | Fanout with idempotent audit |
| `_safety_send_email` pattern in `server.py` | New `_trench_send_email` (identical shape, branded `MASCI Trench Safety`) |
| `pdf_render.SUBJECT_TYPE_TAGS` | Added `"trench-safety": "TRENCH SAFETY"` → `[MASCI · TRENCH SAFETY]` subjects |
| `routes/notifications.py:_build_safety_digest` | Added trench safety section to `/api/safety/notifications/digest` |
| `safety_digest.py` weekly cron | Inherits the digest section via the shared aggregator |
| `routes/resend_webhook.py` | Bounce/complaint handling inherited automatically |
| `lib/i18n.js` | EN→ES translations for every new string |
| `audit_events` collection | Every fanout already writes an audit row through the shared engine |

## Single source of truth
File: `backend/routes/trench_safety/notifications.py`.

Exports:
- `ROUTING_MATRIX` — central event→(recipient roles · severity · email · digest) table.
- `notify_hold_opened(db, asset, hold)`
- `notify_hold_cleared(db, asset, hold)`
- `notify_inspection_failed(db, asset, inspection)`
- `notify_damage_report(db, asset, report)`
- `notify_certification_event(db, asset, cert, *, days)`
- `notify_repair_awaiting_safety(db, asset, repair)`
- `notify_asset_returned_to_service(db, asset)`
- `build_trench_digest_section(db)` — payload consumed by Safety digest aggregator.

Every emitter:
- Fire-and-forget. Never raises (caller's write always succeeds).
- Writes audit via `lib/event_fanout`.
- Uses ROUTING_MATRIX, so add/remove/change rules touch ONE table.

## Wiring locations (production code)
| Event source file | Hook |
|---|---|
| `routes/trench_safety/_helpers.py:open_hold` | calls `notify_hold_opened` |
| `routes/trench_safety/_helpers.py:clear_hold` | calls `notify_hold_cleared` (+ `notify_asset_returned_to_service` when last hold clears) |
| `routes/trench_safety/_helpers.py:recompute_certification_hold` | flips Active→Expired and calls `notify_certification_event(days=-1)` |
| `routes/trench_safety/inspections.py:submit_inspection` | calls `notify_inspection_failed` for Fail + Major/Critical |
| `routes/trench_safety/public.py:public_damage_report` | calls `notify_damage_report` (handles `Unsafe Condition` variant via routing key) |
| `routes/trench_safety/repairs.py:complete_repair` | calls `notify_repair_awaiting_safety` when `requires_reinspection=True` |

## Audit chain (per directive)
Every notification event writes:
- WHO: actor extracted from request (admin / safety / shop / public) into `linked_source_module`.
- WHAT: routing key (`trench_safety.<event>`) into the `type` field.
- WHEN: `created_at` set by the notification service.
- RECIPIENTS: one `notifications` row per recipient_role.
- DELIVERY METHOD: `delivery.internal` + `delivery.email` flags from ROUTING_MATRIX.
- OUTCOME: existing Resend webhook pipeline writes `notification_delivery_*` rows.

No parallel audit system created.

## Constraints honoured
- ❌ No new notification collection
- ❌ No new email wrapper SDK plumbing (`_trench_send_email` reuses Resend exactly like `_safety_send_email`)
- ❌ No new cron (digest section is read by existing `safety_digest.py` + `routes/notifications.py`)
- ❌ No new bell component (existing `NotificationBell.jsx` consumes the new rows automatically)
- ❌ No new severity ladder (reuses `Info/Warning/Critical`)
- ❌ No new translation engine (entries appended to existing `lib/i18n.js` ES dictionary)
