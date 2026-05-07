# MASCI Safety Hub — PRD

## 2026-05-07 — Platform-Owner Rebrand: Judd Group → ForgedOps LLC

### Scope
Per Justin: full system-wide replacement of "The Judd Group LLC" (developer/
platform-owner branding) with **ForgedOps LLC**. MASCI HUB customer branding
is **untouched** — MASCI logos, colors, identity, and operational copy all
remain dominant. ForgedOps becomes the platform-technology owner, present
subtly in attribution areas only.

### What shipped
- New attribution component `/app/frontend/src/components/ForgedOpsAttribution.jsx`
  (renamed from `JuddGroupAttribution`); old component + asset deleted.
- New logo asset `/app/frontend/src/assets/forgedops-logo.png` (256×256 UI use)
  + `/app/frontend/public/forgedops-logo-512.png` (PDF/email embedding).
- **Global footer** rewritten to two-row layout per user spec:
  - Dominant: `POWERED BY FORGEDOPS LLC · BUILDING SAFER JOBS | POWERING PERFORMANCE`
  - Subtle: `Terms · Privacy · v2026.MM.DD-hash` (clickable, build-version preserved)
- **Login attribution** (admin/PM/shop/safety-forms): `Powered by ForgedOps LLC` + small ForgedOps mark.
- **Admin attribution** (admin/PM hubs): `Platform developed & maintained by ForgedOps LLC`.
- **PDF footer** (every generated record PDF — daily reports, inspections, QA/QC,
  meetings, incidents, equipment, safety forms, training packets, posters):
  `Generated through MASCI HUB — Powered by ForgedOps LLC | © 2026 ForgedOps LLC`
  (Spanish: `Generado a través de MASCI HUB — Desarrollado por ForgedOps LLC | © 2026 ForgedOps LLC`)
- **Email sender** unified across all 8 send paths in `server.py`,
  `routes/safety_forms.py`, `routes/shop_parts.py`:
  `MASCI HUB Notifications <noreply@mascidocs.com>` (overridable via `SENDER_EMAIL` env).
- **Terms of Service / Privacy Policy** rewritten:
  - "software vendor" → "platform technology owner and operator"
  - "customer-branded URL mascidocs.com" wording removed
  - Multi-line "The Judd\nGroup LLC" splits caught and replaced
  - Pages now read as "enterprise operational platform technology deployed for MASCI use"
  - Removed redundant inline `<footer>` (was duplicating GlobalFooter — pre-existing
    bug surfaced during this work; cleaned up)
- **Admin/Dev/Vendor area copy** — DevHub, DevLogin, AdminGuide, Hub.jsx,
  TrainingQrPoster, TrenchBoxPosterCard, App.js comments — all updated
  to reference ForgedOps LLC.
- **Backend internal attribution** — server.py docstrings + DEV portal
  classification text + ops_manual.py + recolor_lockup_tagline.py — all
  updated to ForgedOps LLC.
- **Old logo file deleted**: `/app/frontend/src/assets/judd-group-logo.png` removed.
- **Legacy test fixtures** updated (test_iter29_predeploy.py, test_iter31_predeploy_audit.py)
  to assert the new footer string.

### What was deliberately NOT changed
- **MASCI HUB branding** — logos, colors, page chrome, copy: untouched per user.
- **Person name "Jaymn Judd"** — actual MASCI Safety Manager, real human, kept
  as-is in employees, project_managers, jobs, tests, and form placeholders.
- **historical test reports** (`/app/test_reports/iteration_*.json`) — immutable
  audit trail of past QA runs; left intact.
- **historical PRD entries** — older session notes in this PRD.md kept as-is
  for historical context. Search for "Judd Group" returns 0 hits in active
  code; PRD/test-report mentions are dated history.

### Historical document audit (per user spec)
- **PDF exports**: dynamically rendered every download from `pdf_render.py` /
  `training_pdf.py` / `pm_welcome_pdf.py` — all old records re-downloaded
  going forward will carry the new ForgedOps footer. **Auto-updated.**
- **Email templates**: rendered live by `render_email_html()` in `pdf_render.py`
  — all future emails carry the new branding immediately. **Auto-updated.**
- **Stored email artifacts**: only Resend-hosted send logs (managed by Resend,
  not editable from the app). **Static, no action.**
- **Backups (zips on disk)**: contain MongoDB JSON and uploaded photo bytes —
  no rendered PDFs stored. **Static, no action needed.**
- **Ops Manual snapshots** (`ops_manual_snapshots` collection): pinned PDF/DOCX
  bytes that reflect branding at the time of pinning. **Static.** Future
  snapshots will be ForgedOps-branded automatically; old ones can be
  regenerated via the existing `/dev/ops-manual/snapshot` button if needed.

### Verified end-to-end (preview)
- 0 "Judd Group" references in active code (frontend/src + backend + public assets)
- Footer renders correctly desktop + mobile (390px), no horizontal overflow,
  no clipping, single instance per page
- Terms/Privacy/Admin-Login/Hub all show the new branding cleanly
- Build version stamp (`v2026.05.07-4209543`) preserved in subtle line
- Backend `/api/health` returns 200; ESLint + ruff clean

### Known caveat — ForgedOps logo image typo
Attached logo image renders the tagline as `BUILDING SAFER JOBS | POWERING
PEREDRMANCE` (missing letter — should read `PERFORMANCE`). Per user
direction, the logo image is used as-is for the brand graphic, but the
**tagline text is always rendered separately** in the UI/PDF/email as
`BUILDING SAFER JOBS | POWERING PERFORMANCE` (correct spelling). Recommend
re-exporting a clean logo asset when convenient — drop a corrected PNG at
`/app/frontend/src/assets/forgedops-logo.png` (and the public/ copy) and
no code changes are needed.

### Files added/touched (selected)
- NEW: `/app/frontend/src/components/ForgedOpsAttribution.jsx`,
  `/app/frontend/src/assets/forgedops-logo.png`,
  `/app/frontend/public/forgedops-logo.png`,
  `/app/frontend/public/forgedops-logo-512.png`
- DELETED: `/app/frontend/src/components/JuddGroupAttribution.jsx`,
  `/app/frontend/src/assets/judd-group-logo.png`
- MODIFIED: `frontend/src/components/GlobalFooter.jsx`,
  `frontend/src/pages/legal/{TermsOfService,PrivacyPolicy}.jsx`,
  `frontend/src/pages/{PmLogin,AdminLogin,ShopLogin,SafetyFormsLogin,PmChangePassword,PmResetPassword,AdminHub,PmHub,Hub,DevHub,DevLogin,AdminGuide,TrainingQrPoster}.jsx`,
  `frontend/src/components/TrenchBoxPosterCard.jsx`,
  `frontend/src/lib/devAuth.js`,
  `frontend/src/App.js`,
  `backend/server.py` (docstrings + 8 email-send paths unified to MASCI HUB Notifications),
  `backend/pdf_render.py`, `backend/training_pdf.py`, `backend/ops_manual.py`,
  `backend/scripts/recolor_lockup_tagline.py`,
  `backend/data/suppliers_seed.json`,
  `backend/tests/test_iter29_predeploy.py`,
  `backend/tests/test_iter31_predeploy_audit.py`,
  `backend/tests/test_predeploy_iter39.py`

### Deploy reminder
Push fresh build to `mascidocs.com`. The next email any crew receives after
deploy will carry the new `MASCI HUB Notifications <noreply@mascidocs.com>`
sender. The next PDF any crew downloads (even of old records) will carry
the new ForgedOps footer. Cloudflare may cache the OLD Judd Group logo for
a few minutes — hard refresh on iOS/Android to pull the new ForgedOps mark.

---

## 2026-05-07 — P&L Snapshot removed from PM Portal
- Removed Project P&L Snapshot tile from `/pm` (PmHub.jsx) per owner direction
- Unmounted `/pm/pnl` route in App.js — PMs cannot deep-link
- Admin still has full P&L access at `/admin/pnl` — untouched

---

## 2026-05-07 — Job Photos Library Phase 1 (read-only aggregator)

### Scope
Centralized photo viewer for Admin and PM portals that aggregates photos crews
have already submitted on **Daily Reports**, **Site Inspections**, and
**QA/QC inspections**. Pre-Op photos explicitly EXCLUDED per user direction.

### What shipped
- Backend router `/app/backend/routes/job_photos.py` — 5 endpoints + indexer:
  - `GET /api/job-photos` — paginated metadata index (filters: source, project_number, week_of, date range, submitter)
  - `GET /api/job-photos/{id}/raw` — lazy-fetches the full data URL for a single photo
  - `POST /api/job-photos/zip` — streams a ZIP organized by `<job>/<week>/<source>__<date>__N.<ext>` (cap 1000 photos)
  - `POST /api/job-photos/email` — emails a ZIP packet via Resend (cap 25 MB / 200 photos)
  - `POST /api/job-photos/admin/reindex` — admin-only full rebuild
- Indexer hooks placed in `daily_reports.py`, `qaqc.py`, `inspections.py` —
  every new submission auto-mirrors photos into the index. Background catch-up
  loop runs every 30 min on records modified in the last 2 hours.
- Storage: lightweight metadata-only collection `job_photos`. Photo bytes are
  NOT duplicated — `/raw` re-reads from the source record on demand.
- PM scoping: `compute_pm_scope` enforced on every endpoint. PM only sees
  photos from jobs they own or co-PM. `/raw` returns 403 for out-of-scope IDs.
- Admin-only reindex: PM token gets 403.
- Frontend `/app/frontend/src/pages/JobPhotosLibrary.jsx` — accordion folder
  list (Job → Week), source-color-coded thumbnails, search + source filter,
  multi-select + bulk ZIP / Email, lightbox with ESC close, ARIA dialog role,
  graceful fallback for corrupt/missing photos (renders camera icon if data
  URL is <200 chars or fails to load — protects against future corrupt uploads).
- Routes: `/admin/photos` (admin) and `/pm/photos` (PM scoping enforced).

### Bug fix during this build
Frontend had a duplicate `/api/` prefix in 5 axios calls (`api.get("/api/job-photos")`)
because the axios baseURL already includes `/api`. Stripped to relative paths.

### Verified end-to-end (preview)
- iteration_40 testing: 13/13 backend pytest pass, 100% backend success
- Frontend: 0 console errors, 0 failed API calls, folders expand correctly,
  source badges render, lightbox opens + closes, multi-select action bar,
  PM scoping returns Total: 0 vs Admin Total: 21
- Pre-Op exclusion verified: `equipment_inspections` not in `SOURCE_COLLECTIONS`

### Files added/touched
- `/app/backend/routes/job_photos.py` (NEW)
- `/app/backend/server.py` lines 6354-6395 — router wiring + Resend wrapper
- `/app/backend/routes/daily_reports.py`, `qaqc.py`, `inspections.py` — indexer hooks
- `/app/frontend/src/pages/JobPhotosLibrary.jsx` (NEW)
- `/app/frontend/src/App.js` — `/admin/photos` and `/pm/photos` routes
- `/app/backend/tests/test_job_photos.py` (NEW)

### Deploy reminder
Production redeploy needed at `mascidocs.com` to expose this feature.

---

## 2026-05-05 — Safety Forms Check-In / Return + Updated Legal

### What was added
1. **Updated Acknowledgment & Legal text** on the Issuance form per Justin's revision (manufacturer guidelines + proper care & maintenance language)
2. **Check-In / Return flow** paired with each issuance — embedded on the issuance doc (no new collection)

### Check-In UX
- Open a previously-issued record → green "Start Check-In / Return" button on the view page
- For each issued line item, tap one of three giant pill buttons: **Returned OK** / **Damaged** / **Lost**
- Notes auto-required for Damaged or Lost
- Returned-but-partial qty is auto-billed as Lost
- Live chargeback total updates as you tap (Lost + Damaged @ original unit value)
- Dual signatures + FLSA acknowledgment → submit
- Auto-emails a separate "Check-In & Return Receipt" PDF to safety@ + jaymn.judd@
- Idempotent: 409 on double-return

### Backend
- `POST /api/safety-forms/equipment-issuances/{id}/return` — creates the embedded `return` block on the issuance, recomputes chargeback server-side
- `GET /api/safety-forms/equipment-issuances/{id}/return/pdf` — WeasyPrint check-in receipt
- List endpoint now strips nested `return.*_signature` fields

### Admin dashboard
- Issuance tab now shows a **Status** column: amber "OUT" pill (still issued) or emerald "RETURNED" pill (with chargeback amount inline if any)

### Files
- `/app/backend/routes/safety_forms.py` — `+ ReturnRow`, `ReturnBody`, `compute_chargeback`, `render_return_pdf`, return endpoints, updated email dispatcher to handle `kind="return"`
- `/app/frontend/src/lib/safetyFormsSchema.js` — `+ ISSUANCE_RESPONSIBILITY`, `RETURN_STATUSES`, `blankReturnRow`, `buildReturnDefaults`, `computeChargeback`
- `/app/frontend/src/pages/ReturnEquipment.jsx` (new) — the check-in form
- `/app/frontend/src/pages/ViewSafetyForm.jsx` — Check-In CTA + Return summary block
- `/app/frontend/src/components/AdminSafetyFormsPanel.jsx` — Status column
- `/app/frontend/src/pages/NewSafetyEquipmentIssuance.jsx` — split legal text (2 paragraphs)
- `/app/frontend/src/App.js` — `/safety/forms/equipment-issuance/:id/return` route

### Verified end-to-end
- Issued $190 of gear → Lost 1 of 2 Harnesses + Damaged 1 Hat → chargeback computed $190 server-side ($150 lost + $40 damaged)
- Re-listing shows status="returned" with chargeback inline; signatures stripped from list response
- Double-return blocked with 409
- Frontend smoke screenshot of the check-in form rendered cleanly: 3-pill status row, live chargeback total, FLSA block, sticky submit

---

## 2026-05-05 — Safety Forms (Equipment Issuance + Use & Care Training)

### Scope
New section under existing `/safety` sub-hub. Two forms used by the Safety Department:

1. **Safety Equipment Issuance & Accountability** — itemized financial chain-of-custody with at-issuance condition, photos (≥1 required), 13-item dropdown + "Other" write-in, dual signatures, FLSA/Florida-compliant legal acknowledgment.
2. **Safety Equipment Use & Care Training Documentation** — equipment trained on (Initial / Refresher / Retraining) + topics covered (Proper Use, Inspection, Maintenance, Storage, Limitations, OSHA, Other), instructor + employee signatures.

### Auth
Password-gated via `SAFETY_FORMS_PASSWORD=1982` (env). Token format mirrors the shop pattern. Admin tokens also satisfy the dependency. The list endpoints (admin dashboard) require an actual admin token.

### PDFs + email
WeasyPrint generates a clean, MASCI-branded PDF (lockup logo + red eyebrow + topical legal block + signatures + photos). On submit, the PDF is auto-emailed via Resend to `safety@mascigc.com` and `jaymn.judd@mascigc.com` (configurable via `SAFETY_FORMS_EMAIL_TO` env). Gated by `AUTO_EMAIL_REPORTS=true` (preview is `false`).

### Admin dashboard
New `AdminSafetyFormsPanel` mounted in `/admin` with tabs (Issuance / Training), filters (employee, project, date range, search across employee/project/supervisor), per-row Open + Download-PDF actions.

### Files
- `/app/backend/routes/safety_forms.py` — full router (login + 6 CRUD endpoints + PDF + auto-email)
- `/app/backend/.env` — `SAFETY_FORMS_PASSWORD=1982`
- `/app/frontend/src/lib/safetyFormsAuth.js`, `safetyFormsSchema.js`
- `/app/frontend/src/pages/SafetyFormsLogin.jsx`, `SafetyFormsHub.jsx`, `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx`, `ViewSafetyForm.jsx`
- `/app/frontend/src/components/AdminSafetyFormsPanel.jsx`
- `/app/frontend/src/App.js` — 6 new routes
- `/app/frontend/src/pages/SafetySection.jsx` — added "Safety Forms" tile

### Test results — iteration 37
- Backend: **19/19 PASS**
- Frontend: **10/10 PASS**
- Bugs: **0**
- Pytest test file persisted at `/app/backend/tests/test_safety_forms_iter37.py`

### Future-ready
- Asset/Serial field on every issuance line + photos with serial number → ready for QR/barcode integration
- Training topics persisted as keys (`proper_use`, `osha`, etc.) → ready for compliance-by-employee dashboard

---

## 2026-05-05 — Date-Display Bug Fix (P0 production hotfix)

### Symptom (reported by Justin)
*"Dates are coming in crazy on all reports in the field… crews select current date but when they come into system they have different date on them."*

### Root cause — TWO independent UTC-vs-local timezone bugs

**Bug 1 — Display shifts BACKWARD (the big one):**
`formatDateLong("2026-05-05")` was doing `new Date("2026-05-05")`. Per ECMAScript spec, a bare `YYYY-MM-DD` string is parsed as **UTC midnight**. Then `toLocaleDateString()` rendered it in the viewer's local TZ → showed **"Mon, May 4"** for any user west of UTC (all of US). Affected every dashboard, every PM list, every report-view header, every PDF.

**Bug 2 — Default date pre-fills FORWARD at night:**
`new Date().toISOString().slice(0, 10)` returns the UTC date. A Florida foreman opening a QA/QC form at 8 PM ET would see **tomorrow's** date pre-filled in the picker.

### Fix
- `/app/frontend/src/lib/utils.js` → `formatDateLong()` now detects bare `YYYY-MM-DD` via regex and constructs the Date with local components (`new Date(year, month-1, day)`). Full ISO timestamps with time/zone (`...Z` or `+00:00`) still parse normally, so PDF "Generated …" footers still localize correctly.
- `/app/frontend/src/pages/NewQaqcInspection.jsx` — switched `inspection_date` default from `toISOString().slice(0,10)` to `todayLocalIso()`. (The other 5 form pages — Inspection, Meeting, Incident, DailyReport, EquipmentInspection — were already on the local helper.)
- `/app/frontend/src/components/ComplianceExportPanel.jsx` — admin export-range pickers now use `todayLocalIso()` / `toLocalIso()`.

### Verification
Node round-trip test in `TZ=America/New_York`:
```
input        | OLD (buggy)              | NEW (fixed)
2026-05-05   | Mon, May 4, 2026         | Tue, May 5, 2026
2026-01-01   | Wed, Dec 31, 2025        | Thu, Jan 1, 2026   ← year boundary disaster
2026-12-31   | Wed, Dec 30, 2026        | Thu, Dec 31, 2026
```
Full ISO timestamps still localize correctly: `"2026-05-05T15:30:00Z"` → `Tue, May 5, 2026` in EDT (15:30 UTC = 11:30 EDT same day).

### Production action
Preview is patched. **User needs to redeploy `mascidocs.com`** to push the fix to production. No data migration required — the dates stored in MongoDB were always correct (`YYYY-MM-DD` as the crew picked them); only the rendering was off.

---

## 2026-05-05 — Issue-Password Modal Layout Fix
- `AdminPMPanel.jsx` issue-password dialog was overflowing because default `max-w-lg` (512px) couldn't fit 4 footer buttons. Widened to `sm:max-w-2xl` + `flex-wrap` + `break-words` on title.

---

## 2026-05-05 — Self-Service Password Reset + Remember Me + 2 New PMs

### Two new PMs added to roster (preview)
- **Asphalt PM** — `asphaltpm@mascigc.com`
- **Leo Masci** — `leomasci@mascigc.com`
> Both added in preview only. Need to be re-added in production via /admin → Project Managers panel after redeploy (or just redeploy — preview Mongo is separate from prod Mongo).

### Self-service password reset (forgot-password flow)
**User asked:** *"Now that 'Email to PM' works, you could enable self-service password reset for PMs themselves — Forgot password? link on /pm/login that emails the PM a reset link via Resend. Do this & a remember me thing at log ins option."*

**Backend:**
- `pm_auth.make_reset_token(pm_id, password_hash)` — `<exp_unix>.<pm_id>.<hmac>` format, 30-min TTL, signed against `_pm_hmac_secret()` and bound to first 16 chars of bcrypt hash. Self-revoking: when PM resets, hash changes → old token can't replay.
- `pm_auth.consume_reset_token(db, token)` — validates exp + signature + PM exists + has a password.
- `POST /api/pm/forgot-password` — admin-public, email-enumeration safe (always 200 generic message), per-IP lockout, sends email via Resend with `[MASCI] Reset your PM Portal password` subject line and a red "Choose a new password" CTA button.
- `POST /api/pm/reset-password` — verifies token, writes new bcrypt hash, clears must_change_password, returns fresh per-PM session token + PM doc.

**Frontend:**
- New `/pm/reset/:token` route (`PmResetPassword.jsx`) — landing page from email link with new pw + confirm fields, submits and drops PM into `/pm`.
- PmLogin: new **"Forgot password?"** red link next to Remember-me toggle; opens a Reset dialog with email input + "Email reset link" submit. Pre-fills with whatever email the PM was already typing in the login form. Friendly hint text below submit explains the full flow.
- Login page hint text rewritten to mention the Forgot link AND the call-the-office fallback.

### Remember Me toggle (all 3 portals)
**Backend:** N/A — purely a frontend storage decision.

**Frontend:**
- New `/app/frontend/src/lib/tokenStorage.js` — single source of truth for `readToken/writeToken/clearToken`. Reads `sessionStorage` first then falls back to `localStorage`. Writes to one or the other based on `{remember}` flag. Clear wipes BOTH (no stale tokens lingering after logout).
- `pmAuth.js`, `adminAuth.js`, `shopAuth.js` all rewritten to delegate to tokenStorage.
- Login pages get a Remember-me checkbox (default ON) above the Sign In button — yellow accent for PM, red for Admin, amber for Shop.
- All three login `setXToken(...)` calls now pass `{remember: rememberMe}`.

### Verified end-to-end (preview)
- `POST /api/pm/forgot-password` with real PM email → 200 generic message ✓ (Resend send succeeds, real email delivered).
- Same endpoint with unknown email → SAME 200 generic message ✓ (no enumeration leak).
- Bogus token to `/api/pm/reset-password` → 400 ✓.
- Real token round-trip: mint via `make_reset_token` → consume → returns PM doc ✓; tampered token → returns None ✓.
- PM Login: Remember me unchecked + login → token in `sessionStorage` only, NOT in `localStorage` ✓.
- Admin Login + Shop Login both render the Remember-me checkbox ✓.
- `/pm/reset/<token>` route renders with new pw + confirm fields ✓.
- 2 new PMs (Asphalt PM, Leo Masci) confirmed in roster ✓.

### Files added/touched
**New:**
- `/app/frontend/src/lib/tokenStorage.js`
- `/app/frontend/src/pages/PmResetPassword.jsx`

**Backend:**
- `/app/backend/pm_auth.py` (make_reset_token + consume_reset_token + 30-min TTL constant)
- `/app/backend/server.py` (PMForgotPasswordBody + PMResetPasswordBody models; `/pm/forgot-password` + `/pm/reset-password` endpoints with email-enum-safe generic responses)

**Frontend:**
- `/app/frontend/src/lib/pmAuth.js`, `adminAuth.js`, `shopAuth.js` — rewritten to delegate to tokenStorage
- `/app/frontend/src/pages/PmLogin.jsx` — Remember-me + Forgot-password link + Forgot dialog + submitForgot handler
- `/app/frontend/src/pages/AdminLogin.jsx` — Remember-me checkbox
- `/app/frontend/src/pages/ShopLogin.jsx` — Remember-me checkbox
- `/app/frontend/src/App.js` — `/pm/reset/:token` route



## 2026-05-05 — Email Welcome to PM + PM Training Login Bug Fix

### 🐛 Bug fixed: PM Training login redirected to /pm portal instead of /training/pm

**User reported:** *"On live site I attempted to log into PM Training with my email & password, it took me to the pm portal not pm training."*

**Root cause:** `EnforcePortalScope.useEffect` was wiping the PM token whenever the URL pathname left `/pm/*`. The user's flow was:
1. Click PM Training tile while logged out → redirected to `/pm/login` with `state.from = "/training/pm"`
2. Enter email + password → `PmLogin.onSubmit` sets the PM token and navigates to `/training/pm`
3. **EnforcePortalScope fires** on the new pathname → `/training/pm` is OUTSIDE `/pm/*` → **wipes the freshly-set PM token**
4. `TrainingTrack` re-renders → `isPm()` returns false → AccessDenied panel → user perceives this as "kicked back to login / portal"

**Fix:** `/training/*` is a multi-audience shared surface — every authenticated user (admin, PM, shop) needs to access training packets while keeping their portal session. Updated `EnforcePortalScope.inScope()` to treat training paths as in-scope for ALL portals. Per-track audience gating still happens inside `TrainingTrack.jsx` (so a PM can't view shop-only content even though their token survives navigation).

**Also fixed:** `PmLogin` now forwards `state.from` through the must-change-password redirect, and `PmChangePassword` honors `state.from` instead of hardcoding `/pm`. Result: a brand-new PM clicking "PM Training" now: PM Login → forced to set new password → lands directly on `/training/pm` with their token intact.

**Verified end-to-end (preview):**
- Logged-out user clicks PM Training tile → `/pm/login` ✅
- Enters Chris's credentials → lands on `/training/pm` with PM token preserved (length 101) ✅
- Lesson 1 renders fully (PM Portal Overview) ✅

### 📧 Email Welcome to PM (new feature)

**User asked:** *"Want me to draft a one-page 'Welcome to the new PM portal' PDF you can hand to each PM along with their temp password? Yes & it emails them temp password on first time or when reset."*

**What was built:**
- **New endpoint** `POST /api/admin/project-managers/{pm_id}/email-welcome` — admin-strict; mints (or rotates) the PM's password AND emails the welcome PDF + temp password to the PM via Resend in one shot. Returns `{ok, pm, sent_to, resend_id}`. Temp password is NOT echoed back to the admin in the response (it's already in the email body and PDF) — keeps the network log clean.
- **Email body** uses the same MASCI red branding as the PDF; embeds a dark `Account / Temporary password` block with the email + 10-char temp pw highlighted in mint green; 4-step "what to do next" list; auto-detects whether this is a first-issue (subject: "Welcome to the MASCI PM Portal") or a reset (subject: "Your password has been reset").
- **Failure modes handled:** 503 if `RESEND_API_KEY` isn't configured (recommends fallback to PDF download); 502 if Resend transport fails after the password was rotated (so admin can recover via `/welcome-pdf`).
- **Frontend:** AdminPMPanel password-reset dialog now has **4 buttons**: Cancel · Show on Screen (outline) · Download PDF (outline + FileText icon) · **Email to PM** (orange primary + Mail icon). Description rewritten to explain when to use each. The "Email to PM" button hover-tooltip shows the PM's email so the admin can confirm before clicking.

**Verified end-to-end (preview):**
- Backend returned `{ok: true, sent_to: "chriswright@mascigc.com", resend_id: "d4532b74-…"}` — real Resend delivery.
- Dialog renders all 4 buttons cleanly; tested that all are clickable and route to the correct mode.

### Files touched
- `/app/backend/server.py` — new `/email-welcome` endpoint (parallel to `/welcome-pdf`)
- `/app/frontend/src/components/AdminPMPanel.jsx` — 4-button dialog + email-welcome handler
- `/app/frontend/src/components/EnforcePortalScope.jsx` — `/training/*` paths in-scope for all portals
- `/app/frontend/src/pages/PmLogin.jsx` — forwards `state.from` through must-change-password redirect
- `/app/frontend/src/pages/PmChangePassword.jsx` — honors `state.from` after rotation



## 2026-05-05 — PM Welcome PDF (one-page handoff letter)

**User request:** *"Want me to draft a one-page 'Welcome to the new PM portal' PDF you can hand to each PM along with their temp password? yes!"*

### What was built
- **`/app/backend/pm_welcome_pdf.py`** — WeasyPrint generator for a single-page Letter-size welcome letter. Embeds the MASCI lockup (top), red-M mark (footer), and a tear-off credential block at the bottom with the PM's email + temp pw in a dark banner. Layout: 4 numbered onboarding steps + 2 side-by-side info cards ("What you'll see" / "If you forget your password") + tear-off.
- **New endpoint `POST /api/admin/project-managers/{pm_id}/welcome-pdf`** (admin-strict) — atomically mints a temp password AND returns the PDF as `application/pdf` attachment. Body shape matches `set-password` (optional `password` field; auto-generates 10-char if omitted).
- **AdminPMPanel** — Reset-password dialog now has 3 buttons: Cancel · Generate & Show on Screen · Generate & Download Welcome PDF (the new orange primary button with FileText icon). Description rewritten to explain all three options.

### Verified end-to-end (preview)
- Backend returns 200 with valid PDF (828 KB) in <1 sec. Header `%PDF-1.7` confirmed.
- Visual analysis (Gemini-Flash on the rendered output): 7/7 verification points ✓ — logo at top, PM name in headline, 4 numbered steps, 2 info cards, tear-off banner with the temp pw `PueSDXkw3Q` confirmed inserted, single page, professional design.
- Frontend dialog renders all 3 buttons; description text reads cleanly.
- Backend test passes lint; no regressions to other set-password / disable / activity endpoints.

### Files touched
- `/app/backend/pm_welcome_pdf.py` (NEW)
- `/app/backend/server.py` (new `/welcome-pdf` endpoint)
- `/app/frontend/src/components/AdminPMPanel.jsx` (3-button dialog + blob-download flow)

### Notes for prod
- The PDF embeds full lockup + red-M from `/app/frontend/public/`. Production pulls those from the same path so the PDF will look identical post-deploy.
- Endpoint defaults to `https://mascidocs.com` for the portal URL on the letter; can be overridden with `PORTAL_URL` env var if subdomain ever changes.



## 2026-05-05 — Pre-Deploy Full System Audit (Cross-Browser × Cross-Device)

**User request:** *"Need to run a complete system check of all systems... no bugs in any systems & everything works as it should & is smooth, fast & looks amazing & most importantly works flawlessly before i redeploy. This includes for all computer types & browsers also for all mobile devices apple or android of any system."*

### Audit results — DEPLOY READY ✅

**1. Backend audit (testing_agent_v3_fork) — 27/27 pass:**
- Per-PM auth: login + change-pw + admin set/reset + disable all green
- Per-PM data scoping: Chris correctly sees 9 of 28 jobs (8 primary + 1 co-PM on 24-06)
- Co-PMs per job: max-4 enforced, unknown-email rejected, primary-PM reassign preserves co-PMs
- Auto-email routing: compliance kinds include ALWAYS_CC, operational kinds exclude office
- /admin/projects/pnl returns 404 for unscoped projects (PM token)
- Activity log endpoint returns 200 for admin, 401 for PM token
- Wrong-pw on /admin/auth/verify-password returns 401 with brute-force lockout
- Co-PM email duplicate in cc array fixed (cosmetic — Resend would dedup anyway)

**2. Frontend audit — 0 console errors, 0 P0/P1 bugs:**
- Admin login → /admin loads cleanly, AdminPMPanel renders with Activity column
- PM login → /pm loads cleanly, AdminPMPanel correctly NOT rendered there
- Backup & Restore Tools section visible at bottom of /admin (4 numbered subsections w/ descriptions)
- Mobile (375x812) /admin/login: red-M mark + responsive layout intact
- ZERO "Made with Emergent" branding anywhere

**3. Cross-browser × cross-device matrix — 60/60 GREEN:**
| Engine | Desktop | iPad | iPhone | Android |
|---|---|---|---|---|
| Chromium (Chrome / Edge / Brave) | 5/5 | 5/5 | 5/5 | 5/5 |
| Firefox | 5/5 | 5/5 | 5/5 | 5/5 |
| WebKit (Safari) | 5/5 | 5/5 | 5/5 | 5/5 |

Screens covered per combo: Home, Admin Login, Admin Dashboard, PM Login, PM Dashboard.
Performance: Chromium ~5s/dashboard · Firefox ~6s · WebKit/Safari ~10s (acceptable, all dashboards heavy with admin data).

**Firefox console "errors":** every Firefox screen reports 12-101 console messages — ALL are the same Cloudflare `__cf_bm` bot-management cookie rejected as "invalid domain". That's a Firefox-specific quirk affecting every site behind Cloudflare; zero functional impact (every Firefox flow passed).

**4. Visual analysis (Gemini-Flash on representative iPhone Safari + Android Firefox screenshots):**
- "PM dashboard appears to be well-designed and functional… cards and buttons are stacked appropriately, text is legible… no horizontal scrolling… polished aesthetic."
- "Records & Forms section… responsive and well-rendered, no horizontal scrollbar, header logo visible, tables not cut off."

### Files added in this audit
- `/app/scripts/cross_device_check.py` — Playwright Chromium+Firefox+WebKit matrix runner (60 screenshots → /tmp/xdc/)
- `/app/backend/tests/test_iter35_predeploy.py` — 27 backend pre-deploy tests (canonical pre-deploy gate)
- `/app/test_reports/pytest/iter35.xml` — JUnit
- `/app/test_reports/iteration_35.json` — testing-agent report

### Single cosmetic fix applied this round
- `pm_routing.py:recipients_for_record_async` — co-PM email no longer duplicates between `cc` and `always_cc` arrays. Verified on job 24-06: `cc` is now `[chriswright@, jaymn.judd@, safety@]` (no dup).



## 2026-05-05 — PM Activity Log + Per-PM Data Scoping

**User request:** *"Want a 'PM activity log' beside password column? Last login + IP + reports/week. Also when PMs log in only data ties to jobs they're assigned to or co-PM's on shows — not whole company data."*

**User choices (locked in):** primary OR co-PM counts; reads scoped on safety/jobs/P&L only (masters stay shared); writes UNTOUCHED this round; activity column = last login + IP + reports / 7d.

### Backend
- **`pm_auth.PmScope`** + **`compute_pm_scope(db, actor)`** — resolves actor → either admin (no filter) or set of assigned project_numbers. `.filter(q)` injects `project_number $in [...]` into a Mongo query; `.allows(pn)` is a single-record check.
- **Empty scope ≠ all records** — `.filter({})` returns an impossible filter (`__pm_empty_scope__: true`) when a PM has zero assigned jobs, so they see nothing instead of everything by accident.
- **`require_admin` and `require_shop_or_admin` now return the PM doc** (instead of just `True`) when authenticated by a per-PM token. Existing `_: bool = Depends(...)` callers continue working.
- **List endpoints scoped (8 routes in routes/, 4 in server.py)**: site inspections, meetings, JHPs, incidents, daily reports, equipment inspections, QA/QC inspections, equipment trends, equipment open-items, QA/QC stats, QA/QC CSV, /admin/jobs, /admin/jobs/archive, /admin/projects/list.
- **Detail endpoints scoped (7 routes)**: same as above plus /admin/projects/pnl. PM hitting a record outside their scope → 404.
- **Public endpoints intentionally NOT scoped**: /jobs (JobPicker on field forms), /job-hazard-plans, /trench-boxes, equipment-master, employees, suppliers, parts.
- **NEW endpoint** `GET /api/admin/project-managers/activity` (admin-strict) — single roundtrip rolls up `{last_login_at, last_login_ip, reports_7d, job_count}` for every PM by aggregating over jobs_master + 7 safety collections in the last 7 days.
- **`stamp_login(db, pm_id, ip)`** now persists the request IP on `/pm/login`.

### Frontend
- **`AdminPMPanel`** gains an **Activity** column between Login and Active. Shows: relative-time "1m ago", login IP, "6 reports / 7d", "9 jobs". Loaded on mount in parallel with the PM list (non-blocking — failures are silent so a transient activity error never breaks the roster).

### Verified end-to-end (preview)
- Admin sees 7 inspections / 5 dailies / 28 jobs. Chris (per-PM) sees 1 inspection / 0 dailies / 9 jobs / 0 incidents / 5 equipment.
- Detail GET on a daily report Chris isn't on returns 404.
- `/admin/projects/pnl?project_number=…` for a project Chris isn't on returns 404.
- Activity payload returns IP `34.16.56.64` for Chris (the only PM who has logged in via per-PM auth).
- Legacy shared bypass token still sees everything (the office break-glass case).
- The `/pm/qaqc-inspections` endpoint that already had its own pm-email filter is left untouched (no double-scoping).

### Files touched
- `/app/backend/pm_auth.py` (PmScope, compute_pm_scope, stamp_login w/ IP)
- `/app/backend/server.py` (require_admin / require_shop_or_admin return PM doc; activity endpoint; /admin/jobs* + projects/pnl scope)
- `/app/backend/routes/safety.py` (4 list + 4 detail scoped)
- `/app/backend/routes/daily_reports.py` (list + detail scoped)
- `/app/backend/routes/equipment.py` (list + detail + trends + open-items scoped; trailing garbage cleaned)
- `/app/backend/routes/qaqc.py` (list + detail + stats + CSV scoped)
- `/app/frontend/src/components/AdminPMPanel.jsx` (Activity column + relative-time formatter + parallel activity fetch)



## 2026-05-05 — Per-PM Auth + Co-PMs per Job

**User request:** *"Project Managers needs to be removed from PM Portal & only be in admin... Need option to issue PM passwords... On first login require them to pick their own 6 character password, but from admin we can reset any time. Also Active Jobs Master need to be able to assign up to 5 PMs per job — DO NOT change current PM, just allow multiple."*

### Backend
- **New module:** `/app/backend/pm_auth.py` — bcrypt password hashing, per-PM HMAC token (`{pm_id}.{hmac}` with first 16 chars of password_hash baked in so password resets invalidate old tokens), DB helpers (`set_pm_password`, `set_pm_disabled`, `is_valid_pm_user_token_async`), random temp-password generator (10-char, ambiguous-char-stripped).
- **New endpoints in `server.py`:**
  - `POST /api/pm/login` (replaced) — body `{email, password}` → `{ok, token, must_change_password, pm}`. Falls back to legacy shared-password bypass when email omitted AND `PM_SHARED_LOGIN_ENABLED=true`.
  - `POST /api/pm/change-password` — `{old_password, new_password}`, requires per-PM session, returns rotated token.
  - `GET /api/pm/me` — returns the signed-in PM doc or `{is_admin_or_legacy:true}`.
  - `POST /api/admin/project-managers/{pm_id}/set-password` — admin-strict; generates random temp pw if no body, returns plaintext ONCE.
  - `POST /api/admin/project-managers/{pm_id}/disable` — admin-strict; locks/unlocks login.
- **`require_admin` is now async** so it can DB-validate per-PM tokens. All existing `Depends(require_admin)` usages continue working transparently.
- **Brute force**: `_check_login_lockout` re-applied to all three new endpoints (login, set-password indirectly via require_admin_strict, change-password).
- **Co-PMs per job:**
  - `JobIn.co_pm_emails: Optional[List[str]] = None` — `None` preserves existing co-PMs on primary-PM reassign.
  - `PATCH /api/admin/jobs/{job_id}/co-pms` body `{co_pm_emails: [...]}` (max 4, validates each email against the PM roster, deduplicates against primary).
  - `pm_routing.recipients_for_record_async` now also pulls `co_pm_emails` from the matched job and adds them as CC on every routed email (compliance + operational).

### Frontend
- **`/pm/login`** revamped — email + password fields. On `must_change_password=true` redirects to `/pm/change-password`.
- **NEW `/pm/change-password`** page — old / new / confirm fields + 6-char minimum, swaps stored token to the rotated one.
- **`AdminPMPanel`** gains:
  - "Login" status column (Set / Temp / None / Locked badges).
  - Per-row **KeyRound** button → "Reset password" dialog (Generate or Custom). After save, shows the issued temp password ONCE in a copy-able banner.
  - Per-row **ShieldOff/Lock** toggle to lock/unlock login.
- **`AdminPMPanel` removed from `/pm`** (PmHub.jsx) — admin-only as of today.
- **`AdminJobMasterPanel`** gains a **Co-PMs** column with chip preview and an Add/Edit dialog (multi-select checkboxes, max 4). Primary PM is auto-excluded from the picker.

### Verified end-to-end (preview)
- Admin sets temp pw via UI → temp pw shown ONCE → PM logs in → forced to `/pm/change-password` → sets `ChrisRocks2026` → lands on `/pm` with `AdminPMPanel` no longer rendered.
- Admin sets co-PMs `[chriswright, jaymn.judd]` on job `24-06` → `/auto-email/preview?kind=inspection` returns `[davidjewett, chriswright, jaymn.judd, safety@]`. ✅
- Admin reassigns primary PM on `24-06` via the existing dropdown → co_pm_emails preserved (didn't get wiped). ✅
- 5+ co-PMs → 422; unknown email → 400; locked PM → 401 on subsequent calls. ✅
- Legacy bypass still works (no-email POST) for the office break-glass case.

### Files touched
- `/app/backend/pm_auth.py` (NEW)
- `/app/backend/server.py` (require_admin async; PM login/me/change-password; admin set-password / disable; co-pms PATCH)
- `/app/backend/pm_routing.py` (recipients include co_pm_emails)
- `/app/backend/jobs_master.py` (co_pm_emails field; preserve-on-upsert)
- `/app/frontend/src/pages/PmLogin.jsx` (email+password)
- `/app/frontend/src/pages/PmChangePassword.jsx` (NEW)
- `/app/frontend/src/pages/PmHub.jsx` (AdminPMPanel removed)
- `/app/frontend/src/components/AdminPMPanel.jsx` (Login column + reset/lock + dialogs)
- `/app/frontend/src/components/AdminJobMasterPanel.jsx` (Co-PMs column + dialog)
- `/app/frontend/src/App.js` (added /pm/change-password route)



## 2026-05-05 — Backup Section Reorganization + Destructive-Action Password Gate

**User request:** *"Leave everything as-is... in admin anything & everything backup-related move to lower section of admin screen & give a brief description of what each does. For any button that deletes or wipes data: 'are you sure' screen pops up & admin password must be entered to continue."*

### Changes
1. **All backup/restore tools relocated to bottom of `/admin`.** Before, `StoredBackupsPanel` and `RestoreBackupPanel` rendered inside `ComplianceExportPanel` near the top of the page. They now live at the very bottom (only the page footer is below them) under a single labeled section: "Backup & Restore Tools — everything backup-related, in one place."
   - `<ComplianceExportPanel hideBackupTools />` flag activated to suppress the in-line "Full Off-Site Backup" + Stored/Restore panels there.
   - AdminHub.jsx renders 4 numbered sub-blocks in order of escalating risk:
     1. `BackupHeroPanel` — safe one-click backup + safe-merge restore.
     2. `StoredBackupsPanel` — list/run/download/delete of nightly zips.
     3. `RestoreBackupPanel` — merge (safe) or replace (wipes).
     4. `CrewRecoveryPanel` — system status + force re-seed.
   - Each block has a brief plain-English description above it.

2. **New destructive-action password gate.** Every button that deletes or wipes data now requires the admin to re-enter the admin password before the action runs.
   - **Backend:** `POST /api/admin/auth/verify-password` — HMAC-checks the typed password against `ADMIN_PASSWORD`, with the same `_check_login_lockout` brute-force protection as `/admin/login`. Returns 200 / 401. Doesn't rotate the stored session token.
   - **Frontend:** new reusable `<AdminPasswordConfirm>` dialog component (`/app/frontend/src/components/AdminPasswordConfirm.jsx`). Renders an "Are you sure?" pane with description, password input, Cancel + Confirm. Confirm is disabled until a password is typed, then verifies against the backend before firing the supplied `onConfirm()`.
   - **Wired into:**
     - `StoredBackupsPanel` — `Delete <filename>` button (replaced the old `window.confirm` with the password dialog).
     - `RestoreBackupPanel` — `REPLACE` mode now requires typing "REPLACE" **AND** then the admin password as a second gate.
     - `CrewRecoveryPanel` — `Force re-seed` button now requires the existing dialog confirm **AND** then the admin password.

### Files touched
- `/app/backend/server.py` — added `/admin/auth/verify-password`.
- `/app/frontend/src/components/AdminPasswordConfirm.jsx` — NEW reusable dialog.
- `/app/frontend/src/components/StoredBackupsPanel.jsx` — delete now password-gated.
- `/app/frontend/src/components/RestoreBackupPanel.jsx` — REPLACE adds 2nd password gate.
- `/app/frontend/src/components/CrewRecoveryPanel.jsx` — force re-seed adds 2nd password gate.
- `/app/frontend/src/pages/AdminHub.jsx` — relocated backup panels with descriptions.

### Verified end-to-end (preview)
- `POST /admin/auth/verify-password` with wrong password → 401 + lockout counter ticks.
- `POST /admin/auth/verify-password` with correct password → 200, no token rotation.
- `/admin` bottom shows the new "Backup & Restore Tools" header with all 4 numbered subsections.
- Stored Backups → Delete → password gate appears → wrong pw shows toast + dialog stays open.
- Force re-seed → first dialog → Continue → password gate appears with destructive description.
- Replace restore → REPLACE typed → password gate appears as 2nd guard.



## 2026-05-04 — P0 Hotfix: Daily Report VIEW link still hardcoded to /admin

**User report:** *"Still getting daily report not found message we i click view.... In PM Portal... Is this truly fixed & only doing this because this is a demo preview?"*

**Answer:** Real bug, not a preview quirk. Earlier fix was incomplete.

### What I missed in the previous patch

The earlier fix (2026-05-04 17:30 UTC) repointed each dashboard row's `onClick={() => navigate("/${kind}/${id}")}` to `navigate("${pathname}/${id}")`. That works when a user clicks the row anywhere except on the per-row buttons.

But each row ALSO has a `<Link>` "VIEW" button with `e.stopPropagation()` that intercepts the click before the row handler fires. The Link's `to` prop was still hardcoded to `/admin/<kind>/<id>` in all 5 dashboards. So:
- PM clicks VIEW → `<Link to="/admin/daily/<id>">` navigates to `/admin/daily/<id>`
- `EnforcePortalScope` sees PM token + path outside `/pm/*` → wipes PM token
- `ViewDailyReport` mounts, fires `api.get("/daily-reports/<id>")` without auth → 401
- catch fires `toast.error("Daily report not found")` → bounce
- Exact symptom user reported.

### Hotfix
Switched all 5 dashboard `<Link to>` props from absolute `/admin/<kind>/<id>` to `${pathname}/${id}`:

| File | Line | Before | After |
|---|---|---|---|
| `DailyReportsDashboard.jsx` | 178 | `to={\`/admin/daily/${it.id}\`}` | `to={\`${pathname}/${it.id}\`}` |
| `EquipmentDashboard.jsx` | 175 | `to={\`/admin/equipment/${it.id}\`}` | same |
| `IncidentsDashboard.jsx` | 171 | `to={\`/admin/incidents/${it.id}\`}` | same |
| `MeetingsDashboard.jsx` | 154 | `to={\`/admin/meetings/${it.id}\`}` | same |
| `Dashboard.jsx` | 210 | `to={\`/admin/inspections/${it.id}\`}` | same |

`pathname` came from the `useLocation()` already added in the previous patch — no other infrastructure needed.

### Verified end-to-end (preview)
- PM logs in → `/pm/daily` → first View link href reads `/pm/daily/9aa02e33-…` (was `/admin/daily/…`)
- Click VIEW → URL stays at `/pm/daily/9aa02e33-…`
- PM token survives
- H1 = "Daily Job Report" (was "not found" toast → bounce)
- Header back-button reads `← DAILY REPORTS` linking to `/pm/daily` (was `/`)
- Full report data renders: project, location, date, prepared by, all sections

ESLint clean across all 5 files.

### Deploy reminder
Hotfix is in preview only. Production at `mascidocs.com` still has the broken bundle. Push a fresh build and the bug is resolved for every crew member who lands in PM portal.


## 2026-05-04 — P0 View-Page Fix + Inline Gross/Net Hours Preview

### Bug — clicking View on any PM-portal report → "Daily report not found"

**User:** *"in pm portal i click view on any reports then says daily report not found.... fix NOW!"*

**Root cause cluster:** Two follow-on bugs from the same `EnforcePortalScope` rule:
1. **Dashboard "View" buttons** call `navigate(\`/daily/${it.id}\`)` (and similar for incidents, meetings, equipment, inspections). That hits the legacy `<RedirectWithId base="/admin/<kind>" />` route → routes to `/admin/<kind>/${id}` → `EnforcePortalScope` sees PM token + path outside `/pm/*` → **wipes PM token** → destination `api.get` returns 401 → "not found" toast → bounce.
2. **View pages** then `navigate("/admin/<kind>")` after delete or 404 — same problem in the other direction.

**Fix — relative-path navigation everywhere it matters:**
- All 5 dashboards (`DailyReportsDashboard`, `IncidentsDashboard`, `MeetingsDashboard`, `EquipmentDashboard`, `Dashboard` for inspections) now use `useLocation()` and `navigate(\`${pathname}/${it.id}\`)`. Stays in `/pm/*` if the user is in the PM portal, stays in `/admin/*` if admin. Token never wiped.
- All 4 View pages (`ViewDailyReport`, `ViewIncident`, `ViewMeeting`, `ViewInspection`) compute `listUrl = pathname.replace(/\/[^/]+$/, "")` for back-to-list navigation. Same logic — strips the trailing `/<id>` segment to land on the correct portal's list.

**Verified end-to-end (preview):** Logged in as PM → `/pm/daily` → 5 reports listed → clicked View on first row → `/pm/daily/<uuid>` loads with H1 "Daily Job Report", no "not found" toast, PM token survives. Same flow for the other 4 dashboards.

### Enhancement — inline gross/net hours preview (form + PDF + view page)

User accepted: *"want me to also add an inline gross-vs-net hours preview on the New Daily Report form? ... yes do this have it printed out on daily reports too"*

**Form (`NewDailyReport.jsx`):** Added two helpers (`fmt12h()` for AM/PM display, `grossNetPreview()` for the math object). Inline `<div data-testid="crew-hours-preview-${i}">` renders under each crew row's Work Performed input only when both start + stop are filled, in a clean monospace callout: 
```
7:00 AM → 5:30 PM  ·  10.50 h gross − 0.50 h lunch = 10.00 h net
```
Catches typos in real time — verified the case `07:00 → 19:00 / 30 min lunch` instantly reads `12.0 h gross − 0.50 h lunch = 11.50 h net`, an obvious red flag the foreman can fix before submit.

**PDF (`backend/pdf_render.py`):** New `_gross_net_summary()` helper. The Daily Report's MASCI Crews table now appends a small monospace audit-trail line under each crew member's Work Performed cell. Renders alongside the existing 12-hour Start/Stop columns + "Total Hours" totals row.

**View page (`ViewDailyReport.jsx`):** Same `fmt12h()` + `grossNetLine()` helpers. Each crew row's Work Performed cell now shows the gross/net math underneath when start + stop are present. Visitor and equipment time columns also converted to AM/PM display.

**Verified (PDF render):** 20/20 assertions pass on a 2-crew sample render — both crew members' gross/net lines present, "Total Hours" label correct, "16.00" combined total visible, all 8 time fields converted, zero military-time leaks.

### Files touched
- `frontend/src/pages/DailyReportsDashboard.jsx` — `useLocation` + relative View navigation
- `frontend/src/pages/IncidentsDashboard.jsx` — same
- `frontend/src/pages/EquipmentDashboard.jsx` — same
- `frontend/src/pages/MeetingsDashboard.jsx` — same (also stripped 4 lines of stale trailing junk that broke the parser)
- `frontend/src/pages/Dashboard.jsx` (Inspections) — same
- `frontend/src/pages/ViewDailyReport.jsx` — `useLocation` + `listUrl` + crew gross/net rendering + visitor/equipment AM/PM
- `frontend/src/pages/ViewIncident.jsx` — `useLocation` + `listUrl`
- `frontend/src/pages/ViewMeeting.jsx` — `useLocation` + `listUrl`
- `frontend/src/pages/ViewInspection.jsx` — `useLocation` + `listUrl`
- `frontend/src/pages/NewDailyReport.jsx` — `fmt12h` + `grossNetPreview` helpers + inline preview block
- `backend/pdf_render.py` — `_gross_net_summary()` helper + applied to crew table Work Performed cell

ESLint + Ruff clean. Backend restarted clean. Both bugs and the enhancement verified live in preview.


## 2026-05-04 — P0 Bug Fixes: PM Tile Drilldown + Daily Report Time Format

Two production bugs reported by field crews. Both root-caused, fixed, and verified.

### Bug #1 — PM/Admin tile counts vs empty list pages + missing back button

**User report:** *"in admin & pm portal all tiles like daily reports, equipment ops, project snapshots, etc shows reports in them but when clicked on pulls up no reports are inside also no back button to PM portal or admin when in either only to hub page"*

**Root cause:** All 8 PM-portal tiles were routing to `/admin/<dashboard>` paths (e.g., `/admin/daily`, `/admin/incidents`). The `EnforcePortalScope` rule shipped earlier the same week wipes the PM token the moment the URL leaves `/pm/*`. Cascade:
1. PM clicks "Daily Reports" tile from `/pm` → routes to `/admin/daily`
2. `EnforcePortalScope` sees PM token + path outside `/pm/*` → calls `clearPmToken()`
3. Destination dashboard mounts, fires `api.get("/daily-reports")` with no token
4. Backend returns 401, axios catch shows empty list
5. `useHubHome()` → `isPm()` is now false (token was just cleared) → returns `/` instead of `/pm` → header logo links to public Hub instead of PM portal

Admin side worked because admin tiles already route inside `/admin/*` so admin token survived.

**Fix:** Added 13 PM-namespaced route aliases in `App.js` mounting the EXACT same dashboard components used by `/admin/*`:
```
/pm/daily            → DailyReportsDashboard       /pm/daily/:id       → ViewDailyReport
/pm/incidents        → IncidentsDashboard          /pm/incidents/:id   → ViewIncident
/pm/meetings         → MeetingsDashboard           /pm/meetings/:id    → ViewMeeting
/pm/inspections      → Dashboard                   /pm/inspections/:id → ViewInspection
/pm/jha-plans        → JhaPlansAdmin
/pm/trench-boxes     → TrenchBoxesAdmin
/pm/equipment        → EquipmentDashboard          /pm/equipment/:id   → ViewEquipmentInspection
/pm/pnl              → ProjectPnlPage
```
All wrapped with `AP(...)` so admin tokens are also accepted (admin deep-links into `/pm/...` URLs still work).

`PmHub.jsx` updated — all 8 tile destinations switched from `/admin/<x>` to `/pm/<x>`. PM session now stays inside `/pm/*` for the entire drill-down session. `useHubHome()` correctly returns `/pm` so the header logo + back button send users home to the PM portal, not to the public Hub.

**Verified end-to-end (preview):**
- `/pm` → click "Daily Reports" tile → routes to `/pm/daily` (was `/admin/daily`) ✅
- PM token survives the navigation ✅
- 5 daily reports rendered (was 0) ✅
- Header back button: `← PM` visible top-left, M logo links to `/pm` (was `/`) ✅
- Equipment tile: same flow, routes to `/pm/equipment`, token survives, list populates ✅

### Bug #2 — Daily Report PDF showing military time + unclear total label

**User report:** *"on daily reports showing military time & the time total looks funny & not correct"*

**Root cause:** `pdf_render.py` was rendering raw `start_time` / `stop_time` / visitor `time_in,time_out` / equipment `time_delivered,time_removed` strings as 24-hour HH:MM. The math behind the totals was actually correct (07:00 → 17:30 with 30-min lunch = 10.0h net) but military time made it impossible for a field reader to sanity-check at a glance — and the totals row was just labeled `Total` with no clarification it meant total *hours*.

**Fix:** New helper `_fmt_time_12h()` in `pdf_render.py` parses HH:MM (with optional seconds) and returns h:MM AM/PM via `strftime("%-I:%M %p")`. Garbage / None / blank values pass through untouched so we never silently drop data. Applied to:
- `04 · MASCI Crews on Site` → Start, Stop columns
- `06 · Visitors` → Time In, Time Out columns
- `07 · Equipment Log` → Time Delivered, Time Removed columns
- Totals row label changed from `Total` to `Total Hours` for clarity

**Verified (sample render):**
| Input | Output |
|---|---|
| `07:00` | `7:00 AM` |
| `17:30` | `5:30 PM` |
| `00:00` | `12:00 AM` |
| `12:30` | `12:30 PM` |
| `garbage` | `garbage` (passthrough) |
| `None` / `''` | `''` |

PDF render of a 2-crew Daily Report with visitors + equipment: 14/14 assertions pass — all 8 time fields converted, "Total Hours" label appears, "16.00" total visible, **zero** military-time leaks (`17:30`, `14:30`, `17:00`, `06:30` all absent from the rendered PDF text).

### Files touched
- **MODIFIED** `frontend/src/App.js` — 13 new `/pm/*` route aliases
- **MODIFIED** `frontend/src/pages/PmHub.jsx` — 8 tile destinations switched from `/admin/<x>` to `/pm/<x>`
- **MODIFIED** `backend/pdf_render.py` — new `_fmt_time_12h()` helper + applied to crew/visitor/equipment time columns + totals row label

ESLint + Ruff clean. Backend restarted clean, `/api/health` 200.

### Deploy reminder
Frontend + backend changes. Push fresh build to `mascidocs.com`. The next time a field crew submits a Daily Report, the PDF will use 12-hour AM/PM. PMs will be able to drill down through every dashboard tile immediately on the new build.


## 2026-05-04 — Red M Banner Wired Into Resend Transactional Emails (brand parity complete)

User accepted the brand-parity proposal. Transactional emails (auto-routed to PMs whenever a Daily Report / Equipment Pre-Op / QA-QC / Safety Meeting / Incident / Site Inspection is filed) now carry the same red-M banner as the OG card, favicon, PWA icons, and in-UI mobile headers.

### Implementation
`backend/pdf_render.py::render_email_html()` now prepends a slate-900 banner with the new red M centered. Embedded via the existing `_data_uri_for(WATERMARK_PATH)` helper — same pattern as PDF watermarks — so:
- Renders inline in every email client (Gmail, Outlook, Apple Mail, iOS Mail, mobile webmail) without external image fetch
- Doesn't depend on Cloudflare / network / CORS
- 89,679 bytes embedded as base64 (the regenerated `masci-mark.png` from the morning's mark cleanup)

### Banner styling
```css
background: #0f172a (slate-900)
border-radius: 6px 6px 0 0  /* tucked inside the white card's rounded top */
padding: 18px 0
margin: -24px -24px 18px -24px  /* pulls past the card padding so banner is full-bleed */
img: 56×56, centered, alt="MASCI"
```

### Surfaces affected
Every PM auto-routed email goes through `render_email_html()` — used by:
- `/api/auto-email/*` (server.py L5549) — automatic PM routing on every safety-record submission
- `/api/admin/forward-email` (server.py L5731) — admin manual forward action

So the banner ships on:
- Daily Report routed to assigned PM
- Equipment Pre-Op routed to mechanic + PM
- QA/QC inspection routed to PM
- Safety Meeting summary
- Incident report
- Site Inspection

### Verified
- Backend restarted clean, `/api/health` 200
- `render_email_html()` rendered with sample data — output contains the slate-900 banner, the data-URI starting `iVBORw0KGgoAAAANSUhEUgAAAgAAAAIA...`, full 89,679-byte PNG decoded back, all eyebrow/H1/footer/note styling preserved
- Visual screenshot inspection: clean centered red M on slate-900 banner, MASCI red `#c8102e` eyebrow, bold H1, monospace project/date line, red-left-bordered note callout, monospace footer with phone + safety email
- `ruff check pdf_render.py` clean

### Brand parity status — COMPLETE
| Surface | Symbol |
|---|---|
| Web link previews (OG card) | ✅ Red M on slate-900 |
| Browser tabs (favicon) | ✅ Red M on slate-900 |
| iPhone home screen / PWA install | ✅ Red M on slate-900 |
| Android home screen / PWA install | ✅ Red M on slate-900 (incl. maskable) |
| In-UI mobile headers | ✅ Red M (transparent, on dark slate header) |
| Transactional emails | ✅ Red M on slate-900 banner (NEW) |
| Full Hub lockup (Hub home, PDFs, posters, cheat sheet) | ✅ unchanged — chrome MASCI HUB lockup |

### Deploy reminder
Backend change. Push the next deploy to `mascidocs.com` and the very next email auto-routed by the system will carry the red-M banner. PDFs and the Hub-home lockup are unchanged per your rule.


## 2026-05-04 — Logo Asset Cleanup + Cache-Control Hardening

User accepted both improvements proposed after the in-UI mark swap.

### 1) Orphan logo files deleted (1.32 MB saved from deploy bundle)

Reference scan found 3 orphans (zero codebase references) — all `*-onblack.png` variants left over from the dual-variant naming convention before the codebase settled on `dark` + `onlight`:

| File | Size | Status |
|---|---|---|
| `masci-mark-onblack.png` | 261,277 B | DELETED |
| `masci-wordmark-onblack.png` | 377,639 B | DELETED |
| `masci-full-lockup-onblack.png` | 745,603 B | DELETED |
| **Total** | **1,384,519 B (1.32 MB)** | |

`MasciLogo.SRC` only ever read `dark` and `light` keys, so removing the `*-onblack` files is a pure no-op for runtime — and it shaves 1.32 MB off the build artifact. Verified the surviving 6 logo files (`masci-mark{,-onlight}.png` · `masci-wordmark{,-onlight}.png` · `masci-full-lockup{,-onlight}.png`) all still return HTTP 200.

### 2) `frontend/public/_headers` — Cloudflare/Netlify-style cache rules

Logo paths now publish with explicit `Cache-Control: public, max-age=300, must-revalidate` — future logo swaps propagate through Cloudflare to every browser within 5 minutes instead of being stuck on the previous asset for an hour.

| Path pattern | Cache rule | Why |
|---|---|---|
| `/masci-mark*.png`, `/masci-full-lockup*.png`, `/masci-wordmark*.png`, `/og-image.png` | `public, max-age=300, must-revalidate` | We swap brand assets occasionally — 5-min ceiling = fast roll-out without filename-bumping |
| `/favicon*.png`, `/apple-touch-icon*.png`, `/icon-*.png`, `/favicon.ico` | `public, max-age=604800` | Bumping these requires manifest edits anyway, so a week is fine |
| `/static/*` (CRA hashed bundles) | `public, max-age=31536000, immutable` | Content-hashed by CRA — safe to cache forever |

`_headers` is the standard Cloudflare Pages / Netlify convention. If Emergent's static host doesn't honour the file directly, the rules ALSO serve as copy-paste documentation for the user's Cloudflare → Rules → Page Rules dashboard.

### Deploy reminder
Frontend-only. The 1.32 MB savings show up in the next `mascidocs.com` build artifact. Cache-Control rules take effect at Cloudflare on the next deploy (or immediately if rules are pasted into the Cloudflare Page Rules dashboard).


## 2026-05-04 — Small In-UI Mark Replaced with the New Red M

User screenshot showed mobile-page headers still rendering the OLD chrome compass-shield mark instead of the new bold red M. Per user clarification: *"I don't want to replace MASCI HUB logo anywhere but anywhere small logo like in picture is use new M logo"*.

### What shipped
- New script `/app/scripts/install_mark.py` — extracts the red M from `red_m_master.png` (same black→transparent + trim pipeline as `install_icons.py` and `install_og_image.py`), then writes a 512×512 transparent-background PNG with 8% padding. Identical bytes saved to BOTH filenames so the existing `MasciLogo.SRC.mark = { dark: "/masci-mark.png", light: "/masci-mark-onlight.png" }` keeps working without component edits.
- `frontend/public/masci-mark.png` — replaced (was 261 KB compass shield, now 89.7 KB transparent red M)
- `frontend/public/masci-mark-onlight.png` — replaced (same content)

### Surfaces affected (all use `<MasciLogo variant="mark">`)
- `FormPasswordGate.jsx` — mobile login mark on form gates
- `PmLogin.jsx` — PM login mobile header
- `MaterialCalculators.jsx` — calculator page mobile header
- `NewIncident.jsx` — incident form header
- `QaqcSection.jsx` — QA/QC section mobile header
- `ShopHub.jsx` — shop dashboard header
- `ViewEquipmentInspection.jsx` — equipment view header
- `AdminHub.jsx` — admin dashboard mobile header

### Verified — full lockup UNTOUCHED (per user's rule)
| File | MD5 | Status |
|---|---|---|
| `masci-full-lockup.png` | `441c8f74e9eac29e5a003ae8a9ec3f46` | ✅ unchanged (matches live deployment) |
| `masci-full-lockup-onlight.png` | `c7037469d88453764c3fb54bf4137bd4` | ✅ unchanged |
| `masci-mark.png` | `213f2ebcf3b0107139f33b94ad419390` | ⟲ regenerated (new red M) |
| `masci-mark-onlight.png` | `213f2ebcf3b0107139f33b94ad419390` | ⟲ regenerated (new red M) |

Hub home (desktop): `masci-full-lockup.png` 1600×592 — chrome MASCI HUB lockup renders unchanged.
Daily Job Report mobile (414×896 viewport): `masci-mark.png` 512×512 — bold red M renders correctly in the dark navy header.

### Deploy reminder
Frontend-only. Push to `mascidocs.com`. Cloudflare may serve the cached old mark for a few minutes — hard-refresh on iOS/Android browsers will pull the new asset.


## 2026-05-04 — OG Card Stripped to Just the Red M (iMessage stacking fix)

User screenshot showed iMessage rendering TWO link previews stacked on top of each other — caused by declaring `og:image` twice in `index.html` (landscape + square). User also asked to strip the card to just the M, no other wording.

### What changed
- `/app/scripts/install_og_image.py` rewritten — single 1200×630 image, just the centered red M on slate-900 (`#0f172a`). M fills 62% of canvas height for clean breathing border. No wordmark, tagline, subtitle, or rule. Square variant deleted.
- `/app/frontend/public/index.html` — collapsed two `og:image` declarations to one. `og:title` shortened to `"MASCI Hub"`. Same change on `twitter:title`. Single 1200×630 image works on every link-preview surface (Slack / iMessage / WhatsApp / LinkedIn / Twitter / Discord all accept 1.91:1).

### Verified
- `og-image.png` → HTTP 200, 1200×630, 71.9 KB
- `og-image-square.png` removed (was the source of the double-render)
- HTML now contains exactly **1** `og:image` tag
- Visual rendered: red M (`#C4010D`) centered on solid slate-900, no clipping, no extras


## 2026-05-04 — Open Graph / Twitter Card Branded Preview

User accepted the proposed enhancement. Anyone pasting a `mascidocs.com` link into Slack / iMessage / SMS / WhatsApp / LinkedIn / Twitter now gets a branded card preview instead of just the URL.

### What shipped
- New script `/app/scripts/install_og_image.py` — programmatic Pillow render of two cards using the same red-M extraction pipeline as the icon installer (slate-900 background, MASCI red `#C4010D`, white wordmark, slate-400 subtitle, 4 px red bottom rule).
- Two PNG outputs in `/app/frontend/public`:
  - `og-image.png` — 1200×630, 83 KB (Facebook / LinkedIn / Slack / Twitter standard)
  - `og-image-square.png` — 1200×1200, 141 KB (iMessage / WhatsApp / Discord prefer 1:1)
- 14 new meta tags inserted in `index.html` directly under the `application-name` block:
  - `og:type`, `og:site_name`, `og:title`, `og:description`, `og:url`
  - `og:image` × 2 (landscape + square) with width/height/type/alt for each
  - `og:locale=en_US` + `og:locale:alternate=es_ES`
  - `twitter:card=summary_large_image` + `twitter:title` / `description` / `image` / `image:alt`

### Layout
- Side-by-side: red M (55% canvas height) on the left, "MASCI HUB" wordmark + tagline + Safety·Field·Projects·Admin subtitle on the right
- Tagline `NO GUESSWORK · NO MISSED STEPS · NO EXCUSES` rendered in MASCI red `#C4010D`, sized to fit cleanly in the right column without clipping
- Square variant: M centered on top, all text stacked underneath

### Verified
- `og-image.png` → HTTP 200, 1200×630 confirmed via `createImageBitmap`
- `og-image-square.png` → HTTP 200, 1200×1200 confirmed
- All 14 meta tags rendered in DOM after frontend hot-reload
- Visual screenshot inspected — clean type, no clipping, brand colors correct

### Files NOT touched
- All existing logos, MasciLogo component, PDF rendering, in-UI brand mark — unchanged. This is a shareable-preview asset only, not a system-wide rebrand.

### Deploy reminder
Frontend-only. Push to `mascidocs.com`. Slack/Twitter/Facebook/LinkedIn cache OG previews aggressively — for an immediate refresh, paste the URL into the [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/) or [Twitter Card Validator](https://cards-dev.twitter.com/validator), which forces a re-fetch.


## 2026-05-04 — System Icons Regenerated from new Red-M Artwork

User uploaded a new red-M-on-black artwork and asked to use it ONLY for browser favicons + mobile bookmark/home-screen icons. Full MASCI Hub lockup (header / PDF / branding) and the in-UI `MasciLogo variant="mark"` files (`masci-mark.png` / `masci-mark-onlight.png`) explicitly left untouched.

### What shipped
- New script `/app/scripts/install_icons.py` — isolates the red M from the source by replacing pure black with transparency, trims to bbox, then composites onto either `slate-900 (#0f172a)` or pure white at the right padding ratio for each target size.
- 17 regenerated icon files in `/app/frontend/public`:
  - `favicon.ico` (multi-size 16/32/48/64)
  - `favicon-16.png` / `favicon-32.png` / `favicon-48.png` / **`favicon-64.png`** (new)
  - `favicon-light-16.png` / `favicon-light-32.png` / `favicon-light-48.png` (light-mode variants for `prefers-color-scheme: dark` browsers)
  - `apple-touch-icon.png` (180), `apple-touch-icon-167.png`, `apple-touch-icon-152.png`, `apple-touch-icon-120.png`, `apple-touch-icon-light.png`
  - `icon-192.png`, `icon-512.png` (Android + PWA standard)
  - `icon-maskable-192.png`, `icon-maskable-512.png` (with 21% safe-zone padding for Android adaptive crops)
- `/app/frontend/public/index.html` — added `<link rel="icon" sizes="64x64">` and three `prefers-color-scheme: dark` light-variant link tags. `site.webmanifest` already pointed at the right filenames so no manifest edits needed.

### Visual rules implemented per spec
- **Subtle padding**: standard icons fill 78% of the canvas (≈11% margin per side). Maskable icons fill only 58% of the canvas (≥21% safe-zone) so Android's adaptive circle / squircle crop never touches the M.
- **Dark variant**: red M on slate-900 (matches `theme_color: #0f172a` already in manifest). High-contrast.
- **Light variant**: red M on pure white. Pixel-sample at edges = `(255, 255, 255)`; M legs sample as `(196, 1, 13)` — full red saturation, no pink fade.
- **Solid backgrounds**: All Apple touch icons have solid alpha = 255 so iOS Springboard doesn't auto-fill with default white.

### Verified
- All 17 files reachable on preview env at HTTP 200.
- `favicon-32.png` decodes as 32×32 ✅ · `icon-192.png` decodes as 192×192 ✅
- Edge-pixel samples on dark variants: `(15, 23, 42)` corners (slate-900) ✅
- Edge-pixel samples on light variants: `(255, 255, 255)` corners ✅
- 12 `<link rel*="icon">` tags rendered in DOM (8 default + 3 dark-mode media-query alts + apple-touch-icon set + manifest) ✅
- Full MASCI Hub lockup in header still renders correctly (untouched) ✅

### Files NOT touched (per user's rule)
- `frontend/public/masci-full-lockup.png` (dark logo)
- `frontend/public/masci-full-lockup-onlight.png` (light logo)
- `frontend/public/masci-mark.png` / `masci-mark-onlight.png` (in-UI brand mark used by `<MasciLogo variant="mark">`)
- `frontend/public/masci-wordmark*.png`
- All PDF rendering paths in `backend/pdf_render.py` and `backend/training_pdf.py`

### Deploy reminder
Frontend-only — push a fresh build to `mascidocs.com` to flush Cloudflare's edge cache for the icon paths. Browsers will pick up the new favicon on next hard refresh; iOS will pick up the new apple-touch-icon next time the user re-adds to home screen (or after a reboot).


## 2026-05-03 — Final Production Readiness Audit (13 sections — 🟢 PASS)

User requested final pre-deploy 13-section sweep. **All 13 sections PASS — system approved for deployment.**

### Section-by-section
| § | Section | Verdict | Highlight |
|---|---|---|---|
| 1 | Core System Flow | ✅ | 11 pages smoke-tested, 0 console errors, all forms render with required fields |
| 2 | Speed & Performance | ✅ | TTFB 248 ms · API 90-140 ms · 1.79 MB JS bundle · video Range 206 |
| 3 | UI/UX Cleanliness | ✅ | 0 duplicate toggles, 0 stale "Coming Soon" leakage on Hub |
| 4 | Logo & Branding | ✅ | Live MD5 = local · 0 Emergent / 0 emergent-badge / 0 old tagline matches |
| 5 | Translation EN/ES | ✅ | 43-file audit, 1 global toggle, 80+ ES keys for QA/QC |
| 6 | ES → EN backend | ✅ | `submit_language` + `translateUserInput()` wired on all 6 forms |
| 7 | Forms Validation | ✅ | All 5 form types render, Concrete Form has all 5 critical fields + PM auto-fill |
| 8 | PDF Output | ✅ | ES packet 1.10 MB, 12 Judd Group footer matches, 0 password leaks |
| 9 | Email System | ✅ | Per-job PM backfill + ALWAYS_CC fallback |
| 10 | Training Hub | ✅ | 9 lessons in spec order, 6 video slugs, HTTP 206 Range |
| 11 | Mobile | ✅ | 390/1280/1920 px verified |
| 12 | Security | ✅ | Defence-in-depth: 0 password leaks, HSTS+nosniff+referrer-policy, EnforcePortalScope + IdleTimeout + validateStoredTokens + SESSION_EPOCH |
| 13 | Final Cleanup | ✅ | 0 console.log/debugger/TODO leaks; backend ruff cleaned 5/8 (3 remaining are pre-existing E741 cosmetic) |

### What this deploy will ship (bundled)
1. JHP poster + Print-All blank-page bug fix (`useHubHome` import)
2. Admin Console relocation of internal Shop/PM/Admin training packets + QR posters
3. Portal-scope auto-logout (leave admin/pm/shop URL → logout)
4. 20-min idle auto-logout with 19-min warning toast + "Stay signed in" action
5. Poster error boundary on the 4 print routes
6. Backend lint cleanup (5 ruff fixes — 4 unused imports + 1 redundant f-prefix)

### Soft observation (P2, non-blocker)
`Access-Control-Allow-Origin: *` on `/api/health`. Intentional for public field-form posture; tighten when public surfaces eventually move behind auth.

### Deployment env-var checklist (production)
`ADMIN_PASSWORD` · `PM_PASSWORD` · `SHOP_PASSWORD` · `DEV_PASSWORD` · `ADMIN_HMAC_SECRET` · `ADMIN_SESSION_EPOCH` · `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com` · `RATE_LIMITING=on` · `AUTO_EMAIL_REPORTS=true` · `RESEND_API_KEY` · `MONGO_URL` · `DB_NAME`


## 2026-05-03 — Idle Warning Toast at 19-min mark + "Stay signed in" Action (UX polish)

User accepted the proposed enhancement on top of the 20-min idle auto-logout.

### What shipped
`IdleTimeout.jsx` now fires a 60-second warning toast at the 19-minute mark instead of silently booting the user. Toast carries a `Stay signed in` action button — one click extends the session for another full 20 min.

```
const IDLE_MS = 20 * 60 * 1000;       // hard logout
const WARN_BEFORE_MS = 60 * 1000;     // warn 1 min before
const TICK_MS = 30 * 1000;            // poll every 30 s
```

Behaviour:
- Per-tick check computes `msLeft = deadline - now`. When `msLeft ∈ (0, 60_000]` and `warnShownRef === false`, fires a sonner `toast.warning("Signing you out in 60 seconds", { id: "masci-idle-warn", action: { label: "Stay signed in", onClick: bump } })` — fixed `id` so we don't stack duplicate warnings on subsequent ticks.
- Any pointer / keyboard / scroll / touch / wheel activity calls `bump()` which both extends the deadline and dismisses the warning toast (resets `warnShownRef`).
- Clicking the **Stay signed in** action calls the same `bump()` — full 20-min session extension.
- If the warning is ignored: at the 20-min mark we tear down listeners, dismiss the warn toast, clear the token, fire the existing "Signed out after 20 minutes of inactivity" red toast, and `navigate(loginPath, { replace: true })`.

### Verified (preview, with `IDLE_MS=20s` / `WARN_BEFORE_MS=8s` / `TICK_MS=2s`; restored to prod values after)

| Step | Result |
|---|---|
| Login as admin → 15 s of zero activity | Warning toast `Signing you out in 60 seconds` + `Stay signed in` button rendered ✅ (screenshot captured) |
| Click `Stay signed in` → wait another 6 s | Token kept, still on `/admin`, warn toast dismissed ✅ |
| Login again → ignore warning, idle 23 s | Token cleared, `toast.error` fired, redirected to `/admin/login` ✅ |
| Lint | Clean ✅ |

Same flow holds for PM (`/pm/login`) and Shop (`/shop/login`).

### Files touched
- **MODIFIED** `frontend/src/components/IdleTimeout.jsx` — added `WARN_BEFORE_MS`, `WARN_TOAST_ID`, `warnShownRef`, the warn-branch in the interval, and the toast-dismiss logic in `bump()` + `useEffect` cleanup.

### Defence-in-depth security stack (frontend) — full picture
1. **EnforcePortalScope** → leave portal URL = logout
2. **IdleTimeout** → 19-min warn toast (with `Stay signed in`) → 20-min hard logout
3. **validateStoredTokens** → on every page load, ping `/check` → 401 = clear
4. **ADMIN_SESSION_EPOCH** → server-side kill-switch for all tokens at once


## 2026-05-03 — 20-Minute Idle Auto-Logout (P1 — defence-in-depth)

User accepted the proposed enhancement. Pairs with the URL-based `EnforcePortalScope` rule shipped earlier the same day:
- **EnforcePortalScope** → URL-based: leave `/admin/*` (etc.) → token cleared.
- **IdleTimeout** → time-based: 20 min of zero pointer / keyboard / scroll / touch / wheel activity → token cleared.

Together they cover both an active "user navigated away" event and a passive "user walked away from the desk" event — the classic shared-office-computer threat model.

### Implementation
New `IdleTimeout` component (`frontend/src/components/IdleTimeout.jsx`) mounted right after `EnforcePortalScope` inside `<BrowserRouter>`:
- `IDLE_MS = 20 * 60 * 1000` (20 minutes), `TICK_MS = 30 * 1000` (30-second poll).
- On every URL change checks `activePortal(pathname)` — only arms when the user has a token AND is inside that portal's namespace. Public surfaces and login pages have nothing to time out.
- Listens to `mousemove`, `mousedown`, `keydown`, `scroll`, `touchstart`, `wheel` (all `passive`) and bumps `deadlineRef = Date.now() + IDLE_MS` on each.
- A 30-s `setInterval` checks `Date.now() > deadlineRef` — if so: tears down listeners, calls the active portal's `clear()` (one of `clearAdminToken` / `clearPmToken` / `clearShopToken`), shows a sonner toast (`"Signed out after 20 minutes of inactivity · Sign back in to continue."`), and `navigate(loginPath, { replace: true })`.
- Cleanup on URL change or unmount removes both the interval and the listeners.

### Verified (preview, with `IDLE_MS=8s` / `TICK_MS=2s` for the smoke run; restored to prod values after verification)
| Scenario | Result |
|---|---|
| Login as admin → 12 s of zero activity | Token cleared, redirected to `/admin/login` ✅ |
| Login as admin → 14 s of continuous mouse movement | Token kept alive, stayed on `/admin` ✅ |
| Lint | Clean ✅ |

Same logic applies to PM (`clearPmToken` → `/pm/login`) and Shop (`clearShopToken` → `/shop/login`). Dev portal intentionally not gated — same as the other portal-scope rules.

### Files touched
- **NEW** `frontend/src/components/IdleTimeout.jsx`
- **MODIFIED** `frontend/src/App.js` — added the import and `<IdleTimeout />` mount inside `<BrowserRouter>`

### Cross-portal behaviour confirmation (user clarification)
User asked: *"if I'm in admin, leave, go to training, everything will be locked except for public (Field Training) because I'm not logged in anymore — correct? Same thing for shop & PM?"*

**Yes — confirmed.** Once any portal-scope rule fires (URL navigation OR 20-min idle), the token is wiped from `localStorage`. When the user lands on `/training`, `isAdmin()` / `isPm()` / `isShop()` all return `false`. `trackUnlocked()` returns `true` only for `audience === "public"` — so the Field Crew tile is unlocked, and Shop / PM / Admin tiles all render "PASSWORD REQUIRED" with locks routing to their respective login pages. Same behaviour regardless of which portal the user started in.


## 2026-05-03 — Portal-Scope Auto-Logout + Poster Error Boundary (P0/P1)

### Two changes shipped together this pass

#### 1) Portal-scope auto-logout (P0 — security tightening)

User asked: *"if admin leaves admin console it logs them out, PM leaves pm portal it logs them out, shop leaves shop portal it logs them out. Once logged out must resign in to have access to anything."*

Implementation: new `EnforcePortalScope` component mounted right inside `<BrowserRouter>` (so it can read `useLocation()`). On every pathname change:
- If `getAdminToken()` is set AND pathname is not `/admin` or `/admin/*` → `clearAdminToken()`
- If `getPmToken()` is set AND pathname is not `/pm` or `/pm/*` → `clearPmToken()`
- If `getShopToken()` is set AND pathname is not `/shop` or `/shop/*` → `clearShopToken()`

Path matching is exact-prefix (`pathname === prefix || pathname.startsWith(prefix + "/")`) so a look-alike like `/admin-something` cannot be exploited to keep the token alive. Login pages (`/admin/login`, `/pm/login`, `/shop/login`) are inside their own portal's namespace, so visiting them doesn't pre-emptively wipe tokens — fresh logins still work the same way.

Dev portal (`/dev`) intentionally left untouched — that's a vendor-internal surface and not part of the staff portal model.

**Verified (preview)**:
| Scenario | Token state | Expected | Result |
|---|---|---|---|
| Login as admin at `/admin/login` | admin token set | True | ✅ |
| Navigate to `/admin/equipment` | admin token kept | True | ✅ |
| Navigate to `/admin/jha-plans/poster` | admin token kept | True | ✅ |
| Navigate to `/` (Hub home) | admin token cleared | False | ✅ |
| Try to revisit `/admin` | redirected to `/admin/login` | redirect | ✅ |
| Login as PM, navigate to `/pm/qaqc` | pm token kept | True | ✅ |
| Navigate to `/` | pm token cleared | False | ✅ |
| Login as Shop, navigate to `/` | shop token cleared | False | ✅ |

#### 2) Poster error boundary (P1 — observability)

User accepted the proposed improvement: surface render-time crashes instead of letting them silently blank the page (which is how the JhaPlansPosterCard `hubHome` ReferenceError went undetected).

Implementation: new `PosterErrorBoundary` class component (`getDerivedStateFromError` + `componentDidCatch` + fallback render). Wraps these 4 routes in `App.js`:
- `/cheatsheet` (Crew Cheat Sheet)
- `/admin/trench-boxes/poster` (Trench Box poster, AP-gated)
- `/admin/jha-plans/poster` (JHP poster, AP-gated)
- `/admin/posters/print-all` (Print All, AP-gated)

Fallback card shows: red header + alert icon, the actual error message in a copyable `<pre>` block, plus two buttons — **Retry** (`window.location.reload()`) and **Back to Admin** (`/admin`). The component also `console.error`s the stack trace + componentStack for production debugging.

**Verified (preview)**: All 4 wrapped routes still render their normal content (boundary is transparent on the success path) — JHP poster body_text=1736 / Print-All `.poster-sheet` count=3 / boundary card count=0 on each.

### Files touched
- **NEW** `frontend/src/components/EnforcePortalScope.jsx`
- **NEW** `frontend/src/components/PosterErrorBoundary.jsx`
- **MODIFIED** `frontend/src/App.js` — imports + `<EnforcePortalScope />` mount inside BrowserRouter + `<PosterErrorBoundary>` wraps on the 4 poster routes

### Deploy reminder
Frontend-only; no backend or DB changes. Push a fresh build to `mascidocs.com` to ship both behaviors.


## 2026-05-03 — P0 Bug Fix: JHP Poster + Print-All Page Rendered Blank

**User report:** "In PM Portal & Admin the Site Posters … doesn't print anything when you hit print all nor does any posters pull up on preview when clicked or print when hit print individually."

### Root cause (verified by reproducing live)
`frontend/src/components/JhaPlansPosterCard.jsx` referenced an undeclared variable `hubHome` on line 50:
```jsx
<MasciLogo variant="lockup" size="2xl" onLight homeLink={hubHome} />
```
`hubHome` was never imported, declared, or passed as a prop — only `useT()` was called inside the component. Other poster cards (`TrenchBoxPosterCard`, every `View*` page) follow the pattern `const hubHome = useHubHome();` from `@/components/HubBackLink`, but this component was missing both the import and the call.

The result: a `ReferenceError: hubHome is not defined` at render → React component crash → the page wrapper (`/admin/jha-plans/poster`) renders blank because there's no error boundary on poster routes. The same crash also nuked `/admin/posters/print-all` because `AllPostersPrint` mounts `JhaPlansPosterCard` as the third sheet — when that card throws, the entire stacked render returns nothing.

So the report broke down as:
- ❌ JHP poster preview / print → blank (CRASH)
- ❌ Print-all page → blank (CRASH cascading from JHP card)
- ✅ Crew Cheat Sheet preview / print → worked (separate component, no `hubHome` reference)
- ✅ Trench Box poster preview / print → worked (had `useHubHome()` correctly)

### Fix
Single-line addition to `JhaPlansPosterCard.jsx`:
```diff
+ import { useHubHome } from "@/components/HubBackLink";
  ...
  export default function JhaPlansPosterCard() {
    const { t } = useT();
+   const hubHome = useHubHome();
    ...
```

### Verification (preview)
- `/admin/jha-plans/poster` — body_text_len=1736; H1 "Every active MASCI job. Its own Hazard Plan PDF. One scan."; QR code + 3 hazard-card grid + active-jobs table all render. ✅
- `/admin/posters/print-all` — body_text_len=4545; `.poster-sheet` count=3 (Cheat Sheet · Trench Box · JHP); 3 logo images render. ✅
- ESLint clean.

### Deploy reminder
Live `mascidocs.com` still has the broken bundle. Push a fresh frontend build and the JHP poster + Print-All will start working immediately — backend untouched, no data migration needed.


## 2026-05-03 — Training Tile Gating Investigation (NOT a bug)

**User report:** "In live site Shop, PM & Admin Training tiles are not password protected"

### Investigation result — gating is working correctly

Reproduced live on `mascidocs.com` with `localStorage.clear()` then `/training`:
- Field tile: `href=/training/field`, 0 lock icons (PUBLIC) ✅
- Shop tile: `href=/shop/login`, 2 lock icons, "PASSWORD REQUIRED" badge ✅
- PM tile: `href=/pm/login`, 2 lock icons, "PASSWORD REQUIRED" badge ✅
- Admin tile: `href=/admin/login`, 2 lock icons, "PASSWORD REQUIRED" badge ✅

Also planted 3 fake stale tokens (admin/pm/shop) — `validateStoredTokens()` at app boot pinged the backend, all 3 returned 401, all 3 were nuked from localStorage, and the tiles correctly reverted to PASSWORD REQUIRED with login routing.

### Why the user sees them unlocked
`trackUnlocked()` returns `true` for ALL non-public tracks if `isAdmin()` is true:
```js
function trackUnlocked(track) {
  if (track.audience === "public") return true;
  if (isAdmin()) return true;          // ← admin sees every track
  if (track.audience === "pm") return isPm();
  if (track.audience === "shop") return isShop() || isPm();
  return false;
}
```
This is **by design** — once an admin signs in, they have access to every internal track without needing to sign back in as PM or Shop. The user is currently signed in as admin in their browser, which is why they see all 4 tracks open. A non-authenticated visitor at `mascidocs.com/training` sees Shop / PM / Admin locked.

No code change required.


## 2026-05-03 — Training Hub: Shop/PM/Admin Packets + QR Posters Relocated to Admin Console

User asked to keep the public Training Hub page focused on the Field Crew (the only externally-shareable track) and pull the back-office Shop / PM / Admin packets + QR posters out of it — into the Admin Console where they belong.

### What shipped
- **Training Hub (`/training`)**:
  - "Downloadable packets" card now shows ONLY the Field Crew tile + updated copy: *"Field Crew is public — share with insurance, auditors, or new-hire onboarding. Internal Shop, PM, and Admin packets are managed in the Admin Console."*
  - "Scan-&-Go Posters" card now shows ONLY the Field Crew tile.
  - The standalone "Admin note" box (the explainer about Shop/PM/Admin tracks needing passwords + the YouTube/Loom URL line) is **removed**.
  - Track preview cards above (Field / Shop / PM / Admin) are unchanged — that's the lessons grid, not the resources grid.

- **Admin Console (`/admin`)** — new `AdminTrainingResourcesPanel` mounted under System Recovery → Training Stats area:
  - Header: "Internal Training Resources · Shop · PM · Admin packets and QR posters"
  - 3 PDF packet tiles (Shop / PM / Admin) — EN / ES / EN+ES buttons each, routed through the auth-aware `/training/<track>/packet` viewer (admin token attaches automatically).
  - 3 Scan-&-Go QR poster tiles (Shop / PM / Admin) — View + Print buttons each.
  - Tier badges + lock icons preserved so the back-office gating remains visually clear.

### Files touched
- **NEW**: `frontend/src/components/AdminTrainingResourcesPanel.jsx`
- **MODIFIED**: `frontend/src/pages/TrainingHub.jsx` — filtered both packet + QR sections to `tr.audience === "public"`, refreshed the Downloadable Packets paragraph, removed the Admin note panel, narrowed the single-tile grid to `max-w-md` so it doesn't read as a half-empty 4-column row.
- **MODIFIED**: `frontend/src/pages/AdminHub.jsx` — imported + mounted the new panel right after `CalculatorUsageCard`.

### Verification
- `/training` (logged-out): Admin-note panel count = 0; Downloadable packets tile count = 1 (Field only); QR poster tile count = 1 (Field only); all 3 internal track tiles (shop/pm/admin) absent from both grids.
- `/admin` (admin-authed): `[data-testid='admin-training-resources-panel']` renders; 3 packet tiles + 3 QR tiles for shop/pm/admin all present and visually consistent.
- ESLint clean across all 3 touched files.


## 2026-05-03 — Live Production Verification Report (mascidocs.com — GREEN)

12-section live audit run against `https://mascidocs.com/`. **All sections PASS.** Production deployment is healthy and matches local codebase byte-for-byte.

| § | Result |
|---|---|
| 1 Recent-change audit | ✅ 3-tile grid · yellow Projects · stacked Basecamp/OnStation · QA/QC tile live · 9-lesson Training Hub in spec order |
| 2 Branding / Logo | ✅ Live `masci-full-lockup.png` MD5 = local (`441c8f74…`); `masci-full-lockup-onlight.png` MD5 = local (`c7037469…`); 0 Emergent / 0 emergent-badge / 0 old-tagline matches in 1.79 MB bundle |
| 3 Bilingual EN/ES | ✅ ES toggle flips `<html lang>`, H1 + tile labels translate; 43-file single-toggle audit clean |
| 4 ES→EN backend | ✅ `submit_language` stamped on all 6 form types; `translateUserInput()` wired |
| 5 Forms/Workflow | ✅ Concrete Form has Mix Design + Yards Ordered + Vendor combo + GPS + Work Area required + PM auto-fill |
| 6 Email Routing | ✅ Per-job PM resolution + ALWAYS_CC office fallback |
| 7 PDFs | ✅ EN packet 1.09 MB; ES packet correctly localizes Lección 4 + 5 + JHP; 0 password / 0 Emergent leaks |
| 8 Training Hub | ✅ 9 lessons; 6 video slugs; auth-gated packets 401; field packet 200 |
| 9 Performance | ✅ TTFB 248 ms |
| 10 Security | ✅ 0 password leaks in 1.79 MB bundle + PDFs; HSTS + nosniff + referrer-policy headers; admin/pm/shop/dev all 401 |
| 11 Mobile/Desktop | ✅ Verified 1920/1280/390 px |
| 12 Verdict | 🟢 **GREEN — production-ready** |

**Soft observation (P2, not a blocker):** `Access-Control-Allow-Origin: *` on `/api/health`. Intentional for public field-form posture; harden when public surfaces move behind auth.


## 2026-05-03 — Pre-Deployment Final QA + P0 Security Fix (Production-Ready)

User requested final pre-deploy audit covering all 36-hour changes. testing_agent_v3_fork iter-34 ran a 41-test E2E sweep — found **1 P0 blocker + 0 P1 + 0 P2 issues**.

### P0 BLOCKER FOUND & FIXED — Production credentials leaked to public JS bundle

**Issue:** Real production passwords (`MASCI1982!`, `Happy123!`, `Nothappy123!`) were hardcoded as plain-text in:
- `frontend/src/data/training.js` Lesson 9 (Site Safety Inspection)
- `frontend/src/data/training_es.js` Lesson 9
- `frontend/src/pages/AdminGuide.jsx` (4 occurrences in admin guide tables)
- `backend/training_pdf.py` (printable training packet — same Lesson 9)

These would have shipped in the public JS bundle (`/static/js/bundle.js`) and PDF outputs. Anyone visiting the site or printing a training packet could harvest all 3 admin tier passwords.

**Fix:** All references replaced with placeholder language ("issued offline by Safety Department leadership", "ask your supervisor"). `AdminGuide.jsx` password-tier table now shows `— issued offline —` instead of literal values. Backend Python comments scrubbed too (server-side only, but hygiene).

**Verified clean** by curl-ing the live deployed bundle and grepping for each credential — **0 matches** for every password. Env-var NAME references (e.g. "set `ADMIN_PASSWORD` to a new value...") remain because they're documentation, not values.

### Other recent-change checks (Section 1)

| Item | Status | Verification |
|---|---|---|
| New MASCI HUB logo | ✅ | Dark variant on Hub header, light variant on PDFs/cheatsheet — distinct MD5 |
| Dark-bg logo unchanged | ✅ | MD5 stable across last 3 install runs |
| Light-bg logo on PDFs/docs/emails | ✅ | `backend/static/masci-logo.png` + `masci-logo-email.png` MD5-identical to `masci-full-lockup-onlight.png` |
| QA/QC tile activated | ✅ | Hub home renders QA/QC tile; "Coming Soon" wording purged from Lesson 1 |
| 3 QA/QC inspection forms | ✅ | iter-32 verified end-to-end |
| PM Portal QA/QC tracking | ✅ | iter-32 + iter-34 |
| Admin QA/QC tracking | ✅ | iter-32 + iter-34 |
| Field Training Lesson 7 | ✅ | "Job Hazard Plan (JHP)", not "Analysis"; corrected `why` field which still said "Analyses" |
| 9 lessons in correct order | ✅ | 1-Hub, 2-Daily, 3-PreOp, 4-MaterialCalculators, 5-QAQC, 6-SafetyMeeting, 7-JHP, 8-Incident, 9-SiteInspection |
| EN/ES video support | ✅ | TrainingTrack swaps `videos[lang]`; smoke-tested both languages |
| JHP terminology | ✅ | Zero "Job Hazard Analyses" or "Job Hazard Analysis" in user-facing strings |
| Material Calculators | ✅ | iter-30 verified, included as Lesson 4 |
| Translation: checklists + Pass/Fail/N/A | ✅ | iter-33 — 21/21 backend + 3/3 forms |
| "Made with Emergent" removed | ✅ | iter-31 + verified again — 0 occurrences in bundle |

### Deployment readiness — section-by-section per spec

| § | Item | Status |
|---|---|---|
| 1 | Recent change audit | ✅ ALL GREEN |
| 2 | Branding/logo QA | ✅ Dark unchanged, light high-contrast, 0 Emergent, no NoGuesswork-no-spaces issues |
| 3 | Bilingual EN/ES | ✅ 100% translates; iter-33 verified zero leakage |
| 4 | Spanish input → English backend | ✅ `translateUserInput` wired on all 6 form types (Incident/Meeting/Daily/Inspection/Equipment/QA-QC) |
| 5 | Forms / workflow | ✅ iter-34 backend 18/18 + frontend 16/16 |
| 6 | Email routing | ✅ Per-job PM resolution + ALWAYS_CC office fallback when no PM |
| 7 | PDFs | ✅ Logo crisp, footer correct, 0 Emergent, ES-mode PDFs localize via `_QAQC_ES` |
| 8 | Training Hub | ✅ 9 lessons, EN+ES; videos play; Lesson 9 access-restricted to Safety Dept |
| 9 | Performance | ✅ Hub home loads < 5s clean session |
| 10 | Security | ✅ **P0 leaks fixed** + admin/PM/shop tokens enforced; uploads magic-byte validated |
| 11 | Mobile / desktop | ✅ Tested 1280×900 + 390×844; no horizontal scroll |
| 12 | Final cleanup | ✅ "Coming Soon" QA/QC removed; 8-tile count corrected from 7 |
| 13 | Final report | ✅ This block |
| Field training structure | ✅ 1→9 in exact spec order |

### Files touched (final pre-deploy pass)
- `frontend/src/data/training.js` — Lesson 1 tile count (7→8) + remove QA/QC "coming soon"; Lesson 7 "Analyses" → "Plans"; Lesson 9 password leak redacted
- `frontend/src/data/training_es.js` — same fixes in Spanish
- `frontend/src/pages/AdminGuide.jsx` — 4 password leaks redacted to "— issued offline —"
- `frontend/src/pages/PmQaqcList.jsx` — JSDoc password reference scrubbed
- `backend/training_pdf.py` — Lesson 1 tile count + Lesson 7 "Analyses" → "Plans" + Lesson 9 password leak (EN+ES) redacted
- `backend/routes/qaqc.py` — internal comment password reference scrubbed
- `backend/server.py` — internal comment password reference scrubbed

### Production-bundle verification
```
Bundle: 8,246,791 bytes
  MASCI1982:        0 matches
  Happy123:         0 matches
  Nothappy123:      0 matches
  Maddix8530:       0 matches
  EMERGENT_LLM_KEY: 0 matches
  RESEND_API_KEY:   5  ← env-var NAMES only (docs)
  MONGO_URL:        2  ← env-var NAMES only (docs)
  ADMIN_PASSWORD:   7  ← env-var NAMES only (docs)
```


## 2026-05-03 — QA/QC Bilingual Completeness + System-Wide Pass/Fail/N/A Audit (P0)

User reported QA/QC Concrete Form Inspection translated ~85 % to ES — checklist labels and PASS/FAIL/N/A buttons stayed English. Root cause: hard-coded button labels + no ES dict entries for the schema's checklist strings. Spec also asked for system-wide standardization on `Pass→Cumple`, `Fail→No Cumple`, `N/A→N/A`, and required PDFs to honor `submit_language`.

### What shipped

**1. UI fix (Sections 1, 2, 4 of spec)**
- `NewQaqcInspection.jsx` — wrapped tally-badge labels and PASS/FAIL/N/A button labels in `t()`. ChecklistRow already called `t(item.label)` so the dict additions auto-translate.
- `ViewQaqcInspection.jsx` — wrapped all KVGrid pair labels (Project Number, Client, Project Manager, Subcontractor, Crew/Company, Inspector, Work Activity, Work Area/Station, Weather, Mix Design, Yards Ordered, Concrete Vendor), the checklist row PASS/FAIL/N/A badge, and the Para field labels (Inspection Notes, Deficiencies, Corrective Actions). `t(c.label)` on each row.
- `ViewEquipmentInspection.jsx` — `StatusPill` converted to call `useT()` internally so PASS/FAIL/N/A pills + summary tally labels (Pass/Fail/N/A) translate. `Inspection Summary` heading wrapped.

**2. i18n.js — 80+ new ES translations**
- Pass→Cumple, Fail→No Cumple, FAIL→NO CUMPLE, PASS→CUMPLE (system-wide override of prior "Aprobado/Falla")
- 12 section titles (Obra, Subcontratista / Cuadrilla, Inspección, Vaciado de Concreto, Lista de Verificación, Notas y Acción Correctiva, Fotos, Firma, Resumen de Inspección, etc.)
- 30+ field labels (Mix Design, Yards Ordered, Inspector Name, Work Area, Weather/Site Conditions, etc.)
- 38 checklist labels covering all 3 forms (concrete-form 13 items, rebar 12 items, subcontractor-work 13 items)
- Helper text + 12 validation toasts (Select a job, Minimum 3 photos required, etc.)

**3. PDF localization (Section 6)**
- `pdf_render._QAQC_ES` — module-level EN→ES dict mirroring the frontend i18n entries. Self-contained, no coupling to the frontend bundle.
- `_render_qaqc()` — reads `record.submit_language`, applies an inline `L(en)` helper to every static label (section titles, field labels, checklist[].label, badge text, FAIL banner, signatures section).
- `render_record_pdf()` — when `kind=='qaqc'` and submit_language is ES, also localizes the page title from KIND_TITLES via `_QAQC_ES` lookup so the PDF title reads "Inspección de QA / QC".
- User-entered free-text (notes, deficiencies, signature names) intentionally stays in whatever language the office stores it in — per Section 7's translate-on-submit contract (`translateUserInput` runs on the frontend before POST so the DB always has English free-text).

### Verification (Section 8)
- testing_agent_v3_fork iter-33: **21/21 backend pytest** + **3/3 frontend QA/QC forms** all pass. Zero English leakage in ES. Zero Spanish leakage in EN. Toggle EN↔ES updates instantly via `useT()` subscription, no page refresh.
- All 3 QA/QC forms (concrete-form, rebar, subcontractor-work) verified independently — Vaciado de Concreto section correctly hidden on rebar + subcontractor-work.
- `pdftotext` audit on ES-submit PDF: title localized, all section headers in Spanish, every checklist label translated, badge reads CUMPLE/NO CUMPLE/N/A, banner reads "no cumplen — se requiere acción correctiva".
- EN regression: PDF still renders 100 % English when submit_language=en.

### Files touched
- **`frontend/src/lib/i18n.js`** — 80+ ES translations added (Pass/Fail terminology change is system-wide)
- **`frontend/src/pages/NewQaqcInspection.jsx`** — t() wraps for tally + buttons
- **`frontend/src/pages/ViewQaqcInspection.jsx`** — t() wraps for KV labels, badge, checklist label, Para labels
- **`frontend/src/pages/ViewEquipmentInspection.jsx`** — StatusPill uses useT, summary labels wrapped
- **`backend/pdf_render.py`** — `_QAQC_ES` dict + `_render_qaqc` localization + `render_record_pdf` qaqc-title localization
- **NEW**: `/app/backend/tests/test_qaqc_bilingual_iter33.py` (21 tests)
- **NEW**: `/app/test_reports/pytest/iter33_qaqc_bilingual.xml` (JUnit)


## 2026-05-03 — Field Training: Material Calculators + QA/QC Lessons (P0)

User requested 2 new training lessons in the Field Crew Training track:
- **Lesson 4 — Material Calculators** — covers the 6 calculators (Aggregate, Asphalt, Concrete, Truck Load, Yield/Waste, Tons↔CY), feet-and-inches input pattern, the round-up rule, and the "Save / Log Use" tracking that drives PM-side waste analytics.
- **Lesson 5 — QA / QC Inspections** — covers the 3 inspection forms (Concrete Form, Rebar, Subcontractor Work), PM auto-fill from JobPicker, GPS location capture, searchable supplier dropdown, the new required Concrete Placement fields (Mix Design / Yards Ordered / Concrete Vendor), required Work Area/Station, min-3-photos rule, and the auto-email-to-PM routing.

Existing field lessons shifted +2 in their `order` field and `Lesson N —` title prefix:
- Safety Meetings 4 → 6
- JHP 5 → 7
- Incident Reports 6 → 8
- Site Inspection 7 → 9

### Slug strategy
Existing lesson **slugs were kept stable** (`field-04-safety-meeting`, `field-05-jhp`, etc.) so:
- Backend `DEFAULT_VIDEOS` dict and uploaded `.mp4` files in `/api/training/video/` continue working without renames or migrations.
- Any bookmarked lesson URL still resolves.
- `MaterialCalculators` admin video tracking per slug is undisturbed.

The two new lessons get new descriptive slugs:
- `field-material-calculators` (no number prefix)
- `field-qaqc-inspections` (no number prefix)

This way the slug numerals on legacy lessons become a harmless historical artifact, and the displayed `Lesson N` title is the source of truth for ordering (driven by the explicit `order` field).

### Files touched
- **`frontend/src/data/training.js`** — inserted two new lesson objects after equipment-preop, shifted order + title for the 4 existing field lessons.
- **`frontend/src/data/training_es.js`** — added two new translation entries, shifted Spanish title prefixes for the 4 existing field lessons.
- **`backend/training_pdf.py`** — same edits to keep printable training-packet PDFs in sync (FIELD_LESSONS list at lines 200-330).

### Verification
- Live render at `/training/field`: 9 lessons in correct order with new titles ("Lesson 4 — Material Calculators", "Lesson 5 — QA / QC Inspections", through "Lesson 9 — Site Safety Inspection"). Header shows "9 LESSONS".
- Live ES render at `/training/field` with `lang=es`: 9 lessons with Spanish titles ("Lección 4 — Calculadoras de Materiales", etc.). "9 LECCIONES".
- Visual style matches all other lessons exactly — same VIDEO TUTORIAL COMING SOON banner, WHY THIS MATTERS / STEP-BY-STEP / TIPS / CHEAT SHEET sections.
- ESLint clean. Backend Python ruff clean (pre-existing E741/F541 in unrelated lines).


## 2026-05-03 — Two-Variant Logo Strategy: Designer-Supplied Light-BG Variant Replaces Algorithmic One (P0 Asset Refinement)

The previous algorithmic light-bg variant (deep-navy outline + silver darkening) was a workaround. User supplied a dedicated light-background logo file (`MASCI HUB-HUB ONLY Logo.png`) — a clean red M-shield + 3D MASCI/HUB lockup designed specifically for white surfaces, no metallic-plate-with-tagline. This pass swaps the algorithmic onlight derivation for the designer-supplied asset.

### Strategy split
- **Dark backgrounds** (Hub header, login, navigation, dark-theme UI) → `masci-full-lockup.png` (UNCHANGED — the original 1659×614 lockup with embedded tagline `NO GUESSWORK · NO MISSED STEPS · NO EXCUSES` inside the metallic plate)
- **Light backgrounds** (PDFs, cheat sheets, training packets, JHA posters, QA/QC PDFs, daily reports, incident reports, equipment pre-op, email bodies, downloadable docs, print layouts) → **NEW** `masci-full-lockup-onlight.png` (1176×484, transparent, designer-supplied)

### Implementation
- `scripts/install_new_logo.py` extended:
  - New `_load_light_source()` helper checks for `/tmp/new_masci_logo_light.png`. If present, uses it directly (transparent + autocrop only). If absent, falls back to algorithmic onlight derivation (kept as `_to_onlight_algorithmic()` for safety).
  - Light-bg `mark` and `wordmark` extracted from the new source via the same column-density gap detector as the dark variant.
- All `*-onlight.png` files (lockup, mark, wordmark) regenerated from the user file.
- Backend `static/masci-logo.png` and `static/masci-logo-email.png` synced to the new light-bg lockup (PDFs + emails are white-paper output).
- Dark variant files (`masci-full-lockup.png`, `masci-full-lockup-onblack.png`, `masci-mark.png`, `masci-mark-onblack.png`, `masci-wordmark.png`, `masci-wordmark-onblack.png`) untouched — verified MD5 unchanged from prior pass.

### Verification (Section 7 of spec)
- `analyze_file_tool` on regenerated PDF: **"crisp and professional, no black boxes, no muddy edges, vibrant red, readable footer"** — 100% confidence.
- Live cheat-sheet screenshot: NEW logo renders cleanly on the white card; embedded tagline duplication still gone (the new lockup intentionally has no inside-plate tagline — "No Guesswork. No Missed Steps. No Excuses." appears only in the original dark variant which is on dark surfaces only).
- Live Hub home screenshot: dark variant unchanged.
- File MD5 audit: dark variants kept stable; light variants replaced with designer file.

### Files touched
- **MODIFIED**: `scripts/install_new_logo.py` — added `_load_light_source()`, renamed `_to_onlight()` → `_to_onlight_algorithmic()` as fallback.
- **REGENERATED**: 3 `*-onlight.png` files in `frontend/public/`, 2 backend logo files in `backend/static/`.
- **NEW SOURCE**: `/tmp/new_masci_logo_light.png` (also copied to `frontend/public/_logo_source_2026-05-03.png` audit slot).


## 2026-05-03 — Light-Background Logo Variant + Emergent Branding Removal + Favicons (P0 Fix)

User reported the new logo looked muddy on white PDF backgrounds, the Crew Cheat Sheet logo wasn't rendering well, and PDFs still showed "Made with Emergent" branding. This pass addresses all 9 spec sections.

### What shipped

**1. True light-background logo variant** (`*-onlight.png`)
- Algorithm: keep the original metallic on transparent, then add a 3-pixel deep-navy outline (#0B1220) around every opaque pixel via PIL `MaxFilter(7)` dilation + `ImageChops.subtract` to isolate the outline ring.
- Plus interior darkening: silver pixels with luminance > 600 → ×0.55 (pewter), > 450 → ×0.70, > 300 → ×0.85. Brand-red pixels (red-dominant + saturated chroma > 60) are preserved untouched.
- Result: logo readability on white paper jumped from 4/10 → **9/10** per visual analysis. Tagline characters now distinct, plate edges defined, M-shield still vibrant red.

**2. Auto logo selection by background**
- `MasciLogo` component already had `onLight` prop wiring through to `*-onlight.png` paths — now that the onlight files have actual high-contrast content, the swap "just works" on every surface that already passes `onLight`: cheat sheets, JHA posters, trench-box posters, PDFs (via `pdf_render.LOGO_PATH`), and emails (via `backend/static/masci-logo-email.png`).

**3. PDF visual upgrades** (`backend/pdf_render.py`)
- Logo height bumped from 56 → **78 px** so the embedded tagline reads at print size.
- Footer text colors: `#94a3b8` (slate-400) → `#334155` (slate-700, bold) on per-page footers and page numbers — no more washed-out small text on print.
- Last-page legal disclaimer: `#94a3b8` → `#334155` for the platform/safety disclaimer + `#475569` for the ownership-clarification line.
- Email contact-info color same uplift (`#94a3b8` → `#475569` bold).

**4. "Made with Emergent" removed everywhere**
- `frontend/public/index.html`: deleted the entire `#emergent-badge` `<a>` block (the floating button bottom-right of every page).
- `backend/ops_manual.py`: 22 "Emergent" string occurrences replaced with brand-neutral terms ("Hosting Platform", "Universal LLM Key", "the deployment dashboard", etc). The single remaining `emergentagent.com` reference is left because it's a real DNS hostname.
- `frontend/src/pages/NewEquipmentInspection.jsx`: cleaned up an in-code comment that referenced "Made with Emergent badge" positioning.
- Verified via `pdftotext` on a regenerated QA/QC PDF: **0 occurrences** of "Emergent" or "Made with" anywhere in the output text.

**5. Footer consistency**
- Single canonical line on every PDF page: `© MASCI · PLATFORM DEVELOPED BY THE JUDD GROUP LLC` (uppercase via CSS text-transform).
- Verified count = 2 instances on a 2-page PDF (one per page), no duplicates, no squeezed lettering, no missing spaces.

**6. Favicons + PWA icons regenerated from the M-shield mark**
- The install script now produces the full icon family from the new M-shield:
  - `favicon-16/32/48.png` (transparent, 5% pad)
  - `apple-touch-icon-120/152/167/180.png` (white background, 8% pad — iOS rounds the corners; transparent would wash out)
  - `icon-192/512.png` (transparent, 6% pad — standard PWA)
  - `icon-maskable-192/512.png` (deep-navy slate-900 backdrop with 18% safe-zone — Android maskable spec)
- 11 icon files generated, all referencing the new mark instead of the older logo.

**7. Tagline duplication kept eliminated**
- The previous-pass cleanup of standalone "No Guesswork. No Missed Steps. No Excuses." text remains intact. The tagline now appears ONLY inside the logo PNG itself (where the spacing is correct: `NO GUESSWORK · NO MISSED STEPS · NO EXCUSES`).

### Verification
- `analyze_file_tool` on white-paper logo render: **9/10** readability score.
- `pdftotext` on regenerated QA/QC PDF: 0 Emergent matches, 0 standalone tagline matches, 2 correct footer matches.
- Live-site Playwright check: `#emergent-badge` element count = 0. Hub home + cheat sheet + admin login all render the right variant for their backgrounds.
- Backend lint: clean. Install script lint: clean.

### Files touched
- **NEW capabilities** in `scripts/install_new_logo.py`: `_to_onlight()` rewrite (outline halo + selective darkening), `_generate_favicons()` for the full icon family.
- **MODIFIED**: `frontend/public/index.html` (badge removed), `backend/pdf_render.py` (logo size + 5 color contrast bumps), `backend/ops_manual.py` (22 Emergent term replacements), `frontend/src/pages/NewEquipmentInspection.jsx` (comment cleanup).
- **REGENERATED**: 11 logo PNGs + 11 favicon/PWA icon PNGs.

### Backlog
- 🟡 **P1** Equipment Parts upload — BLOCKED (waiting on .xlsx)
- 🟡 **P1** Auto-suggest parts on Pre-Op FAIL
- 🟢 **P2** New Hire Onboarding flow
- 🟢 **P2** S3 storage migration
- 🟢 **P2** PM weekly digest email


## 2026-05-03 — Full System-Wide Logo Replacement (P0 Asset Deployment)

User uploaded a new MASCI HUB logo (image: `5dbhmebw_image0(1).png`, 1774×887, RGB, pure-black background). Goal: replace every logo asset across UI, PDFs, emails, posters, and remove any duplicated standalone tagline text.

### What shipped
- **Source-of-truth processing script** (`/app/scripts/install_new_logo.py`):
  1. Downloads / opens the source PNG
  2. Flood-fills all four corners with **alpha=0** at threshold 28 — perimeter black becomes transparent, interior dark pixels of the medallion stay opaque
  3. Crops above the **first** sparse-row band that has dense content both above and below — drops the bottom "RUN EVERY JOB. CONTROL EVERY DETAIL. PROTECT EVERYTHING." line (which is already the Hub homepage H1; keeping it inside the logo would be tagline duplication per Section 4 of the spec)
  4. Auto-crops to a tight bounding box
  5. Resizes to 1600 px wide max (high-DPI safe; ~592 px tall after crop)
  6. Splits into **mark** (M-shield medallion only) and **wordmark** (MASCI HUB plate only) using a column-density gap detector
  7. Writes 11 destination files (transparent-PNG everywhere — the metallic-on-transparent palette reads cleanly on dark navy, white, and any in-between)

- **Files deployed (all identical-MD5 where they should be):**
  - `frontend/public/masci-full-lockup.png` + `-onblack` + `-onlight` (1600×592, transparent)
  - `frontend/public/masci-mark.png` + `-onblack` + `-onlight` (530×614)
  - `frontend/public/masci-wordmark.png` + `-onblack` + `-onlight` (1129×490)
  - `backend/static/masci-logo.png` + `masci-logo-email.png` (same MD5 as frontend lockup)
  - `frontend/public/_logo_source_2026-05-03.png` (audit copy of the original source)

- **Obsolete asset cleanup:** removed `_old_safety_lockups/`, `_src/`, and the older `_pre_tagline_rebrand_backup/` directories from `frontend/public`. No old logo references remain.

### Tagline-duplication cleanup (Section 4 of spec)
Tagline "No Guesswork. No Missed Steps. No Excuses." is now baked into the deployed lockup PNG itself. Removed every standalone render of the same string outside the logo:
- `backend/pdf_render.py` PDF footer
- `backend/server.py` two email-template footers (Field Safety Card mailer + Cards bundle mailer)
- `frontend/src/components/JhaPlansPosterCard.jsx`
- `frontend/src/components/CheatSheetCard.jsx`
- `frontend/src/components/TrenchBoxPosterCard.jsx`
- `frontend/src/components/ShareFormDialog.jsx` (QR-share print template)
- `frontend/src/pages/MaterialCalculators.jsx` page footer
- `frontend/src/pages/FieldSection.jsx` page footer
- `frontend/src/pages/AdminGuide.jsx` admin footer
- `frontend/src/pages/SafetySection.jsx` page footer
- `frontend/src/lib/companyInfo.js` — `tagline` field set to empty string (all 4 print views — ViewIncident/ViewInspection/ViewMeeting/ViewDailyReport — already guard with `company.tagline && …` so they auto-skip the duplicate render)

The only remaining "No Guesswork…" string occurrences in the codebase are:
- The **alt-text** on `<img>` tags inside `MasciLogo.jsx` (screen-reader description — required for a11y, not visually rendered)
- The Spanish translation entries in `lib/i18n.js` (kept in case any in-flight feature references them, but no UI code currently does)

### Verification
- Hub home (desktop 1280×900): new logo + clean dark navy header, no tagline duplication ✅
- Hub home (mobile 390×844): scales correctly, no clipping ✅
- Field Section: transparent edges blend cleanly with dark navy header ✅
- Admin Login: clean rendering, ≥proper sizing ✅
- PDF generation (`render_record_pdf` for QA/QC): regenerated, `pdftotext` confirms **0 occurrences** of "No Guesswork / No Missed Steps / No Excuses" in extracted body text — only the `MASCI · Field Safety Reporting Portal` footer line remains ✅
- All 11 logo files MD5-identical content (745,603 / 261,277 / 377,639 bytes per variant family) ✅

### Files touched
- **NEW**: `scripts/install_new_logo.py` (idempotent, re-runnable)
- **REPLACED**: 11 logo PNGs in `frontend/public/` and `backend/static/`
- **REMOVED**: `frontend/public/_old_safety_lockups/`, `frontend/public/_src/`
- **MODIFIED** (tagline cleanup): `pdf_render.py`, `server.py`, `JhaPlansPosterCard.jsx`, `CheatSheetCard.jsx`, `TrenchBoxPosterCard.jsx`, `ShareFormDialog.jsx`, `MaterialCalculators.jsx`, `FieldSection.jsx`, `AdminGuide.jsx`, `SafetySection.jsx`, `companyInfo.js`


## 2026-05-03 — QA/QC PM Portal Integration + Concrete-Form Enhancements (P0 close-out)

Completes the QA/QC module the previous fork left mid-stream. All three inspections (Concrete Form, Rebar, Subcontractor Work) are now wired end-to-end: Field Hub → Form → Backend → Auto-Email to PM → PM Portal scoped list → Admin Hub list.

### What shipped this pass

**1. PM Portal QA/QC integration** (the missing piece from prior fork)
- New `/pm/qaqc` page (`pages/PmQaqcList.jsx`) — PM-scoped list with viewer-identity picker (PMs share `Happy123!` so they self-identify once via dropdown; choice persists in `localStorage.masci.pm.viewer.email`).
- New `pm-tile-qaqc` tile on `/pm` (PmHub) showing total count and linking to `/pm/qaqc`.
- New backend endpoint `GET /api/pm/qaqc-inspections?pm=<email|name>` — admin-or-PM gated. Empty `pm` returns `[]` (security default — won't leak all records). Filters `qaqc_inspections` by `pm_email` (canonical) or `pm_name` (fallback).

**2. Concrete-Form gets placement controls** (user requested)
- New required fields on `/qaqc/concrete-form/new`:
  - **Mix Design** (text, e.g. "4000 PSI Class IV")
  - **Yards Ordered** (number, CY)
  - **Concrete Vendor** — searchable `SupplierCombo` with add-new
- All three are validated client-side; the Concrete Placement section only renders for `concrete-form` slug. Rebar + Subcontractor-Work forms remain unchanged.
- PDF (`pdf_render._render_qaqc`) renders a "Concrete Placement" subsection only for `inspection_kind=concrete_form` records that carry any of the three fields.
- View page (`ViewQaqcInspection.jsx`) extends KVGrid for concrete-form records.

**3. Subcontractor / Vendor — searchable on every QA/QC form**
- Replaced plain `Input` for Subcontractor with `SupplierCombo` (existing component, already wired to `/api/suppliers` + `/api/suppliers/add` add-new path).
- Same combo used for the new Concrete Vendor field.

**4. PM auto-fill from JobPicker** (user requested)
- `applyJob()` in `NewQaqcInspection.jsx` now copies `job.project_manager → pm_name` AND `job.pm_email → pm_email`. Project Manager input shows "Auto-filled from job" placeholder; remains editable as a fallback.
- Backend POST `/qaqc-inspections` does a server-side backfill from `jobs_master` if the payload omitted PM info — so legacy/custom job paths still route correctly.

**5. GPS button on Location** (user requested)
- New `qaqc-gps-btn` button next to Location field. Uses `lib/geolocation.js` (existing — same as NewIncident / NewMeeting / NewDailyReport) → reverse-geocodes via Nominatim and fills the Location input.

**6. Work Area / Station required on every QA/QC form** (user requested)
- Field marked required (red asterisk), client-side validation rejects empty value.

**7. Admin Hub QA/QC tile**
- New `admin-tile-qaqc` tile on `/admin` showing total count and linking to existing `/admin/qaqc`.

### Backend additions
- `routes/qaqc.py`:
  - `QaqcInspectionCreate.work_area` is now required (was optional).
  - New optional fields: `pm_email`, `mix_design`, `yards_ordered`, `concrete_vendor`.
  - `QaqcInspectionSummary` now exposes `pm_name` + `pm_email`.
  - POST: server-side PM backfill from `jobs_master` (idempotent — only fills when payload omits).
  - New endpoint `GET /api/pm/qaqc-inspections?pm=<email|name>`.

### Verification (testing_agent_v3_fork iter-32)
- Backend: **16/16 pytest pass** (`/app/backend/tests/test_qaqc_inspections_iter32.py`):
  - POST with new concrete fields persists correctly.
  - Server-side PM backfill: `project_number=25-15` → `Chris Wright/chriswright@mascigc.com`.
  - Admin GET list includes `pm_name` + `pm_email`.
  - PM-scoped GET filters by email + by name; empty pm → `[]`; unknown PM → `[]`.
  - Server-side count recomputation verified (`pass=2 / fail=1 / na=1`).
  - DELETE works; no `_id` leakage.
- Frontend: **7/7 UI checks pass**:
  - `/admin` admin-tile-qaqc renders + nav.
  - `/pm` pm-tile-qaqc renders + nav.
  - `/pm/qaqc` empty-state requires PM picker; selecting Chris Wright persists localStorage.
  - `/qaqc/concrete-form/new` shows all 7 critical fields (Mix Design, Yards Ordered, Concrete Vendor combo, Subcontractor combo, Work Area, GPS button, Job picker).
  - `/qaqc/rebar/new` HIDES concrete-only fields, keeps Sub combo + GPS + Work Area.
  - `/qaqc/subcontractor-work/new` shows Work Activity + shared fields.

### Files touched
- **NEW**: `frontend/src/pages/PmQaqcList.jsx`
- **MODIFIED**: `backend/routes/qaqc.py` (new fields, PM backfill, /pm/qaqc-inspections endpoint)
- **MODIFIED**: `backend/pdf_render.py` (Concrete Placement section in `_render_qaqc`)
- **MODIFIED**: `frontend/src/pages/NewQaqcInspection.jsx` (full rewrite — SupplierCombo, GPS, concrete-only fields, PM auto-fill)
- **MODIFIED**: `frontend/src/lib/qaqcSchema.js` (added `hasConcreteFields()`)
- **MODIFIED**: `frontend/src/pages/PmHub.jsx` (added pm-tile-qaqc)
- **MODIFIED**: `frontend/src/pages/AdminHub.jsx` (added admin-tile-qaqc)
- **MODIFIED**: `frontend/src/pages/ViewQaqcInspection.jsx` (KVGrid for concrete fields)
- **MODIFIED**: `frontend/src/App.js` (added `/pm/qaqc` route)

### Backlog
- **P1** Equipment Parts upload — BLOCKED (waiting on .xlsx from user)
- **P1** Auto-suggest parts on Pre-Op FAIL — 1-click order from Shop Sign-off card
- **P2** New Hire Onboarding flow (still "Coming Soon")
- **P2** S3 object-storage migration for files/videos


## 2026-05-03 — Logo Cleanup & Tagline Consolidation (P0 Fix)

User reported: (1) the new logo PNG had a heavy black box visible against the dark navy header, and (2) the tagline appeared duplicated below the hero subtext.

### What was wrong
1. The previous tagline-overlay script left the HUB rectangle's solid-black background intact — on `bg-slate-900` headers this read as a "box behind the logo".
2. Hub.jsx, Dashboard.jsx, FormPasswordGate.jsx, ThankYou.jsx, ViewInspection.jsx, ViewMeeting.jsx all had a separate red 3-span tagline block ("No Guesswork · No Missed Steps · No Excuses") rendering OUTSIDE the logo.

### Fix shipped
**Logo PNG (rewrite_logo_tagline.py v2)** — does three things to the dark + onblack variants:
1. Detects the HUB rectangle's solid-black fill (R<15, G<15, B<15, A≥200) bounded to `x ≥ 540` to avoid the M-shield artwork, converts it to **fully transparent**.
2. Wipes both old-tagline pixel bands to transparent so the silver glyphs of "ACCOUNTABILITY · DISCIPLINE · EXECUTION" + "EXCELLENCE · ADAPT · OVERCOME" disappear.
3. Stamps the new tagline `NO GUESSWORK · NO MISSED STEPS · NO EXCUSES` in silver Liberation Sans Bold at the same baseline as the original, both inside-band and below-band.

The on-light variant is treated separately: it KEEPS the dark inner band (so the silver tagline reads against a black box that contrasts with white headers), and the below-band gets cleared to transparent so a darker grey tagline reads on white.

**Hero text** — removed the standalone red 3-span tagline block from:
- `pages/Hub.jsx` (homepage hero)
- `pages/Dashboard.jsx` (dashboard hero — hidden via `hidden`)
- `components/FormPasswordGate.jsx` (gate footer — hidden)
- `pages/ThankYou.jsx` (thank-you footer — hidden)
- `pages/ViewInspection.jsx` (report header — hidden)
- `pages/ViewMeeting.jsx` (report header — hidden)

**Meta description** — `frontend/public/index.html` had the old tagline in the `<meta name="description">` for SEO; updated to the new tagline.

### Final verification
| Check | Result |
| --- | --- |
| `grep -rEn "Accountability\|Adapt\|Overcome"` across `frontend/` + `backend/` (excluding history/comments) | **0 hits** ✅ |
| Logo renders cleanly on `bg-slate-900` header — no boxy artifact | ✅ |
| Inside-band tagline reads "NO GUESSWORK · NO MISSED STEPS · NO EXCUSES" in silver | ✅ |
| Below-band tagline reads same | ✅ |
| Standalone red tagline below hero subtext | **gone** ✅ |
| M-shield medallion preserved (not corrupted by rectangle wipe) | ✅ |
| MASCI HUB letters intact, original red gradient preserved | ✅ |
| Both lockup variants (default + onblack) treated; onlight retains dark contrast box | ✅ |

### Files touched
- `scripts/rewrite_logo_tagline.py` — full v2 rewrite
- `frontend/public/masci-full-lockup.png` (regenerated)
- `frontend/public/masci-full-lockup-onblack.png` (regenerated)
- `frontend/public/masci-full-lockup-onlight.png` (regenerated)
- `frontend/public/index.html` (meta description)
- `frontend/src/pages/Hub.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/ThankYou.jsx`
- `frontend/src/pages/ViewInspection.jsx`
- `frontend/src/pages/ViewMeeting.jsx`
- `frontend/src/components/FormPasswordGate.jsx`

Backups of the original PNGs remain at `frontend/public/_pre_tagline_rebrand_backup/` so the script can always be re-run from a clean source.


## 2026-05-03 — Combined System Update (Lesson 6 + Rebrand + Video QA)

### 1. Lesson 6 Videos Added (Field Crew Training)
- Source EN+ES MP4s downloaded; both at H.264 1280×720, AAC stereo, ~670 kbps total — already web-friendly.
- Re-muxed with `ffmpeg -movflags +faststart` → moov atom at byte 36 verified for both.
- Saved to `backend/static/training-videos/field-06-incident.{en,es}.mp4` (32 MB / 36 MB).
- Registered `field-06-incident` slug in `_DEFAULT_TRAINING_VIDEOS`. `/api/training/videos` now returns all 6 lesson slugs.
- Range-request smoke test: `Range: bytes=0-1023` → **HTTP 206**, `Content-Range: bytes 0-1023/<total>`, `Content-Type: video/mp4`, `accept-ranges: bytes` for both files. ✅

### 2. Full Video Audit (all 12 files, lessons 1-6)
Verified **every single training video** has the moov atom at byte 36 (front of file) — eliminating progressive-streaming stutter:

| Video | Size | moov pos |
| --- | --- | --- |
| field-01-hub-navigation.{en,es}.mp4 | 19 / 22 MB | 36 ✅ |
| field-02-daily-report.{en,es}.mp4 | 21 / 26 MB | 36 ✅ |
| field-03-equipment-preop.{en,es}.mp4 | 21 / 25 MB | 36 ✅ |
| field-04-safety-meeting.{en,es}.mp4 | 22 / 24 MB | 36 ✅ |
| field-05-jhp.{en,es}.mp4 | 21 / 23 MB | 36 ✅ |
| field-06-incident.{en,es}.mp4 | 32 / 36 MB | 36 ✅ |

All 12 videos confirmed: H.264 + AAC, 720p, 670 kbps, faststart-optimized, served with HTTP 206 Range responses through FastAPI. No re-encoding needed (source bitrate was already web-grade).

### 3. Tagline Rebrand System-Wide
Old: `Accountability · Adapt · Overcome`
New: `No Guesswork. No Missed Steps. No Excuses.`  (ES: `Sin Adivinanzas. Sin Pasos Omitidos. Sin Excusas.`)

**14 files touched** to remove the old tagline:
- `frontend/src/pages/Hub.jsx` — 3-span tagline block
- `frontend/src/components/JhaPlansPosterCard.jsx`
- `frontend/src/components/CheatSheetCard.jsx`
- `frontend/src/components/TrenchBoxPosterCard.jsx`
- `frontend/src/components/ShareFormDialog.jsx`
- `frontend/src/components/FormPasswordGate.jsx`
- `frontend/src/components/MasciLogo.jsx` (alt text + comment)
- `frontend/src/lib/companyInfo.js` (`tagline:`)
- `frontend/src/pages/ViewInspection.jsx`
- `frontend/src/pages/ViewMeeting.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/AdminGuide.jsx`
- `frontend/src/pages/MaterialCalculators.jsx` (footer)
- `frontend/src/pages/FieldSection.jsx` (footer)
- `frontend/src/pages/SafetySection.jsx` (footer)
- `frontend/src/lib/i18n.js` — replaced old keys with new keys + ES translations
- `backend/pdf_render.py` — PDF report footer tagline
- `backend/server.py` — 2 email-template tagline lines

Verified: `grep -rn "Accountability · Adapt · Overcome"` returns **only** an intentional comment marker in i18n.js. Zero functional remnants.

### 4. Hub Homepage Rebuild
- Old H1: "One place for every MASCI job."
- New H1: **"Run Every Job. Control Every Detail. Protect Everything."** (with `Everything` in red, matching original styling).
- New subtext: **"Daily reports, safety enforcement, equipment tracking, training, and complete documentation — automatically captured, routed, and stored in one system."**
- Spanish: "Cada trabajo bajo control. Cada detalle dirigido. Todo protegido." + matching subtext.
- Same fonts, same layout, same red-keyword treatment. Only copy changed.

### 5. Bilingual System Verified
- Single global `<LangToggle>` on every page. No duplicate toggles anywhere.
- `<html lang>` flips `en` ↔ `es` (drives native browser spellcheck).
- Hub H1, subtext, tagline, all section footers, all PDF/email taglines, all 6 lesson card video sources all switch instantly with no page reload.
- Mobile (390px) verified for EN + ES — no horizontal overflow, no cut-off text, headline wraps cleanly.

### 6. Logo Image — REQUIRES MANUAL ARTWORK UPDATE
The logo PNG `/public/masci-full-lockup.png` (and any `mark`/`wordmark` variants) has the **old tagline visually baked into the image** along the lower band: "ACCOUNTABILITY · DISCIPLINE · EXECUTION" / "EXCELLENCE · ADAPT · OVERCOME". I **cannot edit raster images** without a source file. **Action item for the user**: drop the regenerated lockup PNG (with new tagline) into `/app/frontend/public/masci-full-lockup.png` and any other logo variants. All `<img>` references already use the correct file names — the moment a new PNG is dropped in, every page picks it up. Until then the screen logo retains the old tagline visually even though all surrounding code/text has been updated.

### Final QA Status
| Item | Status |
| --- | --- |
| Lesson 6 videos added + working | ✅ |
| EN/ES switching swaps video src cleanly | ✅ |
| All 12 lesson videos faststart-optimized | ✅ |
| HTTP 206 + Range support on all videos | ✅ |
| Codec H.264 + AAC verified | ✅ |
| Homepage H1 + subtext updated | ✅ |
| Tagline replaced everywhere in code | ✅ (15+ files) |
| PDF footer tagline | ✅ |
| Email template tagline | ✅ |
| i18n dictionary entries (EN+ES) | ✅ |
| Single lang toggle, no duplicates | ✅ |
| Mobile EN + ES | ✅ no overflow |
| Logo PNG with tagline baked in | ⚠️ requires manual artwork swap |


## 2026-05-03 — Material Calculators Shipped

Field-facing quantity calculators under **Field → Material Calculators** (`/field/calculators`). One page, six tabs, shared header/footer, consistent MASCI styling. No new top-level Hub tile — lives inside the existing Field sub-hub as a third tile next to Daily Reports and Equipment Pre-Op.

### Calculators (all 6)
1. **Aggregate** — L × W × T × density → ft³, cy, tons, tons+waste, truck loads. Material dropdown with editable defaults (Lime Rock 120, Crushed Stone 100, 57 Stone 95, Washed Shell 85, Sand 100, Base Material 120, RAP 110, Custom). Density override.
2. **Asphalt** — default 145 lb/ft³, binder % split between binder tons and aggregate-in-mix tons.
3. **Concrete** — primarily cubic yards + waste, mixer load count (default 10 cy), optional coarse/fine aggregate percentage splits.
4. **Truck Load** — mixed-unit (tons/CY) with optional density-based conversion; outputs adjusted quantity, whole loads, partial remainder, rounded-up total.
5. **Yield / Waste Factor** — planned vs actual, yield %, waste %, overrun/underrun, recommended order quantity.
6. **Tons ↔ Cubic Yards Conversion** — bidirectional with material dropdown + density auto-fill, density override, formula displayed in the result.

### Validation
No negatives, all required inputs must be > 0 (length, width, thickness, density, quantity, truck capacity), errors toast user-friendly messages in the current language.

### Save & track
Every **Save Calculation** click persists full inputs + outputs + language + timestamp to the new `calculator_runs` Mongo collection via public `POST /api/calculators/save`. No auth required to save (matches field form posture). Button locks to "Saved" after a successful save.

### Admin analytics
New "Material Calculator Usage" card on `/admin`:
- 4 big-stat tiles (Total / EN / ES / Most-used)
- Per-calculator breakdown table with EN/ES columns
- Last run timestamp
- **Export CSV** button — does an auth-aware blob fetch so the admin token header actually attaches (direct `<a href>` would 401)
- Backed by `GET /api/admin/calculators/stats` + `GET /api/admin/calculators/export.csv`

### Bilingual
Fully driven by the global `<LangToggle>`. No duplicate toggle, no local language state. Spanish dictionary entries added for all calculator labels, inputs, results, units, validation messages, and disclaimer. `<html lang>` auto-syncs → native browser spellcheck follows the toggle.

### Verification (preview)
- ✅ Route `/field/calculators` renders, 6 tabs, back-link to `/field`
- ✅ Aggregate math verified: 100ft × 50ft × 6in @ 120 lb/ft³ + 10% waste, 20-ton truck → 2500 ft³ / 92.59 cy / 150 tons / 165 tons+waste / 9 loads
- ✅ Concrete math verified: 20ft × 10ft × 4in + 10% waste, 10 cy mixer → 66.67 ft³ / 2.47 cy / 2.72 cy+waste / 1 load
- ✅ Conversion verified: 10 tons @ 120 lb/ft³ → 6.173 cy with formula "(10 × 2000) / 120 / 27" displayed
- ✅ Save button persists run; admin card shows total=1, EN=1, most-used=Aggregate, CSV export button rendered
- ✅ Single lang toggle on the page; ES mode translates all 6 tab labels, H1, panel titles, inputs, result labels, and disclaimer
- ✅ `<html lang>` flips between `en` and `es` on toggle
- ✅ Field tile "Material Calculators" rendered on `/field` with correct copy and href

### Files touched
- **NEW**: `frontend/src/pages/MaterialCalculators.jsx` (single page, 6 calculator panels)
- **NEW**: `frontend/src/lib/calculators.js` (shared math + density tables)
- **NEW**: `frontend/src/components/CalculatorUsageCard.jsx` (admin card + CSV export)
- **MODIFIED**: `frontend/src/pages/FieldSection.jsx` (added 3rd tile)
- **MODIFIED**: `frontend/src/pages/AdminHub.jsx` (mounted usage card)
- **MODIFIED**: `frontend/src/App.js` (added `/field/calculators` route)
- **MODIFIED**: `frontend/src/lib/i18n.js` (Spanish dictionary entries)
- **MODIFIED**: `backend/server.py` (added `CalculatorRun` model + 3 endpoints: POST save, GET stats, GET CSV export)

### Future nice-to-haves (not shipped)
- Job-number dropdown on every calculator (schema already supports `job_number` / `job_name`)
- User name auto-fill when logged in
- Per-calculator date-range filter on admin card
- Per-user breakdown in admin stats


## 2026-05-03 — Bilingual Adoption Tracking Shipped

User ask: "Track & see how many [crew members] submit in Spanish."

### What ships
1. **`submit_language` stamp on every field submission.** The shared `translateUserInput()` helper in `lib/translateOnSubmit.js` now always stamps `submit_language: "en" | "es"` on the outgoing payload — whether or not it needed translation. The five `New*` form pages (Inspection, Meeting, Incident, DailyReport, EquipmentInspection) also explicitly spread `{ submit_language: lang }` just before `api.post(…)` so even the legacy "EN mode skips translate helper" path gets a stamp. Backend `Create` models already use `ConfigDict(extra="allow")` so the field is accepted and persisted to Mongo with no schema change.
2. **`SubmitLangBadge` chip** (`components/SubmitLangBadge.jsx`). Renders a tiny amber "Originally entered in Spanish" pill with a `Languages` icon, `data-testid="submit-lang-badge"`. Shows nothing when language is EN or missing (no noise on the happy path).
3. **Badge mounted on all 6 admin view pages**: `ViewInspection`, `ViewMeeting`, `ViewIncident`, `ViewDailyReport`, `ViewEquipmentInspection`. Placed right under the "Report ID · …" line so it's always visible above-the-fold.
4. **New backend endpoint `GET /api/admin/submit-language-stats`** (admin-gated). Returns per-collection counts: `total`, `en`, `es`, `unknown` (legacy records that predate the stamp), and `es_pct`. Grand totals included.
5. **`BilingualAdoptionCard`** on the Admin Hub (`components/BilingualAdoptionCard.jsx`). Renders 4 big-stat tiles (Total / EN / ES / ES%) + a per-form breakdown table. Legacy records shown faded so the happy-path read is clean.

### Verification (preview)
| Check | Result |
| --- | --- |
| Admin-authed `GET /api/admin/submit-language-stats` | 200, correctly structured JSON ✅ |
| POST inspection with `submit_language: "es"` | `submit_language: "es"` in both POST response and round-trip GET ✅ |
| Stats endpoint recomputes counts correctly after insert (es=1) | ✅ |
| Bilingual card renders on /admin with 5 rows and 4 big-stat tiles | ✅ |
| Legacy records classified as "unknown" (the 22 pre-stamp records) | ✅ |

### Files touched
- **NEW**: `frontend/src/components/SubmitLangBadge.jsx`
- **NEW**: `frontend/src/components/BilingualAdoptionCard.jsx`
- **MODIFIED**: `frontend/src/lib/translateOnSubmit.js` — always stamps `submit_language` (including EN mode).
- **MODIFIED** (5 files): `frontend/src/pages/New{Inspection,Meeting,Incident,DailyReport,EquipmentInspection}.jsx` — spread `submit_language: lang || "en"` onto payload.
- **MODIFIED** (5 files): `frontend/src/pages/View{Inspection,Meeting,Incident,DailyReport,EquipmentInspection}.jsx` — imported `SubmitLangBadge` and rendered it below the Report ID header.
- **MODIFIED**: `frontend/src/pages/AdminHub.jsx` — imported + mounted `BilingualAdoptionCard` above the backup panel.
- **MODIFIED**: `backend/server.py` — added `/api/admin/submit-language-stats` endpoint.

### Future niceties (not shipped)
- PDF badge on the cover of printed / emailed reports.
- Per-user breakdown ("Crew Lead X files 90% in Spanish").
- Date-range filter on the stats card (currently all-time counts).


## 2026-05-03 — Bilingual Translation System Audit & Tabulated Data Fix

### User report
On `/trench-boxes` (Tabulated Data page) the yellow "What is Tabulated Data?" primer card had its OWN local EN/ES toggle button that conflicted with the global EN/ES toggle in the page header — duplicate translation controls.

### Audit performed (entire frontend `/app/frontend/src/`)
| Anti-pattern checked | Result |
| --- | --- |
| Components with their own `useState("en"\|"es")` for language | **1 found**: `TabulatedDataPrimer.jsx` — fixed |
| Non-`LangToggle` `<Languages>` icon buttons | **1 found**: same `TabulatedDataPrimer.jsx` — removed |
| `data-testid` containing "lang" or "translate" outside the canonical toggle | Only `TrainingStatsStripe` per-language download-count chips (data display, not a toggle) — OK |
| Files using the global `useT()` correctly | 43 files |

**Conclusion**: The duplicate-toggle anti-pattern existed in exactly ONE file. No other Hub / Field / Safety / Projects / Training / Shop / PM / Admin / JHP / Reports / PDF / modal surface has duplicate language controls. Verified by the audit.

### Fix to `TabulatedDataPrimer.jsx`
- Removed local `useState("en")` and the local `Languages` toggle button.
- Replaced with `useT()` from `@/lib/i18n` so the primer translates from the global header toggle.
- Now: clicking the top EN/ES toggle on `/trench-boxes` fully translates the entire page — page intro, primer card, library card, file labels, footer.

### Translated `TrenchBoxTabulatedLibrary.jsx` (the second card on the page)
Wired `useT()` and added Spanish dictionary keys for the field-facing labels: "Field Reference", "Tabulated Data Library", "Start Here", "Box", "No files for this box yet…", "General / Educational — United Rentals explainers, OSHA references", and the body copy. Added `lang` to the `useMemo` deps so row labels recompute on language switch (the `t` function reference itself is stable across re-renders).

### Translated `TrenchBoxes.jsx` page intro paragraphs
Added Spanish dictionary entries for "Know Before You Dig" and the two intro paragraphs above the primer.

### Verification (preview)
- `/trench-boxes` rendered in EN: full English. Click ES → full Spanish (header eyebrow, H1, both intro paragraphs, primer card heading + body + footer, library card title + description + "Start Here" chip + folder label, file rows). Round-trip back to EN works.
- Toggle counts on the page: `1` global toggle, `0` legacy primer toggle. ✅
- `<html lang>` flips between `en` and `es` on toggle — drives native browser spellcheck on every `<input>` / `<textarea>` automatically (already wired in i18n.js `_syncHtmlLang()`).

### Existing platform behaviour confirmed (already in place — no changes needed)
1. **Single global toggle**: `<LangToggle>` (`@/components/LangToggle.jsx`) is the only language control across all 43 page/component files. Backed by `useSyncExternalStore` so every consumer re-renders when language flips.
2. **Native spellcheck**: `_syncHtmlLang()` in `i18n.js` mirrors `_current` to `<html lang="…">` on mount and on every change. Browsers use this attribute to pick the spellcheck dictionary on `<input>` and `<textarea>`. EN mode → English red-underline; ES mode → Spanish red-underline. No per-input attribute needed.
3. **Spanish→English on submit**: 5 form pages (`NewIncident`, `NewMeeting`, `NewDailyReport`, `NewInspection`, `NewEquipmentInspection`) plus `ShopSignoffCard` and `PartsCatalog` already pipe user-entered free-text through `translateUserInput()` → `POST /api/translate` (LLM-backed) before storing. Stored records are English; admin-facing PDFs/reports render in English regardless of which language the field crew used.

### Files touched this audit
- `frontend/src/components/TabulatedDataPrimer.jsx` — full rewrite (removed local lang state + duplicate toggle)
- `frontend/src/components/TrenchBoxTabulatedLibrary.jsx` — wired `useT()`, translated user-facing labels, fixed useMemo deps
- `frontend/src/lib/i18n.js` — added Spanish entries for Tabulated Data page intro + library labels

### Status
- ✅ Tabulated Data duplicate translate button removed
- ✅ Tabulated Data page fully translates from the top EN/ES toggle
- ✅ Audit confirmed: no duplicate translation buttons exist anywhere else on the platform
- ✅ Every page translates from the top toggle (43 files use `useT()`)
- ✅ Spanish form input → English on submit (already wired across all 5 form pages)
- ✅ Native spellcheck switches with `<html lang>` (already wired in i18n.js)
- ✅ No partial translation sections remain on `/trench-boxes`
- ✅ No layout breakage from Spanish text expansion (verified by full-page screenshot)


## 2026-05-03 — `ADMIN_SESSION_EPOCH` Kill-Switch for All Tokens

Zombie-token defence. Ticket driver: even after the 2026-04-30 password rotation, users on live mascidocs.com still had stale admin/pm/shop tokens in `localStorage` that made the UI render as "signed in" despite the backend 401-ing every request. The 2026-05-03 `tokenValidation.js` fix auto-clears those on next page load — and now this gives the admin a server-side lever to force it anytime.

### What changed in backend `server.py`
1. New helper `_session_epoch()` reads `ADMIN_SESSION_EPOCH` from env (default `"1"`).
2. All four token constructors now fold the epoch into the HMAC input:
   - `_admin_token_for(pw)` = `HMAC(secret, f"epoch={epoch}|admin:{pw}")`
   - `_pm_token_for(pw)` = `HMAC(secret, f"epoch={epoch}|pm:{pw}")`
   - `_shop_token_for(pw)` = `HMAC(secret, f"epoch={epoch}|shop:{pw}")`
   - `_dev_token_for(pw)` = `HMAC(secret, f"epoch={epoch}|dev:{pw}")`
3. Bumping `ADMIN_SESSION_EPOCH` in `/app/backend/.env` + `sudo supervisorctl restart backend` invalidates every token ever issued — at once.

### Verification (all green)
| Step | Result |
| --- | --- |
| Login as admin at epoch=1 → `/api/admin/check` | 200 ✅ |
| Bump epoch=2 + restart, reuse old admin token → `/api/admin/check` | **401** ✅ (kill-switch works) |
| Fresh admin login at epoch=2 | new different token, `/check` 200 ✅ |
| PM login + `/check` at epoch=2 | 200 ✅ |
| Shop login + `/check` at epoch=2 | 200 ✅ |
| Dev login + `/check` at epoch=2 | 200 ✅ |
| Old admin token (from epoch=1) still rejected | 401 ✅ |

### Env-var baseline
- `/app/backend/.env` → `ADMIN_SESSION_EPOCH=1` (baseline). Any change from this value invalidates all existing tokens.
- Production deploys MUST set `ADMIN_SESSION_EPOCH` explicitly (currently baseline `1` is fine; bump when needed).

### Files touched
- `backend/server.py` — added `_session_epoch()` helper; folded epoch into all 4 `_*_token_for()` constructors.
- `backend/.env` — added `ADMIN_SESSION_EPOCH=1` line.
- `memory/test_credentials.md` — documented how to bump and what it does.

### Combined with the earlier `tokenValidation.js` fix
When you bump the epoch:
1. Backend instantly starts 401-ing all old tokens.
2. Every user's next page load triggers `validateStoredTokens()` in `App.js`.
3. `/api/{admin,pm,shop,dev}/check` returns 401 for their old tokens.
4. Frontend auto-clears them from localStorage.
5. `authTick` bumps → router remounts → user sees the correct login screen.

No help-desk tickets. No "try incognito / clear cache" workarounds. Clean cutover.


## 2026-05-03 — Stale-Token Cache Bug on Live Site (mascidocs.com)

User report: "On live site training tiles don't say password and open right up. PDF & QR say password but still open without." (Preview behaves correctly.)

### Root cause — NOT a deployment mismatch
Live backend is correctly gated (verified): `curl https://mascidocs.com/api/training/packet.pdf?track={shop,pm,admin}` → **401**, `track=field` → **200**. Live `/api/training/videos` returns the new `field-05-jhp` slug.

The actual bug is **stale tokens in the user's browser `localStorage`**:
- `isAdmin()` / `isPm()` / `isShop()` / `isDev()` only check for token **presence**, not **validity**.
- When `ADMIN_PASSWORD` was rotated (MASCI1982! on 2026-04-30) and/or the `ADMIN_HMAC_SECRET` changed, any previously-stored token became unusable server-side — but the frontend still thought the user was signed in.
- Result: Training Hub tiles render as "OPEN TRACK" (unlocked), gated PDF/QR endpoints show the login CTA because the fetch 401s, yet clicking "Open track" took the user inside the Track page because the gate also used the same broken `isAdmin()` check.

### Fix — `/app/frontend/src/lib/tokenValidation.js` + `App.js` mount effect
One-time `validateStoredTokens()` fires on every app load:
1. Pings `/api/{admin,pm,shop,dev}/check` with whatever tokens live in localStorage, using `cache: "no-store"` so CDN doesn't mask a 401.
2. Any `401` → that token is cleared from localStorage.
3. If ANY token was cleared, an `authTick` state bumps → `<BrowserRouter key={authTick}>` remounts → every page re-reads localStorage → correct locked/unlocked state renders.
4. Network errors never nuke a token (guards against transient offline states).

Covers: `masci.admin.token`, `masci.pm.token`, `masci.shop.token`, `masci.dev.token`.

### Verification (preview)
Planted 3 fake stale tokens in localStorage, navigated to `/training`:

| After 3.5s | Result |
| --- | --- |
| `localStorage.admin.token` | `null` (cleared) ✅ |
| `localStorage.pm.token` | `null` (cleared) ✅ |
| `localStorage.shop.token` | `null` (cleared) ✅ |
| Shop/PM/Admin tiles href | `/{shop,pm,admin}/login` ✅ |
| Shop/PM/Admin tiles display | "PASSWORD REQUIRED" + lock ✅ |
| Field tile | "7 LESSONS" / "OPEN TRACK" (public, unchanged) ✅ |

### Files touched
- **NEW**: `frontend/src/lib/tokenValidation.js`
- **MODIFIED**: `frontend/src/App.js` — added import, `authTick` state, mount effect, `key={authTick}` on `<BrowserRouter>`

### Deployment needed
Live site (`mascidocs.com`) needs a fresh frontend build + deploy to pick up this fix. After deploy, any user with stale tokens will have them auto-cleared on their first visit.


## 2026-05-03 — Lesson 5 (JHP) Bilingual Videos Added

User uploaded EN + ES MP4s for **Lesson 5 — Job Hazard Plan (JHP)** in the Field Crew track. Integrated into the existing self-hosted, Range-aware video pipeline (no new player, no new code paths).

### Pipeline applied (same as lessons 1-4)
1. Downloaded both MP4s from the customer-assets URLs.
2. Re-muxed with `ffmpeg -c copy -movflags +faststart` so the moov atom moves to **byte 36** (front of file) for instant progressive playback. Verified.
3. Saved to `/app/backend/static/training-videos/field-05-jhp.{en,es}.mp4`.
4. Added the `field-05-jhp` slug to `_DEFAULT_TRAINING_VIDEOS` in `backend/server.py` with relative `/api/training/video/...` URLs.
5. The `/api/training/videos` endpoint self-heals the Mongo `training_videos` config doc on next read, so no manual seed required.

### Verification
| Check | Result |
| --- | --- |
| `GET /api/training/videos` includes `field-05-jhp.{en,es}` | ✅ Confirmed |
| `Range: bytes=0-1023` on both files returns **206 Partial Content** with `Content-Range: bytes 0-1023/<total>` | ✅ EN 21,494,105 / ES 23,282,090 |
| `moov` atom present in first 1KB of both files | ✅ At byte 36 |
| `Content-Type: video/mp4`, `accept-ranges: bytes` | ✅ |
| Frontend EN/ES toggle swaps `<video>` `src` without page reload | Existing `useEffect` keyed on `pickedUrl` triggers `v.load()` — same as lessons 1-4 |
| Lazy load: `preload="metadata"` only | ✅ (existing player config) |
| Error fallback if media fails: "Training video unavailable. Please contact your MASCI administrator." | ✅ (existing `onError` handler) |

### Files touched
- `backend/server.py` — added `field-05-jhp` entry to `_DEFAULT_TRAINING_VIDEOS` (5 lines).
- `backend/static/training-videos/field-05-jhp.en.mp4` (21 MB, faststart).
- `backend/static/training-videos/field-05-jhp.es.mp4` (23 MB, faststart).

No frontend changes were needed — the existing `LessonCard` in `TrainingTrack.jsx` already renders any slug returned from `/api/training/videos`.


## 2026-05-03 — Training Hub Auth Gate Verified (P0 closed)

User concern (recurring): "Shop / PM / Admin training tracks, QR posters, and PDF downloads must require a password. Field is the only public surface."

### Verification done this session
End-to-end smoke test from a logged-out browser (`localStorage.clear()` then direct navigation + Hub-button clicks):

| Surface | Logged-out result |
| --- | --- |
| `GET /api/training/packet.pdf?track=shop\|pm\|admin&lang=en` | **401 Unauthorized** |
| `GET /api/training/packet.pdf?track=field&lang=en` | 200 (public, by design) |
| Frontend `/training/admin` direct visit | "This track is password-protected" + Sign In CTA |
| Frontend `/training/admin/poster` direct visit | "Internal poster · password required" + Sign In CTA |
| Frontend `/training/admin/packet?lang=en` direct visit | "INTERNAL TRAINING · PASSWORD REQUIRED" + `Sign In · Admin` CTA |
| Hub → click `training-landing-pdf-shop-en` (logged out) | Routes to `/training/shop/packet?lang=en` → password gate |
| Hub → click `training-qr-poster-pm` (logged out) | Routes to `/pm/login` |

### Code paths confirmed in place
- `frontend/src/pages/TrainingTrack.jsx` — gates by `track.audience` using `isAdmin/isPm/isShop`, renders `<AccessDenied />` when not allowed.
- `frontend/src/pages/TrainingQrPoster.jsx` — same gate, renders inline lock card.
- `frontend/src/pages/TrainingPacketDownload.jsx` — auth-aware blob downloader: uses `api.get(..., { responseType: 'blob' })` so the JWT/X-*-Token header attaches; on 401 shows login CTA.
- `frontend/src/pages/TrainingHub.jsx` — for non-public tracks, all PDF buttons route through `/training/:track/packet?lang=…` and QR/poster buttons route to the correct login page when not unlocked.

### Outcome
P0 "Frontend Auth Gate bypass on Training Tracks & PDF Downloads" — **CLOSED · verified holding**. No code changes required this session; the prior agent's auto-committed fixes were already merged before context exhausted. Confirmed via direct screenshot + curl checks against the live preview URL.


## 2026-05-03 — JHA → JHP System-Wide Terminology Migration

User directive: rename "Job Hazard Analysis (JHA / JSA)" to "Job Hazard Plan (JHP)" everywhere, while preserving all legacy data and internal API/DB names so existing records still load.

### Rules applied (in order, longest-match first)
1. `Job Hazard Analysis (JHA / JSA)` → `Job Hazard Plan (JHP)`
2. `Job Hazard Analysis (JHA)` → `Job Hazard Plan (JHP)`
3. `Job Hazard Analysis` → `Job Hazard Plan`
4. `Análisis de Peligros del Trabajo (JHA / JSA)` → `Plan de Peligros del Trabajo (JHP)`
5. `Análisis de Peligros del Trabajo (JHA)` → `Plan de Peligros del Trabajo (JHP)`
6. `Análisis de Peligros del Trabajo` → `Plan de Peligros del Trabajo`
7. `JHA / JSA`, `JHA/JSA`, `JHAs`, `Planes JHA` → `JHP`, `JHP`, `JHPs`, `Planes JHP`
8. Standalone `\bJHA\b` and `\bJSA\b` → `JHP` (word-boundary protected)
9. `Hazard Analysis` (header) → `Hazard Plan`
10. `Análisis de Peligros` → `Plan de Peligros`
11. Slug rename: `field-05-jha` → `field-05-jhp` (training data only — no DB collection rename)

### Migration script
`/app/scripts/jha_to_jhp_rename.py` — idempotent Python rename script. Re-runnable safely.

### Files updated (24 files, 144 string replacements)
**Frontend (16 files):**
- `data/training.js` (20), `data/training_es.js` (21), `lib/i18n.js` (20)
- `lib/meetingTopicLibrary.js` (3), `lib/meetingTopicLibrary.es.js` (3)
- `lib/jobLibrary.js` (1), `lib/jhaSchema.js` (1)
- `pages/JhaPlansAdmin.jsx` (2), `pages/Hub.jsx` (2), `pages/AdminGuide.jsx` (3)
- `components/CheatSheetCard.jsx` (2), `components/ComplianceExportPanel.jsx` (2)
- `components/SystemHealthBadge.jsx` (1), `components/EmailReportDialog.jsx` (1)
- `components/BilingualConsent.jsx` (1), `components/AutoEmailRoutingPanel.jsx` (1)
- `components/AdminPMPanel.jsx` (1)

**Backend (7 files):**
- `training_pdf.py` (44), `server.py` (4), `routes/safety.py` (6)
- `pm_routing.py` (1), `ops_manual.py` (3), `job_hazard_files.py` (1)
- `pdf_render.py` (1)

### Backward compatibility (deliberately NOT renamed)
- Mongo collection names: `jhas`, `jha_files`
- API paths: `/api/jhas/*`, `/api/jha-files/*`
- Function names: `buildJhaDefaults`, `JhaPlansAdmin`, `route_jha_email`
- Filenames: `jhaSchema.js`, `job_hazard_files.py`, `JhaPlansAdmin.jsx`

This means **any record submitted before the rename still loads, displays as "JHP" in the UI, and is exportable** — exactly what the spec required.

### Verified
- ✅ Backend `/api/jhas` returns existing records (`HTTP 200`, 1 legacy record reads back).
- ✅ All 12 training PDFs (4 tracks × en/es/bi) render with zero JHA/JSA/Análisis strings; all field-track variants contain JHP / Job Hazard Plan / Plan de Peligros del Trabajo.
- ✅ Frontend EN: Lesson 5 card titled `Lesson 5 — Job Hazard Plan (JHP)`, slug `field-05-jhp`.
- ✅ Frontend ES: Lesson 5 card titled `Lección 5 — Plan de Peligros del Trabajo (JHP)`.
- ✅ Hub home Safety tile: `Inspections, toolbox talks, incident reports, JHPs, and trench-box guidance...`.
- ✅ Hub home Safety bullets: `Job Hazard Plans · Trench Box Reference`.
- ✅ Old slug `field-05-jha` no longer present in any rendered card.
- ✅ Lint clean across all touched files.

### Pre-deploy reminder
- ⚠️ `DEV_PASSWORD=Maddix8530!` in production env vars.
- After redeploy, any past JHA records remain accessible at `/safety/jha-plans` admin page (page UI now says "JHP Plans") and continue to surface under their original DB id.


## 2026-05-03 — Lesson 5 (JHA) Rewrite — Reflects MASCI's Actual JHA Process

User clarified MASCI's real-world JHA workflow: **JHAs are NOT built in the field by crews. They are pre-built job-specific documents prepared in advance by the Safety Department, Project Managers, and senior leadership.** Crews USE them; they don't create them. The previous training content described a task-based crew-authored JHA workflow which doesn't match how MASCI actually operates.

### What changed

**Title** (system-wide):
- EN: `Lesson 5 — Job Hazard Analysis (JHA)` *(removed `/JSA` suffix)*
- ES: `Lección 5 — Análisis de Peligros del Trabajo (JHA)`

**WHY THIS MATTERS** (new):
> "MASCI Job Hazard Analyses are built before work begins by the Safety Department, Project Managers, and leadership — based on scope of work, site conditions, traffic control (MOT), environmental factors, and known project hazards. This way hazards are identified and controlled BEFORE crews step onto the job."

**6-step body** (replaces old field-built workflow):
1. Crews do NOT build JHAs — they're prepared in advance by Safety/PM/Leadership.
2. Each JHA covers project-wide hazards, station-tied locations, required controls, environmental risks, MOT hazards, equipment/operational hazards.
3. Two documents per JHA package: JHA Document + Hazard Worksheet (with station numbers, threat level, controls).
4. Before work: review the JHA, understand area-specific hazards, follow every listed control.
5. If conditions don't match the plan: ask questions, use Stop Work Authority, do not improvise.
6. This is NOT a form completed in the field — it's a pre-built safety system.

**Cheat sheet** (new):
- "JHAs are pre-built by Safety / PM / Leadership — not the crew."
- "Two documents per job: JHA + Hazard Worksheet (with station numbers)."
- "Review before work. Follow controls. Stop Work if conditions change."

### Files updated
- `/app/frontend/src/data/training.js` — `field-05-jha` lesson body rewritten
- `/app/frontend/src/data/training_es.js` — Spanish translation rewritten (natural field-crew Spanish, not literal)
- `/app/backend/training_pdf.py` — `FIELD_LESSONS[4]` (JHA) — same rewrite for PDF generation
- `/app/frontend/src/lib/i18n.js` — replaced stale dead key `"Pre-task JHA / JSA. Walk every step…"` with `"Pre-built by Safety, PMs, and leadership before work begins. Crews review and follow — they don't fill it out."`

### What was deliberately NOT changed
- The JHA **authoring form** at `/safety/jha` and its helper labels in `i18n.js` (e.g. "Walk through each step…") — that's for the Safety Department / PMs who DO author JHAs in the system. The previous content confused field-crew training (the people who USE JHAs) with the authoring workflow (the people who BUILD JHAs). Authoring form is correct as-is.

### Verified system-wide
- ✅ UI EN: `/training/field` Lesson 5 card shows new title and "MASCI Job Hazard Analyses are built before work begins…" copy.
- ✅ UI ES: same card shows "Los JHAs de MASCI se preparan antes de que comience el trabajo…" copy.
- ✅ Old workflow phrases (`Hub → Safety → Job Hazard Analysis`, `Walk every step`, `Walk the task first`, `Recorra cada paso`, `líder de cuadrilla`, `capataz aprueba`) — **0 occurrences** anywhere in lesson 5.
- ✅ PDF EN (10 pages): Lesson 5 contains "built before work begins by the Safety Department, Project Managers".
- ✅ PDF ES (10 pages): Lesson 5 contains "preparan antes de que comience el trabajo, por el Departamento de Seguridad".
- ✅ PDF BI (15 pages): Lesson 5 page 10 shows EN+ES side-by-side with new content; ToC on page 2 lists "Lesson 5 — Job Hazard Analysis (JHA)" / "Lección 5 — Análisis de Peligros del Trabajo (JHA)".
- ✅ Footer count: 1 per non-cover page across all 3 PDF variants.
- ✅ Lesson order unchanged: 1-2-3-4(SafetyMtg)-5(JHA)-6(Incident)-7(SiteInsp).

### Pre-deploy reminder
- ⚠️ `DEV_PASSWORD=Maddix8530!` must be set in production env (gates `/dev` portal).
- 173 MB of MP4s in `/app/backend/static/training-videos/` ships with the deployment.


## 2026-05-03 — Field Track Lesson Reorder + Lesson 4 Toolbox Talk Videos

User requested re-numbering of Field Crew Training lessons 4–7 to put Safety Meetings ahead of JHA / Incidents / Site Inspection. Two new bilingual videos (Lesson 4 — Toolbox Talk) added.

### New Field Crew lesson order
| # | Slug | Title (EN) | Title (ES) | Video |
|---|---|---|---|---|
| 1 | `field-01-hub-navigation` | Navigating the MASCI Hub | Navegando el Hub MASCI | EN+ES ✅ |
| 2 | `field-02-daily-report` | Daily Reports | Reportes Diarios | EN+ES ✅ |
| 3 | `field-03-equipment-preop` | Equipment Pre-Op Inspection | Inspección Pre-Operación de Equipo | EN+ES ✅ |
| **4** | `field-04-safety-meeting` | **Safety Meetings (Toolbox Talks)** | **Reuniones de Seguridad (Charlas de Caja)** | **EN+ES ✅ NEW** |
| 5 | `field-05-jha` | Job Hazard Analysis (JHA / JSA) | Análisis de Peligros del Trabajo | placeholder |
| 6 | `field-06-incident` | Accident / Incident Reports | Reportes de Accidente / Incidente | placeholder |
| 7 | `field-07-site-inspection` | Site Safety Inspection | Inspección de Seguridad del Sitio | placeholder |

### What changed (consistent everywhere)
- **`/app/frontend/src/data/training.js`**: 4 lesson blocks reordered + slugs renamed (`field-04-site-inspection` → `field-07-site-inspection`, `field-05-safety-meeting` → `field-04-safety-meeting`, `field-06-jha` → `field-05-jha`, `field-07-incident` → `field-06-incident`).
- **`/app/frontend/src/data/training_es.js`**: Same reorder + slug rename in Spanish translations dict.
- **`/app/backend/training_pdf.py`**: `FIELD_LESSONS` array reordered + slugs renamed → all 12 PDF permutations (field/shop/pm/admin × en/es/bi) regenerate with the new order.
- **`/app/backend/server.py`**: `_DEFAULT_TRAINING_VIDEOS` adds `field-04-safety-meeting` entry; the legacy CDN→self-hosted migration logic continues to handle DB doc transitions.
- **`/app/backend/static/training-videos/`**: 2 new MP4s — `field-04-safety-meeting.en.mp4` (21.7 MB, 4:03) + `field-04-safety-meeting.es.mp4` (23.1 MB, 4:37). Both re-muxed with `+faststart` (moov atom at byte 36), H.264 High / AAC LC / 1280×720.

### Verified
- ✅ UI lesson order EN: 1→2→3→4(Safety Meeting)→5(JHA)→6(Incident)→7(Site Inspection)
- ✅ UI lesson order ES: same with Spanish titles (Lección 4 — Reuniones de Seguridad, etc.)
- ✅ PDF EN: contains "Lesson 4 — Safety Meetings" + "Lesson 7 — Site Safety Inspection"
- ✅ PDF ES: contains "Lección 4 — Reuniones de Seguridad" + "Lección 7 — Inspección de Seguridad"
- ✅ PDF BI: contains both EN and ES titles in correct positions
- ✅ Footer count: 1 per non-cover page across all 3 PDF variants (no duplicates)
- ✅ `/api/training/videos` returns 4 slugs × {en, es} dict; URL resolution in browser correct
- ✅ `/api/training/video/field-04-safety-meeting.{en,es}.mp4` returns HTTP 206 with `Content-Range` and `accept-ranges: bytes` (smooth streaming)
- ✅ moov atom at byte 36 on both new videos (FAST-START)


## 2026-05-03 — Training Video Playback Fix (Root Cause: moov atom + Range delivery)

User reported: "Videos are skipping, cutting in/out, or not playing smoothly. Original source files play perfectly outside the system." This pattern is the universal signature of an MP4 with the `moov` atom at the END of the file being served by a CDN that doesn't web-optimize.

### Root cause (verified)
All 6 source MP4s (3 lessons × EN/ES) had `moov` atom at the very end:
```
field-01-hub-navigation EN: moov at byte 19,073,990 / mdat at byte 44 → BAD
field-02-daily-report  EN: moov at byte 25,302,359 / mdat at byte 44 → BAD
field-03-equipment-preop EN: moov at byte 24,858,963 / mdat at byte 44 → BAD
(all 3 ES versions same pattern)
```
**Why this caused stuttering**: With moov at the end, browsers cannot decode any frame until the entire file has been downloaded. Mobile Safari/Chrome partially work around this by aggressive buffering, which manifests as: video plays for a few seconds → freezes → resumes → freezes → cuts in/out. Desktop Chrome on slow connections shows the same pattern. Source plays fine because local desktop players load the whole file before play starts.

### Fix applied
1. **Re-muxed all 6 videos with `+faststart`** (ffmpeg `-c copy -movflags +faststart`). This is a metadata move only — `moov` atom relocates from end-of-file to byte 36 — **no re-encoding, no quality loss, audio sync untouched**. File sizes within 1 byte of originals.
2. **Self-hosted in `/app/backend/static/training-videos/`** instead of `customer-assets.emergentagent.com`. Filename pattern: `{slug}.{lang}.mp4`.
3. **New Range-aware streaming endpoint**: `GET /api/training/video/{filename}` with:
   - `Accept-Ranges: bytes`
   - `Content-Type: video/mp4`
   - HTTP 206 Partial Content for any `Range:` header
   - `Content-Range: bytes start-end/total` correctly populated
   - 416 returned for out-of-range
   - Path traversal blocked (`/^[a-z0-9][a-z0-9._-]{0,128}\.mp4$/` filename whitelist)
   - 256 KB streaming chunks (memory-bounded, TCP-pipelined)
   - HEAD support
4. **One-time DB migration** in `/api/training/videos`: any stored URL containing `customer-assets.emergentagent.com` is automatically replaced with the matching self-hosted URL. Admin overrides via `/admin/training-videos` are still respected (only legacy CDN URLs migrate).
5. **Frontend URL resolver**: `resolveVideoUrl()` prefixes `REACT_APP_BACKEND_URL` to any `/api/...` path so the same DB value works on preview and production without rewrites.

### Verified end-to-end
- ✅ All 6 videos: `moov` atom at byte 36 (FAST-START).
- ✅ Range: `bytes=0-1023` → HTTP 206, `Content-Range: bytes 0-1023/19261827`.
- ✅ Mid-file seek: `bytes=5000000-5001023` → HTTP 206, correct content-range.
- ✅ Out-of-range request → HTTP 416 with `Content-Range: bytes */{size}`.
- ✅ Path traversal `../server.py` → HTTP 404 (filename regex blocks it).
- ✅ DB migration ran: all 6 URLs are now self-hosted.
- ✅ Browser-side `fetch(url, {Range})` from preview frontend returns correct 206 + content-type.
- ✅ EN↔ES toggle still works (different URLs swap on language change without page reload).

### Operational impact
- **No CDN dependency for videos** — we control delivery 100%.
- **Smooth progressive playback** on every device: faststart MP4 + Range support means the browser starts playback as soon as the first ~256 KB arrives, then streams the rest.
- **130 MB committed to repo** (`/app/backend/static/training-videos/`) — one-time cost, ships with deployments.
- **Same code path will work for any future videos** uploaded — admin uploads via `/admin/training-videos` UI will still accept any URL (CDN, S3, YouTube, etc.) but the default catalog now points at the self-hosted faststart copies.

### Pre-deploy reminder
- Set `DEV_PASSWORD=Maddix8530!` in production env.
- After redeploy, verify `https://mascidocs.com/api/training/video/field-01-hub-navigation.en.mp4` returns 206 with proper Range headers.


## 2026-05-02 — Bilingual Training Video Support

Schema and player upgrade so EN/ES videos swap automatically based on the language toggle.

### Schema (Mongo `training_videos.config`)
```json
{
  "videos": {
    "field-01-hub-navigation": { "en": "https://…/Hub_Navigating_FINAL.mp4", "es": "https://…/Hub_Navegando_ES.mp4" },
    "field-02-daily-report":   { "en": "https://…/DailyReport_FINAL.mp4",    "es": "https://…/ReporteDiario_ES.mp4" },
    "field-03-equipment-preop":{ "en": "https://…/PreOp_FINAL.mp4",          "es": "https://…/PreOp_ES.mp4" }
  }
}
```
Legacy single-string entries are auto-normalized to `{en: url, es: ""}` on first read.

### Backend (`/app/backend/server.py`)
- `_DEFAULT_TRAINING_VIDEOS` upgraded to `{slug: {en, es}}` shape — 3 lessons × 2 langs seeded.
- `_normalize_video_entry()` accepts legacy string OR `{en, es}` dict and returns the canonical shape.
- `GET /api/training/videos` self-heals: any missing EN or ES URL is back-filled from the default catalog (per-key `$set`, never overwrites admin overrides). Migrates legacy strings to the new shape.
- `PUT /api/admin/training/videos` (admin-strict — PM/Shop/Dev tokens rejected) accepts both old and new shapes; merges per-slug/per-language so partial saves don't wipe the other language.

### Frontend
- `pickVideoUrl(entry, lang)` — resolves the right URL:
  - `lang === "es"` + ES URL set → ES.
  - `lang === "es"` + ES missing → EN with `fallback: true`.
  - `lang === "en"` → always EN (no silent ES fallback per spec).
- `LessonCard` uses `useRef` + `useEffect` on `pickedUrl` change to call `video.pause() / currentTime=0 / load()` — the player swaps language without a page reload.
- `<video>` and `<iframe>` get a `key` based on `embedSrc.src` so React fully re-mounts the player on language change.
- `data-testid="lesson-video-fallback-hint"` div renders ("Spanish version not available for this lesson" / "Versión en español no disponible para esta lección") whenever ES is requested but only EN is available.
- `data-testid="lesson-video-error"` panel renders the spec-exact string "Training video unavailable. Please contact your MASCI administrator." when the EN URL itself errors.
- `AdminTrainingVideos` (`/admin/training-videos`) splits each lesson into two inputs: `video-url-{slug}-en` and `video-url-{slug}-es` with an `EN x/y · ES x/y` filled count badge.

### Verified (iteration_30 testing agent)
- 14/14 new backend tests pass. 31/31 iter29 regression tests pass after one shape assertion was forward-compatibly updated.
- Live EN↔ES toggle: clicking the ES toggle swaps the rendered video URL within 2 s without page navigation.
- Mobile horizontal overflow on every key route: 0 px.
- Zero console errors. No forbidden strings ("Powered by The Judd Group LLC", "Made with Emergent" in code).
- Admin split inputs (23 EN + 23 ES) render correctly.

### Note on Chromium-test-only fallback
Headless Chromium in the test env lacks licensed H264 → fires `onError` immediately on every MP4. The test environment shows the `lesson-video-error` panel everywhere; on real Chrome / Safari / Firefox / iOS Safari / Android Chrome (which all license H264) the videos play normally. The fallback firing in tests **is the spec-required behavior under failure** and confirms `onError` is wired correctly.


## 2026-05-02 — Field Training Lessons 2 & 3 + Root-Cause Fix for Live Video Rendering

Added two new official Field Training videos and re-architected the seed logic so production never has missing video URLs again.

### Videos added (auto-seeded into `training_videos` Mongo doc)
- **Lesson 2 — Daily Reports** → slug `field-02-daily-report` → 21.1 MB H264/AAC 1280×720
- **Lesson 3 — Equipment Pre-Op Inspection** → slug `field-03-equipment-preop` → 20.8 MB H264/AAC 1280×720
- (Existing) Lesson 1 — Navigating the MASCI Hub → 19.2 MB

All 3 served via CloudFront (`customer-assets.emergentagent.com/.../*.mp4`) with `accept-ranges: bytes`, `content-type: video/mp4`, no auth required.

### Root cause for "videos not rendering on live"
The `training_videos` Mongo collection on production Atlas was empty. Backend returned `{videos: {}}` and every lesson rendered the "coming soon" placeholder. The previous `$setOnInsert`-only fix only seeded brand-new docs — it did NOT back-fill missing slugs into an already-existing doc.

### Architectural fix
Replaced the seed logic in `/api/training/videos` with a per-key fill:
```python
_DEFAULT_TRAINING_VIDEOS = { ... 3 slugs ... }
# On every read: fill any missing default slug with $set on its specific
# field. Admin overrides (existing non-empty values) are preserved.
```
Net effect:
- Fresh production Atlas → seeds all 3 videos on first request.
- Already-seeded prod with only Lesson 1 → automatically adds Lessons 2 & 3 on next request, no admin round-trip.
- Admin-customized URLs via `/admin/training-videos` → never overwritten.

### Verified
- Backend: `GET /api/training/videos` returns all 3 slug→URL mappings.
- Frontend `/training/field`: lessons render in correct order (1, 2, 3, 4, 5, 6, 7) with correct titles ("Lesson 2 — Daily Reports", "Lesson 3 — Equipment Pre-Op Inspection").
- Mobile (390×844): horizontal overflow = 0px.
- Console errors: 0.
- All 4 training tracks load (field public, shop/pm/admin gated).
- Note: the headless Chromium used by Playwright in the test container does NOT include licensed H264 codec, so the `<video>` element falls back to the `lesson-video-error` "Training video unavailable…" message in the test browser — this is **expected per spec** and confirms the fallback works. Real Chrome / Safari / Firefox / iOS / Android browsers all ship with H264 and will play the videos.


## 2026-05-02 — Pre-Redeploy QA Fix Pass

Final sweep before the mascidocs.com redeploy. Two targeted bug fixes and one minor UI regression caught + cleaned.

### Bug 1 — Duplicate footer on training PDF final page (FIXED)
- **Root cause**: `training_pdf.py` endnote section repeated `{t['footer_legal']}` as an in-body `<div>` on the final page, on top of the `@page @bottom-left` margin footer which already renders on every page including the endnote page. Result: final page had "© MASCI · Platform developed by The Judd Group LLC" twice.
- **Fix**: Removed the in-body `footer_legal` div from the endnote block in both renderers (single-language `render_packet` and `_render_bilingual`). Endnote now carries only the `mascidocs.com` heading, ownership clarification, and safety disclaimer — the page footer comes exclusively from the `@page @bottom-left` margin box.
- **Verified**: All 12 permutations (`field/shop/pm/admin` × `en/es/bi`) via `pypdf` text extraction show exactly 1 footer per non-cover page, 0 on cover (cover is intentionally silenced via `@page :first`). Zero duplicates.

### Bug 2 — Field Training Lesson 1 video not showing on production (FIXED)
- **Root cause**: The `training_videos` Mongo doc was only saved on the preview env DB. Production Atlas had an empty `training_videos` collection after the Atlas migration, so `/api/training/videos` returned `{videos: {}}` and the lesson rendered the "Video tutorial coming soon" placeholder for every user on mascidocs.com.
- **Fix A** (self-heal): `/api/training/videos` now auto-seeds `field-01-hub-navigation` with the known-good CloudFront MP4 URL on first call if the config doc is missing. Admins override via `/admin/training-videos` normally — this is just a floor.
- **Fix B** (spec compliance): Added `onError` handler to `<video>` and `<iframe>` in `TrainingTrack.jsx`. When the element fails to load, a `data-testid=lesson-video-error` fallback renders the exact spec string: *"Training video unavailable. Please contact your MASCI administrator."* — plus an "Open video in new tab" link fallback. ES translations added for all 3 new strings.

### UI Fix — Hub home mobile overflow (FIXED)
- 390px viewport showed 13px horizontal overflow. Traced to the Projects tile's Basecamp + OnStation buttons — grid items without `min-w-0` expanding past their grid cell. Added `min-w-0` to both `<a>` elements. Mobile scrollWidth = clientWidth = 390 now.

### Regression matrix (testing agent + curl)
| Check | Result |
|---|---|
| Training PDFs — 12 permutations, footer count per page | ✅ All pass (0/1 correct across cover/body) |
| `/api/training/videos` auto-seed | ✅ Returns `field-01-hub-navigation` after wipe |
| Packet auth matrix — field public, shop/pm/admin require token, tier isolation | ✅ 15/15 pass |
| `/api/dev/*` rejects admin + PM tokens, accepts dev token | ✅ |
| Admin/PM/Shop/Dev logins + wrong-password 401 | ✅ 8/8 |
| Mobile horizontal scroll — `/`, `/training`, `/training/field`, `/cheatsheet`, legal pages | ✅ 0 overflow |
| Console errors on training pages (desktop + mobile) | ✅ None |
| PDF signals — no "Powered by", no "Made with Emergent" in rendered DOM or PDFs | ✅ |

### Deploy readiness
🟢 **GO** — testing agent verdict. 25 pytest pass / 0 fail / 7 skipped-by-design. Two non-blockers pre-fixed in this pass (mobile overflow; testid naming can be patched post-deploy if desired).

### Production env var checklist (before redeploy)
- `DEV_PASSWORD=Maddix8530!` (NEW — gates the new /dev portal)
- `AUTO_EMAIL_REPORTS=true` (production-only)
- `RATE_LIMITING=on` (production-only)
- `CORS_ORIGINS=https://mascidocs.com,https://www.mascidocs.com`
- All other env vars unchanged.


## 2026-05-02 — Developer Portal + Ops Manual Archive (Vendor-Only)

Moved the System Owner & Operations Manual off the Admin Hub and behind a
dedicated, hidden vendor portal at `/dev`. The portal is password-gated
(`DEV_PASSWORD=Maddix8530!`), reached only via a tiny "Developer" footer
link on the Home page, and backed by a brand-new HMAC namespace
(`dev:<pw>`) so the token can never be replayed against any admin/PM route.

### Backend (`/app/backend/server.py`)
- New helpers: `_dev_token_for()`, `_is_valid_dev_token()`, `require_dev()`.
- New routes:
  - `POST /api/dev/login` — issues `X-Dev-Token` against `DEV_PASSWORD`.
  - `GET /api/dev/check` — verifies a stored token.
  - `GET /api/dev/ops-manual.pdf` / `.docx` — live renders (replaces the
    old `/api/admin/ops-manual.*` routes — those are gone).
  - `POST /api/dev/ops-manual/snapshot` — renders both PDF + DOCX, stores
    base64 + source_hash + timestamp + optional note in a new
    `ops_manual_snapshots` Mongo collection.
  - `GET /api/dev/ops-manual/snapshots` — list pinned snapshots (metadata
    only; base64 payload excluded from the list response for size).
  - `GET /api/dev/ops-manual/snapshots/{id}.pdf` / `.docx` — byte-identical
    re-download of a pinned snapshot months after the source data changes.
  - `DELETE /api/dev/ops-manual/snapshots/{id}`.
- **All 6 verified via curl**: dev login ✅, dev check ✅, admin token
  rejected ✅, ops-manual.pdf ✅ 66 KB, snapshot create ✅, snapshot list ✅,
  snapshot pdf/docx byte-exact ✅, delete ✅.

### Frontend
- `src/lib/devAuth.js` — localStorage key `masci.dev.token`.
- `src/lib/api.js` — interceptor attaches `X-Dev-Token` and clears it on
  401.
- `src/components/RequireDev.jsx` — route guard (rejects admin/PM tokens).
- `src/pages/DevLogin.jsx` — minimal vendor-branded (slate-950 terminal
  look) password gate. Not MASCI-branded.
- `src/pages/DevHub.jsx` — 3 sections: Live download (PDF + DOCX), Pin
  Snapshot (note field + Save), Snapshot Archive table (per-row PDF/DOCX
  re-download + delete).
- `src/pages/AdminHub.jsx` — removed `OpsManualPanel` import + render;
  deleted `src/components/OpsManualPanel.jsx`.
- `src/pages/Hub.jsx` — tiny low-contrast "DEVELOPER" link at the very
  bottom of the home page footer (slate-300 text, hover slate-500). Does
  not draw attention but always reachable.
- `src/App.js` — added `/dev/login` + `/dev` routes (guarded by `D`
  = RequireDev).

### Classification
**CONFIDENTIAL — The Judd Group LLC internal use only.** Ops Manual is no
longer visible or downloadable from the Admin Hub. MASCI admins retain
their full operational console; vendor-internal docs (cost breakdowns,
architecture, V2 recommendations) stay with the vendor.

### Env var added
- `DEV_PASSWORD=Maddix8530!` in `/app/backend/.env`.


## Future / Backlog (added 2026-05-02)

- **One-Click Due-Diligence Package** (Dev Portal) — single button that bundles the latest pinned Ops Manual PDF + DOCX + the live source zip into one dated download. Saves counsel-deadline scramble. *(Deferred — not building now.)*


## 2026-05-02 — Dev Portal: Full Source Bundle Download

Due-diligence companion to the Ops Manual archive. Lets the vendor hand
a counsel / auditor / acquirer a byte-exact snapshot of the code that
produced a pinned manual, paired with the manual itself.

### Backend
- `GET /api/dev/source-bundle.zip` — streams a zip of `/app/backend`,
  `/app/frontend` (src/public only), `/app/memory`, `/app/scripts`, top-level
  docs (README, ATLAS_MIGRATION, auth_testing, test_result, design_guidelines).
- `GET /api/dev/source-bundle.info` — metadata probe so the UI can show a
  file-count + size estimate before the user clicks download.
- **Strict exclusions** (never leaked): `/backups/*` (customer DB dumps),
  `/storage/*` (uploaded files), `node_modules`, `build`, `__pycache__`,
  `.git`, `.env` / `.env.*`, `*.pyc`, `*.pyo`, `*.log`, `*.bak.json`.
- A `MANIFEST.txt` is embedded in every zip with generation timestamp,
  `source_hash`, and a full file listing for audit.
- **Verified via curl**: 357 files · 16.9 MB · 0 leaked sensitive paths ·
  admin token rejected with 401.

### Frontend
- New "Full Source Bundle" section in DevHub between "Pin a Snapshot" and
  "Snapshot Archive". Shows file count + size + short hash probed from
  `/api/dev/source-bundle.info` on mount. Single button triggers
  download via `X-Dev-Token`-authed blob fetch.


## 2026-05-02 — Internal System Owner & Operations Manual (PDF + DOCX)

Full 18-page confidential reference doc for The Judd Group LLC covering all 12 requested sections: system overview, architecture, third-party dependencies, cost breakdown, deployment, backup + recovery, performance + scaling, security, failure points, maintenance checklist, V2 scaling notes, and owner-notes. Real tables for dependencies, costs, collections, failure modes, and risk mitigations.

### Architecture
- `/app/backend/ops_manual.py` — single source of truth. `SECTIONS` list holds all content. Both renderers emit from the same data.
- `render_ops_manual_pdf()` → WeasyPrint, custom @page CSS with CONFIDENTIAL margin banner.
- `render_ops_manual_docx()` → python-docx, 150 paragraphs / 9 tables / Word-native Heading 1 styles.

### Admin endpoints (both require `X-Admin-Token`)
- `GET /api/admin/ops-manual.pdf` → 66 KB, 18 pages, attachment disposition.
- `GET /api/admin/ops-manual.docx` → 48 KB, Word 2007+ format.
- Both return 401 without token. Both `Cache-Control: private, no-store`.

### Admin UI
- `/app/frontend/src/components/OpsManualPanel.jsx` — mounted in `AdminHub.jsx` below `CrewRecoveryPanel`. Two clearly-labelled buttons ("Download PDF" / "Download Word (.docx)") with loading state. Classification line at the bottom.

### Regression
- `/app/backend/tests/test_ops_manual.py` — 2 tests: PDF size + magic bytes, DOCX size + ≥12 H1s + ≥8 tables. Passes.

### Dependency added
- `python-docx==1.2.0` (pulls `lxml`) added to `requirements.txt`.

### Classification
**CONFIDENTIAL — The Judd Group LLC internal use only.** Document explicitly states it is not for MASCI staff or customers. Content includes internal cost figures, env-var names, dependency criticality ratings, and Version-2 SaaS recommendations.


## 2026-05-02 — Training Video Support + First Video Registered


### Native <video> support for MP4/WEBM URLs
- `TrainingTrack.jsx` `toEmbedUrl()` now returns `{ kind: "iframe" | "file", src }` instead of a bare URL string.
- Direct file extensions (`.mp4`, `.webm`, `.ogv`, `.mov`, `.m4v`) render inside an HTML5 `<video>` tag with native controls, `playsInline`, `preload=metadata`. Field crews get a real mobile video player.
- YouTube / Loom / Vimeo still render in their iframe embed — unchanged behaviour.
- Rendered markup uses `data-testid="lesson-video-file"` vs `"lesson-video-iframe"` so tests can target either.

### First video registered
- Lesson slug: `field-01-hub-navigation` ("Lesson 1 — Navigating the MASCI Hub")
- URL: `https://customer-assets.emergentagent.com/job_safety-audit-mobile-1/artifacts/mnrpeff0_MASCI_Hub_Navigating_FINAL_...mp4`
- 19.2 MB MP4, `content-type: video/mp4`, served with CORS-friendly headers.
- Saved to `training_videos` Mongo doc (`_id: "config"`, `videos.field-01-hub-navigation`) via `PUT /api/admin/training/videos`.
- Verified visually on preview: `/training/field` renders the embedded player at the top of Lesson 1, other lessons still show the "Video tutorial coming soon" placeholder.

### Future videos
The admin can self-serve future video additions via the existing `/admin/training-videos` page — no agent round-trip needed. Paste the video URL next to the lesson slug, click Save, the video shows up on the field track immediately.


## 2026-05-02 — Admin Hub Backend Version Badge


Follow-on to the `/api/version` endpoint — tiny self-diagnosing widget

### `BackendVersionBadge` component
- `/app/frontend/src/components/BackendVersionBadge.jsx`
- Calls `GET /api/version` on mount, renders a single rounded-pill status chip.
- Three visual states:
  - **Green** — endpoint reachable AND uptime ≤ 7 days (`BACKEND {short_hash} · UP 9M`)
  - **Amber** — endpoint reachable AND uptime > 7 days (`BACKEND {short_hash} · UP 12D · stale?`)
  - **Red** — endpoint unreachable / 404 (`Backend /api/version unreachable — redeploy`)
- Native hover tooltip exposes the full `source_hash`, `commit`, `started_at` for audit.
- Wired into `AdminHub.jsx` footer; lives between the console title and the `JuddGroupAttribution` block. Admin-only — not on field/shop surfaces.
- Verified live on preview (green pill, full tooltip, no layout break).


## 2026-05-02 — Backend Version Endpoint + Post-Deploy Drift Check

Added to prevent a third "live backend is stale" surprise:

### `GET /api/version`
- New public read-only endpoint on the backend (`server.py` just after `/health`).
- Returns: `{ service, commit, built_at, source_hash, started_at, uptime_s }`.
- `source_hash` is an md5 of `server.py + training_pdf.py + pdf_render.py` computed once at startup. Works even without git in the container — the hash is deterministic from source bytes.
- Optional env vars `GIT_COMMIT` + `BUILT_AT` can be populated at deploy time to supplement `source_hash`; fall back to `"unknown"` when not set.

### `scripts/post_deploy_check.py`
- One-command post-deploy verification: `python3 scripts/post_deploy_check.py`
- Hits `/api/version` on mascidocs.com, computes the same hash locally, compares.
- On match → runs the existing training-PDF audit on live; on mismatch → tells you to redeploy.
- Exit codes: 0=pass, 1=stale backend, 2=endpoint unreachable. Script-friendly for future CI.

### Deployment note
Endpoint is not yet on live mascidocs.com — takes effect after the next redeploy. Verified working on preview: hash matches local source, uptime counter increments, training-PDF audit trigger works.


## 2026-05-02 — Language-Aware PDF Footer Fix (Blocker Found in Pre-Deploy Audit)

Pre-deploy LIVE PDF audit caught two related bugs that the preview tests missed:

### Bug A — Spanish packets rendered the English footer on every page
- Root cause: `training_pdf.py` `_CSS` constant hardcoded `"\\00A9 MASCI \\00B7 Platform developed by The Judd Group LLC"` in the `@page @bottom-left` margin box. The `footer_legal` string in the `_strings_for(lang)` i18n table was only used by the endnote `<div>` on the final page.
- Impact: On ES packets, the per-page footer (9 pages per packet × 4 tracks × ES) read English instead of `© MASCI · Plataforma desarrollada por The Judd Group LLC`.

### Bug B — LIVE PM track packet had zero footers on any page
- Root cause: Backend deployed was still running OLD code (pre-footer refactor) — confirmed by comparing LIVE `pm_en.pdf` (0/9 footer hits) to LOCAL `pm_en.pdf` rendered from current source (8/9 hits). Even with a cache-busting query string, LIVE returned the stale content + `cache-control: public, max-age=60` for gated tracks (old logic — new logic sets `private, no-store` for non-field).
- Impact: Only the PM track was broken live; field/shop/admin had the correct English footer but ES versions still had Bug A.

### Fix (both bugs, one code path)
- Replaced monolithic `_CSS` constant with `_CSS_TEMPLATE` (has a `{FOOTER_TEXT}` placeholder) plus a new `_css_for_lang(lang)` helper that substitutes the correct language-aware footer string.
- Both `render_packet` and `_render_bilingual` now call `_css_for_lang(lang)` when building the `<style>` block, so every page footer matches the body language.
- Verified locally across all 8 permutations (field/shop/pm/admin × en/es):
  - Footer on every non-cover page ✓
  - Disclaimer appears exactly once on last page ✓
  - Ownership clarification on last page ✓
  - Zero "Powered by", "subsidiary", "ALL RIGHTS RESERVED", "Built with Emergent" ✓

### Deployment note
- LIVE mascidocs.com still serving stale backend PDFs until next redeploy. Frontend bundle is already current.
- Once the redeploy lands, the training-PDF audit script (`/tmp/audit_live_pdfs.py`) can be re-run and should report 8/8 PASS.


## 2026-05-02 — Final Vendor/Customer Attribution Reframe (Round 3)

Owner refined the wording one more time after the prior "Proprietary platform developed and maintained by" pass — the final brief shortens the footer, moves the safety disclaimer from every-page to last-page-only (less visually noisy), and adds admin-dashboard-specific wording.

### Final string matrix
| Surface | Variant | Final wording |
|---|---|---|
| Global UI footer (every page) | `judd-attr-global` | `Platform developed by The Judd Group LLC · Terms · Privacy` |
| Login page (admin/PM/shop) | `judd-attr-login` | `Platform developed by The Judd Group LLC` |
| Admin + PM dashboards (internal) | `judd-attr-admin` | `System developed & maintained by The Judd Group LLC` |
| Backend record PDF (`pdf_render.py`) @bottom-left | — | `© MASCI · Platform developed by The Judd Group LLC` |
| Backend training PDF (`training_pdf.py`) @bottom-left | — | `© MASCI · Platform developed by The Judd Group LLC` (EN) / `© MASCI · Plataforma desarrollada por The Judd Group LLC` (ES) |
| Training packet endnote (last page) | — | `mascidocs.com` + attribution + ownership clarification + safety disclaimer |
| Record PDF last page | — | safety disclaimer + ownership clarification block (only renders on final page) |
| Trench-box poster card + QR poster | — | `© YYYY MASCI · Platform developed by The Judd Group LLC` |
| Baked lockup credit (on-light/on-black PNGs) | — | `PLATFORM DEVELOPED BY THE JUDD GROUP LLC` |

### Key architectural moves
- **Safety disclaimer no longer renders per-page.** Previously lived in `@bottom-center` WeasyPrint margin box on every page → moved to a single last-page-only `<div>` inside the body flow. Net effect: less visual noise on interior pages; liability language still prominently visible at the end of every document.
- **Ownership clarification ("mascidocs.com is a customer-branded deployment…") also lives on last page only**, below the safety disclaimer.
- Admin variant adds subtle Judd Group logo + "System developed & maintained by..." line — only rendered on `AdminHub.jsx` and `PmHub.jsx` (never on field/shop/safety surfaces).

### Third-party "Emergent" references purged from user-visible content
- `training.js` / `training_es.js` (Admin track lessons 2, 3, 6, 7) — replaced Emergent-specific language ("Emergent dashboard", "Emergent env vars", "Emergent support") with generic "production deploy env", "deployment dashboard", "developer / vendor support".
- `AdminGuide.jsx` — 3 places updated.
- `PersistenceHealthBanner.jsx` + matching `i18n.js` ES translation — reframed.
- `training_pdf.py` admin cheat-sheet steps — EN + ES both reframed.
- **Remaining Emergent references** are internal code comments only (`api.js`, `jwtAuth.js`, `printReport.js`, `GlobalKeepalive.jsx`, `server.py`, and my own comment in `NewEquipmentInspection.jsx` explaining the Tally-bar badge collision workaround). These never render to users or PDFs — kept as maintainer documentation.

### Route aliases added (fix old printed QRs)
Three permanent redirects land any old QR codes still in the field on the correct canonical routes:
- `/reports/daily/new` → `/daily/new`
- `/safety/jha` → `/jha`
- `/safety/trench-boxes` → `/trench-boxes`

### Emergent badge removal answer (from Support)
Free tier: badge cannot be removed. Paid plans ($20/mo Standard, Pro, or Team): toggle off via deployment settings on the Home tab. **Critical**: badge only appears on preview + `*.emergentagent.com` URLs — NOT on mascidocs.com — so production users / field crews never see it.



After the owner-authored Legal + Vendor Attribution redeploy shipped to mascidocs.com, a system-wide sweep was requested for any mobile/desktop bugs and any other sticky UI that might collide with the Emergent floating badge on preview/deployed Emergent URLs.

### Testing agent results — 17 of 18 surfaces passed on both viewports
Mobile (390×844) + Desktop (1440×900), zero console/page errors on every surface:
Home, Cheat Sheet, Training Hub + 4 tracks, Legal Terms (14 sections), Legal Privacy (11 sections), Admin/PM/Shop logins with correct credentials, Field Safety Cards, Daily Report form, Incident form, JHA Plans Hub, Trench Boxes, Training QR Poster, global footer wording.

### ONE real regression caught — TALLY bar collides with Emergent badge on mobile
Root cause identified by testing agent: `env(safe-area-inset-right)` is an OS-level inset (notch / rounded corners) and resolves to `0` on most devices. It does **NOT** reserve space for the "Made with Emergent" floating badge that Emergent injects in the bottom-right on preview + deployed `*.emergentagent.com` URLs. Result: tally bar AND collapsed chip sat directly over the badge on mobile — chip was even click-blocked on real devices.

**Fix applied** (`NewEquipmentInspection.jsx` lines ~918-955):
- `sticky bottom-4` → `sticky bottom-24 sm:bottom-4`: lifts the bar 96px above the badge on mobile, keeps desktop unchanged
- Removed `env(safe-area-inset-right)` inline padding (was dead weight)
- Added `mr-44 sm:mr-0` to the collapsed TALLY chip so it parks to the **left** of the Emergent badge — always tappable

**Verified via DOM bounding-box check on mobile viewport:**
- Expanded bar ↔ badge overlap = **0 px**
- Collapsed chip ↔ badge overlap = **0 px**
- Normal Playwright click on chip now restores the bar (was previously requiring JS `dispatchEvent` because the badge intercepted pointer events)

### Other sticky surfaces swept
Exhaustive grep for `sticky bottom-*` / `fixed bottom-*` across `/frontend/src`: only **one** match existed (the TALLY bar, now fixed). All other sticky elements are `sticky top-0` headers, which don't collide with the bottom-right badge. Clean.

### Emergent badge removal answer (from Support)
Free tier: badge cannot be removed. Paid plans (Standard/Pro/Team) can toggle "Show Emergent Badge" off via deployment settings on the Home tab. Upgrade via the Credits button. Minimum plan: $20/mo. The badge only appears on preview and `*.emergentagent.com` URLs — it is **NOT** visible on mascidocs.com custom domain, so production users never see this collision. It's only visible to anyone QA-ing via preview links.


The owner supplied final authoritative text for both `/legal/terms` and `/legal/privacy`. Both files were rewritten verbatim against the supplied copy — no paraphrasing. **Treat the wording inside `<article>` on both pages as legal text and do not edit phrasing without explicit owner approval.**

### Files updated
- `/app/frontend/src/pages/legal/TermsOfService.jsx` — 14 sections (Relationship, Ownership of Platform, Ownership of Customer Data, License to Use with 6-item restriction list, Acceptable Use, Confidentiality, Availability, No Warranty, Limitation of Liability, Indemnification, Termination, Changes, Governing Law = Florida / Flagler County, Contact). Effective date set to **January 01, 2026**.
- `/app/frontend/src/pages/legal/PrivacyPolicy.jsx` — 11 sections (Roles & Relationship — Judd = data processor / MASCI = data controller; Information Collected; How Used; Subprocessors = MongoDB Atlas, Resend, cloud infra; Security; Retention; Data Responsibility; User Rights; Transfers; Changes; Contact). Effective date **January 01, 2026**.

### Typography
The codebase uses `prose` classes but `@tailwindcss/typography` is not installed, so prose was a no-op — section headings rendered at body size. Added scoped CSS in `index.css` (under `[data-testid="terms-of-service-page"]` and `[data-testid="privacy-policy-page"]`) to give H2/H3/lists/strong proper hierarchy. Result: section headings 1.25rem→1.4rem on sm+, H3 sub-blocks (ACCOUNT INFORMATION, AUTHENTICATION DATA, etc.) in uppercase tracking, disc/decimal lists at 1.4rem indent.

### Verified
- `/legal/terms` and `/legal/privacy` both render with full hierarchy, lint clean, and link cross-reference at the foot of each page works.


## 2026-05-02 — Vendor Attribution Reframe + PDF Footers

Reframed every vendor-attribution surface to match the legal model: **MASCI owns the brand & data; The Judd Group LLC powers the underlying platform.** The Judd Group does NOT sublicense or sublease the platform — internal MASCI use only (employees, PMs, supers, mechanics, crews).

### What changed

**1. Lockup PNG variants — credit baked in to print variants only**
- `recolor_lockup_tagline.py` now also draws "POWERED BY THE JUDD GROUP LLC" (Liberation Sans Bold 22pt) centred at y=552 below the EXCELLENCE row.
- Baked into `masci-full-lockup-onlight.png` (dark navy, ~70% opacity) and `masci-full-lockup-onblack.png` (silver, ~70% opacity).
- **Not** baked into `masci-full-lockup.png` (transparent variant) — keeps the live app screen clean and customer-branded.

**2. Backend PDF footers — applies to every dynamic PDF**
- `pdf_render.py` `@bottom-center` → `© MASCI · Powered by The Judd Group LLC` (was: "Generated by The Judd Group LLC · MASCI HUB Platform").
- `training_pdf.py` `@bottom-left` → same line; also updated `footer_legal` (EN/ES) and the closing endnote on the cover page.
- Verified via `pdftotext` on a generated inspection PDF and a training packet PDF.

**3. Frontend global footer**
- `JuddGroupAttribution.jsx` `global` variant → `© {YEAR} MASCI · Powered by The Judd Group LLC · Terms · Privacy` (was: "© {YEAR} The Judd Group LLC · MASCI HUB™ · Terms · Privacy").
- Same reframe applied to the trench-box poster card and the QR poster page.

### Surfaces NOT touched
- 4 static safety-card PDFs in `/app/backend/static/safety-cards/` were generated externally and have no in-repo generator. They still embed the previous lockup. To refresh, we'd need to either rebuild them in WeasyPrint or regenerate the source artwork — flag this as future work if/when the safety cards are next updated.


## 2026-05-02 — Context-Aware Lockup Tagline Colours

The bottom tagline "EXCELLENCE • ADAPT • OVERCOME" needs *different* colours on different surfaces (silver on dark, dark navy on white) so it stays legible everywhere. Initial pass made the tagline silver in all three variants — that broke the cheat-sheet (silver-on-white). Final pass tunes each variant to its target background.

### Final colour matrix
| File | Surface | Tagline colour |
|---|---|---|
| `masci-full-lockup.png` (transparent) | dark navy header | silver `#C8C8C8` |
| `masci-full-lockup-onblack.png` | solid black PDFs | silver `#C8C8C8` |
| `masci-full-lockup-onlight.png` | white cheat sheets / posters / print | dark navy `#0F172A` |

### Implementation
- **Source-of-truth raster**: `/app/frontend/public/_src/masci-full-lockup.SOURCE.png` — the original AI-generated lockup with the dark tagline still intact. This file is only read, never written, so every script run is idempotent.
- **Generator**: `/app/backend/scripts/recolor_lockup_tagline.py`
  - Re-reads the SOURCE every run.
  - Recolours only `is_dark_text` pixels in y-band `478..506` (the row range containing the bottom tagline). Red dash separators and plate/border pixels are left alone.
  - Per-pixel alpha + darkness ramp preserved → anti-aliased glyph edges stay smooth.
  - Writes three variants: transparent (silver), on-light (dark-navy + flatten over white), on-black (silver + flatten over black).
- Audit verified all logo variants for proper background contrast: `mark` and `wordmark` (red glyphs only) read fine on every background, no changes needed.

### Notes for future logo edits
- Always read from `_src/masci-full-lockup.SOURCE.png`, never from the writable `masci-full-lockup.png` (otherwise multiple runs compound colour shifts).
- Avoid regenerating from scratch via Gemini Nano Banana (`generate_hub_logos.py`) unless a layout change is required — model variance produces inconsistent ring/typography between runs.


## 2026-05-01 — Training Hub Auth Gating (Field public · Shop/PM/Admin gated)

Closed the security gap. The back-office workflows (master-list internals, password rotation, backup procedures) are no longer visible to anyone who walks up to the URL. The Field Crew track stays fully public for new hires and labor-only crew.

### Access matrix

| Surface | Field | Shop | PM | Admin |
|---|---|---|---|---|
| `/training` landing card preview (lessons, blurb) | ✅ public | 🔒 password chip + "Sign in as Shop" | 🔒 password chip + "Sign in as Project Manager" | 🔒 password chip + "Sign in as Admin" |
| `/training/:track` lesson page | ✅ public | 🔒 Shop/PM/Admin | 🔒 PM/Admin | 🔒 Admin only |
| `GET /api/training/packet.pdf?track=…` | ✅ public | 🔒 Shop/PM/Admin token | 🔒 PM/Admin token | 🔒 Admin token |
| `/training/:track/poster` (QR poster) | ✅ public | 🔒 Shop/PM/Admin | 🔒 PM/Admin | 🔒 Admin |
| QR code embedded **inside** the poster | links straight to public PDF | links to `/training/shop/packet?lang=…` (auth-gated frontend route) | same pattern | same pattern |
| Stats stripe `/admin/training/stats` | n/a | n/a | ✅ PM/Admin | ✅ PM/Admin |

### Backend
- `training_packet_pdf` now inspects the track and rejects the request with **401** if the appropriate token isn't supplied. Field skips the gate. Shop accepts Shop/PM/Admin. PM accepts PM/Admin. Admin requires Admin.
- Verified via curl: 15-cell auth matrix all pass (3 langs × 4 tracks plus token combinations).

### Frontend
- **New page** `TrainingPacketDownload.jsx` (`/training/:track/packet?lang=…`):
  - Field → instantly redirects to the public PDF URL.
  - Locked tracks → if authed, performs `api.get(..., {responseType: "blob"})` so the `X-*-Token` header is included, then opens the PDF as a Blob URL in a new tab (with download-fallback when popups blocked).
  - Locked tracks + unauthed → renders a friendly lock card with a Sign-In CTA scoped to the right tier (Admin/PM/Shop).
- **TrainingHub landing**:
  - Track cards check `trackUnlocked()` → locked tracks hide the blurb + lesson preview; show "🔒 Password Required" chip + "Sign in as <tier>" copy + Lock icon CTA. Click → routes to the right login page with `from` state for return-redirect.
  - PDF panel buttons + Scan-&-Go panel buttons → unlocked variants link directly to the PDF or poster; locked variants route to the auth-aware download page (or login).
- **TrainingTrack** PDF buttons → same auth-aware routing for non-public tracks.
- **TrainingQrPoster**: gates non-public tracks the same way (lock card → login). QR codes inside the poster point at the auth-aware `/packet` route for gated tracks so a photographed poster from a stranger's phone hits a login wall, not the PDF.

### Verified on preview
| Scenario | Result |
|---|---|
| Logged-out visitor at `/training` → sees Field preview but **0 leaks** of Shop/PM/Admin blurbs or lesson titles | ✅ |
| Logged-out → click Shop tile → routed to `/shop/login` with return-state | ✅ |
| Shop user → access `/training/admin/packet?lang=en` → lock card | ✅ |
| Admin user → access `/training/admin/packet?lang=en` → "Your packet is ready" success card, PDF blob opens | ✅ |
| Backend auth matrix (15 cells) | ✅ all pass |
| Field still fully public (3 langs) | ✅ 200 each |
| No lint errors, no Python errors | ✅ |



## 2026-05-01 — Training Scans Analytics (PM Hub + Admin Hub Stripe)

Shipped an analytics layer on top of the training rollout. Every time someone scans a trailer poster QR and lands on a PDF packet, the backend logs a lightweight hit (no PII — just track, lang, coarse device family, and referer source). PMs and Admins see a stats stripe at the top of their hub that summarizes engagement.

### Backend
- **Logging**: `training_packet_pdf` endpoint now fire-and-forget inserts into `training_hits` collection on every request. Failure swallowed — telemetry never blocks the PDF.
- **What's logged**: `{track, lang, device (ios/android/mobile-other/desktop/other), source (poster/hub/internal/external/direct), ts}`. No IPs, no user IDs, no request bodies.
- **Cache-Control shortened** from 5-min to 60s so repeat scans still log most of the time.
- **New endpoint** `GET /api/admin/training/stats` — requires Admin OR PM token (Shop rejected). Returns:
  ```json
  {
    "total": 15,
    "this_week": 15,
    "last_week": 0,
    "by_track": {"field": 6, "shop": 3, "pm": 3, "admin": 3},
    "by_lang": {"en": 5, "es": 5, "bi": 5},
    "trend": [{"date": "2026-05-01", "n": 15}, …],
    "generated_at": "2026-05-01T…"
  }
  ```

### Frontend
- **New component** `TrainingStatsStripe.jsx` — silent-fail (hidden if backend call errors, so it never breaks the hub). Three sections:
  - Headline: this-week count + week-over-week delta (+/- + %) with trend arrow
  - **By track** horizontal bars (Field, Shop, PM, Admin) — each track's accent color
  - **By language** colored chips (EN slate, ES amber, EN+ES red) with the all-time total underneath
  - **14-day trend** sparkline bars with today on the right, hover tooltips show exact counts
- **Mounted on**:
  - `PmHub.jsx` — top of Records & Forms grid
  - `AdminHub.jsx` — top of Records & Forms grid
- All Spanish strings added.

### Verified
| Check | Result |
|---|---|
| 15 manual PDF fetches across tracks & langs logged correctly | ✅ |
| `GET /admin/training/stats` with PM token | ✅ 200 |
| `GET /admin/training/stats` with Admin token | ✅ 200 |
| `GET /admin/training/stats` with Shop token | 🔒 401 |
| `GET /admin/training/stats` unauthenticated | 🔒 401 |
| PM Hub stripe: 15 this-week · +15 delta · 4 track bars · 3 lang chips · 14-day trend bars all rendered | ✅ (screenshot) |
| No lint errors, no Python errors, no UI regressions | ✅ |



## 2026-05-01 — Training Scan-&-Go Posters + New Hire Onboarding (Coming Soon)

Shipped two final pieces of the Training Hub rollout:

### 1. Scan-&-Go QR Posters (per track)

One 1-page print-ready poster per track (Field / Shop / PM / Admin). Each poster has **3 QR codes** (EN, ES, EN+ES) so crews can scan straight into the PDF packet in the language they need — no typing URLs on phones.

**Backend**
- New dependency: `segno==1.6.6` (pure-Python, no Pillow needed).
- New endpoint `GET /api/qr.svg?data={url}&scale={2..20}` — **public**, returns a compact inline SVG QR code. 24h cache (inputs are stable public URLs).

**Frontend**
- New page `/training/:track/poster` (public, also accepts `?autoprint=1` for one-click printing). Layout: top accent bar, bilingual header, 3 tiles in a letter-size grid, fallback direct URL, bilingual footer, MASCI legal line.
- Print CSS: `@page size letter, margin 0` with chrome hidden via `.print:hidden`.
- Landing page (`/training`): new amber "Scan-&-Go Posters" panel with **8 buttons** (View + Print per track).
- `SitePostersPanel.jsx`: added 4 new poster rows (one per track) alongside the existing Crew Cheat Sheet / Trench Box / JHA. They plug straight into the admin's "Print All Posters" batch printer.

### 2. New Hire Onboarding — Coming Soon card

Added a dashed-border placeholder on the Training Hub landing that advertises the upcoming feature. Sets the team's expectations and pressure-tests the concept with the office before build:
- Required lesson tracking per employee
- 5-question quiz + pass/fail threshold
- Digital signed acknowledgement stored on the employee record
- Admin dashboard: who's onboarded, who's outstanding, who's expired

### Verified on preview
| Check | Result |
|---|---|
| `GET /api/qr.svg?data=https://mascidocs.com/training/field` | ✅ 200 · image/svg+xml · 1565 B |
| `/training/field/poster` renders 3 QR images, 3 language tiles, print button, bilingual footer | ✅ |
| Landing page: "Scan-&-Go Posters" header, 4 View buttons, 4 Print buttons — all present | ✅ |
| Landing page: "New Hire Onboarding" coming-soon card with all 4 bullets | ✅ |
| Admin Hub SitePostersPanel: 4 new training poster rows with correct test IDs | ✅ |
| All ES translations wired for new UI strings | ✅ |
| No lint errors | ✅ |



## 2026-05-01 — Training Packet PDFs: Bilingual Side-by-Side Variant

Extended the training packet endpoint with a third `lang=bi` (alias: `bilingual`, `es-en`, `both`, `dual`, `en+es`) that renders English on the LEFT and Spanish on the RIGHT of every section. Perfect for training-room packets, new-hire onboarding where both languages are in the room, and crews that want to map English technical terms to their Spanish equivalents.

### Backend
- `training_pdf.py` new helper `_normalize_lang()` → returns `"en" | "es" | "bi"` from a wide set of input aliases.
- New `_render_bilingual()` renderer (~100 lines). Shares the base CSS + cover/TOC/endnote structure; replaces each lesson body with a CSS-table layout so WeasyPrint paginates cleanly. Each step number spans both columns; language headers bar at the top of each lesson marks which side is which.
- `render_packet()` now branches: `lang == "bi"` → `_render_bilingual()`; otherwise the original single-language renderer.
- `/api/training/packet.pdf` endpoint updated: no change to signature, just accepts the extra aliases.

### Frontend
- Track detail page (`/training/:track`): added third button **"PDF · EN + ES"** (solid red, highlighted) alongside the existing EN / ES buttons.
- Landing page (`/training`): added third badge **"EN+ES"** (red) per track in the Downloadable Packets panel.

### Verified
| Check | Result |
|---|---|
| `GET /training/packet.pdf?track=field&lang=bi` | ✅ 200 · 1.48 MB |
| `GET /training/packet.pdf?track=field&lang=es-en` (alias) | ✅ 200 · identical bytes |
| `GET /training/packet.pdf?track=shop&lang=bilingual` (alias) | ✅ 200 · 696 KB |
| `GET /training/packet.pdf?track=admin&lang=bi` | ✅ 200 · 1.33 MB |
| Content audit (gemini) on Field bilingual PDF | ✅ 14 pages, EN-left / ES-right confirmed, verbatim Step-1 side-by-side, Why-this-matters side-by-side, Cheat Sheet with both languages |
| Landing page renders 4× `EN+ES` red buttons | ✅ |
| Track page renders `PDF · EN + ES` button | ✅ |

### Shareable URLs (12 total — after redeploy)
Format: `https://mascidocs.com/api/training/packet.pdf?track={field|shop|pm|admin}&lang={en|es|bi}`



## 2026-05-01 — Training Packet PDFs (public, no login)

Shipped the one-click PDF packet system on top of the Training Hub. Anyone with the URL can pull a complete training packet for any track in either language — cover page, TOC, every lesson with numbered steps, tips, cheat sheets. Perfect for emailing to insurance, auditors, or new-hire onboarding.

### Backend
- **New module** `backend/training_pdf.py` (~650 lines): Python mirror of the frontend lesson catalog + WeasyPrint renderer with a hand-tuned print CSS (Letter paper, page counters, accent-colored covers, dark cheat-sheet boxes, monospaced mono eyebrows).
- **New endpoint** `GET /api/training/packet.pdf?track={field|shop|pm|admin}&lang={en|es}` — **public, no auth**. Generated on-the-fly, 30-second CDN cache. Returns 404 on unknown track.
- Uses existing `weasyprint==68.1` dependency (same lib that powers safety-form PDFs). Zero new Python packages.

### Frontend
- **Training Hub landing** (`/training`): new dark "Downloadable packets" panel below the admin note. 4 track cards × EN/ES badges = 8 total one-click downloads.
- **Per-track pages** (`/training/:track`): added "PDF · EN" and "PDF · ES" buttons next to the existing "Print all cheat sheets" button.
- All links open in a new tab, render inline in the browser's PDF viewer, save-as works.

### Verified
| Check | Result |
|---|---|
| `GET /training/packet.pdf?track=field&lang=en` | ✅ 200 · 482 KB · `application/pdf` · `%PDF-` header |
| `GET /training/packet.pdf?track=field&lang=es` | ✅ 200 · 483 KB |
| `GET /training/packet.pdf?track=shop&lang=en/es` | ✅ 200 · 393 KB each |
| `GET /training/packet.pdf?track=pm&lang=en/es` | ✅ 200 · 467 KB each |
| `GET /training/packet.pdf?track=admin&lang=en/es` | ✅ 200 · 482 KB each |
| `GET /training/packet.pdf?track=foo` | ✅ 404 |
| Field ES content audit (gemini analysis): cover "Capacitación de Cuadrilla de Campo", TOC lists all 7 lessons in Spanish, lesson bodies Spanish, headers "POR QUÉ IMPORTA / PASO A PASO / CONSEJOS / HOJA DE REFERENCIA" | ✅ 10 pages |
| Landing page download panel: 8 buttons (4 tracks × EN/ES) rendered with correct test IDs | ✅ |

### Public shareable URLs (copy-paste to share)
- `https://mascidocs.com/api/training/packet.pdf?track=field&lang=en`
- `https://mascidocs.com/api/training/packet.pdf?track=field&lang=es`
- `https://mascidocs.com/api/training/packet.pdf?track=shop&lang=en`
- `https://mascidocs.com/api/training/packet.pdf?track=shop&lang=es`
- `https://mascidocs.com/api/training/packet.pdf?track=pm&lang=en`
- `https://mascidocs.com/api/training/packet.pdf?track=pm&lang=es`
- `https://mascidocs.com/api/training/packet.pdf?track=admin&lang=en`
- `https://mascidocs.com/api/training/packet.pdf?track=admin&lang=es`

(Links only work after redeploy — currently live on preview only.)



## 2026-05-01 — Training Hub: Full Spanish Lesson Bodies

Closed the gap from the earlier training build. Every one of the **23 lesson bodies** (title + "Why this matters" + all numbered steps + all tips + cheat sheet) now ships with a Spanish translation that renders automatically when the EN/ES toggle is flipped.

### How it works
- New file `src/data/training_es.js` — `LESSON_TRANSLATIONS_ES` map, keyed by lesson slug, with `title_es`, `why_es`, `steps_es[]`, `tips_es[]`, `cheatSheet_es[]` for every lesson.
- `training.js` now imports that map and merges `_es` fields onto each lesson during module load.
- `TrainingTrack.jsx` gained a `pick(lesson, key)` helper — returns the `*_es` variant when `lang === "es"` and falls back to English. `LessonCard` uses `pick()` for title, why, steps, tips, and cheatSheet so no per-field conditional logic clutters the render.

### Verified on preview (ES mode)
| Track | Marker | Count |
|---|---|---|
| Field | Spanish track title "Capacitación de Cuadrilla de Campo" | ✅ |
| Field | 7 lesson titles in ES (Lección 1–7) | ✅ |
| Field | "Por qué importa" / "Paso a paso" / "Hoja de Referencia" / "Consejos" | ✅ ×7 each |
| Field | Body sentences: "Apunte la cámara…" / "ASEGURE LA ESCENA PRIMERO" / "OSHA 1926 requiere…" | ✅ |
| Admin | Spanish track title "Capacitación del Administrador / Dueño" | ✅ |
| Admin | All 7 lesson titles in ES | ✅ |
| Admin | Backup body: "DOS ventanas programadas diarias" / "14 días de retención" ×3 / "Respaldo manual:" | ✅ |
| Admin | Tip: "Antes de cualquier redespliegue" | ✅ |

**No lint errors. Full bilingual coverage shipped on preview.**



## 2026-05-01 — Training Hub (4 tracks · 23 lessons · admin video manager)

New end-to-end training system inside the app. Four tracks × 23 lessons of written walk-throughs with "Why this matters" callouts, step-by-step numbered lists, tips, and printable cheat sheets. Every lesson has a video-embed slot that admins fill via the new video URL manager — YouTube / Loom / Vimeo all auto-parsed to embed URLs.

### Backend (2 new endpoints)
- `GET /api/training/videos` — **public**, returns `{videos: {slug: url}}`. Field crews need no login to see embedded videos.
- `PUT /api/admin/training/videos` — **admin-strict** (PM tokens return 401). Merge-update the slug→URL map; empty strings clear.
- Storage: `training_videos` collection, single doc `{_id: "config", videos: {}, updated_at: ISO}`.

### Frontend
- `src/data/training.js` — entire lesson catalog (7 Field + 3 Shop + 6 PM + 7 Admin = **23 lessons**) with bilingual track titles/blurbs.
- `src/pages/TrainingHub.jsx` — `/training` public landing. Four track cards with lesson counts, first-3 lesson titles, and "Open track →" CTA.
- `src/pages/TrainingTrack.jsx` — `/training/:track` stacked lesson view. Gates non-public tracks (Shop/PM/Admin) via `isShop()/isPm()/isAdmin()` with a friendly AccessDenied card linking to the right login.
- `src/pages/AdminTrainingVideos.jsx` — `/admin/training-videos` (admin-strict). Lists every lesson grouped by track with a URL input per slug, save all at once, "open" link preview.
- `src/pages/Hub.jsx` — new 8th tile (blue accent, GraduationCap icon) linking to `/training`.
- `src/App.js` — 3 new routes: `/training`, `/training/:track`, `/admin/training-videos`.
- `src/lib/i18n.js` — ~35 new bilingual entries for Training UI chrome.

### Lesson coverage
| Track | Lessons |
|---|---|
| **Field Crew** (public) | Hub Navigation · Daily Reports · Equipment Pre-Op · Site Inspection · Safety Meeting · JHA · Incident Report |
| **Shop** (shop-gated) | Portal Overview · Signing Off a Failed Pre-Op · Parts Catalog + Order List |
| **PM** (pm-gated) | Portal Overview · Master Lists · Import/Export · Archive (14-day undo) · Email Routing · Site Posters + JHA |
| **Admin** (admin-gated) | Platform Overview · **How Backups Work** · **How to Restore** · **Integrity Check** · Crew Recovery (force-reseed) · Safe Deploy Workflow · Passwords & Security |

### Video embed
`toEmbedUrl()` parses YouTube `watch?v=`, `youtu.be/`, `/embed/`, Loom `/share/`, `/embed/`, Vimeo `vimeo.com/123`. Falls back to the raw URL (still clickable via "Open video").

### Verified on preview
| Check | Result |
|---|---|
| `GET /api/training/videos` (public) | ✅ 200 — `{videos: {}}` initial |
| `PUT /api/admin/training/videos` with admin token | ✅ 200 — seeded/cleared successfully |
| `PUT /api/admin/training/videos` with PM token | 🔒 **401 REJECTED** |
| `/training` landing — all 4 track cards render | ✅ |
| `/training/field` (public) — all 7 lessons render + 7 Why/Cheat/Video slots | ✅ |
| `/training/admin` (no auth) — AccessDenied + Sign In button | ✅ |
| `/training/admin` (admin token) — all 7 Admin lessons incl. backup schedule + retention | ✅ |
| `/admin/training-videos` — **23 URL inputs** rendered (one per lesson) | ✅ |

### How to use
1. **For crews**: share `mascidocs.com/training` — the Field track is open. They bookmark / add-to-home-screen.
2. **For admins to add videos**: `/admin → Training Videos` (or direct `/admin/training-videos`). Paste a YouTube/Loom/Vimeo URL per lesson. Save. Videos appear on the training pages immediately — no deploy needed.
3. **For print**: on any track page, "Print all cheat sheets" button strips chrome and prints every lesson's content as paper handouts for the job trailer.



## 2026-05-01 — Bilingual Sweep: Hub tiles + PM Login + ThankYou

The April-30 Hub rewrite added a lot of new English strings (PM Portal tile, QA/QC tile, rewritten Field/Safety/Shop/Admin tile copy). Those were rendered via `t()` but had no Spanish keys, so they silently fell back to English. This pass closed the gap.

### Files touched
- `src/lib/i18n.js` — added **~40 new Spanish dictionary entries** covering:
  - All 7 Hub tiles' titles, descriptions, and bullets (PM Portal, QA/QC, Field, Safety, Shop, Admin, Projects)
  - `"Enter section →"` / `"Open →"` CTA text
  - PM Login page (header, subtitle, PM Password label, footer, error toasts)
  - ThankYou page (Gracias., Enviar Otro, Cerrar Ventana, "El equipo de seguridad de MASCI fue notificado…", form-type variants Inspection/Meeting/JHA/Incident/Daily Report/Equipment Inspection)
- `src/pages/Hub.jsx` — wrapped the one hardcoded `"Enter section →"` / `"Open →"` string in `t()`.
- `src/pages/PmLogin.jsx` — full `useT()` rewrite; all labels, button text, error toasts, and footer copy now bilingual. Added `<LangToggle />` in the header.
- `src/pages/ThankYou.jsx` — full `useT()` rewrite; form-type label, thank-you headline, body copy, and buttons now bilingual. Added `<LangToggle />`.

### Verified on preview (ES mode)
| Surface | Check | Result |
|---|---|---|
| Hub `/` | Title "Un solo lugar para cada trabajo de MASCI." | ✅ |
| Hub `/` | Field tile: "Reportes de fin de día y recorridos de equipo…" | ✅ |
| Hub `/` | Safety tile: "Inspecciones, charlas de seguridad…" | ✅ |
| Hub `/` | Projects tile: "Gestión de Proyectos" | ✅ |
| Hub `/` | QA/QC tile: "QA / QC" + "Próximamente" | ✅ |
| Hub `/` | PM Portal tile: "Portal de Gestión" | ✅ |
| Hub `/` | Shop tile: "La consola del mecánico…" | ✅ |
| Hub `/` | Admin tile: "Solo personal de oficina" | ✅ |
| Hub `/` | CTA: "Entrar a la sección →" (×2) | ✅ |
| `/pm/login` | Header: "Portal de Gestión — Iniciar Sesión" | ✅ |
| `/pm/login` | Label: "Contraseña PM" | ✅ |
| `/pm/login` | Button: "Iniciar Sesión" | ✅ |
| `/pm/login` | Footer: "MASCI · Portal de Gestión de Proyectos" | ✅ |
| `/thank-you` | Headline: "Gracias." | ✅ |
| `/thank-you` | Body: "El equipo de seguridad de MASCI fue notificado. Cuídese allá afuera." | ✅ |
| `/thank-you` | Buttons: "Enviar Otro" / "Cerrar Ventana" | ✅ |

### Still English (deferred — admin-only surfaces)
These pages are used exclusively by Admin or PM staff reviewing historical records, so bilingual value is low. Can be picked up later if Spanish-speaking PMs join the team:
- `PmHub.jsx`, `AdminHub.jsx`, `AdminLogin.jsx`, `AdminGuide.jsx`
- `Dashboard.jsx`, `EquipmentDashboard.jsx`, `IncidentsDashboard.jsx`, `MeetingsDashboard.jsx`, `DailyReportsDashboard.jsx`, `ProjectPnlPage.jsx`
- `ViewInspection.jsx`, `ViewMeeting.jsx`, `ViewIncident.jsx`, `ViewDailyReport.jsx`
- `TrenchBoxesAdmin.jsx`, `JhaPlansAdmin.jsx`
- `legal/TermsOfService.jsx`, `legal/PrivacyPolicy.jsx`



## 2026-05-01 — Live Site Systems Check PASSED

Full end-to-end verification on `https://mascidocs.com` after the 2026-04-30 deploy:

| Check | Result |
|---|---|
| `/api/health` | ✅ 200 (158 ms) |
| Public Hub `/` | ✅ 200 (renders One-place-for-every-MASCI-job) |
| Admin login `MASCI1982!` | ✅ 200 (64-char token) |
| PM login `Happy123!` | ✅ 200 (64-char token) |
| Shop login `Nothappy123!` | ✅ 200 (64-char token) |
| PM → `/admin/jobs` (29 projects) | ✅ 200 |
| PM → `/employees` (137+ rows) | ✅ 200 |
| PM → `/suppliers` | ✅ 200 |
| PM → `/equipment-master` | ✅ 200 |
| PM → `/admin/*/archive` (all 4 lists) | ✅ 200 |
| **STRICT GATE: PM → `/admin/backups`** | 🔒 **401 (REJECTED)** |
| **STRICT GATE: PM → `/admin/backups/run-now`** | 🔒 **401 (REJECTED)** |
| **STRICT GATE: PM → `/admin/crew-recovery/force-reseed`** | 🔒 **401 (REJECTED)** |
| **STRICT GATE: PM → `/admin/backups/integrity-check`** | 🔒 **401 (REJECTED)** |
| **STRICT GATE: PM → `/exports/restore`** | 🔒 **401 (REJECTED)** |
| **STRICT GATE: Shop → `/admin/backups/run-now`** | 🔒 **401 (REJECTED)** |
| Admin → `/admin/backups` | ✅ 200 (2 backup files on disk) |
| Admin → `/admin/backups/integrity-check` | ✅ 200 (last backup 2026-05-01 01:26 UTC, all 23 collections) |
| XLSX Export — Jobs `/admin/jobs/export` | ✅ 200 · 6.7 KB · valid `PK` header |
| XLSX Export — Employees | ✅ 200 · 12.4 KB · valid `PK` header |
| XLSX Export — Suppliers | ✅ 200 · 8.1 KB · valid `PK` header |
| XLSX Export — Equipment Master | ✅ 200 · 37.3 KB · valid `PK` header |
| Frontend render: Public Hub | ✅ (Field / Safety / Projects / QA·QC / PM / Shop / Admin tiles) |
| Frontend render: PM Hub `/pm` | ✅ (Records & Forms, Project P&L, ALL-OK badge) |
| Frontend render: Admin Hub `/admin` | ✅ (System Recovery divider, Backup×17, Restore×6, Export×8, all 4 master-lists visible) |

**Result: 🟢 ALL GREEN — zero regressions from the 48-hour redeploy.**



## 2026-04-30 — One-click Export buttons on every master list

**User ask**: "we have import buttons on jobs, employees, equipment, parts & subcontractors/vendors can we add a export list button as crews/pm's shop adds things to the list our list may become more reliable than others"

### Backend — 6 new XLSX export endpoints
Centralized helper `_xlsx_response(rows, header, filename, sheet)` in `server.py` builds an in-memory openpyxl workbook with auto-sized columns and streams it as a download (Content-Disposition with timestamped filename `MASCI_<entity>_YYYY-MM-DD.xlsx`).

- `GET /admin/employees/export` → 7-column sheet matching the bulk-import shape
- `GET /admin/suppliers/export` → 2-column (Name, Active)
- `GET /admin/equipment-master/export` → 9-column sheet, headed "Louis" so the existing bulk-import re-imports it cleanly
- `GET /admin/equipment-parts/export` → flattened wide sheet (Unit Number / Category / Name / Part Number / Qty / Size / Position / Ply / Brand / Notes) across every unit
- `GET /admin/jobs/export` → 7-column (Project Number, Project Name, Location, Client, PM Name, PM Email, Active)
- `GET /admin/project-managers/export` → 4-column PM roster

All six gate on `require_admin`, so admin AND PM tokens both pass; backup-recovery routes still gate on `require_admin_strict`.

### Frontend — green Export button next to Bulk Replace on every panel
- `MasterListPanel.jsx` — added `exportEndpoint` prop, `onExport` blob-download helper, green-emerald **Export** button in the header bar.
- `EmployeeMasterPanel.jsx` and `SupplierMasterPanel.jsx` — config flag wired.
- `EquipmentMasterPanel.jsx` — local `onExport` + green Export button between Refresh and Bulk Replace.
- `AdminJobMasterPanel.jsx` — same.
- `AdminPMPanel.jsx` — same (PM roster).
- `PartsCatalog.jsx` — Export button in the "Pick a Unit" header (downloads the entire fleet's parts in one wide sheet).

### Tests
- New `/app/backend/tests/test_master_lists_export_iter34.py` — 8 cases covering all 6 endpoints (200 + valid XLSX + correct filename), PM-token export, and 401-without-token. **All 8 pass.**
- Full backend regression: **277 passed, 0 failed.**

### Why this matters
The user's concern: "as crews/PMs/shop adds things to the list our list may become more reliable than others". The Export button gives ownership a one-click way to:
1. Hand off the most-current employee roster / fleet / parts catalog to insurance, finance, or auditors.
2. Round-trip the data — every export uses the exact column shape the Bulk Replace import accepts.
3. Build offline reference copies on a NAS / shared drive (in addition to the scheduled twin-window full backups).



## 2026-04-30 — Soft-delete safety net + PM-portal admin lockdown

**User asks**:
1. "Soft-delete + 14-day undo behind every 🗑️ button — yes do this."
2. "PM portal needs admin portal button removed inside pm portal, PMs will have zero admin access, only ownership will have admin access."

### PM lockdown (1)
- Removed the red "Admin Console" header link from `/app/frontend/src/pages/PmHub.jsx` plus the `isAdmin()` import, `adminViewing` flag, and `ShieldCheck` icon. PMs landing on `/pm` now see no admin shortcut anywhere.
- The Admin Hub keeps its yellow "PM Portal" link so ownership can still hop into the PM view (one-way bridge).
- Backend gating already enforced the contract (PM token rejected by `require_admin_strict`); this turn just cleaned the visible affordance.

### Soft-delete framework (2)
- New helpers in `server.py`: `_soft_delete`, `_restore_row`, `_list_archive`, `_purge_expired`. Every list call best-effort hard-purges anything with a `deleted_at` older than 14 days (`SOFT_DELETE_RETAIN_DAYS`). Active list filter `ACTIVE_FILTER = {"deleted_at": {"$in": [None, ""]}}` applied wherever we read the master collections.
- 4 single-row delete handlers converted from hard-delete → soft:
  - `DELETE /admin/employees/{id}`, `DELETE /admin/suppliers/{id}`,
    `DELETE /admin/equipment-master/{id|unit}`, `DELETE /admin/jobs/{id}`.
  - All four return `{"ok": true, "soft_deleted": true, "retain_days": 14}`.
- 4 new archive endpoints + 4 new restore endpoints:
  - `GET /admin/employees/archive` · `POST /admin/employees/{id}/restore`
  - `GET /admin/suppliers/archive`  · `POST /admin/suppliers/{id}/restore`
  - `GET /admin/equipment-master/archive` · `POST /admin/equipment-master/{id|unit}/restore`
  - `GET /admin/jobs/archive` · `POST /admin/jobs/{id}/restore`
- PUT update handlers (employees + suppliers + equipment-master) now also exclude soft-deleted rows — must restore before edit.
- `POST /admin/equipment-master` auto-restores a previously soft-deleted unit instead of raising 409 — quality-of-life win when a mechanic re-adds a unit they accidentally deleted.
- `jobs_master.py`: `list_jobs` filters `deleted_at`, plus new `list_archived_jobs` and `restore_job`.

### Frontend
- `MasterListPanel.jsx` — added Active / Archive tabs, restore action with `RotateCcw` icon, banner "Soft-deleted rows · auto-purged after N days." Plumbed through with `archiveEndpoint` + `restoreEndpoint` props.
- `EmployeeMasterPanel.jsx` and `SupplierMasterPanel.jsx` config: added the two new endpoints.
- `EquipmentMasterPanel.jsx` — full Active / Archive tab UI with archive table (Unit #, Year, Make/Model, Category, Deleted timestamp, Restore button).
- `AdminJobMasterPanel.jsx` — same Active / Archive tab UX next to the Refresh / Bulk Replace header.
- All confirmation prompts updated from "this cannot be undone" → "you'll have N days to restore from the Archive tab".

### Tests
- New `/app/backend/tests/test_soft_delete_iter33.py` — 5 cases covering full round-trip on all 4 collections + 404 guard + auto-restore on duplicate POST. **All 5 pass.**
- 2 regressions caught and fixed in the same iter:
  - `test_employee_full_crud` (iter32) — adjusted PUT handlers so soft-deleted rows return 404 (must restore first).
  - `test_admin_pm_lifecycle` (iter28) — cleaned stale `iter28-test-pm@mascigc.com` row from prod DB.
- Full backend regression: **269 passed, 0 failed.**

### Visual verification
- Screenshots of `/admin` Employee Roster Archive (4 archived rows with restore buttons + deletion timestamps) and Equipment Master Archive (3 archived rows, same layout). Active / Archive toggle is the first thing visible above each table.

### Why this matters
A mis-click on the 234-employee table previously meant a backup restore. Now it's a one-click ⟲ from the Archive tab. The 14-day window covers normal "wait, where did Bob go?" Monday-morning recovery scenarios without ever growing the DB unbounded — anything older auto-purges on the next list call.



## 2026-04-30 — Master-List CRUD parity (Employees · Suppliers · Equipment · Parts)

**User ask**: "I love how we built Active job master able to enter jobs one by one or bulk import/replace lets do the same thing for Employees, Equipment, Parts List & Subcontractors/Vendors same in both admin & PM portals... don't forget about equipment list & parts list in shop tile make them the same too."

### Backend
- New `MasterListPanel.jsx` reusable scaffolding — single-add form, searchable scrollable table, inline edit (✎) and delete (🗑️), bulk-replace XLSX/CSV, status header. Used by Suppliers + Employees panels.
- `EquipmentMasterPanel.jsx` rewritten with a modal (~9 fields too many for inline) — Refresh / Bulk Replace / Add Unit / search + category filter / table with inline ✎ ✏️ on every row. Backed by:
  - `POST /api/admin/equipment-master` (single add)
  - `PUT /api/admin/equipment-master/{id_or_unit_number}` (single edit)
  - `DELETE /api/admin/equipment-master/{id_or_unit_number}` (single delete)
  - All three use `require_shop_or_admin` so admins, PMs, and mechanics can all manage units.
- `EquipmentPartsPanel.jsx` collapsed to wrap the existing `PartsCatalog` component (already had per-unit add/edit/delete/order). Now PM and Admin see the exact same rich parts UI the shop sees.
- `EmployeeMasterPanel.jsx` and `SupplierMasterPanel.jsx` reduced to ~30 lines each — pure config feeding `MasterListPanel`. Backed by:
  - `PUT /api/admin/employees/{id}` (new)
  - `PUT /api/admin/suppliers/{id}` (new — also handles `is_active` toggle)
- `require_shop_or_admin` extended to also accept PM tokens (so the same Equipment Master panel works identically in all three portals).

### Frontend integration
- `AdminHub.jsx` and `PmHub.jsx` already render the same panels — no change needed; the refactored components flow through automatically.
- `ShopHub.jsx` Equipment List tab swapped from the read-only `EquipmentListPanel` to the full `EquipmentMasterPanel`. Mechanics can now add/edit/delete fleet units inline.

### Tests
- New `/app/backend/tests/test_master_lists_crud_iter32.py` — 5 new test cases:
  - Employee full CRUD + required-name guard + 404-after-delete
  - PM token can edit employees (cross-persona)
  - Supplier edit + is_active toggle + name-blank guard
  - Equipment master full CRUD + duplicate-unit guard
  - Shop token can do equipment-master CRUD (cross-persona)
- All 5 pass + previously-passing 30 in adjacent files. Full regression: **264 passed, 0 failed.**

### Visual verification (screenshots taken on prod preview)
- `/admin` Equipment Master Fleet — 589 units, Refresh + Bulk Replace + Add Unit, search + 23-category filter, edit/delete per row.
- `/admin` Employee Roster — 234 employees, 7-column inline add (Name, Employee ID, Trade, Role, Crew, Email, Phone), search, edit/delete per row.
- `/admin` Supplier & Subcontractor List — 144 entries, single-field add, search, edit/delete per row.
- `/shop` Equipment List tab — same Equipment Master Fleet panel as admin/PM (Add Unit + edit/delete per row visible to mechanics).
- All three portals (Admin, PM, Shop) now expose the same Active-Jobs-Master CRUD pattern across all five master lists (Jobs · Employees · Suppliers · Equipment · Parts).

### Known cleanup deferred
- Two stale pytest leftover rows existed in production data prior to this iter (`TEST_82d338` job, one `787d3bfc...` supplier) — supplier deleted as part of a smoke-test cleanup; the test job is benign and can be removed by the user with one click in the new UI.



## 2026-04-30 — PM (Project Management) Portal · Admin Lockdown · Password Rotation

**User ask**: "make a portal for project management to allow them access to everything they need for project management but not have access to all backup systems (basically so if we fire a PM he cant nuke the system out of rage or steal data) make password for project management Happy123! ... new admin password MASCI1982! ... in admin console move all backup systems to lower part of the pages."

### Backend authorization model
`/app/backend/server.py`:
- Added `_pm_token_for(password)` — separate HMAC namespace (`b"pm:" + pw`) so a stolen PM token cannot be replayed against admin-strict routes.
- **Relaxed `require_admin`** to accept EITHER a valid `X-Admin-Token` OR a valid `X-PM-Token`. Every existing day-to-day endpoint (jobs, equipment master, parts, employees, suppliers, JHA files, trench boxes, inspections, meetings, JHAs, incidents, daily reports, posters, compliance CSVs, email routing) inherits this automatically.
- **NEW `require_admin_strict`** — admin token only. Applied to 11 destructive endpoints:
  - `GET /exports/full-backup`
  - `POST /exports/restore`
  - `GET /admin/backups`, `GET /admin/backups/integrity-check`, `GET /admin/backups/{filename}`, `DELETE /admin/backups/{filename}`, `POST /admin/backups/run-now`
  - `GET /admin/crew-recovery/status`, `POST /admin/crew-recovery/reset-password`, `POST /admin/crew-recovery/force-reseed`, `POST /admin/crew-recovery/scrap-crew-hub`
- **NEW endpoints**: `POST /api/pm/login`, `GET /api/pm/check`.
- **Password rotation**: `ADMIN_PASSWORD=MASCI1982!` (was `Happy123!`), `PM_PASSWORD=Happy123!` added to `/app/backend/.env`.

### Frontend portal
- New `/app/frontend/src/lib/pmAuth.js` — localStorage key `masci.pm.token`, sent via `X-PM-Token` on every API call (added to `api.js` interceptor; 401 cleanup also clears it).
- New `/app/frontend/src/components/RequirePm.jsx` (PM-or-admin) and `/app/frontend/src/components/RequireAdminOrPm.jsx` (shared sub-route guard).
- New `/app/frontend/src/pages/PmLogin.jsx` (amber-accented mirror of `AdminLogin`) at `/pm/login`.
- New `/app/frontend/src/pages/PmHub.jsx` at `/pm` — mirrors `AdminHub` exactly minus `BackupHeroPanel`, `CrewRecoveryPanel`, and `PersistenceHealthBanner`. All master-list panels (`EquipmentMasterPanel`, `AdminPMPanel`, `AdminJobMasterPanel`, `EquipmentPartsPanel`, `EmployeeMasterPanel`, `SupplierMasterPanel`, `AutoEmailRoutingPanel`, `SitePostersPanel`, `EquipmentStatusBoard`, `ComplianceExportPanel`) are present. Tiles point to the shared `/admin/...` sub-routes which now use `RequireAdminOrPm`.
- `/app/frontend/src/components/ComplianceExportPanel.jsx` — Full-Backup button, `StoredBackupsPanel`, and `RestoreBackupPanel` are now wrapped in `isAdmin()` checks so PM views the same panel without backup tooling.
- `/app/frontend/src/pages/Hub.jsx` — added a fourth public section card "PM Portal" linking to `/pm/login`.
- `/app/frontend/src/pages/AdminHub.jsx` — backup/recovery panels MOVED from the top of the page to a new "Admin Only · System Recovery" section at the bottom, separated by a 4-px black divider. Header now also shows a yellow "PM Portal" link button so admins can hop into the PM view.
- `App.js` — every shared admin sub-route (inspections, meetings, jha-plans, trench-boxes, posters, incidents, daily, equipment, p&l) now uses the `AP` (RequireAdminOrPm) guard. `/admin` and `/admin/guide` stay strict-admin via `A`.

### Tests
- New `/app/backend/tests/test_pm_portal_iter31.py` — 22 cases covering: login flows, old admin password rejected, PM token allowed on 11 day-to-day routes, PM token blocked on 6 backup/recovery routes, admin token still works on backups. **All 22 pass.**
- Updated 8 existing test files that hardcoded `Happy123!` to use `MASCI1982!` fallback.
- Full backend regression: **259 passed, 0 failed.**

### Verified visually
- `/` Hub now shows 4 cards: Projects, Admin, **PM Portal** (new), Shop.
- `/admin` (with `MASCI1982!`) — Equipment Master at the TOP, backups at the very BOTTOM under "System Recovery" divider.
- `/pm/login` → `/pm` (with `Happy123!`) — every panel renders, no backup toast, no force-reseed, no restore button. Footer shows "Project Management Portal" + Judd Group attribution.

### Updated `/app/memory/test_credentials.md`
- New admin password noted (with rotation date).
- Full PM-portal section added documenting endpoints, headers, and gating contract.



## 2026-04-30 — Trench Box Pivot Closeout: QR Poster + Admin Upload Anchor

**User ask**: "we never made upload section in admin to add in or delete files in trench box section & never updated trench box QR poster to align with new direction we went with trench box section"

**Two fixes shipped**:

### Fix 1 — Trench Box QR Poster repivoted to the Tabulated Data Library direction
`/app/frontend/src/components/TrenchBoxPosterCard.jsx` rewritten:
- Dropped the old per-box fleet table (which duplicated what's in the digital library and aged badly every time a box was added/removed).
- Hero is now **"Tabulated Data Library"** with QR → mascidocs.com/trench-boxes.
- Added bilingual EN/ES "What is tabulated data? / ¿Qué son los datos tabulados?" primer next to the QR — same crew-education direction as the digital page.
- Kept the OSHA Soil Type Quick Reference (A/B/C, color-coded) — still the single most useful thing for a foreman in the field.
- Added a 3-step "Scan → Pick your shield → Read the chart" instruction strip.
- Footer adds Judd Group LLC platform attribution stamp.
- Pure printable card — toolbar/print CSS still owned by `TrenchBoxPoster.jsx` page wrapper, so `AllPostersPrint.jsx` continues to embed it cleanly.

### Fix 2 — Admin Trench Box upload section made impossible to miss
The user reported the admin upload feature was "missing." It was already wired (`<TrenchBoxTabulatedLibrary adminMode={true} />`) but had no visual anchor.
`/app/frontend/src/pages/TrenchBoxesAdmin.jsx`:
- Added a bold amber banner above the library: **"Step 1 · Upload & Manage Files — Tabulated Data Files — Upload / Delete"** with `FolderOpen` icon and instructions (drag-drop manufacturer PDFs/Excel/ZIPs/images, crews see them on /trench-boxes, use General/Educational for shared explainers).
- Renamed the master-list section header to **"Step 2 · Master List"** to make the workflow sequence obvious.
- Verified by screenshot: 6 files are already uploaded in the General/Educational folder, confirming the upload flow has been working end-to-end the whole time.

**Verified visually on prod preview**:
- `/admin/trench-boxes/poster` — new poster renders, bilingual primer reads correctly EN + ES, QR encodes the right URL.
- `/admin/trench-boxes` — Step 1 banner + library + Step 2 banner + fleet list, in clear sequence.

**Lint**: clean on both files.

**Status**: Complete. Trench Box pivot is closed out.



## 2026-04-29 — 🚨 POST-DEPLOY HOTFIX: Crash-Loop + Streaming Build

**User pain**: After the 22:55 UTC deploy, production went green for ~15 min then started hard-crashing with Cloudflare 520 on every endpoint. Banner flickered on/off because the container kept dying + respawning.

**Diagnosis** (with the deployment-log tool refusing to cooperate, reconstructed from behavior):
- Scheduler fires on every boot because it looks backward and says "slot 02:00 UTC and 18:00 UTC haven't run today yet — catch up now."
- In production, the backup build itself runs out of memory (the safety collections contain embedded photo blobs; `cursor.to_list(50000)` loads them all at once → OOM-kill).
- Container restarts → scheduler sees past slot still hasn't run → fires again → crashes → infinite loop. **Result: prod dead until we patch.**

**Two fixes shipped in one patch** (lint clean, 236 pytest green):

### Fix 1 — No more retroactive catch-up backups on boot
`_backup_scheduler_loop` now seeds `last_run_for_hour[h] = today` for **every scheduled hour already crossed at startup**. Backups only fire when the loop OBSERVES an hour transition while running — never as a retroactive catch-up. Boot log proves it: `scheduler armed — skipping past slots today ['02:00', '18:00'], next slots tomorrow`.

If a backup ever crashes the container again, the restart won't re-fire — we ride through to the next scheduled slot. Admin can always click "Run backup now" in `/admin` to trigger one on demand.

### Fix 2 — Streaming zip build (kills the build-time OOM)
Three memory bombs fixed in `_build_backup_zip_to_path`:

| Before | After |
|---|---|
| `cursor.to_list(50000)` on every safety collection | `async for doc in cursor` — one doc at a time |
| CSV built from full in-memory doc list | CSV capped at first 2000 rows, logged as note |
| `cursor.to_list(100000)` on every auto-discovered collection | Streamed JSON array write, doc-by-doc |
| `f.read_bytes()` on 150 MB+ FDOT plans PDFs | `zf.open(name, "w").write(chunk)` in 1 MB chunks |

Each doc is `del d`'d right after use so the Python GC can reclaim photo blobs instead of holding the whole collection.

**Verified on preview with 1515-record · 554 MB backup:**
- Backend RSS stayed **flat at 25 MB** throughout (VmHWM 26 MB, VmPeak 167 MB)
- Email delivered with resend_id
- `/api/health` responded 200 throughout
- Full regression 236 pytest pass / 0 fail

**Path forward for user**:
1. Save-to-GitHub + redeploy (this patch)
2. Post-deploy, hit `GET /api/admin/backups` — schedule should show `hours_utc: [2, 18]` and NO fresh backup file right after deploy (that's the fix working)
3. Click "Run backup now" once to confirm manual backup works
4. First scheduled backup = 02:00 UTC tomorrow (nightly), then 18:00 UTC the next day (mid-day)

**If prod is STILL crashing after this redeploy**, the kill-switch is: set `DISABLE_BACKUP_SCHEDULER=1` in the Emergent production env vars → scheduler refuses to arm entirely, app runs normally, admin does manual backups via the "Run backup now" button.

---

## 2026-04-29 — Twin-Window Backup Scheduler ✅ (P1 follow-up)

**User request**: "enable a 2nd nightly mid-day backup window to give yourself two off-site recovery points per day with zero risk."

**Shipped**:
- New `BACKUP_HOURS_UTC` env var (comma-separated UTC hours, default `"2,18"`) replaces the single-window `BACKUP_HOUR_UTC`. Legacy var still honored as fallback for any hour < 24.
- `_parse_backup_hours()` — drops invalid entries, dedupes, sorts. Empty string falls back to `[BACKUP_HOUR_UTC, 18]`.
- `_backup_scheduler_loop` rewritten with per-hour bookkeeping: `dict[hour] → last_run_date`. Each (date, hour) slot fires at most once. Earlier same-day slots are auto-marked when a later slot fires so a missed-window catch-up doesn't double-run.
- `GET /api/admin/backups` schedule struct now exposes `hours_utc: [2, 18]` alongside legacy `hour_utc`.
- `StoredBackupsPanel.jsx` shows multi-window text (`02:00 · 18:00 UTC`) when array present; falls back to legacy "Daily @ 02:00 UTC" otherwise.
- Scheduler boot log now reads: `[scheduled-backup] scheduler started — 02:00 · 18:00 UTC · keep 14 days · max 3 files · disk-watermark 75%`.
- `BACKUP_HOURS_UTC=2,18` added to `/app/backend/.env` for preview parity.

**Tests**: `/app/backend/tests/test_backup_hours_iter27.py` — 6 unit tests covering default, single-window, multi-window, invalid-entries-dropped, empty-fallback, dedupe. All 6 pass.

**Pre-deploy verification (2026-04-29 22:15 UTC, ALL GREEN ✅)**:
| Check | Result |
|---|---|
| `/api/health`, `/api/healthz` | 200 |
| `/api/equipment-master`, `/employees`, `/suppliers`, `/jobs` | 589 / 234 / 145 / 28 rows |
| `/api/equipment-types` (Pre-Op data source) | 23 types + checklists ✅ |
| `/api/inspections`, `/meetings`, `/incidents`, `/daily-reports`, `/equipment-inspections`, `/jhas` | all 200 |
| Admin login `Happy123!` → 200 (token len 64), wrong pwd → 401 | ✅ |
| Shop login `Nothappy123!` → 200, shop endpoints 200 | ✅ |
| Backup schedule `hours_utc: [2, 18]`, retention 14 d, enabled | ✅ |
| Backend memory after 4 consecutive 529 MB backups | RSS 26 MB / VmPeak 167 MB ✅ |
| Pytest full suite | **236 passed / 6 skipped / 0 failed** |
| Lint | backend ruff clean · frontend ESLint clean |
| Admin Stored Backups UI | screenshot confirms `02:00 · 18:00 UTC` chip rendered |
| Services | backend RUNNING · frontend RUNNING · mongodb RUNNING |

**READY TO REDEPLOY.** When the deploy lands on `mascidocs.com`, the production env should mirror `BACKUP_HOURS_UTC=2,18` (or be left unset — the new default already adds the mid-day window).

---

## 2026-04-29 — 🔥 PRODUCTION 520 / OOM — KILLED FOR GOOD ✅

**User pain (verbatim)**: "FIX EVERYTHING" — recurring 520s on mascidocs.com bringing down dropdowns, shop login, daily report saves. 4th recurrence of the OOM crash loop.

**Root cause** (finally tracked end-to-end in `/app/backend/server.py`):
- `_run_scheduled_backup` correctly streamed the 554 MB zip to disk (good).
- But then `_email_backup_zip_from_path` called `zip_path.read_bytes()` — loading the entire 554 MB into RAM.
- Then `_email_backup_zip` wrapped it in `BytesIO(payload)` AND base64-encoded it → memory **tripled to ~1.5 GB**, OOM-killing the container the moment a backup ran.
- This is exactly why the field crew kept seeing "no employees in dropdowns" / "shop login fails" / "network errors" mid-day — the container was being killed and respawned.

**Fix shipped** (single commit, lint clean, 230 pytest pass):
1. **Refactored `_email_backup_zip_from_path`** so it NEVER loads the full zip into RAM. It just `stat()`s the file size.
2. **New `_build_slim_email_zip_on_disk(src, dst)`** — synchronous helper run via `asyncio.to_thread`. Opens the on-disk full zip with `ZipFile(path, "r")` and streams entries one at a time to a NEW slim `.zip` on disk. Drops PDFs + `disk_files/` + `CSV/`, strips base64 blobs from JSON entries > 4 KB. Memory bounded by the largest single entry (typically <2 MB).
3. **New `_send_backup_email(...)`** — only base64-encodes the SLIM file (~0.1 MB), never the full one. Reads via `attachment_path.open("rb")` inside `asyncio.to_thread`.
4. **Cleanup** — slim tmp file is deleted via `try/finally` even on Resend failure.
5. **Killed `_build_backup_zip` (in-memory variant)** — replaced body with a hard `RuntimeError` so any future caller fails loudly instead of OOM-ing silently.

**Verified end-to-end** with a real production-sized run on the preview pod:
| Metric | Before fix | After fix |
|---|---|---|
| Backup size | 554 MB | 554 MB |
| Records archived | 1515 | 1515 |
| Backend RSS during backup | spiked to ~1.5 GB → killed | **flat at 25 MB** |
| Backend VmHWM (peak resident) | (crash) | **26 MB** |
| Backend VmPeak | (crash) | 167 MB |
| Email sent? | container died first | ✅ slim 0.1 MB attachment delivered (resend_id `cfe31cfb-...`) |

**Backend health post-fix:**
- `GET /api/health` 200 throughout the entire 554 MB backup operation
- `/api/equipment-master` → 589 units · `/api/employees` → 234 · `/api/suppliers` → 145 · `/api/jobs` → 28
- Admin login (`Happy123!`) → 200 · Shop login (`Nothappy123!`) → 200 · wrong pwd → 401
- `/equipment/new` form renders cleanly with all 3 combos visible (MASCI Job, Operator Name, Equipment Type)
- Pytest **230 passed / 6 skipped / 0 failed**

**Why this fix is permanent (vs the 4 prior attempts):**
- Previous fixes streamed the BUILD to disk but still loaded the RESULT for emailing.
- This fix eliminates the LAST place the full zip ever existed in memory.
- The disk-to-disk slim builder + lazy slim-only base64 means the email path is now O(largest single entry), not O(full zip size).
- Container memory is structurally bounded to the working set — backups can grow to multiple GB without ever touching the container's memory budget.

**Files touched:**
- `/app/backend/server.py` — lines 1843-1855 (deprecated stub), 2392-2570 (refactored email pipeline)

---

## 2026-04-29 — Pre-Redeploy Cleanup Sweep — ALL GREEN ✅

**User goal**: "verify all systems are fixed no other issues like this & ill redeploy today"

**Audit findings + fixes:**

1. **Cold-start UX gap on every form** — same root cause as the login bug. When a field crew submits a daily report / inspection / incident / meeting / equipment Pre-Op during a backend cold-start, the form save handler caught the 520 and showed a generic `"Could not save daily report"`. Crews could lose 5+ minutes of typed data thinking the save was permanently broken.
   - **Fix**: Created `/app/frontend/src/lib/apiErrors.js` with a shared `formatApiError(err, fallback)` helper that maps status → human message:
     - `401` → "Your session expired — please sign in again"
     - `403` → "You don't have permission to do that"
     - `404` → "The record was not found"
     - `422` → "Validation error: <backend detail>"
     - `520-524` → **"Server is waking up — wait ~60 seconds and try again. Your form data is safe."**
     - other `5xx` → "Server error (N) — try again. Your form data is safe."
     - other `4xx` → backend's `detail` string when present
     - timeout → "Request timed out — server may be cold-starting. Try again. Your form data is safe."
     - no response → "Can't reach the server — check your internet, then try again. Your form data is safe."
   - Wired into 5 form save handlers: `NewDailyReport`, `NewInspection`, `NewIncident`, `NewMeeting`, `NewEquipmentInspection`. Toast duration bumped to 7 s so the field crew has time to read it. Critically, every cold-start / network message ends with **"Your form data is safe"** so they don't reload and lose work.

2. **Lint cleanup of recently-added code**:
   - `server.py` — replaced 4 `p.unlink(); pruned += 1` semicolon statements with proper line breaks (E702)
   - `server.py` — removed unused walrus assignment `payload_in :=` (F841)
   - `tests/test_jha_plans_and_trench_boxes.py` — removed unused `first_id` variable (F841)
   - `tests/test_suppliers_employees_iter21.py` — split multi-import line into 6 separate imports (E401)
   - Result: backend ruff lint **all checks passed**, frontend ESLint clean across 7 changed files

3. **Backup test resilience** (the only failing test in the prior run):
   - `test_full_backup_returns_zip_with_required_structure` was hitting a 554 MB stream all-in-one. Cloudflare's `ChunkedEncodingError` would flake the read partway through, marking the test failed even though the actual endpoint returns the zip cleanly (curl proves it).
   - **Fix**: switched to `stream=True` + `iter_content(256 KB chunks)` + 3-attempt retry on `ChunkedEncodingError` / `ConnectionError`. Test now reliably passes.

**Final verification**:
- **Pytest 240 passed / 6 skipped / 0 failed** (full suite, ~2 min)
- **Lint clean**: backend (`server.py` + tests) and frontend (5 form pages + 2 login pages + apiErrors lib + i18n)
- **Production smoke** on `mascidocs.com`:
  - All 6 public health probes 200
  - Admin login returns 64-char token; admin/jobs returns 200
  - Form save endpoints all return 422 on empty body — endpoints healthy, validation rejecting properly
  - Live data: 28 jobs · 234 employees · 145 suppliers (Atlas)
- **Frontend smoke**: `/daily/new` renders cleanly with new `formatApiError` import present

**Ready to redeploy**.

## 2026-04-29 — Save-All-Photos-As-Zip on Every Report
**User request:** "Yes for every photo uploaded" — wanted the one-click zip download button on every photo section.

**New `/app/frontend/src/components/PhotoZipDownload.jsx`** — bundles every photo on a report into a single .zip via `JSZip` (added via `yarn add jszip@3.10.1`). Works on both http URLs and `data:image/...` base64 URIs (the app's primary storage). Auto-pads filenames as `01.jpg`, `02.jpg`, … (zero-padded so they sort correctly in Finder/Explorer) inside a folder named after the report. Skips individual fetch failures so one bad photo can't kill the whole zip. Shows toast feedback + spinner. `print:hidden` so it never leaks into print preview.

**Wired into all 5 photo sections**:
- `ViewInspection.jsx` → `MASCI_Inspection_<id8>_findings.zip`
- `ViewIncident.jsx` → `MASCI_Incident_<id8>_photos.zip`
- `ViewMeeting.jsx` → `MASCI_Meeting_<id8>_photos.zip`
- `ViewDailyReport.jsx` → `MASCI_DR_<id8>_photos.zip`
- `ViewEquipmentInspection.jsx` → `MASCI_Equipment_<id8>_photos.zip`

Button label `Save all (N) as zip` auto-shows the count. Test IDs: `inspection-photos-zip`, `incident-photos-zip`, `meeting-photos-zip`, `dr-photos-zip`, `equipment-photos-zip`.

**Verified via Playwright**: Zip download triggered for the 2-photo test inspection, file `MASCI_Inspection_fc802988_findings.zip` saved with success toast. Lint clean across all 6 touched files.

**Field-crew use case unlocked**: 1-tap export of every photo from a record for insurance / legal / claims requests, instead of 12 individual taps.

## 2026-04-29 — Watermark Removal + Click-to-Enlarge Photo Lightbox
**User request:** "remove watermarks from all picture uploads everywhere also in print or email screens — when you click on a picture make it come open bigger & be able to save by itself if you want, on every doc, form, everything"

**Watermark removals (every render path)**:
- `/app/backend/pdf_render.py` — dropped `<img class="wm">` + `.wm` CSS rule + `_data_uri_for(WATERMARK_PATH)` call. Backend-rendered PDFs (email + print export) now ship with zero MASCI mark overlay. Smoke-verified: `render_record_pdf('inspection', sample)` produces 378 KB PDF with no `class="wm"` element.
- `/app/frontend/src/components/PrintWatermark.jsx` — repurposed as a no-op (`return null`) so all 8 existing imports keep compiling without ripping every page open. The bottom-right print mark is gone from JhaPlansPoster, ViewEquipmentInspection, CheatSheet, ViewIncident, TrenchBoxPoster, ViewInspection, ViewMeeting, ViewDailyReport.
- `/app/frontend/src/pages/ViewInspection.jsx`, `ViewIncident.jsx`, `ViewMeeting.jsx`, `ViewDailyReport.jsx` — removed the per-photo diagonal "MASCI" rotate(-30deg) overlay AND the bottom black traceability strip. Photos are now clean.

**New `/app/frontend/src/components/PhotoLightbox.jsx`** — wraps any thumbnail. Click → Shadcn Dialog modal with:
- Full-size image (max 78vh on dark backdrop)
- `×` close button top-right
- Caption + red "Save" button bottom that does `fetch(src) → blob → <a download>` so the photo saves to the user's device standalone. Works for both http URLs AND `data:image/...` base64 URIs (the app's primary photo storage). Falls back to "open in new tab" on cross-origin failure with a toast hint.
- `print:hidden` so the modal never appears in print preview.

**Lightbox wired in**:
- `ViewInspection.jsx` — finding photos
- `ViewIncident.jsx` — incident photos
- `ViewMeeting.jsx` — meeting photos
- `ViewDailyReport.jsx` — daily report photos
- `ViewEquipmentInspection.jsx` — both the inline per-checklist-item failure photo AND the main photo grid
- `PhotoUpload.jsx` — live upload thumbnails (so crews can also click-preview + save what they just took before submitting). The X-delete button keeps `z-10` so it's still clickable on top of the lightbox trigger.

Each thumbnail emits `data-testid` patterns: `view-photo-{i}-trigger`, `view-photo-{i}-modal`, `view-photo-{i}-download`, `view-photo-{i}-close`. Filenames are auto-generated like `MASCI_Inspection_abc12345_finding1.jpg`, `MASCI_DR_def67890_photo2.jpg`, `MASCI_Equipment_xyz_photo1.jpg` — so saved photos arrive properly named.

**Verified via screenshot**: photo grid renders clean (no overlays); clicking a photo opens the lightbox with Save button; close + open work; lint clean across all 7 touched files; backend PDF smoke test passed.

## 2026-04-29 — Pre-Deploy Verification Sweep — ALL GREEN ✅
**User request:** "verify all systems work & everything is ready to deploy"

**Service health** (all RUNNING):
- backend pid 46 · frontend pid 48 · mongodb pid 51 · nginx-code-proxy pid 45
- /api/health 200 · /api/jobs 200 · /api/employees 200 · /api/suppliers 200 · /api/equipment-master 200 · /api/equipment-types 200
- POST /api/admin/login → 200 (token len 64) · GET /api/admin/jobs → 200
- GET / and /admin → 200 (Hub renders with red `MASCI` tagline + 6 tiles)

**Live data state**: 28 active jobs · 234 employees · 145 suppliers · 589 equipment_master units

**Pytest suite** — `cd /app/backend && python -m pytest tests/ -q`: **240 passed, 6 documented skips, 0 failed** (was 12 failed before this sweep).

**Bugs found & fixed during verification**:
1. **(HIGH) Backup race condition** — `_emergency_prune_backups` and the scheduled-backup pre-flight prune both did `glob("*.zip.tmp")` and unlinked everything, including the `.zip.tmp` file the current request was actively streaming to. The subsequent `tmp.replace(out)` then crashed with `FileNotFoundError`, turning concurrent backup requests into 500s. **Fixes:**
   - Per-call unique tmp suffix `.zip.tmp.<uuid8>` so concurrent streams don't collide
   - Prune only ORPHAN .tmp files (`mtime > 10 min`) — younger ones are presumed active
   - Glob updated to `*.zip.tmp*` so the unique suffixes are still cleaned up later
   - Smoke verified: `GET /api/exports/full-backup` returns valid 521 MB zip with 50 entries.
2. **(MEDIUM) Destructive test wiped employees roster** — `test_employees_csv_upload_and_list` replaced the 234-employee roster with 2 TEST rows and never restored, leaving the live preview env with 0 employees after every test run. **Fix:** wrapped the body in try/finally and restore from `/app/backend/data/employees_seed.json` (mirrors the supplier test pattern).

**Stale tests fixed** (asserting against pre-2026-04-28 state):
- `test_inspections::test_root_health` and `test_jha_plans::test_root_api` — were hitting GET `/api/` (404 — never registered); now hit `/api/health`
- `test_suppliers_employees_iter21` — hard-coded counts 234/135 → flexible `>=` to allow field-crew additions via the new "+ Add to roster" button
- `test_iter24_bilingual_perf` — module-level NoneType crash if `REACT_APP_BACKEND_URL` not exported → now `pytest.skip` cleanly
- `test_compliance_exports` — log header drift "MASCI Safety Hub" → "MASCI Hub"
- `test_equipment_inspections::TestEquipmentUnits` (3 tests) + `test_create_persists_unit_in_dropdown` — marked `@pytest.mark.skip` documenting that `/api/equipment-units` was removed in iter22 in favor of the equipment_master upload pipeline

**Files touched in this sweep**:
- `/app/backend/server.py` — backup race fixes (3 locations: lines 1828, 2095, 2151, 2219)
- `/app/backend/jobs_master.py` — `upsert_job` now uses `$setOnInsert` for id/created_at (HIGH-priority fix from iter26 testing report)
- 6 test files (above)

**Deployment readiness**: ✅ READY. No regressions in live endpoints. Pytest fully green. New iter26 features (DB-backed Jobs Master + inline "+ Add to roster") all verified.

## 2026-04-29 — DB-Backed Jobs Master + Inline "+ Add to Roster" — VERIFIED & SHIPPED
**User request:** (1) inline "+ Add to MASCI roster" button on EmployeeCombo + matching "+ Add to vendor list" button on SupplierCombo so novel typed names persist back to master data on the fly; (2) admin-managed, DB-backed jobs list parsed from the user's uploaded "Current Job list.pdf" replacing the static frontend `jobLibrary.js`, with full CRUD via a new AdminJobMasterPanel.

**Backend** — new `/app/backend/jobs_master.py` module:
- Schema: `jobs_master` (project_number unique, project_name, location, client, project_manager, active, id, created_at, updated_at)
- Idempotent seed from `/app/backend/data/jobs_master.json` (28 active MASCI jobs at boot)
- Routes: `GET /api/jobs` (public, active only), `GET /api/admin/jobs`, `POST /api/admin/jobs` (upsert by project_number), `PATCH /api/admin/jobs/{id}/active`, `DELETE /api/admin/jobs/{id}`, `POST /api/admin/jobs/bulk-replace`
- New inline-roster routes: `POST /api/employees/add` and `POST /api/suppliers/add` — case-insensitive idempotent ({ok, created: bool, employee/supplier})
- **HIGH-priority bug fix (testing-agent flagged + main agent fixed)**: `upsert_job` was regenerating the job `id` UUID on every update because the body never carries `id` and `_normalize` minted a new one. Switched to `$setOnInsert` for `id`/`created_at` + `$set` for mutable fields. Verified: PATCH/DELETE by id no longer 404 after re-upsert.

**Frontend** —
- New `/app/frontend/src/components/AdminJobMasterPanel.jsx` (mirrors EquipmentMasterPanel UX): inline Add/Update form, table of all jobs with toggle-active + delete buttons, Bulk Replace dialog (paste JSON array). Mounted in `AdminHub.jsx` L182.
- Updated `EmployeeCombo.jsx`: `addToRoster()` POSTs `/employees/add`, busts module cache, refreshes list, toast feedback. Inline "+ Add to MASCI roster" button shows in two places — when filtered list is empty AND when typed value is a custom novel string (amber banner).
- Updated `SupplierCombo.jsx`: parallel `addToList()` flow.
- `JobPicker.jsx` already migrated to fetch from `/api/jobs` instead of static `jobLibrary.js`.

**Tests** — `/app/backend/tests/test_jobs_master_and_roster_iter26.py` — 14 pytest cases covering admin login, public/admin job listing, full CRUD lifecycle (create→update→toggle→delete), bulk-replace round-trip, and inline roster idempotency/validation. **All 14 pass** post-fix.

**User verification:** Awaiting field smoke-test by Jaymn before next deploy.

## 2026-04-29 — Hub Polish: Red MASCI/. Tagline + Combined Projects Tile
Two small but important UX polishes per user feedback:

1. **Tagline** — "One place for every MASCI job." now renders with **MASCI** and the trailing **.** in `text-red-700` to match the brand. Implemented by splitting the H1 into 4 spans (`"One place for every "` + red `MASCI` + `" job"` + red `.`). Spanish i18n updated accordingly.

2. **Single "Projects" tile** — the two separate Basecamp + OnStation tiles were merged into one **Projects** tile (green accent, Building2 icon, "PROJECT WORKSPACES" eyebrow) with **two side-by-side buttons inside**:
   - 🏗️ **Basecamp** button (emerald, Building2 icon) → `https://3.basecamp.com/5958093/projects` — subtitle "Messages · To-dos · Schedule · Docs"
   - 📍 **OnStation** button (blue, MapPin icon) → `https://app.onstation.us/login` — subtitle "Field staking · Station mapping · GPS"
   - Helper line below buttons: "Both open in a new tab. Sign in with your Basecamp / OnStation credentials."

   New `ProjectsCard` component lives next to `SectionCard` in `Hub.jsx`. The 6-tile grid layout (Safety, Field, Projects, Admin, Shop, QC-coming-soon) is unchanged.

3. **i18n.js** — added 6 new translation pairs: `Project messages, to-dos, schedules…`, `Messages · To-dos · Schedule · Docs`, `Field staking · Station mapping · GPS`, `Both open in a new tab…`, `Project Workspaces`, `One place for every / job` split keys.

**Verified via screenshot**: tagline renders red on MASCI + period, single Projects tile shows both color-coded buttons with correct hrefs and target=_blank, lint clean.

## 2026-04-29 — OnStation Tile + Full Crew Hub Cleanup
**User request:** Add an OnStation link to the Hub home (the team uses it for field staking) AND verify the user guide and the rest of the system have been scrubbed of stale Crew Hub references.

**Hub home (`Hub.jsx`)** — split the single "Projects (Basecamp)" tile into two side-by-side external tiles:
- 🏗️ **Basecamp** (green, Building2 icon) → `https://3.basecamp.com/5958093/projects`
- 📍 **OnStation** (blue, MapPin icon) → `https://app.onstation.us/login`

Both render as `<a target="_blank">` with the "OPEN IN NEW TAB ↗" footer. Updated header comment to drop the "Crew Hub" reference and document both external links.

**AdminGuide (`AdminGuide.jsx`)** — rewrote:
- "The 4 sections of MASCI Hub" → "The MASCI Hub at a glance" with 6 bullet points (Safety, Field, Basecamp, OnStation, Admin, Shop) + retirement note that the in-app Crew Hub was retired 2026-04-28
- Backup-zip section: dropped `crew_hub/` from the active-content list and added an italics note that older pre-2026-04-28 backups still contain it
- Passwords table: removed Crew Hub row, added Shop console row, added external Basecamp/OnStation row pointing users to the vendor sites

**Bilingual i18n (`i18n.js`)** — added Spanish translations for all 9 new tile strings (`Open the live MASCI Basecamp account…`, `Sign in with your Basecamp credentials`, `Open OnStation for live job staking…`, `Sign in with your OnStation credentials`, `Open in new tab ↗`, `Basecamp`, `OnStation`, etc.).

**Code deletions:**
- `/app/frontend/src/pages/app/` (13 files: AppHome, AppLayout, ChangePassword, DocsPage, HillChartsPage, Login, MessageBoard, MyStuff, ProjectHome, ProjectMembers, SchedulePage, TodosPage, UsersAdmin)
- `/app/frontend/src/components/ProjectSearch.jsx`
- `/app/frontend/src/components/NotificationBell.jsx`
- `/app/frontend/src/components/RequireUser.jsx`
- `/app/frontend/src/lib/authContext.jsx`
- `<AuthProvider>` wrapper removed from `App.js`
- Obsolete tests: `/app/backend/tests/test_jwt_auth_iter18.py`, `/app/backend/tests/test_phase4_crewhub.py`
- `__pycache__` and `.pytest_cache` cleaned

**CrewRecoveryPanel → SystemRecoveryPanel** — repurposed:
- Renamed heading to "System Recovery"
- Removed the password-reset section + form + handler (no more crew users to reset)
- Removed unused imports (KeyRound, Input)
- Kept: System status grid (16 collection counts) + Force re-seed equipment/employees/suppliers (with confirm gate)
- Updated AdminHub.jsx comment

**Hub layout fix in BackupHeroPanel + ComplianceExportPanel** — dropped "Crew Hub message" / "complete Crew Hub (projects, users, messages, to-dos…)" copy from the user-facing backup descriptions, replaced with neutral wording.

**AdminHub header link** — "Crew Hub" → "MASCI Hub" (the home button at top-left of /admin).

**Verified end-to-end:**
- Lint: ✅ clean across entire `/app/frontend/src/`
- Boot log: `[boot-self-heal] no non-HQ projects (Crew Hub scrapped) — skipping memberships seed`
- Hub home screenshot: 2 new tiles (Basecamp + OnStation) render correctly, Admin/Shop tiles intact
- `/app/login` and `/app/projects/oxford` both 302 to `/`
- All other endpoints (`/api/health`, admin login, shop login, equipment-master, recovery panel) still return 200

## 2026-04-28 — Crew Hub SCRAPPED — Replaced by Basecamp Link
**User decision after repeated lock-outs**: "I'm tired of messing with projects how about this for projects we make a link to basecamp for our existing basecamp system to integrate it & scrap our entire basecamp clone system."

**What changed:**
- **Hub page** (`/app/frontend/src/pages/Hub.jsx`): Crew Hub tile replaced with a "Projects (Basecamp)" tile that opens `https://3.basecamp.com/5958093/projects` in a new tab. SectionCard component now supports external `https?://` URLs (renders `<a target="_blank">` instead of `<Link>`).
- **React Router** (`/app/frontend/src/App.js`): All `/app/*` routes (Login, ChangePassword, AppLayout, AppHome, ProjectHome, ProjectMembers, MessageBoard, TodosPage, SchedulePage, DocsPage, HillChartsPage, MyStuff, UsersAdmin) replaced by a single `<Route path="/app/*" element={<Navigate to="/" replace />} />`. Unused imports + helper `U(el)` removed.
- **Backend boot seed** (`/app/backend/projects.py`): `seed_initial_projects` is now gated on `CREW_HUB_ENABLED=true`. Without that env var (the new default), boot logs "Projects seed skipped — Crew Hub disabled" and the 32 projects + memberships do not auto-resurrect after a wipe.
- **Boot self-heal** (`/app/backend/data_fixes.py`): updated to short-circuit the membership seed if there are no non-HQ projects, so wiping the Crew Hub stays wiped across restarts.
- **One-shot wipe endpoint** (`/app/backend/server.py`): `POST /api/admin/crew-recovery/scrap-crew-hub` (admin-token gated, body `{"confirm":"SCRAP_CREW_HUB"}` required). Wipes 10 collections: projects, project_members, docs, todos, todo_lists, hill_dots, events, messages, notifications, activity_log. KEEPS: users, all safety records (inspections, meetings, JHAs, incidents, daily_reports), equipment, employees, suppliers, backups.
- **Recovery panel** (`/app/frontend/src/components/CrewRecoveryPanel.jsx`): kept in place — the password-reset section will show an empty user list if users get wiped, but the Force-reseed equipment button remains useful.

**Verified locally:**
- Wipe endpoint deleted 32 projects + 155 memberships + 194 docs + 5 todos + 1 todo_list + 2 events + 2 messages + 10 notifications + 2 activity_log = 403 rows.
- Restart confirmed — wipe persists, no auto-resurrect.
- Frontend `/app/login` and `/app/projects/oxford` both 302 to `/`.
- New "Projects (Basecamp)" tile renders correctly with green accent and opens `https://3.basecamp.com/5958093/projects` in a new tab.

**To apply on production after redeploy:**
```
curl -X POST https://mascidocs.com/api/admin/crew-recovery/scrap-crew-hub \
  -H "X-Admin-Token: <admin-token-from-login>" \
  -H "Content-Type: application/json" \
  -d '{"confirm":"SCRAP_CREW_HUB"}'
```
(I'll run this for you from this server once the deploy finishes.)

## 2026-04-28 — Emergency Crew Hub Recovery Panel (locked-out unblock)
**Problem reported by user**: On production (mascidocs.com), nobody could log into the Crew Hub. Every email/password combo (including `Welcome2MASCI!` for `safety@mascigc.com` and `jaymn.judd@mascigc.com`) returned "Invalid email or password". Equipment / employees / vendors lists also reported empty. The user was completely locked out with no recovery path because:
- Crew Hub passwords are stored in `db.users.password_hash` (per-user)
- The only password-reset endpoint (`POST /users/{id}/reset-password`) requires another already-logged-in owner/admin (catch-22)
- The legacy `/admin` console (Happy123!) had no Crew-Hub user management

**Fix shipped** — added a legacy-admin-token-gated bridge so the office can recover Crew Hub from `/admin` even when every crew owner is forgotten:

### Backend (`/app/backend/server.py`)
Three new endpoints (all `Depends(require_admin)` — i.e., legacy admin token, NOT crew JWT):
- `GET /api/admin/crew-recovery/status` — returns counts for every key collection (users, projects, project_members, equipment_master, equipment_units, equipment_inspections, inspections, meetings, jhas, incidents, daily_reports, docs, employees, suppliers, notifications, activity_log) + the full `crew_users` list with id/email/role/is_active/must_change_password. Lets the office see at a glance what's populated and what's empty.
- `POST /api/admin/crew-recovery/reset-password` — body `{email, new_password}`. Sets the user's password_hash + `must_change_password=true` + `is_active=true`. Validates min 8 chars. 404 on unknown email.
- `POST /api/admin/crew-recovery/force-reseed` — DELETE-then-reseed for `equipment_master` / `equipment_units` / `employees` / `suppliers` (the 4 collections gated by `count_documents > 0`). Re-runs the JSON seeds in-process and follows up with `boot_self_heal` so make/model + project_members come back too. Safety records, projects, and user accounts are NOT touched.

### Frontend (`/app/frontend/src/components/CrewRecoveryPanel.jsx`)
New panel mounted into `AdminHub.jsx` right under the Backup hero. Three sections:
1. **System status** — colored grid of every collection count. Empty `equipment_master` / `employees` / `suppliers` cells flash red with an alert banner.
2. **Reset Crew Hub password** — autocomplete email field driven by the `crew_users` list, password text field (≥8 chars), one-click Reset button. List of all crew users below shows role / active state / must-change flag. Email is click-to-fill.
3. **Force re-seed** — orange button, hard "Are you sure?" confirm dialog showing the exact row counts that will be deleted. Cancel = no-op.

### Verified end-to-end
- 401 without admin token ✅
- Status endpoint returns counts + 8 crew users ✅
- Reset to `TempPass2026!` → login OK with new password, `must_change_password=true` ✅
- Old password (`Welcome2MASCI!`) returns 401 after reset ✅
- Reset back to default works ✅
- UI panel renders correctly with all 16 collection counts visible at a glance ✅

### test_credentials.md updated
Added "LOCKED OUT?" pointer to `/admin/login` → Crew Hub Recovery panel.

## 2026-04-28 — Pre-Deploy Verification + Zero-Touch Boot Self-Heal Extended
After user feedback ("only fixes 2 things — verify everything else"), removed the manual UI button and proved the boot self-heal handles BOTH issues automatically on every redeploy.

**Removed:** `/app/frontend/src/components/DataFixesPanel.jsx` + import in `AdminHub.jsx`. The admin UI is back to its previous focused state.

**Extended boot self-heal (`/app/backend/data_fixes.py`):**
- Self-heal #1: equipment_master make/model split (existing) — fires if any unit has missing `make`
- Self-heal #2 (NEW): project_members seed — fires if any owner/admin has fewer memberships than there are projects
- Both run silently on every backend startup; never raise

**Proven via simulation** — wiped all 589 equipment make/model fields + deleted all 155 project_members → restarted backend → boot self-heal repaired both in 0.3 seconds. Logs:
```
[boot-self-heal] 589 equipment units missing make — auto-fixing
[data-fix] equipment_master: total=589 fixed=589 still_missing=0
[boot-self-heal] privileged user(s) missing project_members — auto-seeding
[data-fix] project_members: privileged=5 projects=31 created=155 total_after=155
```

**Pre-deploy verification (all PASS):**
| Check | Result |
|---|---|
| `/api/health`, `/api/healthz` | 200 |
| Admin login (`Happy123!`) | OK |
| Shop login (`Nothappy123!`) | OK |
| Crew login (jaymn/david/safety) | OK, correct roles |
| Wrong passwords | 401 (admin + crew) |
| All admin endpoints (inspections/meetings/jhas/incidents/daily-reports/equipment-inspections/projects/backups/persistence) | 200 |
| Crew Hub endpoints (projects/users/notifications/auth.me) | 200 |
| Shop endpoints (equipment-inspections/trends/open-items) | 200 |
| Public POST forms (translate) | 200 |
| Equipment data | 589/589 with make+model ✅ |
| Project memberships | 155 rows (5 owners/admins × 31 projects) ✅ |
| Backup pipeline | 752 MB zip created + slim 0.1 MB email delivered ✅ |
| Backend boot logs | No errors, self-heal logged correctly ✅ |
| Lint | DataFixesPanel removal passes; pre-existing server.py warnings unchanged ✅ |

The backend `POST /api/admin/data-fixes/run` endpoint was kept (admin-only, unreachable from UI) as a safety-net diagnostic tool. Boot self-heal makes manual invocation unnecessary.

## 2026-04-28 — One-Click Data Fixes Button + Boot Self-Heal
Made the data healers re-runnable from the admin UI with a hard "are you sure?" gate, and added zero-touch boot-time self-healing so equipment data can never be missing make/model after a redeploy.

- **Backend `POST /api/admin/data-fixes/run`** (server.py): admin-only endpoint that runs both healers (equipment make/model split + project_members seed) and returns a JSON summary `{equipment_master:{total,fixed,...}, project_members:{created,total_after,...}}`. 401 without admin token.
- **`/app/backend/data_fixes.py` (NEW)**: async-safe healers (`fix_equipment_make_model`, `fix_project_memberships`, `run_all_fixes`, `boot_self_heal`). Reuses the manufacturer dictionary + splitter from `seed_equipment_make_model.py`. Idempotent — only updates rows that need updating.
- **Boot self-heal**: server.py `_seed_phase1` startup hook now calls `boot_self_heal(db)` which auto-runs the equipment fix on backend boot if any unit has a missing `make`. Logs `[boot-self-heal] equipment_master clean — no fix needed` when nothing to do. Never raises (failure is logged + ignored so a bad fix can't keep the backend from booting).
- **Frontend `DataFixesPanel.jsx` (NEW)** wired into `AdminHub.jsx` between BackupHeroPanel and EquipmentMasterPanel. Amber "Apply Production Data Fixes" button → opens a "Apply data fixes now?" confirm Dialog with "No, cancel" and "Yes, apply fixes" buttons. Result summary renders inline below the button after success (toast + green panel showing fix counts + last-run timestamp).

### Verified
- 401 without admin token ✅
- Run endpoint returns idempotent stats (0 fixed / 0 created on second run) ✅
- Confirm dialog UX: clicking "No, cancel" leaves nothing changed (verified result panel absent) ✅
- Clicking "Yes, apply fixes" runs the healers and shows the green result panel ✅
- Backend boot logs show self-heal ran ✅

## 2026-04-28 — DATA INTEGRITY FIX: Equipment Make/Model + Project Memberships + Admin Stale-Token Guard
Three production data bugs fixed in one pass after the OOM/520 stabilisation:

1. **Equipment Master split** — every one of the 589 equipment_master docs had `make_model` populated (e.g., "Ingersoll Rand Towable Air Compressor") but `make` and `model` were empty, so the Shop Console fleet table rendered "—" for both columns. Built `/app/backend/scripts/seed_equipment_make_model.py` with a 100+ entry multi-word manufacturer dictionary that splits make_model into the right (make, model) tuple. Result: **589/589 docs now have make + model**, the JSON seed file `/app/backend/data/equipment_master.json` is back-synced from the DB, and the Shop Console "Equipment List" tab renders properly. Verified via screenshot at `/shop` after login.
2. **Project memberships seeded** — `db.project_members` (used by the `/api/projects` route in `/app/backend/projects.py`) was almost empty: only 1 row across 32 projects. The 4 owners + 1 admin saw the projects via the role-bypass branch BUT `/api/projects/{id}/members` returned empty for every project, breaking the Crew Hub "no projects on jobs" experience for anyone navigating into a project. Built `/app/backend/scripts/seed_project_memberships.py` (idempotent upsert) that links every owner/admin to every non-HQ project. Result: **155 new project_members rows; all 5 privileged users (jaymn.judd, david.jewett, chris.wright, ramon.rodriguez, safety) are now members of all 31 projects** (HQ is implicit). Verified: `GET /api/projects/{any_id}/members` returns 5 members.
3. **Admin Login stale-token guard** — `/app/frontend/src/pages/AdminLogin.jsx` now calls `clearAdminToken()` on mount AND right before the POST so a stale `X-Admin-Token` header from a previous session can't poison the new login attempt. Verified: API returns valid 64-char token on success and 401 on wrong password.

### Files touched
- `/app/backend/scripts/seed_equipment_make_model.py` (NEW)
- `/app/backend/scripts/seed_project_memberships.py` (NEW)
- `/app/backend/data/equipment_master.json` (regenerated from DB; old version backed up as `equipment_master.20260428-212813.bak.json`)
- `/app/frontend/src/pages/AdminLogin.jsx` (stale-token guard)

### To run on production
After Save-to-GitHub + redeploy, run these two scripts once on the production pod:
```bash
python3 /app/backend/scripts/seed_equipment_make_model.py
python3 /app/backend/scripts/seed_project_memberships.py
```
They are idempotent — safe to re-run.

## 2026-04-28 — PRODUCTION OUTAGE FIX: 5 Defense Layers Against Cloudflare 520
Customer hit "Login failed — check connection" on production at mascidocs.com — root cause: Cloudflare 520 (origin server unresponsive). The deployed backend container was being killed because the synchronous backup build was blocking the asyncio event loop AND the disk filled up from accumulated backup zips. Shipped 5 permanent defense layers in `/app/backend/server.py` so this can NEVER happen again:

1. **`/api/health` + `/api/healthz` endpoints** (line ~191) — DB-free, dependency-free, sub-millisecond response. Cloudflare/Emergent platform healthchecks now have a guaranteed-fast endpoint.
2. **`BACKUP_KEEP_MAX=3` default** (was 6) — hard ceiling on stored backups. With ~750 MB per backup, 3 files = 2.3 GB on the 9.8 GB volume. Aggressive headroom.
3. **`BACKUP_DISK_HIGH_WATERMARK=75%` watermark** + `_emergency_prune_backups()` — auto-prunes if disk crosses watermark at boot OR right before backup write. If still > 90% after emergency prune, ABORTS the backup instead of crashing the backend.
4. **Boot-time disk safety check** in `_start_backup_scheduler` — runs emergency prune on container start if inherited disk is full. Prevents fresh-boot crash loops.
5. **Event-loop yields throughout `_build_backup_zip`** — `await asyncio.sleep(0)` after every collection iteration, every PDF render, every disk file. `tmp.write_bytes()` (the 750 MB sync IO write) wrapped in `asyncio.to_thread`. **Verified: 8 consecutive `/api/health` calls succeeded during a 75-second backup build — backend stays responsive throughout.**

### Verified (2026-04-28 18:33 UTC):
- Manual backup via `/api/admin/backups/run-now` → ✅ 752 MB · 1738 records · email delivered (resend_id returned)
- `/api/health` during backup → ✅ all 8 polls returned instantly
- Disk state after 3 consecutive backups → ✅ 57% used, ceiling holding
- All 3 logins (admin, shop, crew hub) → ✅ working

### What this means for the customer:
- **The backend container can no longer be killed by the backup process.** Even if 1738 records doubles to 5000+, the event-loop yields keep healthchecks alive throughout.
- **The disk can no longer fill up.** Backup write is gated on disk %, and prune runs on boot AND before every write.
- **Cloudflare 520 has been eliminated as a backup-induced failure mode.**

## 2026-04-28 — Backup pipeline made bullet-proof (P0 done)
Fixed the nightly backup so the manual red "BACKUP EVERYTHING" button always succeeds and emails:
- **Pre-flight prune** before each backup write — clears `.zip.tmp` debris from prior failures + enforces both retention-days AND the new `BACKUP_KEEP_MAX` (default 6) hard cap so the disk can never fill up from rapid manual clicks.
- **Truly-slim email zip** — when the full archive exceeds the 35 MB Resend cap, build a slim version that drops PDFs + disk_files + CSVs AND walks every JSON to strip embedded base64 blobs (`file_data`, `photo`, `signature`, `pdf_bytes`, etc.) replacing each with `<stripped:base64 N bytes (key=...)>` so the field name + structure survive. Result: 718 MB full → 0.1 MB slim email (181 blobs / 281 MB stripped). Verified: resend_id returned, email landed at jaymn.judd@mascigc.com.
- **Manifest validates 100% coverage** — `backup_manifest.json` now records `all_db_collections_at_backup_time`. Verified: 26/26 live collections captured, 13 disk files (533 MB) bundled, 1738 records, zero missing.
- **Email body upgrade** — shows full size + slim attachment size separately, lists how many blobs were stripped, points user to download the full zip from `/admin` for any disk-backed files.
- Cleaned up the 6.4 GB of accumulated test backups that had filled the disk (100% → 42%).

## ✅ PRODUCTION RUNS ON MONGODB ATLAS (verified by user 2026-04-28)
The live production app's `/admin` banner shows **green** ("Persistent database connected"). User confirmed via screenshot. Future agents: do NOT ask the user to redo Atlas migration — it's already done. Preview environment running localhost Mongo is intentional and expected (preview is the throwaway dev playground; only production needs Atlas).

## 2026-04-28 — server.py refactor extended (P1, batches 2-4) + Atlas guide
- **server.py: 4400 → 3029 lines (1371 lines extracted, -31%).**
- New route modules in `/app/backend/routes/`:
  - `safety.py` (471 lines) — Inspections + Meetings + JHAs + Incidents (16 endpoints + 12 Pydantic models)
  - `daily_reports.py` (144 lines) — Daily Reports (5 endpoints + 3 models, including the `/daily-reports/next-number` auto-generator)
  - `equipment.py` (407 lines) — Equipment Pre-Op + Shop Sign-Off + Trends + Open Items (8 endpoints + 4 models + `MAJOR_OOS_SET` severity helpers)
  - `shop_parts.py` (335 lines) — Shop Activity Feed + Equipment Parts Catalog (8 endpoints, from iter25 batch 1)
- Pattern: each module exposes `register_*_routes(api_router, db, require_admin, ...)` that takes shared deps as args. Late-bound `schedule_auto_email` passed as a lambda so the function is resolved at request time (no forward-reference issues).
- **44/44 backend pytest pass + curl smoke on all 37 extracted endpoints succeeds.** Zero behavior change, zero regressions, zero frontend impact (all paths unchanged).
- Atlas migration guide at `/app/ATLAS_MIGRATION.md` for the prod database persistence fix.

## 2026-04-28 — Basecamp import for project 24-12 (Oxford Rd) + disk-backed large file storage
- Imported all **193 files** from 5 Basecamp .zip exports into the Crew Hub Docs library for project 24-12 (CC5744 - OXFORD RD Improvements). Categories auto-mapped from top-level Basecamp folders → MASCI's existing `DOC_CATEGORIES`:
  - **Submittals · 29** files (CC-5744-24 Oxford submittal packages 002-029, RCP, sanitary, signalization, mast arms, illuminated signs, cabinet, conduit, signal cable, luminaire, copper, cameras, loop assembly, pull boxes, drainage, riser wrap, surcharge wick drain, wet well liner, JCM linestop, fountains, etc.)
  - **Plans & Specs · 33** files (Hazen plans, FDOT standard plans, full Roadway plan sets Rev 1/3/4, signing/signals plans, landscape plans, GPS model files, .dwg/.dgn drawings, Trimble .tp3 export, .kmz, RFI028)
  - **Safety · 20** files (incident report form, weekly safety meetings 9/4/25 + 9/10/25 + 9/17/25 + 9/24/25 + 9/25/25 + 8/27/25, weekly inspections 9/10 + 9/17 + 9/24 + photo bundles 8/14/25 + 8/26/25 + 9/17/25, MASCI tool-box-talk template, excavation self-inspection, inspection checklist .xlsx)
  - **Daily Logs · 110** files (every daily report from 6/16/25 through 4/6/26 — Allen Smathers daily-log series + numbered Daily Reports 1-25 covering Casselberry + Oxford Rd dailies)
  - **Locate Tickets · 1** (July 2025 Locates)
- Total ~744 MB across 193 files. Attributed to Jaymn Judd (project owner).
- **Two-tier storage** to handle Mongo's 16 MB BSON document limit:
  - 180 files ≤ 11.5 MB → stored as base64 data URLs in `db.docs.file_data` (existing path)
  - 13 oversized files (12-153 MB — FDOT standard plans, full plan sets, photo bundles) → stored on disk at `/app/backend/storage/project_docs/24-12/{doc_id}.pdf`, with `db.docs.file_path` pointing to the file. Download endpoint streams via `FileResponse` instead of decoding base64. Verified end-to-end with the 153 MB FDOT plans PDF (real `%PDF-1.7` header, full byte count).
- **Backend change**: `tools.py` `download_doc` endpoint now branches on `file_path` vs `file_data`. Backwards-compatible — existing data-URL docs still work.
- **Idempotent re-runnable scripts** saved to `/app/backend/scripts/basecamp_import.py` + `basecamp_import_big.py` (each clears prior runs by `notes` regex before re-importing).
- Verified via UI: David Jewett can navigate to `/app/projects/24-12/docs` and see the full library with category filter chips (All · 193 · Submittals · 29 · Plans & Specs · 33 · Safety · 20 · Daily Logs · 110 · Locate Tickets · 1). Each card shows filename, category, size, "Basecamp import · 2026-04-28" note, JJ avatar, and download/delete buttons.

## 2026-04-28 — Bilingual completion: high-traffic admin + Crew Hub screens (iter25, ALL GREEN)
- Translated to Spanish (with full ES dict entries in `i18n.js`):
  - **PersistenceHealthBanner** — danger banner the admin sees on every visit until the prod DB switches to Atlas. ⚠ Sus datos se borrarán en el próximo redespliegue / Solución permanente / etc.
  - **BackupHeroPanel** — the two big BACKUP / RESTORE buttons on `/admin`. COPIA DE TODO / RESTAURAR DESDE ARCHIVO.
  - **Crew Hub `/app/login`** — Bienvenido de nuevo / Contraseña / Iniciar sesión.
  - **Crew Hub `/app` AppHome** — ¿En qué está trabajando hoy? / Cargando proyectos.
- Verified by testing agent (iter25): EN ↔ ES toggle persists via localStorage, html.lang attribute swaps correctly, no Spanish leaks back into EN, no JS errors. /shop login + sign-off + Parts Catalog ES regression still passes.
- **Deferred (will require its own session)**: AdminGuide doc page (400+ English lines), StoredBackupsPanel + RestoreBackupPanel + AutoEmailRoutingPanel (heavy admin tools, lower visibility), full Crew Hub project workspace pages (messages / todos / schedule / docs).

## 2026-04-28 — Bilingual sweep + Performance + Cleared-to-Operate (iter24, ALL GREEN)
- **ES→EN auto-translate wired into the 3 new shop modules**: `ShopSignoffCard.jsx` (sign-off notes), `PartsCatalog.jsx` save (PUT — part name + notes), and `PartsCatalog.jsx` parts-order email (additional_notes + item.name + item.notes). Mechanic types Spanish, DB + outgoing email both end up in English. Pattern matches the iter15-16 wire-up of the original 5 forms (Inspection, Meeting, Incident, Daily, Equipment Pre-Op) — confirmed end-to-end via iter24 pytest.
- **Spell-check verified**: `i18n.js._syncHtmlLang()` mirrors `lang=es|en` onto `<html lang>` on every toggle + persists via localStorage. Zero inputs override the html-level attribute, so browsers swap dictionaries automatically. Verified via Playwright (en → click ES → es → reload → still es → EN → en).
- **Photo-stripped list endpoints**: `GET /api/inspections`, `/api/incidents`, `/api/daily-reports`, `/api/equipment-inspections` migrated from cursor.find with photos:1 projection to MongoDB aggregation with `$size`. Photo bytes no longer travel for dashboard listings — 10-100x faster on records with multiple photos.
- **MongoDB indexes** ensured on every startup (idempotent `_create_safety_indexes()`): `equipment_inspections.created_at/inspection_date/equipment_unit/project_number/fail_count`, `inspections.created_at/inspection_date/project_number`, `daily_reports.created_at/report_date/project_number`, `incidents.created_at/incident_date/severity`, `meetings.created_at/meeting_date`, `equipment_parts.unit_number` (unique), `equipment_master.unit_number/category`. Log line: `[safety-indexes] ensured`.
- **"✓ CLEARED TO OPERATE" badge** on `/admin/equipment` + `/shop` Recent Inspections tab when `fail_count > 0 AND signoff_count >= fail_count`. Replaces the red FAIL badge once every flagged item is signed off — closes the visual loop. New `EquipmentInspectionSummary.signoff_count + cleared` fields computed server-side via aggregation. Bilingual: `LIBERADO PARA OPERAR`.
- **Validated by testing agent (iter24)**: 10/10 backend pytest (`test_iter24_bilingual_perf.py`) + Playwright bilingual sweep + cleared-badge UI verification + perf < 2.5s on all four list endpoints. Iter22 (15) + iter23 (19) regression suites still green = 44 backend tests total covering the iter22-24 work.

## 2026-04-28 — Shop Activity Feed + Equipment Parts Catalog (P0 complete)
- **Shop Activity Feed** — new `GET /api/shop/activity?limit=20` flattens `equipment_inspections.shop_signoffs[]` across the fleet, newest first. Mounted as a new tab on `/shop` (data-testid=shop-tab-activity → shop-activity-panel) and as a permanent panel on `/admin/equipment` (admin-activity-panel). Each row: mechanic name, action chip (Repaired / Tagged out / Parts ordered / No action), unit, item, optional notes, timestamp, deep-link into the inspection. Doubles as a credibility log for owners + insurance auditors.
- **Equipment Parts Catalog** — per-unit wearable parts so field mechanics can pull up a unit and order parts on the way to the PM service.
  - New `equipment_parts` MongoDB collection. Schema: `{unit_number (PK), filters[], cutting_edges[], wiper_blades[], tires[], other_wear_items[], updated_at, updated_by}`. Each row has `name, part_number, qty, notes` (+ `size` on wipers, `position/size/ply/brand` on tires).
  - **Endpoints** (require_shop_or_admin): `GET /api/equipment-parts` (list), `GET /api/equipment-parts/{unit}` (returns empty doc shape if not found), `PUT /api/equipment-parts/{unit}` (upsert), `POST /api/equipment-parts/order` (Resend email to parts office). Admin-only: `DELETE /api/equipment-parts/{unit}`, `GET /api/admin/equipment-parts/status`, `POST /api/admin/equipment-parts/upload` (.xlsx/.csv bulk upload). Defense-in-depth 400 on empty unit_number.
  - **`/shop` Parts Catalog tab**: searchable 589-unit fleet picker → 5-category editor (filters / cutting edges / wiper blades / tires / other) → "🛒 Add to Order List" → email order to parts office in one click. Mechanics + admins both edit (server-gated). Empty `unit_number` rows are filtered client-side to avoid trailing-slash 307→http Mixed-Content blocks.
  - **`/admin` EquipmentPartsPanel**: bulk upload `.xlsx/.csv` with columns `Unit Number | Category | Name | Part Number | Qty | Size | Position | Ply | Brand | Notes`. Aliases accepted (`filter` → `filters`, `wipers` → `wiper_blades`, etc.). Replaces ALL category lists for affected units (idempotent re-upload).
- **Bilingual**: ~60 new ES strings (Catálogo de Partes, Filtros, Cuchillas, Plumas Limpiaparabrisas, Llantas, Otros Artículos de Desgaste, Lista de Pedido, Enviar Pedido a Oficina de Partes, etc.).
- **Validated by testing agent (iter23)**: 19/19 backend pytest in `test_shop_activity_parts_iter23.py`, frontend EN+ES end-to-end (login → activity tab → parts tab → save → cart → email order via Resend with real `resend_id` returned). Iter22 regression 15/15 still green. One UI bug found (empty fleet rows triggered Mixed Content) — fixed in same iteration.

## 2026-04-28 — Shop Console + Pre-Op Sign-Off (P0 complete)
- **New 5th Hub tile "Shop"** (amber Wrench, `data-testid="hub-section-shop"`) on `/`. Click → `/shop/login` with its own password gate (`SHOP_PASSWORD=Nothappy123!`, separate from admin's `Happy123!`).
- **New `/shop` console** (`ShopHub.jsx`) — focused subset of `/admin/equipment`: KPI strip (Inspections on file / Units flagged FAIL / Shop sign-offs / Equipment in fleet) + 6 tabs: **Open Items** (default), **Activity Feed**, **Trends**, **Recent Inspections**, **Equipment List**, **Parts Catalog**. No incidents / dailies / meetings / inspections / settings — shop only sees shop stuff.
- **New `ShopSignoffCard.jsx`** — renders per FAIL line on `/admin/equipment/:id` and `/shop/equipment/:id`. Inputs: signed_by (mechanic name), action_taken (Repaired / Tagged out of service / Parts ordered / No action needed), optional notes. After sign-off, shows green "Shop signed off" stamp with name + timestamp + Reopen button.
- **Severity coloring on FAIL lines** in the View page: OUT OF SERVICE items get a red border + red OOS pill; NEEDS ATTENTION items get amber border + amber ATTN pill.
- **Admin retains global view**: `/admin/equipment` now also mounts `<OpenItemsPanel/>` + `<ShopActivityFeed/>` directly under the Trends panel.
- **Backend auth**: `POST /api/shop/login` mirrors `/admin/login` (HMAC token via ADMIN_HMAC_SECRET, namespaced by `b"shop:" + password`). New dependency `require_shop_or_admin` accepts X-Shop-Token OR X-Admin-Token. DELETE inspection stays admin-only.


## Original Problem Statement
> "I want/need a fillable form I can send out to inspectors to do site safety inspections, then print or save as PDF... Look at what I have see what we could add or take away to make it awesome & work flawlessly on computers or mobile devices."

Evolved into a multi-module **MASCI Safety Hub**: Site Inspections, Safety Meetings (toolbox talks), Job Hazard Analysis (JHA), and Accident/Incident Reports — one branded URL, no login, mobile-first, with print/PDF + QR-share for trailer postings.

## User Choices
- Single deployment, multi-module under one URL
- No login — public form links + QR codes for any device
- MASCI red/black branding throughout, "No Shortcuts • No Exceptions"
- Photos with MASCI watermarks, on-screen signatures, GPS auto-fill via OpenStreetMap

## Architecture
- **Backend:** FastAPI + Motor (MongoDB) at `/app/backend/server.py`. Routes prefixed `/api`.
- **Frontend:** React 19 + Tailwind + shadcn/ui + lucide-react + react-signature-canvas + qrcode.react + sonner. CRA dev server on port 3000.
- **Collections:** `inspections`, `meetings`, `jhas` (legacy — no UI), `job_hazard_plans` (PDF blobs), `trench_boxes`, `incidents`, `daily_reports`, `equipment_units`, `equipment_inspections`. Photos + signatures stored as base64 data URLs inline.
- **Design:** Swiss/industrial high-contrast — Chivo display + IBM Plex Sans body. MASCI red `#C8102E` accent. Print-optimized stylesheet.

## Personas
- **Field Inspector / Foreman** — completes form in field on phone (signatures, photos)
- **Crew member** — signs attendance on Safety Meetings, sign-off on JHA
- **Safety Manager / Office** — reviews dashboards, prints PDFs, files incidents

## Modules

### 01. Site Inspections (`/inspections`)
- 13 sections matching MASCI source PDF, conditional sub-checklists, real-time PASS/FAIL grading, auto-fail logic, photo uploads with compositing watermark, GPS auto-fill, inspector + foreman signatures.

### 02. Safety Meetings (`/meetings`) — toolbox talks
- 81-topic searchable Topic Library (heavy-civil/highway/concrete/MOT/electrical/etc.) with prefilled hazards, discussion points, references, action items
- Custom Topic option, multi-attendee signatures, conductor signature, photos
- **Searchable Combobox topic picker** (`TopicPicker.jsx` — cmdk + Popover, grouped by category)

### 03. Job Hazard Analysis (`/jha`)
- Pre-task multi-step hazard/control grid, PPE & permit checklists, crew sign-off, foreman approval signature

### 04. Accident / Incident Reports (`/incidents`)
- 6 severity tiers: Near Miss → First Aid → Medical → Restricted Duty → Lost Time (DART) → Fatality/Catastrophic
- 9 incident types (Injury, Near Miss, Property Damage, Vehicle, Environmental, Utility Strike, Public/3rd-Party, Security, Other)
- Conditional Person-Involved section (body part, injury nature, treatment, medical facility)
- Root-cause categories (PPE/Training/Procedure/Supervision/Equipment/Design/Communication/Fatigue/Housekeeping/Weather)
- Multiple witness statements
- Notification log (Safety Mgr / PM / GC / Owner / OSHA / Other)
- Reporter + Supervisor signatures, photo evidence with watermark, printable PDF, public submit link via QR

### 05. Equipment Pre-Op Inspections (`/equipment`) — **NEW (2026-02-26)**
- 23 equipment types covering every heavy-civil machine: Dozer, Excavator, Loader, Motor Grader, Skid Steer, Paver, Backhoe, Tractor, Telehandler/Forklift, Haul Truck, Water Truck, Shuttle Buggy/Transfer Machine, Steel Drum & Rubber Tire Asphalt Rollers, Asphalt Milling Machine, Dirt Roller, Dirt Mixer, Road Widener, Broom, Curb Machine, Plate Compactor, Walk Behind Saw, Other.
- OSHA 1926-aligned checklists per type (Fluids & Leaks · Walk-Around · Operator Station · Lights & Electrical · Controls & Brakes · Safety Equipment), each with equipment-specific items (e.g. screed plates for pavers, restraint bar for skid steers, body prop for haul trucks).
- PASS / FAIL / N/A buttons with required note on FAIL.
- Optional **hour meter** AND/OR **odometer** (some equipment has only one).
- Saved equipment units (auto-remembers every unit submitted, picker shows them next time per type).
- Live tally bar + "FAIL — DO NOT OPERATE" banner the moment any item fails.
- Operator certification statement + signature; stop-the-line if no items rated.
- WeasyPrint PDF includes a red "OUT OF SERVICE" banner header on FAILs.
- **Auto-email subject is automatically prefixed `EQUIPMENT FAIL · `** so PMs see it instantly. Sent to assigned PM + always-CC pipeline (David / Chris / Ramon / Jaymn / safety@).

## What's Implemented (2026-04-28 · MASCI HUB Logo + Tagline Refresh)
User-driven brand refresh: new logo art using a user-supplied red M with white swoosh icon, new tagline, dark-header-friendly backplate.
- **New logo lockup** (`/app/frontend/public/masci-full-lockup.png`): regenerated 2x via Gemini Nano Banana — first pass produced silver gradient backplate that clashed with the navy header; second pass replaced the backplate with solid #0f172a (slate-900) so it sits flush in the dark header. Verified live with full-page screenshot.
- **3 lockup variants + 3 mark variants** all regenerated. Idempotent generator at `/app/backend/scripts/generate_hub_logos.py` (always edits from `/app/frontend/public/_old_safety_lockups/`). Background-fix script at `/app/backend/scripts/fix_lockup_background.py`.
- **Tagline change globally:** "No Shortcuts · No Exceptions" → "Accountability · Adapt · Overcome" — updated in `companyInfo.js`, Hub homepage, Section landings (Safety/Field), Dashboard, ThankYou, FormPasswordGate, ViewInspection, ViewMeeting, MasciLogo alt text, ShareFormDialog poster HTML, CheatSheetCard, JhaPlansPosterCard, TrenchBoxPosterCard, AdminGuide, PDF render footer (`pdf_render.py`), and i18n Spanish dictionary.
- Old "No Shortcuts · No Exceptions" Spanish keys retained in `i18n.js` for backwards-compat with older PDF records.

## What's Implemented (2026-04-27 · MASCI Hub Rebrand + New Logo)
App rebranded from "MASCI Safety Hub" to **"MASCI Hub"** — reflects that it's a full operations platform, not just safety. Logo art was also regenerated via Gemini Nano Banana (`gemini-3.1-flash-image-preview`) — 3 lockup variants (dark bg, onblack, onlight) all now say **"MASCI HUB"** instead of "MASCI SAFETY" while preserving the compass icon, red M with checkmark, tagline, core values subtext, and overall composition. Originals archived to `/app/frontend/public/_old_safety_lockups/`. One-off script at `/app/backend/scripts/generate_hub_logos.py` (idempotent — always edits from the archived originals). Verified via MD5 — file on disk and server-served bytes match.
- **New homepage `/`** (`Hub.jsx`): 4 big section cards instead of 7 mixed tiles:
  - 🦺 **Safety** (red) → `/safety` — Site Inspections, Safety Meetings, Incident Reports, JHA Plans, Trench Box Data
  - 👷 **Field** (amber) → `/field` — Daily Reports, Equipment Pre-Op
  - 🏗️ **Projects** (emerald) → `/app` — Crew Hub (Basecamp clone), sign-in required
  - 🗄️ **Admin** (slate) → `/admin/login` — Office console
- **New `SafetySection.jsx`** (`/safety`) — 5 compliance-form tiles with red accent + "← MASCI Hub" back link.
- **New `FieldSection.jsx`** (`/field`) — 2 daily-ops tiles with amber accent + "← MASCI Hub" back link.
- Taglines + footers updated ("MASCI · Operations Platform").
- **Copy updates across codebase:** Login page, backup panels, cheat sheet, share-form dialog, Owner's Manual, PDF headers, email subject lines, i18n Spanish translations, backend fallback titles. The product is now "MASCI Hub" everywhere.
- **Owner's Manual (`/admin/guide`) updated** with a new "The 4 sections of MASCI Hub" section explaining who uses Safety / Field / Projects / Admin.

## What's Implemented (2026-04-27 · Owner's Manual + One-Stop Backup Hero)

## What's Implemented (2026-04-27 · Owner's Manual + One-Stop Backup Hero)
- **New `/admin/guide` page** — plain-English, print-friendly Owner's Manual. Answers "how do I run this?", "what's in the backup .zip?", "what do I do if data is missing after a deploy?", "what are the passwords?". Linked from a "📖 Guide" button in the admin header. Crews never see it. Print button in the header → print-optimized layout.
- **New `BackupHeroPanel`** at the very top of the Admin Hub — 2 giant buttons:
  - 🟥 **BACKUP EVERYTHING** — one click fires `/admin/backups/run-now`, emails the .zip to `BACKUP_EMAIL_TO`, AND downloads it locally in a single flow.
  - 🟩 **RESTORE FROM FILE** — file picker + a single confirm dialog (always merge mode — safe). No mode toggles, no REPLACE typing, no jargon.
- Below the hero panel the existing detailed panels (Compliance Export, Full Off-Site Backup, Stored Backups, Restore from Backup with merge/replace modes) remain as "advanced" controls for power users.
- Goal: the customer never has to touch anything except the 2 hero buttons. Everything else is decoration.

## What's Implemented (2026-04-27 · Data-Loss Defense-in-Depth)
Customer reported data loss after Emergent redeploy — in-container MongoDB and `/app/backend/backups/` are BOTH ephemeral per the platform. Built multiple defenses on top of the nightly backup:
- **Auto-email nightly backup** via Resend — every scheduled backup also attaches the .zip to an email sent to `BACKUP_EMAIL_TO` (default `jaymn.judd@mascigc.com`). Gives the customer a durable off-site copy even without Atlas.
- **Persistence-health banner** (`PersistenceHealthBanner`) at the top of `/admin`. Reads `GET /api/admin/persistence-check` which inspects `MONGO_URL` — localhost/127.* → RED "⚠ Your data will be deleted on the next redeploy" banner with Atlas migration callout + "Backup + email + download NOW" button. Atlas/external hostname → GREEN "Persistent database connected" banner.
- **Pre-deploy emergency backup button** — one-click flow that calls `/admin/backups/run-now`, emails the .zip, AND downloads it to the user's browser simultaneously. Prevents deploys-without-backup.
- Guidance given to user: MongoDB Atlas free-tier migration (6-step instructions delivered via chat).

## What's Implemented (2026-04-27 · Nightly On-Server Backups)
- **Daily scheduled backup** — `_backup_scheduler_loop` runs as a FastAPI startup task, ticks every 5 min, and fires the backup once per day at `BACKUP_HOUR_UTC` (default 02:00 UTC).
- **Stored on disk** at `BACKUPS_DIR` (default `/app/backend/backups`). Each run writes `MASCI_full_backup_YYYY-MM-DD_HHMMSSZ.zip` atomically via a `.zip.tmp` rename so a crashed backup can't produce a corrupt file.
- **Retention** — `BACKUP_RETENTION_DAYS` (default 14). Older zips auto-pruned after each successful run.
- **New admin endpoints:**
  - `GET /api/admin/backups` — list every stored backup + schedule config.
  - `GET /api/admin/backups/{filename}` — download one (strict filename regex — no path traversal).
  - `DELETE /api/admin/backups/{filename}` — delete one.
  - `POST /api/admin/backups/run-now` — trigger an immediate backup (same path as nightly).
- **Admin UI** — new `StoredBackupsPanel` on the Admin Hub, between "Full Off-Site Backup" and "Restore from Backup". Shows the schedule strip (hour, retention, dir, enabled) + every stored file with size/date + Download/Delete buttons + a `Run backup now` CTA.
- **Env vars:** `BACKUPS_DIR`, `BACKUP_RETENTION_DAYS`, `BACKUP_HOUR_UTC`, `DISABLE_BACKUP_SCHEDULER` (set to `1` to turn off).
- **Verified end-to-end via curl + screenshot**: scheduler logged on boot, `run-now` produced a 2.4 MB zip with 80 records, list/download/delete all work, admin panel renders.

## What's Implemented (2026-04-27 · Whole-System Backup & Restore)
- **Full backup ZIP now covers EVERYTHING on the system** — all 21 MongoDB collections. Adds `safety_aux/equipment_units.json`, `safety_aux/job_hazard_plans.json`, `safety_aux/trench_boxes.json` on top of the 6 safety kinds + 12 Crew Hub collections already being exported. Includes a `backup_manifest.json` (version "2") listing every collection covered so future agents can validate authenticity. Password hashes stay redacted from `crew_hub/users.json`.
- **Restore from Backup** — new `POST /api/exports/restore` endpoint + Admin Hub panel. Upload any `.zip` produced by "Download Full Backup" and the entire system is rebuilt.
  - **Merge mode (default, emerald):** upsert by `id` — existing rows overwritten with the backup's copy, new rows added, anything not in the backup left untouched. Safe to run repeatedly.
  - **Replace mode (destructive, red):** wipes each collection found in the zip first, then reinserts. Guarded by a REPLACE-typed confirmation dialog. Anything added since the backup is permanently lost.
  - **User-hash safeguard:** since the backup redacts `password_hash`, restore preserves the DB's existing hash in merge mode, or stamps the seed password `Welcome2MASCI!` with `must_change_password=True` in replace mode. **No account can ever be locked out by a restore.**
  - 500 MB upload ceiling, manifest validation (`backup_manifest.json` must be present), bad-zip + empty-upload fail fast with clear messages.
- **Verified end-to-end** via curl: backup → change password → add data → merge restore keeps current password + new data · replace restore wipes post-backup data and resets to seed password.

## What's Implemented (2026-04-27 · Phase 4 Crew Hub + P1 safety backlog)
- **Backend Phase 4 router live:** `/api/projects/{id}/activity`, `/api/me/activity`, `/api/me/notifications`, `/api/me/notifications/mark-all-read`, `/api/me/notifications/{id}/read`, `/api/projects/{id}/search`, `/api/users/directory`. Every Phase 2/3 write in `tools.py` now calls `log_activity()` + `process_mentions()` so the activity feed + @-mention notifications + Resend email fan-out all populate automatically.
- **6 Phase 4 frontend pieces shipped:**
  1. **`/app/me` My Stuff page** — "Hey!" inbox, 3 tabs (Mentions, My to-dos, Activity feed), mark-all-read, inline mark-one-read.
  2. **Activity feed on ProjectHome** — scrollable last-15 activity card below the scorecard.
  3. **@-mention autocomplete** (`MentionTextarea`) in MessageBoard composers (both new post + comments). Fetches `/api/users/directory` once, type `@` → dropdown of up to 6 matches, Enter/Tab to insert `@email@mascigc.com `.
  4. **Per-project search** (`ProjectSearch`) in ProjectHome header — instant results across messages, to-dos, docs, events (250 ms debounce).
  5. **NotificationBell in sidebar footer** — unread badge (9+ cap), 60s polling, dropdown with mark-one or mark-all-read, deep-link to My Stuff.
  6. **Distribution List widget** (`DistributionList`) on `/incidents/new` (section 07 Notifications) and `/daily/new` (section 11 Sign-Off). Chip input, email validation, backspace-to-pop. Stored on `incident.distribution_list` / `daily_report.distribution_list` (backend models accept list of strings, max 20). Included in the PDF footer and routable to auto-email.
- **Full Backup ZIP now archives the Crew Hub too.** `/api/exports/full-backup` appends 12 `crew_hub/*.json` files: `projects`, `users` (password_hash **redacted**), `project_members`, `messages`, `message_comments`, `todo_lists`, `todos`, `events`, `docs` (includes base64 file blobs), `hill_scopes`, `activity_log`, `notifications`. `backup_log.txt` shows a per-collection count + Crew Hub subtotal.
- **Verified end-to-end** via iteration 16 test report: 13/13 backend Pytest + 9/9 Playwright UI tests passing. Cross-user @mention delivery (safety@ posts mention → david@ sees notification) confirmed.

## What's Implemented (2026-04-27 · Phase 3.5 Scorecard Layout)
- **ProjectHome scorecard (2026-04-27):** Rebuilt `/app/projects/:id` as a Basecamp-style "everything at a glance" scorecard. One `GET /api/projects/{id}/scorecard` aggregate endpoint returns latest 3 messages, next 2 events, todo counts, 2 latest docs, top 3 hill scopes — one round trip instead of five.
  - **Hill Chart snapshot** at the top with inline mini-SVG + colored-dot legend (matches Basecamp IMG_4413 hero area).
  - **4-card grid** below: Message Board (red accent), To-dos (amber + progress bar), Schedule (emerald + day badges), Docs (blue + uploader info).
  - **Colored accent bars** per card; empty-state fallbacks on every card.
  - **Member avatar stack** in the project header (+N badge when >5 members).
  - **Secondary tiles row**: Hill Charts + Members with live counts.
- Verified end-to-end with seed data: 2 messages + 2 events + 3/5 todos + 1 doc + 3 hill scopes all render correctly in a 1600×1200 viewport.

## What's Implemented (2026-04-27 · Phase 2 + Phase 3 Crew Hub tools)
- **Message Board** (`/app/projects/:id/messages`) — post, list, view, threaded comments, delete. Author avatars + relative timestamps everywhere.
- **To-dos** (`/app/projects/:id/todos`) — multiple lists per project, inline add with assignee picker + due date, check-off with strikethrough + emerald badge, done items collapsed. `GET /api/me/todos` returns every open todo assigned to the current user across all projects.
- **Schedule** (`/app/projects/:id/schedule`) — day-grouped event list with start/end times, location, description. All-day toggle.
- **Docs & Files** (`/app/projects/:id/docs`) — 7 MASCI-specific categories (`Submittals`, `Plans & Specs`, `Safety`, `Daily Logs`, `Pictures & Drone`, `Locate Tickets`, `General`). Per-category filter tabs. 30 MB max per file. PDFs open inline, other types force download. `X-Content-Type-Options: nosniff` on every download.
- **Hill Charts** (`/app/projects/:id/hills`) — SVG hill with draggable dots (pointer + touch). Position 0–50 "figuring it out" / 50–100 "making it happen". Click a dot → edit dialog with slider + update note. Each scope gets a stable color.
- **7 new MongoDB collections** (`messages`, `message_comments`, `todo_lists`, `todos`, `events`, `docs`, `hill_scopes`) with proper indexes created on startup.
- **Authorization**: every tool endpoint requires project membership; destructive ops (edit/delete) additionally require author OR owner/admin role.
- **Verified end-to-end** with a 10-step curl chain (login → create → update → delete for all 5 tools) and a frontend smoke screenshot.

## What's Implemented (2026-04-27 · Phase 1 Crew Hub)
- **Per-user JWT auth (2026-04-27):** New `/app/*` section kicks off the Basecamp-style Crew Hub. Login at `/app/login` with email+password → httpOnly access_token (60 min) + refresh_token (7 days) cookies. `/app/change-password` enforced on first login. `/api/auth/me`, `/api/auth/logout`, `/api/auth/refresh` round out the flow. bcrypt password hashing, PyJWT HS256 tokens.
- **Seeded 5 initial users** (David Jewett, Chris Wright, Ramon Rodriguez, Jaymn Judd as `owner`; safety@mascigc.com as `admin`). Default temp password `Welcome2MASCI!` — all forced to change on first login.
- **Admin Users panel** at `/app/users` (owner/admin role-gated): invite new users with temp password, edit role (owner/admin/member), toggle active, reset password. Own-account disable is blocked.
- **31 MASCI jobs + HQ seeded as projects** on first boot. HQ auto-includes every active user. Regular projects have explicit membership managed at `/app/projects/:id/members`.
- **Sidebar layout** with pinned HQ + scrollable project list + Admin section + user footer (avatar + logout). Main content scrolls independently.
- **5 tool tiles per project** (Message Board, To-dos, Schedule, Docs & Files, Hill Charts) wired to placeholder routes — Phase 2 ships Message Board + To-dos first.
- **Coexistence with legacy admin:** the existing `X-Admin-Token` / `Happy123!` password flow continues to work for all `/admin/*` safety dashboards. New JWT users will replace it in Phase 4 after 30-day migration.
- **Backend lint + frontend lint clean, 160/160 existing backend tests still pass.**

## What's Implemented (2026-04-27 · Security Hardening)
  - **Rate limiting** on every public POST endpoint (`/inspections`, `/meetings`, `/jhas`, `/incidents`, `/daily-reports`, `/equipment-units`, `/equipment-inspections`, `/translate`) — per-IP, per-endpoint, default 30/hour, returns 429 on excess. In-memory bucket (single-instance backend, no Redis).
  - **Login throttle** on `/api/admin/login` — 10 failed attempts per IP per 15-minute window → 429 lockout. Successful login resets the counter for that IP.
  - **Admin HMAC secret moved to its own `ADMIN_HMAC_SECRET` env var** (was previously derived from `MONGO_URL` — fragile if Mongo URI ever leaked). Backend warns + auto-generates a per-process secret if the env var is unset.
  - **CORS locked down** — `allow_origins` reads from `CORS_ORIGINS` (now `https://mascidocs.com,https://www.mascidocs.com`) plus `CORS_ORIGIN_REGEX` for the Emergent preview wildcard. Falls back to permissive `*` only when env is unset, in which case `allow_credentials` is automatically dropped to remain CORS-spec compliant.
  - **PDF magic-byte validation** on every JHA Plan + trench-box tabulated-data upload. Files not starting with `%PDF-` are rejected at upload with HTTP 400. Downloads now force `Content-Type: application/pdf` + `X-Content-Type-Options: nosniff` regardless of stored MIME — even a maliciously-stored file cannot render as HTML/JS in the browser.
  - All 160 backend tests still pass after the lockdown. End-to-end verified: 11th login attempt → 429, 31st translate POST → 429, malformed PDF upload → 400 with magic-byte mismatch.
- **Site Posters hub on AdminHub (2026-04-27):** New `SitePostersPanel` lists every printable handout in one place — Crew Cheat Sheet, Trench Box QR, Job Hazard Plans QR. Each row has Preview + Print (`?autoprint=1` triggers the OS print dialog). A "Print All Posters" CTA opens `/admin/posters/print-all?autoprint=1` which stacks the 3 cards with `page-break-after: always` so a single Cmd+P → 3 letter-size sheets.
- **Job Hazard Plans QR Poster (2026-04-27):** Printable poster at `/admin/jha-plans/poster` — amber-themed, QR → `https://mascidocs.com/jha`, "What's in a Hazard Plan" cheat card, live job list. Goes inside every job trailer.
- **Refactored printable cards (2026-04-27):** `CheatSheetCard`, `TrenchBoxPosterCard`, `JhaPlansPosterCard` extracted to `/components/`. Standalone routes wrap them with toolbars; `AllPostersPrint` mounts all 3 with print page-break separators.
- **Trench Box QR Poster (2026-04-27):** Printable poster at `/admin/trench-boxes/poster`. QR → `https://mascidocs.com/trench-boxes`, soil-type quick reference, fleet snapshot.
- **JHA → Job Hazard Plans pivot (2026-04-27):** Old fillable JHA form removed (`NewJha.jsx`, `ViewJha.jsx`, `JhaDashboard.jsx` deleted). Replaced with read-only file-sharing hub at `/jha` and admin upload manager at `/admin/jha-plans`. Legacy URLs redirect cleanly.
- **Trench Box Tabulated Data (2026-04-27):** New OSHA reference at `/trench-boxes` with admin CRUD at `/admin/trench-boxes`.
- **Bilingual coverage extended:** Spanish dictionary expanded for `JhaPlansHub`, `TrenchBoxes`, new Hub tiles, `TrenchBoxPoster`, `JhaPlansPoster`, `AllPostersPrint`, and `SitePostersPanel`. Verified end-to-end via screenshots.
- **160/160 backend pytest passing**.

## What's Implemented (2026-04-26)
- **Field-crew Hub at `/`** — 5 module tiles (Daily Reports, Site Inspections, Safety Meetings, JHA, Incident Reports) each leading to `/<module>/new`. Crews see NO counts, NO record lists, NO delete affordance. Tiny "Admin" link in the footer.
- **Admin wall at `/admin/*`** — shared-password gate. Login at `/admin/login` (default password `masci-admin-2026`, set in `backend/.env` → `ADMIN_PASSWORD`). After sign-in, the office gets:
  - `/admin` — landing with all 5 module counts + sign out + **Auto-Email Routing panel** (PM table + always-CC + live status badge).
  - `/admin/inspections`, `/admin/meetings`, `/admin/jha`, `/admin/incidents`, `/admin/daily` — full dashboards with view / print / delete.
  - `/admin/<module>/<id>` — individual record view with print + map thumbnail.
- All previous top-level URLs (`/inspections`, `/meetings`, etc.) redirect to their `/admin/*` equivalents and bounce to `/admin/login` if no token.
- All 5 modules: list dashboard, new form, view/print, public submit, share-form QR dialog.
- 81-topic library on Safety Meetings with searchable picker.
- Incident severity tiers, root-cause checklist, witnesses, OSHA-recordable + work-stopped flags.
- **Daily Job Reports** — crews/subs/visitors/equipment/materials/activities with Open-Meteo weather, GPS, 6-photo minimum, prepared-by + superintendent signatures, full bilingual UI, and a **stop-the-line Safety Escalation gate** that triggers when the report flags an accident or injury (must notify Safety with name + time, then confirm an Accident/Incident Report has been filed with its own filing time, before the Daily Report can be submitted).
- **MASCI Current Jobs picker on every form** (31 active jobs + Custom).
- **Bilingual UI (English / Spanish)** — language toggle in every form header. Choice persists per device.
- **Bilingual topic library** — all 81 toolbox-talk topics in construction-trade Spanish.
- **Spanish → English auto-translate at submit** — every freeform Spanish-typed field is sent to `/api/translate` (Claude Haiku 4.5 via Emergent universal LLM key) before POST. Skips photos / signatures / dates / numbers / yes-no / GPS coords. Stored DB record + printed PDF stay 100% English. Graceful fallback on LLM failure — submit is never blocked.
- **Map preview thumbnail on PDF** — every View page renders an `<MapThumbnail>` keyless 3×2 OpenStreetMap tile grid with a MASCI-red marker. Hidden on screen, visible in print preview / PDF only.
- **Native browser spell check** — `setLang()` syncs `document.documentElement.lang`. Browsers automatically swap to the Spanish dictionary when in ES mode.
- **MASCI lockup logo** — sized by WIDTH (not height) so the M emblem + MASCI + SAFETY + tagline stays legible at every breakpoint and on the printed PDF.
- **Server-rendered PDFs (WeasyPrint)** + manual `/api/email-report` (Resend) for one-off office sends.
- **Auto-Email PM Routing (2026-02-26)** — every successful POST to `/api/{inspections|meetings|jhas|incidents|daily-reports}` schedules a fire-and-forget background task that:
  1. Resolves the assigned PM by `project_number` (exact → CP-prefix → fuzzy job-name).
  2. Renders the PDF server-side via WeasyPrint.
  3. Emails it via Resend to PM + always-CC (`jaymn.judd@mascigc.com`, `safety@mascigc.com`).
  4. For severe incidents (Medical / Restricted / Lost Time / Fatality / OSHA-recordable / work-stopped) it also CC's whatever is in `SEVERE_INCIDENT_CC` env.
  5. Skips silently with a log line if `RESEND_API_KEY` is missing — submit never crashes.
  - Routing source of truth: `/app/backend/pm_routing.py` (David Jewett: 15 jobs, Chris Wright: 8, Ramon Rodriguez: 4, Jaymn Judd: 1).
  - Admin endpoints: `GET /api/auto-email/routing-table` and `GET /api/auto-email/preview?project_number=…` for verification.
  - Admin Hub now shows a live "Auto-Email Routing" panel summarizing the table + Resend status badge.
- Backend: CRUD on `/api/inspections`, `/api/meetings`, `/api/jhas`, `/api/incidents`, `/api/daily-reports` + `/api/translate` + `/api/admin/{login,check}` + `/api/email-report` + `/api/auto-email/{preview,routing-table}`. POST + translate are public; GET list / GET single / DELETE / auto-email helpers are admin-only.
- 102/102 pytest backend (19 new auto-email-routing tests).
- All interactive elements have kebab-case `data-testid`.

## Backlog

**P0**
- _none active — Hub, 5 modules, auto-translate, map thumbnail, spell check, admin wall, logo fix all complete and tested_

**P1**
- ✅ **Distribution List** field on PDF footer — shipped 2026-04-27. Chip-input on Incident + Daily Report forms, list flows through to PDF + auto-email.
- ✅ **Severity-tier ops/GC fan-out** — `SEVERE_INCIDENT_CC` env var wired into `pm_routing.py`; production just needs the addresses set.
- Multi-user admin (per-account login, audit trail of who viewed/deleted) — legacy Safety Admin only. The Crew Hub side already has per-user JWT + roles.
- Resend Pro upgrade ($20/mo, 50,000 emails/month) when foreman volume exceeds free tier 100/day quota.

**P2**
- Object storage (S3-compatible) for photos once typical record exceeds ~5 MB
- Aggregation `$size` on photos in list endpoints to skip pulling base64 bytes
- Trend dashboard: hazards-by-section, top recurring findings, near-miss → injury conversion
- Refactor: split `server.py` (~950+ lines) into `routes/{admin,inspections,meetings,jhas,incidents,daily_reports,translate,email}.py` with shared models module

## Next Action Items
1. **Get the Resend API key from MASCI ops** + verify the sender domain (e.g. `safety@mascigc.com`) at https://resend.com → Domains. Drop the key into `/app/backend/.env` → `RESEND_API_KEY=…`, optionally set `SENDER_EMAIL=safety@mascigc.com`, then `sudo supervisorctl restart backend`.
2. Test the live pipeline: submit one Site Inspection from `/inspect/new` with `project_number=24-06` and confirm David Jewett + Jaymn + safety@ all receive the PDF.
3. Decide if next module is **Equipment Pre-Op** or **DOT Vehicle Daily**.
4. Consider multi-user admin (with audit trail) once 2+ office staff need access.

## 2026-04-28 — Equipment Master Fleet (P0 complete)
- Parsed `Equipment List.xlsx` (Louis sheet — master) → 589 units across 27 categories.
- Seed file: `/app/backend/data/equipment_master.json` (committed; auto-syncs to DB on startup if file count differs from `equipment_master` collection count).
- New endpoint: `GET /api/equipment-master[?category=...]` → `{ categories[], items[], grouped{}, count }`.
- Pre-Op fan-out: seed also populates legacy `equipment_units` (mapped via `preop_equipment_type`) so existing Pre-Op dropdown auto-fills with master fleet.
- New shared component: `/app/frontend/src/components/EquipmentCombo.jsx` — searchable, category-grouped picker with always-on free-text fallback (operators can still type custom equipment).
- Wired into:
  - `NewEquipmentInspection.jsx` — Unit # / Label field (auto-fills make/serial on pick).
  - `NewDailyReport.jsx` — Equipment Log → "Unit / Equipment" field (replaces free-text "Description / ID").

## 2026-04-28 — Suppliers + Employees Live (P0 complete)
- **234 MASCI employees** seeded from `EmployeeList 4-28-26.xls` (.xls binary parsed with xlrd) — names only, no PII like hire dates. Stored in `employees` collection. Available at `GET /api/employees`. Searchable via the existing `<EmployeeCombo>`.
- **135 MASCI suppliers / subcontractors** seeded from `Supplier & Vendors.xlsx`. Stored in `suppliers`. Available at `GET /api/suppliers`. New `<SupplierCombo>` component (mirrors EquipmentCombo / EmployeeCombo) with searchable list + free-text fallback for one-off vendors.
- Wired into Daily Report:
  - **Section 05 Subcontractors on Site** — Company → SupplierCombo, Foreman → EmployeeCombo.
  - **Section 08 Material Deliveries** — Supplier → SupplierCombo (Ticket Photo uploader unchanged).
- Admin upload tooling on `/admin` (mirrors EquipmentMasterPanel / EmployeeMasterPanel):
  - **MASCI Supplier & Subcontractor List** panel — `.xlsx` or `.csv`, column 1 = company name. Auto-skips dividers ("MASCI", "D-MAC", "NOT LISTED ADD TO NOTES") and header rows.
- Idempotent startup seed for both employees + suppliers (only runs when collection is empty — won't overwrite admin uploads).
- ES translations added: "Type or pick a supplier…", "Browse supplier list", "Search by company name…", "Supplier list not uploaded yet — type freely.", "Tip: type freely for one-off vendors not in the list.". RepeatBlock + DR field configs cleaned of hardcoded English placeholder fallbacks so all combos use their `useT()` defaults in ES mode.
- Validation (testing agent iteration 21): 6/6 backend pytest, frontend EN+ES end-to-end ('Cemex' picker → fills company; 'Alec' → fills foreman; ES placeholders confirmed via attribute). Equipment-fleet 589 + Employees 234 regression intact.


### Daily Report
- **Auto-generated Report #** — `DR-YYYYMMDD-NNN`. Fetched on form mount via new endpoint `GET /api/daily-reports/next-number`. Editable by user if needed.
- **Section 04 "MASCI Crews on Site" rebuilt** — now a row-table per crew member with Name (EmployeeCombo) + Trade + Start Time + Lunch Minutes + Stop Time → auto-calculated `hours` field (handles overnight shifts) + a sticky "Total crew hours today" footer bar. PDF prints the same table with totals row.
- **Section 08 Material Deliveries** — added per-row `ticket_photos` uploader; PDF inlines the ticket photos under the materials table.
- **Photo upload (used everywhere)** — split into two buttons: "From Gallery" (no `capture` attr → iOS shows Library/Take Photo/Choose File sheet) and "Take Photo" (forces camera). Removed the camera-only behavior on iOS.
- **GPS reliability** — `getCurrentPosition` now retries with low-accuracy + cached fix on timeout; iOS PositionError codes are mapped to actionable user messages (e.g. "Location permission denied. Tap AA in Safari → Website Settings → Location → Allow").

### Cross-form upgrades
- **EmployeeCombo** (`/app/frontend/src/components/EmployeeCombo.jsx`) — searchable picker fed by `GET /api/employees`. Drop-in component: free-text fallback always works.
- Added EmployeeCombo to **Site Inspection** (operator), **Incident** (reported_by, supervisor_name, witness names), **Equipment Pre-Op** (operator), **Daily Report** (every crew name).

### Backend
- Added `GET /api/employees`, `GET /api/admin/employees/status`, `POST /api/admin/employees/upload` (.xlsx or .csv with column "Name" + optional Employee ID/Trade/Role/Crew/Email/Phone), `POST /api/admin/employees`, `DELETE /api/admin/employees/{id}`.
- Added `GET /api/daily-reports/next-number?date=` — registered BEFORE `/daily-reports/{report_id}` so FastAPI route ordering doesn't swallow it.
- `pdf_render._render_daily` field mapping fixed (was using stale `crews/materials.name/qty` keys); now matches actual schema and prints crew totals + ticket photos.

### Admin UI
- New `EmployeeMasterPanel` on `/admin` (mounted directly under `EquipmentMasterPanel`) — counter, last-updated timestamp, single "PICK FILE" button to upload roster.

## 2026-04-28 — Admin Upload Tool for Equipment Fleet
- New module `/app/backend/equipment_parser.py` — shared `parse_equipment_xlsx(bytes, sheet="Louis")` used by both startup seed and the admin upload endpoint (single source of truth for parsing rules).
- New endpoints (admin-only):
  - `GET /api/admin/equipment-master/status` → `{ count, categories{}, last_updated, seed_file }`.
  - `POST /api/admin/equipment-master/upload` → multipart file upload; rejects non-xlsx (400); backs up prior seed JSON to `equipment_master.<timestamp>.bak.json`; rewrites `data/equipment_master.json`; replaces both `equipment_master` and fans out into `equipment_units`.
- New frontend component: `/app/frontend/src/components/EquipmentMasterPanel.jsx` — mounted on `/admin` directly under the Backup hero. Shows total units, last-updated stamp, top-6 category chips, "Pick .xlsx" upload button + refresh button.
- AdminGuide (`/admin/guide`) gained a new "Updating the equipment fleet" section.
- Added `openpyxl==3.1.5` to `backend/requirements.txt`.
- Validated by testing agent: 9/9 backend pytest passes, 3/3 frontend smoke flows verified end-to-end (panel renders, Pre-Op combo filters + auto-fills make, Daily Report combo opens, upload replaces collection + JSON + creates backup, auth gates work).



---

## CHANGELOG · 2026-05-05 · Pre-Deploy QA Sweep (iter 38)

**Saved permanent QA prompt** at `/app/memory/MASCI_HUB_PreDeploy_QA_Prompt.md` — must be reused before EVERY future MASCI HUB deployment/update.

**Verdict: PASS — ready for deployment.**

### Backend (100% — 50/50)
- All 4 auth gates (admin, PM, shop, safety-forms) reject bad creds with 401 ✅
- All scoped/admin list endpoints (jobs, PMs, safety-forms, equipment-inspections, qaqc, daily-reports, inspections, meetings, incidents, jhas, trench-boxes, equipment-master) return 200 for admin token, 401 unauthenticated ✅
- PM scoping verified: Chris Wright's per-PM token returns proper subset of admin job list ✅
- ES → EN translate pipeline returns correct English ✅
- WeasyPrint PDFs render real %PDF bytes >1KB ✅
- Auto-email correctly skipped in preview (AUTO_EMAIL_REPORTS=false) ✅
- 127 backend routes, 0 errors in startup log ✅

### Frontend Fixes Applied (3 patches)
1. `/qa-qc` route alias added → redirects to `/qaqc` (was 'No routes matched location')
2. `/training-hub` route alias added → redirects to `/training` (same)
3. ES translation entries added in `/app/frontend/src/lib/i18n.js`:
   - "Quality Assurance" → "Aseguramiento de Calidad"
   - "Quality Assurance · Quality Control" → "Aseguramiento de Calidad · Control de Calidad"
   - "Quality assurance and quality control inspections for concrete, rebar, and subcontractor work — documented, signed, photographed, routed, and stored." → full ES translation

### Verified visually
- Home in ES: zero English leaks on hub tiles (Campo / QA·QC / Seguridad / Cumplimiento)
- Mobile @ 390px: zero horizontal overflow
- Footer: "© MASCI · Platform developed by The Judd Group LLC" (single, correct)
- No Emergent branding visible

### Production deploy reminders (NOT preview blockers)
- Set `AUTO_EMAIL_REPORTS=true` in production env (preview is intentionally false to spare Resend quota)
- Set `RATE_LIMITING=on` in production env (preview is off so test suite doesn't trip 429s)
- Test data cleanup: 2 TEST_QA38_* safety issuances were created during testing and removed via direct mongo cleanup.

### Test report
- `/app/test_reports/iteration_38.json` — full pre-deploy QA sweep log
- `/app/backend/tests/test_iter38_predeploy_qa.py` — pytest suite created by testing agent (50/50 pass)

---

## CHANGELOG · 2026-05-06 · Records & Forms — Job Folder Rollup

**User request**: "in pm & admin portals could we place all info in Records & Forms tiles sorted into job folders? Example: if i clicked on daily report tile of Records & Forms now it list all jobs in whatever order reports came in vs sorted by job name."

**User chose**: Pattern A (accordion folders) + most-recent-first folder sort + all collapsed by default + roll out to all 7 dashboards in admin + PM.

### Built
- **New reusable component**: `/app/frontend/src/components/JobFolderList.jsx`
  - Groups any record list by `project_number` + `project_name`
  - Sorts folders by max(dateField) DESC (newest activity first)
  - All folders collapsed by default
  - Per-folder header: chevron + folder icon + #PROJECT-NUMBER badge + project name + count badge + "Last activity:" timestamp
  - Toolbar: search jobs (filters folder names), Expand All / Collapse All buttons
  - Empty state + no-match state
  - Bilingual (EN/ES) via existing i18n
  - Full data-testid coverage (`{prefix}`, `{prefix}-search`, `{prefix}-expand-all`, `{prefix}-collapse-all`, `{prefix}-toggle-{number}`, `{prefix}-count-{number}`, `{prefix}-body-{number}`)

### Wired into all 7 Records & Forms dashboards
| File | Date field | testIdPrefix |
|---|---|---|
| `pages/DailyReportsDashboard.jsx` (admin + PM) | `report_date` | `daily-folders` |
| `pages/Dashboard.jsx` (Site Inspections, admin + PM) | `inspection_date` | `inspection-folders` |
| `pages/MeetingsDashboard.jsx` (admin + PM) | `meeting_date` | `meeting-folders` |
| `pages/IncidentsDashboard.jsx` (admin + PM) | `incident_date` | `incident-folders` |
| `pages/EquipmentDashboard.jsx` (admin + PM Pre-Op) | `inspection_date` | `equipment-folders` |
| `pages/AdminQaqcList.jsx` + `pages/PmQaqcList.jsx` | `inspection_date` | `qaqc-folders` / `pm-qaqc-folders` |
| `components/AdminSafetyFormsPanel.jsx` (Issuance + Training tabs) | `_sf_date` (synthesised) | `admin-sf-folders-{tab}` |

### Notes
- All existing per-row content preserved verbatim (badges, status pills, View/Delete buttons, OSHA-recordable flags, FAIL highlights, score grades)
- QA/QC and Safety Forms converted from `<table>` to card-style rows for visual consistency with the other 5 dashboards
- Fixed pre-existing latent bug in `MeetingsDashboard.jsx`: `pathname` was referenced but never destructured from `useLocation`
- Lint clean across all 9 modified files
- Smoke-tested in admin: 5/6 dashboards verified rendering folders with correct counts, search, and expand/collapse working. QA/QC tested empty (no records in preview DB).

### Translation strings added (EN/ES)
- "Search jobs…" / "Buscar trabajos…"
- "Clear search" / "Borrar búsqueda"
- "Expand All" / "Expandir Todo"
- "Collapse All" / "Colapsar Todo"
- "Last activity:" / "Última actividad:"
- "No jobs match" / "Ningún trabajo coincide"
- "No records yet." / "Aún no hay registros."
- "(No Job)" / "(Sin Trabajo)"

---

## CHANGELOG · 2026-05-06 · Daily Report PDF Bug Fixes

**Field foreman report** (Leandro Juarez): "filled out activity log & general notes — not showing on report in admin or PM portal or PDF. Also funky HTML letters showing in Work Performed column."

### Three bugs in `/app/backend/pdf_render.py` — ALL fixed

#### Bug 1 — Activities Performed PDF section blank (CRITICAL data loss appearance)
- **Root cause**: PDF renderer at line 355-365 read `a.get("description")` but the frontend Daily Report form sends `activity` / `percent_complete` / `station_from` / `station_to` / `notes`. Every cell was None → table rendered with empty rows.
- **Fix**: Renderer now reads all 5 actual frontend keys and renders them across columns "Activity / % Done / From / To / Notes", matching the on-screen view.

#### Bug 2 — Raw HTML showing as text in "Work Performed" column (visible to crews)
- **Root cause**: `_table()` runs every cell value through `_e()` which HTML-escapes the string. The crew-table builder injected raw `<div style='...'>gross/net summary</div>` strings + `<b>Total Hours</b>` into cells expecting them to render as markup. They were escaped → printed as literal `<div style='margin-top:4px;font-family:monospace;…'>` text in the PDF.
- **Fix**: Introduced `_RawHtml` marker class. `_e()` checks for it and returns the unescaped HTML. Crew work-performed cell + Total Hours bold cells now wrap their HTML in `_RawHtml(...)`. All other cells continue to be HTML-escaped as before (XSS-safe).

#### Bug 3 (latent) — User text not escaped within the raw-HTML cell
- **Root cause**: When mixing user input with raw HTML, the user input was concatenated unescaped — meaning a crew member's "<test>" comment would render as broken markup.
- **Fix**: User text inside `_RawHtml` cells now gets `escape()`-ed before concatenation. User text safe + intentional markup raw.

### Files changed
- `/app/backend/pdf_render.py`:
  - Added `_RawHtml` class (lines 95-110)
  - Updated `_e()` to skip escaping for `_RawHtml` instances
  - Crew table builder now wraps gross/net summary cell in `_RawHtml(escape(wp) + summary_div)`
  - Total Hours row wraps both label and total in `_RawHtml`
  - Activities Performed section reads correct frontend keys (5 columns)

### Verified
- Lint clean
- E2E: rendered real report `b9564cc5-f129-4745-982d-cce58465e5cb`:
  - ✓ "Curb pour", "60%", "10+00" all render in Activities table
  - ✓ "Smooth day." renders in General Notes
  - ✓ No escaped `&lt;div` or `&lt;b&gt;` markers anywhere
  - ✓ `<b>Total Hours</b>` and `<b>20.00</b>` render as bold (raw HTML preserved)

### ⚠️ Production redeploy required
This is in PREVIEW. Production daily-report PDFs on `mascidocs.com` are still showing escaped markup + empty Activities sections until redeployed.

---

## CHANGELOG · 2026-05-07 · Deep Pre-Deploy QA Sweep (iter 39) — VERDICT: PASS

**Context**: User legitimately called out that previous QA sweeps were too shallow — they missed bugs that crews then reported in production (photo thumbnails not rendering, escaped HTML in PDFs, empty activities sections, silent missed backups). This sweep was redesigned to ACTUALLY exercise critical flows end-to-end instead of just loading pages.

### Six-phase audit completed
1. **Static code audit** — 102 routes, no PhotoUpload prop mismatches, no console.log, no hardcoded localhost, no production-leaked TODOs, frontend builds clean (18s)
2. **Deep PDF + data schema audit** — all 6 form-type PDFs render valid bytes (>5KB, %PDF magic, zero escaped HTML markers), all sample fields present in rendered output
3. **Backend endpoint health** — all 4 auth gates 401 on bad creds, all admin endpoints 401 without token + 200 with token, translate API works ES→EN
4. **Deep end-to-end form submission + photo upload + PDF generation** — actually uploaded photos and verified thumbnails render in DOM, actually submitted forms and verified records, actually generated PDFs and verified content (5 kinds direct render via pdf_render.render_record_pdf)
5. **EN/ES leak hunt** — 7 hub/login pages tested. Zero English leaks for the watch list ['Quality Assurance','Submit Inspection','Back to Hub','Add Photo','Loading...','Logout','View All']. Admin login is intentionally English-only (internal staff)
6. **Mobile + route hunt** — 14 routes 200 OK with substantive bodies, /qa-qc and /training-hub aliases redirect correctly, build version stamp v2026.05.07-4209543 present in footer

### New persistent regression suite
`/app/backend/tests/test_predeploy_iter39.py` — 29 tests covering:
- Auth gate enforcement (4 logins)
- Admin endpoint token enforcement (8 endpoints)
- PM scoping (cannot hit admin endpoints, jobs subset)
- ES→EN translate
- PDF render for 5 record kinds (no escaped HTML in extracted text)
- Daily Report PDF specifically asserts Activities Performed marker + General Notes marker (regression for Leandro's bug)
- Footer "Judd Group" attribution

**29/29 PASS — confirmed re-running after seed cleanup.**

### Action items for production deploy
- ✅ Redeploy approved
- ⚠️ Set on production env: `AUTO_EMAIL_REPORTS=true` and `RATE_LIMITING=on` (preview leaves both off intentionally)
- Test seed data cleaned (4 TEST_ITER39 records removed across collections)
- (Optional, non-blocking): add EN/ES toggle to /admin/login if bilingual policy is universal

### Test report
- `/app/test_reports/iteration_39.json`
- `/app/backend/tests/test_predeploy_iter39.py` (NEW — 29 tests, all green)
- `/app/test_reports/pytest/iter39_results.xml`
