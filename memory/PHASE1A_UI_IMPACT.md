# Phase 1A · UI Impact

**Program:** OMEGA · PCP · Phase 1A · Final Build Package
**Mode:** Design-only
**Date:** 2026-06-01

---

## 1 · Summary

| Operation | Count |
|---|---|
| NEW pages | **2** (`SafetyJhaAcks.jsx` · `PublicJhaAck.jsx`) |
| NEW components | **2** (`LifecyclePanel.jsx` · `JhaAcknowledgePanel.jsx`) |
| MODIFIED pages | **7** (ViewIncident · ViewDailyReport · HrPayrollVariance · ViewQaqcInspection · ViewSiteInspection · JhaList · FieldLeadershipHub) |
| MODIFIED routing | `App.js` — 2 new routes |
| MODIFIED hubs | AdminHub (new tile to jha-acknowledgements coverage) |

---

## 2 · `<LifecyclePanel workflow="..." docId="..." />` shared component

### 2.1 · Surface

```
┌───────────────────────────────────────────────────────────────────┐
│  Lifecycle:  [ OPEN ]   Last changed: never                       │
│              [ IN_PROGRESS ]    by Safety/Leticia · 2026-06-08 09:24│
│                                                                    │
│  [ Mark Under Investigation ]  [ Mark Pending Review ]            │
│  [ Mark Closed ]               [ Reopen Incident ]                │
│                                                                    │
│  ▶ View history (3 events)                                        │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 · Behavior

* Reads workflow_type + doc_id from props
* Fetches `GET /api/<workflow>/{id}/state-events` on mount + after every transition
* Renders state pill colored per canonical state (OPEN=slate, IN_PROGRESS=amber, PENDING_REVIEW=indigo, PENDING_CLOSURE=violet, CLOSED=emerald)
* Buttons gated by `role` from session + workflow's role matrix (PHASE1A_ROLE_MATRIX.md)
* Disabled buttons show tooltip explaining why (e.g., "Cannot close: 2 open CAPAs linked")
* History drawer expands to scrollable timeline · paginated (25 per page) · 7y available

### 2.3 · Props

```jsx
<LifecyclePanel
  workflow="incident"              // workflow_type
  docId={incident.id}              // doc_id
  currentRole="safety"             // session role
  onTransition={(newState) => {    // callback to refresh parent
    refetchIncident();
  }}
  data-testid="lifecycle-panel-incident"
/>
```

### 2.4 · States visible per workflow

| Workflow | States rendered |
|---|---|
| incident | all 5 |
| daily_report | OPEN · IN_PROGRESS · CLOSED (skips PENDING_REVIEW + PENDING_CLOSURE) |
| payroll_variance_batch | OPEN · IN_PROGRESS · PENDING_REVIEW · CLOSED |
| qaqc_inspection | OPEN · IN_PROGRESS · PENDING_REVIEW · CLOSED |
| qaqc_deficiency | OPEN · IN_PROGRESS · PENDING_REVIEW · CLOSED |
| site_inspection | OPEN · IN_PROGRESS · PENDING_REVIEW · CLOSED |
| site_finding | OPEN · IN_PROGRESS · PENDING_REVIEW · CLOSED |

### 2.5 · Confirmation modal patterns

* Forward transitions (e.g., Mark Closed): single confirm with checkbox attestation
* OSHA closure (Incidents with `osha_recordable=Yes`): two-step confirm with mandatory OSHA form link or override reason
* Reopen: mandatory text input for `reason` (>= 10 chars)
* DR return-to-field: mandatory text input for `return_reason` (>= 10 chars)
* All confirmations use existing `<Dialog>` from `/components/ui/dialog`

---

## 3 · Modified pages · per-page diff

### 3.1 · `pages/ViewIncident.jsx` (OC-001)

| Section | Change |
|---|---|
| Top banner | "Lifecycle: <STATE>" replaces existing static "Reported → Linked CAPA(s) → Verified → Closed" copy block. Existing copy block moves to a collapsed "Lifecycle reference" tooltip. |
| Action area | NEW `<LifecyclePanel workflow="incident" .../>` mounted below the metadata header |
| Derived followUpStatus banner | Continues to render (no change) — provides quick visual hint complementary to the canonical state |
| OSHA closure flow | When state = PENDING_REVIEW and `osha_recordable=Yes`, the "Mark Closed" button opens a 2-step modal requiring OSHA attestation or Super-Admin override reason |
| Delete button | Existing — unchanged |

### 3.2 · `pages/ViewDailyReport.jsx` (OC-002)

| Section | Change |
|---|---|
| Top banner | NEW `<LifecyclePanel workflow="daily_report" .../>` |
| Action buttons (PM view) | `[Mark Under Review]` · `[Approve & Close]` · `[Return to Field]` |
| Return-to-Field modal | Text area for `return_reason` · sends notification on submit |
| Audit footer | Existing endpoint augmented to render approver name + timestamp from `approved_at`/`approved_by` |

### 3.3 · `pages/HrPayrollVariance.jsx` (OC-007)

| Section | Change |
|---|---|
| Batch header | NEW `<LifecyclePanel workflow="payroll_variance_batch" .../>` |
| Action toolbar | `[Finalize Batch]` button appears when batch state = PENDING_REVIEW · disabled otherwise with tooltip |
| Finalize modal | Attestation text area + checkbox |
| Closed batches | Move to "Archive" tab (existing pattern from suppliers/jobs) |

### 3.4 · `pages/ViewQaqcInspection.jsx` (OC-003 · may be new file)

A view-detail page exists today for QA/QC; if not, this is created.

| Section | Change |
|---|---|
| Top banner | NEW `<LifecyclePanel workflow="qaqc_inspection" .../>` |
| Deficiency rows | Each row gets a `<LifecyclePanel workflow="qaqc_deficiency" .../>` mini variant + action menu (Assign · Claim · Verify · Reject · Reopen) |
| Auto-transition indicators | When inspection-level auto-transitions trigger, a subtle "(auto)" annotation appears |

### 3.5 · `pages/ViewSiteInspection.jsx` (OC-004)

Identical pattern to QA/QC with Safety-domain roles.

### 3.6 · `pages/JhaList.jsx` (OC-005 entry point)

| Section | Change |
|---|---|
| Row actions | NEW "Acknowledge JHA" button (FL · Safety) opens `<JhaAcknowledgePanel/>` modal |
| Row metadata | Today-coverage badge appears for active JHAs (`5 of 7 crews acked today`) |

### 3.7 · `pages/FieldLeadershipHub.jsx`

| Section | Change |
|---|---|
| JHA tile (existing iter445) | + `<TodayCoverageBadge jha />` showing per-FL-user-scoped JHA acknowledgement coverage for today |

---

## 4 · NEW component · `<JhaAcknowledgePanel/>`

```
┌────────────────────────────────────────────────────────────────────┐
│  Acknowledge JHA: JHA-2026-00042 (Paving — North Lane)             │
│                                                                     │
│  Today's date: 2026-06-08 · Shift: ◯AM  ◯PM  ◯DAY  ◯NIGHT          │
│  Job: T5860 · Crew: [ Crew 3 - Paving North ▾ ]                    │
│                                                                     │
│  Acknowledger: [ name ____________________ ]  Role: [ operator ▾ ] │
│                                                                     │
│  Signature:                                                         │
│  ┌─────────────────────────────────────────────────────┐           │
│  │                                                       │           │
│  │           ✍ sign here                                │           │
│  │                                                       │           │
│  └─────────────────────────────────────────────────────┘           │
│  [ Clear ]                                                          │
│                                                                     │
│  OR  [ I attest verbal acknowledgement on crew's behalf ]           │
│                                                                     │
│  [ Submit Acknowledgement ]   [ Cancel ]                            │
└────────────────────────────────────────────────────────────────────┘
```

* Signature: HTML5 canvas → base64 PNG
* Verbal attestation: FL/Safety/Admin can check the box, swapping signature for `attested_by` payload
* On submit: POST → toast → modal closes → list refreshes

---

## 5 · NEW page · `pages/SafetyJhaAcks.jsx` (`/safety/jha-acknowledgements`)

| Section | Content |
|---|---|
| Header | "JHA Acknowledgement Coverage" + date picker (default: today) |
| Coverage KPIs | Today's coverage % · 7-day rolling · this-month |
| Coverage grid | Rows: active jobs today · Cols: count of crews · cell color: green/yellow/red by ack coverage |
| Per-JHA drill | Clicking a job opens a per-JHA per-crew ack timeline |
| Filters | Job · JHA · date range · crew · acknowledger |
| Soft-delete | per-row trash icon (Safety only) opens reason modal |

Estimated 250 LOC. Mirrors AdminSchedulerRuns.jsx pattern.

---

## 6 · NEW page · `pages/PublicJhaAck.jsx` (`/public/jha-ack/:token`)

For crew members to scan a QR code and submit their own acknowledgement without a portal login.

| Section | Content |
|---|---|
| Token validation | GET against `/api/jhas/public/{token}` → resolves JHA + job |
| Disclosure | "By signing you confirm you have reviewed the JHA for <job> on <date>" |
| Signature pad | Same canvas as `<JhaAcknowledgePanel/>` |
| Submit | POST to public endpoint with token |
| Confirmation | Success page with timestamp + a download link for crew's own copy |

This mirrors the existing public submission token pattern (`/daily/submit?token=...`).

---

## 7 · Routing changes (`App.js`)

```jsx
<Route path="/safety/jha-acknowledgements" element={A(<SafetyJhaAcks/>, ["safety"])} />
<Route path="/public/jha-ack/:token" element={<PublicJhaAck/>} />
```

Two new routes. No existing routes modified.

---

## 8 · AdminHub tile (additive)

A new tile in AdminHub linking to the JHA coverage dashboard:

```jsx
<Link to="/safety/jha-acknowledgements" data-testid="admin-tile-jha-coverage">
  <Card>
    <Shield className="..." />
    <h3>JHA Acknowledgement Coverage</h3>
    <p>OSHA 1926.21(b)(2) compliance ledger · per-job per-day</p>
  </Card>
</Link>
```

---

## 9 · Accessibility + i18n

* All new components ship with `data-testid` per OMEGA contract
* All visible strings flow through `useT()` (English-only initially; Spanish in Phase 3)
* Color-state pills include text labels (not color-only)
* Modal flows include keyboard navigation + ESC dismiss

---

## 10 · Test-id contract

| Element | testid |
|---|---|
| Lifecycle panel root | `lifecycle-panel-<workflow>` |
| Transition button | `lifecycle-btn-<workflow>-<to_state>` |
| History drawer | `lifecycle-history-<workflow>` |
| JHA ack modal root | `jha-ack-modal` |
| JHA ack submit | `jha-ack-submit` |
| JHA ack signature pad | `jha-ack-signature-pad` |
| JHA coverage page | `jha-coverage-page` |
| AdminHub JHA tile | `admin-tile-jha-coverage` |

---

## 11 · OMEGA discipline

🟢 Design-only · 2 new pages · 2 new components · 7 modified pages · 2 new routes · 0 existing routes broken · accessibility + testid contracts respected.

🛑 Continue to `PHASE1A_API_IMPACT.md`.
