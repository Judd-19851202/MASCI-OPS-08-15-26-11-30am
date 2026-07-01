# Track 19.15 · 01 · Current System Forensic Audit

## Frontend routes (all `/incidents/*` surfaces)

| Route | Component | Owner | File |
|---|---|---|---|
| `/incidents/new` | NewIncident | field / any auth | `pages/NewIncident.jsx` (1672 lines) |
| `/incidents/submit` | NewIncident (publicMode) | public shift-link | `pages/NewIncident.jsx` |
| `/admin/incidents` | IncidentsDashboard | admin | `pages/IncidentsDashboard.jsx` |
| `/admin/incidents/:id` | ViewIncident | admin | `pages/ViewIncident.jsx` |
| `/pm/incidents` | IncidentsDashboard (PM scope) | PM | shared |
| `/pm/incidents/:id` | ViewIncident (PM scope) | PM | shared |
| `/safety-portal/incidents` | SafetyIncidents | safety | `pages/SafetyIncidents.jsx` |
| `/safety-portal/incidents/:id` | ViewIncident (SF scope) | safety | shared |
| `/incidents` | Navigate → `/admin/incidents` | redirect | App.js:1068 |
| `/incidents/:id` | Redirect helper | redirect | App.js:1069 |
| `/hr/incidents` | HrIncidents | HR | `pages/HrIncidents.jsx` |

## Backend collection

- **`incidents`** — the sole storage collection (server.py:1893 `("incidents", "Incident Reports")`, server.py:5344 shorthand map, and server.py:8717 audit inclusion).
- Additive transition endpoints exist (server.py:2532–2533):
  - `POST /incidents/{id}/transition`
  - `GET /incidents/{id}/state-events`
  - `GET /incidents/{id}/lifecycle`
- Sort-order fallbacks (server.py:5468, 13378, 14948) prefer `incident_date` when present.
- Track 15.47 already backfills `witness_count` (server.py:5480) and `root_cause_categories` (server.py:5482) on read.

## Incident type dropdown (single-select — `incident_type`)

Source: `frontend/src/lib/incidentSchema.js:3-13`

```
Injury / Illness · Near Miss · Property / Equipment Damage ·
Vehicle / Mobile Equipment · Environmental Release / Spill ·
Utility Strike · Public / Third Party · Security · Other
```

## Multi-select classifications (`incident_classifications`)

Source: `incidentSchema.js:20-35` (14 entries) — Track 15.47 G1.
Public Interaction · Verbal Confrontation · Threat · Harassment · Trespass · Property Damage · Physical Contact · Physical Assault · Workplace Violence · Weapon Displayed · Weapon Used · Near-Miss · Media Filmed · Social Media Exposure.

## Attachment kinds (`ATTACHMENT_KINDS`)

photo · video · witness_statement · police_report · medical · insurance · other. Present in schema; **not** surfaced as a first-class field-user experience.

## Severity levels (`SEVERITY_LEVELS`)

near_miss → first_aid → medical → recordable → lost_time → catastrophic (schema lines 58+).

## Fields exposed to the field operator today

Sample subset from `NewIncident.jsx`:
- `project_name`, `project_number`, `location`
- `incident_date`, `incident_time`
- `incident_type` (single-select)
- `severity` (single-select)
- `osha_recordable` (**field-facing — DEFECT**: field is being asked to make an OSHA determination)
- `witness_count`, `witnesses[]`
- `root_cause_categories` (**field-facing — DEFECT**: field asked to do root-cause classification)
- `corrective_actions` (**field-facing — DEFECT**: safety-owned)
- Photos + attachments
- Reporter signature + supervisor signature

## Trust Spine / audit surfaces

- server.py:7231-7232 — reporter_signature + supervisor_signature captured
- server.py:8808 — incidents are included in the historical-record replay
- server.py:8991 — incidents present in the routing exposure map
- server.py:11242 — comment "incidents · CAs" indicates corrective-action linkage exists but is not fully surfaced

## PDF / email / notification routing

- Incidents included in `email_routing.py` and `email_routing_v2.py` (per grep) — routing matrix exists.
- PDF generation exists but its OUTPUT is where the field bug appears (see doc 02).

## Weaknesses identified

1. Single generic form for 9 disparate incident types — no branching.
2. Field operator asked regulatory questions (OSHA recordability, root-cause classification, corrective actions).
3. Utility Strike present but no ticket / locate / potholing / 811 workflow questions.
4. No visible case-lifecycle status on any dashboard.
5. Evidence + witness roles exist in schema but not visually first-class in the field flow.
6. PDF dumps every field regardless of incident type.

## Preservation matrix (must NOT drift)

- Collection name `incidents` — keep
- Every payload key currently written — keep (schema extension in future track can ADD, not RENAME)
- Existing `/incidents/{id}/transition` and lifecycle endpoints — keep, extend
- Historical records — keep 100%
- Reporter + supervisor signatures — keep

**No routes deleted. No fields deleted. Only additive extensions permitted in future tracks.**
