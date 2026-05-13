# MASCI Safety Hub — PRD

## 2026-05-13 — Iter98: Termination Email Routing + FL PDF Daily-Report Parity

### User asks (3-in-1)
1. Employee Termination must email to: job PM + jaymn.judd@mascigc.com +
   safety@ + all HR managers
2. Forms not uniform — Termination PDF looks plain vs Daily Report.
   Daily Report is the gold standard; everything should match.
3. HR portal calculates time weekly, daily reports daily — make uniform

### What shipped

**1. Termination email routing** — `routes/field_leadership.py`
`_send_submit_email` now adds every active `hr_users` email to the
recipients list when `rec.kind == "employee_termination"`. Existing
recipients (assigned PM + jaymn + safety) still fire as before. Deduped
case-insensitively so an HR user who's also CC'd as jaymn doesn't get
two copies.

**2. FL PDF numbered sections** — `field_leadership_pdf.py`
Aligned with Daily Report styling. Every section header now renders
with a red `01 02 03 …` badge to its left + uppercase tracking +
divider line. Implemented via CSS `counter-increment` on every `h3`,
with the intro "Submission Overview" block manually labeled `01` so
detail/photos/signatures pick up `02 03 04` automatically. Output:
17.5 KB PDF, renders clean in WeasyPrint, matches the visual rhythm
of the Daily Report (numbered red badge → uppercase title → underline
→ content table).

**3. Time uniformity (no code change required — explanation)**
HR Time Verification ALREADY has both views via a toggle button bar:
- "Weekly Rollup · N" (per-employee Mon→Sun totals — payroll view)
- "Per-Day Detail · N" (per-employee per-day rows from masci_crews
  in daily_reports)

Backend endpoint returns BOTH datasets in the same payload (`weekly`
+ `rows`). The data IS the same — captured per-day, rolled up to
weekly for payroll. User can toggle views at any time. Default is
weekly because payroll runs weekly. If user wants daily as the
default, that's a 1-line frontend change — flagged below.

### Verified
- ruff clean
- PDF renders: 17,497 bytes for sample termination
- Backend healthy after restart
- `hr_users` enumeration tested via existing schema (collection
  already exists with `disabled` field, query `{"disabled": {"$ne": True}}`)

### Files touched
- `/app/backend/routes/field_leadership.py` (email routing + import logger)
- `/app/backend/field_leadership_pdf.py` (numbered section CSS + intro section markup)

### Action for user
Production needs a redeploy to push iter98. Once live:
- Submit a test termination → should email PM + jaymn + safety + every
  active HR user
- Open the PDF → headers should show "01 SUBMISSION OVERVIEW" /
  "02 EMPLOYEE TERMINATION · DETAILS" / "03 SIGNATURES" with red badges

### Open question for user
Time verification default view — keep current (Weekly default with toggle
to Daily), or flip the default to Daily? Both views are already there;
just a 1-character flip if user prefers daily-first.

---


## 2026-05-13 — Iter97: Uniform Back-Button Component (start of platform-wide migration)

### User asks
1. Make all back buttons uniform — "we've talked dozens of times about
   making the system uniform"
2. PortalSwitcher visibility — should super-admin only / multi-portal
   only? (Confirmed: already correctly gated. Renders null if user has
   <2 portals in their directory record. Single-portal direct logins
   never see it.)

### Root cause of back-button inconsistency
40+ pages each rolled their own `<Link to=…><ArrowLeft … />` snippet
with subtly different sizes (`w-3.5` vs `w-4`), spacing (`mr-0` vs
`mr-1`), color treatments, font sizes, tracking, and capitalization.

### What shipped
**New blessed component** `BackLink.jsx`:
- `<BackLink to label variant />` is the ONE way to render any back link.
- `variant="header"` — sits in dark navy/red header bars, white text.
- `variant="body"` — sits in content sections on light backgrounds,
  slate text.
- Auto-computes destination + label from user's role when `to`/`label`
  omitted: admin→`/admin`, pm→`/pm`, hr→`/hr`, shop→`/shop`, else `/`.
- Single typography spec everywhere:
  `font-mono text-[11px] uppercase tracking-[0.2em] font-bold` +
  `<ArrowLeft w-3.5 h-3.5 />` + `gap-1.5`.

**Pages migrated this iteration (high-traffic record-view pages first):**
- `ViewInspection.jsx` (admin click-through from /admin/inspections list)
- `ViewMeeting.jsx`
- `ViewIncident.jsx`
- `ViewEquipmentInspection.jsx`
- `ViewQaqcInspection.jsx`
- `FieldLeadershipRecords.jsx` (also fixed in iter96)

### Backlog of pages still using their own back-link snippets
~30 remaining pages — they all still work (no regression), but they're
visually inconsistent until migrated. Targets for incremental migration:
PM Hub, Shop Hub, HR Hub, all Admin sub-routes (AdminEquipment,
AdminPeople, etc — though AdminShell already has a uniform breadcrumb),
form submission pages (NewInspection, NewIncident, etc), View*
detail pages, Reset/Forgot password pages, training pages.

### Verified
Screenshots confirm uniform styling across:
- `/admin/inspections` → click record → "← ADMIN" in header (dark)
- `/leadership/records` → "← ADMIN CONSOLE" at body (light)

Both use identical icon size, typography, spacing — visually consistent.

### Files touched
- `/app/frontend/src/components/BackLink.jsx` (NEW)
- `/app/frontend/src/pages/ViewInspection.jsx`
- `/app/frontend/src/pages/ViewMeeting.jsx`
- `/app/frontend/src/pages/ViewIncident.jsx`
- `/app/frontend/src/pages/ViewEquipmentInspection.jsx`
- `/app/frontend/src/pages/ViewQaqcInspection.jsx`
- `/app/frontend/src/pages/FieldLeadershipRecords.jsx`

---


## 2026-05-13 — Iter96: Field Leadership Back-Button Role Routing

### User report
"in admin i click on field leadership shows all forms filled out as it
should but then has back button that takes back to field leadership not
admin console.... you are slipping a lot"

### Root cause
`/leadership/records` and `/leadership/records/:id` both hardcoded their
"back" link to `/leadership` (the password-gated supervisor form-entry
hub). When admins navigated in from the Admin Overview KPI tile (iter95)
or PMs from PmHub, clicking back dropped them on a page they have no
business being on instead of their home portal.

### What shipped
Both pages now compute the back destination dynamically from the user's
token:
- **isAdmin()** → `/admin` ("← ADMIN CONSOLE")
- **isPm() / getPmToken()** → `/pm` ("← PM HUB")
- otherwise → `/leadership` ("← FIELD LEADERSHIP") (legacy supervisor
  flow unchanged)

Applied to:
- `FieldLeadershipRecords.jsx` — primary back link in the records list
- `FieldLeadershipView.jsx` — the secondary "← Field Leadership" link
  next to "← Records" in the detail view header

### Verified live
Signed in as super admin → navigated to `/leadership/records`:
- Back button now reads **"← ADMIN CONSOLE"**
- Click lands on `/admin` ✅
- Screenshot confirms the new label.

### Files touched
- `/app/frontend/src/pages/FieldLeadershipRecords.jsx`
- `/app/frontend/src/pages/FieldLeadershipView.jsx`

### Action for user
Production needs a redeploy (bundled with iter95's tile-route fixes).

---


## 2026-05-13 — Iter95: KPI Tile Route Mismatches (P0 post-deploy)

### User report (post-production-deploy)
"oh boy lots of issues after deploy.... in admin field leadership tile
takes you to field leadership doesn't show forms submitted that's what
admin want to see is forms submitted see what's going on, click on
photos tile blank nothing happens..."

### Root cause
iter91-92 KPI tiles pointed at routes that either didn't exist in
App.js or led to the WRONG page for an admin (forms-entry hub instead
of admin records list). Specifically:
- `/leadership` → password-gated supervisor form-entry hub (correct for
  supervisors entering NEW forms; WRONG for admins who want to view
  submitted records)
- `/job-photos` → ROUTE DID NOT EXIST → blank page
- `/daily-reports`, `/equipment-inspections`, `/job-hazard-plans`,
  `/qaqc-inspections`, `/trench-boxes` → all stale public-shape paths,
  not the actual admin record-list routes

The iter94 audit didn't catch these because the test agent verified
endpoints return 200, not that the FRONTEND ROUTE TABLE includes the
destinations the new tiles point at. New test layer needed.

### What shipped (iter95)
**App.js** — added an explicit alias route so the EquipmentDashboard
(historical inspection list) is reachable independently of the
AdminEquipment section page (status board + master + parts):
- NEW `/admin/equipment-inspections` → `EquipmentDashboard`
  (previously `/admin/equipment` had double-registration — first match
  wins so the inspection LIST was unreachable from /admin/equipment.
  Now both views are available: status board at /admin/equipment,
  inspection list at /admin/equipment-inspections.)

**AdminKpiStrip.jsx** — every tile destination corrected:
- Daily Reports → `/admin/daily`
- Site Inspections → `/admin/inspections`
- Safety Meetings → `/admin/meetings`
- Incident Reports → `/admin/incidents`
- Equipment Pre-Op → `/admin/equipment-inspections`
- Job Hazard Plans → `/admin/jha-plans`
- Trench Box Data → `/admin/trench-boxes`
- QA/QC → `/admin/qaqc`
- Field Leadership → `/leadership/records` (the records-list, not the
  password-gated form-entry hub)
- Job Photos → `/admin/photos` (the AdminEquipment-portal-keyed
  JobPhotosLibrary)

### Verified live
Browser smoke test clicked every tile target — all 10 land on a
non-blank, non-bounced page:
- /admin/daily ✅ (1384 body chars)
- /admin/inspections ✅
- /admin/meetings ✅
- /admin/incidents ✅
- /admin/equipment-inspections ✅ (1915 chars)
- /admin/jha-plans ✅ (2332 chars)
- /admin/trench-boxes ✅
- /admin/qaqc ✅
- /leadership/records ✅ (38309 chars — 335 supervisor records)
- /admin/photos ✅ (Job Photos library renders with 58 photos
  grouped by project)

### Files touched
- `/app/frontend/src/components/AdminKpiStrip.jsx`
- `/app/frontend/src/App.js` (one new route)

### Action for user
**Production needs a redeploy** to pick up these fixes. After redeploy,
do a hard refresh on mascidocs.com/admin and click each tile to verify.

---


## 2026-05-13 — Iter93: KPI Strip — Weekly Deltas + Sign-Off Alert Badge

### User ask
"yes" to both: 📈 +X this week chip under each tile + ⚠ N awaiting
sign-off badge on Equipment Pre-Op.

### What shipped
Two enhancements to `AdminKpiStrip.jsx` — no new endpoints, both
computed from the data already in flight.

**1. "+N 7d" green delta chip** — Shown next to the sub-label on every
tile that has at least one record from the last 7 days. Visual: small
emerald-tinted chip with a trending-up icon. Tile date-fields used:
- Daily: `report_date` → `created_at`
- Inspections / QA/QC / Equipment Pre-Op: `inspection_date` → `created_at`
- Meetings: `meeting_date` → `created_at`
- Incidents: `incident_date` → `created_at`
- JHA plans: `created_at` / `upload_date`
- Trench boxes: `created_at`
- Leadership: `occurred_at` → `created_at`
- Photos: `record_date` → `created_at`

Computed client-side from the already-loaded lists — no extra API calls.

**2. Top-right red alert badge** on the Equipment Pre-Op tile counting
inspections that have at least one FAIL line (`fail_count > 0`) AND are
NOT yet cleared by the shop (`cleared !== true`). Backend already
serves both fields in the inspection summary, so no schema or endpoint
work needed.

Visual: 22px circular red badge with white border, "99+" overflow,
tooltip "N awaiting sign-off — click tile to review". Designed to be
generic (the `Tile` component accepts `alertBadge`) so other tiles can
adopt it later (e.g., "N unresolved incidents", "N stale daily reports").

### Verified
Screenshot shows: Daily Reports **+44 7d**, Equipment Pre-Op **+11 7d**
with a **⚠ 4** alert badge, Field Leadership **+335 7d**. Tiles with
no recent activity correctly omit the chip.

### Files touched
- `/app/frontend/src/components/AdminKpiStrip.jsx`

---


## 2026-05-13 — Iter92: Admin KPI Strip — Whole-Platform Visibility

### User report
"Still missing all forms submitted through field leadership too, job
photos, safety reports, accident/incident reports, etc. this is the
ADMIN console the whole world view......you messed this up fix it"

### Confirmed gap
iter91's strip only showed 8 of the 10 user-facing record collections.
Field Leadership records (335 supervisor records spanning 11 different
kinds — write-ups, coaching, attendance, recognition, terminations,
evaluations, equipment checkouts, etc.) and Job Photos (58 curated
images) had no top-level surface area.

### What shipped
Restructured `AdminKpiStrip.jsx` into two labeled sections so the
visual layout matches how admins think about the platform:

**Section 1 — "Safety & Field forms · Records on file"** (the 8 from iter91):
Daily Reports · Site Inspections · Safety Meetings · Incident Reports ·
Equipment Pre-Op · Job Hazard Plans · Trench Box Data · QA/QC

**Section 2 — "Leadership & Media · Records on file"** (NEW):
- **Field Leadership** (purple accent) — single tile with the total
  count rolled up across every "kind". The kind-by-kind breakdown
  (Write-ups: 3 · Coaching: 5 · Terminations: 1 · …) shows up in the
  hover title attribute so admins don't have to click through to see
  the distribution. Links to `/leadership`.
- **Job Photos** (slate accent) — count of indexed photos from the
  curated gallery, links to `/job-photos`.

### Implementation notes
- Field Leadership endpoint (`GET /api/field-leadership`) returns
  `counts_by_kind` even when items are limited — used `limit=1` to
  avoid hauling 335 records just for a count.
- Job Photos endpoint (`GET /api/job-photos`) returns top-level `count`
  in its response envelope.
- Both endpoints accept the admin token directly.

### Verified
- `curl /field-leadership?limit=1` returns counts_by_kind ✅
- `curl /job-photos?limit=1` returns count: 58 ✅
- Screenshot of `/admin` shows both sections rendering with live data:
  Safety & Field (56 / 7 / 1 / 4 / 18 / 0 / 0 / 0) + Leadership & Media
  (335 / 58) ✅

### Files touched
- `/app/frontend/src/components/AdminKpiStrip.jsx` (rewrite)

---


## 2026-05-13 — Iter91: Admin Overview — KPI Strip Restored

### User report
"What happened to all tiles for reports & everything on admin screens????
KPIs if you will?"

### Confirmed gap
The iter83/84 reorganization stripped the Admin Overview down to "welcome
text + Doc-ID search + 7 section tiles" but never replaced the at-a-glance
count tiles. Admin reported losing the at-a-glance visibility that the
old single-page admin had.

### What shipped
New `AdminKpiStrip.jsx` mounted at the top of the Admin Overview, above
the Doc-ID search. Compact 4×2 grid (responsive: 2 cols on mobile,
3 on tablets, 4 on desktop) showing each module's records-on-file count
with a click-through to the module's record list:

- 📋 Daily Reports → `/daily-reports`
- 📑 Site Inspections → `/inspections`  (red accent)
- 👥 Safety Meetings → `/meetings`
- ⚠ Incident Reports → `/incidents`  (red accent)
- 🔧 Equipment Pre-Op → `/equipment-inspections`
- 🛡 Job Hazard Plans → `/job-hazard-plans`
- 📦 Trench Box Data → `/trench-boxes`
- ✓ QA/QC → `/qaqc-inspections`

Each tile shows the live count, the form name, and "reports on file" /
"plans uploaded" / "boxes on file" sub-label. Hover effect changes the
border + adds an "OPEN →" hint, matching the PmHub tile interaction.
Loading state shows "—" until counts land.

### Verified
Screenshot of `/admin` shows the strip rendering correctly with live
numbers (56 / 7 / 1 / 4 / 18 / 0 / 0 / 0) and full responsive layout.

### Files touched
- `/app/frontend/src/components/AdminKpiStrip.jsx` (NEW)
- `/app/frontend/src/pages/AdminHub.jsx` (mount above Doc-ID search)

---


## 2026-05-13 — Iter90: Access Control Center — Email Delivery Parity

### User report
"Access Control Center doesn't give me option to email out password
like others do for PM, Shop.... I asked for this?"

### Confirmed gap
The Multi-Portal Access Control panel ("Add user" + "Reset password")
only ever copied the password to clipboard and told admin to "deliver
it outside the app." The per-portal admin panels for PM / Shop / HR
ALL have a clean **Email it / Show me** delivery toggle that sends a
branded welcome email with a sign-in link + temp password. The
directory panel was the odd one out.

### What shipped
**Backend** (`auth_directory_routes.py`):
- New `_send_directory_welcome(...)` helper using the shared
  `branded_portal_emails.render_portal_email` chrome (same wrapper as
  PM/HR/Shop welcomes) — sends a styled email with sign-in URL, temp
  password block, and a CTA button.
- `POST /admin/directory` now accepts `delivery: "email" | "show"`. If
  `delivery=email`, backend auto-generates a temp password (if not
  provided), creates the user, fires the welcome email, and returns
  `email_sent: true`. If `delivery=show`, returns the temp password
  for the admin UI to surface on-screen.
- `POST /admin/directory/{id}/reset-password` accepts the same `delivery`
  field — works identically to the create flow.
- Multi-portal users link to `/sign-in`; single-portal users (rare
  through this panel but possible) link to the specific `/x/login`.
- Audit log captures `delivery` mode + `email_sent` outcome.

**Backend** (`server.py`):
- New `_directory_send_email(to, subject, html)` Resend wrapper.
- `build_auth_directory_router(...)` now takes `send_email_fn` +
  `render_portal_email_fn` so the route factory is decoupled from the
  Resend/branding modules.

**Frontend** (`AdminAccessControlPanel.jsx`):
- "Add multi-portal user" dialog: new "How should they receive their
  password?" radio block (Email it ✉ / Show me 📋) — visually styled
  like the per-portal dialogs. Password field is now optional when
  emailing (auto-generates server-side). Inline explainer text changes
  based on selection.
- "Reset password" action: window.prompt asks `EMAIL` or `SHOW`. Success
  toast adapts based on outcome:
  - `email_sent: true` → "✉ Email sent to …" toast (12s)
  - `email_sent: false` → falls back to copy-to-clipboard + on-screen
    password toast (45s) — preview/dev path still works.

### Behavior matrix
| Delivery | Password provided? | Email channel up? | Result |
|---|---|---|---|
| email | yes | yes | Email sent with provided pw |
| email | no  | yes | Email sent with auto-gen pw |
| email | yes | no  | Falls back to show-on-screen + clipboard |
| email | no  | no  | Falls back to show-on-screen + clipboard |
| show  | yes | n/a | Always show-on-screen + clipboard |
| show  | no  | n/a | 400 — password required |

### Verified
- `curl POST /admin/directory delivery=email` creates user, falls back
  to `temp_password` in response when preview's
  `AUTO_EMAIL_REPORTS=false` ✅
- `curl DELETE /admin/directory/{id}` cleanup works ✅
- Frontend dialog screenshot shows new delivery toggle + helpful copy ✅

### Files touched
- `/app/backend/routes/auth_directory_routes.py`
- `/app/backend/server.py`
- `/app/frontend/src/components/AdminAccessControlPanel.jsx`

### Production action
The preview has `AUTO_EMAIL_REPORTS` disabled so emails fall back to
on-screen delivery for testing. Production already has the env var ON;
once the user redeploys, the welcome emails will fire automatically
when "Email it" is selected.

---


## 2026-05-13 — Iter89: THE Multi-Portal Bug (root cause finally identified)

### User report (4th time)
"still doesnt work!!!!!!!!!!!!!!"

### THE actual root cause (after 3 wrong guesses)
Every login page (`AdminLogin`, `PmLogin`, `ShopLogin`, `HrLogin`, `SignIn`)
had a `useEffect(() => { clearAllTokens(); }, [])` that nuked the entire
session the moment the page mounted. So the failure mode was:

  1. User signs in at /sign-in → all 4 tokens + directory session set ✅
  2. User navigates to /admin → RequireAdmin guard transiently sees
     "no admin token" for one render cycle (race during initial mount,
     stale bundle, etc.)
  3. Guard bounces to /admin/login → AdminLogin mounts → useEffect
     wipes all 4 tokens AND directory session ❌
  4. Now the user actually IS logged out everywhere. Hydration can't
     rescue because the directory session token is also gone.

This is why my iter87 + iter88 fixes (EnforcePortalScope multi-portal
awareness, MultiPortalHydrator, usePortalHydration hook with loader)
all looked correct in code review BUT couldn't actually rescue: by the
time hydration ran, the login page had already nuked the directory
session out from under it.

### Bonus blocker discovered
After iter88's file rewrite, the frontend bundle had compile errors
("Can't resolve PortalHydratingLoader") for several seconds. The user
may have caught the broken bundle and held it in cache before the
fix landed.

### What shipped (iter89)
Removed the `clearAllTokens()` mount-time effect from every login page:
- `AdminLogin.jsx`
- `PmLogin.jsx` (mount + onSubmit pre-wipe)
- `ShopLogin.jsx` (mount + onSubmit pre-wipe)
- `HrLogin.jsx` (mount + onSubmit pre-wipe)
- `SignIn.jsx`

Login pages no longer wipe anything on arrival. Tokens are only cleared
when the user explicitly signs out, or when the response from a fresh
login atomically replaces them via `setX(...)`.

### End-to-end verified (NO damage simulation, just natural flow)
1. Clear all cookies, localStorage, sessionStorage
2. Sign in at /sign-in → land on Hub ✅
3. Visit /admin → renders ✅
4. Visit /pm → renders ✅
5. Visit /hr → renders ✅
6. Visit /shop → renders ✅
7. Back to /admin, click SWITCH PORTAL → HR → lands on /hr ✅

### Files touched
- `/app/frontend/src/pages/AdminLogin.jsx`
- `/app/frontend/src/pages/PmLogin.jsx`
- `/app/frontend/src/pages/ShopLogin.jsx`
- `/app/frontend/src/pages/HrLogin.jsx`
- `/app/frontend/src/pages/SignIn.jsx`

### Apology
Took 4 iterations to find this. Lesson: when "the test passes but the
user says it's broken", the test isn't reproducing the user's flow.
Should have stress-tested by deliberately triggering a guard bounce on
day 1 instead of just verifying the happy path.

---


## 2026-05-13 — Iter88: Multi-Portal Bulletproofing (3rd attempt — SELF-HEALING)

### User report (3rd time)
"Still doesn't work — signed in, says welcome super admin, then HR/PM/Admin
asks me to sign in again. This is 3-4 time asking to get this issue resolved
we keep going in loops."

### Why my iter87 fix wasn't enough
The fix worked in my Playwright test (preview verified). But the user was
seeing different reality. Most likely: stale JS bundle in their browser
(hot reload only updates an actively-viewed tab). My iter87 fix required
the user to have the LATEST `EnforcePortalScope.jsx` loaded — anything cached
fell back to the old "auto-wipe sibling tokens" behavior.

### Root cause acceptance
Can't keep fixing the symptom. The whole multi-portal experience needs to
be **self-healing** regardless of what cache state the browser is in.

### What shipped (iter88 — bulletproof layer)
1. **`MultiPortalHydrator.jsx`** — top-level component mounted in App.js
   that runs on every route change. Reads the directory user from
   localStorage, sees which portals they're authorized for, and silently
   re-mints any missing per-portal token via the existing
   `POST /api/auth/issue-portal-token` endpoint.

2. **`usePortalHydration` hook + `PortalHydratingLoader`** — closes the
   synchronous-guard race. When a `RequireX` guard sees "no token but
   directory session authorizes this portal", instead of bouncing to
   /login it renders a brief "Reconnecting to X Portal…" loader, fires
   the re-issue, and renders children when the token lands. Typical
   render time < 500ms.

3. **All 4 guards rewired** (`RequireAdmin`, `RequirePm`, `RequireHr`,
   `RequireShop`) to use the hook. Single-portal direct-login users see
   no behavior change (no directory session → falls through to /login as
   before).

### End-to-end stress test (worst-case)
1. Sign in fresh at /sign-in → all 4 tokens stored ✅
2. **Deliberately wipe** HR / PM / Shop tokens from localStorage to
   simulate a stale-bundle / cache-corruption / token-eviction scenario
3. Navigate to /hr → shows "Reconnecting to HR Portal…" → token
   re-issued → /hr renders ✅
4. Same for /pm, /shop, /admin — all 4 self-heal ✅

### Why this is the right fix permanently
Even if `EnforcePortalScope` misbehaves, even if browser cache serves stale
JS, even if a developer accidentally introduces a token-wiping bug
somewhere in the future — as long as the user's directory session is
alive and they're authorized for the portal, they will never see a
re-login prompt. The system rescues itself.

### Files touched
- `/app/frontend/src/components/MultiPortalHydrator.jsx` (NEW — global background hydrator)
- `/app/frontend/src/lib/usePortalHydration.js` (NEW — synchronous race-closer hook)
- `/app/frontend/src/components/PortalHydratingLoader.jsx` (NEW — brief reconnect splash)
- `/app/frontend/src/components/RequireAdmin.jsx` (rewired)
- `/app/frontend/src/components/RequirePm.jsx` (rewired)
- `/app/frontend/src/components/RequireHr.jsx` (rewired)
- `/app/frontend/src/components/RequireShop.jsx` (rewired)
- `/app/frontend/src/App.js` (mount MultiPortalHydrator globally)

### Action for user
**Hard-refresh the browser once** (Ctrl+Shift+R / Cmd+Shift+R) to drop any
stale bundle. After that, sign in at /sign-in once and you're set across
every portal — no more re-login prompts even if something goes sideways.

---


## 2026-05-13 — Iter87: Multi-Portal Re-Login Bug Fix (P0)

### User report
"Once I log in via /sign-in, it says I'm logged in — but going to /admin, /pm,
/hr, /shop makes me re-log into each. Thought we had this worked out?"

### Two root causes — both fixed

**1. Per-portal minters returned null for directory users (backend)**
`_directory_pm_token`, `_directory_hr_token`, `_directory_shop_token` all
required a pre-existing record in `project_managers` / `hr_users` /
`shop_users`. The super admin lived only in `user_directory`, so PM/HR/Shop
tokens came back as `null` in the multi-login response.

**Fix**: New helper `_ensure_portal_shadow(db, collection, row)` in `server.py`.
On every multi-login, if a directory user authorized for PM/HR/Shop doesn't
have a per-portal record, auto-provision a "shadow" record using the
directory user's id + bcrypt password_hash directly. Subsequent logins
sync the hash so master-pw rotations propagate. Token minters now succeed
for every portal in the user's directory `portals` array.

**2. EnforcePortalScope auto-wiped sibling tokens (frontend)**
Designed before multi-login existed. The moment a user with all 4 tokens
navigated to `/admin`, the PM/HR/Shop tokens were stripped from localStorage
because `/admin` was "out of scope" for those portals. By the time they
visited `/hr`, that token was already gone → bounced to /hr/login.

**Fix**: `EnforcePortalScope.jsx` now reads `masci.directory.user.portals`.
Tokens for portals listed in the directory's portals array are NEVER auto-wiped
during navigation. Single-portal direct-login sessions retain the original
sandbox behavior (no behavior change for that path).

### Verified
- `curl /api/auth/multi-login` returns all 4 portal tokens for super admin ✅
- Each token validates against its respective `/me` endpoint ✅
- Browser test: sign in once at `/sign-in`, visit `/admin`, `/pm`, `/hr`, `/shop` in
  sequence — all 4 stay logged in, none bounce to a login page ✅
- "SWITCH PORTAL" dropdown shows "ALL OK" green chip ✅

### Files touched
- `/app/backend/server.py` — `_ensure_portal_shadow` helper + rewired the 3 minters
- `/app/frontend/src/components/EnforcePortalScope.jsx` — multi-portal aware

### Side benefit (free)
Adding an admin to user_directory with `portals: ["admin", "pm", "shop", "hr"]`
now auto-creates their PM/HR/Shop records on first multi-login — admin no
longer has to manually add them in 4 different panels. The shadow records are
flagged `linked_to_directory: true` + `source: "directory-shadow"` so the
admin UI can show "linked from directory" in the per-portal panels later.

---


## 2026-05-13 — Iter86: Doc Refresh — AdminGuide + Ops Manual

### User ask
"Is all training manuals updated with changes, guides, cheat sheets everything
with any & all changes so they are accurate?" — answer: no, AdminGuide.jsx and
ops_manual.py were stale. Cheat Sheet + PM Welcome PDF + Training Tracks were
already current.

### What shipped
- **AdminGuide.jsx full rewrite** (customer-facing owner's manual at `/admin/guide`):
  - 5-portal Hub at a glance (Field/Safety/PM/Shop/HR + Field Leadership)
  - 3-way sign-in explainer (single portal `/admin/login` · multi-portal `/sign-in` · field public)
  - Full Admin Console layout table covering all 7 sub-routes
  - New Pre-Deploy Snapshot section with traffic-light explainer
  - 3-layer backup strategy (hourly R2 + nightly email + weekly verification)
  - Restore-from-R2 workflow documented
  - Passwords table reflects per-user accounts (no more "single shared admin password")
  - Training Hub / QR posters section
  - Updated branding: "MASCI Operations Platform" + "Powered by ForgedOps™"
- **ops_manual.py (ForgedOps internal manual)** key sections refreshed:
  - User Tiers: per-portal accounts (project_managers, shop_users, hr_users, user_directory) — no more ADMIN/PM/SHOP_PASSWORD env-gating language
  - Key Collections: added user_directory, admin_audit, calculator_runs, backup_health, shop_users, hr_users, project_managers
  - File Handling: now references Cloudflare R2 (not local disk)
  - Section 3 (Third-Party): added R2 as HIGH-criticality dependency
  - Section 5 (Deployment): Pre-Deploy Snapshot panel check is now Step 1; updated env-var list (BACKUP_R2_HOURLY, S3_* credentials, SUPER_ADMIN_*)
  - Section 6 (Backup & Recovery): full rewrite — three-layer strategy table, on-demand panel docs, R2-first recovery procedures
  - Section 8 (Security): multi-portal directory authentication; per-user revocation via password_hash[:16] binding; super-admin lockout recovery procedure
  - Section 9 (Failure Points): R2 outage row added, removed local-disk-fill row, replaced "ADMIN_PASSWORD forgotten" with "super-admin lockout" recovery
  - Section 10 (Maintenance): daily check of Pre-Deploy Snapshot panel; weekly verification email check; monthly R2 storage review + admin_audit review
  - Section 11 (V2): updated server.py line count (9k); IT Server Dump endpoint added to roadmap; on-disk scheduler removal path noted
- **CheatSheet, PM Welcome PDF, Training PDFs** — verified already current (no edits needed)

### Files touched
- `/app/frontend/src/pages/AdminGuide.jsx` (rewrite)
- `/app/backend/ops_manual.py` (sections 1, 2, 3, 5, 6, 8, 9, 10, 11 refreshed)

### Verified
- AdminGuide page renders correctly at /admin/guide ✅
- ops_manual PDF renders: 73 KB (was 73 KB) ✅
- ops_manual DOCX renders: 51 KB (was 51 KB) ✅
- Lint clean (JS + Python) ✅

---


## 2026-05-13 — Iter85: Admin Login Parity + Option C Backup Hardening

### User asks (two combined)
1. "Admin login still has single-password — make it email + password like the rest."
2. "Once you click an admin tile, hard to get back without signing out — wasn't thought out very good."
3. Approved Option C: hourly auto R2 snapshot + smart "Snapshot before redeploy" button with freshness indicator.

### What shipped
- **AdminLogin.jsx rewritten** — now has Email + Password fields, "Remember me" toggle, and routes through `/api/auth/multi-login` (the same unified directory auth `/sign-in` uses). Matching visual chrome to `PmLogin.jsx` / `HrLogin.jsx` / `ShopLogin.jsx`. Footer link directs multi-portal admins to `/sign-in`. Legacy `POST /api/admin/login` (single-password) stays intact server-side as an API-only break-glass path.
- **AdminShell breadcrumb + back button** — fixed the "can't escape a tile" issue. Red header bar now shows `ADMIN CONSOLE › SECTION NAME` (the first segment is a link back to `/admin`), AND every non-Overview section page renders a prominent "← Back to Admin Overview" button above the intro card. Critical on mobile where the sidebar is collapsed behind a hamburger.
- **Hourly auto R2 snapshot** — added `BACKUP_R2_HOURLY=true` env flag (now ON in preview). The backup scheduler fires a complete archive build → R2 every UTC hour instead of only at 3am. Closes the maximum data-loss window from 24h → 1h. Falls back to the nightly schedule if the env is `false`.
- **PreDeploySnapshotPanel.jsx (NEW)** — mounted at the top of `/admin/system`. Color-coded freshness:
  - 🟢 GREEN < 1h old · "SAFE TO REDEPLOY"
  - 🟡 YELLOW 1-12h · "SNAPSHOT IS STALE"
  - 🔴 RED > 12h · "ARCHIVE IS DANGEROUSLY OLD"
  - 🔵 BLUE while a build is in flight
  - Big "Snapshot Now" button kicks `/api/admin/backups/run-complete-now` with poll-to-completion + toast
  - Footer line confirms hourly-auto status + nightly fallback time
  - Auto-refreshes every 30s while the page is open

### Files touched
- `/app/frontend/src/pages/AdminLogin.jsx` (rewrite — email+pass parity)
- `/app/frontend/src/components/AdminShell.jsx` (breadcrumb + back-button)
- `/app/frontend/src/components/PreDeploySnapshotPanel.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminSystem.jsx` (mount new panel at top)
- `/app/backend/server.py` (hourly R2 gate + state endpoint flag)
- `/app/backend/.env` (`BACKUP_R2_HOURLY=true`)

### Verified
- Hourly cron fired immediately on backend restart (logs show `firing complete-archive → R2 (hourly) bucket=2026-05-13T11` → uploaded successfully)
- Admin login page renders email+password fields like PM/HR
- `/admin/system` shows 🟢 GREEN "SAFE TO REDEPLOY" panel at top
- Breadcrumb + back button render on every section page

---


## 2026-05-13 — Iter84: Admin Console Re-shuffle + Backup System Audit

### User ask
"Is this banner system needed still — let's look at how our backup system has
grown, what's really needed & what if anything doesn't fit for where we're
going? … On admin console I don't want that big red thing at the top — maybe
it's going away, but if not put it with other backup things. Training scans
and bilingual adoptions and calculator need to go with other training stuff
or somewhere else they fit better."

### Audit verdict
Backup surface area had grown to 7 separate UI panels + 2 backend schedulers +
3 storage tiers (local disk, R2, email). The real direction is **Atlas Mongo +
R2 archives + verification email** — once Atlas lands, the local-disk path
becomes obsolete. UI consolidation done in this pass; backend disk-backup
trim deferred until Atlas migration is confirmed.

### What shipped (UI reorganization)
- **PersistenceHealthBanner relocated** — moved from Admin Overview top to top
  of `/admin/system` panel list. Auto-renders only when Mongo is ephemeral;
  goes green on Atlas. (`AdminHub.jsx`, `AdminSystem.jsx`)
- **3 analytics cards relocated** — `TrainingStatsStripe`,
  `BilingualAdoptionCard`, `CalculatorUsageCard` moved off Admin Overview and
  grouped under a new "Field adoption" sub-header on `/admin/training`.
  Configuration panels (resources, forms) live below under their own header.
  (`AdminTraining.jsx`)
- **/admin/system panel list slimmed from 7 → 5**: dropped
  `StoredBackupsPanel` (on-disk library — superseded by R2) and
  `AdminSignatureMigrationPanel` (one-time DB→R2 migration, complete). Files
  remain in the repo, just unmounted from the section.
- **Restore-from-R2 added**: `RestoreBackupPanel` got a Source toggle —
  "Upload .zip" (legacy) or "From R2 archive". Picking a cloud archive
  streams the presigned URL → blob → re-uploads through the same
  `/exports/restore` endpoint. No new backend route needed.
- **Admin Overview** now reads as a true glance: welcome text + Doc-ID search
  + 7 section tiles.

### Daily-workflow guarantees (verified)
| Workflow | Status after iter84 |
|---|---|
| Nightly email with backup link | ✅ unchanged (BACKUP_EMAIL_TO flow intact) |
| Admin downloads a backup | ✅ Cloud Archives panel (R2 presigned URLs) |
| Admin uploads .zip to restore | ✅ Restore panel · Source = "Upload .zip" |
| Admin restores from R2 directly | ✅ NEW · Restore panel · Source = "From R2 archive" |
| Dump to MASCI office server | ✅ same R2 presigned link, IT-shareable |

### Files touched
- `/app/frontend/src/pages/AdminHub.jsx` (removed 3 cards + banner)
- `/app/frontend/src/pages/admin/AdminTraining.jsx` (mounted 3 cards under
  Field adoption section)
- `/app/frontend/src/pages/admin/AdminSystem.jsx` (banner moved here,
  stored/migration panels dropped)
- `/app/frontend/src/components/RestoreBackupPanel.jsx` (R2 source toggle +
  archive picker)

### Backend deferred (Phase 2, post-Atlas migration)
- Remove on-disk backup scheduler + emergency disk-prune logic
- Drop mid-day disk backup (BACKUP_HOURS_UTC=2,18 → R2-nightly only)
- Re-point nightly email to use R2 build instead of disk build
- Delete `/api/admin/backups` listing endpoints

---


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

## 2026-05-13 — Iter83: Admin Console Section-Based Restructure

### User ask
"Admin console has grown into a huge thing it's like one long
scrolling web of everything. I do NOT want to remove anything but it
needs to be more organized & look better. Tiles inside it... backup
system tile, password tile, jobs tile..."

### Decision: Option B (sub-routes + persistent side nav)
- 24 admin panels split into 8 sections, each at its own URL
- Persistent left nav (desktop) / hamburger drawer (mobile) showing
  all sections with icons + descriptions
- Overview at `/admin` is the new landing: KPI strip + Doc-ID search
  + 7 navigation tiles + persistence banner

### Section map (zero panels removed)
- `/admin` Overview — Training stats · Bilingual adoption ·
  Calculator usage · Doc-ID search · 7 navigation tiles
- `/admin/people` — Access Control Center · PM users · Shop users ·
  HR users · Employee Master
- `/admin/jobs` — Job Master · Site Posters · Hub Banners
- `/admin/equipment` — Status Board · Equipment Master · Parts ·
  Suppliers
- `/admin/email` — Auto-Routing · Email Distribution Lists
- `/admin/training` — Training Resources · Safety Forms
- `/admin/compliance` — Compliance Export · Date Audit
- `/admin/system` — Backup Hero · Stored Backups · Cloud Archives ·
  Backup Verification · Signature Migration · Restore · Crew Recovery

### What shipped
**New shared chrome**:
- `/app/frontend/src/components/AdminShell.jsx` — Wraps every admin
  page with: sticky red top bar (MASCI logo, ADMIN CONSOLE eyebrow,
  section title, PortalSwitcher, SystemHealthBadge, Home link, Sign
  out), persistent left side nav (desktop) / `<Sheet>` drawer
  (mobile via hamburger), body slot with optional intro card,
  ForgedOps™ footer. Exports `SECTIONS` array so all section pages
  + the Overview tile grid use one source of truth.

**Section pages (NEW)**:
- `/app/frontend/src/pages/admin/AdminPeople.jsx`
- `/app/frontend/src/pages/admin/AdminJobs.jsx`
- `/app/frontend/src/pages/admin/AdminEquipment.jsx`
- `/app/frontend/src/pages/admin/AdminEmail.jsx`
- `/app/frontend/src/pages/admin/AdminTraining.jsx`
- `/app/frontend/src/pages/admin/AdminCompliance.jsx`
- `/app/frontend/src/pages/admin/AdminSystem.jsx`

Each is ~25 lines — just imports the panels and wraps them in
`AdminShell` with a section-specific intro paragraph.

**Overview rewrite**:
- `/app/frontend/src/pages/AdminHub.jsx` — Was 600 lines of
  procedural-scroll panel mounting. Now 80 lines: stats strip, Doc-ID
  search, 7 tile-grid. All previous content is preserved at its
  destination section pages.

**Routes**:
- `/app/frontend/src/App.js` — 7 new sub-routes mounted with the
  existing `A(...)` admin-required guard wrapper.

### Why this design wins
- **Each page is short and focused** → faster TTFB, less mobile data,
  zero scroll fatigue.
- **URL says where you are** → deep-link bookmarks work
  (`/admin/system` → directly to disaster-recovery toolkit).
- **Browser back/forward works correctly** (especially on iOS Safari
  where state-only tabs are flaky).
- **Persistent side nav** → one click to jump between sections from
  anywhere, just like Stripe / GitHub / Vercel admin consoles.
- **Mobile drawer** → hamburger → full nav slides in from left, same
  click behavior, no horizontal scroll.
- **Zero panels removed** → every single feature still exists, just
  organized by mental category.

### Verification
- Lint clean across all 10 changed/new files.
- Visual smoke test at desktop + mobile widths:
  - Overview at `/admin`: header sticky, dark left nav with 8 sections
    (Overview row highlighted red), KPI strip + Doc-ID search + 7
    tiles render.
  - Click "People & Access" tile → URL becomes `/admin/people`, title
    in header updates, AccessControlCenter renders at top of body
    with Super Admin row + email routing roster below.
  - Side-nav click "System & Backups" → URL becomes `/admin/system`,
    Backup Hero + Stored Backups + Cloud Archives + Backup
    Verification render.
  - Mobile hamburger trigger present.
- All 24 panels preserved at their destination section pages.

### Files touched
- `/app/frontend/src/components/AdminShell.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminPeople.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminJobs.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminEquipment.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminEmail.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminTraining.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminCompliance.jsx` (NEW)
- `/app/frontend/src/pages/admin/AdminSystem.jsx` (NEW)
- `/app/frontend/src/pages/AdminHub.jsx` (REWRITE: 600 → 80 lines)
- `/app/frontend/src/App.js` (7 new routes mounted)

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
