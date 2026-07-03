# TRACK 20.2 · Executive Audit

## Verdict
🟢 **PROMOTE + ADAPTERS.**

## Central finding
Unlike the Employee Thread (where a single certified endpoint served as
the promotion foundation), the Project Thread ecosystem is **heavily
distributed** across a rich set of certified endpoints and components.
There is no single "/project-timeline" endpoint — but every operational
signal already exists in a certified location.

## Foundation surfaces (existing)
- **Pages:** `PmProjectDetail.jsx`, `ProjectHealth.jsx`, `PmProjectFirstHome.jsx`, `PmProjectStaffing.jsx`, `JobTeamRosterPanel.jsx`, `JobPhotosLibrary.jsx`, `ProjectPnlPage.jsx`, `PmJobTeam.jsx`, `PmProjectSelector.jsx`, `PmProjectRedirect.jsx`.
- **Backend:** `/api/projects/{id}`, `/api/projects/{id}/members`, `/api/projects/{id}/scorecard`, `/api/jobs/{project_number}/recent-context`, `/api/operational-events/project-day/{project_number}/{date}`, `/api/material-movement/daily/{project_number}/{date}`, `/api/job-hazard-files/by-project/{project_number}`, `/api/admin/projects/list`, `/api/admin/projects/pnl`, `/api/daily-reports/*`.
- **OI signal:** `project_intelligence` in `/api/operational-intelligence/summary`.
- **Command Center:** `/pm/command-center` already presents live project state via strips + selectors (Track 19.52).

## Why PROMOTE + ADAPTERS (not "promote existing foundation")
- No single certified endpoint returns the Project payload the way `/accountability/timeline` does for the Employee.
- The `PmProjectDetail.jsx` page already composes many of the pieces (operational events, material movement, project-day facts).
- A promotion track would consume THIS page's endpoints + `project_intelligence` OI + `JobTeamRosterPanel` + `JobPhotosLibrary` + certified daily-report / dispatch feeds — **all through frontend adapters, zero new backend.**

## Recommendation
🟢 **PROMOTE + ADAPTERS.** Track 19.57 (proposed) becomes a
promotion track that wraps the existing project endpoints and
components with the Track 19.55 `OperationalThreadPage` shell + Track
19.54 Guidance Card + universal chips + RelationshipGraph. Zero new
backend endpoints. All content already exists.

## Estimated net-new code (out of Track 20.2 scope)
- Backend: **0 LOC.**
- Frontend: **~ 350 LOC** (one page + 5 adapters similar to Track 19.56).
- Tests: 1 lock file.
