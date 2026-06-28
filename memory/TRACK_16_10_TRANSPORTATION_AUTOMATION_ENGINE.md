# TRACK 16.10 · MASCI Transportation Automation Engine

**Status:** ✅ Production-ready · Deployment gate PASS · 50/50 regression tests · Frontend 100% live-verified

## STATUS
GO

## SIX-PILLAR SCORE
- **Powerful:** 5 / 5 — daily scan across trucks · drivers · carriers · packets · overrides; proactive eligibility re-derivation.
- **Simple:** 5 / 5 — one runner, one action queue, one command center.
- **Beautiful:** 5 / 5 — native sub-tab inside Transportation app; same colour ramp + chips as Tracks 16.04–16.09.
- **Trusted:** 5 / 5 — every action, email, eligibility change, and skipped send writes an audit row; dedupe via deterministic event_key.
- **Proven:** 5 / 5 — 50 tests including 10 live e2e against preview backend; deployment gate green.
- **Deployable:** 5 / 5 — additive; scheduler gated by `SCHEDULER_ENABLED`; singleton lock; pilot routes default to dry-run.
- **Overall:** GO

## WHAT WAS BUILT
* `lib/transport_automation.py` — async runner + 6 scanners + reminder windows + deterministic dedupe + eligibility recompute + email send adapter.
* `routes/transportation_automation.py` — 8 admin endpoints + 1 dispatch read-only visibility endpoint + bootstrap (9 new dry-run routes) + scheduler loop.
* Frontend `_command_queue.jsx` — Morning Queue · Automation Health · 30-day Forecast sub-tabs. Sub-nav entry added to Transportation app.
* `tests/test_track_16_10_transportation_automation_engine.py` — 50 regression tests wired into the deployment gate.

## AUTOMATION RUNNER
* `run_transportation_automation(db, *, now=None, dry_run=False, triggered_by=...)`
* Returns: `{ok, started_at, completed_at, dry_run, counts:{items_scanned, actions_created, emails_attempted, emails_sent, emails_needs_configuration, eligibility_updates, errors}, actions:[…], errors:[…]}`.
* Idempotent — second live run within seconds returns `actions_created=0` due to deterministic event_key dedupe.
* Per-scanner + per-item errors caught and counted; runner never crashes on one bad record.
* Dry-run **does not** persist event rows (locked by `test_34`); a dry-run can be replayed indefinitely.

## REMINDER WINDOWS
* `30_days` (info) → `14_days` (advisory) → `7_days` (advisory) → `1_day` (action_required) → `due_today` (action_required) → `overdue` (urgent, re-emitted every 7 days via `overdue_bucket`).
* Sub-second pure computation; locked by tests 06-12.

## ACTION QUEUE
* Collection `transport_action_items` with fields per spec (source · action_type · severity · entity · title · description · due_date · status · assigned_role · related_route_key · related_event_key · audit fields).
* Severity buckets: `blocking | urgent | action_required | advisory | info`.
* One open row per `related_event_key` (no duplicates).
* PATCH endpoint transitions `open → in_progress / resolved / dismissed` with audit row.

## EMAIL ROUTING
* Re-uses `email_routing_v2.resolve_and_audit` for resolution + audit.
* Real send via existing `lib/fsi_email_sender.fsi_send_email` (Resend). NO duplicate sender.
* 9 NEW route keys seeded by `bootstrap_track_16_10` — **every one defaults to `enabled=false` (dry-run)**:
  - `TRANSPORT_ANNUAL_INSPECTION_REMINDER`
  - `TRANSPORT_ANNUAL_INSPECTION_OVERDUE`
  - `TRANSPORT_DOC_EXPIRING`
  - `TRANSPORT_DOC_OVERDUE`
  - `TRANSPORT_ORIENTATION_OVERDUE`
  - `TRANSPORT_PACKET_PENDING_REVIEW`
  - `TRANSPORT_ELIGIBILITY_CHANGED`
  - `TRANSPORT_OVERRIDE_APPROVED`
  - `TRANSPORT_OVERRIDE_EXPIRING`
* Track 16.09 pilot routes remain live (4 routes). Activation of any new route requires explicit admin toggle through the Track 16.09 Email Pilot panel.
* Missing recipients → `needs_configuration` audit row, no crash.

## ELIGIBILITY AUTOMATION
* `_maybe_recompute_eligibility` derives via existing `compute_transport_eligibility` (read source facts only) and upserts the canonical `transport_eligibility_state` row when the state changes.
* Source records (`transport_persons`, `transport_trucks`, `carriers`) are NEVER mutated by the automation engine.
* State changes emit a tracked event + bump the `eligibility_updates` count + audit row.

## COMMAND CENTER UI
* `/admin/transportation/command-queue` — Three sub-tabs:
  1. **Morning Queue** — severity-bucketed action items with Resolved / Dismiss buttons.
  2. **Automation Health** — last run KPIs · route live/dry-run lists · Manual run + Dry-run buttons with JSON result preview · stale-run advisory after 72 h.
  3. **30-day Forecast** — 6 sections (inspections / orientations / driver docs / carrier docs / packets / overrides) populated from the same scanners without writing anything.

## DISPATCH VISIBILITY
* `GET /api/dispatch/transportation/visibility` — read-only at-risk view.
* Returns `expiring_this_week`, `blocked_today`, `at_risk`, `note`. Accepts admin OR dispatch token. No write endpoints surfaced to dispatch.

## SCHEDULER
* 24-hour cadence; respects `SCHEDULER_ENABLED` env var (defaults `true` in production; preview ships `false`).
* Wired under the existing `run_with_singleton_lock(db, "transport_automation", ...)` so multi-worker prod never double-fires.
* Loop exceptions are logged but do not abort.
* If `SCHEDULER_ENABLED=false`, the loop sleeps 1 hour and re-checks (allows hot-flip without restart).

## RBAC
* All `/api/admin/transportation/automation/*` endpoints require `X-Admin-Token` (validated via async directory admin validator).
* Dispatch visibility accepts admin OR dispatch token. Read-only by design.
* Inline `_dispatch_or_admin` resolver mirrors the Track 16.09 fix.

## AUDIT
* New kind: `transport_action_item_update` for PATCH lifecycle.
* Every email send (or `needs_configuration` / `errored`) writes to `email_routing_audit_v2`.
* Every run writes to `transport_automation_runs` with the full counts envelope.
* Every event written to `transport_automation_events` carries `dry_run`, `route_key`, `reminder_window`, `due_date`, deterministic `event_key`.

## TESTS
* 50 tests pass (35 static · 5 pure runner · 10 live e2e).
* Live e2e covers: dry-run summary, live run, idempotent rerun, run history, action queue with buckets, forecast, health (routes live/dry-run + scheduler flag), action PATCH → resolved, dispatch visibility, admin auth gate.
* Wired into `scripts/deployment_gate.py`.

## LIVE SMOKE
* Backend: testing-agent ran all 10 live e2e against preview URL — **all pass**.
* Frontend: testing-agent verified `/admin/transportation/command-queue` mounts; sub-tabs render; Run buttons fire and update the Health view; severity buckets render; dispatch visibility endpoint responds.
* Zero console errors. Zero design drift.

## DEPLOYMENT GATE
* Decision: **PASS**.
* Full transportation regression now spans Tracks 16.04 → 16.10. Every prior track's tests are still wired and still green.

## DEFERRALS
* Predictive analytics, carrier scorecards, payment calculator, full HR lifecycle automation, AI recommendations, advanced dispatch optimisation, SMS / text / push.

## RISKS / UNKNOWNS
* All 9 new routes default to dry-run with empty recipient lists. Operators populate recipients and toggle enabled via the Track 16.09 Email Pilot panel.
* `SCHEDULER_ENABLED=false` is normal in preview; the daily cycle does not fire until production flips it on.
* `RESEND_API_KEY` must be set in production for real SMTP; absent → `errored` audit row.
* Free-text legacy dispatch (no `transport_persons` row) is invisible to the runner by design — automation activates per-driver only when a transportation-governed record exists.

## NEXT RECOMMENDED TRACK
**Track 16.11 — HR Lifecycle Integration.** Wire MASCI HR events (hire / leave / termination / role-change) into the eligibility engine so MASCI employee drivers move through `pending_review → active → suspended` automatically. Re-uses the existing `transport_automation_events` ledger + the 4-route email pilot once recipients are configured.

## FINAL CALL
**GO.** Transportation is no longer a passive database — it is a proactive operating system. Reminders fire on schedule, action items materialise the moment an item is due, eligibility re-derives without human intervention, and the entire loop is audited. Done means done.
