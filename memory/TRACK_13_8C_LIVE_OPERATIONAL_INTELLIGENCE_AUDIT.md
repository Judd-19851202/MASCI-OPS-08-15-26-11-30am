# TRACK 13.8C — Live Platform Operational Intelligence Audit

**Date**: 2026-06-12
**Mode**: PRODUCTION READ-ONLY AUDIT → **HALTED · NO PRODUCTION ACCESS**
**Doctrine**: If you cannot confirm read-only production access, **STOP**. Preview adoption data is **not** representative and must **not** be substituted for production evidence.

---

## 1 · Executive Summary

**This audit cannot be completed as specified.** The Emergent preview pod where this work happens does not have read credentials for the production MASCI database. The only Mongo database accessible from this pod is `masci_safety_preview` on the production Atlas cluster — preview data only. Per the explicit directive (*"Do not use preview adoption data. Use live production data only."*) every Phase 2–11 metric is **deferred** until a read-only production query session is conducted by a human operator with production access.

This report does the **only** things that are honest given current access:

1. **Confirms** the safety lock — no writes, no mutations, no provider calls, no cron triggers, no test data, no production touches were performed (Section 2).
2. **Inventories** the production evidence sources by their **code-defined shape** (collections / log writers / endpoint surfaces). This is code-truth, not data-truth (Section 3). Code-truth is identical between preview and production because both run the same git revision.
3. **Hands off** an executable runbook of read-only Mongo queries an operator with production credentials can run to populate every requested metric (Section 4). The runbook is intentionally written so that copy-paste produces the report sections.
4. **Documents** the unknowns honestly (Section 5) so the deployment decision is made with eyes open.

**Recommendation**: Before any deploy / production-readiness call, an operator with production read credentials must run the §4 runbook. The output of those queries — not this report alone — is what justifies a Green / Yellow / Red call.

---

## 2 · Production Safety Confirmation

| Check | Verified value | Source |
|---|---|---|
| `APP_ENV` (pod) | `preview` | `/app/backend/.env` |
| `DB_NAME` (pod) | `masci_safety_preview` | `/app/backend/.env` |
| Mongo cluster host | `masci-prod.1nduwmg.mongodb.net` (Atlas cluster shared with prod) · `appName=MASCI-preview` | `/app/backend/.env` MONGO_URL |
| Production override credentials in pod | **NONE** — no `.env.production`, no `.env.prod`, no `MONGO_URL_PROD`, no `PROD_READ_TOKEN` | bash probe |
| Writes executed in this track | **ZERO** — no `insert*`, `update*`, `delete*`, `aggregate $merge`, `bulkWrite`, or restart was issued | session record |
| Provider calls executed | **ZERO** — no Motive, MaintainX, Resend, R2, SMS, or webhook calls | session record |
| Cron / scheduled job triggered | **ZERO** | session record |
| Emails / SMS sent | **ZERO** | session record |
| Frontend changes | **ZERO** | session record |
| Token / permission changes | **ZERO** | session record |
| Code changes | **ZERO** | session record |

> **Safety lock honoured.** This track produced markdown only. No production system was touched. No preview write occurred either (the seed from Track 13.7C, if still in place, is unaffected by this audit — operator may roll it back at any time via `python3 /app/scripts/preview_seed_13_7c.py rollback`).

---

## 3 · Evidence Sources Inventory (code-truth · what an operator with prod access can query)

The following collections / logs exist in the application schema (verified by grep against `routes/`, `services/`, and `db.<collection>` references). For each, this is the **shape an operator can query**, not the current production count.

| Source | Records what | Likely fields | Window field | Reliability when present |
|---|---|---|---|---|
| `audit_logs` | every admin-mutating action (IAM, settings, deploys, integrations) | `actor_id`, `action`, `target`, `ts`, `outcome` | `ts` | High |
| `operational_events` (collection) | system-detected operational events (asset moves, geofence enter/exit, dispatch state) | `event_kind`, `project_number`, `detection_key`, `event_at`, `dispatch_status` | `event_at` | High |
| `motive_events` | Motive webhook + poll events | `provider`, `event_kind`, `vehicle_id`, `event_at`, `received_at` | `event_at` | High (Motive live) |
| `asset_mappings` | canonical mappings (provider → MASCI spine) | `provider`, `masci_equipment_id`, `masci_unit_number`, `motive`, `maintainx_asset_id`, `fleetwatcher_asset_id` | `updated_at` | High |
| `dispatch_assignments` | every dispatch assignment lifecycle | `created_at`, `status`, `driver_id`, `asset_key`, `project_number` | `created_at` / status timestamps | High |
| `daily_reports` | foreman/super daily report submissions | `submitted_at`, `status` (draft / submitted / approved / needs_revision), `project_number`, `submitted_by` | `submitted_at`, status_history | High |
| `qaqc_inspections` | QA/QC inspection submissions | `status`, `created_at`, `closed_at` | timestamps | High |
| `incidents` | safety incidents | `status`, `reported_at`, `closed_at` | timestamps | High |
| `corrective_actions` (CAPAs) | corrective actions | `status`, `created_at`, `due_at`, `closed_at` | timestamps | High |
| `operational_constraints` | project constraints (formerly "risks") | `status`, `created_at`, `resolved_at` | timestamps | High |
| `fleet_defects` | DVIR-derived defects | `status` (open / acknowledged / repaired / cleared), `reported_at`, `cleared_at`, `truck_unit_number` | `reported_at` | High |
| `fleet_status` | per-asset operational state | `status` (oos / defect_open / available / etc.), `updated_at` | `updated_at` | High |
| `equipment_inspections` | pre-op / post-op inspections | `status`, `inspection_date`, `equipment_master_id` | `inspection_date` | High |
| `jha_acknowledgements` | JHA crew acknowledgements | `acknowledged_at`, `crew`, `project_number` | `acknowledged_at` | High |
| `employee_requests` | HR action requests | `status`, `submitted_at`, `closed_at` | timestamps | High |
| `time_off_requests` | HR time-off | `status`, `submitted_at`, `approved_at` | timestamps | High |
| `po_requests` | PO Requests (lifecycle: open → approved → receipt → close / cancel) | `status`, `created_at`, `approved_at`, `received_at`, `closed_at`, `cancelled_at` | created_at + per-status | High |
| `training_records` | training records | `completed_at`, `expires_at` | timestamps | Medium (depends on capture) |
| `document_expirations` | expiry tracker | `expires_at`, `acknowledged_at` | timestamps | High |
| `job_photos` | photo library entries | `uploaded_at`, `tagged_to` | `uploaded_at` | High |
| `notifications` (in-app) | per-user notification feed | `created_at`, `read_at`, `acknowledged_at`, `recipient_id` | `created_at` | High |
| `notification_log` / `email_log` (if present) | email/SMS send attempts via Resend / SMS provider | `provider`, `to`, `status`, `sent_at`, `error` | `sent_at` | Medium (verify exists) |
| `scheduler_runs` | cron / scheduled job runs | `job_name`, `started_at`, `ended_at`, `status`, `error` | `started_at` | High |
| `webhook_logs` / `integrations.webhooks` collection | inbound webhook receipts | `provider`, `received_at`, `verified`, `error` | `received_at` | Medium (verify) |
| `usage_analytics` (collection · referenced by `routes/usage_analytics.py`) | frontend / backend usage events | route, user role, timestamp | timestamp | Medium (verify population) |
| `last_activity` (referenced by `routes/last_activity.py`) | last-active per user | user_id, last_seen_at | last_seen_at | High |
| `draft_telemetry` | form-draft lifecycle | route, draft state, ts | ts | Medium |
| `signatures` / `signature_audit` | e-signature trail | who, what, when | ts | High |
| `operational_locations` reconciliation queue | geofence reconciliation lifecycle | status (pending / approved / rejected), submitted_at | timestamps | High |
| `backup_verification_runs` | nightly backup verification | run_at, ok | run_at | High |
| `motive_geofences` | imported Motive geofences | last_synced_at | last_synced_at | High |
| `dispatch_day1_debrief` records | day-1 debrief output | created_at | created_at | High |

Tables that **may** exist but were not source-confirmed by name and need verification:
- `auth_failures` / `login_attempts` — Phase 9 needs these or equivalent for failed-login audit.
- `frontend_errors` / `client_logs` — Phase 4 needs these for white-screen / component-crash counts.
- `route_access_log` — Phase 2 needs this for portal page-view counts.

If any of the "verify exists" rows are missing in production, the corresponding Phase 2–9 metrics will be marked **NOT INSTRUMENTED** in the operator's run. **This is acceptable — honest absence beats invented numbers.**

---

## 4 · Operator Runbook · Read-Only Production Query Pack

> **This runbook is for the human operator with production read credentials to execute. Do NOT run it from a write-capable connection.**
> Every query is a Mongo aggregation with **zero `$out`, zero `$merge`, zero `update`, zero `delete`, zero `insert`**. All read-only.

### 4.1 · Pre-flight (confirm read-only)
```js
// In mongosh against the production database, verify connection has NO write capability:
db.runCommand({ connectionStatus: 1 }).authInfo.authenticatedUserRoles
// EXPECTED: a role that includes `read` only · NOT `readWrite` · NOT `dbAdmin` · NOT `clusterAdmin`.
// If readWrite or dbAdmin appears, ABORT. Use a read-only role only.
```

### 4.2 · Time windows (paste once, reuse)
```js
const NOW = new Date();
const D7  = new Date(NOW.getTime() - 7  * 24 * 3600 * 1000).toISOString();
const D30 = new Date(NOW.getTime() - 30 * 24 * 3600 * 1000).toISOString();
const D90 = new Date(NOW.getTime() - 90 * 24 * 3600 * 1000).toISOString();
```

### 4.3 · Phase 2 — Portal usage audit
```js
// usage_analytics is the canonical source. If empty / absent → NOT INSTRUMENTED.
db.usage_analytics.aggregate([
  { $match: { ts: { $gte: D30 } } },
  { $group: { _id: { portal: "$portal", role: "$role" }, events: { $sum: 1 }, uniq: { $addToSet: "$actor_id" } } },
  { $project: { _id: 0, portal: "$_id.portal", role: "$_id.role", events: 1, unique_actors: { $size: "$uniq" } } },
  { $sort: { events: -1 } }
]).toArray();

// Per-route 30-day usage:
db.usage_analytics.aggregate([
  { $match: { ts: { $gte: D30 } } },
  { $group: { _id: "$route", events: { $sum: 1 } } },
  { $sort: { events: -1 } }, { $limit: 50 }
]).toArray();

// Per-portal first/last seen:
db.usage_analytics.aggregate([
  { $group: { _id: "$portal", first: { $min: "$ts" }, last: { $max: "$ts" } } }
]).toArray();
```

### 4.4 · Phase 3 — Workflow volume audit
Repeat the pattern below for **each collection** in §3 (changing the `COLL` and timestamp field):

```js
const COLL = "daily_reports";   // change to each target collection
const TS   = "submitted_at";    // or "created_at" / "reported_at" / etc.

[
  { window: "7d",  cutoff: D7  },
  { window: "30d", cutoff: D30 },
  { window: "90d", cutoff: D90 },
  { window: "all", cutoff: null },
].map(w => ({
  window: w.window,
  total: db[COLL].count(w.cutoff ? { [TS]: { $gte: w.cutoff } } : {}),
  by_status: db[COLL].aggregate([
    ...(w.cutoff ? [{ $match: { [TS]: { $gte: w.cutoff } } }] : []),
    { $group: { _id: "$status", n: { $sum: 1 } } }
  ]).toArray()
}));

// Oldest open (per workflow that has "open" or equivalent):
db[COLL].find({ status: "open" }).sort({ [TS]: 1 }).limit(1).project({ id: 1, [TS]: 1, status: 1 });

// Stale: open and older than 14 days
db[COLL].count({ status: "open", [TS]: { $lt: D14 = new Date(NOW.getTime() - 14*24*3600*1000).toISOString() } });
```

**Collections to repeat for**: `daily_reports`, `qaqc_inspections`, `jha_acknowledgements`, `incidents`, `corrective_actions`, `operational_constraints`, `fleet_defects`, `fleet_status`, `equipment_inspections`, `dispatch_assignments`, `employee_requests`, `time_off_requests`, `po_requests`, `training_records`, `document_expirations`, `job_photos`, `notifications`, `operational_events`, `operational_locations`, `signatures`.

### 4.5 · Phase 4 — Reliability / failure audit
```js
// Backend errors (if `error_log` collection exists):
db.getCollectionNames().filter(n => /error|log|exception/i.test(n));   // discover
// Then for the canonical error log (e.g. `error_log`):
db.error_log.aggregate([
  { $match: { ts: { $gte: D30 } } },
  { $group: { _id: "$status_code", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
]).toArray();

// Scheduled jobs failed runs:
db.scheduler_runs.aggregate([
  { $match: { started_at: { $gte: D30 } } },
  { $group: { _id: { job: "$job_name", status: "$status" }, n: { $sum: 1 } } }
]).toArray();

// Webhook failures:
db.webhook_logs.count({ received_at: { $gte: D30 }, verified: false });
db.webhook_logs.aggregate([
  { $match: { received_at: { $gte: D30 } } },
  { $group: { _id: { provider: "$provider", verified: "$verified" }, n: { $sum: 1 } } }
]).toArray();

// Auth failures (verify collection name first):
db.getCollectionNames().filter(n => /auth|login|mfa/i.test(n));
```

### 4.6 · Phase 7 — Stale work
For each workflow:

```js
db.fleet_defects.aggregate([
  { $match: { status: "open" } },
  { $group: { _id: null, n: { $sum: 1 }, oldest: { $min: "$reported_at" } } }
]).toArray();
```
Repeat for `corrective_actions`, `operational_constraints`, `employee_requests`, `time_off_requests`, `po_requests`, `qaqc_inspections`, `incidents`, `equipment_inspections`, `notifications` (acknowledged_at == null), `daily_reports` (status == draft + > 7d), and any other lifecycle collection from §3.

### 4.7 · Phase 8 — Integration reality
```js
// Motive:
db.motive_events.aggregate([
  { $match: { event_at: { $gte: D7 } } },
  { $group: { _id: "$event_kind", n: { $sum: 1 } } }
]).toArray();
db.motive_events.find().sort({ event_at: -1 }).limit(1).project({ event_at: 1 });

// MaintainX (likely empty):
db.getCollectionNames().filter(n => /maintainx/i.test(n));
// + check `integration_settings` for the `maintainx` row's `enabled`/`api_key_present` flags
db.integration_settings.find({ provider: "maintainx" }).project({ enabled: 1, api_key_present: 1, last_test_at: 1 });

// FleetWatcher (likely zero rows):
db.getCollectionNames().filter(n => /fleetwatcher/i.test(n));

// Resend (email delivery):
db.notification_log.aggregate([
  { $match: { sent_at: { $gte: D7 } } },
  { $group: { _id: { provider: "$provider", status: "$status" }, n: { $sum: 1 } } }
]).toArray();
```

### 4.8 · Phase 6 — PO Requests adoption
Critical question from Track 13.8B Hidden Gold #1:
```js
db.po_requests.aggregate([
  { $facet: {
      all_time:     [ { $count: "n" } ],
      last_90:      [ { $match: { created_at: { $gte: D90 } } }, { $count: "n" } ],
      last_30:      [ { $match: { created_at: { $gte: D30 } } }, { $count: "n" } ],
      last_7:       [ { $match: { created_at: { $gte: D7  } } }, { $count: "n" } ],
      by_status:    [ { $group: { _id: "$status", n: { $sum: 1 } } } ],
      first_seen:   [ { $sort: { created_at: 1 } }, { $limit: 1 }, { $project: { created_at: 1 } } ],
      last_seen:    [ { $sort: { created_at: -1 } }, { $limit: 1 }, { $project: { created_at: 1 } } ],
      with_receipt: [ { $match: { received_at: { $ne: null } } }, { $count: "n" } ]
  } }
]).toArray();
```
**If 30-day count is 0–5** → the system is built but operationally unused (validates the hidden-gold thesis · operator interview confirms next).
**If 30-day count > 20** → the system is in active use; surfacing on PM Hub V2 would amplify, not introduce.
**If created_at always = approved_at** → no approval cycle in practice; "approval workflow" is being bypassed.

### 4.9 · Phase 9 — Auth signals
```js
// Discover collection names:
db.getCollectionNames().filter(n => /mfa|passkey|session|auth|login/i.test(n));

// Failed login attempts (whichever collection is canonical):
// Aggregate by hour-bucket; identify spikes:
db.<auth_failure_coll>.aggregate([
  { $match: { ts: { $gte: D7 } } },
  { $group: { _id: { $dateToString: { format: "%Y-%m-%d %H", date: { $toDate: "$ts" } } }, n: { $sum: 1 } } },
  { $sort: { _id: 1 } }
]).toArray();
```
**Do not print credential values · do not print tokens · use aggregate counts only.**

### 4.10 · Phase 9 — Driver public flow
```js
// Driver shift starts:
db.driver_shifts.aggregate([
  { $match: { started_at: { $gte: D30 } } },
  { $group: { _id: null, n: { $sum: 1 }, completed: { $sum: { $cond: [{ $ne: ["$completed_at", null] }, 1, 0] } } } }
]).toArray();

// Magic-link usage:
db.driver_magic_links.aggregate([
  { $match: { issued_at: { $gte: D30 } } },
  { $group: { _id: null, issued: { $sum: 1 }, exchanged: { $sum: { $cond: [{ $ne: ["$exchanged_at", null] }, 1, 0] } } } }
]).toArray();
```
Verify the public flow (Driver hard lock) is actually exercised in production. If the exchange rate is high → workflow is healthy. If issued >> exchanged → magic links are not being delivered or drivers aren't tapping them.

---

## 5 · Unknowns / Not Instrumented (honest list)

Until §4 is executed by an operator with prod read access, every item below is **UNKNOWN**:

| Phase | Unknown |
|---|---|
| 2 | Per-portal 7/30/90-day visit counts · unique actors · trend direction · most/least/never-used routes |
| 3 | Per-workflow 7/30/90-day created / submitted / completed / pending / abandoned / reopened counts · oldest open / time-to-completion |
| 4 | Backend 5xx counts · validation-error counts · auth-error counts · most-affected routes · most-affected workflows |
| 5 | Which workflows are demonstrably reliable · which integrations are silently working |
| 6 | Is PO Requests adopted? Is Operational Events project-day consumed by anyone? Is the Operational Locations reconciliation queue worked? |
| 7 | Stale work counts and ages across every lifecycle collection |
| 8 | Motive 7d/30d event volume · MaintainX live status · Resend send/error counts · webhook verified vs. unverified rate · last-successful vs last-failed timestamps |
| 9 | Failed login spikes · token failures · permission-mismatch events · public-driver-flow exception rate |
| 10 | The full usage + failure matrix |
| 11 | Top 10 evidence-backed risks |
| 12 | Top 10 evidence-backed opportunities |
| 13 | Green / Yellow / Red readiness call per core area |

**This list is the answer to the brief's "What is missing?" question.** It is also the deployment-readiness gate: every Yellow / Red answer that emerges from running §4 against production becomes an explicit pre-deploy ticket.

---

## 6 · What CAN Be Said With Code-Truth Today (no production data needed)

These claims hold true regardless of access because they read source files only:

- **Map engine**: one engine (`operations_map_v1.py` snapshot · `MapCanvas.jsx` renderer). No duplicate map engine. **Hard lock intact in source.**
- **Driver hard lock**: no `/driver/*` auth endpoint exists. Public flow only. **Hard lock intact in source.**
- **Shop hard lock**: `summary.shop` distinguishes `repair_complete` and `returned_to_service_7d` as separate fields (`routes/dispatch_command_center.py`). **Hard lock intact in source.**
- **MaintainX**: stub (`awaiting_credentials`) confirmed by source. Will return 0 production activity unless credentials were activated outside this audit.
- **FleetWatcher**: no service file in source. Will return 0 production activity.
- **Motive**: live service (`services/motive_service.py`) wired to webhooks + poll. Production volume requires §4.7 to read.
- **PO Requests**: 12 backend endpoints + 795-line frontend (Track 13.8B). Production adoption requires §4.8 to read.
- **Operational Records family**: 8 modules in backend; 5 of them have zero frontend consumers (per Track 13.8B grep). Production usage of admin-only endpoints requires §4.3 to read.
- **Notifications stack**: 11 task endpoints + 6 portal-digest endpoints exist in source. Production send/error rates require §4.5 to read.
- **Backup verification**: nightly job exists in source (`routes/backup_verification_routes.py`). Production runs require §4.5 to read.
- **Scheduler runs**: surfacing exists in source (`routes/scheduler_runs_admin.py`). Production cron health requires §4.5 to read.

---

## 7 · Final Recommendation

1. **Do not deploy on the basis of this report alone.** It is intentionally incomplete because the safety lock required halting at "no production access".
2. **Authorise one operator (or platform engineer) with read-only production credentials to execute §4** against the production DB. Estimated 30–60 minutes of `mongosh` time. The runbook is structured so the output drops directly into Phases 2–13 of a follow-up `TRACK_13_8C_LIVE_RESULTS.md` report.
3. **No code changes are needed before that runbook runs.** Doctrine: discover reality first, then decide.
4. **If the runbook surfaces a Red signal** (e.g., backend 5xx > 1% on any portal, or driver-shift completion rate < 80%, or stale CAPAs > 30 days old), the deploy is **Yellow at best** until those are addressed. None of those answers can be guessed from the pod.
5. **Do not interpret PO Requests / Operational Events / Operational Locations adoption from this report.** Track 13.8B suggested they are under-surfaced; only the §4.8 query confirms whether they are *actually unused* (validates the hidden-gold thesis) or just *invisible in this pod* (changes nothing about adoption).
6. **Hard locks remain enforced in source** (§6). Production runtime behaviour of those locks (no driver auth, dispatch map dominance, single map engine, Shop repair ≠ RTS) does **not** require a production probe — source-truth is sufficient.
7. **Track 13.8C remains formally OPEN** until §4 results are pasted into a follow-up `TRACK_13_8C_LIVE_RESULTS.md` and a Green/Yellow/Red call is made on each Phase 13 core area.

---

## 8 · Files Produced This Track

| File | Type | Purpose |
|---|---|---|
| `/app/memory/TRACK_13_8C_LIVE_OPERATIONAL_INTELLIGENCE_AUDIT.md` | new file (this report) | Halt + handoff + runbook |
| `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md` | append | Ledger entry |
| `/app/memory/PRD.md` · `/app/memory/CHANGELOG.md` · `/app/memory/ROADMAP.md` | append | Doctrine bookkeeping |

**Zero code changes. Zero production touches. Zero preview writes.**

---

## 9 · Closing

This audit's value comes from **what it did not do** as much as from **what it documented**. It refused to fabricate production numbers from preview data. It refused to write or call any production system. It refused to estimate adoption from feelings. It delivered the runbook that converts code-truth into data-truth — for whoever holds production credentials to execute under their own audit trail.

**Track 13.8C · HALTED · DELIVERABLE COMPLETE. Awaiting operator runbook execution against production read-only access.**
