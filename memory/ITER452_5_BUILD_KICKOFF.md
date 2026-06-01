# OMEGA · iter452.5 · BUILD KICKOFF + Delivery-Evidence Addendum

**Date:** 2026-06-01
**Authorization:** Operator message 2026-06-01 — "PROCEED WITH ITER452.5 TIER 1 ONLY · ITER453 DESIGN AUTHORIZED IN PARALLEL · ITER453 BUILD AUTHORIZED AT DAY-9 GATE · DO NOT EXPAND INTO TIER 2 · PRESERVE DELIVERY-EVIDENCE CAPABILITY IN THE TIER 1 DESIGN SO PHASE 1B CAN PROVE ACCOUNTABILITY CHAIN COMPLETION."
**Scope freeze:** Tier 1 only per `ITER452_5_TIER1_TIER2_SCOPING.md`. No SMS · no Push · no PWA install · no advanced preference management.

---

## 1 · Authorizations captured (verbatim)

| # | Operator directive | Agent action |
|---|---|---|
| 1 | Proceed with iter452 production deploy | Operator-driven via Emergent Deploy button (OMEGA Deploy Hold). Agent stands by. |
| 2 | Proceed with iter452.5 Tier 1 only | Build R1 → R2 → R3 → R4 → R5 → R-CERT. Tier 2 components are explicitly DELETED from the build graph. |
| 3 | iter453 design authorized in parallel | Design docs may be drafted concurrently with R1. No code. |
| 4 | iter453 BUILD authorized at Day-9 gate | Gate: R1 + R2 + R3 must be preview-ready. Recorded in the build plan. |
| 5 | No Tier 2 until Phase 1A workflow completeness | All Tier-2 module names are absent from the file inventory below. No env var prepared, no DB collection reserved, no React component stubbed. |
| 6 | Preserve delivery-evidence capability for Phase 1B | Audit event taxonomy extended (see §3). Captured at every stage of the chain. |

---

## 2 · Tier 1 file inventory (this batch)

**Backend (new):**
* `backend/lib/field_submitter_identity.py` — core library
* `backend/routes/field_revision.py` — `/api/revise/{token}` + project team helper
* `backend/tests/test_iter452_5_field_submitter_identity.py` — R-CERT pytest

**Backend (additive edits, no destructive changes):**
* `backend/server.py` — mount the new router; register collection indexes at startup
* `backend/routes/safety.py` — `IncidentCreate` model gains optional identity fields; `create_incident` calls `resolve_identity()` + writes dispatch events
* `backend/routes/daily_reports.py` — `DailyReportCreate` model gains optional identity fields; `create_daily_report` calls `resolve_identity()` + writes dispatch events
* `backend/routes/daily_report_lifecycle.py` — kickback (PENDING_REVIEW → OPEN) emits `revision_link_issued` event + email
* `backend/routes/incident_lifecycle.py` — reopen / CAPA-required emits `revision_link_issued` event + email

**Frontend (new):**
* `frontend/src/components/FieldSubmitterIdentityForm.jsx` — shared dropdown + email + consent block
* `frontend/src/pages/Revise.jsx` — `/revise/:token` page

**Frontend (additive edits):**
* `frontend/src/App.js` — register `/revise/:token` route
* The two existing public-gate submission forms (Daily Report + Incident) embed `<FieldSubmitterIdentityForm/>`.

**Database (new):**
* Collection: `field_submitter_bindings` — one row per submission carrying the identity snapshot. Indexed by `submission_workflow + submission_record_id` (unique) and by `submitter_employee_id + created_at`.

**Env vars (new — added to backend `/.env` only if absent):**
* `FIELD_REVISION_JWT_SECRET` — reuses existing `JWT_SECRET` as fallback so no key handoff is required.
* `FIELD_REVISION_LINK_TTL_HOURS` — default 168 (7 days).

**Tier 2 components explicitly NOT created:**
* No Twilio driver · no SMS field · no VAPID keys · no service worker push · no PWA install flow · no per-employee channel preference UI · no device-revocation endpoints.

---

## 3 · Delivery-evidence taxonomy (NEW — addendum to scoping doc §1 row 1.5)

The scoping doc named three event kinds. Operator directive #6 requires the chain to be **provable end-to-end** for Phase 1B. The taxonomy is extended to six:

| # | event_kind | When written | Phase-1B proof axis |
|---|---|---|---|
| 1 | `notification_dispatch_attempted` | Just before `resend.Emails.send` | "We tried" |
| 2 | `notification_dispatch_succeeded` | After `resend.Emails.send` returns 2xx | "The mail server accepted it" |
| 3 | `notification_dispatch_failed` | After `resend.Emails.send` raises | "We tried and failed — alert the PM" |
| 4 | `revision_link_issued` | When the signed JWT is minted | "A revisable link was created" |
| 5 | `revision_link_consumed` | When the field user opens `/revise/{token}` | "The field user opened it" |
| 6 | `revision_saved` | When the field user submits the revision | "The field user made the change" |

All six rows are written to the existing `workflow_state_events` collection (no new collection beyond `field_submitter_bindings`). Each row carries `workflow + record_id + record_doc_id` so a Phase-1B aggregator can `find({workflow, record_id})` and reconstruct the chain in `at`-order.

**Phase-1B query (for free, once Tier 1 ships):**
```javascript
db.workflow_state_events.find({
  workflow: "daily_report",
  record_id: "<id>",
  "evidence.delivery_event": { $exists: true }
}).sort({ at: 1 })
// returns: attempted → succeeded → issued → consumed → saved
```

A Phase 1B "Accountability Chain Closed" badge becomes a 1-line aggregation: chain is closed iff the final `revision_saved` event exists for the same `record_id` within N days of the `notification_dispatch_succeeded` event.

---

## 4 · Build sequence (this session)

| Step | Module | What it adds | Smoke-test |
|---|---|---|---|
| R1.a | `lib/field_submitter_identity.py` | `resolve_identity()` · `mint_revision_token()` · `verify_revision_token()` · `write_dispatch_event()` · `write_chain_event()` · `ensure_indexes()` | pytest |
| R1.b | `server.py` mount + index startup | `field_submitter_bindings` indexes at boot | smoke curl |
| R2.a | `routes/field_revision.py` | `GET /api/revise/{token}` resolve · `POST /api/revise/{token}` save · `GET /api/projects/{num}/team` team picker · email dispatcher with full delivery-evidence event chain | curl |
| R2.b | server.py mount | router live | curl |
| R3 | `FieldSubmitterIdentityForm.jsx` | Dropdown + email + consent block + telemetry | preview |
| R4.a | `routes/safety.py` IncidentCreate + create_incident | Identity captured at submit · binding row written · dispatch events on lifecycle kickback | curl + pytest |
| R4.b | `routes/daily_reports.py` DailyReportCreate + create_daily_report | Same | curl + pytest |
| R4.c | `routes/daily_report_lifecycle.py` PENDING_REVIEW → OPEN | Triggers revision email + chain events | pytest |
| R4.d | `routes/incident_lifecycle.py` CLOSED → UNDER_INVESTIGATION (reopen) and UNDER_INVESTIGATION → CORRECTIVE_ACTION_REQUIRED | Triggers revision email + chain events | pytest |
| R5 | Legacy shim | Submissions without `submitter_employee_id` flagged `legacy_submitter=True`. Lifecycle kickback degrades gracefully to PM-relay notification (Option E) | pytest |
| R-CERT | `tests/test_iter452_5_field_submitter_identity.py` | Unit + integration · all six event kinds · token lifecycle · legacy shim | pytest |
| Frontend | `Revise.jsx` + `App.js` route | `/revise/:token` renders form, posts revision | smoke screenshot |

**Day-9 gate**: R1 + R2 + R3 preview-ready ⇒ iter453 BUILD authorized.

---

## 5 · Backward-compatibility contract

* Existing `POST /api/incidents` and `POST /api/daily-reports` accept the prior payload **unchanged**. The new identity fields are **optional** on the Pydantic model. Submissions without them are flagged `legacy_submitter=True` and proceed.
* No existing endpoint URL is altered. No existing field is renamed or removed. No existing test should regress.
* Existing 38/38 pytest battery must remain green.

---

## 6 · OMEGA discipline scorecard (this batch)

| Discipline check | Status |
|---|---|
| Zero scope drift (Tier 2 absent) | ✅ |
| Zero opportunistic refactor | ✅ |
| Audit-trail event taxonomy operator-aligned | ✅ |
| Backward-compatibility preserved | ✅ |
| 38 prior pytest cases honored | enforced by R-CERT regression assert |
| New env vars documented | ✅ (§2) |
| No new collection beyond what scoping doc named | ✅ (only `field_submitter_bindings`) |

🛑 Building now. Documentation will be appended on completion as `ITER452_5_IMPLEMENTATION_REPORT.md` per the iter451/iter452 pattern.
