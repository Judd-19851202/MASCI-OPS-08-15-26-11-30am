# S1-4 Notification Delivery Certification Evidence

Date: 2026-07-27
Environment: Preview only (`APP_ENV=preview`)
Status: **IMPLEMENTED / VERIFIED / BLOCKED ON INVALID RESEND KEY**

## Scope

Certify the bounded notification chain for one controlled Preview-only live provider attempt:

- workflow event
- routing
- queued
- provider submission
- provider reconciliation
- audit
- operator status

Strict Preview constraints preserved:

- `SAFE_CAPTURE` remains globally enabled
- no global disable of `EMAIL_SAFETY_MODE=strict`
- no CC / BCC / distribution-group expansion on the live certification lane
- only the authorized recipient `jaymn.judd@mascigc.com`
- only one active certification notification record at a time
- fail-closed override with automatic expiration and post-use disable semantics

## Implementation completed

### New / updated code

- `/app/backend/lib/preview_notification_certification.py`
  - bounded Preview-only certification override provisioning
  - exact-recipient send claim guard
  - original-intended-recipient preservation
  - operator-status notification fanout
  - webhook / provider reconciliation metadata hooks
- `/app/backend/lib/notification_delivery.py`
  - scoped Preview certification override support inside `deliver_notification`
  - truth-preserving permanent failure classification for invalid provider key errors
- `/app/backend/server.py`
  - Track 21.2 Resend SDK clamp now permits only the scoped certification send claim
  - `_dispatch_auto_email` now provisions the bounded override, preserves certification metadata, and writes workflow dispatch events for the certification lane
- `/app/backend/routes/resend_webhook.py`
  - certification reconciliation metadata updates wired into the existing webhook route
- `/app/backend/routes/daily_reports.py`
  - explicit certification override request fields accepted and persisted
- `/app/backend/lib/governed_certification_lane.py`
  - bounded fallback routing tightened so certification fallback recipient scope does not expand unexpectedly

### Targeted automated verification

- `pytest -q /app/backend/tests/test_s1_4_notification_delivery_certification.py /app/backend/tests/test_c2_phase2_notification_contract.py /app/backend/tests/test_dr03_governed_certification_lane.py /app/backend/tests/test_iter452_5_2_resend_webhook.py`
  - result: `29 passed`
- independent verification report: `/app/test_reports/iteration_50.json`
  - result: scoped override implementation verified; external blocker confirmed

## Controlled certification runs

### Run A — stale-code comparison only

- run_id: `s1-4-cert-f470927a9b`
- record_id: `369cde60-8e29-4e0c-b7e2-3c93cec2eef9`
- doc_id: `DR-2026-03556`
- outcome: `SAFE_CAPTURE` / `captured_preview`
- note: created before backend refresh; retained only as comparison evidence, not as the authoritative live-provider attempt

### Run B — authoritative bounded provider attempt

- run_id: `s1-4-cert-e217a5ffd8`
- record_id: `2e690268-7dba-42d7-aeea-c1d858797c91`
- doc_id: `DR-2026-03557`
- override_id: `94d23b6e-370e-4384-a230-c6a839006d5b`
- actual recipient: `jaymn.judd@mascigc.com`
- original intended recipients preserved separately: `['jaymn.judd@mascigc.com']`
- live mode activated: `PROVIDER_LIVE`
- provider called: `true`
- provider accepted: `false`
- final stored state: `permanent_failure`
- failure reason: `API key is invalid`

## Canonical chain evidence for Run B

### Trust Spine correlation

Correlation id: `cid-01803ab5f8714b248d4b1a2b46a30de6`

Observed stages for `DR-2026-03557`:

1. `record_created` → `ok`
2. `routing_resolved` → `ok`
3. `recipients_built` → `ok`
4. `notification_queued` → `ok`
5. `audit_written` → `ok`
6. `provider_accepted` → `failed` with `failure_reason="API key is invalid"`
7. `completed_for_environment` → `ok`

### Workflow dispatch evidence

Stored `workflow_state_events` for record `2e690268-7dba-42d7-aeea-c1d858797c91`:

- `NOTIFICATION_DISPATCH_ATTEMPTED`
  - binding_id: `94d23b6e-370e-4384-a230-c6a839006d5b`
  - recipient: `jaymn.judd@mascigc.com`
  - resolution_tier: `certification_override`
- `NOTIFICATION_DISPATCH_FAILED`
  - same binding_id
  - error: `API key is invalid`

### Routing audit evidence

`email_routing_audit_v2` row for `DR-2026-03557`:

- route_key: `AUTO_EMAIL_REPORTS`
- resolved_to_count: `1`
- resolved_cc_count: `0`
- resolved_bcc_count: `0`
- status: `permanent_failure`
- resend_message_id: `null`

### Operator status evidence

`notifications` collection row written:

- type: `notification_delivery.certification_pending`
- title: `S1-4 certification send armed — DR-2026-03557`
- recipient_role: `admin`
- linked_source_record_id: `2e690268-7dba-42d7-aeea-c1d858797c91`

## Reconciliation outcome

### Webhook proof source

- result: **not available for Run B**
- reason: provider auth failed before any provider message ID was issued

### Provider API corroboration

- direct SDK auth probe also failed with `ValidationError: API key is invalid`
- this independently confirms the provider credential blocker is external to the certification override logic

Final proof source classification for Run B:

- `WEBHOOK`: no
- `PROVIDER_API`: no successful provider session could be established
- `BOTH`: no
- authoritative blocker: **invalid Resend API key**

## Retry / idempotency decision

No second live certification message was sent.

Reason:

- the first authoritative provider attempt failed with a **permanent credential error**, not a retryable or inconclusive provider outcome
- per instruction, a second message is not allowed merely for more evidence

## Independent verification summary

Source: `/app/test_reports/iteration_50.json`

- scoped Preview-only override provisioned: PASS
- `PROVIDER_LIVE` activated only for certification lane: PASS
- `SAFE_CAPTURE` remains globally enabled: PASS
- original intended recipients preserved: PASS
- provider failure recorded truthfully: PASS
- synthetic / hidden Preview certification record markers: PASS
- webhook endpoint exists and remains wired: PASS
- final blocker: `RESEND_API_KEY is invalid`

## Final S1-4 status for this run

### Completed

- bounded Preview-only certification override implemented
- canonical trust spine / audit / dispatch-event chain verified
- operator-status notification row written
- permanent provider-auth failure classified truthfully and independently verified

### Blocked

- live provider submission could not complete because the configured `RESEND_API_KEY` is invalid
- webhook reconciliation and provider-message reconciliation cannot complete until a valid Resend key is supplied

### Required next action

1. rotate or replace `RESEND_API_KEY` with a valid Resend API key in `backend/.env`
2. restart backend
3. re-run exactly one bounded certification message
4. wait bounded window for webhook proof; fall back to provider API only if webhook does not arrive in time
5. append final provider proof source (`WEBHOOK`, `PROVIDER_API`, or `BOTH`) and close S1-4 as certified