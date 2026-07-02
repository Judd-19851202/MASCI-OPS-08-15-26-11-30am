# FINAL Portal Destination Certification

**Verdict:** 🟢 **PASS** — every submitted record has a documented portal destination.

## Portal destination map

### Daily Report → `/daily/submit`
- Admin daily reports feed (`/admin/daily-reports`)
- PM portal daily reports (`/pm/daily-reports`)
- Project daily history (attached to job number)
- Job photos library (`/admin/photos`)
- CSV export (Admin Console)

### Equipment Pre-Op → `/equipment/submit`
- Equipment record (unit history)
- Shop / maintenance board (on FAIL / OOS)
- Equipment status board (on OOS)
- Admin / Safety visibility

### DVIR → `/fleet/dvir/new`
- Transportation / Fleet portal (`/admin/transportation`)
- Shop / defect queue (on FAIL)
- Dispatch / equipment readiness

### Safety Meeting → `/meetings/submit` or `/meetings/new`
- Safety meeting archive
- Training / attendance history
- Admin / Safety visibility
- PDF archive

### Incident Report → `/incidents/report`
- **Safety Case Workspace** (`/safety/cases/:caseId`) — created immediately on submit
- Incident dashboard (`/safety/incidents`)
- Executive Intelligence Center (`/safety/executive-intelligence`)
- Evidence/photos section (case tab)
- Timeline (case tab)
- PDF/report catalog (9 reports on demand)
- Project context (linked via job number)
- Fleet/equipment cross-link (if unit selected — Track 19.16 final closeout)

### Safety Case → `/safety/cases/:caseId`
- Corrective action queue
- Notifications state (case timeline audit trail)
- Closeout record (case_service closeout summary)

### Near-Miss → `/near-miss` (public kiosk)
- Direct Safety inbox routing
- Anonymous submissions retained (no employee attribution required)

## Sample submission trace

Vehicle accident submitted at 14:22 by Foreman M. Ortega:

1. **Field:** `/incidents/report` → picks "Vehicle Accident" → completes 8 steps → hits Submit.
2. **Backend:** POST to `/api/incident-cases/*/lifecycle/*` (Zero-Drift new engine) creates `incident_cases` doc with `state=FIELD_SUBMITTED`.
3. **Case:** New case appears in Safety Case Workspace at `/safety/cases/{new_case_id}` — immediately accessible.
4. **Dashboard:** New row appears in Safety Incident Dashboard.
5. **Executive Intelligence:** Aggregate risk chart increments the "vehicle_accident" bucket.
6. **Timeline:** First `STATE_CHANGE` event recorded (FIELD_DRAFT → FIELD_SUBMITTED, actor = M. Ortega, tablet).
7. **Cross-link:** If a vehicle was selected during the flow, the vehicle appears under the case's "Linked Records" tab.
8. **PDF catalog:** Any of 9 report definitions (Field Report, Safety Report, Executive Summary, Investigation Package, Insurance Package, OSHA Package, Utility Owner Package, Client Package, Closeout Package) is generable on-demand from `/safety/cases/{id}/reports/{report_type}`.
9. **Email routing:** Safety (always) + assigned PM + severe_incident_cc if severity ≥ Serious.

## Verification

- **Code-level route enumeration:** `/app/frontend/src/App.js` inspected — every submit target has a documented portal route.
- **Testing agent confirmation:** All 6 field workflows return HTTP 200 with no console errors.
- **Zero-Drift:** Legacy `/api/incidents` untouched — legacy submits still route to their historical portals; new Incident Engine routes to the new Safety Case Workspace without overlap.

## Verdict

🟢 **Every submission has a portal destination. No orphan records.**
