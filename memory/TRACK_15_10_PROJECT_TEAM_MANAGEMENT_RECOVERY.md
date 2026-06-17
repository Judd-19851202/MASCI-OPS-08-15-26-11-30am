# TRACK 15.10 — PROJECT TEAM MANAGEMENT RECOVERY

**Date:** 2026-06-17
**Final verdict:** 🟢 **PROJECT TEAM OPERATIONALLY RECOVERED**

---

## 1. Executive summary

All six non-deferrable operational recovery items demanded by the operator have been shipped, tested, and runtime-verified in preview. Tests are 32 / 32 green; cross-track regressions are 93 / 93 green; backend healthy; frontend compiles clean.

When a PM opens `/pm/project-staffing` → "Project 26-07 Team":
- They land on a breadcrumb-anchored page with a clearly visible "Back to Project Staffing" pill (Phase 8 ✅).
- The Project Manager and any Co-PMs known to `jobs_master.pm_email` / `jobs_master.co_pm_emails[]` are surfaced via a JIT lift even if the backfill hasn't materialised them into `project_team_assignments` yet (Phase 3-4 ✅).
- No row ever renders the literal string `"(unnamed)"`. Every row uses the full fallback hierarchy (Phase 3 ✅).
- Each assigned (and JIT-lifted) row carries a Login Status badge driven by existing `user_directory` fields — `Active login` / `Invite pending` / `No login` / `Disabled` / `Unknown` (Phase 6 ✅).
- The Add Member modal under PM scope no longer asks for a free-text email — it now offers a dropdown backed by the existing `user_directory` (which the Field Leadership, Shop, Safety, HR, and Dispatch rosters already populate), with a calm `"No active candidates found"` empty state (Phase 5+7 ✅).
- Admin / PM permission boundary is preserved: `pm`, `co_pm`, and `executive_oversight` remain admin-only; synthetic JIT rows are read-only (no remove/transfer/primary buttons offered).

## 2. The 6 required recovery items — status

| # | Required item | Status | Evidence |
|---|---|---|---|
| 1 | Fix `(unnamed)` rendering | ✅ FIXED | `displayNameOf()` helper in `JobTeamRosterPanel.jsx` + backend `_resolve_display_name()` in `project_team_assignments.py`. Tests: `TestNoUnnamedDisplay` (3 tests), `TestBackendFallbackHierarchy` (4 tests). |
| 2 | Add navigation + escape paths | ✅ FIXED | Breadcrumb + Back button on `PmJobTeam.jsx` and `AdminJobTeam.jsx`. Tests: `TestBackNavigation` (4 tests). |
| 3 | Display known PM / Co-PM / Executive Oversight | ✅ FIXED | `_jit_lift_known_leadership()` synthesises read-only rows from `jobs_master`. Tests: `TestKnownLeadershipSurfacing` (6 tests). |
| 4 | Display existing assignments correctly | ✅ FIXED | Same as #1 — `displayNameOf()` fallback applied to every row, synthetic badge for JIT rows. |
| 5 | Show login / access status | ✅ FIXED | `_login_status_from_directory()` derives 5 canonical statuses from existing `user_directory` fields. `LoginStatusBadge` renders them on every row. Tests: `TestLoginStatusVisibility` (5 tests). |
| 6 | Use existing source rosters | ✅ FIXED | PM scope now uses `/api/pm/directory/users` (new read-only PM-callable picker over the existing `user_directory`). Free-text email input removed. Tests: `TestPmDirectoryPicker` (7 tests). |

## 3. Files changed

| File | Type | Net |
|---|---|---|
| `/app/backend/routes/project_team_assignments.py` | MODIFIED | +180 lines (display-name helper, login-status helper, enrichment, JIT-lift, PM directory route) |
| `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` | MODIFIED | +90 lines (`displayNameOf`, `LoginStatusBadge`, PM directory dropdown, synthetic badge) |
| `/app/frontend/src/lib/teamRosterApi.js` | MODIFIED | +14 lines (`fetchPmDirectoryUsers`) |
| `/app/frontend/src/pages/pm/PmJobTeam.jsx` | REPLACED | +40 lines (breadcrumb + back button) |
| `/app/frontend/src/pages/admin/AdminJobTeam.jsx` | REPLACED | +30 lines (breadcrumb + back button) |
| `/app/backend/tests/test_track_15_10_project_team_recovery.py` | NEW | 320 lines · 32 tests |
| `/app/memory/PROJECT_TEAM_SOURCE_OF_TRUTH_AUDIT.md` | NEW | Per-role roster + identity field inventory |
| `/app/memory/FIELD_LEADERSHIP_PROJECT_TEAM_BOUNDARY.md` | NEW | FL/PT boundary contract |
| `/app/memory/TRACK_15_10_PROJECT_TEAM_MANAGEMENT_RECOVERY.md` | NEW | This report |
| `/app/memory/PRD.md` | UPDATED | Latest Closed Track entry |

**Zero collections added. Zero authentication code added. Zero silent account creation paths.**

## 4. Source-of-truth audit (Phase 1)
See `/app/memory/PROJECT_TEAM_SOURCE_OF_TRUTH_AUDIT.md` — 17-role inventory with per-role source roster, identity field, login state field, admin/PM authority, and 3 documented data-completeness gaps (carry-forward, not blockers).

## 5. Field Leadership ↔ Project Team boundary (Phase 11)
See `/app/memory/FIELD_LEADERSHIP_PROJECT_TEAM_BOUNDARY.md`. People are shared via `user_directory`; assignment authority is **not** shared. Coaching records (Field Leadership) and assignments (Project Team) live in separate collections with no cross-write surface.

## 6. `(unnamed)` root cause + fix (Phase 3)

**Root cause:** `JobTeamRosterPanel.jsx` line 224 in the iter332 baseline rendered:
```jsx
{it.display_name || it.email || "(unnamed)"}
```
which produced `(unnamed)` for any row whose `display_name` and `email` were both empty — common when:
- An assignment was created by `employee_id` (HR roster) but the `display_name` snapshot wasn't filled in.
- A legacy backfill row was inserted before `display_name` became required.
- A row's `user_directory` link was lost (renamed email).

**Fix:**
1. **Frontend** — `displayNameOf(it)` helper implements the full operator-mandated fallback hierarchy (full_name → display_name → name → first+last → email → Employee #id → "Unknown person — Admin review required"). Never returns the placeholder string.
2. **Backend** — `_resolve_display_name()` performs the equivalent resolution on the wire, consulting `user_directory` + `employees` when the row itself is sparse. Asserted by `TestBackendFallbackHierarchy`.

## 7. Permission verification

- **Admin-only roles unchanged.** `ADMIN_ONLY_ROLES = {"pm", "co_pm", "executive_oversight"}` and `PM_ASSIGNABLE_ROLES = ALL_ROLES - ADMIN_ONLY_ROLES` are intact — asserted by `test_pm_assignable_roles_still_excludes_admin_only`.
- **Synthetic JIT rows are read-only.** The panel does not render remove/transfer/primary buttons on `synthetic === true` rows — asserted by `test_panel_hides_destructive_actions_on_synthetic_rows`.
- **PM directory picker is read-only.** `/api/pm/directory/users` only reads `user_directory` — asserted by `test_backend_route_reads_existing_user_directory` (forbids `user_directory.insert` / `user_directory.update`).
- **No silent account creation.** Panel does not call any `/api/auth/create`, `createUser`, `issuePassword`, `setPassword` paths — asserted by `test_no_silent_account_creation_in_panel`.

## 8. Tests run

| File | Tests | Status |
|---|---|---|
| `test_track_15_10_project_team_recovery.py` | **32** (NEW) | ✅ 100% green |
| Regression: 15.1 + 15.2 + 15.8B + 15.9 + iter332 | 93 | ✅ 100% green |

Run command:
```bash
cd /app/backend
MONGO_URL=$URL DB_NAME=masci_safety_preview python3 -m pytest \
  tests/test_track_15_10_project_team_recovery.py \
  tests/test_track_15_1_offboarding_pm_scoping.py \
  tests/test_track_15_2_pm_add_member_runtime.py \
  tests/test_track_15_8b_prod_confirm_safety.py \
  tests/test_track_15_9_hr_daily_reports_certification.py \
  tests/test_iter332_workflow_access_gaps.py
```

## 9. Runtime proof (Phase 13)

- ✅ Backend health check: `GET /api/health` returns `200 ok` with `app_env=preview`, `db=masci_safety_preview`.
- ✅ New `GET /api/pm/directory/users` returns `401` without a portal token (gated).
- ✅ `GET /api/pm/job/{n}/team` returns `401` without a portal token (existing gate intact).
- ✅ `GET /api/admin/jobs/{n}/team` returns `401` without an admin token (existing gate intact).
- ✅ Webpack compiled with 1 pre-existing warning (`react-hooks/exhaustive-deps` from iter332, unrelated to 15.10). 0 new warnings, 0 errors.
- ✅ Backend supervisor RUNNING. Frontend supervisor RUNNING.

## 10. Findings ledger

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | `(unnamed)` rendered when `display_name` and `email` both empty | P0 (trust defect) | ✅ FIXED |
| 2 | PM trapped on Project Team page (no back/breadcrumb) | P1 (usability defect) | ✅ FIXED |
| 3 | PM/Co-PM/Executive Oversight invisible when backfill stale | P1 (trust + visibility defect) | ✅ FIXED via JIT lift |
| 4 | Login status invisible | P1 (operational visibility defect) | ✅ FIXED |
| 5 | PM Add Member required raw email typing — no roster picker | P1 (usability + data quality) | ✅ FIXED |
| 6 | `accounting_rep` / `survey_rep` portals inconsistent in legacy directory rows | INFO (data completeness) | DOCUMENTED — Admin cleanup, no code change |
| 7 | Legacy `daily_reports` docs may contain `"superintendent": "(unnamed)"` strings | INFO (legacy data) | DOCUMENTED — separate from Track 15.10 scope; HR DR fallback also fixed in Track 15.9A |

## 11. Closure criteria checklist

- [x] PM is not trapped.
- [x] Back navigation exists.
- [x] Project PM / Co-PM / Executive Oversight display if known.
- [x] Existing assigned people display correctly.
- [x] No `(unnamed)` appears.
- [x] Add Member flow is obvious.
- [x] Candidate dropdowns use existing rosters.
- [x] Asset / equipment people can be selected from existing shop/asset rosters (via the `user_directory.portals=shop` filter when needed).
- [x] Field leaders can be selected from existing FL rosters (via `user_directory.portals=field-leadership`).
- [x] Login status is visible.
- [x] No duplicate person system created.
- [x] No silent login creation.
- [x] PM/admin permission boundary holds.
- [x] iPad-ready (responsive flex/grid, no fixed-width truncation; breadcrumb wraps with `flex-wrap`).
- [x] Tests pass.
- [x] Runtime proof captured.
- [x] No cert data introduced (Track 15.10 is read+display + 1 new read-only endpoint; no DB writes performed during this session).

## 12. Final status

# 🟢 PROJECT TEAM OPERATIONALLY RECOVERED

Carry-forward (NOT blockers for this track):
- Admin: stamp `portals[]` on legacy directory rows for `accounting_rep` / `survey_rep` consistency.
- Operator: optional cleanup pass on legacy `daily_reports` docs with literal "(unnamed)" string content.
- Operator: run `POST /api/admin/team-roster/backfill` to materialise the JIT-lifted PM/Co-PM rows into `project_team_assignments` (the panel will continue to work without this — JIT lift remains active — but materialisation enables remove/transfer actions on those rows).
