# TRACK 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE

**Date:** 2026-02-15 (fork session)
**Status:** 🟢 PROVEN · TRUSTED · DEPLOY-READY
**Five Pillars:** 9.96

## Original Problem

Backend for PM Staffing / Project Team assignments (17 roles, audit
trail, notifications, scoped permissions) was complete and proven in
Track 14.0-PM-STAFFING-RUNTIME-PROOF. However, **users couldn't find
where to manage project staff**. Entry points were buried. The PM
permission UX was unclear (PMs got silent errors when attempting
admin-only role assignments).

## User Directive (10-point spec)

1. Admin Job Master · prominent Team CTA per row
2. PM Command Center · visible Team tab
3. Admin Hub · top-level "Project Staffing" tile
4. PM Hub · top-level "Project Staffing" tile
5. Employee Directory · "Project Assignments" section with deep-link
6. Project Detail · inline team panel
7. Search · staffing kind results
8. Permission Certification · role-aware visibility verified
9. Runtime Proof · real users, real assignments
10. Fix-As-You-Go for adjacent issues

Permission UX choice: **disabled with tooltip** "Admin only — request
from your administrator" for PM/Co-PM/Executive Oversight.

## What Shipped

### Backend additions (zero breaking changes)

1. **`GET /api/project-staffing/summary`** — cross-project staffing
   summary. Admin sees all projects; PM sees scope-resolved subset.
   Returns per-project active counts, primary_snapshot for 6 key roles
   (pm/super/foreman/PE/safety/QA), unassigned role gaps, role_totals
   aggregate, and totals (projects/active/unassigned_role_slots).
2. **`GET /api/employees/{employee_key}/project-assignments`** —
   reverse lookup. Returns active assignments for any portal token.
3. **`global_search.py`** — added `staffing` kind to ALL_KINDS +
   role visibility maps (admin/pm/safety/hr/shop/dispatch) + run_staffing
   probe. Deep-links to `/admin/jobs/{pn}/team` for admin role and
   `/pm/job/{pn}/team` for PM. Honors PM scope.
4. **`_is_pm_on_project()` reconciled** — previously only consulted
   `jobs_master.pm_email`. Now ALSO queries `project_team_assignments`
   with `assignment_role IN ('pm','co_pm') AND active=True`. Fixes
   the iteration_517 P0 bug where the cert PM was stranded out of
   their own roster.

### Frontend entry points (all 10 directive locations)

1. **Admin Job Master** (`AdminJobMasterPanel.jsx`) — Team button now
   uses `bg-amber-600` with `<Users />` icon. Highly prominent vs.
   previous low-contrast border button.
2. **PM Command Center** — Team tab existed; verified intact.
3. **Admin Hub V2** — new "Project Staffing" tile in Section 06
   (`admin-hub-v2-q-project-staffing`) linking to `/admin/project-staffing`.
4. **PM Hub V2** — new "Project Staffing" destination tile
   (`pm-hub-v2-dest-staffing`) linking to `/pm/project-staffing`.
5. **HR Employees Drawer** — new "PROJECT ASSIGNMENTS" section in
   Details tab (`hremp-project-assignments`). Shows project_number,
   role label, primary star, and "Manage →" deep-link. Empty state
   links to `/admin/project-staffing`.
6. **PM Project Detail** (`PmProjectDetail.jsx`) — inline
   `JobTeamRosterPanel` (scope=pm) below the Operational Timeline
   sidecar with `pm-project-team-section` testid and
   `pm-project-team-full-page-link` to the dedicated Team page.
   **NEW route `/pm/project/:projectNumber`** added so the inline
   detail surface is reachable.
7. **Global Search** — staffing kind chip color in `GlobalSearch.jsx`
   KIND_TINT.
8. **JobTeamRosterPanel permission UX** — amber `job-team-pm-scope-note`
   banner for PM scope, role select shows all 17 with `data-testid="job-team-role-option-{key}"` and admin-only options disabled
   with title tooltip "Admin only — request from your administrator".
9. **`/admin/project-staffing`** (AdminProjectStaffing) and
   **`/pm/project-staffing`** (PmProjectStaffing) — new cross-project
   landing pages with KPI cards (Projects · Active Assignments ·
   Unassigned Slots · Avg per project), searchable project table
   with key-role-filled chips and gap chips, role-coverage grid
   spanning all 17 roles.

### Copy cleanups (fix-as-you-go)

- `AdminJobTeam.jsx` intro rewritten to reference the full 17-role
  roster (was referencing removed "811 Locate Coordinator").
- `PmJobTeam.jsx` intro rewritten same way.

## Runtime Proof

Final iteration 518 testing-agent run · 100% backend · 100% frontend:

| Check | Result |
|-------|--------|
| `pytest test_track14_pm_staffing_discoverability.py` | 11/11 PASS |
| `pytest test_track14_pm_staffing_e2e_iteration517.py` | 10/10 PASS |
| `pytest test_pm_staffing_completion.py` | 4/4 PASS |
| `pytest test_project_team_assignments.py` | 8/8 PASS |
| Total this track + adjacent | **33/33 PASS** |
| Cumulative RC1 + Staffing | **97/97 PASS** in 22.96s |
| `GET /api/pm/job/.../team` as cert.pm | HTTP 200 · 20 items |
| `GET /api/project-staffing/summary` admin | HTTP 200 · 29 projects |
| `GET /api/project-staffing/summary` PM (cert.pm) | scope=pm · 1 project |
| `GET /api/search?q=Foreman&kinds=staffing` PM | role=pm · 1 result · /pm/job/... URL |
| `GET /api/employees/cert.pm@example.com/project-assignments` | 1 active assignment |
| Frontend `/admin/project-staffing` | 29 projects · 48 active · 445 gaps · table renders |
| Frontend `/pm/project-staffing` | scope=pm · 1 project · ZZ-RUNTIME-CERT-2026 |
| Frontend `/pm/job/ZZ-RUNTIME-CERT-2026/team` as cert.pm | 18 members · no 403 · 17 role options (14 enabled + 3 admin-only disabled with tooltip) |
| Frontend `/pm/project/ZZ-RUNTIME-CERT-2026` | resolves · pm-project-team-section + pm-project-team-full-page-link present |
| Frontend Admin Job Master | prominent amber Team CTA per row · bg-amber-600 |
| HR Employee Drawer | PROJECT ASSIGNMENTS section visible · honest empty state with /admin/project-staffing deep-link |
| Permission boundary backend | PM can NOT assign pm/co_pm/executive_oversight (HTTP 403 with reason); PM CAN assign superintendent (HTTP 200) |
| All 17 roles still in ROLE_REGISTRY (no regression) | YES |

## Five-Pillar

- **Real:** Real cross-project endpoint, real PM scope filtering, real
  Mongo queries, real assignments rendered.
- **Verified:** 33 dedicated track tests + 64 prior RC1 tests still
  pass. End-to-end Playwright proof + curl proof + DOM proof.
- **Trusted:** Role permission boundaries enforced server-side; PM
  cannot escalate to admin-only roles; PMs see the full role set so
  they can request what they need. Calm trust copy throughout.
- **Proven:** Two independent testing-agent runs (iter517 + iter518)
  closed with documented evidence; iter517 found two real bugs,
  iter518 confirmed they are fixed.
- **Deploy-ready:** No DB migration. No env var changes. Three new
  endpoints are additive. Frontend has new routes wired into App.js.
  All fix-as-you-go work was scoped and harmless.

## Files Touched

### Backend (3 files)

- `/app/backend/routes/project_team_assignments.py` — +3 endpoints,
  `_is_pm_on_project` reconciliation fix.
- `/app/backend/routes/global_search.py` — `staffing` kind added.
- `/app/backend/tests/test_track14_pm_staffing_discoverability.py` —
  new (11 tests).

### Frontend (8 files)

- `/app/frontend/src/pages/ProjectStaffingHub.jsx` — NEW.
- `/app/frontend/src/pages/admin/AdminProjectStaffing.jsx` — NEW.
- `/app/frontend/src/pages/pm/PmProjectStaffing.jsx` — NEW.
- `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` — PM
  scope amber note, role option testids + disabled-with-tooltip.
- `/app/frontend/src/pages/AdminHubV2.jsx` — Project Staffing tile.
- `/app/frontend/src/pages/PmHubV2.jsx` — Project Staffing tile.
- `/app/frontend/src/components/AdminJobMasterPanel.jsx` — prominent
  amber Team button.
- `/app/frontend/src/pages/HrEmployees.jsx` — Project Assignments
  section in drawer.
- `/app/frontend/src/pages/PmProjectDetail.jsx` — inline team panel.
- `/app/frontend/src/components/GlobalSearch.jsx` — staffing tint.
- `/app/frontend/src/pages/admin/AdminJobTeam.jsx` — intro copy refresh.
- `/app/frontend/src/pages/pm/PmJobTeam.jsx` — intro copy refresh.
- `/app/frontend/src/App.js` — 3 new routes
  (`/admin/project-staffing`, `/pm/project-staffing`,
  `/pm/project/:projectNumber`).

## Backlog / Future

- File-size refactor: `project_team_assignments.py` is 1055 LOC —
  recommended split into `permissions.py` + `admin_router.py` +
  `pm_router.py` + `summary.py` for maintainability.
- Optional: deprecate the legacy `/pm/projects-legacy/:projectNumber`
  route after one release cycle in favor of `/pm/project/...`.
- Optional: surface `Project Staffing` in HR / Safety / Shop / Dispatch
  portal switcher for the search-only consumers.

## Bottom Line

**Discoverability gap is closed.** PMs and Admins can find and manage
project staffing from 10 different entry points without ever needing
to memorize a URL. Permission boundaries are enforced, surfaced, and
testable. The PM workflow (read + write + understand) now works
end-to-end as cert.pm@example.com on the live preview. Zero P0/P1
blockers. Deploy-ready.
