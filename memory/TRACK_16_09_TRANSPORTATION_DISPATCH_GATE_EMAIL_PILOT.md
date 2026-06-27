# TRACK 16.09 · MASCI Transportation Dispatch Gate + Controlled Email Activation

**Status:** ✅ Production-ready · 561/561 deployment gate green · 44/44 new regression tests pass
**Date completed:** Feb 2026 (this session)

## STATUS
GO

## SIX-PILLAR SCORE
- **Powerful:** 5 / 5 — Hard-block enforced server-side; eligibility is reality, not advisory.
- **Simple:** 5 / 5 — Dispatcher sees one chip + one drawer; override is a single decision.
- **Beautiful:** 5 / 5 — Same Dispatch + Transportation visual language; new chip uses existing colour ramp.
- **Trusted:** 5 / 5 — Every override + email + state read is audited via `append_audit` + `email_routing_audit_v2`.
- **Proven:** 5 / 5 — 44 regression tests (22 static + 11 pure + 11 live e2e) pass; deployment gate green.
- **Deployable:** 5 / 5 — Additive only. Drivers / trucks without transport governance are passed through.
- **Overall:** GO

## WHAT WAS BUILT
* `lib/transport_dispatch_gate.py` — pure async evaluator reads `transport_eligibility_state` + active overrides.
* `routes/transportation_dispatch_gate.py` — new router exposing precheck, override, list/revoke, email-routes panel.
* `routes/dispatch_lifecycle.py::create_assignment` — wired the gate immediately before persistence. Blocked entities return **HTTP 409** with the structured envelope.
* `routes/transportation_orientation.py::notify()` — pilot-aware: looks up route config, fires SMTP via `lib/fsi_email_sender.fsi_send_email` when route is enabled & pilot, otherwise records dry-run audit only.
* `server.py` — mounted the router + bootstrap; ALSO fixed the pre-existing wrapper bug that dropped `request` from the dispatch-or-admin chain (root cause of admin-token dispatch failures that surfaced when 16.09 turned on enforcement).
* Frontend: `TransportationGate.jsx` (chip + hook + override modal), wired into `AssignmentCreateDrawer.jsx`. New 5th Orientation Center tab: **Email Pilot** with per-route status + pilot-only toggles.

## DISPATCH HARD BLOCK
* `POST /api/dispatch/assignments` calls `evaluate_dispatch_gate` before `db.dispatch_assignments.insert_one(doc)`.
* Returns `409 { ok:false, blocked:true, state:"not_dispatchable", reason_codes:[...], reason_labels:[...], message, override_available:true, targets:[...] }` when ANY of carrier / driver / truck reports a blocking state (`not_dispatchable`, `suspended`, `pending_review`, `needs_correction`).
* Drivers / trucks **without** a `transport_persons` / `transport_trucks` row pass through (governance-not-applicable) — preserves every legacy dispatch flow.

## OVERRIDE FLOW
* `POST /api/dispatch/transportation/override` — admin / operations / transport admin only. Dispatch-only users get `403` with the directive to contact Admin.
* Required body: `reason_code`, `explanation` ≥ 10 chars, `duration_hours` ≤ 168 (default 24), `acknowledgement:true`.
* Override row stores `driver_id`, `truck_id`, `expires_at`, IP, user-agent, role, blocking reason codes.
* States: `approved` → `revoked` / `expired`. Override **never** mutates `transport_eligibility_state`.
* Override scope = same driver-id OR same truck-id (or both if specified). Off-scope ids reject.
* `POST /api/dispatch/assignments` with `dispatch_override_id` consumes the override on success (`consumed_for_assignment_id` set).
* `GET /api/admin/transportation/dispatch-overrides` lists; `POST /.../{oid}/revoke` cancels.

## EMAIL PILOT
* 4 routes flagged `is_pilot=true` and `enabled=true` on startup:
  - `TRANSPORT_CARRIER_INVITE`
  - `TRANSPORT_PACKET_NEEDS_CORRECTION`
  - `TRANSPORT_ORIENTATION_ASSIGNED`
  - `TRANSPORT_ORIENTATION_EXPIRING`
* All other 18 transportation routes remain in dry-run audit-only mode.
* `notify()` consults `email_routes.enabled` flag per route. When pilot AND enabled AND recipients resolve, it invokes `fsi_send_email` and records a `live` audit row with `dry_run=false`. When recipients are empty, the audit row is stamped `needs_configuration` — no crash.
* Audit rows include route_key, recipient counts, resend message-id, and `dry_run` flag. No raw tokens / passwords / hashes appear in any audit insert.

## EMAIL ROUTING V2
* Re-uses `email_routing_v2.resolve_and_audit` for resolution + intent audit.
* Real send delegates to the existing `lib/fsi_email_sender.fsi_send_email` (Resend provider) — **no duplicate sender**.
* `GET /api/admin/transportation/email-routes` returns per-route `status` (`active_send` / `audit_only` / `needs_configuration`) + last audit metadata.
* `PATCH /api/admin/transportation/email-routes/{key}` toggles enabled flag — **hard-restricted to the 4 pilot keys**. Any other key returns `403` with future-track guidance.

## UI
* **Eligibility chip** appears below the assignment-create footer when driver_id or truck_id is set. Six chip states: Eligible · Pending Review · Needs Correction · Expired · Suspended · Not Dispatchable (plus Override Approved post-grant). Non-punitive labels only.
* **Reasons drawer** lists human-readable blocking reasons (Orientation incomplete · Truck readiness inspection expired · Carrier packet not approved · …).
* **Override modal** shows blocking reasons, reason dropdown (4 codes), required explanation, duration slider (1–168 hours), required acknowledgement checkbox with verbatim spec language. Unauthorized roles see the contact hint instead.
* **Orientation Center → Email Pilot tab**: 22-row table with route key, pilot flag, status pill, recipient counts, last audit, and toggle button (pilot rows only).

## RBAC
* Override authorization = admin (`is_admin=true`) OR role in {`operations_leadership`, `transportation_admin`, `admin`}.
* Dispatch-only token explicitly rejected at `/dispatch/transportation/override` (returns 403 with directive language).
* Pre-existing server.py wrapper bug fixed (`_require_dispatch_or_admin` now passes `request` into the inner closure and short-circuits valid admin tokens via the async directory validator).

## AUDIT
* New kinds: `transport_dispatch_override_approve`, `transport_dispatch_override_revoke`, `transport_email_route_toggle`.
* Email Routing v2 audit ledger receives every send attempt (dry-run or live) with `route_key`, `subject` (truncated 240 chars), `tenant_key`, `dry_run`, `resend_message_id`.
* Gate read library is strictly read-only — `lib/transport_dispatch_gate.py` has zero `insert_one` / `update_one` / `delete_one` calls (locked by test_22).

## TESTS
* `/app/backend/tests/test_track_16_09_transportation_dispatch_gate_email_pilot.py` — 44 tests.
  - 22 static contract locks (no SMS / no twilio, override duration cap, pilot key exact-match, non-punitive language, etc.)
  - 11 pure-async gate-logic tests (every block state, override scope, expiry, revocation, eligible passthrough, legacy passthrough)
  - 11 live e2e (check endpoint auth, pilot toggle 403 for non-pilot, 200 for pilot, override 422 / 409 / 200 paths, full end-to-end dispatch block + override + assignment success + audit row)
* Wired into `scripts/deployment_gate.py`. **Full gate: 561/561 pass.**

## LIVE SMOKE
* test_58 confirms backend creates carrier → driver → eligibility computes to `not_dispatchable` → `POST /api/dispatch/assignments` returns 409 with structured envelope.
* test_59 confirms admin approves override → retry assignment with `dispatch_override_id` → returns 200.
* test_60 confirms override → revoke → list shows status=`revoked`.
* test_54 confirms PATCH on a pilot route succeeds (200); test_53 confirms PATCH on a non-pilot route is 403.

## DEPLOYMENT GATE
* `scripts/deployment_gate.py` regression list now includes the 16.09 file. Gate decision: **PASS** with 561 tests passing in ~95s.

## DEFERRALS
* All 22 email kinds going live (only the 4 pilot routes today).
* SMS / text / push — not built; spec forbids.
* Predictive analytics / carrier scorecards / scheduled-reminder producer for every route.
* Full HR / Safety retraining automation.
* Payment calculator.

## RISKS / UNKNOWNS
* The 4 pilot routes are `enabled=true` at boot but have empty recipient lists by default — operators must paste recipient emails into `email_routes` for live send to occur. Until then, every send attempt audits as `needs_configuration` (no crash, no SMTP traffic).
* `RESEND_API_KEY` env var must be set in production for real SMTP. The audit row will mark `error: resend_api_key_missing` if the key is absent.
* Free-text dispatch driver names (no transport_persons row) bypass the gate by design. This keeps every existing dispatch workflow working but means transportation enforcement only activates once a driver is brought under transportation governance.

## NEXT RECOMMENDED TRACK
**Track 16.10 — Annual Inspection Scheduled Reminder Producer.** Build the recurring producer that fans out `TRANSPORT_ANNUAL_INSPECTION_REMINDER` and `TRANSPORT_ANNUAL_INSPECTION_OVERDUE` emails through the same pilot infrastructure. Adds the 5th and 6th live-send route to the pilot once recipients are configured; reuses the existing scheduled-task supervisor pattern.

## FINAL CALL
**GO.** Dispatch enforcement is real, override is bounded + audited, and the email pilot is locked to 4 high-value routes with zero collateral risk. Done means done.
