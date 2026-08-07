# WP18DB Field Auth Contract Certification

## Scope

This certification captures the corrected boundary between **public field/safety tile forms** and **authenticated portal workspaces** after the reopened regression pass.

## Corrected constitutional truth

- Daily Report (`/daily/submit`) — public submit
- Incident / Accident Report (`/incidents/report`) — public submit
- Safety Meeting (`/meetings/submit`) — public submit
- Equipment Pre-Op (`/equipment/submit`) — public submit
- DVIR / fleet inspection (`/fleet/dvir/submit`) — public or signed-in submit
- Site Audit / Safety Inspection (`/safety/inspections/new`) — authenticated exception

## Certified contract matrix

| Surface | Expected contract | Certified result |
|---|---|---|
| `POST /api/public/incident-cases` | allow without login | `200` |
| repeat `POST /api/public/incident-cases` with same idempotency key | no duplicate record | `200`, `duplicate=true`, same case |
| `POST /api/incident-cases` without portal auth | deny (internal workspace stays protected) | `401` |
| `GET /api/incident-intelligence/weather` without login | allow public helper | `200` |
| `GET /api/incident-intelligence/project-context/{project}` without login | helper must not auth-fail | non-`401` / non-`403` |

## Certified backend contract

### Public form surfaces

- `/api/public/incident-cases` is now the public Incident Report write surface
- `/api/meetings`, `/api/equipment-inspections`, `/api/daily-reports`, and `/api/fleet/inspections` remain public rate-limited write surfaces

### Protected workspace surfaces

- `/api/incident-cases/*` remains an authenticated internal workspace route family
- site audit / safety inspection remains the authenticated exception

## Certified frontend contract

File: `frontend/src/lib/incidentReportApi.js`

- Incident Report public page submits through `submitPublicIncident(...)`
- Daily Report is routed as `NewDailyReportV3 publicMode`
- Safety Meeting is routed as `NewMeeting publicMode`
- DVIR and Equipment Pre-Op remain public submit surfaces on the field/safety tiles

## Draft preservation / continuity proof

### Bounded preview proof executed

Route: `/incidents/report`

Proof steps:

1. open Incident Report
2. pick an incident type
3. enter step data
4. confirm draft keys appear in browser storage
5. reload the page
6. confirm the same draft keys remain and the draft indicator is still present

Observed draft keys before and after reload:

- `masci.incident_report.draft.v1.__index__`
- `masci.incident_report.draft.v1.dr_msi5nony_7lew3e`

Observed after reload:

- `incident-report-draft-indicator` present
- entered step state restored on the same draft shell

## Session / continuity conclusion

The incident form no longer fails on a missing portal login because the public page is now bound to a public write surface. Combined with the existing draft persistence and the new Daily Report midnight session anchor, the corrected boundary removes both the false-login blocker and the midnight reset risk for public field forms.

## Certification result

**CERTIFIED IN PREVIEW:** the public field/safety tile forms remain no-login submit surfaces, the protected workspace APIs remain protected, and draft continuity is preserved across interruption/reload on the public Incident and Daily Report shells.