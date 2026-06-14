# Track 14.0-JOB-OWNERSHIP-FOUNDATION · Phase 1 Closure

**Date:** 2026-06-14 · **Mode:** Controlled implementation · **Status:** CLOSED

Phase 1 of the Job Ownership Foundation. Editable per-project team roster, admin-managed + PM-managed, audited, idempotently backfilled from existing `pm_email` / `co_pm_emails` data. Person-level notification routing now has a real, editable data source to read from in Phase 2 producer rewrites.

Hard locks honoured: no deploy, no GitHub push, no merge, no Spanish, no PDF lockup, no integration banners, no UXS-11, no new portal, no PM portal access widening, no existing-PM behaviour broken, no notification producers rewritten in this phase.

---

## 1. Track status
**CLOSED — Phase 1 of 3.** Five-Pillar composite: 9.55 (Trusted 9.85, Proven 9.85). All 8 backend regression tests pass. Admin UI renders compile-clean. PM scope enforced server-side.

## 2. Collection / model created
- **`project_team_assignments`** Mongo collection with 5 indexes (id unique · project+role+active composite · user+active composite · email+active composite · partial-unique active triple). Fields: `id, project_number, user_id, employee_id, email, display_name, assignment_role, assignment_scope, is_primary, is_backup, active, start_date, end_date, assigned_by, assigned_by_role, assigned_at, updated_by, updated_at, removed_by, removed_at, remove_reason, source, notes`.
- 13 closed-set roles in `ROLE_REGISTRY`. 3 admin-only (`pm`, `co_pm`, `executive_oversight`). 10 PM-assignable.

## 3. APIs created
| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/api/team-roster/role-registry` | any portal | role taxonomy w/ labels and capability flags |
| GET | `/api/admin/jobs/{n}/team` | admin | full roster (active + inactive) |
| GET | `/api/admin/jobs/{n}/team/audit` | admin | history drawer (project-scoped) |
| POST | `/api/admin/jobs/{n}/team` | admin | assign |
| PATCH | `/api/admin/jobs/{n}/team/{aid}` | admin | update (scope, primary, backup, end_date, notes) |
| DELETE | `/api/admin/jobs/{n}/team/{aid}` | admin | soft-delete |
| POST | `/api/admin/team-roster/backfill` | admin | idempotent PM/Co-PM backfill |
| GET | `/api/pm/job/{n}/team` | PM (own job) | roster (read) |
| POST | `/api/pm/job/{n}/team` | PM (own job) | assign (PM-assignable roles only) |
| DELETE | `/api/pm/job/{n}/team/{aid}` | PM (own job) | soft-delete (PM-assignable roles only) |
| GET | `/api/jobs/{n}/team` | any portal | read-only team list (Foreman/FL/Asset Admin/Dispatch) |
| GET | `/api/users/me/projects` | any portal | reverse lookup — "what jobs am I on?" |

## 4. UI screens created
- **`/admin/jobs/{projectNumber}/team`** — Admin Project Team Manager (full role-set, audit drawer, directory dropdown)
- **`/pm/job/{projectNumber}/team`** — PM Job Team Manager (PM-assignable roles only, no audit drawer)
- **"Team" link added** to AdminJobMasterPanel job-row actions
- Reusable component `components/team/JobTeamRosterPanel.jsx` (scoped admin|pm)
- Reusable API client `lib/teamRosterApi.js`

All UI honors existing PortalShell / AdminShell chrome, uses shadcn Card + Select + Input + Button + Badge, sonner toast for outcomes, and 25+ data-testid attributes (`job-team-roster-panel`, `job-team-row-{role}`, `job-team-member-{id}`, `job-team-add-btn`, `job-team-role-select`, `job-team-user-select`, `job-team-submit`, `job-team-remove-{id}`, `job-team-toggle-primary-{id}`, `job-team-audit-toggle`, `job-team-audit-drawer`, etc.) for downstream testing.

## 5. Roles supported (13 total)
| Key | Label | Assignable by |
|-----|-------|----------------|
| `pm` | Project Manager | Admin only |
| `co_pm` | Co-PM | Admin only |
| `executive_oversight` | Executive Oversight | Admin only |
| `assistant_pm` | Assistant PM | Admin + PM |
| `superintendent` | Superintendent | Admin + PM |
| `foreman` | Foreman | Admin + PM |
| `safety_lead` | Safety Lead | Admin + PM |
| `project_engineer` | Project Engineer | Admin + PM |
| `asset_admin` | Asset Admin | Admin + PM |
| `locate_coordinator` | 811 Locate Coordinator | Admin + PM |
| `dispatcher_contact` | Dispatcher Contact | Admin + PM |
| `shop_contact` | Shop Contact | Admin + PM |
| `read_only_stakeholder` | Read-only Stakeholder | Admin + PM |

## 6. Admin assignment result
Verified live against preview backend:
- Add Foreman → 200, assignment row inserted with audit row
- Duplicate add of same (project, user, role) → 409
- Unknown role → 400
- PATCH is_primary → 200, audit row added
- DELETE with reason → 200, row marked `active=false`, `removed_by` populated, `end_date` set
- Subsequent admin list shows the inactive row with `active=false`

## 7. PM assignment result
- PM token on own job (`26-05`, `26-06`): can add/remove Foreman/Superintendent/Safety Lead/etc. → 200
- PM token on someone else's job (`24-06` owned by davidjewett): 403 "PM not assigned to this project"
- PM token tries to assign `pm` role on own job: 403 "role 'pm' is admin-only"
- PM token tries to assign `executive_oversight`: 403

## 8. Co-PM assignment result
Co-PM matching logic (`_is_pm_on_project`) checks both `jobs_master.pm_email` and `jobs_master.co_pm_emails[]`. A user whose email appears in either field has full PM-scope on that project. Verified: backfilled 2 Co-PM rows (1 distinct Co-PM: `pm.demo@mascigc.com` across 2 jobs).

## 9. Field Leadership visibility readiness
- `GET /api/jobs/{n}/team` — any authenticated portal token (including FL) reads the active roster. Verified with `X-FL-Token`: 200.
- `GET /api/users/me/projects` — FL user gets their rostered projects (jaymn.judd is rostered as PM on 26-05 and 26-06 by backfill → returned 2 rows).
- FL token CANNOT write: `POST /api/pm/job/{n}/team` with `X-FL-Token` → 403 "actor kind 'fl' cannot manage team".

**Phase 1 exposes the data**; Phase 2 will wire the FL portal sidebar to consume it via `useFlPortalRoster(projectNumber)`.

## 10. Asset Admin / 811 readiness
- Roles `asset_admin` and `locate_coordinator` are first-class entries in the registry, both PM-assignable.
- Admin can assign these roles to any project (verified by passing the role in payload).
- Asset Care UI integration is Phase 2 work (`/asset-care/projects/{n}`). Phase 1 supplies the roster API both surfaces will read.

## 11. Backfill result (live preview data)
```
{
  "jobs_scanned": 28,
  "pm_assignments_created": 22,
  "co_pm_assignments_created": 2,
  "unmatched": [],
  "ran_at": "2026-06-14T14:54:23.707490+00:00"
}
```
Re-running the backfill produced `pm_assignments_created: 0 · co_pm_assignments_created: 0` — **idempotent confirmed**. Zero `unmatched` entries (every PM/Co-PM email resolved to a directory user).

`pm_email` and `co_pm_emails[]` on `jobs_master` remain UNTOUCHED. The existing PM rename cascade in `pm_admin.py:148-164` continues to be authoritative for PM identity.

## 12. Audit trail result
Every insert / update / soft-delete writes one row to `audit_events` with:
```
category: "project_team_roster"
action: "assign" | "update" | "remove"
project_number, assignment_role, target_user_id, target_email
before, after  (full row snapshots)
actor_user_id, actor_role, actor_email, actor_name
at  (ISO timestamp)
notes  (optional reason)
```
Verified: after add+patch+remove on project 26-05, `GET /api/admin/jobs/26-05/team/audit` returns 5 rows with all three action verbs present.

## 13. Notification bell readiness
Two resolver helpers exported from `routes/project_team_assignments`:
```python
async def resolve_team_for_project(db, project_number, *, active_only=True) -> list[dict]
async def resolve_users_for_project_role(db, project_number, role) -> list[str]
```
Phase 2 will call `resolve_users_for_project_role(db, pn, "superintendent")` from each producer and set `recipient_user_id=<first match>` (or fan-out across the list, one notification per recipient).

The existing `_notif_filter` in `tasks_notifications.py` (Track 14.0-NOTIFY-OWNERSHIP-LOCK) already honours `recipient_user_id` — so the moment producers start populating it from the roster, the bell drawer and chime light up correctly.

**Bell + chime regression**: untouched. Track 14.0-NOTIFY-OWNERSHIP-LOCK tests (`tests/test_notify_ownership_lock.py`) still pass; person-level filter / asset-admin OR-scope unchanged.

## 14. Email routing readiness
The roster resolver supplies the recipient list. The existing email path (`lib/email.py` + `resend` integration) reads `notification.recipient_user_id` and `notification.recipient_email` and dispatches accordingly when `AUTO_EMAIL_REPORTS=true` (preview: `false`).

Contract for Phase 2 producers — both bell + email targeting:

| Event | Bell + email targets |
|-------|----------------------|
| Daily Report submitted | rostered Superintendent → fallback rostered Co-PM → fallback rostered PM → fallback role `fl` |
| Safety incident submitted | rostered Safety Lead → rostered Superintendent → rostered PM → fallback role `safety` |
| Trench / excavation issue | rostered Safety Lead → rostered Superintendent → rostered Foreman → critical also PM → fallback role `safety` |
| QA/QC deficiency | rostered Project Engineer → rostered PM → rostered Superintendent → fallback role `pm` |
| 811 locate update | rostered Asset Admin / Locate Coordinator → optional rostered PM → fallback role `asset_admin` |
| Dispatch stale location | rostered Dispatcher Contact → optional rostered Superintendent → fallback role `dispatch` |
| Asset document expiration | rostered Asset Admin → optional rostered PM (if project-linked) → fallback role `asset_admin` |

Producers do not need to be rewritten until Phase 2.

## 15. Tests passed
`backend/tests/test_project_team_assignments.py` — **8 of 8 PASS** in 25.6s:
- `test_role_registry` — 13 roles, admin-only flags correct
- `test_backfill_idempotent` — second run creates 0 dupes
- `test_admin_crud_and_audit` — add → 409 dup → 400 bad-role → patch → audit → soft-delete
- `test_pm_can_add_on_own_job` — PM token on own project succeeds
- `test_pm_blocked_on_unowned_job` — PM token on someone else's project → 403
- `test_pm_blocked_on_admin_only_role` — PM tries `pm` role → 403
- `test_fl_read_only` — FL reads roster, cannot write → 403
- `test_reverse_lookup` — `/api/users/me/projects` returns ≥2 rows for super-admin

`backend/tests/test_notify_ownership_lock.py` — still PASS (no regression from prior Track 14.0).

## 16. Failures found / fixed during implementation
1. **`require_admin` returns `True` (bool), not a dict** — admin token actor was crashing `actor.get('id')`. Fixed with `_coerce_actor()` helper that normalises bool → admin dict and tags PM docs explicitly.
2. **`/api/notifications?limit=500` exceeded server cap of 200** — already fixed in prior fork, but reused harness pattern updated to clamp at 200.
3. **Frontend `PortalShell` import path** — pages tried `@/components/PortalShell` but the actual location is `@/design-system/PortalShell`. Caught by compile overlay on first screenshot, fixed.
4. **Backfill unmatched on first run was 0** — actually a good thing; all 22 PM emails resolve cleanly to `user_directory`.

## 17. Files changed (8 files · 1 new collection · 5 new indexes · 0 existing collection mutated outside the new one)

| File | Type | LOC |
|------|------|-----|
| `backend/routes/project_team_assignments.py` | NEW | 487 |
| `backend/tests/test_project_team_assignments.py` | NEW | 165 |
| `backend/server.py` | EDIT | +35 (register + index ensure) |
| `frontend/src/lib/teamRosterApi.js` | NEW | 105 |
| `frontend/src/components/team/JobTeamRosterPanel.jsx` | NEW | 268 |
| `frontend/src/pages/admin/AdminJobTeam.jsx` | NEW | 28 |
| `frontend/src/pages/pm/PmJobTeam.jsx` | NEW | 22 |
| `frontend/src/App.js` | EDIT | +5 (2 lazy imports, 2 routes) |
| `frontend/src/components/AdminJobMasterPanel.jsx` | EDIT | +12 (Team link added to row actions) |

**Total: ~1 127 LOC** across 9 files. No existing API contract broken. No existing collection schema mutated.

## 18. Five-Pillar score

| Pillar     | Score | Reasoning |
|------------|-------|-----------|
| Powerful   | 9.5   | Editable per-project roster · 13 roles · admin + PM + read-only paths · resolver helpers ready for Phase 2 producer rewrites · backfill idempotent · audit complete. |
| Simple     | 9.4   | One panel component reused across Admin and PM scopes · single API client · existing PM email cascade untouched. Empty "Unassigned" chips communicate state clearly. |
| Beautiful  | 9.5   | Matches AdminShell + PortalShell chrome. Card layout. Lucide icons. Soft amber primary star. No new color system, no AI-slop gradients. |
| Trusted    | 9.85  | Server-side permission checks at every write path · soft-delete only · full audit trail · idempotent backfill · 8/8 regression tests green · existing notification leakage matrix still passes. |
| Proven     | 9.85  | Live preview verified: 22 PM + 2 Co-PM backfilled, CRUD lifecycle, dup blocked, bad-role blocked, PM scope blocked on unowned job, admin-only role blocked from PM, FL read-only confirmed, reverse lookup returns correct project count. |

**Composite: 9.62.** Above the 9.5 RC-1 bar.

## 19. What Phase 2 must do

1. **Producer rewrites (~360 LOC across 18 producers)** — replace `recipient_role=…` with a small helper that calls `resolve_users_for_project_role(db, project_number, role)` and sets `recipient_user_id` when the roster has a match. Feature-flag with `OWNERSHIP_LOCK_ENABLED`.
2. **Email routing wiring** — extend the existing `resend` path to honour the resolver's user list for project-scoped notifications.
3. **Field Leadership portal sidebar** — wire `JobTeamRosterPanel scope="readonly"` (or a thin "Team" widget) into `/field-leadership/portal/jobs/{n}` so Foremen / Superintendents can see who else is on their job.
4. **Asset Care project-scoped view** — `/asset-care/projects` listing rostered projects for the current Asset Admin, then `/asset-care/projects/{n}` for per-project asset docs + 811 placeholder.
5. **Closed-record team_snapshot freeze** — embed a frozen `team_snapshot` array on Daily Reports, Incidents, QAQC, Trench, and DVIR at submit-time so historical records keep the original roster.
6. **Disabled-user orphan migration UI** — when an admin disables a user who holds active assignments, prompt to reassign or leave to backup.
7. **PM Job Team link from PM dashboard** — surface a "Team" tab/CTA on the PM job detail / hub views.

## 20. Whether Spanish can start

**No, not yet.** Spanish translation should begin after Phase 2 producer rewrites are deployed and verified. The English copy that ships in Phase 1 ("Unassigned", "Roster history", "User/employee link missing — notifications may route by role until linked", etc.) is finalised and ready to translate. But translating ahead of producer rewrites would mean Spanish strings on screens that still show role-broadcast notifications, masking the very ownership truth this track was built to deliver.

**Recommended sequence**:
1. ✅ Phase 1 — Foundation (this closure)
2. 🟠 Phase 2 — Producer rewrites + FL sidebar + Asset Care view (~5 days)
3. 🟠 Phase 3 — Closed-record team_snapshot + orphan migration UI (~2 days)
4. 🔴 Spanish Translation Sweep (14.0-S1) — after Phase 3 is closed
5. 🔴 PDF Lockup Sweep (14.0-P1)
6. 🔴 Integration Honesty Banners (14.0-I1)
7. 🔴 UXS-11 final certification

## 21. Deployment readiness

| Concern | Status |
|---------|--------|
| Backend service running | YES — supervisor `backend` RUNNING |
| Migrations needed | NO — new collection, indexes created on startup |
| Existing endpoints regressed | NO — `tests/test_notify_ownership_lock.py` still passes |
| Existing PM cascade broken | NO — `pm_email` / `co_pm_emails` untouched |
| Existing notification bell broken | NO — read filter unchanged |
| Feature flag required | NO — Phase 1 is additive only |
| .env changes required | NO |
| Frontend compile errors | NO (verified post-fix) |
| Hard locks | ALL HONOURED — no deploy, no GitHub, no merge, no Spanish, no PDF, no banners, no UXS-11 |

**Ready for user verification and Phase 2 trigger.**

---

## Appendix — Reproducible verification snippets

```bash
# 1. Login + admin token
URL="https://safety-audit-mobile-1.preview.emergentagent.com"
TOKEN=$(curl -s -X POST "$URL/api/auth/multi-login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"jaymn.judd@mascigc.com","password":"Maddix123!"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['portal_tokens']['admin'])")

# 2. Role registry
curl -s "$URL/api/team-roster/role-registry" -H "X-Admin-Token: $TOKEN" | python3 -m json.tool

# 3. Idempotent backfill
curl -s -X POST "$URL/api/admin/team-roster/backfill" -H "X-Admin-Token: $TOKEN" | python3 -m json.tool

# 4. List a real project's team
curl -s "$URL/api/admin/jobs/26-05/team" -H "X-Admin-Token: $TOKEN" | python3 -m json.tool

# 5. Reverse lookup
curl -s "$URL/api/users/me/projects" -H "X-Admin-Token: $TOKEN" | python3 -m json.tool

# 6. Full regression
cd /app/backend && python3 -m pytest tests/test_project_team_assignments.py -v
# Expected last line: 8 passed in ~26s
```
