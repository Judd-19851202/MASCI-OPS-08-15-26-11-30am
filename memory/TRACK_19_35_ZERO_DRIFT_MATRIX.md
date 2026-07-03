# TRACK 19.35 · ZERO-DRIFT MATRIX

**Date:** 2026-07-03 · **Anchor:** `PRODUCTION_READINESS_QUALITY_GATE.md`

Proves Track 19.35 preserved every certified contract, permission, and workflow byte-for-byte.

---

## Zero-Drift Matrix

| Category | Status | Notes |
|---|---|---|
| Schemas (`incident_cases`, `incident_case_audit`, `case_evidence`, `case_witnesses`, `case_medical`, `case_agency`, `case_communications`, `case_tasks`, `case_corrective_actions`) | ✅ unchanged | No collection touched |
| Backend routes (`GET/PATCH /api/incident-cases/{id}` · `GET /api/incident-cases/{id}/health` · executive-snapshot · timeline · evidence · witnesses · medical · agency · communications · tasks · corrective-actions · verify) | ✅ unchanged | 0 backend files modified |
| Payloads | ✅ unchanged | Field Facts + Closeout tabs are display-only · read from existing case document |
| PDFs (`GET /api/safety/cases/{id}/reports/executive.pdf`) | ✅ unchanged | Not touched |
| Emails (`fsi_send_email` incident dispatches) | ✅ unchanged | Not touched |
| Notifications | ✅ unchanged | Not touched |
| Permissions | ✅ unchanged | Safety Case Workspace remains Safety-gated |
| Trust Spine (`incident_case.employee_ids` · `incident_case.equipment_ids` · `incident_case.project_id`) | ✅ unchanged | Not touched |
| Audit events (`incident_case_audit`) | ✅ unchanged | Append-only invariant preserved · no new reasons |
| HR Source-of-Truth | ✅ unchanged | Employee-linkage contract untouched |
| Autosave / drafts | ✅ preserved | Workspace has no drafts flow · new tabs do not introduce one |
| Historical records | ✅ preserved | Immutable field block rendered from same document shape |
| Bilingual engine (`useT()`) | ✅ preserved | Both new tabs use same engine |
| Operational form primitives (`FormShell` · `ProgressRail` · `HelpDrawer` · `SubmitReviewPanel` · `useFormAutosave`) | ✅ preserved | Not touched — workspace does not consume them |
| Incident case architecture (10 existing investigation tabs) | ✅ preserved | Timeline · Evidence · Witnesses · Medical · Agency · RCA · CAPA · Communications · Tasks · Linked all untouched |
| Rollback paths | ✅ preserved | Field Facts + Closeout tabs revertible in-place |
| Session behavior | ✅ preserved | Not touched |
| Case tab state machine (`useState("timeline")` → `useState("field_facts")`) | ⚠️ additive default only | Default landing tab changed but no tab removed · zero state migration |
| Route table | ✅ unchanged | No new routes · no removed routes |
| Track 19.34 Field-vs-Safety grep invariant | ✅ preserved | Track 19.35 touches `SafetyCaseWorkspace.jsx` only — Safety-gated page where investigation vocabulary is allowed |
| CAPA state machine | ✅ unchanged | OPEN → IN_PROGRESS → COMPLETED → VERIFIED preserved |

## File-level change footprint

| Change | File | Type | Lines |
|---|---|---|---|
| `TABS` array — add `field_facts` (first) and `closeout` (last) entries | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | +2 array entries |
| `Lock` icon import | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | +1 token |
| Default tab literal (`"timeline"` → `"field_facts"`) | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | 1-char |
| Field Facts render block | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | +~19 |
| Closeout render block | `frontend/src/pages/SafetyCaseWorkspace.jsx` | EDIT | +~21 |

**Total: 1 file edited · 0 files created · 0 files deleted.**

**Backend footprint: 0 files touched.** Verifiable via `git diff --stat backend/`.

## Payload-level drift check

- `POST /api/incident-cases` request body: unchanged (Track 19.34 already locked this).
- `PATCH /api/incident-cases/{id}` body: unchanged.
- `POST /api/incident-cases/{id}/evidence` body: unchanged.
- `POST /api/incident-cases/{id}/witnesses` body: unchanged.
- `POST /api/incident-cases/{id}/corrective-actions` body: unchanged.
- `GET /api/incident-cases/{id}` response shape: unchanged — Field Facts panel reads existing fields (`incident_type`, `occurred_at`, `reporter_name`, `location`, `summary`, `immediate_actions`).

## Permission drift check

- `/safety/cases/:caseId` remains Safety-token-gated (unchanged).
- No public route affected.
- Executive PDF endpoint remains Safety + Admin-gated (unchanged).

## Legacy route drift check

- `/incidents/new` → `<Navigate to="/incidents/report" replace />` — unchanged.
- `/incidents/submit` → `<Navigate to="/incidents/report" replace />` — unchanged.
- `/incidents/report` renders `<IncidentReport />` — unchanged (Track 19.34 doctrine banner preserved).
- `/safety/cases/:caseId` renders `<SafetyCaseWorkspace />` — unchanged route mapping · same page component with new tabs inside.

## PDF drift check

- ReportLab-generated executive PDF still consumes the same `incident_cases` document shape.
- Layout untouched.
- Track 19.36 (Executive PDF redesign) will handle PDF-side changes · this track does not.

## Email drift check

- `fsi_send_email` dispatch calls for incident submission and case notifications unchanged.
- `email_routing_audit_v2` ledger entries unchanged in shape and reason codes.

## Notification drift check

- In-platform digest at `/notifications` renders incidents from the same source with the same visibility rules.

## Audit event drift check

- `incident_case_audit` append-only invariant preserved.
- No new audit reasons introduced by Track 19.35 (Field Facts + Closeout tabs do not write).

## Rollback drift check

The Field Facts + Closeout tabs are stateless display panels. Removing them (5 in-place edits to `SafetyCaseWorkspace.jsx`) reverts to pre-19.35 behavior with zero side effects. No files to delete. No schema migration.

## Verdict

🟢 **Zero drift.** Track 19.35 is a display-only enhancement of an existing Safety-gated page. Every backend contract, permission surface, PDF, email, and audit invariant is preserved.
