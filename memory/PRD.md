# MASCI Safety Hub — PRD

## 2026-05-13 — Iter77: Crew Cheat Sheet → "Field Card" Redesign

### User ask
Uploaded `Cheat Sheet Issues.pdf` requesting the printable Crew Cheat
Sheet be redesigned to reflect the full 5-portal MASCI Hub (not just
the legacy safety-only flow) and remove the hardcoded
`safety@mascigc.com` email.

### What shipped
- **`CheatSheetCard.jsx` full rebuild**:
  - Re-titled "MASCI Operations Platform · Field Card" (legacy was
    "Crew Cheat Sheet · Field Safety Reporting Portal").
  - **3 Submission tiles** (public, no sign-in): Field · QA / QC · Safety.
  - **4 Office Portal pills** (sign-in required): PM · Shop · HR ·
    Field Leadership — matches the iter73 Hub redesign exactly.
  - Removed `safety@mascigc.com` everywhere. Office phone-only
    contact (386-322-4500).
  - Footer standardized to "MASCI Operations Platform · Powered by
    ForgedOps™" (matches iter74 / iter76 brand standard).
  - "Stop-the-Line · Accidents & Injuries" 4-step protocol preserved.
  - "Tips for Everyone" expanded (ES toggle · 6-photo rule · Doc ID
    tracking · Pre-Op FAIL auto-emails · home-screen install).
  - Training Hub + Need Help mini-strip retained.
- Verified visually at `/cheatsheet`: layout responsive, branding
  correct, all 5-portal verbiage present.

### Files touched
- `/app/frontend/src/components/CheatSheetCard.jsx` (rewrite)

---

## 2026-05-13 — Iter77b: 48-Hour Regression Sweep ("15/10 Polish Check")

### User ask
"Run through all changes done in last 48 hours, verify everything works,
no bugs no issues, don't overlook things. Site needs to run extremely
FAST, SMOOTH, look AMAZING, flow & have everything work with ZERO
issues. Needs to work on all computers & browsers, all mobile devices."

### What was verified
- **All 5 portals login cleanly**: Hub (public), HR, PM, Shop, Admin,
  Field Leadership — every login page renders + footer present.
- **Hub `/`**: TTFB 200ms, full load 1,169ms (desktop). Hero banner +
  audience-grouped sections + all tiles render with `data-testid`.
  Zero console errors.
- **Cheat Sheet `/cheatsheet`**: All 4 office portal pills + 3
  submission tiles render. `safety@mascigc.com` REMOVED globally.
  ForgedOps™ footer present. Print button reachable.
- **HR Portal `/hr`**: All 5 tiles render after login (Field Leadership
  Records, Employee Accountability, Time Verification, Training
  Records, Payroll Variance). Cross-portal isolation confirmed —
  HR token returns 401 on `/api/admin/jobs`.
- **Payroll Variance**: Real Exact CSV upload returns variance items
  with daily-report cross-check.
- **Signature R2 Migration**: 4/54 daily reports carry signatures —
  ALL stored as `photo://masci-hub/...` references. Zero base64
  data: URLs detected in any signature field across the entire
  collection. Migration is clean and complete.
- **Legal pages `/legal/terms` + `/legal/privacy`**: All iter76
  hardening sections verified (Trademarks · Platform Availability
  · Notifications · Automated/AI Features · Compliance · Cloudflare
  R2 · OSHA · DOT · FAA · FMCSA · GDPR · CCPA).
- **Public submission still works**: Daily Report POST + Equipment
  Pre-Op POST both accept under preview-creds.
- **Mobile 390×844**: No horizontal scroll on Hub. Layout collapses
  cleanly.
- **Backend test suite**: 22/24 passed. The 2 "failures" were both
  test-infrastructure artifacts (conftest auto-injects admin token;
  legacy tests assumed a non-existent `/api/daily-reports/{id}/pdf`
  endpoint). Neither represents a real regression.

### False positives identified in iter77 report
1. **"ForgedOps footer missing"** — agent searched DOM `innerText` for
   mixed-case "MASCI Operations Platform", but the footer uses CSS
   `text-transform: uppercase`. The rendered text is "MASCI OPERATIONS
   PLATFORM". Footer was always present (re-verified case-insensitive
   on 8 pages — all PASS).
2. **"Privacy missing Trademarks heading"** — by spec, §2A Trademarks
   lives in Terms, not Privacy. Privacy correctly omits the heading.

### Files touched
- `/app/test_reports/iteration_77.json` (regression report)
- `/app/backend/tests/test_iter77_regression.py` (added by testing agent)

### Outcome
**System is regression-clean. No P0/P1 issues. Ready for next P1 stream.**

---

## 2026-05-13 — Iter78: Email Chrome Cleanup ("Daily Report ≠ Safety Record")

### User ask
Photo of a Daily Report email showed three issues:
1. Body eyebrow read "MASCI · SAFETY RECORD" — wrong for a Daily Report.
2. Raw HTML leaking as literal text: `<p>Auto-routed to <b>Ramon</b>...</p>`.
3. Hardcoded `safety@mascigc.com` in visible footer chrome.
"Platform has grown beyond a safety only thing. Emails should state
what they are, look clean & professional."

### What shipped
- **`pdf_render.py · render_email_html`** rewritten chrome:
  - Eyebrow: `MASCI · Safety Record` → **`MASCI Operations Platform`**
    (record-type-agnostic; the H1 below already names the kind).
  - Body line: "The full safety record is attached as a PDF." →
    **`The full {KIND_TITLES[kind]} is attached as a PDF.`** —
    record-aware ("Daily Job Report" / "QA / QC Inspection" /
    "Equipment Pre-Op Inspection" / "Accident / Incident Report" /
    "Site Inspection Report" / "Site Safety Meeting" / "Job Hazard Plan").
  - Footer: dropped visible `safety@mascigc.com` → now
    **`MASCI General Contractors · 386-322-4500 · mascidocs.com`**
    with a second line **`Powered by ForgedOps™`** matching the
    iter74/77 brand standard.
  - Auto-detects WARN tone (notes starting with SEVERE / EQUIPMENT
    FAIL / WARN / ⚠) and switches the callout box from neutral slate
    to **red on red-50** with bold weight.
- **`server.py` auto-route note constructor** rewritten — all four
  branches (severe incident, equipment fail, PM-resolved, no-PM) now
  build the note as **plain text** instead of HTML strings. Combined
  with the existing `escape(note)` in render_email_html, the result
  is clean readable text in every email client. No more leaking
  `<p>` / `<b>` tags.
- **Distribution routing unchanged**: emails still get sent to
  `safety@mascigc.com` per `email_routing.py` (that's a real inbox,
  not visual chrome). Only the visible body chrome was cleaned up.

### Verification
- 13 backend assertions PASS (no safety email in chrome, MASCI Operations
  Platform eyebrow, record-aware body line, ForgedOps footer, no
  literal HTML in note, warn-tone red bg on EQUIPMENT FAIL/SEVERE,
  qaqc title swap renders correctly).
- Two sample HTML emails rendered + screenshotted via Playwright —
  both render clean, professional, mobile-readable.

### Files touched
- `/app/backend/pdf_render.py` — `render_email_html()`
- `/app/backend/server.py` — auto-email note constructor (line 8444)

---

## 2026-05-13 — Iter82: Multi-Portal Access Control Center

### User ask
"A few people in our org need login across multiple portals — let
certain people have access to multiple portals with the same login.
Keep existing passwords intact (no resets). Admin would get email +
password too. Add a dashboard to see/manage who has what."

### Decisions made (with user "go with your picks")
- **Seeded super-admin** (not hardcoded backdoor) — bcrypt-stored,
  rotatable from admin panel, auditable.
- **bcrypt from day 1** — `Maddix123!` is what bcrypt hashes; no grace
  period plaintext fallback needed.
- **Full audit log** — logins (success + failed), portal switches,
  directory mutations, password resets all recorded.
- **Launch with just Jaymn** (`jaymn.judd@mascigc.com / Maddix123!`,
  all 4 portals, super-admin flag).

### What shipped
**Backend:**
- `/app/backend/user_directory.py` — Core module: bcrypt-12 password
  hashing, public_view serializer (no _id / no password_hash leakage),
  CRUD with super-admin protection (can't delete/disable, admin portal
  locked on), audit log writer, directory session token store with
  12h server-side TTL, bootstrap_super_admin (idempotent — runs at
  startup, top-ups portals if new types added later).
- `/app/backend/routes/auth_directory_routes.py` — 8 endpoints:
  - Public: `POST /api/auth/multi-login`, `POST /api/auth/multi-logout`,
    `GET /api/auth/me-directory`, `POST /api/auth/issue-portal-token`,
    `POST /api/auth/change-master-password`.
  - Admin-strict: `GET /api/admin/directory`, `POST /api/admin/directory`,
    `PATCH /api/admin/directory/{id}`, `DELETE /api/admin/directory/{id}`,
    `POST /api/admin/directory/{id}/reset-password`, `GET /api/admin/audit`.
- `server.py` — Wires the router with 4 portal-token minters that
  bridge directory user → existing per-portal token systems (admin uses
  env-derived format; pm/shop/hr look up by email in their collections).
  Mints `None` gracefully when no per-portal record exists.
- `/app/backend/.env` — Added `SUPER_ADMIN_EMAIL` +
  `SUPER_ADMIN_BOOTSTRAP_PASSWORD`. Email stays in env for future
  bootstrap top-ups; password becomes irrelevant after first deploy
  (the bcrypt hash on the directory row is authoritative).

**Frontend:**
- `/app/frontend/src/lib/directoryAuth.js` — localStorage helpers +
  `applyMultiLoginResponse()` that fans out per-portal tokens into the
  existing admin/pm/hr/shop token stores so all the existing API
  middleware "just works" with zero changes.
- `/app/frontend/src/pages/SignIn.jsx` — New `/sign-in` route. Master
  password sign-in with eye-toggle, Remember Me, 90s timeout, error
  mapping, MASCI Operations Platform branded chrome, single-portal
  sign-in links at the bottom for normal employees.
- `/app/frontend/src/components/PortalSwitcher.jsx` — Dropdown widget
  that auto-hides when a user has 0 or 1 portals. Shows colored dots
  per portal, marks the current one as disabled, jumps to the other
  hub with zero re-auth (existing per-portal tokens still valid).
- `/app/frontend/src/components/AdminAccessControlPanel.jsx` —
  Full management table: per-row portal checkboxes (toggle to
  PATCH directory), super-admin badge + locked admin checkbox, disable
  toggle, delete button, key-icon reset-password button (generates
  secure random, auto-copies to clipboard, shows in 30s toast).
  Includes a "Add user" dialog with portal checkboxes, generate-
  password button, and `must_change_password=true` enforced for newly
  created accounts.
- Mounted PortalSwitcher in `/admin`, `/pm`, `/shop`, `/hr` headers.
- Mounted AdminAccessControlPanel in `/admin` System Recovery section.
- Added "Sign in" link to the public Hub header (desktop only).

### Why this design
- **Additive, not destructive** — every existing per-portal login URL
  (`/admin/login`, `/pm/login`, `/hr/login`, `/shop/login`) keeps
  working unchanged. Single-portal employees see zero change. Rollback
  = delete `user_directory` collection + remove `/sign-in` route.
- **No password resets** — existing PM/HR/Shop password hashes are
  untouched. Multi-login bridges into them via per-portal lookups.
- **No env-stored passwords after bootstrap** — bcrypt hash on the
  directory row is the source of truth; bootstrap env var only used on
  the very first deploy. Rotate from `/admin` after that.
- **Super-admin can never lock itself out** — the directory bootstrap
  is idempotent and tolerant; the row is protected from delete/disable;
  and `is_super_admin` flag has admin portal locked on permanently.

### Verification
- Backend smoke test (curl): multi-login with `Maddix123!` returns
  `ok=true`, `session_token`, `portal_tokens={admin: <token>, pm: null,
  shop: null, hr: null}`. Admin token works against `/api/admin/jobs`.
  Bad password → 401 "Invalid email or password." Unknown email →
  same 401. Audit log records both successes and failures.
- E2E Playwright test:
  - `/sign-in` form renders, eye toggle works, Remember Me styled,
    ForgedOps™ footer present.
  - Submit with Maddix123! → lands on `/` (Hub).
  - `localStorage["masci.directory.token"]` set; `["masci.adminToken"]`
    set; user payload has all 4 portals.
  - `/admin` page: PortalSwitcher dropdown trigger visible.
  - Dropdown opens: shows "SUPER ADMIN · ACCESS" label, Admin Console
    marked Current (disabled), HR / PM / Shop entries clickable with
    colored dots.
  - AdminAccessControlPanel renders: Super Admin row with shield icon,
    all 4 portal checkboxes checked, admin checkbox locked (disabled).

### Files touched
- `/app/backend/user_directory.py` (NEW)
- `/app/backend/routes/auth_directory_routes.py` (NEW)
- `/app/backend/server.py` (mount + 4 portal-token minters +
  bootstrap startup hook)
- `/app/backend/.env` (SUPER_ADMIN_EMAIL + SUPER_ADMIN_BOOTSTRAP_PASSWORD)
- `/app/frontend/src/lib/directoryAuth.js` (NEW)
- `/app/frontend/src/pages/SignIn.jsx` (NEW)
- `/app/frontend/src/components/PortalSwitcher.jsx` (NEW)
- `/app/frontend/src/components/AdminAccessControlPanel.jsx` (NEW)
- `/app/frontend/src/App.js` (mount /sign-in route)
- `/app/frontend/src/pages/Hub.jsx` (Sign in link in header)
- `/app/frontend/src/pages/AdminHub.jsx` (PortalSwitcher + panel mount)
- `/app/frontend/src/pages/PmHub.jsx` (PortalSwitcher mount)
- `/app/frontend/src/pages/ShopHub.jsx` (PortalSwitcher mount)
- `/app/frontend/src/pages/HrHub.jsx` (PortalSwitcher mount)

---


## 2026-05-13 — Iter81: Cross-Portal Email Chrome Parity (PM + Shop + HR)

### User ask
"Make everything the same" — PM + Shop welcome/reset emails were using
the older bare-HTML chrome (dark navy header bar, "MASCI Hub · PM
Portal" eyebrow, grey footer line). Bring them up to the iter78/80
standard the rest of the platform uses.

### What shipped
**New shared module** — `/app/backend/branded_portal_emails.py`:
- `render_portal_email(portal, headline, body_inner_html)` — wraps
  any portal onboarding/reset body in the standard chrome:
  - Eyebrow: **MASCI Operations Platform** (red)
  - Sub-eyebrow: per-portal label + color (PM=red · Shop=amber · HR=purple)
  - H1: bold headline
  - Body: caller-supplied HTML (greeting + credentials block + steps)
  - Divider + standard footer: **MASCI General Contractors Inc. ·
    386-322-4500 · mascidocs.com** + **Powered by ForgedOps™**

**Refactored 4 email bodies in server.py**:
- PM welcome (`_email_pm_welcome`) — was inline 40-line HTML block
- PM forgot/reset (`pm_forgot_password`) — was inline 35-line HTML block
- Shop welcome (`set_password_for_shop_user` admin trigger) — was inline 40 lines
- Shop forgot/reset (`shop_forgot_password`) — was inline 35 lines
- All four now build the inner-body HTML string and call
  `render_portal_email(portal=..., headline=..., body_inner_html=...)`.
  Net code reduction: ~150 lines of duplicate HTML chrome eliminated.

**Refactored HR emails in routes/hr_portal.py**:
- Removed the duplicate `_branded_hr_email_html` helper (was iter80
  HR-only) — now reuses the shared `render_portal_email(portal="HR", ...)`.

### Verification (21 assertions all PASS)
For each portal (PM, Shop, HR):
- MASCI Operations Platform eyebrow present ✅
- Per-portal sub-eyebrow present ✅
- Headline rendered ✅
- Per-portal accent color present (#c8102e / #ea580c / #7e22ce) ✅
- MASCI General Contractors Inc. footer ✅
- Powered by ForgedOps™ footer ✅
- Old "MASCI Hub · PM Portal" style eyebrow ABSENT ✅

Three sample emails rendered + screenshotted side-by-side — visual
parity confirmed.

### Files touched
- `/app/backend/branded_portal_emails.py` (NEW)
- `/app/backend/server.py` (4 email-body sites refactored + import)
- `/app/backend/routes/hr_portal.py` (drop duplicate helper, use shared)

---


## 2026-05-13 — Iter80: HR Auth Parity (P0 BUG FIX + Visual Standardization)

### User-reported bugs (from production mascidocs.com)
1. **HR temp-password change-password flow broken** — toast "HR login
   required" after submitting the form. User stuck.
2. **HR Login looks different than PM Login** — missing Forgot
   Password, Remember Me, eye-toggle visibility, helpful copy.
3. **HR welcome email looks different** than other portal emails.

### Root cause analysis
- `HrChangePassword.jsx` was reading `must_change_password` from
  `getHrUser()?.must_change_password` and branching the form to HIDE
  the "Current password" field on first login. On iOS Safari the
  navigation race between `setHrToken` → `setHrUser` → `nav()` and
  the next API call could pre-empt localStorage commit, sending the
  change-password request with no `X-HR-Token` header → backend
  returns "HR login required".
- `HrLogin.jsx` was a stripped-down skeleton — no `PasswordInput`,
  no inline Forgot dialog, no Remember Me styling, no helpful copy,
  no ForgedOps™ footer.
- `_send_welcome_email` and `hr_forgot_password` in
  `routes/hr_portal.py` were emitting bare HTML (`<p>Hi name,</p>`)
  with no MASCI Operations Platform chrome — looked like spam next
  to the iter78-branded daily-report emails.

### What shipped
**Backend (`/app/backend/routes/hr_portal.py`):**
- New `_branded_hr_email_html(eyebrow, h1, body_html)` wrapper —
  produces the standard MASCI Operations Platform red eyebrow + HR
  Portal purple sub-eyebrow + bold h1 + body content + MASCI General
  Contractors Inc. line + Powered by ForgedOps™ footer.
- `_send_welcome_email` rebuilt — now uses branded chrome with a
  proper table layout (Sign-in URL · Email · Temporary password with
  dashed border highlight), a big purple **Sign in & set password**
  CTA button, and a "change password immediately" reminder.
- Subject standardized: `[MASCI] Your HR Portal account — temporary
  password inside` (matches iter78 subject grammar).
- `hr_forgot_password` rebuilt — branded chrome, 30-min link
  expiration explicit, big purple **Reset password** button, falls
  through to plain-text URL for accessibility.
- Subject: `[MASCI] Reset your HR Portal password` (matches PM).

**Frontend (rebuilt to PM parity):**
- **`pages/HrLogin.jsx`** — full PM mirror w/ purple accent:
  hub-back link, MASCI logo, EN/ES toggle, Building2 icon eyebrow,
  Mail-icon email field, `PasswordInput` with eye-toggle, **inline
  Forgot Password Dialog** (purple/red branded, 30-min expiry copy),
  styled Remember Me checkbox, helpful bottom copy, 90s timeout,
  per-status error mapping (401/403/timeout/5xx/cold-start), clears
  every other portal's token on arrival.
- **`pages/HrChangePassword.jsx`** — full PM mirror w/ purple accent:
  fresh `/hr/me` on mount (bounces to /hr/login if token invalid),
  **always shows Current/Temp password field** (no must_change
  branching), `PasswordInput` everywhere, 8+ char + match validation,
  on success swaps token + navigates to `from || /hr`.
- **`pages/HrResetPassword.jsx`** — PM mirror w/ purple accent for
  the `/hr/reset/:token` post-email flow.
- **`pages/HrForgotPassword.jsx`** — deprecated to a redirect to
  /hr/login (inline dialog now lives there).

### Verification
- End-to-end backend smoke test: admin create user → email delivered
  with new chrome → login w/ temp → /hr/me confirms must_change=true
  → change-password (sends current+new) → 200 OK, must_change flips
  to false. PASS.
- Visual screenshots verified: HR Login renders all PM-parity
  features (eye toggle reveals, Forgot dialog opens with purple/red
  branding, Remember Me checkbox styled, ForgedOps footer present).
- Welcome email screenshotted — full MASCI chrome with HR Portal
  sub-eyebrow + sign-in CTA + Inc. footer.

### Files touched
- `/app/backend/routes/hr_portal.py` (branded email helper + 2 emails rewritten)
- `/app/frontend/src/pages/HrLogin.jsx` (full rebuild)
- `/app/frontend/src/pages/HrChangePassword.jsx` (full rebuild)
- `/app/frontend/src/pages/HrResetPassword.jsx` (full rebuild)
- `/app/frontend/src/pages/HrForgotPassword.jsx` (deprecated → redirect)

---


## 2026-05-13 — Iter79: Weekly Backup Verification Cron

### User ask
Weekly automated email confirming R2 archives are healthy + lists what
was backed up. Peace-of-mind insurance vs. the existing watchdog (which
only fires when something breaks).

### What shipped
**Backend (`/app/backend/backup_verification.py` — new isolated module):**
- `list_r2_backup_archives()` — paginated R2 `list_objects_v2` over
  `backups/` prefix; handles >1000 objects.
- `build_verification_report(db)` — assembles full health report:
  R2 archive count + size + age, cross-checked against the local
  `backup_health` ledger, plus per-collection MongoDB record counts.
  Verdict: pass/warn/fail.
- `render_verification_email_html(report)` + `render_verification_subject(report)` —
  brand-matched HTML email + mobile-friendly subject (`[MASCI] Weekly
  Backup Verification ✓ · N archives healthy` for pass; `🚨 BACKUP
  VERIFICATION FAILED · check immediately` for fail).
- `send_verification_email(db)` — wraps build + Resend send. Falls
  through recipient resolution: `BACKUP_VERIFICATION_TO` →
  `BACKUP_EMAIL_TO` → `SAFETY_EMAIL_TO`.
- `verification_scheduler_loop(db)` — long-running asyncio cron.
  Default schedule **Mon 14:00 UTC** (10 AM ET Mon). Uses a
  `backup_health._verification_last_run` marker so it survives
  restarts — fires catch-up at boot if past-due.

**Backend (`/app/backend/routes/backup_verification_routes.py` — new):**
- `GET /api/admin/backup-verification/preview` — build report,
  no email (admin-strict)
- `POST /api/admin/backup-verification/run-now` — build + email
  immediately, optional `{recipients: [...]}` override (admin-strict)
- `GET /api/admin/backup-verification/state` — last/next fire,
  recipients, threshold (admin-strict)

**Backend (`server.py`):**
- Router mounted alongside signature-migration router.
- `_start_backup_verification_cron` startup hook spawns the
  scheduler as its own asyncio task — isolated from the main backup
  scheduler so a crash here can't disturb backups.

**Frontend (`AdminBackupVerificationPanel.jsx` — new):**
- Mounted in `AdminHub.jsx` System Recovery section, right between
  Cloud Archives and Signature Migration panels.
- Shows: schedule (day/hour/next-fire), recipients, last-run age.
- `Preview Report` button — runs the verification, shows verdict +
  R2 archive count + ledger status + record count inline.
- `Send Verification Now` button — confirm dialog → fires the
  email immediately. Returns toast with success or error.

**Env knobs** (all optional with sensible defaults):
- `BACKUP_VERIFICATION_ENABLED` (default true)
- `BACKUP_VERIFICATION_DAY` (0–6, Mon=0; default 0)
- `BACKUP_VERIFICATION_HOUR_UTC` (0–23; default 14)
- `BACKUP_VERIFICATION_TO` (CSV emails; falls through to
  `BACKUP_EMAIL_TO`/`SAFETY_EMAIL_TO`)
- `BACKUP_VERIFICATION_MAX_AGE_HOURS` (default 36)

### Verification (live preview test)
- Boot log: `[verify] weekly cron started — fires weekly on day-of-week=0 at 14:00 UTC`.
- Catch-up fire at boot succeeded: sent to `jaymn.judd@mascigc.com`,
  verdict **pass**, 50 R2 archives, 1.4 GB total, newest 3.0h ago.
- All 3 admin endpoints respond correctly (preview, run-now, state).
- Email renders cleanly — full HTML reviewed via Playwright
  screenshot.
- Admin panel verified at `/admin` — schedule/recipients/last-run
  card + preview card all render correctly.

### Files touched
- `/app/backend/backup_verification.py` (NEW)
- `/app/backend/routes/backup_verification_routes.py` (NEW)
- `/app/backend/server.py` (mount + startup hook)
- `/app/frontend/src/components/AdminBackupVerificationPanel.jsx` (NEW)
- `/app/frontend/src/pages/AdminHub.jsx` (import + render)

---


## 2026-05-13 — Iter78e: CompanyInfoDialog Two-Tier + Hub Header Cleanup

### User feedback
1. Header "INFO" button and bottom "Need Help" tile are duplicates
   — drop one.
2. The "VIEW ONLY · ADMIN LOGIN REQUIRED TO EDIT" banner felt off —
   should just silently disable, not warn.

### What shipped
- **Header INFO button removed from Hub.jsx** (line 235). The bottom
  "Need Help?" tile under the Reference section is now the single
  entry point.
- **CompanyInfoDialog rebuilt as two-tier**:
  - **Public / field-crew view**: title flips to "Need Help?", description
    explains "Office phone, address, and after-hours contact for
    MASCI General Contractors Inc.", renders as a clean business-card-
    style display (Company / Address / Office Phone / Website rows
    using new `InfoRow` sub-component). Email field hidden — field
    crews don't need internal addresses. Big red `Call Office`
    button preserved. Just a single `Close` button — no Save, no
    warning banner, no greyed-out form inputs.
  - **Admin view**: full editable form preserved unchanged. Title
    stays "Company Info", Save button + Cancel button.
- Removed unused `Lock` icon import + the `inputClsLocked` style
  fallback path.

### Verification
- Header: `info-btn count=0`, lang toggle remains.
- Read-only: banner gone, read-only card present, Save hidden, Close
  button visible, title = "Need Help?".
- Admin: full editable form + Save button restored after admin login.

### Files touched
- `/app/frontend/src/pages/Hub.jsx`
- `/app/frontend/src/components/CompanyInfoDialog.jsx`

---


## 2026-05-13 — Iter78c+d: Email Subject Redesign + Long-Form Brand Strings

### What shipped
**Email subject line redesign:**
- New helper `pdf_render.build_email_subject()` — project-first,
  mobile-truncation-friendly, status-aware.
  - Normal: `[MASCI] Spruce Creek · Daily Report · DR-2026-00638`
  - Equipment fail: `⚠ EQUIPMENT FAIL · Spruce Creek · CAT 320 · EQ-2026-00042`
  - Severe incident: `🚨 SEVERE INCIDENT · Daytona Beach Pier · IR-2026-00007`
- Smart project trim: extracts trailing location segment for
  separator-style names (` - ` / ` — ` / ` · ` / ` | `), or ellipsis-
  trims to 32 chars otherwise.
- Short kind titles: Daily Report (not Daily Job Report), Pre-Op (not
  Equipment Pre-Op Inspection), QA/QC (not QA / QC Inspection), etc.
- Dropped `· PM: Name` tail (PM already in To: field).
- Kept `[MASCI]` prefix for filter-rule continuity.
- Both subject construction call sites updated: auto-route
  (`server.py:8442`) and admin email-record (`server.py:8804`).

**Long-form brand string updates (option "a"):**
- Browser tab title: `MASCI Hub — Safety · Field · Projects · Admin`
  → **`MASCI Operations Platform`**
- Meta description: `MASCI Hub — Safety, Field, Projects, Admin...`
  → **`MASCI Operations Platform. The single system for daily field
  reports, QA/QC, safety, equipment, and payroll — at every MASCI job.`**
- PWA description: → **`MASCI Operations Platform. Field Reports ·
  Equipment · Safety · QA/QC · Payroll — every job, every detail.`**
- **Unchanged (by design)**: PWA `short_name` (`MASCI`), iOS home-
  screen title (`MASCI Hub`), OG/Twitter share titles (`MASCI Hub`),
  and the iconic tagline `No Guesswork. No Missed Steps. No Excuses.`
  — short-form touchpoints stay branded as MASCI Hub.

### Files touched
- `/app/backend/pdf_render.py` (build_email_subject, SHORT_KIND_TITLES,
  _short_project_label)
- `/app/backend/server.py` (both subject call sites)
- `/app/frontend/public/index.html` (title + meta description)
- `/app/frontend/public/site.webmanifest` (description)

### Verification
- 10-sample subject test PASS across all 7 record types + edge cases
  (long names, no doc_id, severe incident, equipment fail).
- Live curl confirmed tab title + meta description + manifest
  description all updated correctly post-frontend-restart.

---


## 2026-05-13 — Iter78b: PDF Chrome Standardization + "Inc." Closure

### User ask
- Update PDF header/footer to match iter78 email cleanup
- Standardize "MASCI General Contractors" → "MASCI General Contractors Inc."
  everywhere as visible chrome

### What shipped
- **`pdf_render.py` PDF chrome**:
  - Header kicker: `Field Safety Reporting Portal` →
    **`MASCI Operations Platform`**
  - Footer: `MASCI · Field Safety Reporting Portal` →
    **`MASCI Operations Platform · Powered by ForgedOps™`**
- **`Inc.` standardization** (visible chrome only — backend +
  frontend acknowledgments, footers, and legal text). Distribution
  routing emails to `safety@mascigc.com` unchanged.
- **"Field Safety Reporting Portal" → "MASCI Operations Platform"**
  also applied to `ShareFormDialog.jsx` QR-poster print footer and
  `Dashboard.jsx` inspections-page eyebrow.

### Verification
- 11 backend assertions PASS. Real PDF rendered (939 KB).
- Email screenshot confirms footer:
  "MASCI GENERAL CONTRACTORS INC. · 386-322-4500 · MASCIDOCS.COM"
  with "POWERED BY FORGEDOPS™" underneath.

### Files touched
- `pdf_render.py`, `field_leadership_pdf.py`, `hub_banners_pdf.py`,
  `routes/safety_forms.py`, `fieldLeadershipSchemas.js`,
  `safetyFormsSchema.js`, `i18n.js`, `ViewSafetyForm.jsx`,
  `Dashboard.jsx`, `ShareFormDialog.jsx`

### Pending decision
- Email subject line redesign — three options presented; awaiting
  user pick on `[MASCI]` prefix, emoji warnings, and project-name
  source (short location vs. full project label).

---


## 2026-05-13 — Iter76: Legal / Infrastructure / Branding Hardening

### User ask
"Review, update, strengthen, and standardize ALL legal policies,
infrastructure language, branding references, operational disclaimers,
backup/redundancy language, trademark/service mark positioning,
notification permissions, and enterprise platform terminology across
the entire MASCI HUB / ForgedOps platform ecosystem."

### What shipped
- **Terms of Service** (`/legal/terms`) — five sections added/hardened:
  - **§2A — Trademarks, Branding & Trade Dress**: ForgedOps™ +
    MASCI HUB™ proprietary marks language, registered/unregistered
    notice, prohibitions on reproduction / imitation / reverse-
    engineering / derivative branding, and a clause forbidding
    removal of ForgedOps™ / MASCI HUB™ marks from exports & PDFs.
  - **§7 — Platform Availability, Backup & Operational Resiliency**:
    upgraded from generic uptime disclaimer to a full enterprise
    resiliency clause: "commercially reasonable backup, redundancy,
    disaster-recovery, and operational-resiliency measures" with
    explicit Cloudflare R2 + nightly archives + encrypted-at-rest +
    periodic recovery testing + RTO/RPO disclaimer.
  - **§7A — Notifications & Operational Communications**: consent
    for push / PWA / email / SMS / safety / maintenance / account
    notifications, plus opt-out limits for safety-critical alerts.
  - **§7B — Automated Processing & AI-Assisted Features**: defines
    "Automated Features," disclaims that they do not constitute
    regulatory determinations / legal opinions / engineering
    certifications, and references the Privacy Policy for AI
    subprocessor disclosure.
  - **§8 — Operational Compliance**: hardened with OSHA + DOT +
    FAA + FMCSA + GDPR + CCPA + employment / wage-and-hour /
    payroll regulatory disclaimer ("does not by itself ensure
    compliance").
- **Privacy Policy** (`/legal/privacy`) — same five-area hardening:
  - **§3** — How Information Is Used updated to include
    notifications-routing language.
  - **§4 — Subprocessors**: full disclosure list now includes
    MongoDB Atlas · Cloudflare R2 (redundant object storage,
    archival, resiliency) · Cloudflare (DNS/edge/TLS/DDoS) ·
    Resend · Anthropic Claude · OpenAI · Google Gemini · cloud
    infrastructure providers.
  - **§5 — Security, Backup & Operational Resiliency**: parallels
    the Terms clause; lists role-based access scopes, session-
    token isolation, automated nightly archives, redundant cloud
    storage, recovery testing, and the heartbeat / dashboard
    diagnostic stack.
  - **§7 — Data Responsibility & Regulatory Compliance**: split
    explicit MASCI vs ForgedOps responsibilities; lists OSHA +
    DOT + FAA + FMCSA + employment + wage-and-hour + GDPR +
    CCPA + state privacy laws.
  - **§7A — Notifications & Communications Consent**.
  - **§7B — Automated Processing & AI-Assisted Features**: discloses
    that AI subprocessors process only the specific input necessary,
    are NOT used for model training on MASCI data, and are not
    granted ongoing data access.
- **Branding standardization closure**: `ops_manual.py` prose flipped
  to ForgedOps™ where appropriate. LLC retained ONLY for:
  - Legal references (terms, privacy, PDF ownership disclosures).
  - Classification stamps on vendor-internal docs (the ops manual's
    "CONFIDENTIAL — ForgedOps LLC" footer is a legal classification
    construct).
  - Code comments / docstrings (not user-visible per spec).

### Verified
- Testing agent iter76 — 59/59 spec assertions pass:
  - All five new Terms sections render correctly.
  - All five new Privacy sections render correctly.
  - Subprocessor list complete (8 items).
  - Hub footer remains the iter74 3-line stack.
  - Login pages all show "Powered by ForgedOps™".
  - Banned strings ("Built and maintained in-house by MASCI" +
    "Powered by ForgedOps LLC" in UI) confirmed absent.
- PDF footer iter74 regression (`Generated through MASCI HUB —
  Powered by ForgedOps™ | © 2026 ForgedOps™`) confirmed still in
  place.

### Files modified
- `/app/frontend/src/pages/legal/TermsOfService.jsx`
- `/app/frontend/src/pages/legal/PrivacyPolicy.jsx`
- `/app/backend/ops_manual.py` (prose tweaks; classification stamps preserved)
- `/app/memory/PRD.md`

---

## 2026-05-13 — Iter75: Signature → R2 migration

Admin migration tool + read-side compat shim. 14/14 signatures
moved to R2. Documented for posterity.

## 2026-05-13 — Iter74: ForgedOps™ Standardization

UI + PDF footers + posters flipped to ForgedOps™. LLC retained
only where legally appropriate.

## 2026-05-13 — Iter73: Public Hub Redesign

4-section layout · welcome-back hero · hybrid verbiage scrub ·
EnforcePortalScope fix.

## 2026-05-13 — Iter72: HR Payroll Variance + Training Updates
## 2026-05-12 — Iter71: HR Portal full stack

---

## Prioritized backlog

### P1
- **Backup verification cron** — weekly check that the previous 7
  nightly R2 archives exist + are openable; alarm email if not.
- **IT server-dump endpoints** — `GET /api/admin/server-dump/list`
  + `/latest`. Now meaningful since signatures are no longer
  bloating the DB.
- **Employee Login Gate** — bulk import + termination + usage.
- **Photo-First Daily Report** — AI-drafted from gallery photos
  (already covered legally by §7B Automated Features and Privacy
  §7B AI subprocessor disclosure).
- **Motive (Fleet) integration** — Pre-Op autofill + GPS verification.
- **Notification system** — once the legal consent is in place
  (iter76), build the actual push-notification + workflow-trigger
  infrastructure.
- **Add `eslint --rule no-duplicate-imports:error`** to CI.

### P2
- Auto-cron for signature migration on a schedule.
- "Restore from R2" admin button.
- "Forward to IT" share button on backup rows.

---

## Test credentials
See `/app/memory/test_credentials.md`. Quick refs:
- Admin: `MASCI1982!`
- HR Manager: `hrmanager@mascigc.com` / `HRPortal2026!`
- Shop: `testmech@mascigc.com` / `ResetWorks2026!`
- Field Leadership: `MASCIGC`
- PM (Chris Wright): `chriswright@mascigc.com` / `ChrisRocksThis2026`
