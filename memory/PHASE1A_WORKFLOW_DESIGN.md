# Phase 1A · Workflow Design

**Program:** OMEGA · Platform Completion Program (PCP)
**Phase:** 1A · Mission-Critical Dead-End Removal · DESIGN STAGE
**Mode:** Design-only · no code changes · awaits operator certification before Build stage
**Scope:** **6 workflows** currently 🔴 INCOMPLETE — Incidents · Daily Report Office Review · Payroll Variance Finalization · QA/QC Deficiency Follow-Up · Site Inspection Follow-Up · **JHA Acknowledgement Ledger (OC-005 · elevated iter449)**
**Companion:** `PHASE1A_STATE_MACHINE.md` · `PHASE1A_ROLE_MATRIX.md` · `PHASE1A_CERTIFICATION_PLAN.md`
**Date:** 2026-06-01

---

## 0 · Design principles (apply to all 5 workflows)

1. **One canonical state machine.** All five workflows resolve to the same 5-state vocabulary defined in Phase 1B: `OPEN · IN_PROGRESS · PENDING_REVIEW · PENDING_CLOSURE · CLOSED`. (PENDING_CLOSURE is optional; see §0.2.)
2. **Native + canonical fields coexist.** Existing native fields (e.g., `incidents.status`, `corrective_actions.status`) are NOT removed. A parallel `lifecycle_state` field is introduced for canonicalization. Migration is read-shim until Phase 1B completes.
3. **Every transition writes an audit row.** A single sibling collection `workflow_state_events` (per workflow type) records `{workflow, doc_id, from_state, to_state, actor_id, actor_role, reason, occurred_at, metadata}`. No inline-only history.
4. **Every transition has at least one role authorized.** No state is "stuck" with no actor. Role matrix in `PHASE1A_ROLE_MATRIX.md`.
5. **Closure requires explicit closure conditions.** No silent / derived closure. Closure conditions are enumerated per workflow in §1-§5.
6. **Every closure can be reopened by an authorized actor with a required `reason`.** Reopens write a new state event.
7. **No regressions.** Existing Create + View + Delete continue unchanged. New endpoints are additive.
8. **All transitions enforce idempotency** — a state-event row with the same `(workflow, doc_id, to_state, actor_id, occurred_at_minute)` is rejected to prevent double-clicks creating duplicate audit rows.
9. **Backwards-compatible UI rendering.** Existing consumers (Accountability projection, Command Center, frontend list filters) continue to derive their projections until they migrate to read `lifecycle_state` (Phase 1B).
10. **Out-of-band manual writes are forbidden** to `lifecycle_state` — all writes go through transition endpoints which validate from-state, actor role, and required reason.

### 0.1 · Canonical 5 states (Phase 1B-aligned)

| Canonical | Plain English | Terminal? | Reopen-able? |
|---|---|---|---|
| `OPEN` | Filed; not yet acted on | no | n/a |
| `IN_PROGRESS` | Active investigation / review / work | no | n/a |
| `PENDING_REVIEW` | Field/owner work complete; waiting for reviewer sign-off | no | n/a |
| `PENDING_CLOSURE` | Optional intermediate · awaiting external dependency (e.g., open CAPA, OSHA filing) | no | n/a |
| `CLOSED` | Terminal · operational record complete | ✅ | ✅ via authorized reopen |

`PENDING_CLOSURE` is used only when an external blocker is enumerated (e.g., incident with open CAPAs). Workflows without external dependencies skip directly `PENDING_REVIEW → CLOSED`.

### 0.2 · Transition contract (universal)

Every state transition endpoint:
* Path: `POST /api/<workflow>/{id}/transition`
* Body: `{ to_state: "<canonical>", reason?: str, metadata?: dict }`
* Auth: role-gated per `PHASE1A_ROLE_MATRIX.md`
* Validates: current state allows transition · actor has permission · required fields per to_state (e.g., `reason` mandatory on REOPEN and on REJECTION transitions)
* Writes: `workflow_state_events` row + updates `lifecycle_state` + updates `closed_at`/`closed_by` if to_state is CLOSED
* Returns: updated doc + new state event ID
* Idempotency: 409 if same actor + same to_state + same minute already recorded

---

## 1 · Incident Lifecycle

### 1.1 · Source of friction
* `INCIDENT_LIFECYCLE_AUDIT.md` documented the 4-way vocabulary split. Today every incident reads `status: "open"` and no transition is possible.
* Operator-stated vocab (Under Investigation · Corrective Action Required · Pending Closure · Closed) maps to canonical 1:1 as below.

### 1.2 · State map (per incident)

```
OPEN
  ├─→ IN_PROGRESS  ("Under Investigation"; opened by Safety or Admin)
  │     ├─→ PENDING_REVIEW  ("All investigative findings recorded; awaiting Safety final review")
  │     └─→ PENDING_CLOSURE ("Awaiting CAPA(s) to close" — auto-transition when ≥1 linked CAPA exists and ≥1 is not yet Closed/Verified)
  │
  ├─→ PENDING_REVIEW (only allowed when incident is corrected_on_site == "Yes" and no CAPA needed)
  │
PENDING_REVIEW
  └─→ CLOSED  ("Operationally complete"; closer = Safety or Admin)
  └─→ IN_PROGRESS  ("Reopen for further investigation"; reason required)
  
PENDING_CLOSURE
  └─→ PENDING_REVIEW  (auto-transition once last linked CAPA reaches Closed/Verified)
  └─→ IN_PROGRESS  ("Reopen investigation" with reason)
  
CLOSED
  └─→ IN_PROGRESS  ("Reopen incident"; reason required; closer event preserved in audit)
```

### 1.3 · Closure conditions

A transition `PENDING_REVIEW → CLOSED` requires ALL of:
* No linked CAPA in state `Open` or `In Progress` or `Pending Review` (CAPA-side vocab; Phase 1B canonicalizes)
* If `osha_recordable == "Yes"` and `severity ∈ {Fatality, Lost Time, Hospitalization}`: an OSHA form linkage (existing OSHA 300/301 surfaces) must be confirmed by Safety officer at closure (checkbox + audit row)
* Closer role ∈ {Safety, Admin, Super-Admin}

### 1.4 · Auto-transitions

* `OPEN → PENDING_CLOSURE` when first CAPA is linked AND remains open
* `PENDING_CLOSURE → PENDING_REVIEW` when last linked CAPA reaches `Closed`/`Verified`
* No state is auto-cleared without an authorized human action (no time-based auto-closure)

### 1.5 · Required new endpoints (Build stage)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/incidents/{id}/transition` | universal transition |
| `GET` | `/api/incidents/{id}/state-events` | per-doc history |
| `GET` | `/api/admin/workflow-state-events?workflow=incidents` | admin cross-cutting |

### 1.6 · Schema additions (incidents)

```
lifecycle_state           str       canonical 5-state vocab
state_changed_at          ISO ts    last transition time
state_changed_by          str       actor user_id (legacy admin token resolves to "admin")
closed_at                 ISO ts    null until CLOSED
closed_by                 str       actor user_id
reopened_count            int       monotonic counter
osha_closure_attested     bool      only meaningful for OSHA-recordable
```

Existing `status`, `resolution_status`, and the Sprint 1B `_backfilled_*` markers are NOT removed. A startup migration sets `lifecycle_state = "OPEN"` for every incident lacking it.

### 1.7 · UI surface changes (Build stage · NOT implemented yet)

* `ViewIncident.jsx` adds a "Lifecycle" panel with 4 buttons gated by role + current state:
  * `[Mark Under Investigation]` · `[Mark Pending Review]` · `[Mark Closed]` · `[Reopen Incident]`
* Banner says: *"This incident is currently <STATE>. Last changed by <actor> on <date>."*
* When closure blocked: *"Closing requires <list of unmet conditions>"*
* History tab: scrollable state-event timeline

### 1.8 · Accountability / Command Center alignment (Phase 1B-coordinated)

* Accountability projection's `_status_for_incident` is updated to **prefer** `lifecycle_state` when set, falling back to existing derivation when not. (Read-shim — no behavioral change for unmigrated records.)
* Command Center's hardcoded label strings are replaced with `lifecycle_state` rendering — `"Open · unresolved" → "OPEN — Active"`, `"Open · OSHA notification clock active" → "OPEN — OSHA notification clock active"`.

---

## 2 · Daily Report Office Review

### 2.1 · Source of friction
* `daily_reports` has no status field. Office cannot mark a DR "reviewed". Time Verification + Payroll Variance build atop unverified data.

### 2.2 · State map

```
OPEN ("Submitted; office has not yet reviewed")
  └─→ IN_PROGRESS  ("PM is reviewing")
       └─→ PENDING_REVIEW  ("PM finished; awaiting Admin/PM-Lead approval — OPTIONAL; default skip")
       └─→ CLOSED  ("Approved — reflects in Time Verification / Payroll Variance as canonical")
       └─→ OPEN    ("Returned to Field for correction"; reason required — re-submission re-files the same `id` with status=OPEN)
       
CLOSED
  └─→ IN_PROGRESS  ("Reopen for re-review"; reason required)
```

### 2.3 · Closure conditions

`IN_PROGRESS → CLOSED` requires:
* Closer role ∈ {PM (assigned to job), Admin, Super-Admin}
* PM affirms (checkbox audit): "Hours align with crew on site this date"
* If the DR has `accident_or_incident_today == "Yes"`: a linked incident must exist (already enforced at create-time; re-checked at closure)

### 2.4 · Auto-transitions

* None. Office review is a deliberate human action.

### 2.5 · Required new endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/daily-reports/{id}/transition` | universal transition |
| `GET` | `/api/daily-reports/{id}/state-events` | per-doc history |

### 2.6 · Schema additions (daily_reports)

```
lifecycle_state             str       default "OPEN"
state_changed_at            ISO ts
state_changed_by            str
approved_at                 ISO ts    set on CLOSED
approved_by                 str
return_reason               str       set on CLOSED→OPEN return
```

### 2.7 · UI surface changes

* `ViewDailyReport.jsx` adds a "Review Status" panel with role-gated buttons:
  * `[Mark Under Review]` · `[Approve & Close]` · `[Return to Field]` · `[Reopen]`
* Time Verification + Payroll Variance only consume rows where `lifecycle_state == "CLOSED"` (Phase 1B).

---

## 3 · Payroll Variance Finalization

### 3.1 · Source of friction
* Sandy decides every row but the batch never closes; old batches accumulate.

### 3.2 · State map (per batch)

```
OPEN ("Upload landed; rows imported; no decisions yet")
  └─→ IN_PROGRESS ("≥1 row has a decision recorded; HR working through batch")
        └─→ PENDING_REVIEW ("All rows decided; awaiting batch-level finalize")  [auto]
              └─→ CLOSED ("Sandy clicks Finalize Batch"; batch reflected as canonical for the week)
              └─→ IN_PROGRESS ("Reopen — found a row to re-decide"; reason required)
              
CLOSED
  └─→ IN_PROGRESS ("Reopen batch"; reason required)
```

### 3.3 · Closure conditions

`PENDING_REVIEW → CLOSED` requires:
* Closer role ∈ {HR, Admin, Super-Admin}
* Sandy affirms (checkbox): "All variance rows have been reconciled or escalated to PM"
* No row left with decision == null

### 3.4 · Auto-transitions

* `OPEN → IN_PROGRESS` on first row decision
* `IN_PROGRESS → PENDING_REVIEW` when all rows have a decision

### 3.5 · Required new endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/hr/payroll-variance/batches/{id}/transition` | universal transition (HR · Admin only) |
| `GET` | `/api/hr/payroll-variance/batches/{id}/state-events` | per-batch history |

### 3.6 · Schema additions (payroll_variance_batches)

```
lifecycle_state             str       default "OPEN"
state_changed_at            ISO ts
state_changed_by            str       (HR userid)
finalized_at                ISO ts
finalized_by                str
finalization_attestation    str       Sandy's reconciliation comment
```

### 3.7 · UI changes

* `HrPayrollVariance.jsx` shows batch-level Lifecycle pill (OPEN/IN_PROGRESS/PENDING_REVIEW/CLOSED).
* When `PENDING_REVIEW`: `[Finalize Batch]` button appears with a confirmation modal.
* Closed batches move to an "Archive" tab.

---

## 4 · QA/QC Deficiency Follow-Up

### 4.1 · Source of friction
* Deficiencies are stored as a text array; no per-item state; PM cannot mark them resolved.

### 4.2 · Schema redesign (read-shim)

Current: `qaqc_inspections.deficiencies: [str, str, ...]`
Build-stage: `qaqc_inspections.deficiencies: [{ id, text, lifecycle_state, assigned_to?, resolved_at?, resolved_by?, resolution_notes?}, ...]`

Read-shim: existing text-array records are migrated on read to objects with `lifecycle_state="OPEN"` and stable `id` derived from `(inspection_id, index)`.

### 4.3 · State map · two levels

**Inspection level:**
```
OPEN
  └─→ IN_PROGRESS  ("PM reviewing")
        └─→ PENDING_REVIEW  ("All deficiencies have a non-OPEN state")  [auto]
              └─→ CLOSED  ("PM affirms remediation complete")
              └─→ IN_PROGRESS  ("Reopen — found a deficiency to revisit")
CLOSED
  └─→ IN_PROGRESS  ("Reopen inspection"; reason required)
```

**Deficiency level (within inspection):**
```
OPEN → IN_PROGRESS (assigned to crew) → PENDING_REVIEW (crew claims resolved) → CLOSED (PM verified)
                                                                                 └─→ IN_PROGRESS (PM re-opens)
```

### 4.4 · Closure conditions

* Inspection `PENDING_REVIEW → CLOSED`: every deficiency in `CLOSED`
* Deficiency `PENDING_REVIEW → CLOSED`: PM/Admin attests "verified resolved"
* Reopen deficiency or inspection: reason required

### 4.5 · Required new endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/qaqc-inspections/{id}/transition` | inspection-level |
| `POST` | `/api/qaqc-inspections/{id}/deficiencies/{def_id}/transition` | deficiency-level |
| `GET` | `/api/qaqc-inspections/{id}/state-events` | combined history |

### 4.6 · UI changes

* `ViewQaqcInspection.jsx`: per-deficiency action menu; assign to crew · mark resolved · verify · reopen
* Inspection-level Lifecycle banner with `[Mark Closed]` button when all deficiencies CLOSED

---

## 5 · Site Inspection (Safety Walk-Around) Follow-Up

### 5.1 · Source of friction
* Identical pattern to QA/QC — no per-finding state; no follow-up surface.

### 5.2 · Schema redesign

Current: `inspections` model with finding fields per area
Build-stage: parallel `inspection_findings` array (objects) per inspection — same shape as QA/QC deficiencies:

```
findings: [
  { id, category, severity, description,
    lifecycle_state, assigned_to?, resolved_at?, resolved_by?, resolution_notes? }
]
```

### 5.3 · State map (same as QA/QC; inspection-level + finding-level)

(See §4.3 — identical structure with `inspection_findings` instead of `deficiencies`.)

### 5.4 · Closure conditions

* Inspection `PENDING_REVIEW → CLOSED`: every finding in `CLOSED`
* Finding `PENDING_REVIEW → CLOSED`: Safety officer attests verified

### 5.5 · Required new endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/inspections/{id}/transition` | inspection-level |
| `POST` | `/api/inspections/{id}/findings/{finding_id}/transition` | finding-level |
| `GET` | `/api/inspections/{id}/state-events` | combined history |

---

---

## 5.5 · JHA Acknowledgement Ledger (OC-005 · ELEVATED iter449)

### 5.5.1 · Source of friction
* JHA library exists (`/jha` · iter445 surfaced in FL Hub) but **no per-crew per-day acknowledgement ledger exists**. OSHA 1926.21(b)(2) general-duty exposure: employer must "instruct each employee in the recognition and avoidance of unsafe conditions" — JHA acknowledgement is the documentation of that instruction.
* ~500 crew acknowledgements/week occur verbally without platform record.

### 5.5.2 · NOT a state-machine workflow
OC-005 is **single-event** (one acknowledgement record per crew member per JHA per shift). No `OPEN/IN_PROGRESS/CLOSED` lifecycle. Each acknowledgement is born as a permanent audit record with no transitions.

### 5.5.3 · Data model

New collection `jha_acknowledgements`:

```
{
  _id: ObjectId,
  id: str (uuid),
  jha_id: str           # FK to jhas
  jha_doc_id: str       # JHA-YYYY-NNNNN (human-readable)
  job_id: str           # FK to jobs_master
  job_doc_id: str
  shift_date: str (YYYY-MM-DD)
  shift: "AM" | "PM" | "DAY" | "NIGHT" | null
  crew_label: str       # free-text crew identifier (e.g., "Crew 3 - Paving North")
  acknowledged_by: {
    employee_id: str | null,    # if known/looked up
    display_name: str,           # required free-text
    role: "operator" | "laborer" | "foreman" | "other"
  }
  signature: str          # base64 PNG signature OR "verbal_attested" if FL attests verbally
  attested_by: {          # if signature == "verbal_attested"
    user_id: str,
    role: "fl" | "safety" | "admin",
    display_name: str
  } | null
  acknowledged_at: ISO ts
  created_at: ISO ts
  ip_address: str | null
  user_agent: str | null
  ttl_at: ISO ts (acknowledged_at + 7y)   # OSHA retention
}
```

Indexes:
* `{jha_id: 1, shift_date: -1}` — per-JHA per-day
* `{job_id: 1, shift_date: -1}` — per-job per-day rollup
* `{acknowledged_at: -1}` — recent
* TTL: `{ttl_at: 1}, expireAfterSeconds: 0`

### 5.5.4 · States

None. Each row is immutable on write. The ONLY mutation is a soft-delete (`deleted_at`, `deleted_by`, `deletion_reason`) by Safety / Admin / Super-Admin for correction (e.g., wrong crew tagged). Deletion is an audit event in `audit_events`.

### 5.5.5 · Endpoints (Build stage)

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/jhas/{jha_id}/acknowledgements` | submit single ack (signature OR verbal attestation) | FL · Safety · Admin · public-token (signed) |
| `GET` | `/api/jhas/{jha_id}/acknowledgements` | per-JHA ack list (with shift_date filter) | FL · Safety · PM (job-scoped) · Admin |
| `GET` | `/api/jobs/{job_id}/jha-acknowledgements` | per-job daily acknowledgement summary | Same roles |
| `GET` | `/api/admin/jha-acknowledgements` | global admin view with date/job/jha filters | Admin · Safety |
| `DELETE` | `/api/jhas/{jha_id}/acknowledgements/{ack_id}` | soft-delete with `deletion_reason` | Safety · Admin · Super-Admin |
| `GET` | `/api/jha-acknowledgements/coverage` | daily coverage report (jobs ran × jobs with ack) | Safety · Admin |

### 5.5.6 · UI changes (Build stage)

* `JhaList.jsx` (`/jha`): per-row "Acknowledge JHA" button (FL · Safety) opens signature-capture modal
* `FieldLeadershipHub.jsx` (iter445): JHA tile shows today's coverage badge ("3 of 4 active crews acknowledged today")
* New page `/safety/jha-acknowledgements` (Safety · Admin): coverage dashboard + drill into per-JHA ledger
* Public submission flow: crew member scans QR → signs → acknowledgement recorded (separate token-based route TBD)

### 5.5.7 · Notifications
* If a JHA is created for a job and **no acknowledgement is recorded within 4 hours** of job start: Safety + PM receive a notification (existing `notifications` collection · new `kind=jha_ack_missing`).
* Coverage gap notifications batched daily at 18:00 UTC for unacknowledged JHAs of the current shift.

### 5.5.8 · Audit trail
Every ack row IS the audit. Deletions write to `audit_events` with `kind="jha_ack_deleted"`. No `workflow_state_events` involvement (no states to transition).

### 5.5.9 · Closure model
**There is no closure.** A JHA acknowledgement is a one-shot evidence record. The OSHA-required documentation exists from the moment the row is written. Daily/weekly/monthly OSHA exports filter by `acknowledged_at` window.

### 5.5.10 · Accountability + Command Center impact
* Accountability projection: new source `JHA_ACK_MISSING` (Job-day with active crew but no ack) — owner = PM
* Command Center: new rule `SAF-JHA-ACK-MISSING` (job-day with no ack by 10:00 local) — severity Yellow

---

## 6 · Common cross-workflow specifications

### 6.1 · `workflow_state_events` collection

Single collection serving all 5 workflows.

```
{
  _id: ObjectId,
  workflow_type: "incident" | "daily_report" | "payroll_variance_batch" | "qaqc_inspection" | "qaqc_deficiency" | "site_inspection" | "site_finding",
  doc_id: str,                       # the workflow record's id
  parent_doc_id: str | null,         # for deficiency/finding child records
  from_state: "OPEN" | ...,
  to_state: "OPEN" | "IN_PROGRESS" | "PENDING_REVIEW" | "PENDING_CLOSURE" | "CLOSED",
  actor_user_id: str | null,
  actor_role: "safety" | "admin" | "hr" | "pm" | "super-admin",
  actor_display_name: str,
  reason: str | null,                # required on REOPEN and some REJECT paths
  metadata: dict,                    # e.g. {"osha_attested": True} or {"closer_attestation": "..."}
  occurred_at: ISO ts,
  ttl_at: ISO ts (occurred_at + 7y)  # OSHA + IRS records hold 7 years
}
```

Indexes:
* `{workflow_type: 1, doc_id: 1, occurred_at: -1}` — per-doc timeline
* `{workflow_type: 1, to_state: 1, occurred_at: -1}` — admin cross-cutting
* `{occurred_at: -1}` — global recent
* TTL: `{ttl_at: 1}, expireAfterSeconds: 0`

### 6.2 · Read-shim contract (during Phase 1B migration)

Backend exposes a helper `get_lifecycle_state(workflow_type, doc)` that returns:
* The doc's `lifecycle_state` field if set, OR
* The legacy-derived state (per-workflow logic preserved):
  * Incidents: `corrected_on_site + linked CAPA` → maps to one of 5 canonical states
  * Daily Reports: returns `OPEN` (no legacy producer)
  * Payroll Variance: derives from row decision counts
  * QA/QC: returns `OPEN` (no legacy producer)
  * Inspections: returns `OPEN` (no legacy producer)

This ensures every consumer reads a non-null canonical state during migration.

### 6.3 · Frontend deep-link contract

Each workflow's detail page renders a `<LifecyclePanel workflow="{type}" docId="{id}" />` component:
* Reads current state from `get_lifecycle_state` helper
* Renders state pill + last-changed metadata
* Renders role-gated transition buttons per the role matrix
* Renders history drawer on click

### 6.4 · Telemetry

Every transition event is also emitted to `audit_events` for cross-cutting search. This is in addition to `workflow_state_events` (which is the canonical source).

---

## 7 · Out-of-scope clarifications (Phase 1A explicit boundaries)

The following are NOT part of Phase 1A. They appear in subsequent phases of the PCP:

| Out of Phase 1A | Phase that addresses it |
|---|---|
| Canonicalizing OTHER workflows' status (CAPA · Asset Transfers · Tasks · Fleet Defects · etc.) | Phase 1B |
| Eliminating PPE Return / Photo Janitor / JHA Acknowledgement placeholders | Phase 2 |
| Employee Onboarding/Offboarding multi-step checklist | Phase 3 |
| Asset & Equipment lifecycle completion | Phase 4 |
| Re-running the Operational Completeness Audit | Phase 9 |
| White Label / ForgedOps Ops Center work | NEVER — explicitly frozen by directive |

---

## 8 · Design risks (called out for operator certification)

| Risk | Severity | Mitigation |
|---|---|---|
| Migration of existing incidents to `lifecycle_state` could mis-categorize legacy "open" incidents that are operationally complete | 🟡 | Read-shim falls back to `corrected_on_site + linked CAPA` derivation; Safety officer reviews + manually closes incidents that should be closed |
| QA/QC deficiency reshape (text array → object array) requires data migration | 🟡 | Idempotent read-shim: legacy strings translated on read; write path emits new shape; one-shot script can migrate at any future point |
| Closure attestation checkbox is forgeable by admin (could click without actually verifying) | 🟢 | Standard for any audit-trail system; the attestation is the closer's signature, not the platform's |
| OSHA-recordable closure gate could block closure indefinitely if OSHA forms aren't filed | 🟡 | Gate is overridable by Super-Admin with explicit reason; reason recorded |
| New endpoints add ~12 routes — backend surface grows | 🟢 | Additive only; existing routes unchanged |
| Frontend Lifecycle panel may regress existing detail page render | 🟢 | Component scoped; tested independently before integration |
| Auto-transition logic (e.g., DR batch's `PENDING_REVIEW` on row complete) needs careful idempotency | 🟡 | Auto-transitions are gated on actual state read + write-once guard |

---

## 9 · Open design questions for operator certification

1. **OSHA closure gate severity:** Should `Fatality` / `Lost Time` / `Hospitalization` incidents block closure entirely until OSHA 301 form is linked, or only require attestation? *Design default: attestation suffices; Super-Admin can override with reason.*
2. **Reopen authority:** Who can reopen a CLOSED record? *Design default:* same role tier that closed it · or Admin / Super-Admin.
3. **DR return-to-field workflow:** Should `OPEN ← CLOSED return-to-field` notify the original submitter via the existing notifications collection? *Design default: yes · piggybacks on `tasks_notifications.py`.*
4. **Payroll Variance auto-finalize:** Should there be an "all rows decided + 24h elapsed" auto-transition to CLOSED, or always require explicit Sandy finalize? *Design default: always explicit finalize.*
5. **QA/QC + Site Inspection deficiency assignment:** Should "assigned_to" be a free-text crew name or a strict FK to `employees`? *Design default: free-text (matches existing FL form pattern; FK migration deferred to Phase 3).*

These five questions block authorization to Build stage.

---

## 10 · OMEGA discipline

🟢 Design-only · zero code changes · zero deployments · zero new endpoints registered yet.

🛑 **STOP. Awaiting operator certification of this design + answers to §9 before Build stage authorization.**
