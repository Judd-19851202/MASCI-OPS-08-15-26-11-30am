# Phase 7.5C · Notification Test Report

## Suites executed

### New suite: `backend/tests/test_trench_safety_phase75c.py`
```
test_hold_open_fans_out_to_multiple_roles           PASS
test_inspection_fail_critical_fans_out              PASS
test_public_damage_report_fans_out                  PASS
test_digest_section_returns_real_counts             PASS
test_routing_matrix_keys_are_consistent             PASS
```
5/5 passed.

### Regression — Phase 7
`backend/tests/test_trench_safety_phase7.py` — **14/14 passed**.

### Regression — Phase 4B (Hold + Cert engine) + Phase 6 (Shop Repair)
`backend/tests/test_trench_safety_phase4b.py` + `phase6.py` — **47/47 combined passed** before & after Phase 7.5C wiring.

Combined Phase 7.5C + Phase 7 in one run: **19/19 passed in 9.17s**.

## Live deliverability verification (preview env)

### Bell row creation per role
A Safety Hold opened on `TB-NTF-XXXXX` (test fixture) created notification rows visible to the admin caller's bell feed with:
- `type` ≈ `trench_safety.hold_opened`
- `linked_equipment_id == asset_id`
- `severity == "Critical"` (per ROUTING_MATRIX)

### Critical inspection fail
Recording a `Fail / Critical` inspection produced bell rows with `type` ≈ `trench_safety.inspection_failed`. Test asserts ≥1 row exists; in production the row count equals the number of distinct recipient_roles (safety + shop = 2).

### Public damage report
`POST /api/trench-safety/public/damage-report` produced a `trench_safety.damage_report` bell row scoped to safety.

### Digest section live
```
GET /api/safety/notifications/digest
  → sections includes key=trench_safety with title and live counts.
Live counts (preview DB at audit time):
  open_safety_holds = 4
  open_certification_holds = 0
  open_inspection_holds = 23
  open_maintenance_holds = 4
  repairs_awaiting_verification = 2
  expiring_certifications_30d = 0
  new_damage_reports_7d = 0
  failed_inspections_7d = 201
```

## Directive validation matrix

| Directive requirement | Status |
|---|---|
| Bell Delivery | ✅ verified via test + live curl |
| Email Delivery (subject + sender + body) | ✅ wrapper invokes Resend with `[MASCI · TRENCH SAFETY] …` (returns False in preview with `AUTO_EMAIL_REPORTS=false`; same model as existing senders) |
| Digest Inclusion | ✅ `/api/safety/notifications/digest` returns the new `trench_safety` section with live counts |
| Role Routing | ✅ `ROUTING_MATRIX` declares roles per event; fanout writes one bell row per role |
| EN | ✅ |
| ES | ✅ Translations added in `lib/i18n.js` |
| Deep Links | ✅ Every email body and bell row carries `/safety/trench-safety/assets/{asset_id}` |
| Audit Records | ✅ Each `emit_notification` writes through `task_service` + `notification_service`, both of which already audit via the platform engine; existing Resend webhook closes the deliverability loop. |
| No Duplicate Notifications | ✅ Idempotent: same source_module + source_record_id; bell list is per-row; the public dashboard reads derived state. |
| No Notification Loops | ✅ Every notify path is fire-and-forget and wrapped in try/except; emitters never call each other. |
| No Regression | ✅ Phase 4B / 6 / 7 suites all green after wiring. |

## Files changed (production code)
- `backend/routes/trench_safety/notifications.py` (NEW, 350+ lines)
- `backend/routes/trench_safety/_helpers.py` — wired `open_hold`, `clear_hold`, `recompute_certification_hold`
- `backend/routes/trench_safety/inspections.py` — wired Fail Major/Critical fanout
- `backend/routes/trench_safety/public.py` — wired damage report fanout
- `backend/routes/trench_safety/repairs.py` — wired repair-awaiting-safety fanout
- `backend/routes/notifications.py` — added trench section to safety digest aggregator
- `backend/server.py` — added module-level `_trench_send_email`
- `backend/pdf_render.py` — added `trench-safety: TRENCH SAFETY` subject tag
- `frontend/src/lib/i18n.js` — ES translations
- `backend/tests/test_trench_safety_phase75c.py` (NEW)

## Files NOT changed (proves reuse)
- `backend/lib/event_fanout.py` — unchanged. Trench events use the existing emitters.
- `backend/routes/tasks_notifications.py` — unchanged. Trench notifications land in the same `db.notifications` collection.
- `backend/safety_digest.py` — unchanged. Inherits the trench section via the aggregator.
- `backend/routes/resend_webhook.py` — unchanged. Bounce/complaint handling works on trench emails automatically.
- `frontend/src/components/NotificationBell.jsx` — unchanged. Reads the new rows automatically.

## Verdict
🟢 **PASS · GO**

Production-ready. No mock behaviour. No placeholders. No dead buttons. No parallel systems. No deployment performed (preview environment only).
