# TRACK 20.2 · Project Inventory

## Frontend surfaces
| File                                              | Purpose                                     | Recommendation |
|---------------------------------------------------|---------------------------------------------|----------------|
| `pages/PmProjectDetail.jsx`                       | Composite project detail (operational events + material movement) | PROMOTE (foundation) |
| `pages/ProjectHealth.jsx`                         | Project health readout                       | MERGE (Section 8 OI) |
| `pages/ProjectPnlPage.jsx`                        | P&L                                          | KEEP (deep-link)     |
| `pages/ProjectStaffingHub.jsx`                    | Staffing overview                            | KEEP                 |
| `pages/JobPhotosLibrary.jsx`                      | Photo library                                | KEEP (Section 7)     |
| `pages/PmProjectRedirect.jsx`                     | Redirect helper                              | KEEP                 |
| `pages/pm/PmJobTeam.jsx`                          | Job team page                                | KEEP                 |
| `pages/pm/PmProjectStaffing.jsx`                  | Staffing per project                         | KEEP (Section 5)     |
| `components/pm/command/PmProjectFirstHome.jsx`    | PM CC project-first home                     | KEEP                 |
| `components/pm/command/PmProjectSelector.jsx`     | Project selector                             | KEEP                 |
| `components/pm/PmJobsRead.jsx`                    | Jobs read component                          | KEEP                 |
| `components/team/JobTeamRosterPanel.jsx`          | Team roster                                  | KEEP (Section 5)     |
| `components/JobFolderList.jsx`                    | Document folder list                         | KEEP (Section 6)     |
| `components/JobPicker.jsx`                        | Job picker widget                            | KEEP                 |
| `components/dispatch/command/JobBoard.jsx`        | Dispatch job board                           | KEEP                 |
| `components/operations-map/ProjectIntelligenceStrip.jsx` | OI strip for map view                | KEEP                 |

## Backend endpoints (project-scoped)
| Endpoint                                                              | Owner       | Purpose                                    |
|-----------------------------------------------------------------------|-------------|--------------------------------------------|
| `GET /api/projects/{id}`                                              | PM          | Project record                              |
| `GET /api/projects/{id}/members`                                      | PM          | Team members                                |
| `POST/DELETE /api/projects/{id}/members[/{user_id}]`                  | PM (Admin)  | Team CRUD                                   |
| `GET /api/projects/{id}/scorecard`                                    | PM          | Project scorecard                           |
| `GET /api/jobs/{project_number}/recent-context`                       | PM          | Track 19.04 smart-prefill baseline          |
| `GET /api/operational-events/project-day/{project_number}/{date}`     | Ops         | Per-day project event snapshot              |
| `GET /api/material-movement/daily/{project_number}/{date}`            | Materials   | Loads / tickets / hauls per day             |
| `GET /api/job-hazard-files/by-project/{project_number}`               | Safety      | JHA + hazard files                          |
| `GET /api/admin/jobs/export`, `.../archive`, `POST .../restore`       | Admin       | Job CRUD                                    |
| `PATCH /api/admin/jobs/{job_id}/active`, `.../co-pms`                 | Admin       | Job flags                                   |
| `DELETE /api/admin/jobs/{job_id}`                                     | Admin       | Job delete                                  |
| `GET /api/admin/projects/list`                                        | Admin       | All projects                                |
| `GET /api/admin/projects/pnl`                                         | Admin       | P&L                                         |
| `POST /api/daily-reports/attachments/upload`                          | PM          | DR attachments                              |
| `GET /api/operational-intelligence/summary` (filtered `project_intelligence`) | OI  | Project OI signal                          |

## Categories present today
Daily Reports · Employees (via team roster / daily reports) · Equipment
(via daily reports + dispatch + fleet) · Materials · Trucking · Safety
(JHAs · hazard files) · Photos · Operational Intelligence · Communications
(comments on DRs) · Audit (via OI audit).

## Categories with thin surfaces (would benefit from surfacing)
- **Survey** — control / models / design files: not directly project-page-linked today.
- **QA/QC** — tests / density / concrete: not directly project-page-linked today.
- **RFIs / Submittals / Change Orders** — not surfaced as first-class project sections today.

These are all NON-BLOCKING for a promotion track — the shell renders
honest empty states for slots that lack live data.
