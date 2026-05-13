# MASCI Safety Hub — PRD

## 2026-05-13 — Iter72: HR Payroll Variance + Training Updates (Phase A & B)

### User ask
"Now that HR has read-only payroll cross-check, the natural next move
is a paste-Exact-CSV payroll diff... Do this. Also a whole weekly
employee export email option whatever you think is best. We need to
update all guides/cheat sheets on HR Hub & make a training section
so HR can be trained. Update admin training on all new admin sections
too. (Phase C/D — tile layout + verbiage — deferred to next round.)"

### What shipped — Phase A (Payroll Variance)
- **Backend** `/app/backend/routes/payroll_variance.py`:
  - `parse_exact_csv()` — flexible parser w/ column auto-detection
    (Employee Name + Reg-or-Total Hours required; OT, ID, Week
    Ending optional; comma/tab/pipe delimited).
  - `build_variance_rows()` — matches each Exact row to a
    masci_crews weekly aggregate by `last:first-initial` name key;
    produces flagged rows (match · minor · flag · unmatched ·
    missing_from_payroll).
  - Endpoints (all X-HR-Token gated):
    - `POST /api/hr/payroll-variance/upload`
    - `GET  /api/hr/payroll-variance/recent`
    - `GET  /api/hr/payroll-variance/{batch_id}`
    - `POST /api/hr/payroll-variance/{batch_id}/decision`
    - `GET  /api/hr/payroll-variance/{batch_id}.csv`
  - Weekly email cron (server.py background loop): Sunday 18:00 UTC
    default. Recipients = `PAYROLL_VARIANCE_EMAIL_TO` env or
    `hrmanager@mascigc.com,jaymn.judd@mascigc.com`. Skipped when
    `AUTO_EMAIL_REPORTS=false` or `RESEND_API_KEY` unset.

- **Frontend** `/app/frontend/src/pages/HrPayrollVariance.jsx`:
  - Paste-CSV textarea + week-ending date + threshold (min) input.
  - "Run Variance" → batch card with stats strip + colour-coded
    rows (🟢 match · 🟡 minor · 🔴 flag · 🟥 missing-in-payroll).
  - Per-row Approve / Dispute buttons persist immediately.
  - Recent Variance Batches table (re-loadable).
  - "Download CSV" button on the batch card.
  - New HR Hub tile (red accent, 5th tile).

- **Bug found & fixed during test agent run**: FastAPI route shadowing
  — `/{batch_id}.csv` was registered AFTER `/{batch_id}`, so the
  dynamic param captured the `.csv` suffix and returned 404. Fix:
  re-order routes so the `.csv` endpoint comes first.

### What shipped — Phase B (Training Updates)
- **HR track** added (`audience: "hr"`, purple accent, 8 lessons):
  - hr-01 Portal overview
  - hr-02 Field Leadership Records (read-only)
  - hr-03 Employee Accountability (offboarding clearance)
  - hr-04 Time Verification
  - hr-05 Payroll Variance (Exact CSV diff)
  - hr-06 Training Records
  - hr-07 End-to-end Offboarding Workflow
  - hr-08 Your Account & Password
  All bilingual EN+ES. PDF packets work via existing
  `/api/training/packets/hr.pdf` route since `training_pdf.py` now
  registers `TRACKS["hr"]` and appends `HR_LESSONS` to LESSONS.

- **Admin lessons 11-14** added (all bilingual):
  - admin-11 HR Users & Logins
  - admin-12 Employee Terminations Dashboard
  - admin-13 Hub Banner Messaging System
  - admin-14 Cloud Archives (Cloudflare R2)

- **TrainingHub.jsx**: `trackUnlocked()` + `loginPathFor()` + tile
  preview now handle `audience === "hr"` (login redirect → /hr/login,
  unlock requires `isHr()`).

### Verified
- Backend pytest iter72: 21/21 ✓ (parse + threshold + lifecycle +
  CSV + auth + cron-safe no-op).
- Iter71 regression: 21/21 ✓.
- Playwright (testing agent + main agent smoke): 5-tile HR Hub
  renders, paste-CSV → batch with 2 rows → Approve persists,
  Recent batches table populated, Open reload works.

### Files added
- `/app/backend/routes/payroll_variance.py`
- `/app/frontend/src/pages/HrPayrollVariance.jsx`
- `/app/backend/tests/test_payroll_variance_iter72.py`

### Files modified
- `/app/backend/server.py` (variance router mount + weekly cron hook)
- `/app/frontend/src/App.js` (HR variance route)
- `/app/frontend/src/pages/HrHub.jsx` (5th tile)
- `/app/frontend/src/data/training.js` (HR track + 8 HR_LESSONS + 4 admin)
- `/app/frontend/src/data/training_es.js` (Spanish mirrors)
- `/app/frontend/src/pages/TrainingHub.jsx` (HR audience routing)
- `/app/backend/training_pdf.py` (HR track + HR_LESSONS + admin 11-14)
- `/app/memory/PRD.md`

---

## 2026-05-12 — Iter71: HR Portal (full stack)

See previous notes. Summary: HR auth + chrome (RequireHr,
EnforcePortalScope, tokenValidation), 4 HR sub-pages, AdminHRUsersPanel
in /admin, Public Hub HR Portal section card.

---

## Earlier iterations
- iter70: Field Leadership Employee Termination form + Admin Terminations dashboard.
- iter69: Shop Portal "View inspection does nothing" 404 fix.
- iter68: Full Enterprise Deployment-Readiness Audit (scored 9.4/10).
- iter67: Banner Audit PDF/CSV/Clone/Archive toggle.
- iter66: Banner Audit Trail.
- iter65: Hub Banner Messaging System.
- iter64: R2 photo migration + Cloud Archives panel + nightly archive.
- iter63: Backup hardening.
- iter62: Backup resiliency.
- iter61: Training docs sweep.
- iter60: Admin Email Routing.
- iter59: Job Photos performance.
- iter58: System Audit log + Doc ID search.

---

## Prioritized backlog (next tasks)

### P0 — pending user decision
- **Phase C — Public Hub tile layout** (4 options presented).
- **Phase D — Tile verbiage tone** (3 options + visibility scoping).

### P1
- Migrate remaining base64 signatures to R2 (write_up, recognition).
- Backup verification cron (weekly R2 archive integrity check + email).
- IT server-dump endpoints (`/api/admin/server-dump/list|latest`).
- Employee Login Gate (bulk import + termination + usage).
- Photo-First Daily Report (AI drafted from gallery photos).
- Motive (Fleet) integration (Pre-Op autofill, GPS verification).
- Optional refactor: extract parse_exact_csv + build_variance_rows
  to a `services/` module (iter72 reviewer suggestion).
- Strengthen `_name_key` matcher with `employee_id` fallback for
  common-surname collisions.

### P2
- "Restore from R2" admin button (manual archive pick).
- "Forward to IT" share button on backup rows.

---

## Test credentials
See `/app/memory/test_credentials.md`. Quick refs:
- Admin: `MASCI1982!`
- HR Manager: `hrmanager@mascigc.com` / `HRPortal2026!`
- Shop: `testmech@mascigc.com` / `ResetWorks2026!`
- Field Leadership: `MASCIGC`
- PM (Chris Wright): `chriswright@mascigc.com` / `ChrisRocksThis2026`
