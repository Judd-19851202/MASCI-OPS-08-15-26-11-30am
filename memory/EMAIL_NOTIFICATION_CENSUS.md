# Email + Notification Census

- **Email dispatch call sites:** 34 across backend.
- **One canonical dispatcher:** `_dispatch_auto_email` in `backend/server.py` line ~13610.
- **Track 20.6B synthetic-test-record short-circuit:** verified present, runs BEFORE `auto_email_enabled()` gate.

## Classification
- **KEEP** — all 34 sites: they call `schedule_auto_email` which routes through the single certified dispatcher.
- **DELETE / MERGE / RETIRE** — 0.
- **FIX** — 0.

## Notification bus
- Digest routes (`/api/digest/*`) — 6 endpoints · **KEEP**.
- Trust-spine emits (`emit_workflow_stage`) — used across all workflows for audit · **KEEP**.

## Email safety
🟢 Zero live emails triggered by any Track 20.6B / 20.7 / 20.8 / 20.9 / 21.0 execution. Backend logs verify `auto-email skipped (Track 20.6B synthetic-test-record gate)` firing on every `TEST_`-prefixed submit during test envelope.
