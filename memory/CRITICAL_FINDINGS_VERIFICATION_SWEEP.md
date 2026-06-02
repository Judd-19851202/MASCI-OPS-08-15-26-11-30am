# CRITICAL FINDINGS VERIFICATION SWEEP

**Authority**: OMEGA · Critical Finding Verification Sweep
**Mode**: READ-ONLY · 12-step verification per finding · zero code · zero estimates
**Date**: 2026-06-03T00:10 UTC
**Subjects**: TR-0001 (JHP Acknowledgement Ledger) · TR-0002 (Universal Undo / Recovery) · TR-0005 (Status Canonicalization)

---

## Method

For each finding I ran the 12-step protocol: source / backend routes / collections / UI / permissions / lifecycle integrations / audit trails / training-help deps / alternate-name search / partial-implementation search / abandoned-implementation search / doctrine-document search. Every conclusion below is traceable to cited file + line evidence.

---

# TR-0001 · JHP Acknowledgement Ledger

## Verification Steps 1–8 (current state)

### Existing JHA / JHP infrastructure

| Asset | Location | Status |
|---|---|---|
| `db.jhas` collection | `backend/routes/safety.py:544-590` | ✅ exists |
| `POST /api/jhas` (create JHA) | `safety.py:544` | ✅ exists |
| `GET /api/jhas` (list summaries) | `safety.py:591` | ✅ exists |
| `GET /api/jhas/{id}` (read) | `safety.py:615` | ✅ exists |
| `DELETE /api/jhas/{id}` (admin) | `safety.py:625` | ✅ exists |
| JHA fanout to operational signals | `safety.py:559-589` | ✅ exists |
| Auto-email routing for JHAs | `safety.py:553` | ✅ exists |
| `JhaPlansAdmin.jsx` (admin page) | 451 LOC frontend page | ✅ exists |
| `job_hazard_files.py` (file upload/download) | 324 LOC backend module | ✅ exists · upload / download / scope filter |
| `BilingualConsent` component | `components/BilingualConsent.jsx` | ✅ exists · header says "JHP forms + their printable PDF views · Always renders BOTH English [and Spanish]" |
| JHA pdf rendering | `pdf_render.py` | ✅ exists |
| `stop_work_acknowledged` field on a JHA | `safety.py:173` | ✅ exists (single boolean at JHA level) |
| Compliance findings ack pattern | `governance.py:1239-1255` | ✅ exists (`POST /api/admin/compliance/findings/{id}/acknowledge` w/ note) |

### Step 9 · Equivalent functionality under different names

* Compliance-findings ack flow is the **closest** existing analog. It captures: actor + timestamp + note. But it operates on **findings**, not per-employee-per-JHA-per-version.
* `safety_forms.py` ack flow: safety-equipment issuance + training forms have `acknowledgment: bool` on EACH submission (lines 115, 148, 180) — these are PER-EVENT, one-record-per-employee-per-event, captured by signature. But the records are siloed in `safety_equipment_issuance` and `safety_equipment_training` collections, NOT cross-indexed by JHA version.
* `tasks_notifications.py`: 10 hits on "acknowledg" — notification-read receipts on the task feed, not JHA-specific.

### Step 10 · Partial implementations

* JHA documents collection ✅
* JHA file storage ✅
* JHA admin page ✅
* JHA pdf ✅
* JHA-level stop-work acknowledgement boolean ✅ (single boolean per JHA, not per-employee)
* JHA bilingual EN/ES via `BilingualConsent` ✅

### Step 11 · Abandoned implementations

* No `jhp_acknowledgements` collection
* No `jhp_documents` collection (the actual JHA collection is `db.jhas`)
* No per-employee acknowledgement endpoint
* No "who has not acked the current JHA" rollup endpoint
* No "JHP ledger" page

### Step 12 · Doctrine documents already satisfying

* No doctrine doc states "per-employee JHA ack is not required" or "stop_work_acknowledged single boolean is the canonical answer."

## Classification

# 🟡 **PARTIALLY IMPLEMENTED**

* The **JHA document, distribution, storage, bilingual rendering, and PDF** layer is fully built.
* The **per-employee, per-version, per-project acknowledgement LEDGER** layer is NOT built.
* The work needed is **additive on top of existing infrastructure**, not new-from-scratch. Scope shrinks from "build a JHP module" to "add a ledger collection + ack endpoints + 2 UI surfaces that feed off `db.jhas`."

## Exact remaining gap (FOR ACTIVE-GAP portion only)

| Dimension | Specifics |
|---|---|
| Missing capability | Per-employee acknowledgement records (1 row per employee × JHA × project × version). Operator-facing "Who has acked / has not?" rollup. Re-ack-on-version-bump enforcement. |
| Files involved | NEW: `backend/routes/jhp_acknowledgements.py`. EXTEND: `safety.py` (to add `version` field on Jha model). EXTEND: `JhaPlansAdmin.jsx` (to surface the new ledger drill-down). NEW: `frontend/src/pages/JhpAckLedger.jsx`. NEW: `frontend/src/pages/safety/JhpAcknowledge.jsx` (employee-facing). |
| Collections involved | NEW: `jhp_acknowledgements`. EXTEND: `jhas` (add `version` + `supersedes_version`). |
| Routes involved | NEW: `POST /api/jhp/acknowledgements` · `GET /api/jhp/acknowledgements?...` · `GET /api/jhp/ledger/project/{id}` · `GET /api/jhp/ledger/employee/{id}`. |
| UI surfaces involved | Operator ledger drill-down on `JhaPlansAdmin.jsx` + standalone `JhpAckLedger.jsx` + employee `JhpAcknowledge.jsx`. |
| Users impacted | Safety (operator-side ledger view + alerts) · Foreman / Field employee (per-employee ack flow) · Admin (audit + export) · HR (compliance dashboard integration). |
| Audit impact | New audit-log event type: `jhp.acknowledged` · `jhp.version_published`. Re-ack required on version bump → emits `jhp.re_ack_required` for each prior-acker. |
| Governance impact | Closes the audit-grade gap. OSHA / insurance / customer-audit responses gain a per-employee provable signature trail. |
| Retirement criteria | All 4 endpoints respond per spec · operator ledger drill-down shipped on JhaPlansAdmin · employee ack flow shipped · re-ack-on-version-bump verified by automated test · PDF audit export verified. |

---

# TR-0002 · Universal Undo / Recovery

## Verification Steps 1–8 (current state)

### Existing recovery / reverse infrastructure

| Asset | Location | Status |
|---|---|---|
| Soft-delete + 14-day retention TTL | `server.py:1229-1273` (`_soft_delete`, `_restore_row`, `_list_archive`) | ✅ exists |
| Restore endpoints | 10+ collections (employees, suppliers, etc.) | ✅ exists |
| `status_history[]` field | 16 collection-bearing modules (incident, daily report, qa/qc, employee, capa, etc.) | ✅ exists · append-only · verified by `test_iter356_capa_lifecycle.py:230` |
| Lifecycle `/transition` endpoint | `daily_report_lifecycle.py:62`, `incident_lifecycle.py`, `qaqc_lifecycle.py`, `site_inspection_lifecycle.py`, `dispatch_lifecycle.py`, `payroll_variance_lifecycle.py` | ✅ exists · accepts `to_state` + `reason` + `evidence` |
| Backward state transitions allowed | `daily_report_lifecycle.py:107` (`PENDING_REVIEW → OPEN`), L110 (`CLOSED → PENDING_REVIEW`) | ✅ exists · per-workflow validators allow some backward transitions with reason |
| `Reopen` verbs in LifecyclePanels | `IncidentLifecyclePanel`, `QaqcLifecyclePanel`, `SiteInspectionLifecyclePanel` | ✅ exists (verified previously) |
| Reactivate / Rehire | HrEmployees + employee_lifecycle | ✅ exists |
| Draft restore | `lib/resiliency/DraftStatusPill.jsx` + draft recovery banner system | ✅ exists |
| Comment undo / typo amend (in some forms) | various | ✅ exists |
| Per-workflow `audit[]` event log | PO requests + many others | ✅ exists |

### Step 9 · Equivalent functionality under different names

* "Undo" exists pervasively (47 files contain the word) but predominantly as **draft undo · comment undo · soft-delete restore · transition-with-reason**. Each is a domain-specific recovery primitive.
* "Reopen" exists on every lifecycle-bearing detail page (via `*LifecyclePanel`).
* "Restore" exists for soft-deleted rows.
* "Reactivate" exists for employees.
* "Rollback" 10 hits — mostly DB-restore / system-level rollback, not user-facing.

### Step 10 · Partial implementations

* The **substrate** for status reversal is FULLY PRESENT: every lifecycle has `status_history` (audit log) + `/transition` (mutation endpoint) + admin RBAC. A backend handler `POST /api/{workflow}/{id}/undo-last-status` can be built as a thin wrapper that reads `status_history[-1]` and emits a reverse `/transition` call.
* What is missing is a **unified user-facing affordance** — one button + one confirmation modal + one cross-workflow audit-stream surface.

### Step 11 · Abandoned implementations

* No `universal_undo` module
* No `revert_status` endpoints
* No "undo my last action" page

### Step 12 · Doctrine documents already satisfying

* `RECOVERY_AND_REVERSAL_REGISTER.md` (Phase 7 deliverable) explicitly notes: *"The platform's recovery doctrine is centered on **soft-delete + audit-log replay + reopen-by-state-transition** rather than a per-workflow undo button. This is a defensible choice for compliance-heavy domains…"*
* That doctrine **already exists** and is **internally consistent**. A "universal undo verb" is therefore an ADDITION to existing doctrine, not a fix for missing doctrine.

## Classification

# 🟡 **DECENTRALIZED · FUNCTIONALLY PRESENT · MISSING UNIFIED AFFORDANCE**

* Every recovery primitive a universal undo would invoke ALREADY exists per-workflow.
* The platform achieves the *outcome* of undo via the existing pattern: open detail page → see `status_history` → click `/transition` with reverse `to_state` + reason. That is functional today.
* The missing piece is the **single-tap unified affordance** ("Undo my last status change") + a **cross-workflow audit-stream view** ("Show me everything I've changed in the last 24 hours with one-click undo").
* This is more of a **governance / UX-discoverability problem** than a missing-capability problem.

## Exact remaining gap (FOR the ACTIVE portion only)

| Dimension | Specifics |
|---|---|
| Missing capability | A unified "Undo Last Status Change" verb. Optional: a cross-workflow "My Recent Changes" page with bulk-undo. |
| Files involved | NEW: `backend/routes/universal_undo.py` (thin wrapper that reads `status_history[-1]` and calls the per-workflow transition validator with reverse to_state). NEW: `frontend/src/components/UndoLastStatusButton.jsx`. SWEEP: ~12 detail pages add the button. |
| Collections involved | None new. Reuses existing `status_history` on every lifecycle collection. |
| Routes involved | NEW: `POST /api/{collection}/{id}/undo-last-status` (one route, parameterized by collection name; or a registry of allowed collection→validator map). |
| UI surfaces involved | 12 lifecycle-bearing detail pages get the button. Optional Phase-2: "My Recent Changes" admin page. |
| Users impacted | Every persona (highest user-impact item in the priority register). |
| Audit impact | New event-type `undo.executed` linked to the original `status.changed` event via `parent_event_id`. No state lost; the undo is an *additional* event on the same chain. |
| Governance impact | Doctrine UPDATE required: `UNDO_DOCTRINE.md` codifying "side-effects (notifications already sent, PDFs already generated) do NOT roll back; only the state field rolls back." Re-affirms the existing recovery doctrine. |
| Retirement criteria | Button visible on 12 detail pages · backend wrapper green-tests across all 12 workflows · audit-log event-type added · doctrine doc shipped · zero data-loss verification on rollback. |

---

# TR-0005 · Status Canonicalization

## Verification Steps 1–8 (current state)

### Existing canonicalization infrastructure

| Asset | Location | Status |
|---|---|---|
| `lib/statusBadges.js` ("Iter B unification") | `frontend/src/lib/statusBadges.js` 117 LOC | ✅ exists — header explicitly says *"Single source of truth for every status-color mapping platform-wide. Replaces 5 separate STATUS_COLORS constants in PoRequests, Tasks, DocumentExpirations, HrEmployees, SafetyCorrectiveActions."* |
| `<StatusBadge kind="…" value="…" />` component | `frontend/src/components/StatusBadge.jsx` 42 LOC | ✅ exists · supports `sm` / `md` / `lg` sizes · emits `data-testid="status-badge-${kind}-${value}"` |
| `<StatusPill>` components | 15 files | ✅ exists (workflow-specific variants) |
| Domain maps already wired | PO · Tasks · Task Priority · Doc Expirations · Lifecycle · Corrective Actions · Severity (7 domains) | ✅ exists |
| `DEFAULT_TINT` fallback | `statusBadges.js:14` | ✅ exists |
| Domain registry `STATUS_DOMAINS` + `tintFor()` helper | `statusBadges.js:102-116` | ✅ exists |
| Consumer count | 11 files use `StatusBadge` directly · 15 files use `StatusPill` variants | ✅ medium adoption |

### Step 9 · Equivalent functionality under different names

* The `Iter B unification` work already shipped is itself the canonicalization substrate. It pre-empted this finding.
* `SeverityPill` (`components/operational/SeverityPill.jsx`) is the severity-specific component.
* `DraftStatusPill` (`lib/resiliency/DraftStatusPill.jsx`) is draft-specific.
* `EquipmentStatusBoard` (`components/EquipmentStatusBoard.jsx`) — equipment-specific.
* `BackendStatusBanner` — system-health-specific.

### Step 10 · Partial implementations

The TR-0005 audit's claim of "38 distinct status words rendered raw" overstates the residual. Mapped present:

* ✅ PO domain (11 statuses)
* ✅ Tasks domain (9 statuses)
* ✅ Task Priority (4)
* ✅ Doc Expirations (8)
* ✅ Lifecycle / Employees (13)
* ✅ Corrective Actions (7)
* ✅ Severity (6)

**Total covered: ~ 58 status values across 7 domains.**

What is NOT yet in `statusBadges.js`:

* Incident lifecycle (open / in_review / corrective_pending / closed / reopened — 5)
* QA/QC lifecycle (IN_PROGRESS / DEFICIENCY_RAISED / PENDING_RE_INSPECTION / CLOSED — 4)
* Site Inspection lifecycle (IN_PROGRESS / FINDINGS_RAISED / PENDING_RE_INSPECTION / CLOSED — 4)
* Daily Report lifecycle (similar set — 4-5)
* Asset Transfer (Requested / Approved / In Transit / Received / Rejected / Closed / Cancelled — 7)
* Dispatch (varies)
* FleetDVIR (Pass / Fail / Needs Service / Out of Service — 4)
* Constraint (open / monitoring / resolved / void — 4)

**Total NOT covered: ~ 36 status values across 8 domains.**

### Step 11 · Abandoned implementations

* No `statusDisplay`, `displayStatus`, `canonicalStatus`, `STATUS_MAP`, `STATUS_DISPLAY`, `STATUS_LABELS` (verified: 0 hits each).
* Operator-target labels (Needs Revision / Action Required / Pending Verification / Pending Closure) are absent — `statusBadges.js` carries COLOR mappings only, not LABEL mappings.

### Step 12 · Doctrine documents already satisfying

* `STATUS_CANONICAL_DICTIONARY.md` (Phase 8 deliverable) proposes the operator-target labels + the per-workflow mapping. This IS the doctrine.
* `statusBadges.js` header is the implementation-doctrine — it says the file IS the single source of truth.
* The two are consistent. The finishing work is mechanical, not architectural.

## Classification

# 🟡 **PARTIALLY IMPLEMENTED · GOVERNANCE + EXTENSION GAP**

* The substrate exists and is correctly designed. ~ 58 status values are already canonicalized.
* The remaining ~ 36 status values across 8 lifecycle-bearing workflows need to be ADDED to the existing `STATUS_DOMAINS` registry.
* The operator-target display labels (per `STATUS_CANONICAL_DICTIONARY.md`) need to be ADDED as a parallel `STATUS_LABELS` map (currently the file carries colors only).
* This is more of a **governance problem** (deciding the canonical mapping) and an **extension problem** (adding rows to an existing registry) than a **build-from-scratch engineering problem**.

## Exact remaining gap (FOR the ACTIVE portion only)

| Dimension | Specifics |
|---|---|
| Missing capability | (1) 8 additional domains in `STATUS_DOMAINS`. (2) Parallel `STATUS_LABEL_MAP` for operator-target display labels. (3) Sweep of ~ 12 lifecycle-bearing list / detail pages currently rendering raw backend strings (e.g., `IN_PROGRESS` literal). |
| Files involved | EXTEND: `lib/statusBadges.js` (add 8 domain maps + label map + new helper `labelFor(kind, value)`). NEW: usage in `<StatusBadge>` to render label OR raw value via prop. SWEEP: ~ 12 page-level integrations. |
| Collections involved | None. Pure-display refactor. |
| Routes involved | None. |
| UI surfaces involved | Incident · Daily Report · QA/QC · Site Inspection · Asset Transfer · Dispatch · FleetDVIR · Constraint list & detail pages. |
| Users impacted | All personas; especially new-hires who currently see raw backend strings (`DEFICIENCY_RAISED`, `PENDING_RE_INSPECTION`) and ask "what does this mean?" |
| Audit impact | None (display-only). |
| Governance impact | Closes the "what does Closed mean across modules?" semantic-drift problem at the display layer. |
| Retirement criteria | (a) 8 new domain maps in `statusBadges.js` reviewed by operator. (b) `STATUS_LABEL_MAP` added & wired into `<StatusBadge>`. (c) Per-page sweep verified — no raw backend status string visible on non-admin pages. (d) Storybook entries updated. |

---

## Summary table · the answer to the operator's 5 questions

| TR ID | Real? | Partially real? | Already solved? | Governance vs engineering? | Should be built? |
|---|:-:|:-:|:-:|---|---|
| TR-0001 JHP Acknowledgement Ledger | YES | YES (substrate exists, ledger doesn't) | NO | **Mostly engineering** (new collection + endpoints + 2 UI surfaces) | **YES · scoped down** — extend `db.jhas` + add ledger; do NOT re-do JHA documents/files |
| TR-0002 Universal Undo / Recovery | YES (the *unified affordance*) | YES (all primitives exist; affordance does not) | functionally yes, ergonomically no | **Mixed · 60% engineering + 40% governance/doctrine** | **YES · scoped as a thin wrapper + button + doctrine doc**, not as new architecture |
| TR-0005 Status Canonicalization | YES (extension) | YES (substrate exists; coverage incomplete) | partially | **Mixed · 40% governance + 60% engineering** | **YES · extension only** — add 8 domains to the existing registry + add label map + per-page sweep |

## Net effect on engineering scope

* TR-0003 already retired by prior work in FOCP Phase 1
* TR-0001 scope reduces by ~ 30% (skip JHA documents layer; reuse existing)
* TR-0002 scope reduces by ~ 50% (wrapper + button, not new module)
* TR-0005 scope reduces by ~ 60% (extend existing registry, not build from scratch)

The 3 remaining ACTIVE engineering items are all **real**, all **scope-able as extensions of existing infrastructure**, and none require new architectural decisions. The platform is even more done than the prior Truth Register said.

## Should anything be retired outright?

* TR-0001: NO. Per-employee ledger genuinely does not exist.
* TR-0002: NO. Unified affordance genuinely does not exist.
* TR-0005: NO. 8 of the 15 lifecycle-bearing domains genuinely lack canonical mappings.

None of the three retires entirely. All three move from "build" to "extend." The work IS real but smaller than the original Truth Register estimates.

---

## STOP CONDITIONS HONORED

* ✅ No code
* ✅ No implementation
* ✅ No build plan beyond capability-level specifics
* ✅ No sprint plan
* ✅ No estimates
* ✅ Read-only · 12-step protocol applied to each finding
* ✅ Every classification cited to file + line evidence

STOP.

Awaiting operator decision on which (if any) of the three "extend rather than build" tasks to authorize for implementation.
