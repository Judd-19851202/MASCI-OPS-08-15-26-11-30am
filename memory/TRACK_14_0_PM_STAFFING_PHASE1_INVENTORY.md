# Track 14.0-PM-STAFFING-ASSIGNMENT-ACCESS — Phase 1 Inventory & Reality Check

**Date**: 2026-02-14 (fork session)
**Purpose**: Honest, evidence-based inventory of what already exists vs what is genuinely missing — required reading before opening repair tickets.

---

## Phase 1.A — Backend Staffing Backbone (EXISTS)

* **`backend/routes/project_team_assignments.py`** (772 lines) — production-grade closed-set role registry + admin + PM self-serve + cross-portal team API.
* **Closed-set `ROLE_REGISTRY`** (13 roles, snake_case keys → operator-friendly labels):
    * `pm` → Project Manager
    * `co_pm` → Co-PM
    * `assistant_pm` → Assistant PM
    * `superintendent` → Superintendent
    * `foreman` → Foreman
    * `safety_lead` → Safety Lead
    * `project_engineer` → Project Engineer
    * `asset_admin` → Asset Admin
    * `locate_coordinator` → 811 Locate Coordinator
    * `dispatcher_contact` → Dispatcher Contact
    * `shop_contact` → Shop Contact
    * `executive_oversight` → Executive Oversight
    * `read_only_stakeholder` → Read-only Stakeholder
* **Endpoints** (12 total, all wired in `server.py:11910`):
    | Method | Path | Caller | Verified |
    |--------|------|--------|----------|
    | GET | `/api/team-roster/feature-flags` | any portal | ✅ live |
    | GET | `/api/team-roster/role-registry` | any portal | ✅ live (returns 200) |
    | GET | `/api/admin/jobs/{project_number}/team` | Admin | ✅ |
    | GET | `/api/admin/jobs/{project_number}/team/audit` | Admin | ✅ |
    | POST | `/api/admin/jobs/{project_number}/team` | Admin | ✅ |
    | PATCH | `/api/admin/jobs/{project_number}/team/{assignment_id}` | Admin | ✅ |
    | DELETE | `/api/admin/jobs/{project_number}/team/{assignment_id}` | Admin | ✅ |
    | POST | `/api/admin/team-roster/backfill` | Admin | ✅ |
    | GET | `/api/pm/job/{project_number}/team` | PM self-serve | ✅ |
    | POST | `/api/pm/job/{project_number}/team` | PM self-serve | ✅ |
    | DELETE | `/api/pm/job/{project_number}/team/{assignment_id}` | PM self-serve | ✅ |
    | GET | `/api/jobs/{project_number}/team` | cross-portal read | ✅ |
    | GET | `/api/users/me/projects` | "my jobs" widget | ✅ |
* **Permission model already enforced**:
    * `ADMIN_ONLY_ROLES = {"pm", "co_pm", "executive_oversight"}` — PMs cannot self-assign PM/Co-PM/Executive.
    * `PM_ASSIGNABLE_ROLES` = registry − admin-only.
    * Helper: `_can_manage_project_team(actor, project_number)` — gated by both admin token AND project membership.
* **Audit log**: every assignment / removal / role change emits an `audit_events` row via `_audit()` with actor signature + IP.
* **Identity-aware**: assignments include `display_identity` / `legal_first_name` / `preferred_name` once the underlying employee row carries them (UXS-11D plumbing).
* **MongoDB indexes** (`server.py:9377`): unique `id` + composite (`project_number`, `assignment_role`) + email lookup index.
* **Team snapshot embedding**: assignments are denormalised onto the `jobs` collection so PM Hub / Daily Reports can read the team without a join.

## Phase 1.B — Frontend Staffing UI (EXISTS)

* **`/admin/jobs/:projectNumber/team`** → `pages/admin/AdminJobTeam.jsx` (registered at `App.js:562`)
* **`/pm/job/:projectNumber/team`** → `pages/pm/PmJobTeam.jsx` (registered at `App.js:702`)
* **`components/team/JobTeamRosterPanel.jsx`** (354 lines) — shared panel used by both Admin and PM routes:
    * Renders 13-role roster.
    * Inline add via role-registry dropdown.
    * Inline remove with confirm + audit reason.
    * "Backfill from legacy PM/Co-PM fields" button (admin only).
    * Role-aware action gating: admin-only roles hidden from PM-side assignment UI.
* **`components/team/MyAssignedProjectsWidget.jsx`** — "My assigned jobs" tile rendered on the Field Leadership Portal Dashboard (and any other "what am I on" surface).
* **`lib/teamRosterApi.js`** — typed client.

## Phase 1.C — User Creation (EXISTS via K4 IAM)

* **`routes/admin_directory_k4.py`** — multi-portal IAM directory.
* Endpoints (admin-step-up gated):
    * `POST /api/admin/directory/k4/users/{user_id}/role-template` — assign a portal-role template (PM / HR / Safety / Shop / Dispatch / FL).
    * `POST /api/admin/directory/k4/users/{user_id}/convert-to-managed` — convert a legacy user to managed identity.
    * Plus list / search / lifecycle endpoints (lines 101–251).
* **Per-portal user-management panels** already wired:
    * `components/AdminFieldLeadershipUsersPanel.jsx` — FL portal user CRUD (locked by UXS-11E).
    * HR-side host: `pages/HrFieldLeadershipUsers.jsx`.
* Result: Admin and HR can create users today. PM self-creating PMs is intentionally blocked (matches the `ADMIN_ONLY_ROLES` policy).

## Phase 1.D — Regression Coverage (EXISTS)

* `tests/test_project_team_assignments.py` + `tests/test_team_snapshot_embedding.py` → **19 tests passing** (full role registry CRUD, PM self-serve gates, admin-only role gate, audit emission, backfill, team_snapshot denormalisation).

---

## Gap Analysis vs User Directive

The directive lists these roles HR/PM should be able to manage:

| Directive Role | Registry Match | Status |
|---|---|---|
| PM | `pm` | ✅ |
| Co-PM | `co_pm` | ✅ |
| Project Engineer | `project_engineer` | ✅ |
| Project Administrator | *no exact match* | 🟡 **GAP** — directive uses "Project Administrator"; registry has `assistant_pm` ("Assistant PM"). Same role, different label, **or** a genuinely distinct role HR wants? Needs user decision. |
| Project Coordinator | *no exact match* | 🟡 **GAP** — possibly satisfied by `assistant_pm`, or wants its own enum. |
| Superintendent | `superintendent` | ✅ |
| Foreman | `foreman` | ✅ |
| Safety Representative | `safety_lead` | 🟡 Label drift: "Safety Lead" vs "Safety Representative". Same role conceptually. |
| QA/QC Representative | *no exact match* | 🟡 **GAP** — no QA/QC slot on the closed registry. QA/QC has its own portal but no project-level team role. |
| Asset Administrator | `asset_admin` | ✅ |
| Dispatch Representative | `dispatcher_contact` | ✅ (label drift) |
| HR Representative | *no exact match* | 🟡 **GAP** — HR is a portal but not a project-level team role. Decision needed: should HR have a per-project rep slot? |

## Honest scope assessment

The directive describes a 9-phase **complete operational audit** of staffing, user creation, permissions, portal landing, notification routing, and team visibility. Given the system is already substantial (12 endpoints + 354-line shared panel + 19-test regression suite + K4 IAM + per-portal user management already in production), the **honest work remaining** is:

1. **Resolve role registry label drift / gap roles** (1 user decision + ~3 hours of code if any new roles are added).
2. **Phase 4 permission matrix documentation** (no code change — a deliverable doc enumerating what each role can read/write per portal).
3. **Phase 5 portal landing certification** — already largely done by UXS-11E PortalShell sweep, but a written matrix per role is missing.
4. **Phase 6 notification routing matrix** — code already routes via `lib/event_fanout.py`; what's missing is the **document** that proves correct routing per role.
5. **Phase 7 PM project team visibility** — `JobTeamRosterPanel` is already mounted on both `/admin/jobs/{pn}/team` AND `/pm/job/{pn}/team`. **What's missing is surfacing it as an "always-visible Team Card" on the PM Job Detail / Project Health page** so a PM doesn't have to navigate to a separate `/team` route.
6. **Phase 9 regression** — 19 tests today; adding ~10 more for role-registry stability + permission-matrix-locking + portal-landing-locking would cover the gap.

Beyond that, the directive's "every role can be created / removed / transferred / multi-project assigned" is already implemented.

---

*Generated 2026-02-14 · Phase 1 Inventory · honest reality check before any new code.*
