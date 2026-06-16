# PM Staffing — Account & Password Flow

**Source of truth:** `/app/backend/routes/project_team_assignments.py` + frontend `/app/frontend/src/components/team/JobTeamRosterPanel.jsx` + auth playbook (`/app/memory/test_credentials.md`).
**Authored:** 2026-06-16 — TRACK 15.2 Phase 4/5.
**Verified by:** `/app/backend/tests/test_track_15_2_pm_add_member_runtime.py` (6/6 PASS).

---

## TL;DR

**Project Staffing is an identity-binding operation, NOT a credential-issuance operation.**

When you (admin or PM) click "Add member" on a project, the system writes ONE row to `project_team_assignments` and that is the entire write-path. It does NOT create a portal login, does NOT generate a password, does NOT send a temp-password email, does NOT touch any of the seven portal-user collections (`shop_users` · `hr_users` · `project_managers` · `field_leadership_users` · `safety_users` · `dispatch_users` · `user_directory`).

If the person already has a portal login, **they keep their existing credentials unchanged.** If they don't, **the project assignment alone never gives them one** — login provisioning is a separate workflow under `/admin/people` → Access Control Center, owned by Admin.

---

## The 14 questions, answered

| # | Question | Answer |
|---|---|---|
| 1 | Does assigning a project team member create a login? | **No.** The only write is `db.project_team_assignments.insert_one(...)`. The user must already exist in `user_directory` or `employees` for the picker to find them. |
| 2 | If yes, where? | N/A — no login is created. |
| 3 | If no, what existing account is used? | The user's existing portal login(s), if any. The `user_directory` row holds portal-grant flags (admin / pm / shop / hr / safety / dispatch / field_leadership) that are independent of project staffing. |
| 4 | If the employee already has a Field Leadership login, is that same password used? | **Yes — they keep it.** No password rotation, no email, no notification of a new password. The FL token continues to authenticate `/api/field-leadership/portal/*` exactly as before. Project staffing rows are read by routing/scoping logic only; they are not consulted by `/api/field-leadership/portal/login`. |
| 5 | If employee has another portal login, does SSO inherit access? | **Yes** for tokens that the user already has. Multi-portal access is granted via the `user_directory` grants → `POST /api/auth/multi-login` returns ALL granted portal tokens in one response. Project staffing assignment never adds or removes a grant. |
| 6 | If the employee has no login, can the PM create one? | **No.** The PM can only assign existing directory/employee identities. The user picker (`fetchDirectoryUsers()`) reads `user_directory` and shows only existing rows. If the desired person isn't there, the PM cannot proceed. |
| 7 | If the PM cannot create a login, who must? | **Admin.** `/admin/people` → Access Control Center → "Add user" creates a new `user_directory` row with portal flags. Once the row exists, the PM can assign that person to a project. |
| 8 | Does Add Member only assign an existing directory/employee user? | **Yes.** `_resolve_user(db, payload)` in `project_team_assignments.py` reads `user_directory` (primary) and `employees` (secondary) by id / email / employee_id. It never inserts. |
| 9 | Does Add Member send a password email? | **No.** There is no Resend call, no `email-welcome`, no temp-password mint. Search `routes/project_team_assignments.py` for `password`, `email-welcome`, `set_password` — zero hits. |
| 10 | Does Add Member trigger a notification? | **Yes — one IN-APP notification only.** `_notify_assignment(...)` writes a `team.assignment` notification to `db.notifications`. The recipient is the assigned user via `recipient_user_id`, and **never broadcasts to a role**. No email is sent. |
| 11 | Does Add Member create an audit trail? | **Yes.** `_audit(...)` writes a row to `db.audit_events` with `category="project_team_roster"`, `action="assign"`, before/after snapshots, actor identity, and project_number. Available at `GET /api/admin/jobs/{pn}/team/audit`. |
| 12 | What happens for Project Engineer / Project Administrator / Project Coordinator / Superintendent / Foreman? | All five are in `PM_ASSIGNABLE_ROLES` (the 14-role PM-allowed set). PMs can assign them. **The assignment doesn't create or alter any portal login** for the target — it just binds an existing identity to the project at that role. |
| 13 | What about Asset Manager / Equipment Manager / Shop Representative? | `equipment_manager` and `shop_rep` are in `PM_ASSIGNABLE_ROLES` (canonical keys in `ROLE_REGISTRY`). "Asset Manager" and "Asset Administrator" are recently-added **label-only** options on the Shop Users panel; they do NOT exist as canonical project-staffing roles yet. To assign someone as "Asset Administrator" on a project, use `equipment_manager` — that's the operational equivalent. Future Track may add canonical `asset_admin` / `asset_manager` project-staffing roles if needed. |
| 14 | What happens if a duplicate email exists across portal systems? | The directory (`user_directory`) is the multi-portal identity layer — one row per person, portal-grant flags on that row. Per-portal user collections (`shop_users` / `hr_users` / etc.) are legacy and used only by the single-portal sign-in paths. If a person was bootstrapped into BOTH `shop_users` AND `user_directory`, sign-in works via either path but the directory is the canonical identity. Project staffing always resolves via the directory first; the per-portal collections are not consulted. |

---

## Canonical contract (the rule the code now enforces)

```
ASSIGNING A PERSON TO A PROJECT  ≠  GIVING THEM A LOGIN

  • Project staffing writes ONE row to project_team_assignments + ONE audit row.
  • Project staffing reads from user_directory and employees ONLY.
  • Project staffing NEVER writes to:
        user_directory       (login grant flags)
        shop_users           (shop portal accounts)
        hr_users             (HR portal accounts)
        project_managers     (PM portal accounts)
        field_leadership_users (FL portal accounts)
        safety_users         (safety portal accounts)
        dispatch_users       (dispatch portal accounts)
  • Project staffing NEVER mints a password.
  • Project staffing NEVER sends a temp-password email.
  • Project staffing emits exactly ONE in-app notification: a
    person-targeted "team.assignment" row to the assigned user.
```

The contract is enforced by static analysis in
`test_add_member_does_not_create_a_login` — if a future refactor
smuggles in a write to any of the seven forbidden collections or a
password-issuance call, the test fails at CI time.

---

## What does grant a login

Only these admin-owned flows mint passwords / issue tokens:

| Surface | Path | Effect |
|---|---|---|
| `/admin/people` → Access Control Center → "Add user" | `POST /api/admin/directory` | Creates a `user_directory` row with one master password (bcrypt) and portal-grant flags. The user signs in at `/sign-in`. |
| `/admin/people` → PM Users → "Issue password" | `POST /api/admin/project-managers/{id}/set-password` or `/email-welcome` | Sets a per-PM password on the `project_managers` row. Optionally emails it via Resend. |
| `/admin/people` → Shop Users → "Issue password" | `POST /api/admin/shop-users/{id}/set-password` or `/email-welcome` | Sets a per-shop-user password. Optionally emails. |
| `/admin/people` → HR Users → "Issue password" | `POST /api/admin/hr-users/{id}/reset-password` | Same pattern. |
| `/admin/people` → Dispatch Users → "Issue password" | `POST /api/admin/dispatch-users/{id}/reset-password` | Same pattern. |
| `/admin/people` → Field Leadership Users → "Issue password" | `POST /api/admin/field-leadership-users/{id}/reset-password` | Same pattern. |
| Safety Users (HR/Admin) → "Issue password" | `POST /api/admin/safety-users/{id}/reset-password` | Same pattern. |
| Self-serve | `POST /api/{portal}/forgot-password` | User initiates a 30-min Resend-link reset. |

These are the **only** code paths that touch a password or a portal-user collection. Project staffing is not one of them.

---

## What happens to a Field-Leadership person assigned to a project

Concrete example illuminating Q4 above:

1. Admin (earlier) created `john.foreman@mascigc.com` via `/admin/people` → Field Leadership Users → "Issue password". John received a Resend email with a 10-char temp password. He signed in at `/field-leadership/portal/login` and rotated his password to his own.
2. **One week later**, the PM of Project 26-07 wants John on the project as Foreman.
3. PM opens `/pm/project-staffing` → Project 26-07 → "Add member" → role = Foreman → user picker → selects "John Foreman".
4. PM clicks Save. **Behind the scenes**:
   - `db.project_team_assignments.insert_one({project_number: "26-07", user_id: john.id, assignment_role: "foreman", active: true, ...})` ✅
   - `db.audit_events.insert_one({category: "project_team_roster", action: "assign", ...})` ✅
   - `db.notifications.insert_one({type: "team.assignment", recipient_user_id: john.id, message: "Assigned as Foreman on 26-07"})` ✅
5. **What does NOT happen**:
   - ❌ No new row in `field_leadership_users` (John's FL row is untouched)
   - ❌ No password rotation (John's chosen password stays)
   - ❌ No "your password is XXXX" email (no Resend call)
   - ❌ No row in any other portal collection
6. **What John sees**: his existing FL portal login at `/field-leadership/portal/login` continues to work with his existing password. The next time he opens the FL portal, his bell shows the new "Assigned as Foreman on 26-07" notification (read-once, person-targeted, no role broadcast). Daily reports for Project 26-07 now appear in his FL portal's scope, governed by the `project_team_assignments` row.

---

## Edge cases

| Situation | Behaviour |
|---|---|
| Person exists in `employees` but NOT in `user_directory` | The picker shows them (employees are searched as a fallback). The assignment row is written with `employee_id` set and `user_id=None`. The notification is role-routed (no person-targeted recipient) until admin links them to a directory user. The `user_link_warning: true` field on the response surfaces this to the UI. |
| Person exists in `user_directory` but has no portal grants | Assignment succeeds. Person cannot sign into any portal until admin grants a portal flag via `/admin/people`. |
| PM tries to assign someone as `pm` / `co_pm` / `executive_oversight` | Backend `check_pm_can_assign(target_role)` rejects with 403. UI marks these three roles as disabled with the inline note: "Project Manager, Co-PM, and Executive Oversight are admin-only — request changes from your administrator." |
| Same person already assigned to the same project at the same role (active=true) | `POST /api/admin/jobs/{pn}/team` returns 409 with `"active assignment already exists for this user+role on this project"`. The UI surfaces the toast. |
| Person leaves the company | HR runs the offboarding playbook. **After Track 15.1**: PMs of projects the person was actively staffed on receive ONE person-targeted "Backfill open project assignments" task per project. All other PMs see nothing. The offboarded user's `user_directory` row is disabled by admin via the same playbook (separate task). |

---

## Cleanup of pre-15.1 leaked notifications

Historical PM offboarding notifications already in `db.notifications` are governed by `/app/backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py`. Per Track 15.2 Phase 3, an operator runs:

```
# dry-run first
MONGO_URL="<prod>" DB_NAME="masci_safety" python scripts/track_15_2_backfill_leaked_pm_offboarding.py

# review the ledger, then:
MONGO_URL="<prod>" DB_NAME="masci_safety" python scripts/track_15_2_backfill_leaked_pm_offboarding.py --apply
```

The script expires the broadcast row (`expires_at=now`) — no delete, audit-logged — and fans out person-targeted copies to the legitimate PM(s) per the same logic as the post-15.1 write site. The cleanup is reversible row-by-row using the ledger.

---

**End of doc.**
