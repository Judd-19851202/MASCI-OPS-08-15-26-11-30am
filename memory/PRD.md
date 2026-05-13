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
