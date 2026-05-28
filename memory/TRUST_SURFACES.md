# TRUST SURFACES — REGISTRY

_Phase GOVERNANCE-INFRA-1 · Workstream 2 · 2026-05-28._

A **Trust Surface** is any platform surface where an operator-visible
state (saved / synced / approved / pending / safe) must remain
truthful under field conditions. Every trust surface in the platform
inherits the seven doctrine fields below. Future features
**MUST** declare their surface in this registry before merge.

Companion machine-readable manifest: `TRUST_SURFACES.json`.

---

## Doctrine Fields (every surface declares all seven)

| Field | Purpose |
|---|---|
| **survivability** | What survives reload / token rotation / Safari ITP / quota / offline |
| **truthful-state** | What states the surface MAY claim. False-positive states forbidden. |
| **authority** | Which capability flags gate which actions. Capability-scoped only. |
| **telemetry** | Which events the surface emits + when |
| **recovery** | What operator-facing recovery affordance exists when state is lost |
| **calmness** | Wording / colour / animation constraints |
| **regression** | Which pw_suite tests lock the contract |

---

## Daily Reports
* **survivability**: IDB autosave (device-scoped actorId · 24h archive on discard · photos in `photoStaging` blob store · idempotency key persisted across reload).
* **truthful-state**: `idle` / `saving` / `saved` / `failed`. Pill MUST distinguish queued vs server-confirmed.
* **authority**: `po.request.respond_clarify` for clarification flow; create/upload unrestricted within FL+Admin+PM+HR.
* **telemetry**: `draft.write.ok` · `draft.write.fail` · `draft.restore.offered` · `draft.restore.action` · `draft.recovery.absent` · `draft.lifecycle` · `quota.warning`.
* **recovery**: `DraftRestorePrompt` · `DraftRecoveryNotice` (24h archive) · `PriorUsageBanner` (TF-001).
* **calmness**: slate banners · amber chips (never red) · operator language ("Storage 82% full") · no debug / ITP / corruption wording.
* **regression**: `test_draft_loss_remediation.py` (mobile+ipad) · `test_field_trust_iter442.py` · `test_trust1_wave1_wave2_calmness.py` · `test_trust1_final_hardening.py`.

## PO Requests (Procurement)
* **survivability**: IDB autosave for the request form · idempotency key persisted across reload (NewDailyReport pattern · iter440).
* **truthful-state**: `Submitted` / `Pending Approval` / `Clarification Needed` / `Approved` / `Pending Receipt` / `Overdue Receipt` / `Receipt Uploaded` / `Closed` / `Cancelled` / `Rejected`. Approval block only when status permits.
* **authority**: `po.approve` · `po.reject` · `po.clarify` · `po.issue_number` · `po.set_approved_amount` · `po.close` · `po.cancel`. Field Leadership FORCED OFF for all approver caps.
* **telemetry**: backend operational signals (`po.approve`, `po.reject`, `po.clarify`, `po.close`, `po.cancel`, `po.receipt`); frontend draft autosave events.
* **recovery**: requester can re-submit if clarification responded; admin can cancel mid-workflow.
* **calmness**: "Authority & Visibility" banner explains who-does-what. No permission-denied toasts.
* **regression**: `test_trust_po1_backend_enforcement.py` · `test_trust_po1_frontend_capability_scope.py`.

## Incidents
* **survivability**: IDB autosave (`incident-new` form key) · idempotency key persisted · photo blobs IDB-staged.
* **truthful-state**: form-level draft pill same contract as Daily Reports.
* **authority**: Safety + Admin can investigate / close. Reporters can view their own.
* **telemetry**: standard draft.* event family.
* **recovery**: `DraftRestorePrompt`.
* **calmness**: same colour palette as Daily Report.
* **regression**: `test_contextual_return_path_iter443.py` (return-path) · draft suite covers the IDB pattern.

## CAPAs
* **survivability**: linked to incidents; share incident draft survivability via `ViewIncident`.
* **truthful-state**: `Open` / `In Progress` / `Pending Verification` / `Closed`. Verification audit chain (append-only).
* **authority**: Safety + Admin manage; reporters can view their CAPAs.
* **telemetry**: CAPA-specific events emitted by `routes/capa.py`.
* **recovery**: re-open path requires explicit admin action.
* **calmness**: slate / amber palette consistent with incident.
* **regression**: TBD — Wave 3 doctrine extension will add `test_contextual_return_path` coverage.

## RFIs (Phase V — planned, NOT yet implemented)
* **survivability**: TBD — must inherit Daily Report autosave doctrine.
* **truthful-state**: `Open` / `Sent` / `Answered` / `Closed`. Sent ≠ Delivered ≠ Acknowledged — must be truthful about each.
* **authority**: PM + Admin send; Subs respond; FL view-only on their job's RFIs.
* **telemetry**: TBD — submit / response / dead-letter / re-send events.
* **recovery**: dead-letter requeue when external collaboration fails.
* **calmness**: TBD — adhere to the existing doctrine palette.
* **regression**: TBD — must be locked at MVP.

## Schedule Imports (Phase V.3 — planned)
* **survivability**: `.xer` upload with chunked progress; resume on reconnect.
* **truthful-state**: `Uploaded` ≠ `Parsed` ≠ `Linked`. Each state distinct in UI.
* **authority**: PM + Admin upload.
* **telemetry**: upload start / upload ok / parse fail / link complete.
* **recovery**: re-upload preserves prior linkage.
* **calmness**: long-running progress with calm "Still working" copy.
* **regression**: TBD.

## Offline Queue (Shared)
* **survivability**: IDB-backed `resiliencyQueue`. Max retries = 5; on exhaustion, `status=failed` + `queue.exhausted` listener fires.
* **truthful-state**: queued ≠ confirmed; the pill MUST NOT say "Saved" for queued-not-yet-sent items unless server confirms via `onQueueItemSettled` callback (TRUST-1 TF-011).
* **authority**: orthogonal — queue is content-agnostic.
* **telemetry**: `queue.commit.confirmed` · `queue.commit.failed`.
* **recovery**: drain on focus/online; manual replay (admin).
* **calmness**: calm "queued · will upload when reconnected" toast.
* **regression**: `test_draft_loss_remediation.py` exercises the queued path.

## Notifications / Bell Feed
* **survivability**: server-authoritative; no offline buffering.
* **truthful-state**: read ≠ acknowledged; unread count must match list.
* **authority**: routing is role-scoped (`assignee_role` + `cc_roles`); FL never receives approver-queue notifications.
* **telemetry**: existing notification fan-out logs.
* **recovery**: digest endpoint surfaces missed notifications.
* **calmness**: no badge pulse > 60s; no sound.
* **regression**: `test_trust_po1_backend_enforcement.py::test_approval_task_assigned_to_pm_not_leadership`.

## Shared Surfaces (cross-portal · `/po-requests`, future `/rfis`, `/schedule`)
* **survivability**: inherits per-form survivability above.
* **truthful-state**: every shared surface MUST consult `getPortalContext()` for capability gating.
* **authority**: capability-scoped rendering via `poCapabilities.js` (or future siblings).
* **telemetry**: per-surface as above.
* **recovery**: per-surface.
* **calmness**: per-surface. Banner explains who-does-what regardless of caller.
* **regression**: per-surface frontend cap-scope test.

## Restore / Recovery Systems
* **survivability**: IDB-only; never server-side autosave (TRUST-1 doctrine).
* **truthful-state**: `pendingDraft` non-null ⇔ archive entry exists ⇔ banner shows. Mutually consistent.
* **authority**: device-scoped — no cross-device restore.
* **telemetry**: `draft.restore.offered` / `draft.restore.action(restore|discard)`.
* **recovery**: this IS the recovery surface.
* **calmness**: slate-only · reassuring · NEVER amber for restore-state.
* **regression**: `test_field_trust_iter442.py` · `test_trust1_*.py`.

---

## Adding a new trust surface

1. Open a PR that adds a stanza to this file AND `TRUST_SURFACES.json`.
2. Reference the capability flag(s) the surface depends on.
3. Add the regression test path(s) — even if marked TBD.
4. The pre-deploy Authority Mismatch Probe scans for token-coexistence
   rendering on the new surface; resolve any violations before merge.
