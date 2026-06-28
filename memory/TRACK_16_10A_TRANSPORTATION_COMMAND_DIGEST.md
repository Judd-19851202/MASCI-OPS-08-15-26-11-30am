# TRACK 16.10A · Monday-morning Transportation Command Digest

**Status:** ✅ Production-ready · Deployment gate PASS · 42/42 new regression tests · 100% live verification

## STATUS
GO

## WHAT WAS BUILT
* `lib/transport_command_digest.py` — pure builder + sender. Reads `transport_action_items` + `email_routes`. Generates plain-text AND HTML bodies with the executive summary, blocking / urgent / due-soon / overdue lists, email route health classification, and direct links back to the Transportation Command Queue, Document Center, Inspection Center, Orientation Center, and Email Pilot Panel.
* 4 new admin endpoints inside `routes/transportation_automation.py`:
  - `GET  /api/admin/transportation/automation/digest/preview` — read-only digest payload
  - `POST /api/admin/transportation/automation/digest/dry-run` — audit-only run (always repeatable)
  - `POST /api/admin/transportation/automation/digest/send-now` — live send (week-keyed dedupe; `force=true` to override)
  - `GET  /api/admin/transportation/automation/digest/runs` — history
* `bootstrap_track_16_10` extended to seed `TRANSPORT_COMMAND_DIGEST_WEEKLY` with `enabled=False`, `internal_only=True`, `pilot_safe=True`, `track="16.10A"`.
* `transport_command_digest_scheduler_loop` — Monday 07:00–10:00 UTC weekly cadence under singleton lock. Respects `SCHEDULER_ENABLED`. Wakes every hour; the deterministic `transport_command_digest:YYYY-WW` dedupe key prevents duplicate sends.
* Frontend `DigestCard` inside the existing Automation Health sub-tab at `/admin/transportation/command-queue/health` — last-run KPIs, 6-cell summary stats, Dry-run / Send-now / Preview email buttons, inline HTML preview pane.
* 42-test regression file wired into `scripts/deployment_gate.py` — gate decision: **PASS**.

## DIGEST CONTENT
* **Subject:** `MASCI Transportation Command Digest — Week of YYYY-MM-DD`
* **Sections:** Executive Summary (open / blocking / urgent / action_required / due_this_week / overdue / routes_needs_configuration) · Blocking · Urgent / Action Required · Expiring Soon (next 7 days) · Overdue · Email Route Health (active / audit-only / needs_configuration) · Direct Links.
* **Tone:** professional, concise, operational, non-punitive — no "rejected / denied / failed".

## EMAIL ROUTING
* Single new route key `TRANSPORT_COMMAND_DIGEST_WEEKLY`. Defaults `enabled=False`, `internal_only=True`.
* Recipients resolved through Email Routing v2 — never hardcoded.
* Real SMTP fires via existing `lib/fsi_email_sender.fsi_send_email` (Resend) when (a) route is enabled, (b) recipients configured, (c) `RESEND_API_KEY` set in env. **No new sender.**
* Missing recipients → `needs_configuration` audit row, no crash.
* Carrier emails are explicitly excluded from this route (`internal_only=True`).

## SCHEDULER
* 1-hour wake cycle under `run_with_singleton_lock(db, "transport_command_digest", …)`.
* Fires only on `weekday()==0 (Monday)` and `07:00 ≤ hour < 10:00` (UTC).
* `SCHEDULER_ENABLED=false` (preview default) → loop sleeps and reports.
* Singleton lock prevents multi-worker double-fire in production.
* Weekly dedupe key prevents duplicate live sends even if the scheduler ticks twice in the same window.

## ADMIN UI
* DigestCard inside Automation Health view (Command Queue Center → "Automation Health" sub-tab).
* Renders week key, last-run status / dry-run flag / recipients count, summary KPI grid, three buttons (Dry-run · Send now · Preview email), and an inline HTML preview pane that uses the same renderer as the live email.
* Admin token required for every action.

## RBAC
* Every digest endpoint requires `X-Admin-Token`. Validated via the async directory admin validator. Dispatch tokens cannot fire the digest.

## AUDIT
* Every send (or `needs_configuration` / `errored`) writes a row in `email_routing_audit_v2` with `route_key`, `subject` (240-char cap), `dry_run`, `resend_message_id` when live.
* Every run writes a row to `transport_command_digest_runs` with `week_key`, `status`, `recipients_count`, `triggered_by`, `summary`, optional `error`.

## TESTS
* 42 tests pass (32 static + 5 pure builder + 5 live e2e).
* Static locks: weekly route seeded, route is internal-only, route defaults dry-run, builder reads action queue, summarises every required section, includes command-queue links, plain-text + HTML bodies, sender uses Email Routing v2, no SMS / Twilio / push, needs_configuration audit on empty recipients, weekly dedupe via ISO week, dry-run repeatable, scheduler respects env flag, every admin endpoint exists, UI status card present, no external carrier recipients, no punitive language, Track 16.10 tests preserved, deployment gate updated.
* Pure builder: empty DB → zero summary · severity bucketing · route-health classification · week-key dedupe blocks duplicate live · dry-run never short-circuited by dedupe.
* Live e2e against preview backend: preview / dry-run / send-now (`needs_configuration`) / history / unauth-gate.

## LIVE SMOKE
* Testing agent verified 100% backend + 100% frontend. Zero console errors. Zero design drift. DigestCard renders correctly, all 3 buttons fire successfully, HTML preview opens.

## DEPLOYMENT GATE
* Decision: **PASS**.

## DEFERRALS
* Per-recipient timezone localisation, per-section configurable thresholds, optional PDF attachment, audit-trail CSV export.

## RISKS / UNKNOWNS
* TRANSPORT_COMMAND_DIGEST_WEEKLY route ships with empty recipient lists. Operators must populate the `email_routes` row before live SMTP fires. Until then every send audits as `needs_configuration` (intentional, locked by spec).
* Production needs `SCHEDULER_ENABLED=true` AND `RESEND_API_KEY` set for the Monday cycle to actually send mail.
* Singleton-lock failover behaviour inherited from `lib/singleton_scheduler.run_with_singleton_lock` — battle-tested in prior tracks (Operator Digest, Track 16.10 automation engine).

## NEXT RECOMMENDED TRACK
**Track 16.11 — HR Lifecycle Integration.** Wire MASCI HR events into the eligibility engine so employee drivers transition automatically and (when ready) become a 6th live email pilot route.

## FINAL CALL
**GO.** Every Monday morning the Transportation team will now receive a single internal email summarising the current operating state. Email-only, internal-only, audited, deduped, scheduler-gated, deployment-locked. Done means done.
