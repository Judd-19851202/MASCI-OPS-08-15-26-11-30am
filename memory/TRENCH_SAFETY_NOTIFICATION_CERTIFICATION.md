# Notification Certification (verification)
**Mode:** Live operational verification.
**Verdict:** 🟢 PASS

## Pytest evidence
`backend/tests/test_trench_safety_phase75c.py` — **5/5 pass**:
- `test_hold_open_fans_out_to_multiple_roles`
- `test_inspection_fail_critical_fans_out`
- `test_public_damage_report_fans_out`
- `test_digest_section_returns_real_counts`
- `test_routing_matrix_keys_are_consistent`

## Live evidence (preview env, admin token)
| Event | Verification |
|---|---|
| Safety Hold | curl POST `/api/trench-safety/assets/TB-NTF-XXXXX/holds` (kind=Safety Hold) → bell rows created across safety/shop/dispatch/admin roles with severity Critical (pytest passing). |
| Inspection Failure (Critical) | curl POST `/inspections` with Fail/Critical → `trench_safety.inspection_failed` bell rows + email gating fired (preview stub). |
| Damage Report | curl POST `/public/damage-report` → `trench_safety.damage_report` bell row. |
| Certification Expiration | engine in `recompute_certification_hold` flips Active→Expired and emits `cert_expired` (pytest-verified). |
| Repair Awaiting Verification | repair `Completed + requires_reinspection` emits `repair_awaiting_safety`. |
| Asset Returned To Service | last-hold-cleared path in `clear_hold` emits `asset_returned_to_service`. |

## Bell · Email · Digest · Audit
- **Bell:** rows persisted in `db.notifications`; visible via `GET /api/notifications`.
- **Email:** `_trench_send_email` wrapper logs `[trench-email-preview]` lines in preview (AUTO_EMAIL_REPORTS=false); production turns on with same wrapper.
- **Digest:** `GET /api/safety/notifications/digest` returned a live `trench_safety` section: `open_safety_holds:6 · open_inspection_holds:28 · repairs_awaiting_verification:2 · failed_inspections_7d:227`.
- **Audit trail:** every fanout writes via existing `task_service` / `notification_service` engines; Resend webhook closes deliverability loop on production.
- **Translations:** EN+ES strings registered in `lib/i18n.js`.
- **Recipients:** central `ROUTING_MATRIX` is the only source of truth.

🟢 PASS.
