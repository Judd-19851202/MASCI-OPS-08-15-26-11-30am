# TRACK 20.3 · Final Recommendation

## Decision
🟢 **PROMOTE + ADAPTERS.**

## Proposed Track 19.58 scope
### Route
`/safety/incidents/:caseId/thread`

Rationale: keeps the case-ID form used everywhere in the Incident Engine
(`incident_cases.case_id`); mounts inside the Safety portal so the guard
inherits Safety + Admin (existing `RequireSafety` gate).

### Source page / component
- New file: `frontend/src/pages/SafetyIncidentThread.jsx`.
- Import and render: `OperationalThreadPage` (Track 19.55) · `RelationshipGraph` (Track 19.55) · `GuidanceCard` (Track 19.54) · `AttentionChip` / `TrendChip` (Track 19.54).
- Reuses: `SafetyShell` layout wrapper.

### Adapters (pure functions, local to the page)
1. `missionAdapter({ caseDoc, health, snap })` — Case Story, kind, health chip, plain-English "Why:", identity facts (case #, project, severity, type, opened_at, status, next action).
2. `attentionAdapter({ health, oi, capaSummary })` — max 5 items derived from `health.blockers[]` + missing evidence/witness/medical/agency + open CAPA count + OI portfolio-attention rank if the case appears in it.
3. `actionQueueAdapter({ health, tasks, capaSummary, hasExecReport })` — up to 5 next-step suggestions.
4. `timelineAdapter({ events })` — verbatim consumption of `/incident-cases/{id}/timeline`.
5. `relationshipAdapter({ caseDoc, crossLinks })` — Project · PM · Superintendent · Involved employees · Equipment · Witnesses (text-only, not clickable) · Photos / evidence counts.
6. `documentsAdapter({ caseDoc, reportTypes })` — Executive Report deep-link (permission-gated) + available per-type report packages (permission-gated) + evidence file items (Safety+Admin only).
7. `photosAdapter({ evidence })` — filter `evidence` by `kind=image` (Safety+Admin only).
8. `oiProductAdapter({ summary })` — return `safety_morning_digest` product row (unchanged).
9. `historyAdapter({ oiHistory })` — link only (reference to OI history for `safety_morning_digest`).
10. `auditAdapter({ audit })` — verbatim consumption of `/incident-cases/{id}/audit` (Safety+Admin only, honest empty otherwise).

### Certified endpoints consumed (zero new backend)
- `GET /api/incident-cases/{id}` (case core)
- `GET /api/incident-cases/{id}/health`
- `GET /api/incident-cases/{id}/executive-snapshot`
- `GET /api/incident-cases/{id}/timeline`
- `GET /api/incident-cases/{id}/evidence`
- `GET /api/incident-cases/{id}/witnesses`
- `GET /api/incident-cases/{id}/tasks`
- `GET /api/incident-cases/{id}/audit`
- `GET /api/incident-cases/{id}/executive-intelligence`
- `GET /api/incident-reports/types`
- `GET /api/operational-intelligence/summary` → `safety_morning_digest` product
- `GET /api/corrective-actions?incident_case_id={id}` (existing filter)

Optional (permission-gated):
- `GET /api/incident-cases/{id}/medical` (Safety+Admin only)
- `GET /api/incident-cases/{id}/agency-contacts` (Safety+Admin only)
- `GET /api/incident-cases/{id}/communications` (Safety+Admin only)

### Cross-links (surgical only)
- **From** `SafetyCaseWorkspace` (`data-testid="safety-case-open-thread-link"`) → new thread.
- **From** promoted thread (`data-testid="safety-incident-thread-workspace-link"`) → `SafetyCaseWorkspace`.
- **Optional** (only if obvious): from `IncidentsDashboard` case row → thread. Not from every portal hub.

### Permission model
- Route guarded by the same `RequireSafety` (Safety + Admin) gate as `SafetyCaseWorkspace`.
- Page-level `isSafety() || isAdmin()` guard; otherwise `<AccessDenied attemptedPortal="safety" />`.
- Every restricted section (Medical · Agency · Communications · Audit) renders an honest empty state when the underlying call returns 403 or is not attempted for this role.
- **Zero permission widening. Zero data leak vectors.**

### Redaction model
- Witness names render as text pills, not clickable nodes.
- Medical section shows readiness state ("Medical rows on file: N") only when Safety+Admin; otherwise "Restricted — Safety only".
- Attorney work product references never appear in the thread (they live only on the report package endpoints, which are gated).

### Estimated LOC
- **Backend LOC: 0.**
- **Frontend LOC: ≈ 450** (new `SafetyIncidentThread.jsx` + adapters + tiny cross-link in `SafetyCaseWorkspace.jsx`).
- **Lock test LOC: ≈ 130** in `test_track_19_58_incident_thread_promotion.py`.

### Lock tests required
1. Thread page exists.
2. Route registered at `/safety/incidents/:caseId/thread`.
3. Only certified endpoints consumed.
4. No POST/PUT/PATCH/DELETE anywhere in the page.
5. Uses `OperationalThreadPage` shell.
6. Uses `safety_morning_digest` OI product (no new product).
7. Same `RequireSafety` (or equivalent) auth gate as workspace.
8. Cross-link from workspace to thread present.
9. Cross-link from thread to workspace present.
10. Backend module inventory frozen.
11. OI component inventory frozen.
12. PRD + CHANGELOG updated.
13. Prior track docs preserved.
14. Honest empty state for medical / agency / audit when restricted.

### Risk level
🟢 **LOW.** Same pattern as the successfully-shipped Track 19.56 (Employee) and Track 19.57 (Project) promotions. Zero backend drift. Zero permission widening.

### Deployment impact
🟢 **NONE.** Additive frontend-only. No env, no migration, no schema change.

## Justification for zero backend LOC
Every incident field the shell needs is already served by an existing certified endpoint (see the Universal Thread Fit Matrix). The Guidance / Trend / History slots consume the existing `safety_morning_digest` OI product. Attention derives from the existing `case.health.readiness_level` + `case.severity`. The audit trail already lives at `/incident-cases/{id}/audit`. **There is no honest justification for touching the backend to ship this thread.**
