# TRACK 20.3 · Executive Audit

## Verdict
🟢 **PROMOTE + ADAPTERS.**

## One-paragraph summary
The Incident Operational Thread is not missing — it is **already present**
across the certified Incident Engine (`/api/incident-cases/*` + `/api/incident-intelligence/*` + `/api/corrective-actions` + `/api/public/near-miss` + `/api/incidents/{id}/lifecycle`). The **Safety Case Workspace** (`SafetyCaseWorkspace.jsx`) already exposes Case Story, Next Action, visual Timeline spine, Blockers, Evidence, Witnesses, Medical, Agency, Communications, Tasks (CAPA), Health, Executive Snapshot, Cross-links, and a deep-link to the boardroom-grade Executive Case Report PDF. Everything the mandate requires is already stored, permissioned, and rendered by certified surfaces. **Track 19.58 must be a frontend-only presentation layer** that wraps these existing endpoints in the Track 19.55 `OperationalThreadPage` shell — identical to how Track 19.56 promoted the Employee Thread and Track 19.57 promoted the Project Thread.

## Certified endpoints identified (zero backend construction required)
### Case core
- `GET /api/incident-cases` · `POST /api/incident-cases` · `GET /api/incident-cases/{case_id}` · `GET /api/incident-cases/vocabulary`
- `GET /api/incident-cases/legacy/{incident_id}` (legacy adapter — bridge for pre-Track-19.15 records)

### Timeline · Audit · State
- `GET /api/incident-cases/{case_id}/timeline`
- `GET /api/incident-cases/{case_id}/audit`
- `POST /api/incident-cases/{case_id}/transitions`
- `PATCH /api/incident-cases/{case_id}/field-block`
- `PATCH /api/incident-cases/{case_id}/safety-block`
- `POST /api/incident-cases/{case_id}/executive-review`
- `POST /api/incidents/{incident_id}/transition`
- `GET /api/incidents/{incident_id}/state-events`
- `GET /api/incidents/{incident_id}/lifecycle`

### Evidence · Witnesses · Medical · Agency · Communications · Tasks
- `POST/GET /api/incident-cases/{case_id}/evidence` · `POST /evidence/{id}/withdraw`
- `POST/GET/PATCH /api/incident-cases/{case_id}/witnesses`
- `POST/GET /api/incident-cases/{case_id}/medical`
- `POST/GET /api/incident-cases/{case_id}/agency-contacts`
- `POST/GET /api/incident-cases/{case_id}/communications`
- `POST/GET/PATCH /api/incident-cases/{case_id}/tasks`

### Health · Executive · Reports · PDFs
- `GET /api/incident-cases/{case_id}/health`
- `GET /api/incident-cases/{case_id}/executive-snapshot`
- `GET /api/incident-cases/{case_id}/executive-intelligence`
- `GET /api/incident-cases/{case_id}/executive-report.pdf`
- `GET /api/incident-cases/{case_id}/presence-score`
- `GET /api/incident-cases/{case_id}/reports/{report_type}`
- `GET /api/incident-cases/{case_id}/reports/{report_type}.pdf`
- `GET /api/incident-reports/types`

### Cross-links
- `POST /api/incident-cases/{case_id}/cross-links`
- `DELETE /api/incident-cases/{case_id}/cross-links/{link_id}`

### Corrective actions
- `POST/GET /api/corrective-actions`
- `POST /api/corrective-actions/{action_id}/verify`
- `POST /api/corrective-actions/{action_id}/cancel`

### Intelligence · Guidance · Digests
- `GET /api/incident-intelligence/home`
- `GET /api/incident-intelligence/root-causes`
- `GET /api/incident-intelligence/corrective-actions`
- `GET /api/incident-intelligence/projects`
- `GET /api/incident-intelligence/fleet`
- `GET /api/incident-intelligence/learning`
- `GET /api/incident-intelligence/heatmap`
- `GET /api/incident-intelligence/brief`
- `GET /api/incident-intelligence/portfolio-attention`
- `GET /api/incident-intelligence/safety-priority`
- `GET /api/incident-intelligence/pm-project-cases`
- `GET /api/incident-intelligence/morning-digest/preview{,.json}`
- `POST /api/incident-intelligence/morning-digest/send`
- `GET/POST /api/incident-intelligence/morning-digest/recipients`
- `PATCH /api/incident-intelligence/morning-digest/recipients/{id}`
- `GET /api/incident-intelligence/digest/weekly{,.pdf}`

### Public / legacy incidents API
- `POST /api/incidents` (public rate-limited)
- `GET /api/incidents{,/{id},.csv}`
- `DELETE /api/incidents/{id}`
- `POST /api/public/near-miss`

## Why PROMOTE + ADAPTERS (and not the others)
- **NOT `PROMOTE EXISTING FOUNDATION` alone** — the Universal Thread shell (Track 19.55) is not what Safety Case Workspace uses; Safety needs a "morning read" view that speaks the same operational language as the Employee, Fleet, and Project Threads.
- **NOT `PROMOTE + EXTEND`** — no new backend logic is required. Every field the shell needs is already available.
- **NOT `BUILD NEW`** — the mandate forbids duplication and every surface already exists.
- **YES `PROMOTE + ADAPTERS`** — a single new frontend page + pure-function adapters mapping the certified case payload into the 10-section shell. Estimated new code: 0 backend LOC + ≈ 450 frontend LOC + 1 lock file. Same delivery pattern as 19.56 (Employee) and 19.57 (Project).
