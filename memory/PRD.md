# MASCI Safety Hub — PRD

## 2026-05-12 — Iter71: HR Portal (full stack)

### User ask
"Carry on with P0 & Admin HR Users panel (admin can add/reset HR
passwords — backend exists, no UI yet)" — completing the HR Portal
work that was 80% done at the iter71 handoff.

### What shipped (frontend completion)

**HR auth + chrome**
- `RequireHr.jsx` — gates `/hr/*` routes (admin token does NOT satisfy).
- `EnforcePortalScope` extended to clear `masci.hr.token` on
  navigation outside `/hr/*` (mirrors PM/Shop/Admin isolation).
- `tokenValidation.js` calls `/api/hr/me` so a rotated password drops
  the stale HR token on next page load.
- `HrPageShell.jsx` shared header + sign-out + back-link chrome.

**HR pages**
- `HrLogin.jsx`, `HrChangePassword.jsx`, `HrResetPassword.jsx`,
  `HrForgotPassword.jsx` — full self-service auth lifecycle.
- `HrHub.jsx` — 4 fully-clickable tile cards (post-iter71 fix):
  Field Leadership Records · Employee Accountability ·
  Time Verification · Training Records.
- `HrTimeVerification.jsx` — weekly cross-check view. Filters
  (week_ending, employee, project_number, supervisor) + stats strip
  (employees, total hours, regular, overtime — overtime row turns
  amber). Toggle Weekly Rollup ↔ Per-Day Detail. CSV export.
- `HrFieldLeadership.jsx` — read-only list with kind filter + search.
  Per-row View drawer (renders all detail fields) + PDF download.
- `HrEmployeeAccountability.jsx` — search by name → consolidated
  counts (FL records · active write-ups · outstanding equipment ·
  trainings) + by-kind chip strip + outstanding-equipment table
  (red-bordered "must be recovered before offboarding") + FL records
  + training records tables.
- `HrTrainingRecords.jsx` — training compliance roster with empty
  state since `training_track_records` is empty in preview.

**Admin HR Users management**
- `AdminHRUsersPanel.jsx` mounted in `/admin` between Shop Console
  and Auto-Email Routing. Add user · edit · disable · delete · issue
  password (Show on Screen / Email to User / Custom). Uses purple
  accent to match HR scope. Always-email default sends Resend welcome
  with login URL + temp password.

**Public Hub**
- `Hub.jsx` now exposes an "HR Portal" section card linking to
  `/hr/login` so HR managers can self-discover the portal.

### Backend (already shipped, verified again this iter)
- `/api/hr/login` · `/api/hr/me` · `/api/hr/change-password` ·
  `/api/hr/forgot-password` · `/api/hr/reset/{token}`
- `/api/hr/field-leadership` (+ `/{id}` + `/{id}/pdf`)
- `/api/hr/employee-accountability`
- `/api/hr/time-verification` (+ `.csv`)
- `/api/hr/training-records`
- `/api/admin/hr-users` full CRUD (admin-strict)
- Seeded HR Manager (`hrmanager@mascigc.com`) — admin issued
  `HRrocks2026!` temp → user rotated to `HRPortal2026!` during this
  iter's smoke test.

### Verified end-to-end
- 21/21 iter71 pytest cases pass (`test_hr_portal_iter71.py`).
- Frontend Playwright (testing agent v3 + main agent smoke):
  - Sign-in → must-change-password gate → HR Hub renders all 4
    tiles → tile cards are fully clickable (post-fix).
  - Time Verification renders filters + stats + toggle + empty
    state correctly when no DR rows in window.
  - Field Leadership Records returns 5+ items from seed data.
  - Employee Accountability returns counts + by-kind + outstanding
    equipment for a known seed name.
  - Training Records empty state renders cleanly.
  - RequireHr redirects unauthenticated `/hr` → `/hr/login`.
  - EnforcePortalScope wipes HR token when navigating to `/`.
  - AdminHRUsersPanel mounted between Shop Users and Auto-Email
    Routing with full Add → Edit → Reset password → Delete lifecycle.

### Files added
- `/app/frontend/src/components/RequireHr.jsx`
- `/app/frontend/src/components/HrPageShell.jsx`
- `/app/frontend/src/components/AdminHRUsersPanel.jsx`
- `/app/frontend/src/pages/HrChangePassword.jsx`
- `/app/frontend/src/pages/HrResetPassword.jsx`
- `/app/frontend/src/pages/HrForgotPassword.jsx`
- `/app/frontend/src/pages/HrTimeVerification.jsx`
- `/app/frontend/src/pages/HrFieldLeadership.jsx`
- `/app/frontend/src/pages/HrEmployeeAccountability.jsx`
- `/app/frontend/src/pages/HrTrainingRecords.jsx`
- `/app/backend/tests/test_hr_portal_iter71.py`

### Files modified
- `/app/frontend/src/App.js` (HR routes + RequireHr import)
- `/app/frontend/src/lib/tokenValidation.js` (HR `/me` check)
- `/app/frontend/src/components/EnforcePortalScope.jsx` (HR scope)
- `/app/frontend/src/pages/AdminHub.jsx` (mount AdminHRUsersPanel)
- `/app/frontend/src/pages/Hub.jsx` (HR Portal section card)
- `/app/frontend/src/pages/HrHub.jsx` (post-test fix: tiles are
  now full `<Link>` cards, not divs with an inner Open anchor)
- `/app/memory/test_credentials.md` (HR Portal section added)

### Production deploy
"Save to GitHub → Deploy". After deploy, the HR Manager logs in at
`mascidocs.com/hr/login` with `hrmanager@mascigc.com` /
`HRPortal2026!`, lands on the HR Hub, and can immediately cross-check
the current week's payroll against supervisor-reported Daily Report
hours. Admins manage HR rosters from `/admin → HR Users & Logins`.

---

## Previous iterations
- iter70: Field Leadership Employee Termination form + Admin
  Terminations dashboard. Supervisor Notes tile removed.
- iter69: Shop Portal "View inspection does nothing" 404 fix
  (`compute_pm_scope` honors `_actor_kind=shop_user`).
- iter68: Full Enterprise Deployment-Readiness Audit (scored 9.4/10).
- iter67: Banner Audit PDF/CSV/Clone/Archive toggle.
- iter66: Banner Audit Trail (per-ack/dismiss IP+UA log).
- iter65: Hub Banner Messaging System (9 templates, ack-gate,
  auto-Spanish via Claude Haiku 4.5).
- iter64: R2 photo migration GO-LIVE + Cloud Archives admin panel +
  complete-system nightly archive to R2 + blank-photo regression
  fix on every View page.
- iter63: Backup hardening (preflight, watchdog, supervisor task).
- iter62: Backup resiliency (lite mode escape hatch).
- iter61: Training docs full sweep (iter48–60 features).
- iter60: Admin Email Routing console (DB-backed overrides).
- iter59: Job Photos thumbnail concurrency + auto-warm scheduler.
- iter58: System Audit log + Doc ID search.
- earlier: see legacy PRD entries.

---

## Prioritized backlog (next tasks)

### P1
- **Admin HR Users panel — Email-on-create + welcome HTML**: currently
  the panel always sends Resend welcome on Add. Double-check copy +
  add a "Copy join link" affordance.
- **Migrate remaining signatures to R2** (write_up, recognition, etc.
  still store base64 sig images in Mongo — large rows).
- **Backup verification cron** — weekly check that the previous 7
  nightly R2 archives exist + are openable; alarm email if not.
- **IT server dump endpoints** — `GET /api/admin/server-dump/list`
  and `latest` so IT can pull a complete-system zip without going
  through Cloudflare R2.
- **Employee Login Gate** — wrap the entire site in a login gate with
  bulk employee import, termination, and usage tracking.
- **Photo-First Daily Report** — AI drafts a report based on the
  gallery photos for the job.
- **Motive (Fleet) integration** — Pre-Op autofill from Motive odometer
  + GPS verification of supervisor location.

### P2
- "Restore from R2" admin button (manual pick of any archive zip)
- "Forward to IT" share button on a backup row (presigned URL +
  email composer)
- HR — payroll variance ingestion: paste Exact CSV → diff vs.
  supervisor-reported hours, surface variance % flags.

---

## Test credentials
See `/app/memory/test_credentials.md` for the full list. Quick refs:
- Admin: `MASCI1982!`
- HR Manager: `hrmanager@mascigc.com` / `HRPortal2026!`
- Shop: `testmech@mascigc.com` / `ResetWorks2026!`
- Field Leadership: `MASCIGC`
- PM (Chris Wright): `chriswright@mascigc.com` / `ChrisRocksThis2026`
