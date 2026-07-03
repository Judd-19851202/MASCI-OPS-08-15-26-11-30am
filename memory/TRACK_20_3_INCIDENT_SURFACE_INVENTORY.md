# TRACK 20.3 · Incident Surface Inventory

## Frontend surfaces (certified · in use)
| Surface                                       | Path                                                      | Portal            | Purpose                                          |
|-----------------------------------------------|-----------------------------------------------------------|-------------------|--------------------------------------------------|
| Incidents Dashboard                           | `/app/frontend/src/pages/IncidentsDashboard.jsx`          | Safety            | List of open / recent cases · triage             |
| Safety Case Workspace                         | `/app/frontend/src/pages/SafetyCaseWorkspace.jsx`         | Safety            | **The de-facto incident thread today**            |
| Incident Report (Public)                      | `/app/frontend/src/pages/IncidentReport.jsx`              | Public / Field    | Public field-crew report intake                  |
| Incident Report Viewer                        | `/app/frontend/src/pages/IncidentReportViewer.jsx`        | Safety / PM       | Read-only incident detail view                   |
| New Incident (Admin)                          | `/app/frontend/src/pages/NewIncident.jsx`                 | Admin / Safety    | Admin-side incident creation                     |
| Near-Miss Kiosk                               | `/app/frontend/src/pages/NearMissKiosk.jsx`               | Public            | Kiosk-mode anonymous near-miss submission        |
| Executive Case Report                         | `/app/frontend/src/pages/ExecutiveCaseReport.jsx`         | Executive         | Boardroom-grade single-case brief                |
| Executive Intelligence                        | `/app/frontend/src/pages/ExecutiveIntelligence.jsx`       | Executive         | Portfolio-attention view                         |
| Safety Incidents                              | `/app/frontend/src/pages/SafetyIncidents.jsx`             | Safety            | Safety-centric listing                            |
| HR Incidents                                  | `/app/frontend/src/pages/HrIncidents.jsx`                 | HR                | HR-visible incident rollup for employee context  |
| Safety Corrective Actions                     | `/app/frontend/src/pages/SafetyCorrectiveActions.jsx`     | Safety            | CAPA queue                                        |
| Safety Reports                                | `/app/frontend/src/pages/SafetyReports.jsx`               | Safety            | Report package browser                            |
| Safety Digest                                 | `/app/frontend/src/pages/SafetyDigest.jsx`                | Safety            | Weekly digest preview                             |
| Notifications Digest                          | `/app/frontend/src/pages/NotificationsDigest.jsx`         | Cross-portal      | Morning-digest recipient view                     |

## Frontend rollups (references only)
| Surface                                       | Purpose                                     |
|-----------------------------------------------|---------------------------------------------|
| `EmployeeProfile.jsx`                         | Incident count / recent by employee         |
| `HrEmployeeThread.jsx`                        | Employee Thread reads incident timeline     |
| `HrEmployeeAccountabilityTimeline.jsx`        | Accountability timeline includes incidents  |
| `ProjectHealth.jsx`                           | Project incident rollup                      |
| `PmProjectThread.jsx`                         | Project Thread reads OI incident driver     |
| `AssetTimelinePage.jsx`                       | Equipment/fleet incident cross-link         |
| `PmCommandCenter.jsx` / `LeadershipHubV2.jsx` | Guidance card + attention chips             |

## Backend modules
| Module                                                | Purpose                                                                        |
|-------------------------------------------------------|--------------------------------------------------------------------------------|
| `backend/routes/safety.py`                            | Legacy incidents API (`/api/incidents{,.csv,/{id}}`)                           |
| `backend/routes/incident_lifecycle.py`                | State events + transitions + lifecycle for legacy `incidents`                  |
| `backend/incident_engine/routes.py`                   | `/api/incident-cases/*` — case CRUD, evidence, cross-links, transitions        |
| `backend/incident_engine/workspace_routes.py`         | Workspace payloads — witnesses, medical, agency, communications, tasks, health |
| `backend/incident_engine/executive_report_routes.py`  | Executive intelligence + PDF                                                    |
| `backend/incident_engine/presence_score_routes.py`    | Presence score                                                                  |
| `backend/incident_engine/report_routes.py`            | Report packages, weekly digest                                                  |
| `backend/incident_engine/intelligence_routes.py`      | Incident portfolio intelligence (home / root-causes / corrective-actions / …)  |
| `backend/incident_engine/morning_digest_routes.py`    | Morning digest preview / send / recipients                                     |
| `backend/incident_engine/portfolio_intelligence.py`   | Portfolio-attention / safety-priority / pm-project-cases                       |
| `backend/incident_engine/public_gate.py`              | Public `/api/public/near-miss`                                                  |

## Data collections
| Collection                          | Purpose                                                          |
|-------------------------------------|------------------------------------------------------------------|
| `incident_cases`                    | Case core record (Track 19.15+)                                  |
| `incidents` (legacy)                | Pre-Track-19.15 incidents (still surfaced via `/legacy/{id}`)     |
| `incident_evidence`                 | Evidence rows                                                     |
| `incident_witnesses`                | Witness statements                                                |
| `incident_medical`                  | Medical rows (permissioned)                                       |
| `incident_agency_contacts`          | Agency / police / fire / utility                                  |
| `incident_communications`           | Communications log                                                |
| `incident_tasks`                    | Safety tasks (CAPA-adjacent)                                      |
| `corrective_actions`                | Formal CAPA records                                               |
| `incident_case_audit`               | Case audit trail                                                  |
| `incident_case_events`              | State events (open → investigation → executive-ready → closed)   |
| `incident_cross_links`              | Cross-entity relationships (project / employee / equipment)      |
| `morning_digest_recipients`         | Digest recipient list                                             |

## PDFs / report packages
| Package                           | Endpoint                                                        | Audience                    |
|-----------------------------------|-----------------------------------------------------------------|-----------------------------|
| Executive Case Report             | `GET /api/incident-cases/{id}/executive-report.pdf`             | Executive · board · owner   |
| Per-report-type package           | `GET /api/incident-cases/{id}/reports/{report_type}.pdf`        | Depends on report_type       |
| Weekly digest                     | `GET /api/incident-intelligence/digest/weekly.pdf`              | Safety leadership           |

## Zero missing capabilities
Every category the mandate lists (narrative · type · severity · reporter · involved · witnesses · photos · attachments · GPS · weather · medical · agency · evidence · CAPA · communications · timeline · status · reports · email routing · audit · linkages) already has an authoritative endpoint, collection, and page. **No backend construction required.**
