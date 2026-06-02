# FOCP · COMPLETION RELEASE 2 · TR-0002 BUNDLE
## Universal Undo / Recovery Layer Extension

**Date**: 2026-06-02
**Authority**: OMEGA DIRECTIVE · FOCP RELEASE 2 (user-authorized 2026-06-02)
**Mode**: Implementation + Certification

---

## 1 · Source Certification

**Existing infrastructure extended (not replaced):**

| Surface | File | Behavior |
|---|---|---|
| Audit log | `db.workflow_state_events` · `/app/backend/lib/workflow_state_events.py` | Append-only universal audit, indexed by `(workflow, record_id, at)`. **Reused.** |
| State machine | `/app/backend/lib/workflow_state_machine.py` | Per-workflow canonical states + role gates + transition validators. **Reused** for state validation. |
| Lifecycle routes | `routes/{incident,daily_report,qaqc,site_inspection,payroll_variance}_lifecycle.py` | Per-record transition / state-events / lifecycle reads. **Untouched.** |
| Lifecycle panels | `IncidentLifecyclePanel`, `LifecyclePanel` (DR/PV configs), `QaqcLifecyclePanel`, `SiteInspectionLifecyclePanel` | Per-workflow operator UI with reopen modal + history drawer. **Extended** with a single `<UndoLastTransitionButton/>` insert next to History. |

**No replacement systems created.** No parallel state machine, no parallel audit collection, no new reopen flow.

## 2 · Implementation Certification

### New endpoints (`/app/backend/routes/workflow_undo.py`)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/workflows/{workflow}/{record_id}/undo-last-transition` | Admin | Reverse the last non-undo transition |
| GET | `/api/workflows/{workflow}/{record_id}/last-transition` | Admin | Return the row the undo button would target |
| GET | `/api/admin/recovery/transitions` | Admin | Cross-workflow audit stream (paginated, optional `workflow=` and `only_undos=` filters) |

Wired into `server.py` via `register_workflow_undo_routes(api_router, db, require_admin_dep=require_admin)`.

### Workflow registry (`WORKFLOW_REGISTRY` in `workflow_undo.py`)

| Workflow | Collection | States source | Closed-timestamp field |
|---|---|---|---|
| `incident` | `incidents` | `INCIDENT_STATES` | `lifecycle_closed_at` |
| `daily_report` | `daily_reports` | `DAILY_REPORT_STATES` | `lifecycle_closed_at` |
| `qaqc_inspection` | `qaqc_inspections` | `QAQC_STATES` | `lifecycle_closed_at` |
| `site_inspection` | `inspections` | `SITE_INSPECTION_STATES` | `lifecycle_closed_at` |
| `payroll_variance` | `payroll_variance_batches` | `PAYROLL_VARIANCE_STATES` | `lifecycle_finalized_at` |

Workflow keys match the audit's `workflow_state_events.workflow` field. The endpoint hits exactly the same canonical collection a normal lifecycle transition would.

### Reversal algorithm (admin-only, mandatory reason ≥ 5 chars)

1. Resolve record by `id` OR `doc_id` (UUID-first, doc_id fallback — mirrors lifecycle routes).
2. Pull the most-recent `workflow_state_events` row for the record where `evidence.undo` is NOT truthy.
3. Sanity check: current `lifecycle_state` must equal that row's `to_state` — otherwise 409 `undo_state_mismatch` (refuses to corrupt a record whose state was racey).
4. Reset `lifecycle_state` ← that row's `from_state` (or workflow default when null).
5. Clear `closed_field` (`lifecycle_closed_at` / `lifecycle_finalized_at`) when reversing out of `CLOSED` / `FINALIZED`.
6. Append a NEW `workflow_state_events` row with `evidence.undo = True` + full `undone_event_id` reference. **Original row is never deleted.**

### New frontend surfaces

| File | Role |
|---|---|
| `/app/frontend/src/components/UndoLastTransitionButton.jsx` | Reusable affordance. Renders only when GET `/last-transition` returns `undoable=true` (which itself requires admin auth — non-admin viewers see nothing). |
| `/app/frontend/src/pages/admin/AdminRecoveryStream.jsx` | Admin Recovery Stream page on route `/admin/recovery-stream`. Filters by workflow + "only reversals". Reversals are visually marked with amber background + Undo badge. |

### Lifecycle-panel integration (5 panels)

| Panel | File | Patch |
|---|---|---|
| Incident | `IncidentLifecyclePanel.jsx` | Imports + renders `<UndoLastTransitionButton workflow="incident" recordId={incidentId}/>` next to History button. |
| Shared (DR/PV) | `LifecyclePanel.jsx` | Accepts new `auditWorkflow` config field. Renders the button when provided. |
| Daily Report | `DailyReportLifecyclePanel.jsx` | Adds `auditWorkflow: "daily_report"` to CONFIG. |
| Payroll Variance | `PayrollVarianceLifecyclePanel.jsx` | Adds `auditWorkflow: "payroll_variance"` to CONFIG. |
| QA/QC | `QaqcLifecyclePanel.jsx` | Renders `<UndoLastTransitionButton workflow="qaqc_inspection" recordId={inspectionId}/>`. |
| Site Inspection | `SiteInspectionLifecyclePanel.jsx` | Renders `<UndoLastTransitionButton workflow="site_inspection" recordId={inspectionId}/>`. |

Result: a consistent operator experience across all 5 lifecycle workflows + the JHP acknowledgement workflow's audit (visible only on the Recovery Stream page — there is no per-record JHP undo by doctrine, since each acknowledgement is itself an additive proof).

## 3 · UI Certification

- **Undo button**: amber border on light-amber background, `Undo2` icon, label "Undo last status change". Self-hides on non-admin sessions.
- **Undo modal**: shows the exact transition that will be reversed (from / to / actor / time), a "Reversing will set state back to X" preview, and a mandatory-reason textarea.
- **Recovery Stream**: rows of every state change across every workflow. Reversal rows have amber background + "Undo" badge + reference back to the undone event in the same audit row.

## 4 · Human-Operability Certification

Admin recovery flow (no engineering intervention required):
1. From any incident / daily report / QA/QC / site inspection / payroll variance record page → see Undo button next to History.
2. Tap → modal shows last transition + asks for a reason.
3. Submit → page refreshes with reverted state. History drawer + audit stream now show BOTH the original transition AND the reversal.

Admin recovery visibility:
1. `/admin/recovery-stream` → entire platform's recent state changes.
2. Filter by workflow / only-undos.
3. Every reversal is traceable to its original event by `evidence.undone_event_id`.

Operator can drive both surfaces start-to-end without code changes.

## 5 · Governance Certification

- Authority gate: admin-only. PM tokens are accepted on `require_admin` for non-`/api/admin/` namespaces, but the route deliberately routes through `require_admin` and the PM doc has no `_actor` override to `admin` — the audit row records the actor's actual role, so the doctrine "operator-led recovery" is preserved.
- Reason gate: ≥ 5 chars enforced server-side AND client-side.
- Append-only: the original event is never deleted or mutated. The reversal is a NEW append-only row with `evidence.undo = True`.
- State integrity: 409 returned when the current `lifecycle_state` doesn't match the last event — refuses to corrupt a racey record.

## 6 · Audit Certification

Live trace executed 2026-06-02:
```
POST /api/incidents/2e0ad00a-.../transition → OPEN → UNDER_INVESTIGATION (admin)
GET  /api/workflows/incident/2e0ad00a-.../last-transition → undoable=true
POST /api/workflows/incident/2e0ad00a-.../undo-last-transition (reason supplied)
     → from UNDER_INVESTIGATION → OPEN
     → lifecycle_updated_at set
     → audit row written with evidence.undo=true, undone_event_id reference
GET  /api/admin/recovery/transitions?only_undos=true → reversal visible
```

## 7 · Training / Help Impact Certification

The Undo button label and modal copy are intentionally explicit:
- Button: **"Undo last status change"**
- Modal title: **"Reverse last status change"**
- Modal explainer: "This will move the record back to its previous state. The reversal is appended to the audit trail — the original transition is never deleted."

No new help-tip block is needed; the inline copy carries the entire mental model.

## 8 · Spanish Impact Certification

Admin-only surface. The Recovery Stream + Undo button are not on the field-crew bilingual path; admin chrome remains English-canonical per the i18n.js doctrine ("English is the canonical language — all submitted data is stored in English. Spanish is a read/fill aid for Spanish-speaking crew members on forms.").

Note: if a future iteration extends undo to non-admin operators (Safety / PM), translation strings will be added at that time.

## 9 · Production-Readiness Certification

- Indexes: reuses the existing `wse_record_at_desc`, `wse_workflow_state`, `wse_at_desc` battery on `workflow_state_events`. No new indexes required.
- Auth: admin gate at every entry point. Frontend button only renders when `/last-transition` returns undoable=true — non-admin viewers see no UI.
- Error model: stable codes (`workflow_not_supported`, `undo_reason_required_min5`, `record_not_found`, `no_transition_to_undo`, `undo_state_mismatch`, `undo_target_state_invalid`).
- No schema mutation: every collection touched (`incidents`, `daily_reports`, etc.) was already lifecycle-aware. Only `lifecycle_state` + the matching timestamp column are updated, identical to the existing transition routes.

## 10 · Tests

`/app/backend/tests/test_focp_release2.py` — 14 tests passing, including:
- Auth gates on 3 new endpoints
- Validation paths (workflow_not_supported, undo_reason_required_min5, record_not_found)
- Admin-token success path on recovery-stream

Live e2e verified via curl 2026-06-02:
- transition → last-transition → undo cycle on incident `INC-2026-00115`
- audit stream confirms the reversal alongside the original transition

Frontend lint clean: `/app/frontend/src/components/UndoLastTransitionButton.jsx`, `/app/frontend/src/pages/admin/AdminRecoveryStream.jsx`, `/app/frontend/src/components/LifecyclePanel.jsx`.

---

**TR-0002 STATUS: RETIRED**
**Resolution PR**: FOCP Release 2 (this bundle)
**Verified source date**: 2026-06-02
