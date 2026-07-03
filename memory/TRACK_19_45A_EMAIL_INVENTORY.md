# TRACK 19.45A · Existing Email Inventory (Post-19.44 Re-Audit)

Complete re-audit of every email path in the platform.

| # | Path | File | Provider | Recipients | Schedule / Trigger | Under OI Engine? | Action |
|---|---|---|---|---|---|---|---|
| 1 | Morning Safety | `incident_engine/morning_digest.py` | `fsi_send_email` | Managed | Manual + Track 19.39 send | 🟢 Yes (`safety_morning_digest`) | Keep · operator cutover pending |
| 2 | Executive Ops | engine · `executive_operations_brief` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 3 | PO Weekly | `po_digest.py` + engine wrapper | `fsi_send_email` | PMs + HR from `project_managers` + `hr_users` | Mon 14:00 UTC | 🟢 Yes (wrapper) · legacy cron + engine wrapper coexist | Cutover gate `OI_ENGINE_PO_WEEKLY_LIVE` ready |
| 4 | Transportation | engine · `transportation_intelligence` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 5 | Fleet | engine · `fleet_intelligence` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 6 | HR | engine · `hr_intelligence` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 7 | Training | engine · `training_intelligence` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 8 | Project | engine · `project_intelligence` | `fsi_send_email` | Managed | Engine dispatch | 🟢 Yes | Keep |
| 9 | Legacy Safety Digest | `safety_digest.py` | `fsi_send_email` | env-address | Mon 14:00 UTC | ⚠️ Superseded | Cutover gate `OI_ENGINE_SAFETY_MORNING_LIVE` ready |
| 10 | Transportation Command Digest | `lib/transport_command_digest.py` | `fsi_send_email` | Multi | Weekly | ⚠️ Superseded by `transportation_intelligence` | Track 19.46+ cutover |
| 11 | Operator Weekly | `lib/operator_digest.py` | `fsi_send_email` | Configurable | Manual only | ❌ Excluded (manual admin fire) | Fold into `corporate_intelligence` when it ships |
| 12 | Backup Verification | `backup_verification.py` | `fsi_send_email` | env-address | Weekly | ❌ Correctly excluded (infra health) | Keep |
| 13 | Incident lifecycle notifications | `routes/incident_lifecycle.py` | `fsi_send_email` | Per-event | On-event | ❌ Event-driven, not digest | Keep |
| 14 | Transportation orientation | `routes/transportation_orientation.py` | `fsi_send_email` | Per-driver | On-event | ❌ Event-driven | Keep |
| 15 | Daily Report lifecycle | `routes/daily_report_lifecycle.py` | `fsi_send_email` | PMs | On-event | ❌ Event-driven | Keep |
| 16 | Trench safety notifications | `routes/trench_safety/notifications.py` | `fsi_send_email` | Safety + Foreman | On-event | ❌ Event-driven | Keep |
| 17 | Trench safety report distribution | `routes/trench_safety/report_distribution.py` | `fsi_send_email` | Configurable | On-demand | ❌ On-demand | Keep |
| 18 | Notification Center | `routes/notifications.py` | in-app + optional email | Per-role | On-event | ❌ Rail | Keep |
| 19 | PM Engine alerts | `routes/pm_engine.py` | in-app | PMs | On-event | ❌ Rail | Keep |
| 20 | Dispatch Reminders | `dispatch_reminders.py` | in-app only | Bell rail | 60s scan | ❌ Rail | Keep |

## Summary

- Total email/digest surfaces: 20.
- Under OI Engine: 8 (all IMPLEMENTED products).
- Awaiting cutover: 2 (`safety_digest.py` · `po_digest.py`) — both operator-gated.
- Superseded but active: 1 (`transport_command_digest`) — Track 19.46+ cutover.
- Correctly excluded: 9 (event-driven notifications · rails · infra health).

## No duplicate providers · no duplicate schedulers

Verified by grep-lock in `test_no_new_email_provider_or_scheduler_in_track_19_45a`.
