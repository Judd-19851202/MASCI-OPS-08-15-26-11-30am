# MASCI Safety Hub — PRD

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
