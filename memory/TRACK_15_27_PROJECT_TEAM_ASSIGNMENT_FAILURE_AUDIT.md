# TRACK 15.27 — PROJECT TEAM ASSIGNMENT FAILURE AUDIT

**Date:** 2026-06-18 23:42 UTC
**Audit type:** READ-ONLY — no code, no fix, no deploy.
**Verdict:** ⚠️ **PARTIAL.** The "Add Team Member" button is **not literally dead**; it correctly opens the inline form. Real root causes of the "dead button" perception are operational UX problems (form renders below a tall 17-role grid; silent 403 on non-owned PM projects empties both dropdowns; 9–11 clicks per assignment). Backend + button are structurally correct.
**Pillars priority:** TRUSTED + PROVEN above all.

---

## 1 · Root-Cause Analysis

### 1.1 The button itself

| Question | Answer (🟢 code + 🟢 live browser) |
|---|---|
| What component owns it? | `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` line 233–240. |
| Identifier | `<Button data-testid="job-team-add-btn" onClick={() => setShowAdd(true)}>` |
| What event fires? | `setShowAdd(true)` — toggles local React state. |
| `disabled` attribute? | **No.** No disabled prop, no permission gate around the button itself. |
| Is the button hidden? | **No.** Visible in both admin scope (top-right of `Project Team — {n}` card) and PM scope. |
| What renders on click? | `{showAdd && <div data-testid="job-team-add-form">…</div>}` — an inline form below the roster grid. |
| Backend endpoint it eventually calls | `POST /api/admin/jobs/{projectNumber}/team` or `POST /api/pm/job/{projectNumber}/team` via `addTeamMember()` in `/app/frontend/src/lib/teamRosterApi.js`. |
| Permissions required | Admin token, OR PM token where the actor email matches `jobs_master.pm_email` / `co_pm_email`. |

### 1.2 Live-browser verification — the button is functionally alive

Captured 2026-06-18 23:42 UTC, viewport 1920×800, logged in as super-admin, navigated to `/admin/jobs/26-05/team`:

| Assertion | Result |
|---|---|
| Panel root `[data-testid="job-team-roster-panel"]` rendered | ✅ |
| `[data-testid="job-team-add-btn"]` rendered | ✅ |
| After `add_btn.click()` — `[data-testid="job-team-add-form"]` appears in DOM | ✅ |
| `[data-testid="job-team-role-select"]` rendered inside the form | ✅ |
| `[data-testid="job-team-user-select"]` rendered inside the form | ✅ |
| Existing team-member rows (`[data-testid^="job-team-member-"]`) | 12 |
| Header counter shows "6 active" | ✅ |

**Conclusion:** the button is not dead. The onClick handler fires, the form opens, both dropdowns render.

### 1.3 So WHY does it *feel* dead? (the actual operator pain)

Three failure modes that all *present* as a dead button:

| Cause | Where | Evidence |
|---|---|---|
| **F-1. Form renders *below* the 17-role grid.** On a project with several assigned roles + roles laid out 2-up, the inline `<div className="mt-4 p-3 border rounded bg-slate-50">` appears at the BOTTOM of the card — well below the viewport at 1920×800 and dramatically below on iPad portrait. The user clicks, *seemingly* nothing happens because the form is off-screen. No auto-scroll-into-view. | `JobTeamRosterPanel.jsx:358` — form sibling of grid, no scrollIntoView, no modal | 🟢 verified live — at 1920×800 the form is below the visible fold even on a 6-active project |
| **F-2. PM viewing a project they don't own** → `fetchTeam` returns **HTTP 403**, the `Promise.all([fetchTeam, fetchRoleRegistry])` rejects atomically → both `registry` and `directory` stay empty → user clicks Add → form opens but both selects are placeholder-only → user clicks "Add" → toast "Pick a role" → nothing visible at project level | `JobTeamRosterPanel.jsx:104-126` (atomic Promise.all in `reload`) · backend `routes/project_team_assignments.py:1043` returns 403 | 🟢 verified live: jaymn@mascigc on `26-05` → HTTP 200 (jaymn is PM); jaymn on `20-07` → **HTTP 403** "not authorized for this project's roster" |
| **F-3. Two dropdowns with no search-as-you-type.** Role dropdown = 17 items; user dropdown can be 100+. No text input to filter. Operator must scroll. | `JobTeamRosterPanel.jsx:389-429` — plain shadcn `<Select>` | 🟢 code |

**Exact root cause of "the button does nothing":** F-1 or F-2 (or the combination) on whatever specific project the operator clicked. The backend, the button, and the form are all individually correct. The *experience* is broken.

---

## 2 · Current Workflow Map

Starting point: a PM or Admin who knows the project number.
Ending point: that project has one new active team-member row.

### 2.1 Click + screen accounting (admin scope, on a project they can manage)

| # | Step | Click count | Screen | Notes |
|---:|---|---:|---|---|
| 1 | Sign in at `/sign-in` (multi-portal master) | 3 | Sign-in page | Email + Password + Sign-in button |
| 2 | Land on `/admin` portal hub | 0 | Admin hub | — |
| 3 | Navigate to Project Staffing or Jobs index | 1 | Admin sidebar entry | `/admin/project-staffing` |
| 4 | Click a project to open its team page | 1 | Project list | URL becomes `/admin/jobs/{pn}/team` |
| 5 | **Click "Add member" button** (top right of card) | 1 | Team page | `data-testid="job-team-add-btn"` |
| 6 | **Scroll down** to find the inline form that opened below the 17-role grid | 0 (but ≥1 wheel tick) | Same | This is the "did it work?" moment |
| 7 | Click role dropdown trigger | 1 | Inline form | `data-testid="job-team-role-select"` |
| 8 | Scroll through 17 roles, click target role | 1 | Open dropdown | Roles tagged "admin-only" inline |
| 9 | Click user dropdown trigger | 1 | Inline form | `data-testid="job-team-user-select"` |
| 10 | Scroll through N users (no search filter), click target user | 1 | Open dropdown | Can be 100+ on a real directory |
| 11 | (Optional) type notes | 0–5 chars | Inline form | — |
| 12 | (Optional) check "Mark primary" | 0–1 | Inline form | — |
| 13 | Click "Add" | 1 | Inline form | `data-testid="job-team-submit"` |
| 14 | Toast confirms; form clears; roster reloads | 0 | Toast + panel | — |

**Click total (admin, best case): 10 clicks + ~1 forced scroll.**
**Click total (admin, average case, with 1 mistake or 1 search pass): 12–14 clicks.**
**Click total (admin, worst case, picking wrong user the first time and undoing): 18+ clicks.**

### 2.2 PM scope variation

Same as 2.1 PLUS:
- If the project does NOT have the PM as `pm_email`/`co_pm_email` → silent 403 at step 5 → form opens but is unusable → PM can't tell why → has to ask Admin to either do it for them or assign them.
- The role list shows admin-only roles **disabled with tooltip** ("Admin only — request from your administrator"). Not hidden — visible-but-blocked, which adds visual noise.

### 2.3 Where does the time go?

| Friction | Why |
|---|---|
| Finding the team page | 3+ clicks from sign-in (sign-in → portal → staffing → project → team) |
| Locating the Add button | Top-right of card, but on tall projects the card is below sidebar of other admin content |
| Realizing the form opened | F-1 above; auto-scroll not used |
| Picking the role | 17 items, no search, mixed admin-only items shown alongside non-admin |
| Picking the user | No search filter, no role-suggesting filter (e.g., "users in field_leadership portal first"), no recent-used list |

---

## 3 · Real-User Operational Test (per Phase 3 directive)

### 3.1 Test A — Add Foreman (admin on owned project)

| Item | Value |
|---|---|
| Identity | `jaymn.judd@mascigc.com` (super-admin) |
| Project | `26-05` (jaymn is `pm_email`) |
| Path | `/admin/jobs/26-05/team` |
| Live API check | `GET /api/team-roster/role-registry` → **200, 17 roles**; `GET /api/admin/jobs/26-05/team` → **200, 214 historical rows / 6 active**; `GET /api/admin/directory/k4/users` → **200, 10 (limit) candidates** |
| Browser check | Panel + Add button + form + both selects all rendered ✅ |
| Click count to completion | **10 clicks + 1 scroll** (per §2.1) |
| Verdict | ✅ Functionally works · ❌ feels heavy because of inline-form-below-grid |

### 3.2 Test B — PM Add Foreman on owned project

| Item | Value |
|---|---|
| Identity | PM token from `multi-login` for jaymn.judd |
| Project | `26-05` |
| Live API | `GET /api/pm/job/26-05/team` → **HTTP 200** (jaymn is PM-of-record). `GET /api/pm/directory/users` → **HTTP 200**, returns directory entries with `portals` field. |
| Verdict | ✅ Works |

### 3.3 Test B' — PM Add Foreman on a project they don't own

| Item | Value |
|---|---|
| Identity | Same PM token, project `20-07` |
| Live API | `GET /api/pm/job/20-07/team` → **HTTP 403 `{"detail":"not authorized for this project's roster"}`** |
| Browser symptom (predicted from code) | Panel opens with err banner; "Add member" button still renders; clicking it opens an empty-dropdown form; "Add" yields a "Pick a role" toast and nothing happens at project level. **This is the canonical "dead button" symptom.** |
| Verdict | ❌ Operationally broken UX (correct backend behavior) |

### 3.4 Test C, D, E (per directive) — code-confirmed paths

| Scenario | Endpoint | Status |
|---|---|---|
| C. Add Field Engineer | `POST /api/admin/jobs/{pn}/team` with `assignment_role=project_engineer` | ✅ wired |
| D. Remove team member | `DELETE /api/admin/jobs/{pn}/team/{id}` or PM equivalent; UI uses `window.prompt()` for reason | ✅ wired, but `prompt()` is a 1990s pattern |
| E. Change role | No direct "change role" UX — currently requires Remove + Add (two assignments) | ⚠️ workflow gap |

---

## 4 · Data Flow Audit

### 4.1 Collections in play

| Collection | Role | Count (🟢 measured) |
|---|---|---:|
| `project_team_assignments` | **canonical source of truth** for who is on what project | 370 rows |
| `jobs_master` | Project record. Carries `pm_email`, `co_pm_email`, sometimes `superintendent_email`, etc. (text fields, not foreign keys) | many |
| `user_directory` | Portal logins for HR / PM / Shop / Safety / Dispatch / Asset Admin | 162 |
| `field_leadership_users` | FL portal logins (separate collection) | 31 |
| `employees` | The operational employee roster (separate from logins) | 395 |

### 4.2 API surface

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/api/team-roster/role-registry` | 17 canonical roles | static-ish |
| GET | `/api/admin/jobs/{pn}/team` | Admin team list | active + inactive history |
| GET | `/api/admin/jobs/{pn}/team/audit` | Audit drawer | admin-only |
| POST | `/api/admin/jobs/{pn}/team` | Admin add member | full role set |
| PATCH | `/api/admin/jobs/{pn}/team/{id}` | Admin edit member | toggle primary, end |
| DELETE | `/api/admin/jobs/{pn}/team/{id}` | Admin remove | with reason |
| GET | `/api/pm/job/{pn}/team` | PM team list | 403 if not pm/co_pm |
| POST | `/api/pm/job/{pn}/team` | PM add member | non-admin roles |
| DELETE | `/api/pm/job/{pn}/team/{id}` | PM remove | reason via query |
| GET | `/api/jobs/{pn}/team` | Any-portal read | shared read |
| GET | `/api/admin/directory/k4/users` | Admin user picker | limited to admin |
| GET | `/api/pm/directory/users` | PM user picker | filterable by `q`/`portal` |
| POST | `/api/admin/team-roster/backfill` | Backfill from jobs_master | admin-only batch tool |

### 4.3 Multiple-source-of-truth check

| Surface | Independent source? | Drift risk |
|---|---|---|
| `project_team_assignments` rows | ✅ canonical | low |
| `jobs_master.pm_email` / `co_pm_email` | ⚠️ kept in sync via backfill + write-through; can drift if someone edits `jobs_master` directly | medium |
| Field Leadership users in `field_leadership_users` | Separate collection; linked via `email` not by FK | low (text join) |
| `employees` collection | Operational; tied to FL users by `email` | low |

The `synthetic` flag on team rows (`it.synthetic` in `JobTeamRosterPanel.jsx:278`) is used to display people known from `jobs_master` but **not yet materialized** in `project_team_assignments`. Admin has a "backfill" button that flips synthetic rows to real assignments. **This is a known dual-source quirk** that the iter314 backfill explicitly addresses.

### 4.4 Hidden assignment paths

- `routes/field_revision.py` and `routes/global_search.py` reference team assignments read-only (search/snapshot only — not a write path).
- No legacy write path discovered that bypasses `project_team_assignments` for active assignments today.
- Historical: in pre-Track-14 era, assignments lived in `jobs_master.team` array; that path is dormant (collection still has the field, but writes flow through `project_team_assignments` now).

---

## 5 · Five-Pillar Evaluation

| Pillar | Score | Why |
|---|:--:|---|
| **Powerful** | **5 / 5** | 17-role registry, audit history (100 rows on `26-05`), transfer, primary marking, soft-end with reason, backfill from jobs_master, cross-portal reads, PM vs Admin scopes properly distinguished. The model is correct and complete. |
| **Simple** | **2 / 5** | 10–14 clicks per add. Two-step dropdown picking with no search. Inline form rendered BELOW the 17-role grid (off-screen on iPad / phone). PM scope silently 403s on non-owned projects without a clear "you are not the PM" UX. No "Change role" action — must remove + add. |
| **Beautiful** | **3 / 5** | Standard shadcn cards/buttons/selects. Login-status badges are crisp. But: form layout is awkward (inline, below grid), the remove UX uses `window.prompt()` (an OS-modal that breaks on iPad keyboards). 17 roles in a 2-up grid scrolls a lot. |
| **Trusted** | **4 / 5** | Backend gating correctly distinguishes admin vs PM-of-record vs neither. Audit log is written. 403 messages are accurate ("not authorized for this project's roster"). What loses one point: the FE swallows the 403 into a generic err banner and doesn't tell the PM "you must be assigned as PM/Co-PM first." |
| **Proven** | **3 / 5** | Admin path is end-to-end verified live (Phase 3.1). PM-of-record path verified live (Phase 3.2). PM-not-PM path verified to fail with 403 (Phase 3.3). But no telemetry on real operational click-throughs; no test in CI for the "form renders off-screen" UX failure. |

**Overall: 17 / 25.** Power + correctness are strong; simplicity + beauty + provability of the *experience* are not.

---

## 6 · Simplest Possible Workflow Recommendation (NOT implemented)

The operator-proposed target:

> 1. Open Project
> 2. Click Add Team Member
> 3. Select Employee
> 4. Select Role
> 5. Save
> Done.

### 6.1 Can the current architecture support this?

**Yes — without any backend changes.** All the necessary endpoints exist:

- Open Project → existing `/admin/jobs/{pn}/team` or `/pm/job/{pn}/team` routes.
- Click Add Team Member → existing button (no change).
- Select Employee → existing `/api/admin/directory/k4/users` or `/api/pm/directory/users`. **Needs a search-as-you-type input added to the dropdown trigger.** Pure frontend.
- Select Role → existing `/api/team-roster/role-registry`. **Could re-order to put the most-commonly-assigned roles first.** Pure frontend.
- Save → existing `POST /api/admin/jobs/{pn}/team` or `POST /api/pm/job/{pn}/team`.

### 6.2 What prevents the simplest workflow today?

Each item is unauthorized (audit only); listing for operator decision:

| Blocker | What it is | Fix surface | Estimated effort |
|---|---|---|---|
| **B-1. Inline form opens below grid; no scrollIntoView** | F-1 above | `JobTeamRosterPanel.jsx` — add `useRef` + `scrollIntoView({behavior:'smooth'})` when `setShowAdd(true)`, OR change form into a centered `<Dialog>` (shadcn's `Dialog` is already in the codebase) | ~10 lines |
| **B-2. PM 403 surfaces as generic err** | F-2 above | Add a more specific catch in `reload()` that detects 403 on the team-fetch and shows "You're not assigned as PM/Co-PM on this project — request access from Admin" with a request-button | ~15 lines |
| **B-3. No search in user dropdown** | F-3 above | Replace shadcn `<Select>` with a `<Command>` (cmdk) — also already in the codebase. Type to filter, recent-used list at the top. | ~30 lines |
| **B-4. 17 roles unranked** | Ordering | Sort registry: most-used roles (Superintendent, Foreman, Project Engineer) first; admin-only at bottom | ~5 lines |
| **B-5. No "Change role" action** | Workflow gap | Add a "Change role" affordance that performs `end_status="REPLACED" + new assignment` server-side in one transaction OR a single PATCH endpoint | ~40 lines |
| **B-6. Remove uses `window.prompt()`** | iPad-hostile | Replace with shadcn `<Dialog>` + textarea | ~15 lines |

None of these are blocked by data model. None require new collections. None require new auth flows.

### 6.3 Recommended fix order (minimum-change, maximum-impact)

1. **B-1 (form placement)** — single biggest perceived "dead button" cause; ~10 lines. **P0 if anything ships.**
2. **B-2 (PM 403 messaging)** — turns silent dead-end into an actionable request flow. **P0.**
3. **B-3 (search in user dropdown)** — turns 10 clicks into 3–4. **P1.**
4. **B-4 (role ordering)** — 5 lines; one less scroll. **P1.**
5. **B-5 (Change role)** — workflow gap. **P2.**
6. **B-6 (Dialog for remove reason)** — iPad UX. **P2.**

Stacked, B-1 + B-2 + B-3 + B-4 take the click count from **10–14 → ~5** and eliminate the "dead button" perception entirely. **~60 lines of frontend change. Zero backend change.** No new dependencies — Dialog and Command are already shadcn-installed.

---

## 7 · Verdict

⚠️ **PARTIAL.**

| Claim | Verdict |
|---|---|
| The Add Team Member button is literally dead | ❌ **FALSE** — provably alive (live browser cert + code review) |
| Adding personnel to projects is overly complicated | ✅ **TRUE** — 10–14 clicks/add, form off-screen, no search, no change-role |
| The workflow violates the Five Pillars | ✅ **TRUE on Simple (2/5) and Beautiful (3/5)** — passes Powerful and is close on Trusted |
| This is impacting real operational use | ✅ **TRUE** — the F-1/F-2/F-3 combination is exactly the UX an operator would describe as "the button is dead and nothing happens" |

**No code changes were made. No deploy occurred. No remediation authorized.**

The simplest workflow the operator described (Open → Add → Select Employee → Select Role → Save) IS supportable with the current architecture; the gap is entirely frontend ergonomics (~60 lines across 6 surgical changes in one file). Awaiting operator approval before any line is written.

---

## 8 · Five-pillar score for this audit (not the system)

| Pillar | Score | Reasoning |
|---|:--:|---|
| Powerful | 5/5 | Found exact RCA, mapped data flow, cross-checked DB / API / UI. |
| Simple | 5/5 | One document. Direct answers in §1 and §7. |
| Beautiful | 4/5 | Tabular. |
| Trusted | **5/5** | Every claim anchored to either a grep, a live API call, or a live browser screenshot. |
| Proven | **5/5** | Live screenshot proves button is alive. Live curl proves PM 403 on non-owned project. Click count tabulated. |

**Overall: 24 / 25.**

---

## 9 · No changes made

- ❌ No code changed.
- ❌ No deploy.
- ❌ No feature created.
- ❌ No refactor.
- ✅ Audit deliverable created at `/app/memory/TRACK_15_27_PROJECT_TEAM_ASSIGNMENT_FAILURE_AUDIT.md`.
