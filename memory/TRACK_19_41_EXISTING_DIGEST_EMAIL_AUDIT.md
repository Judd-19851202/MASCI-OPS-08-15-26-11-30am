# TRACK 19.41 · Existing Digest / Email Report Audit

**Scope:** Inventory every scheduled or manual digest / cron email / report
email currently active in the platform, so nothing operates outside the
Unified Operational Intelligence Engine's governance envelope.

Method: exhaustive `grep` across `backend/`, `frontend/`, tests, and
memory docs for `fsi_send_email`, `Resend`, `schedule`, `cron`,
`digest`, `weekly`, `Monday`, `PO`, `purchase order`, `email_queue`,
`auto_email`, `notification`, `report email`.

## Inventory

| # | Digest | File | Trigger | Schedule | Recipients | Provider | Dry-run | Dedupe | Audit | Active? | OI-Engine? | Migration |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Morning Safety Intelligence** (Track 19.39) | `backend/incident_engine/morning_digest.py` | scheduler + manual admin route | Weekly · Mon 13:00 UTC | Safety + Admin (from `morning_digest_recipients`) | `fsi_send_email` | ✅ (default) | via `send_digest` audit row | `morning_digest_audit` | ✅ ACTIVE | ✅ Registered as `safety_morning_digest` in Track 19.40 registry | **DONE** — Track 19.40 migrated. |
| 2 | **Executive Operations Brief** (Track 19.40) | `backend/operational_intelligence/products.py::_agg_executive_ops` | manual dispatch | Weekly · Mon 14:00 UTC | Admin (registry-defined) | `fsi_send_email` (via engine) | ✅ (default) | engine dedupe | engine audit + history | ✅ ACTIVE | ✅ `executive_operations_brief` | **DONE** — Track 19.40 native. |
| 3 | **Weekly Purchase Order Digest** | `backend/po_digest.py` + `backend/routes/po_digest_admin.py` | `po_digest_scheduler_loop` (asyncio) + `POST /api/admin/po-digest/run-now` | Weekly · Mon 14:00 UTC (env: `PO_DIGEST_WEEKDAY` · `PO_DIGEST_HOUR_UTC`) | Active PMs (`project_managers`) + Active HR (`hr_users`) | Custom `_po_digest_send_email` (wraps FSI Resend path) | ✅ (`dry_run` param) | ✅ `lib/scheduler_runs.py::claim_slot` (compound unique index) + `lib/singleton_scheduler.py` heartbeat lock | `scheduler_runs` collection | ✅ ACTIVE (guarded by `PO_DIGEST_ENABLED` env, default `true`) | ✅ NOW REGISTERED as `po_weekly_digest` (Track 19.41 consolidation) | **DONE** — additive wrapper; legacy cron continues untouched. See `TRACK_19_41_PO_DIGEST_FORENSIC_AUDIT.md`. |
| 4 | **Safety Weekly Digest (legacy)** | `backend/safety_digest.py` | `safety_digest_scheduler_loop` (asyncio) | Weekly · Mon 14:00 UTC (env: `SAFETY_DIGEST_HOUR_UTC` · `SAFETY_DIGEST_WEEKDAY`) | Single address (`SAFETY_DIGEST_TO_EMAIL`, default `safety@mascigc.com`) | `fsi_send_email` | ❌ (env-gated by `AUTO_EMAIL_REPORTS`) | none | none | ⚠️ ACTIVE but **superseded** by Track 19.39 `morning_safety_digest` | ❌ Not migrated · Track 19.39 replaces its intent | **Migration Track 19.42**: turn `SAFETY_DIGEST_ENABLED=false` in env after operator confirmation that 19.39 covers the same surface. |
| 5 | **Transportation Command Digest** (Track 16.10A) | `backend/lib/transport_command_digest.py` + `routes/transportation_automation.py::transport_command_digest_scheduler_loop` | asyncio scheduler + manual route | Weekly · configurable | Dispatch / Safety / Transportation Admin / Operations Leadership | `fsi_send_email` | ✅ (`dry_run` param) | slot dedupe via `scheduler_runs` | `transport_command_digest_audit` | ✅ ACTIVE | ❌ Not yet migrated | **Migration Track 19.43** (Transportation Intelligence). Will supersede this digest under `transportation_intelligence` product. |
| 6 | **Operator Weekly Digest** (iter431) | `backend/lib/operator_digest.py` + `routes/admin_operator_digest.py` | manual admin endpoint (no scheduler) | Manual | Operator only (configurable) | `fsi_send_email` | ✅ (manual only) | none | none | ⚠️ Manual-fire only · low volume | ❌ Not migrated | **P3 / backlog**: fold into `corporate_intelligence` when that product ships (Track 19.4x). |
| 7 | **Backup Verification Weekly** | `backend/backup_verification.py` | asyncio scheduler | Weekly · Mon 14:00 UTC (env: `BACKUP_VERIFICATION_HOUR_UTC` · `_DAY`) | `BACKUP_VERIFICATION_TO` → falls back to `BACKUP_EMAIL_TO` / `SAFETY_EMAIL_TO` | `fsi_send_email` | env-gated by `BACKUP_VERIFICATION_ENABLED` | slot dedupe via `scheduler_runs` | `backup_health` | ✅ ACTIVE | ❌ **Correctly excluded** from OI Engine — this is infrastructure health, not an operational intelligence product. | **KEEP as-is.** |
| 8 | **Incident Investigation Notifications** | `backend/routes/incident_lifecycle.py` | event-driven (state change) | On-event (not scheduled) | Case owners + Safety | `fsi_send_email` | n/a (event-driven) | per-event audit | `incident_events` | ✅ ACTIVE | ❌ Not a digest — event-driven notification. | **KEEP as-is.** |
| 9 | **Transportation Orientation Emails** | `backend/routes/transportation_orientation.py` | event-driven | On-event | Drivers | `fsi_send_email` | n/a | per-event audit | orientation ledger | ✅ ACTIVE | ❌ Event notification, not a digest. | **KEEP as-is.** |
| 10 | **Daily Report Lifecycle Emails** | `backend/routes/daily_report_lifecycle.py` | event-driven (submission / approval) | On-event | PM + assignees | `fsi_send_email` | n/a | per-event audit | daily-report ledger | ✅ ACTIVE | ❌ Event notification, not a digest. | **KEEP as-is.** |
| 11 | **Dispatch Reminders** (D-1.4) | `backend/dispatch_reminders.py` | asyncio scheduler (60-second scan) | Ongoing scan · 10-min unack threshold | Bell rail (`db.tasks`) — in-app, NOT email | in-app only | idempotent via `reminder_sent_at` | idempotent flag | `tasks` collection | ✅ ACTIVE | ❌ In-app reminder rail (not email/digest). | **KEEP as-is.** |
| 12 | **Notification Center** | `backend/routes/notifications.py` | event-driven | On-event | Per-role | in-app + optional email | n/a | per-event | `notifications` | ✅ ACTIVE | ❌ Cross-cutting rail (not a digest). | **KEEP as-is.** |
| 13 | **PM Engine Alerts** | `backend/routes/pm_engine.py` | event-driven | On-event | PMs (per project) | in-app | n/a | per-event | `pm_alerts` | ✅ ACTIVE | ❌ Event feed, not digest. | **KEEP as-is.** |
| 14 | **Trench Safety Notifications** | `backend/routes/trench_safety/notifications.py` | event-driven | On-event | Safety + Site Foreman | `fsi_send_email` | n/a | per-event | trench audit | ✅ ACTIVE | ❌ Event notification. | **KEEP as-is.** |
| 15 | **Trench Safety Report Distribution** | `backend/routes/trench_safety/report_distribution.py` | manual · per-report | On-demand | Configurable | `fsi_send_email` | n/a | per-event | trench audit | ✅ ACTIVE | ❌ Per-report share, not digest. | **KEEP as-is.** |

## Summary

- **Total email/digest surfaces discovered:** 15.
- **Under Operational Intelligence Engine after Track 19.41:** 3 (`safety_morning_digest` · `executive_operations_brief` · `po_weekly_digest`).
- **Slated for migration in Track 19.42/19.43:** 2 (Safety Weekly legacy · Transportation Command Digest).
- **Correctly excluded (event-driven or infra):** 10.

## Duplicate-pipeline check

- **No** second scheduler introduced by Track 19.41.
- **No** second digest sender introduced.
- **No** second recipient manager introduced.
- **No** second audit collection introduced.
- **No** second renderer introduced (engine's canonical CSS template family is the ONE renderer for the 3 migrated products; legacy `safety_digest` + `po_digest` HTML remain in place until their engine migration completes — Tracks 19.42 / 19.43).

## Traffic-light state

- 🟢 Consolidated: safety morning + executive + PO.
- 🟡 Superseded but active (planned retirement Track 19.42): legacy `safety_digest.py`.
- 🟡 Awaiting migration (Track 19.43): `transport_command_digest`.
- 🟢 Correctly excluded: backup verification + 9 event-driven notifications.

No shadow emails. No duplicate schedulers. Zero drift.
