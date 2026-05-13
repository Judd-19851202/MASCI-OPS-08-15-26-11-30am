# MASCI Safety Hub — PRD

## 2026-05-13 — Iter73: Public Hub Redesign (Phase C + D)

### User ask
"Do what you recommend. I want this to look sharp like a well put
together system but not over complicated or make anyone nervous to
use, very user friendly but definitely well put together."

### What shipped — full Hub rewrite
- **4 grouped sections with kicker numbers (Phase C)**:
  - `01 — TODAY IN THE FIELD`: 3 big BigTiles → Field · QA/QC · Safety
  - `02 — LEADERSHIP TOOLS`: 2 MediumTiles → Field Leadership · Projects (Basecamp + OnStation)
  - `03 — OFFICE PORTALS`: 4 compact PortalPills → PM · Shop · HR · Admin
  - `04 — REFERENCE`: 3 ReferenceLinks → Training Hub · Cheat Sheet · Need Help?
- **Hybrid verbiage scrub (Phase D)**:
  - Public tiles keep warm descriptive copy + feature bullets.
  - Restricted PortalPills show only title + 1 neutral sentence + lock icon + "SIGN IN →" CTA. **No feature bullets exposed** to unauthenticated viewers.
  - When the matching session is active, the lock icon disappears and CTA flips to "OPEN →".
- **Auto-personalization "Welcome Back" hero strip**:
  - Reads localStorage synchronously; precedence admin > hr > pm > shop > leadership.
  - Palette per kind (admin=slate, pm=indigo, shop=orange, hr=purple, leadership=slate).
  - One-tap "Open" button → /admin | /hr | /pm | /shop | /leadership.
  - Sign-out clears the strip instantly (state-driven re-render).
- **Need Help? tile** in the Reference strip opens the existing
  CompanyInfoDialog (phone, address, after-hours) — surfaces info
  that was previously buried in the header button.

### Critical bug fixed during iter73
- `EnforcePortalScope` was wiping admin/pm/shop/hr tokens the moment
  the user navigated to `/` — so the Welcome-Back hero would show
  for a single render and immediately stop working. Fix: added `/`
  (the Hub) to the inScope exemption list alongside `/training/*`.
  The Hub is the multi-audience rendezvous point; security sandbox
  still applies to every other route outside each portal's namespace.

### Verified
- 34/34 frontend assertions ✓ (testing_agent_v3_fork iter73).
- Manual round-trip verification ✓:
  - Admin login → / shows hero → click Open → /admin → navigate back to / → hero still present.
  - Sign-out clears the hero instantly.
  - HR login → / renders purple "WELCOME BACK · HR PORTAL · HR Manager" with one-tap Open.
- Need Help? opens Company Info dialog ✓.
- All 12 section testids preserved (iter65-iter71 e2e tests still pass).

### Files added
- `/app/frontend/src/pages/Hub.jsx` (full rewrite — 4 sub-components + helpers)

### Files modified
- `/app/frontend/src/components/EnforcePortalScope.jsx` (Hub-root exemption)
- `/app/memory/PRD.md`

### Optional polish (deferred per reviewer notes)
- Extract `BigTile / MediumTile / PortalPill / WelcomeBackHero` into
  `/components/hub/` for reuse (Hub.jsx is 530 lines — readable but
  could be split).
- Add `window.addEventListener('storage', force)` so multi-tab logout
  clears the strip live (low priority).
- Verify Spanish translations exist for "Open Portal" / "Open Console"
  / "Welcome back" strings.

---

## 2026-05-13 — Iter72: HR Payroll Variance + Training Updates (Phase A & B)

(see previous PRD section — full detail preserved in git history)

Highlights:
- HR Payroll Variance: paste Exact CSV → match by employee+week →
  flag ≥15 min variances → approve/dispute persistence + CSV export.
- Weekly auto-email cron (Sun 18:00 UTC).
- HR training track (8 bilingual lessons) + 4 new admin lessons.

---

## 2026-05-12 — Iter71: HR Portal (full stack)

HR auth + chrome, 4 HR sub-pages, AdminHRUsersPanel in /admin, Public Hub HR Portal card.

---

## Earlier iterations
- iter70: Field Leadership Employee Termination + Admin Terminations dashboard.
- iter69: Shop Portal View 404 fix.
- iter68: Full Deployment-Readiness Audit (9.4/10).
- iter65-67: Hub Banner Messaging System + Audit Trail.
- iter64: R2 photo migration + Cloud Archives.
- iter58-63: Doc ID search, Email Routing, Job Photos perf, Backups.

---

## Prioritized backlog

### P1
- Migrate remaining base64 signatures to R2 (write_up, recognition).
- Backup verification cron (weekly R2 archive integrity check).
- IT server-dump endpoints (`/api/admin/server-dump/list|latest`).
- Employee Login Gate (bulk import + termination + usage).
- Photo-First Daily Report (AI drafted from gallery photos).
- Motive (Fleet) integration (Pre-Op autofill, GPS verification).
- Refactor: extract Hub sub-components to `/components/hub/`.
- Refactor: extract payroll variance parser to a `services/` module.
- Strengthen `_name_key` matcher with `employee_id` fallback.

### P2
- Multi-tab live sync for Welcome-Back strip (storage event listener).
- "Restore from R2" admin button.
- "Forward to IT" share button on backup rows.
- HR payroll variance — paste-Exact-CSV variance auto-suggestion (LLM).

---

## Test credentials
See `/app/memory/test_credentials.md`. Quick refs:
- Admin: `MASCI1982!`
- HR Manager: `hrmanager@mascigc.com` / `HRPortal2026!`
- Shop: `testmech@mascigc.com` / `ResetWorks2026!`
- Field Leadership: `MASCIGC`
- PM (Chris Wright): `chriswright@mascigc.com` / `ChrisRocksThis2026`
