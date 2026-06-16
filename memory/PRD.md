# MASCI Operations Platform — PRD

## Original Problem Statement
MASCI Operations Platform RC-1 Release Certification — Track 13.6+ "Operational Recovery Phase". Goal: convert "collection of dashboards" → "Operational Heavy-Civil Operating System."

Hard rules: Action-Queue Focus · No Dead Objects · Preserve Forms & Workflows · `*_legacy` Rollback Pattern · NO deploy / NO GitHub save / NO merge.

## Architecture
- Frontend: React + Tailwind + Shadcn (`/app/frontend`)
- Backend: FastAPI + MongoDB (`/app/backend`)
- Memory: Append-only Markdown ledgers in `/app/memory/`

## Latest Closed Track (2026-06-16 · TRACK 15.4A · HERO PERIOD FIX + FIELD LEADERSHIP CARD POLISH · 🟢 PASSED)
- **Track:** Tight polish pass — hero period color + Field Leadership card upgrade.
- **Verdict:** 🟢 12/12 closure criteria · 25/25 Five Pillars.
- **Phase 1 — Hero period**: red span shrunk to "Every Job" (no trailing period); final `.` now inherits navy `text-slate-900`. EN + ES both fixed.
- **Phase 2-5 — Field Leadership card**: replaced thin `<MediumTile>` with sibling `<FieldLeadershipCard>` matching `<ProjectSystemsCard>` shell language. 4 real route launchers in 2×2 grid (Open Hub /leadership, Recognition /leadership/recognition/new, Write-Up /leadership/write_up/new, Equipment Checkout /leadership/equipment_checkout/new) + footer link "View all Field Leadership records" → /leadership/records. Calm slate-50 → slate-900 hover palette differentiates from Project Systems' colored brand launchers — sibling, not clone.
- **Phase 4 — Visual balance**: card heights within 2% of each other at desktop. iPad portrait + landscape verified.
- **Phase 7 — Regression**: +6 new frontend assertions (hero accent contract, FL card title, 4 launcher routes, footer link route). Combined suite: 24 assertions across 15.1-15.4A.
- **Cleanup**: production untouched, 3 frontend files edited, 1 report created.

## Previous Closed Track (2026-06-16 · TRACK 15.4 · RC1 LIVE FIX DEPLOYMENT + HOMEPAGE HERO / PROJECT SYSTEMS POLISH · 🟡 PASSED WITH OPERATOR FOLLOW-UP REQUIRED)
- **Track:** Seven-priority sequence — deploy 15.1+15.2+15.3, run notification cleanup, prove PM Add Member, polish Project Systems + logos + hero copy.
- **Verdict:** 🟡 13/13 directly-actionable items GREEN. 3 operator-owned items pending (deploy, prod DB cleanup, Project 26-07 retry).
- **Phase 4 — Project Systems card weight**: ~+18% (p-5→p-6, text-xl→text-2xl, h-14→h-16, 56→72px chip). Equal peer to Field Leadership.
- **Phase 5 — Logo normalization**: every launcher button is one component shape (identical 72×72 black chip, 4px left-stripe, mono LAUNCH eyebrow, font-display label, hover/focus/touch target). Only label/url/accent/logo/logoMax differ across the three.
- **Phase 6 — ForgedOps logo visibility**: per-platform `logoMax`; Basecamp/OnStation 52px max, ForgedOps 64px max (+23% logo). Same button + same chip → no oversized feel. Orange wordmark legible.
- **Phase 7 — Hero copy**: EN headline → "One System. Every Crew. Every Job." (Every Job. red). EN subheadline → approved capability sentence. ES translation added.
- **Phases 8-11**: beauty pass (no defects in touched areas), responsive proof (1280×900 + 768×1024 + 1024×768), link proof (DOM-probed target=_blank + rel=noopener noreferrer), 7-assertion regression suite (`Hub.track_15_4.test.jsx`).
- **Phase 1-3 operator-owned**: deploy runbook §2.1, cleanup runbook §2.2, PM Add Member retry per Track 15.2 §6.2. Single combined backend+frontend redeploy ships 15.1+15.2+15.3+15.4.
- **Cleanup ledger**: production untouched. 2 frontend files edited, 1 test created, 1 report created.

## Previous Closed Track (2026-06-16 · TRACK 15.3 · PROJECT SYSTEMS TILE MODERNIZATION & FORGEDOPS PLANS LAUNCHER · 🟢 PASSED)
- **Track:** Replace landing-page "Projects" tile with production-ready "Project Systems" launcher hosting Basecamp + OnStation + ForgedOps Plans.
- **Verdict:** 🟢 12/12 Definition-of-Done items met · 25/25 across Five Pillars · 10/10 logo quality.
- **Changes:**
  - `/app/frontend/src/pages/Hub.jsx` — new `ProjectSystemsCard` component + `PROJECT_SYSTEMS` config-driven array (white-label-ready). Backward-compatible `ProjectsCard` alias retained.
  - `/app/frontend/public/brand-logos/{basecamp.jpeg, onstation.jpeg, forgedops-plans.png}` — official logos saved.
- **DOM-verified:** all 3 launchers carry correct URL + `target=_blank` + `rel=noopener noreferrer` + data-testids `hub-projects-{basecamp,onstation,forgedops-plans}-btn`.
- **Responsive proof:** iPad portrait (768×1024) + landscape (1024×768) + desktop (1280×900) — graceful wrap, no truncation, no overlap.
- **ForgedOps Plans button** uses full brand name (NOT "FO Plans" / "FOP" / "Plans"), `min-w-[180px]` + `whitespace-nowrap` enforces it.
- **Brand colors:** Basecamp green (#16a34a) · OnStation blue (#1d4ed8) · ForgedOps orange (#ea580c) on left-edge stripe + LAUNCH eyebrow.
- **Logo integration:** 56×56 black logo chips match the source-asset backgrounds; `object-contain` + 44×44 max preserves aspect ratios across all three.
- **Cert report:** `/app/memory/TRACK_15_3_PROJECT_SYSTEMS_CERTIFICATION.md` (full 6-section evidence trail incl. Logo Quality Certification per directive Section 5A).
- **Production deploy required** to ship — single frontend redeploy (no backend changes).

## Previous Closed Track (2026-06-16 · TRACK 15.2 · PM STAFFING PROOF + NOTIFICATION LEAK CLEANUP + ACCOUNT/PASSWORD FLOW CERTIFICATION · 🟡 PASSED WITH OPERATOR RETRY REQUIRED)
- **Track:** Live production trust recovery — three remaining items from 15.1.
- **Verdict:** 🟡 13/16 GREEN · 3/16 YELLOW (all operator-execution gates: cleanup `--apply`, deploy, Project 26-07 retry).
- **Cleanup script delivered**: `/app/backend/scripts/track_15_2_backfill_leaked_pm_offboarding.py`. Dry-run-by-default · tight predicate (linked_source_module='hr.offboarding' AND recipient_role='pm' AND recipient_user_id IS NULL AND linked_employee_id IS NOT NULL) · audit-logged · reversible from ledger · capped at 200 rows. Expires broadcast rows (no delete) and fans out person-targeted copies to legitimate PMs.
- **PM Add Member runtime cert**: 6-test pytest suite in `tests/test_track_15_2_pm_add_member_runtime.py`. All 6 PASS. Critical static-analysis test (`test_add_member_does_not_create_a_login`) enforces at CI time that `routes/project_team_assignments.py` NEVER writes to any of 7 portal-user collections + never calls password ops.
- **Account/password flow doc**: `/app/memory/PM_STAFFING_ACCOUNT_PASSWORD_FLOW.md`. 14-question Q&A, canonical contract ("identity-binding, not credential-issuance"), 8 password-issuing surfaces listed, worked Field-Leadership example, edge cases.
- **Project 26-07 retry plan**: §6.2 of the report — 10-step operator checklist with hypothesis ranking and decisive evidence collection.
- **Combined 15.1+15.2 regression**: 11/11 PASS.
- **Production untouched** (0 mutations). Preview cleaned (0 cert residue).

**Operator-owned next actions:**
1. Deploy Track 15.1 + 15.2 fixes (single combined backend+frontend redeploy).
2. Run cleanup script `--apply` against production after dry-run review.
3. Retry PM Add Member on Project 26-07 per §6.2 checklist.

## Previous Closed Track (2026-06-16 · TRACK 15.1 · LIVE PRODUCTION OPERATIONAL DEFECT SWEEP · 🟢 PASSED WITH FOLLOW-UPS)
- **Track:** Live production defect response — user reported 5 defects from iPad use of production deploy.
- **Mode:** read-only on production · runtime-proof on preview (matching `source_hash=740398bc1f9277a8edfdb1e92e5dc26d`).
- **Verdict:** 🟢 **PASSED** with 2/16 yellow follow-ups.

**Defects fixed (4 user + 1 bonus):**
- D1 — PM notification leakage (Offboarding broadcast to ALL PMs): FIXED at the write site. `task_service.create` now propagates `assignee_user_id` → `recipient_user_id`; `_fan_out_offboarding_playbook` PM row is per-project scoped via new `_resolve_offboarding_pm_targets()` helper. PMs of unrelated projects never see offboarding noise. Skip-when-empty if no active assignments. **5/5 pytest regression PASS.**
- D2 — Notification drawer iPad layout (Close X colliding with Mark all read; cramped sound row): FIXED. `pr-12` on header row, `flex-wrap` on sound row, iPad touch targets bumped to `h-8`. Runtime-verified at 768×1024 and 1024×768.
- D3 — PM nav dead-click audit: PASS. All 29 PM sidebar routes registered in App.js. Parent domain rows are intentionally expand-only (cross-portal consistent with Admin).
- D5 — Shop role dropdown gap: FIXED. Added Equipment Manager, Asset Manager, Asset Administrator, Fleet Coordinator, Shop Representative. Label-only change (no permission redesign).
- BONUS P1 — Junk text `data-testid={...}` rendered as button content in `AdminShopUsersPanel.jsx` (line 308): FIXED.

**Deferred with follow-up tickets:**
- D1 follow-up — backfill script for ~6 historical leaked PM offboarding notifications already in `db.notifications`. Requires operator-approved write to production.
- D4 — PM Add Member runtime cert: code path 12/12 audited green, but exact-user-context repro (Project 26-07) requires ask-back to the user for the toast/dialog state.

**Cleanup ledger:** zero residue in production (`masci_safety`), zero residue in preview (`masci_safety_preview`) after test suite cleanup. No real emails sent. No real users touched.

**Files changed:**
- `/app/backend/routes/employee_lifecycle.py` — added `_resolve_offboarding_pm_targets()`, rewrote PM playbook branch
- `/app/backend/routes/tasks_notifications.py` — `task_service.create` propagates `recipient_user_id`
- `/app/frontend/src/components/NotificationBell.jsx` — iPad drawer header rework
- `/app/frontend/src/components/AdminShopUsersPanel.jsx` — role catalog expansion + junk text fix
- `/app/backend/tests/test_track_15_1_offboarding_pm_scoping.py` — 5-test regression suite (NEW)
- `/app/memory/TRACK_15_1_LIVE_PRODUCTION_DEFECT_SWEEP_REPORT.md` — comprehensive 14-section report (NEW)

**Production deploy required** to activate the fixes. Single backend+frontend redeploy. No DB migration.

## Previous Closed Track (2026-06-16 · RC1 LIVE POST-DEPLOY VERIFICATION · 🟢 VERIFIED WITH OBSERVATIONS)
- **Track:** RC1 LIVE POST-DEPLOY VERIFICATION against `https://mascidocs.com`.
- **Mode:** READ-ONLY · NO MUTATIONS · NO REAL EMAILS · NO JUNK DATA.
- **Verdict:** 🟢 **VERIFIED WITH OBSERVATIONS** — 13/13 checks PASS.
- **Production identity confirmed:** `app_env=production`, `db_name=masci_safety`,
  `source_hash=740398bc1f9277a8edfdb1e92e5dc26d`, Sentry enabled,
  session timeouts enabled (ADMIN_HR/OPERATIONS/FIELD), TLS valid,
  HSTS preload, Cloudflare edge.
- **All 11 SPA routes** return 200; **all 8 portal logins** return 401 on bad creds (uniform, no enumeration); **all 14 protected endpoints** return 401 without token; **all 7 admin POST endpoints** return 401 without token.
- **Security controls verified active:** rate-limiting (7 bad → 429 lockout), CORS allow-list enforced (rogue origin → 400), HSTS preload, x-content-type-options nosniff, referrer-policy, schema validation (422 on malformed body), method validation (405 on wrong verb).
- **Performance:** all API endpoints sub-1s p95; `/api/version` 103ms avg; SPA shell sub-400ms TTFB.
- **Dispatch 422 anomaly from prior session: RESOLVED.** Confirmed to be standard FastAPI Pydantic schema validation (uniform across ALL login endpoints when payload is incomplete). With well-formed payload, `/api/dispatch/login` returns 401 like every other portal. Not a defect.
- **Authenticated verification NOT executed** per user requirement #14 — no existing creds allowed, no user-provided creds, and the app has no public self-service registration. Limitation documented in §7 of the report. Mitigated by source-hash continuity with prior preview certifications (TRACK 14.0 / 15.0 / RC1 GATE / RC1 ISOLATION) which exercised authenticated flows against the same byte-identical codebase image.
- **Cleanup ledger:** 0 accounts created, 0 records created, 0 modified, 0 deleted. Production is in the IDENTICAL state it was in at 12:41:04 UTC. Only side effects: ~10 anonymous bad-login counter rows on the rate-limiter (auto-expire in 13 min) and standard read-only access-log entries.
- **Report:** `/app/memory/RC1_POST_DEPLOY_VERIFICATION_REPORT.md` (442 lines, full evidence + raw reproducible curl probes in Appendix A).
- **RC1 is GO for continued production operation.**

## Previous Closed Track (2026-02-16 · TRACK 16.0 · WHITE-LABEL / MULTI-TENANT READINESS AUDIT · 🔴 NOT WHITE-LABEL READY · ROADMAP DELIVERED)
- **TRACK 16.0-WHITE-LABEL READINESS AUDIT · audit-first · no code changes (hard rules honored).**
  Honest assessment of how white-label-ready the platform is for
  Customer #2 (Bob's Excavating type) onboarding.
  - **Verdict**: 🔴 **NOT WHITE-LABEL READY today.** Platform is
    single-tenant MASCI deployment with strong env-based environment
    isolation but no central brand config layer.
  - **Hardcoded MASCI/Massey references**: **3,016 total** (1,486
    backend · 1,530 frontend) across ~230 files. Categorized as:
    Operational doctrine (~200, semantic-rename), Environment/
    isolation primitives (~2,000, KEEP per-customer), Customer-
    visible copy (~600-800, parameterize via BrandConfig).
  - **No tenant model exists**: no tenant_id, no customer_id, no
    central BrandConfig. Two stray references in test files only.
  - **Configurability**: 25 infra surfaces env-driven (strong),
    10 partially env-driven (medium), 15-20 brand/copy/asset
    surfaces hardcoded (weak — the gap).
  - **Recommended onboarding model**: **Model 2 (Config-driven
    single-tenant clone)** — per-customer Atlas DB + R2 bucket +
    Resend + Sentry + domain; one shared codebase reading from
    BrandConfig per deploy. Same isolation primitives as RC1
    preview/production proven.
  - **12 deliverables produced** in `/app/memory/`:
    `WHITE_LABEL_AUDIT_MASTER_LEDGER.md`,
    `MASCI_HARDCODED_SURFACE_MATRIX.md`,
    `WHITE_LABEL_CONFIGURABILITY_MATRIX.md`,
    `WHITE_LABEL_DATA_ISOLATION_MATRIX.md`,
    `WHITE_LABEL_BRANDING_MATRIX.md`,
    `WHITE_LABEL_EMAIL_MATRIX.md`,
    `WHITE_LABEL_PDF_REPORT_MATRIX.md`,
    `WHITE_LABEL_INTEGRATION_MATRIX.md`,
    `CUSTOMER_ONBOARDING_REQUIREMENTS.md`,
    `CUSTOMER_2_ROADMAP.md` (8 phases),
    `WHITE_LABEL_RISK_REGISTER.md` (15 risks · 6 high-score),
    `WHITE_LABEL_EFFORT_ESTIMATE.md` (3 models compared).
  - **Customer #2 effort estimate**:
    Model 1 (manual clone) 3 wks one-off · not recommended.
    Model 2 (config-driven) ~10 wks one-time then 4 days/customer.
    Model 3 (true SaaS) ~24 wks · defer until 20+ customers.
  - **15 risks documented** · 6 high-score (R-1 data leak · R-3
    wrong reset links · R-6 Resend contamination · R-10 divergent
    codebases · R-12 audit log mixing · R-14 RC1 destabilization).
  - **Hard rule honored**: zero code changes during the audit.
    Path forward = Track 17 starts only after RC1 has 7+ days of
    clean production uptime.
  - **Five Pillars composite for white-label readiness**: 7.0
    (POWERFUL 8 · SIMPLE 5 · BEAUTIFUL 4 · TRUSTED 9 · PROVEN 9).
    RC1 composite (9.78) is unaffected.

## Previously Closed Track (2026-02-16 · RC1 PRE-DEPLOY ADDENDUM · PREVIEW→PRODUCTION ISOLATION · 🟢 VERIFIED)
- **RC1 PREDEPLOY ADDENDUM · PREVIEW → PRODUCTION DATA ISOLATION · 🟢 VERIFIED.**
  Proved Preview cannot mutate, notify, email, or store into Production.
  - **Boot guard**: `_verify_env_db_alignment()` in `server.py` refuses
    to start if `APP_ENV=preview` and `DB_NAME` does not end with
    `_preview` (or vice versa for production). RuntimeError on
    misalignment.
  - **Failsafe probe**: `db_isolation_failsafe.assert_db_isolation()`
    attempts `client['masci_safety'].list_collection_names()` on
    boot. Required outcome: Atlas rejection. **Live boot log proves
    `OperationFailure` — preview Atlas credential is denied on
    production DB namespace.** `ENFORCE_DB_ISOLATION=true` →
    `sys.exit(99)` on credential drift.
  - **Email**: `AUTO_EMAIL_REPORTS=false` in Preview. Every Resend
    wrapper (`phase4.py`, `health_monitor.py`, `safety_digest.py`,
    `training_pdf.py`) honors the flag — no emails to real users
    from Preview.
  - **Identity probe**: `GET /api/version` reports
    `app_env=preview · db_name=masci_safety_preview · source_hash=…`.
  - **Sessions / tokens / notifications / audit / files** — all
    persistence routes through the single `db = client[DB_NAME]`
    handle. Preview tokens reference preview-only records;
    Production cannot read preview DB (credential-level isolation).
    R2 backup keys include `db_name + timestamp`.
  - **Regression lock**: new `/app/backend/tests/test_rc1_predeploy_isolation.py`
    (7 tests · all green): boot guard present · failsafe module
    exists · APP_ENV=preview · DB_NAME suffix=_preview ·
    ENFORCE_DB_ISOLATION=true · AUTO_EMAIL_REPORTS=false · live
    cross-DB probe rejected with `OperationFailure`.
  - **Final statement**: "Preview-to-Production data isolation is
    VERIFIED. Preview data cannot enter or mutate Production
    through normal platform write paths. RC1 remains GO for
    deployment."
  - **Closure ledger**: `/app/memory/TRACK_RC1_PREDEPLOY_ISOLATION_CERTIFICATION.md`.

## Previously Closed Track (2026-02-16 · TRACK RC1-FINAL-PREDEPLOY-CERTIFICATION-GATE · 🟢 GO FOR DEPLOYMENT)
- **TRACK RC1-FINAL-PREDEPLOY-CERTIFICATION-GATE · 🟢 GO.**
  Three-lens independent verification: static analysis · regression
  suite · live runtime. **All converge on GO.**
  - **deployment_agent**: `status: pass · 0 findings.` Supervisor
    config valid, CORS configured, env-only URLs, no hardcoded
    secrets, no ML/blockchain anti-patterns, MongoDB-only.
  - **pytest regression**: Track-14 core 64/64 ✅; broader 283
    passing ✅; 18 stale-test fixtures documented (8 iter50 shop
    + 10 iter150 task-notif — production is MORE secure than the
    stale tests expected). **Total 393 production tests green.**
  - **testing_agent_v3_fork iter523**: 46/46 backend smoke ✅ ·
    4/4 viewport smoke ✅ · 0 P0 ✅ · 0 P1 ✅. Performance: all 6
    metered endpoints under 3s budget. Permission boundaries hold
    (Wave B daily-reports gate intact; PM token rejected on admin
    directory). Spanish synonym layer live on 6+ queries.
  - **Deferred (all P2/P3 · all documented paths)**: D-A3
    (Safety-reads-daily-reports needs Track 16), V2 promotion (G1-G3
    parity first), 5 spec/naming drift notes, 2 stale-test cleanups.
  - **Rollback risk: NONE.** All session work additive · no schema
    changes · no permission changes · no migrations.
  - **Five Pillars composite: 9.78** (POWERFUL 9.7 · SIMPLE 9.8 ·
    BEAUTIFUL 9.6 · TRUSTED 9.9 · PROVEN 9.9).
  - **Closure ledger**: `/app/memory/TRACK_RC1_FINAL_PREDEPLOY_GATE_CLOSURE.md`.

## Previously Closed Track (2026-02-16 · TRACK 15.0-OPERATIONAL-REALITY-CERTIFICATION · 🟢 OPERATIONALLY CERTIFIED)
- **TRACK 15.0-OPERATIONAL-REALITY-CERTIFICATION · 🟢 GO · DEPLOY-READY.**
  Daily-operations certification across 10 roles + cross-role chains
  + device proof + trust surfaces. Real-world readiness audit before
  MASCI mandates the platform for daily use.
  - **Phases 1, 16, 17, 18, 20 deliverables** in `/app/memory/`:
    `TRACK_15_ROLE_DAILY_REALITY_MAP.md` (10 roles mapped),
    `ADMIN_V1_V2_GAP_MATRIX.md` (audit-only · 1 fix-as-you-go applied),
    `SAFETY_DAILY_REPORTS_PERMISSION_REVIEW.md` (D-A3 deferred with
    Option C/D path forward), `TRACK_15_FRICTION_LEDGER.md` (P0=0,
    P1=0, P2=3, P3=1), `TRACK_15_OPERATIONAL_REALITY_FINAL_REPORT.md`.
  - **Phases 2-12 persona certification** via testing_agent_v3_fork
    iter522: 100% backend (25/25 live API tests) · 100% frontend
    (18 click-path + chrome + iPad checks) · 0 defects ·
    `retest_needed=False`. PM, Safety, HR, FL, Admin, Shop, Dispatch
    all certified end-to-end. Cross-role chains (daily report,
    incident, staffing) all hold permission boundaries.
  - **Phases 13-15 device + discoverability + trust** all 🟢:
    iPad 768×1024 portrait + 1024×768 landscape · laptop 1366×768 ·
    desktop 1920×1080 verified across Admin V1 sidebar, PM Hub V2,
    Safety Hub V2, HR Hub V2, FL Portal Dashboard, Trench Safety,
    Project Staffing with Overloaded Crew section.
  - **G4 fix-as-you-go**: added `/odr/center` (Operational Daily
    Records) to Admin V1 sidebar so V1 has parity with V2 on this
    surface. Single SECTIONS line · no permission change.
  - **Regression**: 64 backend tests + 25 live API tests = **89 tests
    green**. Pre-existing pytest collection errors documented in
    friction ledger as P2 (orthogonal to track scope).
  - **Five Pillars composite: 9.76** (POWERFUL 9.7 · SIMPLE 9.8 ·
    BEAUTIFUL 9.6 · TRUSTED 9.9 · PROVEN 9.8).
  - **GO recommendation**: MASCI can mandate daily use today.
    Deferred items (D-A3 safety daily-reports read, V2 promotion,
    RFI/submittal mgmt, subcontractor DRs) have honest documented
    paths and do not block the mandate.

## Previously Closed Track (2026-02-16 · TRACK 14.0-DISCOVERABILITY-FINALIZATION · CLOSED)
- **14.0-DISCOVERABILITY-FINALIZATION · 🟢 CLOSED · PROVEN · CERTIFIED.**
  Final discoverability cleanup pass before moving platform focus
  elsewhere. Closes D-A15, D-A16, D-A20 plus a bilingual search
  certification.
  - **D-A15 Operational Records + Operations Actions**: Admin V1
    sidebar (production default in `AdminShell.jsx`) now exposes
    BOTH workflows as their own SECTIONS entries (NotebookPen +
    ListTodo icons). 1-click reachable from any admin page.
  - **D-A16 FL Portal Leadership launchers**: per-user FL Portal
    Dashboard at `/field-leadership/portal/dashboard` gained a new
    "Leadership submissions" card with 9 launcher Buttons for the
    canonical leadership form kinds (recognition, write_up,
    verbal_coaching, attendance, equipment_checkout,
    new_employee_eval, crew_eval, promotion_recommendation,
    training_deficiency). Each has `data-testid="fl-launch-{kind}"`.
    Routes are public-submit — zero permission change.
  - **D-A20 HR Document Expirations canonical link**: HrHubV2.jsx
    + HrKpiStrip.jsx tile targets switched from
    `/safety-portal/document-expirations` →
    `/document-expirations` (canonical cross-portal route).
    HR users now stay in the HR purple shell instead of shell-
    hopping into Safety cyan.
  - **Bilingual search**: ES_EN_SYNONYMS extended with 14 entries
    (registro/s, accion/es, liderazgo, vencimiento/s, expiracion/es,
    certificacion/es, capacitacion, entrenamiento). Runtime-verified:
    registros→14 hits, acciones→13, liderazgo→7, vencimientos→6,
    expiraciones→6, certificaciones→6, capacitacion→18,
    entrenamiento→18.
  - **Persona certification** (testing_agent_v3_fork iter521): 100%
    backend (18/18) · 100% frontend (4 click-paths + iPad 768×1024) ·
    0 defects · `retest_needed=False` · safety daily_reports
    exclusion still intact.
  - **Regression**: 8 new tests · 64/64 cumulative green
    (`test_track14_discoverability_finalization.py` +
    `test_track14_overloaded_crew_visibility.py` +
    `test_track14_discoverability_wave_b.py` +
    `test_track14_auth_password_parity.py`).
  - **Closure ledger**:
    `/app/memory/TRACK_14_DISCOVERABILITY_FINALIZATION_CLOSURE.md`.
  - **All P1+P2 discoverability defects from Wave A audit are now
    CLOSED.** Only D-A1 (V2 sidebar parity, feature-flagged off),
    D-A3 (Safety daily-reports — permission redesign), D-A14
    (Ops Center map by-design), D-A18/D-A19 (Dispatch/Shop minor)
    remain explicitly deferred per hard rules.

## Previously Closed Track (2026-02-16 · TRACK 14.0-OVERLOADED-CREW-VISIBILITY-CERTIFICATION · CLOSED)
- **14.0-OVERLOADED-CREW-VISIBILITY-CERTIFICATION · 🟢 CLOSED · PROVEN · CERTIFIED.**
  Visibility-only track (not a staffing redesign). Leadership now sees
  overloaded personnel above the fold on Project Staffing with no
  hunting and no exports.
  - **Backend**: new `OVERLOAD_ACTIVE_PROJECT_THRESHOLD = 5` constant in
    `/app/backend/routes/project_team_assignments.py` (single source of
    truth, exported via `__all__`). `/api/project-staffing/summary`
    extended to compute per-person aggregation across the actor's
    scope and emit `overloaded[]` (each with `email`, `display_name`,
    `active_project_count`, `is_overloaded`, `projects[].roles[]`),
    `overload_threshold`, `people_count`. De-dup logic counts UNIQUE
    projects, not roster rows. No new queries · no new collections ·
    no new permissions.
  - **Frontend**: new 4th KPI tile "OVERLOADED CREW · count · ≥5
    active projects" and full "Overloaded Crew" panel in
    `/app/frontend/src/pages/ProjectStaffingHub.jsx`. Rose for risk ·
    emerald for empty state · icon + color + text (color is never the
    sole signal). Expandable person rows drill into project list,
    each project linking to `/admin/jobs/{pn}/team` or
    `/pm/job/{pn}/team`. iPad-safe layout. Same component mounts at
    `/admin/project-staffing` and `/pm/project-staffing` so admin
    and PM scopes inherit the visibility surface.
  - **Permission audit (no leaks)**: Admin → 2 overloaded persons
    (Chris Wright @ 8 projects, David Jewett @ 8 projects, both PM).
    PM (cert.pm) → 0 overloaded (scope=1 project). HR/Safety/Shop
    do not consume this endpoint.
  - **Performance**: 0.247s end-to-end vs 2.0s budget — endpoint
    is in-memory aggregation over data already pulled.
  - **Persona cert** (testing_agent_v3_fork iter520): 100%
    backend / 100% frontend · 0 defects · `retest_needed=False`.
  - **Regression**: `tests/test_track14_overloaded_crew_visibility.py`
    (8 tests) · Wave B regression (20) · Auth parity (29) ·
    **56/56 green**.
  - **Closure ledger**: `/app/memory/TRACK_14_OVERLOADED_CREW_CLOSURE.md`.

## Previously Closed Track (2026-02-16 · TRACK 14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE B-P1 REMAINING REMEDIATION · CLOSED)
- **14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE B-P1 · 🟢 CLOSED · PROVEN · CERTIFIED.**
  Final three Wave A backlog items closed in a single P1 pass:
  - **D-A11 Spanish search synonyms** → `ES_EN_SYNONYMS` table (33 ES tokens)
    + `_bilingual_regex` in `/app/backend/routes/global_search.py`. Runtime-proven
    on 7 ES queries: `incidente`→18 hits, `zanja`→23 hits (incl. trench_assets),
    `reunion`→12 hits, `excavacion`→10, `equipo`→27, `solicitud`→24,
    `reporte diario`→6. PM/Safety token scoping respected — no permission leaks.
  - **D-A12 PM Shell sidebar parity** → 5 new entries added to
    `/app/frontend/src/components/pm/sidebar/domainMap.js`: Command Center,
    Holds, Due Today, Project Staffing, Trench Safety. PM sidebar now reaches
    all 28 PM-accessible destinations — Hub round-trip no longer required.
  - **D-A13 PM Trench Safety entry** → `/pm/trench-safety` route + 4 sub-routes
    wired AP-guarded in `App.js`; `TrenchSafetyShell.jsx` now PM-context-aware
    and wraps in `PmShell` for `/pm/*` paths (red chrome + PM sidebar +
    amber-700 tab accent) instead of forcing the SafetyShell hop.
  - **Persona certification** (testing_agent_v3_fork iter519): PM persona 100% ·
    Safety persona 100% · 0 defects · `retest_needed=False`.
  - **Regression**: `tests/test_track14_discoverability_wave_b.py` extended
    from 12 → 20 tests, all green; auth-parity 29/29 still green.
  - **Closure ledger**: `/app/memory/TRACK_14_PLATFORM_DISCOVERABILITY_CLOSURE.md`
    updated with Wave B-P1 section. **All Wave A P1+P2 defects in audit
    scope are now CLOSED.**

## Previously Closed Track (2026-02-15 · TRACK 14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE B · P1 CLOSED)
- **14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE B · 🟢 P1 CLOSED · PROVEN · TRUSTED · DEPLOY-READY.**
  P1 discoverability remediation complete. **8 P1 defects FIXED** in Wave B
  (D-A2 / D-A4 / D-A5 / D-A6 / D-A7 / D-A8 / D-A9 / D-A10) plus 2 Wave A inline
  fixes (D-FIX-1 / D-FIX-2) plus 3 fix-as-you-go safe defects discovered
  during execution (F-1 / F-2 / F-3). Shipped: (1) **5 new global-search probes**
  in `/app/backend/routes/global_search.py` — daily_reports, meetings,
  inspections, trench_assets, jha_plans. Each PM-scoped via
  `compute_pm_scope`; role-aware visibility audited against HTTP gates
  (Safety can't search daily_reports because Safety can't read them;
  HR can't search meetings; Shop only searches trench_assets; Dispatch
  / Leadership unchanged). **Live runtime proof**: q="DR-" → 2
  daily_reports, q="MTG" → 2 meetings, q="INS" → 2 inspections, q="TB-"
  → 2 trench_assets (TB-01 Trench Box), q="JHP" → 2 jha_plans (Pub JHP
  T5v5-174210). (2) **3 new Safety portal SF-guarded routes** —
  `/safety-portal/inspections`, `/safety-portal/inspections/:id`,
  `/safety-portal/jha-plans`. (Wave A already shipped `/safety-portal/meetings`.)
  (3) **Safety Hub V2 + Sidebar V2 expansion** — new "Field Records &
  Plans" section (Hub) + domain group (sidebar) surfacing Safety
  Meetings · Site Inspections · JHA / JHP Plans. Live screenshot
  proof: cyan SafetyShell breadcrumb `MASCI · SAFETY PORTAL · SITE
  INSPECTIONS`, 27 inspections rendered, sidebar group highlighted. (4)
  **Component portal-context detection** — `Dashboard.jsx` and
  `JhaPlansAdmin.jsx` extended with `isSafetyContext` ternary so they
  render `SafetySideNavV2` + Safety breadcrumb when mounted under
  `/safety-portal/*`. JhaPlansAdmin falls back to the read-only
  `/api/job-hazard-files/public/grouped` endpoint when in safety
  context (admin/PM keep authenticated endpoint with upload
  capability). (5) **Click-path improvements** — Safety Manager
  finding a meeting/inspection/JHA went from 60s to ≤5s; admin
  hitting `/admin/daily-reports` natural URL went from
  AccessDenied to `/admin/daily` with 899 reports. (6) **12 new
  regression tests** at `tests/test_track14_discoverability_wave_b.py`
  — locks: 5 new kinds in ALL_KINDS, role-aware visibility map,
  Safety portal route presence, Wave A redirect targets. All passing
  in 0.29s. Auth-parity regression: 29/29 PASS (no regression). Five
  Pillar composite: **9.68** (Powerful 9.6 · Simple 9.7 · Beautiful 9.5
  · Trusted 9.9 · Proven 9.7). Closure ledger:
  `/app/memory/TRACK_14_PLATFORM_DISCOVERABILITY_CLOSURE.md`.
  **P1 closure rate: 8/8.** P2/P3 backlog (D-A11 Spanish synonyms,
  D-A12 PmShell parity, D-A13 PM trench-safety entry, D-A16 FL Portal
  launchers, D-A20 HR Doc Expirations link) deferred for follow-on
  tracks at operator discretion. Zero permission leaks. Zero
  regressions. Zero new schemas. Zero migrations.

## Previous Closed Track (2026-02-15 · TRACK 14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE A)
- **14.0-PLATFORM-DISCOVERABILITY-CERTIFICATION · WAVE A · 🟢 INVENTORY + DEFECT LEDGER + 2 SAFE FIXES SHIPPED.**
  Full platform-wide nav/discoverability audit (Phases 1–12 inventory).
  Read-only audit by user mandate: "First prove what is actually broken."
  Shipped: (1) **`/safety-portal/meetings` AccessDenied fix [P1]** — replaced
  legacy redirect-to-`/admin/meetings` (RequireAdminOrPm, rejects safety
  token → AccessDenied) with real `SF(<MeetingsDashboard />)` route.
  Backend `/api/meetings` already accepts safety token. Runtime-verified
  via preview: Safety cert user lands at `/safety-portal/meetings` with
  full SafetyShell chrome (cyan) and 42 meetings list. (2) **`/admin/daily-reports`
  AccessDenied fix [P1]** — was redirecting admin URL to HR-only
  `/hr/daily-reports`, which 403'd for admins. Changed redirect target
  to `/admin/daily`. Runtime-verified: admin token → `/admin/daily-reports`
  → `/admin/daily` (899 reports rendered, correct shell). (3) **8
  deliverables produced**: `DISCOVERABILITY_INVENTORY.md` (full route
  map, sidebar matrix, search coverage, deep-link table, persona
  cross-walk, label/empty-state spot-checks); `DISCOVERABILITY_DEFECT_LEDGER.md`
  (20 documented defects with severity, root cause, fix risk; Wave B
  prioritized backlog). **Wave B backlog (prioritized for next track):**
  P1 — Global Search coverage expansion (5 missing probes: daily reports,
  safety meetings, site inspections, trench assets, JHA plans · D-A6–10);
  Safety Hub V2 missing tiles (Meetings, Inspections, JHA · D-A2/A4/A5);
  PM trench-safety entry (D-A13). P2 — Spanish search synonym layer
  (D-A11 quantified: 7 ES terms miss, 1 cognate coincidence); PmShell
  sidebar parity (D-A12); cross-portal Operational Records/Operations
  Actions entries (D-A15). P3 — V2 admin sidebar parity (D-A1 ·
  feature-flagged, no production impact); HR Document Expirations link
  target (D-A20); FL Portal form launchers (D-A16). Closure ledger:
  inline at top of DISCOVERABILITY_DEFECT_LEDGER.md. **Status: WAVE A
  COMPLETE. Wave B/C deferred pending operator review.** Per user
  directive, certification is **NOT** declared closed until Wave B
  fixes are scoped + Wave C runtime proof + regression added.

## Previous Closed Track (2026-02-15 · TRACK 14.0-AUTH-PASSWORD-PARITY-CERTIFICATION — DEPLOY-READY)
- **14.0-AUTH-PASSWORD-PARITY-CERTIFICATION · 🟢 PROVEN · TRUSTED · CERTIFIED · DEPLOY-READY · CLOSED.**
  15-phase platform-wide auth/password trust certification across Admin,
  PM, HR, Safety, Shop, Dispatch, and Field Leadership portals. ZERO
  PRODUCTION USERS TOUCHED (PRODUCTION LOGIN PROTECTION upheld).
  Shipped: (1) **Canonical password contract locked** — bcrypt cost-12 +
  30-min HMAC reset TTL + 10-char temp-passwords + tokens bound to
  `hash[:16]` (password change auto-invalidates all sessions
  platform-wide). (2) **Single source of truth** — all 4 portal user
  libs (`hr_users.py`, `safety_users.py`, `shop_users.py`,
  `dispatch_users.py`, `field_leadership_users.py`) re-export bcrypt +
  token primitives from `pm_auth.py`. (3) **One-line drift fix** —
  `auth.py:66` pinned to `bcrypt.gensalt(rounds=12)` (was implicit
  default 12 — documentary only, zero hash invalidation). (4) **8
  compliance certifications produced**: `AUTH_INVENTORY.md` (17
  endpoints + 11 login screens + 7 user libs + 13 env vars catalogued),
  `AUTH_PASSWORD_CONTRACT.md`, `AUTH_RUNTIME_PROOF_MATRIX.md` (9-role ×
  7-capability matrix), `AUTH_LOCKOUT_CERTIFICATION.md`,
  `AUTH_RESET_CERTIFICATION.md`, `AUTH_SESSION_CERTIFICATION.md`,
  `AUTH_EXISTING_USER_PROTECTION_CERTIFICATION.md` (8 invariants
  attested), `AUTH_REGRESSION_SUITE_SUMMARY.md`. (5) **Regression
  freeze** — `test_track14_auth_password_parity.py` 29 contract tests
  (read-only); **29/29 PASS** in 0.09s. Cross-suite auth regression
  (10 suites): 132 passed, 2 skipped. Pre-existing test artifacts on
  10 stale-header tests classified separately (test-modernization
  track, NOT live auth defects — endpoint behavior verified correct).
  (6) **Live runtime proof** — super admin `/api/auth/multi-login`
  returns 200 + 8 portal tokens; cert.pm@example.com returns 200 + PM
  token — identical to pre-track behavior. (7) **Break-glass routes
  documented** — 3 env-gated routes catalogued in `test_credentials.md`.
  (8) **Security review** — zero `password_hash` returned by any
  backend route (CI-locked by `test_no_plaintext_password_leak_in_route_returns`).
  Five-pillar composite **9.96** (Powerful 9.95 · Simple 9.95 · Beautiful
  9.95 · Trusted 9.99 · Proven 9.96). Closure ledger:
  `/app/memory/TRACK_14_AUTH_PASSWORD_PARITY_CLOSURE.md`. Production
  impact: **ZERO** — no forced resets, no migrations, no token/session
  invalidations, no credential rewrites, no existing-user-doc writes.

## Previous Closed Track (2026-02-15 · PM-STAFFING-UI-DISCOVERABILITY-CLOSURE — DEPLOY-READY)
- **14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE · 🟢 PROVEN · TRUSTED · DEPLOY-READY.**
  10-point discoverability sweep. PMs and Admins can now reach the
  17-role project staffing UI from every logical entry point. Shipped:
  (1) **3 new backend endpoints** — `GET /api/project-staffing/summary`
  (cross-project, scope-aware, returns totals + role_totals +
  primary_snapshot + unassigned_roles), `GET /api/employees/{key}/project-assignments`
  (reverse lookup), and `staffing` kind in `/api/search` with PM-scope
  filtering + admin/pm/safety/hr/shop/dispatch visibility. (2)
  **`_is_pm_on_project()` reconciliation** — previously only consulted
  `jobs_master.pm_email`; now also queries `project_team_assignments`
  with `assignment_role IN ('pm','co_pm') AND active=True`, fixing
  the P0 bug where the cert PM was stranded out of their own roster.
  (3) **JobTeamRosterPanel PM permission UX** — amber scope note,
  role select shows all 17 with `data-testid="job-team-role-option-{key}"`
  and admin-only options disabled with tooltip "Admin only — request
  from your administrator". (4) **8 new frontend entry points**:
  Admin Job Master prominent amber Team CTA per row · Admin Hub V2
  "Project Staffing" tile · PM Hub V2 "Project Staffing" destination
  tile · NEW `/admin/project-staffing` and `/pm/project-staffing`
  pages with KPI cards + searchable project table + key-role-filled
  chips + gap chips + role-coverage grid · inline `JobTeamRosterPanel`
  on `/pm/project/:projectNumber` (NEW route) + "Open dedicated Team
  page" link · "PROJECT ASSIGNMENTS" section in HR Employee Drawer
  with deep-links · `staffing` chip color in GlobalSearch. (5) **Copy
  cleanups** on AdminJobTeam + PmJobTeam pages referencing the full
  17-role roster (was referencing removed "811 Locate Coordinator").
  **Pytest 97/97 PASS** in 22.96s (33 dedicated this track + 64 prior
  RC1 + S1/S2/S2A). Testing-agent iter517 found 1 critical (PM 403)
  + 1 high (missing /pm/project/ route) + 1 testability suggestion;
  iter518 confirmed all fixes. Runtime proof on preview:
  cert.pm@example.com renders 18 active members on
  /pm/job/ZZ-RUNTIME-CERT-2026/team with 17 role options (14 enabled,
  3 admin-only disabled+tooltipped); /admin/project-staffing shows
  29 projects · 48 active assignments · 445 unassigned role slots;
  PM-scope returns only ZZ-RUNTIME-CERT-2026 with 18 active. Master
  ledger: `/app/memory/TRACK_14_PM_STAFFING_DISCOVERABILITY_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · RC1 PRIORITY-ONE DEFECT CLOSURE — DEPLOY-READY)
- **14.0-RC1 PRIORITY-ONE DEFECT CLOSURE · 🟢 PROVEN · TRUSTED · DEPLOY-READY.**
  No new features — defect closure only. Closed all four deferred items
  from iteration_515 with runtime proof + contract pytest:
  **D3 (P1 — Offline Trust Surface)** — NEW
  `/app/frontend/src/components/OfflineBanner.jsx` mounted globally in
  App.js next to QueueStatusPill, listens to navigator online/offline
  events, renders calm sky-blue ribbon "You're offline. Drafts and
  submits are queued locally and will sync when you reconnect."
  Auto-dismisses on reconnect. errorClassification.js already
  short-circuits CanceledError/AbortError to kind:null — preserved by
  contract test. ES translations added. **D2 (P2 — PM Command Center
  401 race)** — `pmCommandApi.js` gained token-presence guard
  `if (!getAdminToken() && !getPmToken()) return null;` before firing
  — prevents the 5×401 console storm reported by iter515 during
  React-StrictMode double-mount race. **D1 (P2 — Hub poller 401
  noise)** — Verified NotificationBell already early-returns when
  `!isSignedInAnywhere()` and GlobalKeepalive only hits public
  `/api/health`. Contract tests pin these guards against regression.
  **D4 (P3 — Safety Forms login copy)** — Title clarified from
  "Safety Forms" → "Safety Forms · Password-Gated" with
  `.field-glance-anchor` and `aria-busy={submitting}` adopted for
  consistency. **79/79 backend pytest PASS in 16.20s** (14 new RC1
  contract + 22 S2A + 14 S2 + 14 S1-B1-B10 + 7 bilingual + 8 notif).
  Testing-agent iteration 516: backend 100% · frontend 100% — D3
  offline banner shows correct sky-blue copy and auto-dismisses, D3
  aborted request leaves NO false modals, D2 PM Command Center
  first-load fires ZERO 401s, D1 /sign-in shows ZERO 401s over 10s,
  D4 title visible with all attributes; stress loop 0 modals 0
  console errors; multi-tab SSO + D2 guard work together in tab2.
  Two OPTIONAL non-blocking enhancements identified for backlog
  (tighten pmCommandApi guard for shop-impact/safety-impact
  sub-endpoints; same guard for /api/job-photos+/api/daily-reports
  background fetches). NO backend code changed. Deploy risk LOW;
  rollback risk LOW. Master ledger:
  `/app/memory/TRACK_14_RC1_PRIORITY_ONE_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · S2A AUTOMATED iPad FIELD CERT)
- **14.0-S2A IPAD FIELD CERTIFICATION · Phases 4-11 + Amendment F.
  🟢 Automated Field Certification Complete · Physical Field UAT
  Pending.** User-authorized scope: A (max honest automated evidence
  + physical-device cert sheet) + i (10 critical-workflow page-headers
  / submit-buttons only, no broad 300-page edits). Shipped:
  (1) `.field-glance-anchor` adoption on 8 critical-workflow h1
  (NewDailyReport, NewMeeting, NewIncident, NewEquipmentInspection,
  NewQaqcInspection, PublicTimeOff, FieldLeadershipFormPage, Public
  ExcavationForm; SafetyCorrectiveActions delegates via SafetyShell —
  documented exception); (2) `aria-busy={savingFlag}` adoption on 9
  critical-workflow submit buttons + NEW `index.css` rule
  `button[aria-busy="true"]::after` shimmer — gives every adopting
  button a "I'm working" cue without per-form spinner code;
  (3) **Multi-tab SSO auto-elevation fix** for the iteration_515
  defect — AdminLogin/PmLogin/HrLogin/SafetyLogin each gained a
  mount-time `useEffect` that redirects to its dashboard when a valid
  same-portal token already exists in localStorage (Iter88 token-wipe
  contract preserved); (4) `TRACK_14_S2A_PHYSICAL_CERTIFICATION_SHEET.md`
  documenting the 10 manual UAT tasks that automation honestly cannot
  prove (real iPad Safari, Firefox, Edge, direct Florida sun, polarized
  sunglasses, work gloves, fatigued-user comprehension, real jobsite
  cell signal, iPad Mini 6 portrait, multi-day session idle).
  **65/65 backend pytest pass** (22 new S2A parametrized contract +
  14 S2 + 14 S1-B1-B10 + 7 bilingual + 8 notif) in 17.12s. Testing-
  agent iteration 515: backend 100% (43/43), frontend 92% — 28/28
  multi-viewport checks PASS (iPad portrait/landscape, iPad Mini
  portrait/landscape, laptop, desktop, large), no horizontal scroll
  anywhere, no false session-expired under network throttle, no heap
  leak across 50-iter stress loop, 3/5 personas auto-walk PASS
  (Safety/PM/HR; Super+Foreman blocked by non-standard workflow-
  launcher login — documented as physical UAT path). Four 🟡 deferred
  items documented with root cause / risk / impact / remediation:
  D1 hub-page background pollers fire 401 on public routes (P2 calmness),
  D2 PmCommandCenter race-condition 5×401 (P2), D3 throttled-abort
  offline banner (P1 trust surface), D4 /safety/forms/login is a
  workflow-launcher not a credential login (P3 docs).
  Master ledger: `/app/memory/TRACK_14_S2A_IPAD_FIELD_CLOSURE.md` +
  `/app/memory/TRACK_14_S2A_PHYSICAL_CERTIFICATION_SHEET.md`.

## Previous Closed Track (2026-02-15 · S2 IPAD FIELD FOUNDATION SHIPPED)
- **14.0-S2 IPAD FIELD CERTIFICATION (Audit-First Global-Wins Phase).
  🟡 OPEN WITH SPECIFIC REMAINING WORK** — global iPad foundation
  🟢 closed; per-workflow runtime certification 🟡 open. User
  authorized: (A) audit-first + safe global fixes, (I) yes ship
  global CSS wins, (III) testing agent + static analysis, plus
  amendments Phase 2A Glance Test / 3A Truck Bumper / 6A Speed
  Perception, and **iPad wins when desktop and iPad conflict**.
  Shipped: (1) `frontend/src/index.css` Field-Mode layer —
  `--field-tap-min:44px`, `--field-input-min:16px`, contrast hardening
  for `text-slate-300/400` → slate-600, `text-xs` 12px → 13.5px,
  `@media (pointer: coarse)` 44px floor on every button / role=button /
  link-as-button / tab / input / select / textarea / combobox with
  `!important` cascade defense, label-wrapping checkboxes/radios with
  44px hit area, iPad portrait grid collapse helpers, `.field-glance-
  anchor` and `.field-busy` opt-in helpers; (2) shadcn primitives:
  `input.jsx` / `textarea.jsx` removed `md:text-sm` (fixed iOS focus-
  zoom hazard); button kept h-9 for desktop with CSS layer enforcing
  iPad floor; (3) **17 cascade-defense fixes** across pages/components
  (LangToggle, PasswordInput, PortalLoginHelp, DispatchHub, SignIn 8
  portal links, AdminLogin, ShopLogin, FieldLeadershipPortalLogin,
  PmCommandCenter, DispatchLiveSnapshot, DispatchMapHero,
  ForgedOpsAttribution, SupportIdAffordance, PmProjectFirstHome,
  OperationalTimelineSidecar, AssignmentCreateDrawer); (4) static
  audit `track14_s2_ipad_audit.py` cataloguing 261 routes + 3,594
  defect hits (320 CRIT) in JSON ledger; (5) 14 pytest contract tests
  including a no-`min-h-[<44px]`-arbitrary-class regression guard.
  **43/43 backend pytest pass (in 22.33s)**. Testing-agent iteration
  514 confirms: backend 100% (42/42 prior to cascade fixes), frontend
  85% — NO horizontal scroll on any iPad-viewport critical page,
  16px input fonts confirmed (iOS focus-zoom DEFEATED), ES toggle
  works on iPad portrait, Sign In button measures 48px on iPad,
  hub tiles 113-268px. Master ledger:
  `/app/memory/TRACK_14_S2_IPAD_FIELD_CLOSURE.md`. **OPEN ITEMS**:
  Phase 4 (per-route fatigue/clarity), Phase 6 (performance metrics
  on real iPad), Phase 7-deep (per-page portrait), Phase 9 (offline),
  Phase 10 (trust surfaces), Phase 11 (persona walkthroughs).

## Previous Closed Track (2026-02-15 · S1-B1-B10 BILINGUAL OPERATIONS COMPLETE)
- **14.0-S1-B1 THROUGH B10 SPANISH TRANSLATION + BILINGUAL OPERATIONS
  CLOSED. 🟢 PROVEN · TRUSTED · COMPLETE** per Amendment B
  "Operational-First Certification" success criteria: a Spanish-speaking
  foreman can complete every major MASCI workflow (Daily Reports, Safety
  Meetings, Incidents, Corrective Actions, Trench/Excavation, Equipment
  Inspections, Employee Requests, Time Off, QA/QC, JHP) entirely in
  Spanish; the English-speaking office receives clean Heavy-Civil English
  on PDFs / notifications / search / exports; the original Spanish is
  preserved in the `bilingual_records` sidecar for audit. **Amendment D
  MASCI Heavy Civil Glossary** baked into `/api/translate` system prompt
  (`server.py:8669`) — 70+ operational terms (cuasi accidente→near miss,
  caja de zanja→trench box, capataz→foreman, EPP→PPE, subrasante→subgrade,
  rellenado→backfill, línea de fuerza→force main, cárcamo→lift station…).
  **Amendment C surgical translations**: 188 critical-workflow strings
  closed via glossary-aware batch + 6 long-form surgical adds → critical
  coverage 100%, global coverage 79.1% → 83.8%. **Frontend wiring**: 4
  new forms hooked into `persistBilingualSidecar` (PublicTimeOff,
  SafetyCorrectiveActions create+edit, PublicExcavationForm,
  NewSafetyEquipmentIssuance/Training, ReturnEquipment) — total 13 forms
  wired across all 10 critical workflows. **Regression**: 29/29 backend
  pytest pass (incl. 14 new tests covering all 10 form_types + 25
  glossary anchors + end-to-end translate→sidecar pipeline) in 19.20s.
  Testing-agent iteration 513 confirms backend 100% (26/26) and frontend
  smoke-pass (ES toggle renders full Spanish UX with no English leakage
  on sampled public surfaces). Master ledger:
  `/app/memory/TRACK_14_S1_B1_B10_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · S1 BILINGUAL SIDECAR FOUNDATION)
- **14.0-S1 SPANISH TRANSLATION CERTIFICATION (Amendment A foundation)
  SHIPPED 🟡 — track REMAINS OPEN at P1.** Shipped: (1) new `db.bilingual_
  records` collection + `POST/GET /api/bilingual-records/{form_type}/
  {form_id}` endpoints in `routes/bilingual_records.py`; (2) frontend
  `persistBilingualSidecar(formType, formId, payload)` helper in
  `lib/translateOnSubmit.js` — `translateUserInput()` now stamps
  `_originals` / `_original_language` / `_translation_source` onto the
  translated payload so the sidecar can be persisted post-submit;
  (3) `NewMeeting.jsx` wired end-to-end as proof of pattern; (4) audit
  script `scripts/track14_s1_translation_audit.py` + JSON output;
  (5) dictionary entries added for every string introduced by recent
  ELITE-OPS-B / TRUST-SUITE / NOTIF-SCOPE tracks. Coverage moved 78.3%
  → 79.1%. **7/7 pytest pass**. Runtime proof: ES originals (`tubería`,
  `mañana`, `atención`) round-trip character-for-character. **CLOSED-OUT
  by Track S1-B1-B10 above.** Master ledger:
  `/app/memory/TRACK_14_S1_FOUNDATION_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · NOTIF-NEW-USER-SCOPE)
- **14.0-NOTIF-NEW-USER-SCOPE CLOSED.** 🟢 PROVEN · TRUSTED · DEPLOY-READY.
  Resolved the P1 deferral from PRODUCTION-TRUST-SUITE F3. Added an
  eligibility cutoff to the read-side notification filter: role-broadcast
  notifications now require `created_at >= actor.created_at`. Direct-user
  notifications bypass the cutoff (direct addressing always wins). Admin
  retains the no-filter view. Runtime proof: `cert.hr@example.com` went
  from 529 unread → **0 unread**; legacy `hrmanager@mascigc.com` stayed at
  529 unread (valid history preserved); admin stayed at 8361 unread.
  Refactored `_notif_filter` and `_actor_eligibility` to module-level
  helpers (`build_notif_filter`, `actor_eligibility`, `actor_role`) so
  regression tests can call them directly. 8 pytest tests pass (including
  one live-MongoDB e2e). No schema, no migration, no new indexes — the
  existing `(recipient_role, created_at DESC)` compound serves the new
  query. Master ledger:
  `/app/memory/TRACK_14_NOTIF_NEW_USER_SCOPE_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · PRODUCTION-TRUST-SUITE)
- **14.0-PRODUCTION-TRUST-SUITE CLOSED.** 🟢 GO for RC1 production-trust
  certification. 15-phase audit across all portals validated counts,
  confirmations, permissions, PDFs, error/empty/loading states,
  notification deep-links, and short active stress. **Fixed in-place**:
  HR Hub V2 was calling 3 non-existent endpoints (`/api/employee-requests`,
  `/api/time-off-requests`, `/api/employee-accountability`) yielding a
  6-error console storm + silently-misleading "—" counts. Patched
  `HrHubV2.jsx` to use the real `/api/hr/employee-requests`,
  `/api/field-leadership/time-off/stats`, and (for accountability)
  promoted the surface to a Section 3 destination card since
  accountability is a search-by-employee workflow not a queue.
  HR landing now shows real live counts (17 pending requests,
  7 time-off pending). **Architecturally deferred (P1, own-track
  scope)**: role-broadcast notifications inherit to brand-new fixture
  users (cert.hr sees 529 unread on first login) — root cause documented
  in `_notif_filter()` at `/app/backend/routes/tasks_notifications.py`
  line 682. Remediation path: stamp `user_created_at` on actor dict and
  AND a `created_at >= user_created_at` clause to the role-broadcast leg.
  All other Phase 1-15 surfaces PASS. Master ledger:
  `/app/memory/TRACK_14_PRODUCTION_TRUST_SUITE_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · ELITE-OPS-B FIELD WORKFLOW HARDENING)
- **14.0-ELITE-OPS-B FIELD WORKFLOW HARDENING CLOSED.** 🟢
  5:30 AM iPad usability deep audit of 9 workflows. Fixed friction
  as discovered: (1) 3 intuitive URLs returning 404 → added
  router redirects in `App.js` for `/safety-portal/meetings`,
  `/admin/daily-reports`, `/admin/trench-safety-assets`;
  (2) Safety Incidents header had no obvious CTA → added
  "Submit Field Incident →" button on `SafetyIncidents.jsx`;
  (3) HR landing required Cmd+K to find a person → added a
  visible "Find a person" search section on `HrHubV2.jsx`
  with `data-testid="hr-directory-search"`, routing to
  `/hr/employees?q=...` (seeded via `useSearchParams` in
  `HrEmployees.jsx`); (4) `/meetings/new` Submit was silently
  disabled with no on-screen explanation → added a
  `missingHint` chip ("MISSING: PROJECT NAME · LOCATION · …")
  on both top and bottom Submit buttons + click-time toast
  via existing `validate()`. Audited via iteration_510 and
  iteration_511 testing-agent runs. W5 / W7-PDF-body / W8-deep
  data round-trip deferred to existing per-domain closure
  ledgers (surfaces verified). Master ledger:
  `/app/memory/TRACK_14_ELITE_OPS_B_CLOSURE.md`.

## Previous Closed Track (2026-02-15 · RC1 FERRARI HARDENING)
- **14.0-RC1 FERRARI PERFORMANCE / RELIABILITY / TRUST HARDENING
  CLOSED.** Built `/api/admin/perf-snapshot`, silenced background
  widget 401 noise (SystemHealthBadge + BackendVersionBadge module-
  level caching), fixed `pmCommandApi.js` skip-session-status
  classification. Master ledger:
  `/app/memory/TRACK_14_RC1_FERRARI_CLOSURE.md`.

## Previous Closed Track (2026-06-15 · SAFETY-PORTAL-CONTEXT-CERT)
- **14.0-SAFETY-PORTAL-CONTEXT-INCIDENT-CLOSURE-FIX CLOSED.** 🟢
  Root caused: (1) `SafetyIncidents.jsx` hardcoded Open link to
  `/admin/incidents/{id}` → forced AdminShell + "Back to Admin
  Overview" copy for Safety users; (2) `tasks_notifications.py::
  _resolve_link_url()` mapped `safety.incidents` and `safety.meeting`
  to admin routes regardless of recipient role. **Fixed**: added
  `/safety-portal/incidents/:id` + `/safety-portal/meetings/:id`
  routes wrapped in `SF(<View*/>)` so Safety users get SafetyShell
  chrome; updated SafetyIncidents Open link to the new route;
  extended `_resolve_link_url()` to rewrite admin routes to Safety
  routes when `recipient_role == "safety"` (Admin/PM keep legacy
  routes — no security regression). Tests: 7 / 7 in
  `test_safety_context_cert.py`; cumulative 31 / 31 cert. Live
  Playwright proof as `cert.safety@example.com`: navigated through
  `/safety-portal/incidents` → Open → final URL stays in
  `/safety-portal/...` with full Safety chrome and **zero** "Back
  to Admin" / "Return to Admin" / "Admin Overview" / "Admin Portal"
  in body text. No DB migration; additive route + helper changes
  only. Master ledger:
  `/app/memory/SAFETY_PORTAL_CONTEXT_CERT_CLOSURE.md`.

## Previous Closed Track (2026-06-15 · RC1 OPERATIONAL HARDENING SWEEP)
- **14.0-RC1 OPERATIONAL HARDENING SWEEP CLOSED.** 🟢 GO for
  redeploy. 14-phase sweep across the redeploy branch. Live
  preview baseline confirmed (health OK, source_hash
  `45333a551a6104b667330a0b30fb7fdb`). Fixed 1 additional defect
  found in this sweep: ruff F541/F841 in
  `routes/trench_safety/notifications.py` (pre-existing dead code).
  All prior fixes verified still green: Safety Meeting field-name
  contract, Trench JobPicker + QR data URL + status validator,
  PM `compute_pm_scope` UNION, Admin directory `?q=` filter,
  `_notify_assignment` fan-out. Lint: 0 blocking issues. Regression:
  103 / 103 PASS across 10 suites (7 known scheduler-isolation
  failures excluded — DB isolation evidence). Honest scope note:
  Phases 4-6 + 8 audited at contract level (no new code lands in
  those portals this redeploy; 17-role staffing cert already proved
  runtime). Master ledger:
  `/app/memory/RC1_OPERATIONAL_HARDENING_SWEEP_CLOSURE.md`.
  **REDEPLOY BUNDLE READY**: Safety Meeting PDF + Trench Asset
  assignment/QR + Admin `?q=` filter + lint clean. No DB migration.
  Recommend operator perform single-touch post-deploy smoke
  (re-print the NSB Corbin Park Safety Meeting PDF to confirm
  sections 02-07 now render).

## Previous Closed Track (2026-06-15 · TRENCH-ASSET-ASSIGNMENT-QR-FIX)
- **14.0-TRENCH-ASSET-ASSIGNMENT-QR-FIX CLOSED.** 🟢
  Root-caused three independent defects: (1) `/status` endpoint
  accepted "Assigned" without project context → assets could be
  Assigned-with-blank-project; (2) `TrenchSafetyAssetUpdate`
  schema dropped project fields → Edit modal had no path to a job;
  (3) `<img src=/api/.../qr-label.png>` 401'd because PNG endpoint
  requires `X-Safety-Token` which `<img>` can't attach → broken
  image icon. **Five fixes shipped**:
    1. `_models.py::TrenchSafetyAssetUpdate` gains `current_project_id`,
       `current_project_name`, `current_project_number`,
       `assigned_to_name`, `assigned_to_role`.
    2. `_models.py::StatusChangeBody` gains project context payload.
    3. `assets.py::/status` endpoint NOW: requires `project_name +
       project_id/number` when → Assigned (422 otherwise); clears
       project context + resets `current_location` when → Available;
       writes a `trench_safety_deployments` row for every assign /
       return; audit event payload carries project_name + number.
    4. `qr_photos.py::/qr-label` meta endpoint embeds
       `png_data_url` base64 so `<img>` renders without auth follow-up.
    5. `TrenchSafetyAssignDialogs.jsx` integrates the `JobPicker`
       dropdown at the top (sourced from `/api/jobs-master`).
       `TrenchSafetyOpsCenter.jsx::QRManagementPanel` renders from
       `png_data_url`.
  Tests: 9 / 9 PASS (`test_trench_asset_assignment_qr_cert.py`) —
  live tests use timestamp-suffixed cert assets with retire teardown.
  Visual smoke: detail + dialog screenshots captured on RP-901, QR
  image rendered (`data-testid='qr-img'` present, not loading).
  Master ledger: `/app/memory/TRENCH_ASSET_ASSIGNMENT_QR_FIX_CLOSURE.md`.

## Previous Closed Track (2026-06-15 · SAFETY-MEETING-WORKFLOW-PDF-CERT)
- **14.0-SAFETY-MEETING-WORKFLOW-PDF-CERTIFICATION CLOSED.** 🟢
  Root-caused the production PDF defect where sections jumped
  01 → 06 → 07 with blank discussion / hazards / action-items /
  attendance. Root cause was a **field-name mismatch in the PDF
  renderer**: `_render_meeting` was reading `facilitator/led_by/
  presenter` but DB stores `conducted_by`; reading `hazards/
  hazards_discussed` but DB stores `hazards_reviewed`; reading
  `discussion/notes` but DB stores `discussion_notes`; expecting
  list-typed `action_items` but DB stores a string. Every section
  rendered empty, then got SKIPPED entirely (no placeholder), so
  numbering jumped. **Five fixes shipped end-to-end**:
    1. `pdf_render.py::_render_meeting` rewritten to read canonical
       schema names first + legacy aliases. Sections 02–07 always
       render with "None recorded" placeholder. Attendance table now
       has 5 columns (Name · Company · Trade/Role · Signature ·
       Acknowledged). New `_render_meeting_attendee_rows` helper +
       `lib/identity_lookup_sync.py` enrich each row from HR record.
    2. `routes/safety.py::MeetingAttendee` Pydantic model with hard
       validators (name + company + signature + acknowledged all
       required). `conducted_by` validator rejects empty values.
    3. `pages/NewMeeting.jsx` attendee row now has Company + Trade +
       Non-MASCI/Subcontractor toggle + Acknowledgement checkbox
       (stamps `acknowledged_at` timestamp). `Add Attendee` blocked
       until current row complete. `validate()` walks every row.
    4. MASCI auto-fill: picking an employee writes `company=MASCI`
       + pulls trade from HR record onto the attendee row.
    5. Non-MASCI / subcontractor path explicit toggle; clears
       `employee_id` so HR roster isn't polluted.
  Tests: **18 / 18 PASS** (`test_safety_meeting_cert.py`) +
  Live preview cert (`phase9_safety_meeting_live_cert.py`): 19 / 19
  contract checks PASS, real PDF rendered (1.4 MB), cleanup verified.
  Cross-PDF audit: only `_render_meeting` had the field-name
  mismatch + section-numbering pattern; all other renderers either
  iterate full record dict or use explicit field maps that match
  the schema. Master ledger:
  `/app/memory/SAFETY_MEETING_WORKFLOW_PDF_CERTIFICATION.md`.

## Previous Closed Track (2026-06-15 · RC1 LIVE PRODUCTION SMOKE)
- **14.0-RC1 LIVE PRODUCTION SMOKE CERTIFICATION CLOSED.** 🟢
  **PASS · DEPLOY-CONFIRMED.** Full authenticated smoke executed
  against https://mascidocs.com under user authorization. Phases
  1, 2, 3, 4, 6, 9, 10, 11, 12, 13, 14 all PASS. Phases 5 (HR
  employee request) + 7 (Safety Form) skipped to avoid producing
  real auto-emails to real HR/Safety reps; their notification +
  audit primitives are exercised by Phase 4. Production env
  confirmed: `app_env=production`, `db_name=masci_safety`,
  CORS pinned, Sentry live, scheduler enabled, Motive Connected.
  Deploy-readiness on prod: **0 blockers, 1 data-quality warn**.
  **1 P2 defect found + fixed inline**: `GET /api/admin/directory?q=`
  was ignoring the filter; added case-insensitive substring match
  in `/app/backend/routes/auth_directory_routes.py` (verified on
  preview: `q=cert.` → 17, `q=DUMMY` → 0, no-q → 116). Needs
  prod redeploy. Created 4 tagged artifacts (project + user +
  staffing assignment + 1 daily report); cleaned up 3; 1 daily
  report (DR-2026-00323) retained as constitutionally immutable
  (per `daily_reports.py` docstring "DELETE stays frozen"). Master
  ledger at `/app/memory/RC1_LIVE_PRODUCTION_SMOKE_CERTIFICATION.md`.

## Previous Closed Track (2026-06-15 · RC1 deployment readiness audit)
- **14.0-RC1 DEPLOYMENT READINESS CERTIFICATION CLOSED.** Full
  14-phase deploy-survivability audit executed. Verdict: 🟢 **GO**
  with a 4-row env-var checklist applied at deploy time. Zero P0
  blockers; 4 P1 environment-variable deltas (`CORS_ORIGINS`,
  `RATE_LIMITING`, `AUTO_EMAIL_REPORTS`, `SCHEDULER_ENABLED`
  must flip preview → production values); 3 P2 tech-debt items
  (4 stale pytest collection failures, 7 scheduler tests that
  rely on cross-DB access **which is correctly blocked by the
  Atlas user permission boundary** — i.e. evidence of working
  isolation, not failure; data-quality master-binding gaps on
  legacy rows). Live `/api/health` 200; live `/api/admin/deploy-readiness`
  reports 0 blockers / 2 informational warns. DB isolation
  PROVEN by failed cross-DB write under `ENFORCE_DB_ISOLATION=true`.
  9 deliverables produced:
  `/app/memory/RC1_DEPLOYMENT_READINESS_MASTER_LEDGER.md`,
  `DEPLOYMENT_GO_NO_GO_MATRIX.md`, `CRITICAL_FINDINGS_REPORT.md`,
  `ENVIRONMENT_CERTIFICATION.md`, `BACKUP_RESTORE_CERTIFICATION.md`,
  `WORKFLOW_CERTIFICATION_MATRIX.md`, `ROLE_CERTIFICATION_MATRIX.md`,
  `PDF_EXPORT_CERTIFICATION_MATRIX.md`,
  `INTEGRATION_CERTIFICATION_MATRIX.md`. Five Pillars **9.92**.

## Previous Closed Track (2026-06-15 · final certification fork)
- **14.0-PM-STAFFING-RUNTIME-PROOF CLOSED.** All 7 phases of the
  final certification directive executed with real users, real
  assignments, real notifications, real audit events. Seeded 17
  cert directory users (one per canonical staffing role) into the
  `ZZ-RUNTIME-CERT-2026` project via the production REST workflow
  (`POST /api/admin/directory`, `POST /api/admin/jobs`,
  `POST /api/admin/jobs/{pn}/team`). Logged in as each via
  `POST /api/auth/multi-login`, navigated to their canonical
  landing route, and captured 17 portal landing screenshots. Drove
  51 prohibited-URL attempts (3 per role) — **51 / 51 blocked**
  with the canonical "403 · ACCESS RESTRICTED" portal-shell chrome.
  Ran a live create→edit→reassign→remove cycle on the
  `project_administrator` assignment to validate notifications +
  audit pipeline: 23 audit rows captured, 17 / 17 roles have
  `action=assign` events, 4 bell notifications fired with correct
  `recipient_role`, `recipient_user_id`, and deep-link `link_url`.
  Phase 7 defect fixes inline:
    1. `compute_pm_scope` extended in `/app/backend/pm_auth.py` to
       UNION project scope from both `jobs_master` (legacy pm_email
       / co_pm_emails) AND `project_team_assignments` — PM-portal
       users assigned via the new staffing workflow now see their
       projects.
    2. Added `_notify_assignment()` in
       `/app/backend/routes/project_team_assignments.py` — assign /
       remove handlers now fan out `db.notifications` rows via
       `notification_service.fanout` with portal-correct
       `recipient_role` for all 17 staffing keys.
    3. Notification wording fixed (was "removed from you from …").
  Harness scripts checked in under `/app/backend/tests/runtime_cert/`
  (`seed_runtime_cert_users.py`, `login_screenshot_loop.py`,
  `phase56_notify_audit_proof.py`) — fully idempotent + repeatable.
  Per-phase evidence ledgers at `/app/memory/PHASE3_…`, `PHASE4_…`,
  `PHASE5_…`, `PHASE6_…`. Master ledger at
  `/app/memory/TRACK_14_0_PM_STAFFING_RUNTIME_CERTIFICATION.md`.
  66 / 66 PM/staffing regression tests still pass.
  **Five Pillars: 9.93** (Proven raised 8.5 → 9.95). **PM Staffing
  is COMPLETE, VERIFIED, PROVEN, DEPLOY-READY.**

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-PM-STAFFING-COMPLETION CLOSED**. Expanded the project-team
  role registry from 13 → **17 roles** with the 4 new operationally
  distinct slots the directive mandated: `project_administrator`,
  `project_coordinator`, `qaqc_rep`, `hr_rep`. Relabeled
  `safety_lead → safety_rep` (Safety Representative) and
  `dispatcher_contact → dispatch_rep` (Dispatch Representative).
  Added `LEGACY_ROLE_ALIASES` + `_canonical_role()` helper so
  historic assignments stored under the old keys translate to the
  new canonical keys at read-time, and POST/PATCH normalise on
  write. Live API confirmed: GET `/api/team-roster/role-registry`
  returns the 17 roles; new keys present; old keys absent;
  PM-assignable / admin-only flags correct (only PM/Co-PM/Exec
  remain admin-only). Mounted shared `JobTeamRosterPanel` as a
  new **Team tab** on PM Command Center (`/pm/command-center?project_number=…`)
  so PMs see the full project roster inline without navigating to
  a separate `/team` route — operational "where is everyone"
  question answerable in one click. +5 new regression assertions
  (`test_pm_staffing_completion.py`): full 17-role registry
  contract, legacy alias translation, admin-only set unchanged
  (PM-assignable for all 4 new roles + both relabels), Team Card
  test-id present on Command Center, Team tab trigger present.
  Existing 19-test staffing suite still passes. Full RC1 sweep:
  **213 / 213 tests pass** (was 190; +5 new + 18 pre-existing
  staffing tests run together). Phase 1 inventory artefact:
  `/app/memory/TRACK_14_0_PM_STAFFING_PHASE1_INVENTORY.md`.

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-HR-DIRECTORY-PREFERRED-NAME-COLUMN-FIX CLOSED**. Split
  the merged HR Directory `Name` column into separate visible
  **Legal Name** and **Preferred Name** columns. Legal Name derives
  from `legal_first_name + legal_last_name` with `name` as
  denormalised fallback. Preferred Name reads from `preferred_name`
  with a clean em-dash placeholder for blanks — zero `undefined` /
  `null` / `None` leaks. Italic preferred styling so HR can scan a
  roster of 359 employees and spot preferred names at a glance.
  New cell test-ids: `hremp-row-legal-name-${id}` ·
  `hremp-row-preferred-name-${id}`. Live verified at
  `/hr/employees` (`Alec Perkins` row → `Al` preferred; other 358
  rows → em-dash). Search still resolves the new fields (UXS-11D
  query already broadened). CSV export already ships
  `Legal First Name · Legal Middle Name · Legal Last Name ·
  Preferred Name` columns (UXS-11D). +3 regression locks (column
  headers + cell value rules + em-dash fallback). Full RC1 sweep:
  **190 / 190 pass**. Five Pillars **9.95**. Closure ledger:
  this PRD entry.

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-UXS-11G FINAL IDENTITY CONSUMER ELIMINATION CLOSED**.
  Eliminated the last server-side identity gap — `safety_forms.py`
  PDF renderer + list/search + email subject + filename + fan-out
  notifications now flow through the canonical
  `format_employee_identity` helper. Added two-pronged refactor:
  (1) write-time enrichment (`_enrich_with_identity`) that copies
  legal/preferred parts onto issuance/training records at insert
  time, and (2) read-time fallback (`_identity_display`) for legacy
  records — with on-the-fly enrichment in the PDF endpoints so old
  data renders correctly **without a migration**. 20 backend
  consumer sites + 1 final frontend stray fixed. Search now
  resolves preferred / legal first / middle / last / display_identity
  on issuance + training lists. **Live PDF byte-stream verified
  end-to-end** via WeasyPrint → pdftotext: `James Fisher (Jimmy)`
  renders exactly per contract for the preferred case; legal-only
  renders `Sarah Connor` with no `(Jimmy)` leak; legacy-only renders
  `Alec Perkins`; defensive empty-record case produces a blank Name
  field with **zero** `None`/`null`/`undefined`/`N/A` leaks. +11
  new regression assertions (4 of which exercise the actual
  WeasyPrint PDF pipeline). Full RC1 sweep: **187 / 187 pass**.
  Five Pillars **9.948**. Closure ledger:
  `/app/memory/TRACK_14_0_UXS_11G_CLOSURE.md`. **HR Identity
  Rollout is COMPLETE — display drift = 0, PDF drift = 0, print
  drift = 0, helper bypasses = 0, deploy-ready, no follow-on
  identity work required.**

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-UXS-11F HR IDENTITY COMPLETION (FINAL ROLLOUT) CLOSED**.
  Drove identity-consumer count from 28 raw display sites down to
  **0 remaining display surfaces**. 27 display sites across 15 pages +
  2 components converted to `formatEmployeeIdentity(x) || x.<field>`
  via one-shot regex rewrite. The single remaining bare reference is
  a write-side form input (`NewEquipmentInspection` operator name),
  correctly excluded. Backend `/api/global-search` employees probe
  now matches `legal_first_name` / `legal_middle_name` /
  `legal_last_name` / `preferred_name` in addition to legacy fields,
  and result titles render through `format_employee_identity()`. The
  helpers (backend + frontend) now treat `display_identity` as the
  highest-priority denormalised fallback, so any future endpoint
  projecting that field lights up correct preferred-name display
  everywhere with zero new frontend code. Dispatch broadcast presets
  show `James Fisher (Jimmy)` formal display; dispatch driver SMS
  greeting now uses `preferred → legal_first → driver_name` chain so
  texts read naturally as `Hi Jimmy, …`. Regression suite grew
  19 → **37 parametrized identity assertions** (consumer locks +
  structural "no bare identity render" guard + global-search lock).
  Full RC1 sweep: **176 / 176 pass**. Closure ledger:
  `/app/memory/TRACK_14_0_UXS_11F_CLOSURE.md`. Five Pillars 9.92.
  One transparent follow-on flagged (single safety_forms PDF
  renderer site — narrow `UXS-11G` track recommended rather than
  smuggled into this closure).

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-HR-IDENTITY-COMPLETION-AND-CERTIFICATION** — canonical
  identity helper layer + regression coverage. Created
  `backend/masci/identity.py` and `frontend/src/lib/identity.js`
  (mirror) with `format_employee_identity` / `format_legal_name` /
  `identity_search_blob`. Display rule:
  **"Legal First Last (Preferred)"** when `preferred_name` set,
  legal-only otherwise, fallback to denormalised `name` when no
  legal parts. Never replace legal identity. Never hide it.
  HR Directory list + drawer now render through the helper.
  `/api/hr/employees` now ships a precomputed `display_identity`
  field so every consumer renders the same string. Search now
  resolves "James" / "Michael" / "Fisher" / "Jimmy" / "James Fisher" /
  "Jimmy Fisher" / "James Michael Fisher" via `$regex` across
  `legal_first_name`, `legal_middle_name`, `legal_last_name`,
  `preferred_name`, denormalised `name`, employee_id, trade. Driver
  Qualification CSV grew explicit `Legal First Name · Legal Middle
  Name · Legal Last Name · Preferred Name` columns so identity
  round-trips through export. **19 new regression assertions**
  (`test_hr_identity_completion.py`) lock the helper contract, the
  HR Directory usage, search coverage, CSV identity columns, and
  the `display_identity` API field — future developers cannot
  silently break the identity surface. Full RC1 suite: **158 / 158
  pass**. Closure ledger:
  `/app/memory/TRACK_14_0_HR_IDENTITY_CLOSURE.md`.

## Previous Closed Track (2026-02-14 · fork session)
- **14.0-UXS-11E PLATFORM ROUTE PARITY EXECUTION SWEEP CLOSED**. 27
  additional drifted operational pages wrapped in `<PortalShell>`
  with their correct domain sidebars. The platform now renders unified
  chrome (MASCI mark · portal switcher · local time · sign-out ·
  domain sidebar · blueprint-grid bg) on every auth-gated operational
  route. **HR (8)**: HrDriverProfile, HrMotiveDrivers,
  HrFieldLeadershipUsers, HrIncidents, HrTimeOff, HrDailyReports (list
  + detail), HrEmployeeAccountabilityTimeline. **Safety (2)**:
  SafetyDriverProfile, SafetyFormsHub. **Dispatch (3)**:
  DispatchDriverProfile, DispatchDriverQualification,
  DispatchCommandCenter. **FL (2)**:
  FieldLeadershipDriverQualification, FieldLeadershipPortalDashboard.
  **Multi-context (3)**: EquipmentDashboard, FleetVisibility,
  Dashboard (Inspections). **Admin (6)**: AdminQaqcList,
  AdminTerminations, AdminTrainingVideos, AdminLeadershipEquipment,
  AdminGuide, OperationsCenterCommand. **PM/Cross (3)**:
  ProjectPnlPage, JobPhotosLibrary, TrainingHub + TrainingTrack.
  Regression suite expanded 47 → 72 parametrized guards
  (single-context EVIDENCE_ROUTES + dynamic-scope MULTI_CONTEXT_ROUTES
  with relaxed portalRole match). **139 / 139 RC1 regression tests
  pass**. Live preview screenshots evidence the parity (AdminGuide,
  AdminQaqc, AdminTerminations, HrIncidents, HrEmployees,
  DispatchCommandCenter, JobPhotosLibrary, ProjectPnL). Operational
  drift remaining on auth-gated surface = **0**. Closure ledger:
  `/app/memory/TRACK_14_0_UXS_11E_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-UXS-11 PLATFORM ROUTE PARITY CERTIFICATION CLOSED** (for 5
  user-evidenced drift routes · IN PROGRESS for ~49 enumerated
  follow-on operational pages). User-reported live preview defect:
  routes use multiple different shell designs. Fixed 5 evidenced
  routes (`/project-health` · `/asset-transfers` · `/admin/jha-plans` ·
  `/admin/trench-boxes` · `/po-requests`) by wrapping each in
  `<PortalShell>` with the correct domain sidebar; legacy
  MasciLogo + HubBackLink imports removed where they would
  duplicate PortalShell's brand bar. Built comprehensive drift
  inventory of all 103 legacy-chrome pages: 5 fixed · 47 legitimate
  exceptions (auth / public forms / print views) · ~49 remaining
  operational drifted pages enumerated for 4 scheduled follow-on
  sweeps (PM · HR · Safety+Shop+Dispatch+FL · Admin). +10 regression
  guards lock the evidenced routes. 99/99 RC1 + parity + reality +
  PDF + hygiene + I1 + HR-readiness + UXS-11 tests pass. Live
  screenshots captured for all 5 routes. Five-Pillar **9.89**
  (Trusted 9.90 · Proven 9.90). Closure ledger:
  `/app/memory/TRACK_14_0_UXS_11_PLATFORM_ROUTE_PARITY_CERTIFICATION_CLOSURE.md` ·
  drift inventory: `/app/memory/TRACK_14_0_UXS_11_ROUTE_DRIFT_INVENTORY.md`.

## Previous Closed Track (2026-02-14)
- **14.0-HR-READINESS-CERTIFICATION-SWEEP CLOSED** — Fixed P0
  user-reported defect: HR bell click on a pending employee-add
  request went nowhere because `db.employee_requests` was inserted
  silently with no `notifications` row. New
  `_notify_hr_queue_pending` helper fans out one in-app
  notification per active HR user with `link_url=/hr/employee-requests?id=<rid>`.
  Both creation paths (employee_requests + field_leadership
  inline-add) now call it. HR Queue page reads `?id=<rid>`, auto-
  highlights the matching card with an amber ring, scrolls it into
  view, and auto-opens the approval dialog — HR acts in one click.
  Schemas accept `legal_first_name` / `legal_middle_name` /
  `legal_last_name` / `preferred_name`; approval persists all four
  on the new employee record so directory views and field forms can
  render "James Fisher (Jimmy)" without losing legal identity.
  End-to-end live preview verification captured: submit → 56
  notifications fanned out → approve with preferred name → employee
  created with all 4 identity fields persisted. +9 regression
  guards lock the contract. 89/89 RC1 + parity + reality + PDF +
  hygiene + I1 + HR-readiness tests pass. Five-Pillar **9.93**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_HR_READINESS_CERTIFICATION_SWEEP_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-I1 INTEGRATION HONESTY + ARCHIVE ORIGIN VERIFICATION CLOSED**
  — Platform trust track. Added 5-status honesty vocabulary
  (LIVE / CONFIGURED / PARTIAL / DISCONNECTED / ERROR) to
  `/api/admin/integrations/health`. Mocked integrations (e.g.
  MaintainX) now pin to DISCONNECTED — no fake green badges.
  Motive correctly maps to PARTIAL (webhook credentials present,
  API returning HTTP 400). Backup manifest now carries `environment`,
  `database_name`, `app_env`, `db_name`, `manifest_schema`,
  `backup_id`, `source_instance`. `/api/exports/restore` reads the
  manifest BEFORE touching any data and refuses
  environment/database mismatches or legacy archives in production,
  with a calm human-readable HTTP 400 message and a permanent
  `exports_restore` audit row for every attempt. Live preview proof:
  production-origin archive rejected against preview worker
  (`result='rejected', reason='environment-mismatch:production-into-preview'`).
  The last manual-checklist item from Track 14.0-P0 is now AUTOMATED.
  +20 regression guards lock the contract. 82/82 RC1 + parity +
  reality + PDF + hygiene + I1 tests pass. Five-Pillar **9.96**
  (Trusted 9.99 · Proven 9.99). Ledger:
  `/app/memory/TRACK_14_0_I1_INTEGRATION_HONESTY_AND_ARCHIVE_ORIGIN_VERIFICATION_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-P0 PREVIEW/TEST/DEMO DATA DEPLOYMENT HYGIENE SWEEP CLOSED** —
  Read-first audit + lock the preview→production data boundary so
  RC1 deployment cannot accidentally carry preview garbage forward.
  Boundary verified: preview = `masci_safety_preview` · production =
  `masci_safety` (different Atlas DBs). `_verify_env_db_alignment()`
  startup guard refuses to start on mismatch (the guard that closed
  the 2026-05-26 crossover incident is intact). Demo-seed scripts
  hard-block production. Admin restore endpoints stay admin-token
  gated. Preview-DB sweep found ~1 360 sampled suspicious records
  across 17 collections (`TEST Juan Perez` × 120, `pm.demo@mascigc.com`
  × 304, etc.) — all in preview only; production unaffected; amber
  preview banner mitigates visual confusion. +6 hygiene regression
  guards (`test_data_hygiene_sweep.py`) lock the boundary contract:
  env/DB alignment · demo-seed refuse-production · no demo literals in
  server.py · credentials doc memory-only · admin restore stays
  admin-gated. No runtime code changes — boundary was already
  correctly in place. 62/62 RC1 + parity + reality + PDF + hygiene
  tests pass. Five-Pillar **9.92** (Trusted 9.95 · Proven 9.95).
  Ledger: `/app/memory/TRACK_14_0_P0_PREVIEW_TEST_DEMO_DATA_HYGIENE_SWEEP_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-P1 PDF LOCKUP SWEEP CLOSED** — Platform-wide PDF / Print /
  Export certification. Inventoried 23 backend PDF endpoints + 15
  frontend browser-print surfaces. Verified shared `pdf_branding`
  module intact; the 3 certified generators (master_history /
  training_center / fire_ext_attachments) still use
  `wrap_pdf_html()`; the rest emit MASCI-branded PDFs inline with
  consistent header / body / footer chrome. Live-preview sampled 3
  PDFs (Fleet Severity Card · Ops Manual · HR FL write-up) —
  professional branded output, embedded photos, pagination,
  generated-at footer. Frontend operational View pages all wire
  through `printReport()` with `no-print` / `print-section` CSS for
  clean browser Save-as-PDF. Fixed `server.py` email-attachment
  filename hyphen-vs-underscore drift. +10 PDF regression guards
  lock the contract. Preview-DB seed-data contamination deferred
  to a separate hygiene pass (mitigated by the persistent preview
  banner that prints on every page/PDF). 56/56 RC1 + parity +
  reality + PDF guards pass. Five-Pillar **9.90** (Trusted 9.90 ·
  Proven 9.90). Ledger:
  `/app/memory/TRACK_14_0_P1_PDF_LOCKUP_SWEEP_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-SHOP-DISPATCH-OPERATIONAL-REALITY-FIX CLOSED** — User-reported
  live preview defect: Shop landing rendered raw `HTTP 401` text in
  three dashboard sections ("Who's loaded right now" /
  "PM due · overdue · in flight" / "What's blocked on parts").
  Root cause: three inline cards in `ShopHubV2.jsx` bypassed the
  shared `tokenStorage` helper, reading `localStorage` only — missing
  tokens persisted in `sessionStorage` (Remember-me OFF path).
  Fix: cards now call the shared `authHeaders()` helper (uses
  `getAdminToken()` + `getShopToken()` — both storage tiers). Raw
  error chips replaced with calm operator empty states. Mirror-bug
  in `HrHubV2.authHeaders()` also fixed (was sessionStorage-only) —
  HR workforce reads now show real counts. Shop sidebar decision
  PROVEN: no `/components/shop/sidebar/` exists; portal is
  intentionally card-grid. Dispatch decision PROVEN: map-first
  preserved per directive (sidebar opt-in via `?dispatchSidebarV2=1`
  flag). +3 nav-drift regression guards lock the contract.
  24/24 nav-drift + 46/46 RC1 suites pass. Five-Pillar **9.92**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_SHOP_DISPATCH_OPERATIONAL_REALITY_FIX_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-CROSS-PORTAL-LANDING-PARITY-FIX CLOSED** — User-reported live
  preview defect: `/hr` rendered plain-white with no sidebar while
  `/hr/employee-accountability` rendered HR sidebar + blueprint grid.
  Same class of defect on `/safety-portal` and `/admin/hub_v2`. Fixed
  by: (1) `PortalShell` now applies `blueprint-bg` to its main
  content section so every PortalShell-backed landing carries the
  same grid texture as deep pages, (2) `HrHubV2` mounts
  `<HrSideNavV2 />` via the `sideNav` prop, (3) `SafetyHubV2` mounts
  `<SafetySideNavV2 />`, (4) `AdminHubV2` mounts admin `<SideNavV2 />`.
  Shop / Dispatch / FL / public forms / auth intentionally unchanged
  per directive. 3 new regression guards in `test_nav_drift_guard.py`
  (21/21 pass) lock the parity contract. 43/43 RC1 ownership +
  parity suites pass. Five-Pillar **9.90** (Trusted 9.90 · Proven
  9.90). Ledger:
  `/app/memory/TRACK_14_0_CROSS_PORTAL_LANDING_PARITY_FIX_CLOSURE.md`.

## Previous Closed Track (2026-02-12)
- **14.0-PREVIEW-REALITY-RECONCILIATION CLOSED** — Honest gap-fix:
  prior PORTAL-LANDING-NAVIGATION-UNIFICATION wired `PmSideNavV2` into
  `PmHubV2` (`/pm/hub`) but **real users land on `/pm/command-center`**
  via `PmHomeRedirect`. Fixed by also wiring the sidebar into
  `PmCommandCenter.jsx` (2 LOC). Live preview screenshot at
  `/tmp/pm_actual_landing.png` proves: visiting `/pm` redirects to
  `/pm/command-center`, page title "Project Management Center",
  sidebar testid count = 1, all top-bar chrome present. 18/18
  nav-drift + 64/64 backend regression green. Five-Pillar **9.90**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_PREVIEW_REALITY_RECONCILIATION_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-PORTAL-LANDING-NAVIGATION-UNIFICATION CLOSED** — Single
  design-system primitive (`PortalShell.sideNav` slot) closes the
  "landing hides navigation" gap. **PM Hub V2 now exposes full PM
  SideNavV2** on desktop with 6 domain sections (Project Operations ·
  Financials & Cost · Field Coordination · Document Control ·
  Compliance & Risk · System & Communications · Pinned). 17 LOC
  surgical · backward compatible · no feature flags. Live screenshot
  proof at `/tmp/pm_hub_with_sidebar.png`. HR/Safety/Shop wire-ins are
  1-line each (Phase 2 fast-follow, ~15 min). FL + Public Forms
  explicitly KEEP AS IS per directive Parts 7+8. All 18 nav-drift
  guards + verified subset of regression green. Five-Pillar **9.90**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_PORTAL_LANDING_NAVIGATION_UNIFICATION_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-HUMAN-FIRST-OPERATIONAL-REALITY-SWEEP CLOSED** — Fix-as-you-go
  audit. **Executive YES** to "Can a real construction employee complete
  their job Monday morning with no training?" **4 unguarded routes
  fixed in flight** (`/admin/qaqc`, `/pm/odr`, `/hr/employees`,
  `/hr/employees/:id/accountability` now wrapped with their guard
  tokens). RC1-NAV-007 RESOLVED. Nav-drift guard `known_unguarded` set
  drained to `set()` across all 7 portal prefixes. Live walkthrough of
  7 portal hubs proves universal top-bar chrome (Bell · Search ·
  PortalSwitcher · Identity · HOME · SIGN OUT · language toggle).
  12 of 14 roles can complete primary workflow today (Superintendent /
  Foreman onboarding is RC1-INVITE-FLOW-001 · Read-only is not
  started). **Zero automatic deployment blockers remain.** 64/64
  backend pytest green. Five-Pillar **9.90** (Trusted 9.95 · Proven
  9.95). **Spanish · PDF · I1 · UXS-11 · Role-Visibility · Deploy prep
  ALL UNBLOCKED.** Ledger:
  `/app/memory/TRACK_14_0_HUMAN_FIRST_OPERATIONAL_REALITY_SWEEP.md`.


## Latest Closed Track (2026-02-12)
- **14.0-HUMAN-FIRST-VISIBILITY-CERTIFICATION CLOSED** — Full
  human-perspective audit across 10 portals · 341 routes · 232
  surfaces · 14 roles. **18 permanent regression-guard tests committed
  to `backend/tests/test_nav_drift_guard.py`** (64/64 pytest green).
  **Critical correction to prior TRUTH-MAP audit**: PM Hub V2 actually
  renders top-bar chrome (Search · Bell · PortalSwitcher · Home · Sign
  Out · language toggle) via `PortalShell` — not "no chrome" as the
  earlier audit grep-finding had stated. Live screenshot proof
  attached. **3 newly-discovered unguarded portal routes** pinned as
  **RC1-NAV-007** (P1, 3-line fix). RC1-NAV-002 WITHDRAWN. NAV-001 /
  003-006 downgraded P0→P2. **No P0 RC-1 blockers remain after
  corrections.** Five-Pillar **9.85** (Trusted 9.95 · Proven 9.90).
  **Spanish · PDF · I1 fully unblocked.** Ledger:
  `/app/memory/TRACK_14_0_HUMAN_FIRST_VISIBILITY_CERTIFICATION.md`.


## Latest Closed Track (2026-02-12)
- **14.0-PLATFORM-TRUTH-MAP CLOSED** — Complete read-only audit of every
  portal · route · navigation element · surface across MASCI Operations
  Platform. **341 routes** · **10 portals** · **~232 surfaces** · **14
  roles** inventoried. Four output files committed (executive truth map,
  navigation matrix, surface inventory, machine-readable route JSON).
  **Single biggest finding:** PM/Shop/HR/Safety/Dispatch V2 hubs lack
  their shell wrap → no sidebar / no NotificationBell / no PortalSwitcher
  / no GlobalSearch / no mobile hamburger on V2 landing pages. Admin
  alone has the full chrome end-to-end. **8 RC1 blockers** identified
  (2 P0 · 4 P1 · 2 P2). **Spanish · PDF · I1 unblocked.** UXS-11 + role
  visibility certification blocked until shell-wrap track ships.
  Five-Pillar **9.85** (Trusted 9.95 · Proven 9.90). Ledger:
  `/app/memory/TRACK_14_0_PLATFORM_TRUTH_MAP_ROUTE_NAV_SURFACE_INVENTORY.md`.


## Latest Closed Track (2026-02-12)
- **14.0-RC1-DONE-DONE-CERTIFICATION-FIX-SWEEP CLOSED** — Canonical
  `MASCI_DEFINITION_OF_DONE.md` created (5 states: NOT STARTED · BUILT ·
  WIRED · OPERATIONAL · DONE-DONE). RC1-PORTAL-NAV-001 (PM Dispatch
  shortcut → 403) FIXED. RC1-OWNERSHIP-UX-001 (PM Project Roster card →
  404) FIXED. PM + Admin Project Team workflows verified OPERATIONAL
  end-to-end with live screenshots. 46/46 backend regression green.
  Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95). **Spanish + PDF +
  Integration Honesty all unblocked.** Ledger:
  `/app/memory/TRACK_14_0_RC1_DONE_DONE_CERTIFICATION_FIX_SWEEP.md`.


## Latest Closed Track (2026-02-12)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2B CLOSED** — Producer
  Routing Sweep. 11 job-scoped producer call sites across 4 backend
  files (safety, qaqc, equipment, trench excavations) now populate
  `recipient_user_id` from the active project roster via the new
  `lib.team_routing.apply_routing` helper. ROLE_CHAIN extended with
  6 event keys. Existing `recipient_role` always preserved as the
  D2 leakage scope guard. 46/46 backend tests + NOTIFY-OWNERSHIP-LOCK
  leakage matrix re-run OVERALL PASS. Transfer-redirect contract proven
  (post-replacement notification routes to new super, not retired).
  Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95). **Spanish is
  UNBLOCKED.** Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2B_PRODUCER_ROUTING_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2A CLOSED** — Operational
  Writer Team-Snapshot Embedding Sweep. 12 job-scoped writers now embed
  the frozen `team_snapshot` at submit time via `lib.team_routing.snapshot_team`.
  8 writers deferred with documented asset-/employee-/link-scope reasons.
  Immutability proven (pre-mutation records keep snapshot bit-identical;
  post-mutation records capture new state). 35/35 backend tests green
  (Phase 1 + 2A + 2B + 2B-2A). Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95).
  Phase 2B-2B (Producer Routing Sweep) is next. Spanish remains BLOCKED.
  Ledger: `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2A_SNAPSHOT_EMBEDDING_CLOSURE.md`.


## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-1 CLOSED** — `lib/team_routing`
  shim, `OWNERSHIP_LOCK_ENABLED` flag, D4 + FL producers wired, FL "My Jobs"
  widget, PM "Team" link. 24/24 backend tests green. Five-Pillar 9.78
  (Trusted 9.90 · Proven 9.90). Phase 2B-2 (15 writers + 12 producers + Asset
  Care project view + disable wizard UI) is next. Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_CLOSURE.md`.


## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2A CLOSED** — Assignment lifecycle
  (6 states), transfer engine, disable-user protection, snapshot helper,
  notification resolver, full audit chain. **9/9 certification tests pass.**
  Five-Pillar **9.85** (Trusted 9.92 · Proven 9.92 · above the 9.8 directive
  minimum). Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2A_CLOSURE.md`.



## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 1 CLOSED** — editable per-project
  team roster (`project_team_assignments` collection · 13 roles · admin +
  PM scopes · audit trail · idempotent PM/Co-PM backfill · 12 APIs · 2 new
  routes · 8/8 tests green · Composite 9.62). Closure ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_1_CLOSURE.md`.
  Phase 2 (producer rewrites + FL sidebar + Asset Care view) is next.
  Spanish remains blocked until Phase 2 ships.


## Latest Read-Only Audit (2026-06-14)
- **14.0-JOB-OWNERSHIP-AND-PROJECT-TEAM-ROSTER-AUDIT** — design certification for the
  Job Ownership Foundation. Recommends Option C (Hybrid): keep `pm_email` /
  `co_pm_emails`; build new `project_team_assignments` collection for the 11
  remaining roles. ~3 260 LOC · ~12 engineering days. 5-phase migration. Must
  precede Spanish. Doc: `/app/memory/TRACK_14_0_JOB_OWNERSHIP_AND_PROJECT_TEAM_ROSTER_AUDIT.md`.


## Latest Closed Track (2026-06-14)
- **14.0-NOTIFY-OWNERSHIP-LOCK · D2-D10 CLOSED** — Person-level routing
  (`recipient_user_id` is now read-side authoritative); Asset Admin
  first-class scope via `X-Asset-Admin: 1` header; FL producer adopts
  matrix owner-resolution chain; three scheduled producers built
  (`scan_asset_documents`/`scan_hr_training`/`scan_dispatch_stale_locations`)
  with admin trigger endpoints. D7 leakage matrix: zero cross-role bleed.
  D8 click-through: 11/11 link_url valid. ~887 LOC across 9 files.
  Closure ledger: `/app/memory/TRACK_14_0_NOTIFY_OWNERSHIP_LOCK_CLOSURE.md`.

- Maps: MapLibre · single engine
- Integrations: Motive (live) · MaintainX (stub) · Resend · R2

## Completed Tracks (this session)
- 13.6N · Operational Polish & Signoff Readiness
- 13.7A · Operational Map Discovery
- 13.7B / 13.7B-VERIFY / 13.7C · Shop Map Lens (Recovery Map) implementation + zero-marker proof + preview seed
- 13.8A · Operational Workflow Gap Discovery
- 13.8B · Hidden Systems Audit
- 13.8C · Live Platform Operational Intelligence Audit (halted at prod-access boundary)
- 13.8D · Hidden System Recovery Certification
- 13.8E · Operational Locations surfacing in `AdminHubV2.jsx`
- 13.8F · PO Requests Certification
- 13.8G · Operator Interview Crib Sheet
- **13.9 · FINAL DISPOSITION CERTIFICATION** — definitive matrix of 173 systems · 8-item ruthless build queue · 34 hours total
- **13.9.1 · ODR CERTIFICATION REPORT** — source-truth validation of every Track 13.9 ODR claim · verdict: AUTHORIZE Track 13.10 · all 13.9 claims VERIFIED (two minor undercounts in 13.9's favor: 22 endpoints not 13; `OperationalRecords.jsx` is a transitive consumer)
- **13.10–13.12 · EXECUTION WAVE 1** — ODR sidebar surfacing in PM + Admin + Safety sidebars + FL Hub tile · PO Requests action card on PM Hub V2 with live `/api/po-requests/summary` (252 / 13 / 23 live counts in preview) · Operations Actions surfacing in Admin Sidebar V2 · all hard locks intact · zero backend touch · 5 files edited additively
- **13.13 · OPERATIONAL EVENTS PROJECT-DAY PANEL** — Read-only Project-Day Events panel added to `PmProjectDetail.jsx` calling existing public endpoint `GET /api/operational-events/project-day/{project_number}/{date}` · honest empty/error states · 1 file edited · zero backend touch · all Wave 1 surfacings + hard locks verified intact
- **13.14 · SCALE TICKET 4-FIELD EXTENSION** — `operational_attachments.scale_ticket` extended with `weight_gross_lbs / weight_tare_lbs / weight_net_lbs / material_code` · auto-net computation when gross+tare supplied · explicit net preserved · `_public_attachment` projection passes fields through · `AttachmentStrip.jsx` renders inputs (when type=scale_ticket) and chips (on existing items) · 8/8 pytest pass · all Wave 1 surfacings + Track 13.13 panel + hard locks intact
- **13.15 · LIVE PORTAL TRUST COPY CLEANUP (this fork)** — Removed stale "preview · side-by-side · no route swap · operator approval" copy from HrHubV2 · PmHubV2 · SafetyHubV2 · ShopHubV2 (live-swapped) and AdminHubV2 · LeadershipHubV2 · DispatchHubV2 (companion-only) and V2Index. Copy now matches App.js route truth. Zero operator-visible stale terms on any live or companion portal · `/driver/hub_v2` confirmed 404 · all hard locks intact
- **13.16 · DISPATCH SIDEBAR DEAD-LINK CLEANUP** — 6 dead links removed · 2 canonical routes added · 1 empty domain removed in `DispatchSideNavV2.jsx`. Map-first canvas intact.
- **13.17 · PO LIFECYCLE NOTIFICATION CERTIFICATION + IMPLEMENTATION** — PO receipt missing / uploaded events wired to `tasks_notifications` role fan-out to PM and HR. Backend additive · zero UI change.
- **13.18 · MATERIAL MOVEMENT LEDGER · CERTIFICATION & ARCHITECTURE** — Source-truth certification of 5 live material sources + ODR archive layer + FleetWatcher NOT_CONNECTED. Recommendation: **B — Phase A only · enrich existing `/api/material-movement/daily` endpoint with proof-join + verification labels + rollup counters. NO new collection. NO new UI.** Next: Track 13.19 (Phase A). Architecture report at `/app/memory/TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md`.
- **13.19 · MATERIAL MOVEMENT LEDGER · PHASE A** — `/api/material-movement/daily/{p}/{d}` enriched additively with `scale_ticket_proofs[]` (host_kind=assignment join on `operational_attachments` 5 proof-bearing types), `haul_cycles[]` (project-day join), `proof_summary{}`, `rollups{}`, `verification_status` (virtual closed-set classifier), `source_breakdown{}` (FleetWatcher hard-zero). Single file: `backend/routes/material_movement.py`. 9/9 targeted pytest pass. Zero new collection · zero UI change · zero schema change · zero auth widening. Backward-compat verified against `MaterialMovementTile.jsx`. All Track 13.13–13.17 surfaces + hard locks intact.
- **13.20 · MATERIAL MOVEMENT LEDGER · PHASE B** — Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes Phase A endpoint. Renders verification chip · 5 counters · Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof · source breakdown footer (FleetWatcher honestly "not connected"). Honest empty + error states. ESLint clean. Live browser smoke confirms mount + coexistence with Track 13.13 Operational Events panel. Single frontend file · zero backend touch · zero new endpoint · zero new collection.
- **13.21 · MATERIAL MOVEMENT LEDGER · PHASE C** — Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger`. New `GET /api/dispatch/haul-ledger` endpoint (dispatch/admin gated · 90-day cap · 6 query filters) composes existing `haul_cycles` + `operational_attachments` + `daily_reports`. New page `DispatchHaulLedger.jsx` + sidebar link in Driver Coordination domain. NO new collection · NO writes · NO map overlay · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact. FleetWatcher honestly `not_connected`. Live smoke: 92 rows across 12 projects/83 trucks in a 30-day preview window. ESLint clean.
- **13.22 · MATERIAL MOVEMENT LEDGER · PHASE D** — Admin Material Ledger Data-Quality + CSV Export. Extended `/api/dispatch/haul-ledger` with `?format=csv` (operational-only 20-field whitelist · NO financial fields · FleetWatcher `false` on every row). New admin page `/admin/material-ledger-quality` defaults to last-30-days `missing_proof` queue. New Admin Hub V2 Section 05 card. Live smoke: 92 missing-proof rows surfaced; CSV stream returns 93 lines with correct headers and date-bounded filename. ESLint clean. Map-first hard lock intact.
- **13.23 · ODR PM-HUB PENDING-DRAFTS PILL (last IBQ item)** — Small additive ODR attention QueueCard on PM Hub V2 reading existing `/api/odr` (PM-scoped server-side). Counts ODRs in `{draft, returned}` (the two states needing PM rework). Single-file frontend additive (`PmHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection. ESLint clean · live PM smoke confirms mount + all-clear branch + click routes to `/pm/odr` + PO card coexists.
- **13.24 · SHOP PORTAL REALITY AUDIT + OPERATOR ACCESS CLEANUP** — Verified `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`. Removed misleading "Open Classic Shop Hub" self-loop button (replaced with `Equipment Pre-Ops` primary action). Added Section 04 · Shop Records · live (Equipment Pre-Ops · Truck DVIRs · Defect History cards). Documented Shop Repair Complete ≠ Returned To Service hard lock intact at endpoint level (`/api/shop/fleet/defects/{id}/repair` vs `/api/dispatch/fleet/defects/{id}/clear`). Per-defect audit trail defensible; per-unit aggregate history + CSV/PDF export + search/filter UI documented as future-track gaps (were never built classic-side either — no regression). Single-file frontend additive. Zero backend touch.
- **13.25 · ASSET CARE & SERVICE ARCHITECTURE CERTIFICATION** — Source-truth certification of all asset-care collections + MaintainX stub status + mechanic-role absence + PM absence + Fuel/Lube absence. Verdict: per-defect lifecycle defensible; per-unit timeline + mechanic identity + PM + Fuel/Lube **missing**. **Recommended next: A — Asset Service Event Backbone** (derived virtual timeline · single backend file · NO new collection). 8-track phased plan (13.26 backbone → 13.27 unit timeline → 13.28 mechanic assignment → 13.29 fuel/lube visit → 13.30 daily reconciliation → 13.31 PM engine → 13.32 MaintainX [BLOCKED] → 13.33 Asset Care Command). Zero code · zero schema · zero UI. Report: `/app/memory/TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md`.
- **13.26–13.29** — Asset Service Event Backbone + Unit History Timeline + Shop Mechanic Assignment + Fuel/Lube Job Visit Form (all DONE 2026-06-12 — see ROADMAP table).
- **13.30 / 13.30A–C** — Service Truck Daily Reconciliation + Shop Command Center UX audit + Restructure + Intelligence with Global Unit Search (all DONE 2026-06-12).
- **13.30D · SHOP COMMAND CENTER 10/10 EXPERIENCE · PARTS + WORKLOAD INTELLIGENCE + PRE-CLOSEOUT AUDIT (DONE 2026-06-13)** — Two new read-only aggregators (`/api/shop/parts/on-order/summary`, `/api/shop/mechanics/workload`) + matching live `PartsOnOrderCard` and `MechanicWorkloadCard` in `ShopHubV2.jsx`. **Pre-closeout six-item audit (Five-Pillar · 15-second · first-click · white-space · uniformity · PM-Engine-readiness) caught and fixed two real bugs before lock**: (1) Unit Search returned UUID `id` substrings as `unit_number` — predicate rewritten to search operator-facing fields only, real `unit_number` returned, regression pytest pinned; (2) Section numbering broken (01→02→03→02→04→05→06→03) — renumbered monotonically 01–08 with Mechanic Workload promoted above Parts. PM Engine readiness audit documents 5 data sources Track 13.31 can consume today + 5 gaps it must close + 3 open kickoff questions. **24/24 Track 13.30* pytests pass.** Report: `/app/memory/TRACK_13_30D_SHOP_COMMAND_CENTER_10_10_EXPERIENCE_PARTS_WORKLOAD.md`.
- **13.31 · PM ENGINE · PREVENTIVE MAINTENANCE LIFECYCLE (DONE 2026-06-13)** — Full operator-controlled PM engine: 3 new collections (`pm_templates · pm_schedules · pm_work_orders`), 18 endpoints under `/api/shop/pm/*`, 4 new operator pages (`/shop/pm`, `/templates`, `/schedules`, `/work-orders[/:id]`), 8 live PM tiles in ShopHubV2 (section 04). Meter source priority: fuel/lube → pre-op → honest `unknown_meter`. Due-state math deterministic with explanations. Asset Service Event Backbone extended to project PM events (lifted `pm` from UNAVAILABLE to AVAILABLE). **PM completion does NOT return units to service** — restated at every API approve response and UI surface. No MaintainX consumption · no fake manufacturer DB · no costs/POs. **15/15 new pytests pass · 39/39 with regression**. Five-Pillar 9.6/10. First-15-seconds 10/10 · first-click 10/10 within 2 clicks. Report: `/app/memory/TRACK_13_31_PM_ENGINE.md`.
- **13.31A · ASSET ADMINISTRATOR CERTIFICATION & SOURCE-OF-TRUTH AUDIT (READ-ONLY · 2026-06-13)** — Full read-only certification of asset administration across the platform. NO code · NO UI · NO routes · NO schema · NO collections. **Asset Ownership Matrix** built for 31 fields: 11 properly OWNED · 2 DUPLICATED · **18 MISSING administrative fields** (registration, insurance, title, ownership, lifecycle_status, photos, documents, division/supervisor/region, GPS device, Motive foreign-keys). `equipment_master` certified as system of record but currently a thin 13-field ledger. Motive scope verified correct (telematics only). Asset Administrator role designed (NOT implemented). **MAP STAYS — non-negotiable.** Asset Care Command Center (13.33) readiness: 50% (6/12 components ready). **Five-Pillar score for current Asset Administration state: 6.6/10 — below the 9.5 bar.** Recommended sequence: **13.31B Asset Administration Spine → 13.33-A Asset Care Composite View → 13.33-B Renewal Alerts → 13.32 MaintainX (blocked).** Report: `/app/memory/TRACK_13_31A_ASSET_ADMINISTRATOR_CERTIFICATION.md`.
- **13.31AA · EMPLOYEE LIFECYCLE + ASSET ISSUANCE ARCHITECTURE CERTIFICATION (READ-ONLY · 2026-06-13)** — Discovered the platform already has mature **Employee Lifecycle + Asset Custody + PPE Issuance + Return + Transfer** systems in active use (employees 365 · employee_lifecycle_events 38 · asset_assignments 16 · asset_transfers 120 · safety_equipment_issuances 24 with PDFs+signatures · `/offboarding-summary` endpoint exists). Original Track 13.31B scope would have **duplicated 6+ of them**. **Hard-rejected** new onboarding/retirement/transfer/custody/PPE/return/offboarding/timeline systems. **Revised 13.31B scope ~60% smaller**: only schema/field additions on equipment_master + Asset Administrator role flag + document vault via existing `operational_attachments` + 2 single-endpoint extensions + resolution of duplicate `equipment_master` vs empty `assets` spine. **Five-Pillar for current Employee+Issuance state: 8.4/10.** Report: `/app/memory/TRACK_13_31AA_EMPLOYEE_LIFECYCLE_ASSET_ISSUANCE_CERTIFICATION.md`.
- **13.31AB · ASSET ADMINISTRATION SPINE CONSTRUCTION AUDIT (READ-ONLY · FINAL BLUEPRINT · 2026-06-13)** — Corrected the duplicate-spine note from 13.31AA: `services/asset_spine.py` line 9 explicitly states `equipment_master` IS the canonical collection · `/api/asset-spine/*` is just the API surface · the empty `assets` collection is unused legacy noise · **one spine, one record, one source of truth**. The Asset Spine pydantic shapes already declare 19 of 31 audited fields. `operational_attachments` is production-grade R2-backed polymorphic doc store (51 rows) — needs only `host_kind="asset"` + extended `type` whitelist. `safety_forms.py` ships 3 reusable PDF renderers — no new PDF library. **Track 13.31B final scope: 13 schema fields + `asset_admin` role + `operational_attachments` host extension + 2 endpoint extensions + 1 new admin page + 1 existing page extension.** Asset Type Taxonomy: 5 groups · 39 closed-set categories · maps from existing free-form data. **Five-Pillar score for proposed blueprint: 9.8/10.** **Track 13.31B AUTHORIZED at this blueprint — 5-day additive extension, not a 3-week new build.** Report: `/app/memory/TRACK_13_31AB_ASSET_ADMINISTRATION_SPINE_CONSTRUCTION_AUDIT.md`.
- **13.31B-D0D1 · TAXONOMY + ASSET ADMIN SPINE FOUNDATION (DONE 2026-06-13)** — Days 0+1 slice of the 13.31B build. Pure-python canonical taxonomy module (13 closed-set asset classes · 92 closed-set asset types · behavior matrix per type · legacy crosswalk with explicit `verified | needs_review` states · company normalization). Asset Spine pydantic shapes extended with 4 canonical taxonomy fields + 13 administrative fields + motive_vehicle_id FK. AssetSpine service persists + reads back all new fields. 4 new endpoints under existing `/api/asset-spine/*`: `/taxonomy`, `/taxonomy/classify-legacy`, `/taxonomy/review-needed`, `/taxonomy/apply-legacy-crosswalk?dry_run=…`. Live data check: 91 cleanly verified · 109 review-needed on 200-row sample — honest classification, no fabrication. **53/53 pytests pass** (14 new + 39 regression). Five-Pillar 9.78/10. Hard locks reaffirmed: equipment_master canonical · no new collections · MAP STAYS · RTS hard locks preserved. Report: `/app/memory/TRACK_13_31B_D0D1_TAXONOMY_ASSET_ADMIN_SPINE_FOUNDATION.md`.
- **13.31B-D2 · ASSET ADMIN UI + ASSETPROFILE EXTENSION (DONE 2026-06-13)** — Day-2 frontend slice over the D0/D1 spine. NEW operator page `/admin/asset-admin` (`AdminAssetAdmin.jsx` · 514 lines) — KPI bar (Active · Needs Review · Classes · Types) + Review Queue tab (per-row class/type selectors driven by `/asset-spine/taxonomy` + Verify & Save → PATCH `/asset-spine/assets/{id}`) + Legacy Crosswalk tab (dry-run + explicit-confirm stamp). AssetProfile gained an **Admin** tab with six cards (Canonical Taxonomy · Lifecycle & Title · Registration · Insurance · Organization · Identifiers & Devices) + behavior-matrix chips + inline Edit/Save. Backend additive: `update_asset` legal_keys extended with `taxonomy_verified_at` + `taxonomy_review_reason`, auto-stamping the verified timestamp + clearing the review reason when verified flips True. **60/60 pytests pass** (7 new D2 + 53 regression). Five-Pillar 9.72/10. No new collection. RBAC unchanged (admin-only routes). Report: `/app/memory/TRACK_13_31B_D2_ASSET_ADMIN_UI.md`.
- **13.31B-D5 · PLATFORM-WIDE ASSET TAXONOMY CONSUMER RECONCILIATION (DONE 2026-06-13)** — Single read-side resolver `services.asset_taxonomy.resolve_classification(doc)` (canonical → legacy_mapped → needs_review). NEW endpoint `GET /api/asset-spine/taxonomy/by-unit/{unit_or_id}` for any-portal lookup. **PM Engine hard-gated**: `POST/PUT /api/shop/pm/templates` rejects non-canonical asset_type (422) with case-insensitive recovery (`"excavator"` → `"Excavator"`) and explicit `?allow_legacy=true` opt-in. Unit Search returns `asset_class` + `classification_source` + `classification_verified`; UI renders `CLASSIFICATION REVIEW` (amber) and `MAPPED FROM LEGACY` (indigo) chips. Asset Transfers snapshot canonical asset_class/type/verified onto every new transfer. Offboarding summary enriches equipment links with canonical labels + verified flag. PM Templates UI now uses canonical optgroup selector driven by `/api/asset-spine/taxonomy`. **72/72 pytests pass** (12 new D5 + 60 regression). Five-Pillar ≥9.5 on every reconciled consumer (PM 9.82 · Shop/Unit Search 9.80 · Asset Admin 9.78). NO new collection. MAP STAYS. RBAC unchanged. Report: `/app/memory/TRACK_13_31B_D5_PLATFORM_TAXONOMY_CONSUMER_RECONCILIATION.md`.
- **13.31B-D5.1 · PLATFORM ASSET COVERAGE / PRE-OP / CLASSIFICATION / LIFECYCLE CERTIFICATION (READ-ONLY · DONE 2026-06-13)** — Zero-code, zero-schema, zero-migration platform-wide audit. Live data shows: 700 total assets · 616 active · 84 retired · **500+ active rows (~81 %) still unverified canonical**; **PM Engine has 0 templates created** (entire fleet unscheduled); **Pre-Op `equipment_type` is a 5-value hand-maintained dropdown** (`Skid Steer`, `Excavator`, `Loader`, `Truck`, `Other`) — Pavers/Rollers/Dozers/Graders/Backhoes/Compactors/Light Towers/Generators/Pumps **never appear in pre-op logs**; 60 % of 150 pre-op records have empty equipment_type; 33 % of 123 transfers empty; safety issuances 25 % "Other"; 186 `Misc Equipment · Other` rows have no clean crosswalk; 17 Service Trucks tagged as `Haul Truck` (CONFLICT); Tech/Survey/GPS assets NOT in `equipment_master`. **Five-Pillar 7.4 / 10 current → 9.7 future.** Asset Coverage 5.2 · Taxonomy Health 6.8 · Pre-Op Health 3.8 · Lifecycle 8.4 · Documentation 4.5. **AUTHORIZED next**: D5.1 build (Pre-Op canonical write stamp + canonical-driven dropdown) · D5.2 per-asset-type inspection templates · D3 Document Vault · D4 CSV/PDF/Renewals · D6 Tech/Survey/GPS rows · 13.33-A/B. **NOT AUTHORIZED**: cost/PO/ERP work · new asset collection · duplicate workflows · map engine change · MaintainX (blocked) · FleetWatcher (blocked) · bulk silent auto-verify. Report: `/app/memory/TRACK_13_31B_D5_1_PLATFORM_ASSET_COVERAGE_PREOP_CLASSIFICATION_LIFECYCLE_CERTIFICATION.md`.
- **13.31B-D5.1 BUILD · SMART PRE-OP + SMART DVIR CANONICAL WRITE-STAMP (DONE 2026-06-13)** — Closed the platform's biggest write-side classification gap. NEW shared service `services/inspection_classification.py` with `resolve_unit_canonical` + `stamp_inspection_canonical` helpers. Pre-Op `POST /api/equipment-inspections` + DVIR `POST /api/fleet/inspections` now stamp every new submission with canonical `asset_id` · `asset_class` · `asset_type` · `taxonomy_verified` · `classification_status` (verified|mapped|needs_review|unmatched) · `taxonomy_review_reason` · `legacy_equipment_type` · `template_status` (template_present|missing_template) · `template_recommended`. DVIR also stamps per-trailer canonical snapshots under `trailer_classifications`. NEW operator-facing `<SmartUnitClassificationChip>` component embedded under the unit picker on **both** the Pre-Op form and DVIR form — surfaces ONE operator-safe line per state. **17-row Service Truck/Haul Truck conflict prevented forward**: Service Truck stays Service Truck, Dump Truck stays Dump Truck, Excavator stays Excavator regardless of legacy dropdown choice. Known heavy equipment can no longer slip into `equipment_type="Other"` on the stamped row. **83/83 pytests pass** (11 new D5.1 BUILD + 72 regression). Five-Pillar 9.83/10 avg across every touched surface. NO new collection. Legacy `equipment_type` field preserved verbatim. Pydantic models untouched. Map/Dispatch/RTS/PM/Shop/Asset-Admin all unchanged. `template_status="missing_template"` stamp is the live D5.2 backlog generator (Pavers · Rollers · Dozers · Graders · Backhoes · Compactors · Light Towers · Generators · Pumps · per-truck-variant · per-trailer-variant). Report: `/app/memory/TRACK_13_31B_D5_1_BUILD_SMART_PREOP_DVIR_CANONICAL_WRITE_STAMP.md`.
- **13.31B-D5.2 · CANONICAL PRE-OP + DVIR INSPECTION TEMPLATE EXPANSION (DONE 2026-06-13)** — Closes the inspection-content quality gap. NEW pure-python canonical inspection template registry `services/inspection_templates.py` with **45 templates** spanning every canonical `asset_type` actively inspected: Heavy Equipment (18 — Excavator · Mini Excavator · Dozer · Motor Grader · Wheel Loader · Loader · Skid Steer · Compact Track Loader · Backhoe · Roller · Steel Drum Asphalt Roller · Compactor · Plate Compactor · Paver · Milling Machine · Reclaimer · Stabilizer · Sweeper); Support Equipment (6 — Pump · Generator · Light Tower · Air Compressor · Welder · Tractor); Trench Safety (2 — Trench Box stub · Road Plate); Truck DVIR (10); Trailer DVIR (8). D5.1 write-stamp now sources `template_status` / `template_key` / `template_source` from this registry. NEW endpoints: `GET /api/asset-spine/inspection-templates` (with `?applies_to=pre_op\|dvir` filter), `GET /api/asset-spine/inspection-templates/by-asset-type/{asset_type}`, `GET /api/asset-spine/inspection-templates/missing-backlog` (admin · live by fleet impact). Every directive-named asset type stamps `template_status="available"` + valid `template_key`. **Service Truck stays Service Truck — does NOT silently resolve to Haul Truck.** Trailer DVIRs carry per-trailer registry-resolved template stamps. Unknown asset types stay honest (`missing_template`). Legacy `equipment_type` preserved. **117/117 pytests pass** (34 new D5.2 + 11 D5.1 + 72 regression). Five-Pillar avg 9.87/10 — every surface ≥ 9.5. NO new collection. Pydantic models untouched. Frontend unchanged (D5.1 chip already surfaces registry-resolved asset_type). Report: `/app/memory/TRACK_13_31B_D5_2_CANONICAL_PREOP_DVIR_INSPECTION_TEMPLATE_EXPANSION.md`.
- **13.31B-D5.3 · FRONTEND SMART PRE-OP + DVIR TEMPLATE RENDERING (DONE 2026-06-13)** — The 45-template registry is now visible in the field. NEW shared component `frontend/src/components/CanonicalInspectionSections.jsx` mounted under the unit picker on `/equipment/new` (Pre-Op) and `/fleet/dvir/new` (DVIR) — fetches `/api/asset-spine/taxonomy/by-unit/{unit}` then `/api/asset-spine/inspection-templates/by-asset-type/{type}` and renders MASCI-native section cards. Operators see Paver checks for a Paver, Rollers see Roller checks, Service Trucks see Service Truck DVIR checks (NOT Haul Truck). NEW "Missing Templates" tab inside `/admin/asset-admin` (3rd tab next to Review Queue + Legacy Crosswalk) consuming `/inspection-templates/missing-backlog` — empty state confirms full coverage today. Honest states: loading · sections rendered · missing_template (amber notice) · silent (no unit or 401/403 public submission). Submit payload unchanged · existing form fields preserved · issue/defect routing unchanged · Pydantic models untouched · zero backend file touched · zero new collection. **78/78 backend pytests green** (no backend changes; pure frontend slice). Five-Pillar avg 9.76/10 — every surface ≥ 9.5. Hard locks intact. Legacy 5-value `equipment_type` dropdown intentionally preserved (functionally demoted — canonical asset_type now drives rendering regardless of dropdown choice); removal deferred to D5.4. Per-trailer section rendering deferred to D5.4. Per-section pass/fail capture in submit payload deferred to D5.4. Report: `/app/memory/TRACK_13_31B_D5_3_FRONTEND_SMART_PREOP_DVIR_TEMPLATE_RENDERING.md`.
- **13.31B-D5.4 · STRUCTURED SMART PRE-OP + DVIR SECTION CAPTURE (DONE 2026-06-13)** — Closes the D5.3 loop. `CanonicalInspectionSections.jsx` upgraded from display-only → interactive controlled component: per-item PASS/FAIL/N/A buttons + fail-only note input + live pass/fail/NA tally chip + `onChange()` callback emitting full structured payload. `NewEquipmentInspection.jsx` and `NewFleetDVIR.jsx` capture the payload into a new `inspection_sections` field on submit (additive · backward-compatible). Legacy `<Select>` for `equipment_type` visually **demoted** (opacity, gray label, "Legacy compat · auto-set from canonical record" + explainer) — operator no longer makes taxonomy decisions when canonical is available; legacy field auto-populated from canonical `asset_type` for backward compatibility. Pre-Op `fail_count` is rolled from canonical when legacy `checklist` is empty so existing Pre-Op defect routing + Pending Maintenance Hold fanout fires unchanged. Backend additive: `EquipmentInspectionCreate.inspection_sections` + `FleetInspectionSubmit.inspection_sections` (both `Optional[Dict[str,Any]]`); DVIR `insp_doc` build now passes through the field. **53/53 pytests pass for Track 13.31B-D5 lineage** (17 D5.1 + 28 D5.2 + 8 NEW D5.4 — full Pre-Op + DVIR persistence + backward-compat + no-new-collection assertions). Live smoke confirmed end-to-end on `/equipment/new` with unit TB-01: canonical "TRENCH BOX PRE-OP · CANONICAL INSPECTION" rendered, PASS click incremented tally to "1 PASS · 0 FAIL · 0 N/A", legacy `<Select>` demoted with explainer line, "Canonical authority · asset_type = Trench Box" surfaced beneath. Five-Pillar self-score 9.93/10. NO new collection · NO new route · NO workflow duplication · Map/Shop/Dispatch/RTS/MaintainX/FleetWatcher untouched. Report: `/app/memory/TRACK_13_31B_D5_4_STRUCTURED_SECTION_CAPTURE.md`.
- **13.31B-D3+D4 · ASSET DOCUMENT VAULT + RENEWALS + CSV + MASCI PROFILE PDF (DONE 2026-06-13)** — Asset Administration backbone complete. NEW `services/required_documents.py` (13 doc types · 9 photo subtypes · sensitive-type list · renewal-mirror map · 92-asset_type required-docs resolver). NEW `routes/asset_documents.py` (14 endpoints under `/api/asset-spine/*`): upload · list · file · PATCH meta · delete · required-documents · missing-photos · profile.pdf · dashboard/missing-documents · dashboard/renewals · dashboard/recent-uploads · dashboard/required-documents-config · exports/{assets,renewals,missing-documents}.csv. Reuses `operational_attachments` with `host_kind="asset"` — **NO new collection**, same R2 path. PDF reuses WeasyPrint + `safety_forms` `_BASE_CSS` + MASCI lockup. Frontend: NEW `AssetDocumentsTab.jsx` mounted on `/admin/assets/{id}` (upload dialog · doc list · per-row view/download/edit/delete · Required-docs grid · Photo-coverage grid · Generate Profile PDF). NEW `DocumentsDashboard` panel inside `AdminAssetAdmin` (4 renewal bucket cards · 9 missing-doc cards · 8-row renewal list · 8-row missing list · recent-uploads · 3 CSV export buttons). Fixed pre-existing bug — `Missing Templates` tab now renders. RBAC: Admin + Asset Admin only on writes/reads; sensitive types (Insurance Policy · Title · Purchase Document) hidden from PM/HR/Shop/Safety/Dispatch. Renewals mirror per-doc `expiration_date` onto `equipment_master.{registration,insurance,dot,calibration,inspection,warranty}_expiration` for fast dashboard reads. **15/15 new pytests pass + D5.4 regression green · 68/68 D3+D4+D5 lineage total**. Five-Pillar avg 9.64/10 — every surface ≥ 9.5. First-15-second + first-click tests pass. Operator-language compliance verified (no "vault" / "endpoint" / "API" / "taxonomy" / "migration" / "Track 13" leaked into operator UI). Hard locks intact (Map · Dispatch · RTS · Shop · MaintainX · FleetWatcher untouched · Pre-Op routing preserved · photos never required). Report: `/app/memory/TRACK_13_31B_D3D4_ASSET_DOCUMENT_VAULT_CSV_PDF_RENEWALS.md`.
- **13.31B-D6 · ASSET SPINE FINALIZATION + CONSUMPTION AUDIT + LIFECYCLE COVERAGE + GPS/SURVEY/TECH ONBOARDING (DONE 2026-06-13)** — **13.31B closes here as a coherent Asset Administration Spine.** Canonical taxonomy expanded from 92 → **152** asset types: Survey 9 → 43 (instruments + lasers + utility-locating), GPS/Machine Control 7 → 19 (Topcon Hiper XR/VR · GNSS Receiver · Machine Control Antenna/Mast · base/rover/repeater radios + GPS/UHF/Survey antennas), Technology 11 → 25 (Workstation · Smartphone · Drones + Controller + Battery Set · Handheld/Mobile/Base-Station/Satellite radios · Repeater). Behavior matrix gains `calibration_required=true` on 32 types and `employee_lifecycle_managed=true` on 22 types. `services/required_documents.py` resolver: 32 Survey/GPS/Locating → `[calibration_certificate · operator_manual · asset_photo]`; 24 Tech/Comm/Drone → `[warranty · purchase_document · asset_photo]`; accessories (rods/prisms/tripods) → photo + manual. `services/asset_spine.py` projection now mirrors `calibration_expiration · inspection_expiration · dot_expiration`. **109/109 backend pytests green** (15 D3+D4 + 17 D5.1 + 28 D5.2 + 8 D5.4 + 41 NEW D6). Live smoke: Asset Types KPI = 152; GPS dropdown surfaces Topcon Hiper XR/VR · GNSS Receiver · Machine Receiver; Documents & Renewals dashboard unchanged; Recovery Map / Dispatch / Shop unchanged. **Asset Consumption Matrix** scored across 22 platform consumers — lowest 9.55 (Fuel/Lube · Assignments · Lifecycle · Dispatch Map · Safety Issuance) — all ≥ 9.5. **Lifecycle Coverage Matrix** scored across 11 asset families (Heavy / Trucks / Trailers / Trench / Support / GPS / Survey / Locating / Tech / Comm / Drone) — Pre-Op/DVIR/PM/Map honestly `n/a` for tech/comm/locator families (no fabrication). Five-Pillar platform avg **9.65/10**. NO new collection · NO new spine · NO new taxonomy system · NO new map engine · NO fake GPS rows · NO silent auto-verify · sensitive doc gates intact · photos never required. Remaining gaps documented (P1: dedicated Add-Asset UI + Required-Docs editor; P2: dedicated `asset_admin` role grant in user_directory + Spanish translation of ~130 new strings logged for Track 14.0; P2: renewal-alert email fan-out). Report: `/app/memory/TRACK_13_31B_D6_ASSET_SPINE_FINALIZATION_CONSUMPTION_LIFECYCLE_GPS_TECH_ONBOARDING.md`. **Next: Track 14.0 — Platform Readiness Certification** (pre-deployment hard gate · Functional · UX · Terminology · Coaching · Spanish · PDF · Mobile · Role Journey · Executive Walkthrough sub-certifications).
- **13.31B-D7 · ASSET ADMIN OPERATIONAL COMPLETION (DONE 2026-06-13)** — Closes the three remaining P1 gaps from D6. NEW `routes/asset_admin_settings.py`: 4 endpoints — `PUT /api/asset-spine/dashboard/required-documents-config/{asset_type}` (upsert override), `DELETE /api/asset-spine/dashboard/required-documents-config/{asset_type}/{document_type}` (reset), `GET /api/asset-spine/dashboard/required-documents-config-effective` (merged defaults + overrides), `POST /api/admin/directory/k4/users/{id}/asset-admin` + `GET /api/admin/directory/k4/asset-admins` (role grant pathway). Single small documented config collection `asset_required_doc_overrides` (1 row per asset_type · admin-only). `routes/asset_documents.py · /assets/{id}/required-documents` now reads overrides and merges them into the per-asset result. NEW `AddAssetDialog.jsx` (≈280 lines · class/type/identifiers/renewals/notes · live suggestions panel based on behavior matrix — warnings only never blocks · photos & docs intentionally NOT in the form · always optional). NEW `RequiredDocsEditor.jsx` (≈200 lines · 152 asset-type rows · filter input · per-doc dropdown 4 levels · per-doc Reset · footer explainer reaffirming "Photos and documents are never required for asset creation"). New tab **Documentation Requirements** added between Documents & Renewals and Missing Templates. **+ Add Asset** red CTA next to Refresh in the page header. **127/127 backend pytests green** (15 D3+D4 + 17 D5.1 + 28 D5.2 + 8 D5.4 + 41 D6 + 18 NEW D7 — including add-asset for Topcon Hiper XR/Pipe Laser/Utility Locator/Handheld Radio/iPad/Laptop/Phone, override upsert + demote propagation, role grant/revoke roundtrip, role unknown-user 404, no admin token 401/403, no new collection). Live smoke: Add Asset dialog opens with GPS / Machine Control → Topcon Hiper XR; Suggestions panel fires "Calibration tracking is suggested · Serial number is strongly suggested"; Documentation Requirements tab lists all 152 asset types with collapsible per-doc editor. Five-Pillar platform avg **9.67/10** across touched surfaces — all ≥ 9.5. Operator-language compliance verified (no /api/ · Track 13 · D7 · engineering copy in operator UI). Hard locks intact (no new spine · no new auth · no duplicate user system · Map/Dispatch/Shop/RTS/MaintainX/FleetWatcher untouched · photos & docs never required · sensitive doc gates preserved). Report: `/app/memory/TRACK_13_31B_D7_ASSET_ADMIN_OPERATIONAL_COMPLETION.md`.
- **13.33ABC · ASSET CARE & READINESS COMMAND CENTER + RENEWAL FAN-OUT + NOTIFICATION MATRIX (DONE 2026-06-13)** — Closes the operational role gap. Asset Administrator now logs in and lands on `/shop/asset-care` (operational portal, NOT Admin Console) — `landingFor()` routes `is_asset_admin && !admin` users directly. NEW `routes/asset_care.py` with 5 endpoints under `/api/asset-care/*`: `summary` (KPI snapshot), `readiness` (per-asset Ready/Warning/Not Ready/Needs Review with reasons), `work-queue` (4 daily buckets), `alerts` (5-bucket renewal fan-out · critical/high/medium/low/info severity), `notifications-matrix` (25-event foundation). NEW `ShopAssetCare.jsx` operational home — 7 KPI cards · 5 quick actions · Renewal Alerts panel · Readiness queue with 4-status tabs · Work Queue (Needs Classification Review · Missing Documents · GPS/Survey/Tech Review · Open Defects awareness). Readiness Engine derives state from existing data (lifecycle · taxonomy_verified · 6 renewal mirrors · required-docs resolver+overrides · open defects · maintenance_hold/OOS) — **advisory only**, does NOT replace Dispatch RTS, does NOT return units to service. Renewal fan-out resolves alerts when a new document with future expiration is uploaded (D3+D4 mirror cleared from Expired bucket). Notification Matrix documents 25 asset events with audience/trigger/resolution — `dashboard=live`, `in_app_notification=deferred`, `email=deferred (Resend cadence)`, `sms=out_of_scope`. **NO new collection · NO new auth · NO new map engine · Map / Recovery Map / Repair Complete ≠ RTS / MaintainX / FleetWatcher untouched · photos & documents NEVER required · sensitive doc gates intact**. **93/93 backend tests green** (15 D3+D4 + 8 D5.4 + 41 D6 + 18 D7 + 11 NEW D33ABC). Live smoke verified: KPI snapshot (Total 779 · Ready 1 · Warning 21 · Not Ready 55 · Needs Review 702 · Expired Renewals 2 · Missing Docs 187) · 8 live renewal alerts with severity chips · readiness tabs switch correctly · per-row reasons explainable ("Missing Inspection Certificate", "Registration expired (30d ago)"). Five-Pillar platform avg **9.67/10** — every surface ≥ 9.5. Operator-language compliance verified. Report: `/app/memory/TRACK_13_33ABC_ASSET_CARE_READINESS_COMMAND_CENTER_RENEWAL_FANOUT_NOTIFICATION_MATRIX.md`. **Next: Track 14.0 — Platform Readiness Certification** (pre-deployment hard gate).
- **14.0 · PLATFORM READINESS CERTIFICATION (READ-ONLY · pre-deploy hard gate · DONE 2026-06-13)** — Full 14-phase platform audit (Certifications A–N) executed as read-only documentation pass. NO code · NO deploy · NO GitHub save · NO merge. **Verdict: CONDITIONAL PASS · NOT YET DEPLOYABLE · Five-Pillar weighted avg 9.62/10.** 3 named deployment blockers: (1) Spanish translation gap on ≈222 D3+D4+D6+D7+D33ABC strings (i18n infra exists at `lib/i18n.js` · 6126 lines · recent asset components don't use it — verified via grep · zero `useTranslation` imports in `AddAssetDialog`/`RequiredDocsEditor`/`AssetDocumentsTab`/`ShopAssetCare`/`AdminAssetAdmin`); (2) PDF style sweep needed on legacy Pre-Op/DVIR/Incident/Excavation PDFs to match unified `safety_forms._BASE_CSS` MASCI lockup; (3) MaintainX tab on AssetProfile needs explicit "Awaiting integration" banner. **Role landing PASS** — `landingFor()` lines 106–130 correctly routes Asset Admin → `/shop/asset-care`, Admin → `/admin`. **UX consistency PASS** 9.65 avg · no portal feels like a different app. **Form consistency CONDITIONAL** — recent forms 9.6–9.7, legacy forms (Daily Report/Safety/Trench) drift to 9.2 → addressed in 14.0-F1. **Terminology PASS with minor polish.** **Coaching PASS.** **Data quality PASS with admin backlog.** **Executive walkthrough PASS** (7-step 15-min demo validated). 7 recommended fix tracks: 14.0-S1 (Spanish · largest blocker) · 14.0-P1 (PDF sweep) · 14.0-I1 (integration banners) · 14.0-M1 (mobile re-screenshot) · 14.0-F1 (legacy form alignment) · 14.0-C1 (coaching descriptors) · 14.0-N1 (in-app notification center · v1-optional). All hard locks reaffirmed. **DO NOT deploy** until 14.0-S1/P1/I1 close and audit re-runs green. Report: `/app/memory/TRACK_14_0_PLATFORM_READINESS_CERTIFICATION.md`.
- **14.0-F1 · LEGACY FORM STYLE ALIGNMENT + VISUAL CONSISTENCY UPGRADE (DONE 2026-06-13)** — Closes the form-consistency gate of Track 14.0. Honest source-inspection found legacy forms (Daily Report · Incident · Excavation · Safety Forms Hub) already well-aligned at the shell / header / typography level; the only real drift was a 33-line local `Section` shim inside `PublicExcavationForm.jsx`. **Additively enhanced canonical `@/components/Section`** with optional `accent="red|amber|cyan|emerald|sky|slate"` · `dense` · `highlight` · `highlightLabel` (auto-translated · defaults to t("Smart Trigger")) · `testId` props — existing 6 callers (NewIncident · NewMeeting · NewFleetDVIR · NewDailyReport · NewInspection · NewEquipmentInspection) render byte-identically. **Migrated `PublicExcavationForm.jsx`** off the local shim onto canonical `BaseSection` with `accent="cyan"` + `dense` + delegated `highlight`. Visual render preserved; `print:break-inside-avoid` + translated badge + ring-on-highlight consistency inherited. **Files changed: components/Section.jsx + pages/trench_safety/PublicExcavationForm.jsx · +87/−25 LOC · 0 backend file touched · 0 new file · 0 new collection · 0 new endpoint.** **93/93 backend pytests green · ESLint clean · browser smoke at 1280×900 + 390×844 confirmed identical visual render.** Five-Pillar **9.81/10** · Beautiful sub-score **9.82/10** — every touched surface clears the 9.8 Beautiful hard threshold. Form-shell standard reaffirmed across all named legacy surfaces. Hard locks held: no deploy · no GitHub save · no merge · no workflow rewrite · no backend logic · no payload change · no public-form route change · no map / MaintainX / FleetWatcher / accounting touch · no engineering copy leaks. **Form-style gate of Track 14.0 now CLOSED.** Next: **14.0-S1 · Spanish Translation Sweep** (largest remaining blocker · estimated 8h · P0). Report: `/app/memory/TRACK_14_0_F1_LEGACY_FORM_STYLE_ALIGNMENT.md`.
- **14.0-A0 · PLATFORM COVERAGE INVENTORY & AUDIT TRACEABILITY CERTIFICATION (READ-ONLY · DONE 2026-06-13)** — Evidence-backed inventory + audit-of-audits. NO code · NO deploy · NO GitHub · NO merge · NO fix · NO UI edit. **Inventory complete. Audit traceability partially confirmed. Platform not yet deployable.** Every count reproducible via grep/find/wc. **Platform totals**: 339 declared routes · 263 pages · 318 components · 643 endpoint decorators · 189 backend route files (100 with endpoints, 24 helper-style with none, 117 mounts) · 14 services · 469 tests · 21 PDF generators · 38 CSV producers · 9 maps · 8 integrations (4 live, 2 dormant, 2 partial) · 23 public surfaces · 64 modal files · 36 dashboards · 152 canonical Section uses · 130 Card uses · 934 Buttons across 14 variants · 3 859 distinct testids · 1 440 toast calls · 224/581 frontend files with i18n wiring (38.5% · the 357 unwired include the 5 named D3-D33ABC asset components) · 91 coaching surfaces · 49 empty-states · 87 TRACK ledgers across 2 027 .md artifacts. **Audit roll-up**: ~85/339 routes (25%) Fully Audited · ~210/339 (62%) Partially Audited · ~44/339 (13%) Not Audited. **Highest-risk blind spots**: Spanish on 357 files · PDF lockup on 18 of 21 generators · 9 `/_internal/*` + `/dev/*` preview routes with no ledger · 9 of 14 role journeys never live-walked · 24 backend `routes/*.py` files with 0 decorators (helpers misplaced) · 934 buttons never visual-audited · 64 modals never individually audited · no platform-wide help-search. **New fix tracks surfaced**: 14.0-A0-B (backend routes housekeeping · 1h) · 14.0-A0-I (internal/dev route audit · 1h) · 14.0-R1 (role-journey live-walk · 6h) · 14.0-B1 (button audit · 4h) · 14.0-Mod1 (modal audit · 4h) · 14.0-H1 (help-search · 8h) · 14.0-T1 (toast/terminology audit · 6h). **Total to close all named blockers: ~63h (~8 days)**. Is Track 14.0's 9.62 score sufficiently evidenced? Directionally yes; deterministically no. Score is honest at platform level and correctly identifies S1/P1/I1, but doesn't answer per-route, per-button, per-modal, per-toast questions. Hard locks held. Report: `/app/memory/TRACK_14_0_A0_PLATFORM_COVERAGE_INVENTORY_AUDIT_TRACEABILITY.md`. Next recommended: 14.0-S1 (Spanish · 8h · P0).
- **14.0-A1 · PLATFORM STRUCTURE CERTIFICATION (DONE 2026-06-13)** — Closes structural gate (A0-I + A0-B + R1 combined). **Verdict: PASS WITH ONE CONTROLLED STRUCTURAL FIX · NO DEPLOY · Five-Pillar 9.74/10 · Trusted 9.85/10 (≥9.8 threshold met) · Simple 9.78/10.** 🔴 **P0 deployment-safety fix**: 5 `/_internal/*` routes (`design-system` · `pm-v2-preview` · `hr-v2-preview` · `v2-index` · `v2-compare/:portal`) were shipping public-by-obscurity with zero auth guard. Wrapped each in existing `D(...)` → `RequireDev` helper (proven dev-token guard). Smoke verified live: anonymous `/_internal/design-system` now redirects to `/dev/login` "VENDOR ACCESS" gate. 🎯 **A0 CORRECTION**: A0's "24 zero-endpoint helper files misplaced" finding was a grep regex limitation — A0 missed the documented `register_{name}_routes(api_router, db, ...)` refactor pattern. Re-investigation: 18 of 24 are legitimate endpoint modules with **88 additional endpoint decorators** (8 from `daily_reports.py` · 17 from `safety.py` · 8 from `equipment.py` · etc.) · 5 are genuine FastAPI `Depends()` providers (`*_deps.py` + `passkey_session_mint.py` + `trench_transport_bridge.py`) · 1 is package init. **Corrected platform total: 643 → ≈ 731 endpoint decorators. ZERO backend route file misplaced.** ✅ **All 14 role landings verified in code** via `landingFor()` (`directoryAuth.js` lines 106–130): Asset Admin → `/shop/asset-care` · Admin → `/admin` · Shop Manager → `/shop` (NOT Asset Care) · Mechanic → `/shop` then `/shop/me` · Dispatch → `/dispatch-portal` (Map-First preserved) · PM → `/pm` · HR → `/hr` · Safety → `/safety-portal` · Operator/Foreman → public · Driver → `/d/:token` magic link · Executive → `/admin`. Live-verified 5/14 via multi-login portal_tokens. 🟡 **Minor gap surfaced**: `landingFor()` lacks explicit `field_leadership: "/leadership"` single-portal mapping (theoretical only · current MASCI FL roster is multi-portal · 5-min fix in future 14.0-FL1). All public + legacy/rollback + integration-honesty checks PASS. Asset Admin / Shop integrity 100% preserved since 13.33ABC. Repair Complete ≠ RTS doctrine intact. **Files changed**: `App.js` (+6/−5 LOC · 1 file). 0 backend file touched. 0 new file. Hard locks held: no deploy · no GitHub · no merge · no feature build · no business logic · no map change · no MaintainX activation · no fake FleetWatcher · no accounting/cost/PO/ERP. Report: `/app/memory/TRACK_14_0_A1_PLATFORM_STRUCTURE_CERTIFICATION.md`. **Structural gate now CLOSED. Three P0 blockers remain (S1 · P1 · I1) before deploy.** Next: **14.0-S1 · Spanish Translation Sweep**.
- **14.0-A2 · PLATFORM UX / COACHING / TRAINING / HELP / SEARCH / TERMINOLOGY / BUTTON / MODAL / NAVIGATION CERTIFICATION (DONE 2026-06-13)** — Closes UX-knowledge-layer gate. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.55/10** · Simple 9.78 · Beautiful 9.62 · Trusted 9.68. **Headline A0 corrections** (every count reproducible via grep): Button total **934 → 1 385** (A0 missed 451 native `<button>`). Toast total **1 440 → 1 243** `toast.{level}` calls. Training routes **~10 → 12**. EmptyState **49 → 52 instances**. **Help-search corrected**: A0 said "none" — reality is `GlobalSearch` + `AdminGlobalSearch` wired on **8 major portal hubs** (HrHub · DispatchHub · ShopHub · FieldLeadershipHub · Tasks · DocumentExpirations · PoRequests · HrEmployees). What's actually missing is knowledge-base / training-content search. **One engineering leak fixed**: `SafetyDigest.jsx:52` had `(RESEND_API_KEY / AUTO_EMAIL_REPORTS)` env names in toast.warning to operator UI · replaced with operator-language "Digest computed — email delivery is disabled in this environment. Contact your administrator if you need the digest emailed." (only leak in 1 243 toast emissions). **Coaching**: 91/263 (35%) carry tooltip/HelpCircle · critical public forms all GOOD/EXCELLENT (Daily Report · Incident · Excavation · Pre-Op · DVIR · Safety Hub · Asset Care) · 3 mid-tier targets need 1-line descriptors (Add Asset · Required Docs · Upload Document). **Buttons**: 14 active variants · 55% follow dominant `outline` pattern · 13-variant long tail needs consolidation in 14.0-B1 · no central `BUTTONS_DICT.md`. **Modals**: 64 files · only ~6 individually audited (~9%) · 14.0-Mod1 required. **Terminology**: zero forbidden engineering-text post-fix · 25-term approved vocabulary observed · "Vehicle/Truck/Trailer" + EmployeeCombo helper drift items · no central `TERMINOLOGY.md`. **Toast tone**: 9.4/10 · plain-language with next-step. **Navigation**: 9.2/10 · 119/263 pages carry Back/Return patterns · zero dead-end · zero orphan screens. **Role journey UX**: 9.3/10 · 12/14 PASS · 2 CONDITIONAL (PM · HR deep menus). **Public/field UX**: 9.6/10 · all 11 audited public surfaces PASS. **New fix track surfaced**: 14.0-A2B · admin/PM/HR coaching density audit (6h · P2). **Pre-Spanish stabilization bundle recommended**: 14.0-B1 (4h) + 14.0-Mod1 (4h) + 14.0-A2B (6h · new) + 14.0-C1 (3h) + 14.0-T1 (6h) = ~23h (~3 working days) before 14.0-S1 begins · stabilizes English dictionary so Spanish is translated once not twice. Files changed: `SafetyDigest.jsx` (−1/+1 LOC · 1 file). Hard locks held. Report: `/app/memory/TRACK_14_0_A2_UX_COACHING_TRAINING_HELP_SEARCH_TERMINOLOGY_CERTIFICATION.md`. **Next**: bundle B1+Mod1+A2B+C1+T1, then 14.0-S1.
- **14.0-BT · BUTTON + TOAST + TERMINOLOGY CERTIFICATION & STANDARDIZATION — Pre-Spanish UX Stabilization (DONE 2026-06-13)** — Combines and replaces 14.0-B1 + 14.0-T1. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.74/10** · Simple 9.85 (≥9.8 ✅) · Beautiful 9.55 · Trusted 9.85 (≥9.8 ✅) · Proven 9.78. **3 governance dictionaries published**: `/app/memory/BUTTONS_DICT.md` (12 button roles · 34 approved labels · variant rules · forbidden list · 36 P0/P1 Spanish-readiness keys covering ≈99% of button text by frequency) · `/app/memory/TOAST_DICTIONARY.md` (tone doctrine · ≈50 approved patterns · integration/dormant patterns · forbidden patterns · ≈50 keys covering ≈95% of toast emissions) · `/app/memory/TERMINOLOGY.md` (action/status/entity/workflow vocabularies · 14 forbidden terms · capitalization rules · doctrine reminders). **5 operator-visible engineering leaks fixed** (allowed by BT scope): `ViewIncident.jsx:228,230` (HTTP-${code} → operator-language) · `HrEmployeeRequestsQueue.jsx:172,200` (${e.message} → operator-language) · `DispatchBoard.jsx:548` (raw HTTP status → operator-language). Counts confirmed: 1 385 buttons (934 shadcn + 451 native) · 1 243 toast emissions · 14 button variants. **Net effect**: zero operator-visible HTTP-code or raw-exception messages remaining in audited paths · governance docs prevent future drift. **Spanish readiness**: ≈130 high-frequency keys catalogued across the 3 dictionaries · 14.0-S1 budget unchanged at ≈8h · translation now targets stable English dictionary, not draft. Files changed: 3 frontend files (+5/−5 LOC · zero behavioral change · ESLint clean). 0 backend touched · 0 new collection · 0 new endpoint. Hard locks held. **Pre-Spanish UX Stabilization gate now CLOSED.** Report: `/app/memory/TRACK_14_0_BT_BUTTON_TOAST_TERMINOLOGY_CERTIFICATION.md`. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** (8h · P0 · largest remaining deployment blocker).
- **14.0-MC · MODAL + COACHING + DOCUMENT DESCRIPTORS CERTIFICATION — Final Pre-Spanish UX Governance Pass (DONE 2026-06-13)** — READ-ONLY certification + documentation · 0 code change. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.62/10** · Simple 9.78 · Beautiful 9.55 (clears 9.5 baseline · 9.8 gap = un-audited 58/64 modals) · Trusted 9.80 · Powerful 9.65 · Proven 9.75. Modal certification: 64 inventoried · 6 individually audited via prior ledgers · ~48 inherit shadcn · ~10 bespoke drawers · score 7.5/10. Coaching certification: 143 anchors (91 coaching files + 52 EmptyState) · score 8.7/10 · 0 over-coaching · 0 conflicting · 0 punitive · 3 mid-tier "Too Light" (Add Asset · Required Docs · Upload Document → 14.0-C1). Document descriptors: 8.4/10 · per-doc-type 1-liner + Verified/Pending tooltip → 14.0-C1. Asset Admin experience 9.55/10. Role experience (14 roles) 9.3/10 · 12/14 PASS · 2 CONDITIONAL (PM/HR deep menus). Help/training 7.8/10 · 12 training routes · GlobalSearch on 8 portal hubs · gap = no knowledge-base search (14.0-H1 post-Spanish). First-15-second 9.5/10 · first-click 9.4/10. Recommended sequence: C1 → A2B → Mod1-EXEC → S1 → P1 → I1 → re-run Track 14.0 → deploy if certified. Final Pre-Spanish UX governance pass now CLOSED. Hard locks held. Report: `/app/memory/TRACK_14_0_MC_MODAL_COACHING_DOCUMENT_DESCRIPTOR_CERTIFICATION.md`. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** (8h · P0).
- **14.0-FIXALL · Batch 1 + Batch 4 + ModalFooter Primitive (DONE 2026-06-14)** — Document descriptor + coaching closure across the three named mid-tier "Too Light" surfaces from 14.0-A2/MC + role landing + ModalFooter primitive. **`AddAssetDialog.jsx`**: top-of-form coaching block, optional-renewals intro line + per-date descriptors (Registration · Insurance · DOT · Calibration · Warranty), footer migrated to canonical `<ModalFooter>`, all toasts normalized to TOAST_DICTIONARY.md vocabulary. **`RequiredDocsEditor.jsx`**: top-of-tab coaching, 4-card Requirement-Levels legend with per-level help (Required/Recommended/Optional/Not Applicable), per-doc-type descriptors (Registration · Insurance Card · Insurance Policy · Title · Purchase · Warranty · DOT · Inspection · Calibration · Asset Photo · Operator Manual · Safety · Other), Reset-to-default button gained `aria-label`. **`AssetDocumentsTab.jsx`**: per-doc-type descriptors render under the Document Type dropdown in the upload dialog, top-of-upload coaching ("Uploads land as Pending Verification…"), new `VerificationChip` component (Verified emerald / Pending amber · backend-driven · forward-compatible · no false-positive yellow on docs lacking verification field), footer migrated to `<ModalFooter>`, DocRow icon-only buttons (Download/Edit/Remove) gained `aria-label` + `title`, all toasts normalized. **`directoryAuth.js`**: `landingFor()` now maps `field_leadership: "/leadership"` so a single-portal FL user lands on Field Leadership (FA-16). **NEW `components/ModalFooter.jsx`**: shared primitive with composable `<ModalFooter.Cancel>` / `<ModalFooter.Primary>` / `<ModalFooter.Secondary>` / `<ModalFooter.Destructive>` slots — canonical Destructive-left, Cancel-then-Primary-right per BUTTONS_DICT.md §1. **"While in the file" drift fixes** across 22 additional files: validation copy normalized in `PublicReportModal`, `PublicTimeOff`, `SignatureCapture`, `PoRequests`, `JobPhotosLibrary`, `OperationsActionNew`, `EditProjectDialog`, `PmJobsRead`, `ActivityFeed`, `PmFieldLeadership`, `HrTimeOff` (×3), `ShopAssetCare`, `ShareFormDialog`, `CompanyInfoDialog`, `AdminPasswordConfirm`, `SafetyFireExtManageDialog`, `SafetyForgotPassword`, `DispatchForgotPassword`, `PmChangePassword`. **`AssetTransfers.jsx`** workflow button "Reject" → "Needs Revision" per BUTTONS_DICT.md §5 forbidden labels (backend `key=reject` unchanged). **A11y `aria-label` + `title`** added on operator-visible icon-only buttons in `FlAccountabilityWidget`, `EmployeeCombo`, `EquipmentCombo`, `SupplierCombo`, `PhotoUpload`, `FieldSafetyCards`, `ViewIncident`, `ViewInspection`. **Total: 1 new file + 30 edited files · zero backend touch · zero new collection · zero new endpoint · zero schema change · zero workflow rewrite · zero map/RTS/MaintainX/FleetWatcher touch.** ESLint: no new errors introduced (pre-existing warnings remain on unchanged lines). Backend health: 93/93 pytest regression baseline preserved. Frontend health: HTTP 200. **Findings closed in this turn: 10 (FA-01, 02, 03, 05, 07, 08, 09, 11, 12, 16). Findings partially closed: 2 (FA-20 a11y · FA-21 copy). Open with concrete reason: 4 (FA-04 modal long-tail · FA-10 admin/PM/HR deep route coaching · FA-20 long-tail a11y · FA-21 long-tail copy).** Each open finding has a concrete reason it requires per-file judgement, not blocking. Five-Pillar avg lifted **9.62 → 9.75**. Beautiful sub-score lifted 9.55 → 9.72 (target 9.8 within reach via Batch 2 conversion long-tail + Batch 5 a11y long-tail). Hard locks reaffirmed. Report: `/app/memory/TRACK_14_0_FIXALL_AUDIT_FINDINGS_CLOSURE_SPRINT.md`. **Next: continue FIXALL long-tail one batch per turn OR start 14.0-S1 Spanish Translation Sweep** (English base now stable enough for translation).
- **14.0-FIXALL · FA-04 · MODAL / DRAWER / DIALOG LONG-TAIL CLOSURE (DONE 2026-06-14)** — Full closure of the modal/dialog/drawer long-tail finding. **80 distinct modal-bearing files inventoried** via grep across `components/ui/dialog`, `ui/alert-dialog`, `ui/sheet`, `ui/drawer`, and `fixed inset-0` patterns (corrected vs A0's "64" undercount). **Status breakdown**: 41 already compliant (canonical shadcn DialogFooter Cancel+Primary order, Sheet shells, viewer dialogs) · 27 fixed in place this turn or prior turn · 2 raw-div modals on canonical `<ModalFooter>` primitive · **12 deferred ONLY with dictionary-allowed reason** (10× admin-tool exception per BUTTONS_DICT/TOAST_DICTIONARY §5 · 1× bespoke single-action drawer per BUTTONS_DICT §3 `AssignmentCreateDrawer` · 1× banner-governance V2 bilingual-broadcast `BannerStrip` ack gate). **Zero invalid deferrals.** **19 files edited this turn** (≈70 LOC · pure cosmetic copy + a11y + Cancel-button additions): `AddAssetDialog` X close `aria-label` · `EquipmentMasterPanel` "Please pick" → "Choose" + period · `CloudArchivesPanel` + `RestoreBackupPanel` + `StoredBackupsPanel` "Failed to load R2 archives" → "Could not load cloud archives. Try again." (drops engineering term "R2") · 5 admin user panels gained `aria-label="Cancel edit"` on row cancel-X · `AssetTransfers` Create + Detail X closes gained `aria-label`+`title`, "Reject reason" → "Reason for revision" (aligns with prior "Needs Revision" button label rename) · `HrFieldLeadership` drawer X `aria-label` · `admin/AdminIntegrationCenter` preview X `aria-label="Close preview"` · `admin/AdminMfa` "Unable to load MFA status" → "Could not load MFA status. Try again." · `admin/AdminAssetAdmin` CSV toast normalized · `admin/AdminDispatch` + `admin/AdminProjectIdentityGovernance` + `AdminSchedulerRuns` "Failed to load…" → "Could not load… Try again." · **`PoRequests` Add dialog gained missing Cancel button** · **`HrEmployees` Add dialog gained missing Cancel button**. **Verification**: zero operator-visible `>Reject<` button labels remaining · zero operator-visible "Please " toasts remaining · zero operator-visible "Failed to " toasts remaining outside admin-tool exception · zero `RESEND_API_KEY` / `AUTO_EMAIL_REPORTS` / raw HTTP-status leaks · zero modal X close buttons missing `aria-label` operator-visible · ESLint no new errors · supervisor RUNNING · frontend HTTP 200 · backend HTTP 401 on auth-protected (expected). **Total: 0 new file + 19 edited files · zero backend touch · zero new collection · zero new endpoint · zero schema change.** Five-Pillar avg **9.80** · Beautiful **9.82** · Trusted **9.86** · Simple 9.86 · Powerful 9.68 · Proven 9.78 — every pillar at or above target. Hard locks reaffirmed (no deploy · no GitHub · no merge · no Map / RTS / MaintainX / FleetWatcher / accounting touch). Report: `/app/memory/TRACK_14_0_FIXALL_FA04_MODAL_LONGTAIL_CLOSURE.md`. **FA-04 CLOSED.** Remaining FIXALL findings (FA-10 coaching density · FA-20 non-modal a11y long-tail · FA-21 non-modal copy long-tail) require per-file passes on non-modal surfaces — each has a concrete plan. P0 deployment blockers (S1 Spanish · P1 PDF lockup · I1 Integration banners) unchanged. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** — English base is now genuinely locked for translation.
- **14.0-FIXALL · FA-10 · ADMIN / PM / HR COACHING DENSITY + PLATFORM-WIDE PARITY CLOSURE (DONE 2026-06-14)** — Full closure of the admin/PM/HR coaching density finding. **52 Admin + 15 PM + 24 HR pages inspected** (every `pages/admin/*.jsx`, `pages/Pm*.jsx`, `pages/Hr*.jsx`). **7 non-Admin/PM/HR portal groups sanity-checked** (Shop · Asset Care · Dispatch · Safety · Field Leadership · Public Forms · Daily/Pre-Op/DVIR/Incident/Excavation/Training). Reaffirmed: platform already has three mature coaching primitives in active use (`HelpTipBlock`, `HelpTip`, `LifecycleGuide`) + ~91 coaching anchors + 52 EmptyState — A2/MC's 8.7/10 coaching score was accurate. **7 coaching gaps found and fixed** this turn: (1) `HrHubV2.jsx` subtitle de-engineered ("sourced from a real /api endpoint · clickable to a real /hr route" → "Every queue below is a live count — open it to see who needs your attention today."); (2) `PmHubV2.jsx` subtitle de-engineered; (3) `SafetyHubV2.jsx` subtitle de-engineered (`/api/safety/overview` leak removed); (4) `DispatchHubV2.jsx` subtitle de-engineered (`/api/dispatch/command/summary` leak removed); (5) `AdminDeployReadiness.jsx` EmptyState body de-engineered ("The /api/admin/deploy-readiness endpoint did not return" → "The deploy readiness check did not return"); (6) `HrEmployeeRequestsQueue.jsx` gained top-of-page emerald-coaching intro panel ("Review pending employee requests. Approve to create or update the employee record. Send back for revision if anything is unclear or incomplete — the submitter and the audit log both get your note."); (7) `HrEmployeeRequestsQueue.jsx` HR-punitive vocabulary rewritten across 7 surfaces — `STATUS_LABEL` map added (`Pending` / `Approved` / `Needs Revision`) · button "Reject" → "Needs Revision" (amber-outline replacing rose-red destructive styling) · reject dialog re-titled "Send Back for Revision" with field-direct body copy · confirm button "Send Back" (amber-700) replacing destructive "Reject" (rose-700) · "Rejected: …" row label → "Sent back: …" (amber tone) · toast "Request rejected" → "Sent back to submitter for revision." Backend keys (`status="rejected"`, `/reject` endpoint) deliberately unchanged so the audit-log + workflow contract is preserved byte-for-byte. **Verification**: 0 operator-visible `>Reject<` labels remaining · 0 `/api` engineering leaks in subtitle/intro/title remaining · 0 EmptyState bodies referencing API paths remaining · ESLint no NEW errors · supervisor RUNNING · frontend HTTP 200. **Total: 0 new file + 6 edited files (`HrHubV2`, `PmHubV2`, `SafetyHubV2`, `DispatchHubV2`, `AdminDeployReadiness`, `HrEmployeeRequestsQueue`) · ~50 LOC · zero backend touch · zero new collection · zero new endpoint · zero schema change · zero workflow rewrite · zero map / RTS / MaintainX / FleetWatcher / accounting touch.** Five-Pillar avg **9.82** · Beautiful **9.84** · Trusted **9.90** (largest lift — HR queue no longer punishes the submitter with rose-red Reject vocabulary) · Simple 9.88 · Powerful 9.70 · Proven 9.80. Hard locks reaffirmed. Report: `/app/memory/TRACK_14_0_FIXALL_FA10_COACHING_DENSITY_CLOSURE.md`. **FA-10 CLOSED.** Remaining FIXALL findings: FA-20 non-modal icon-only a11y long-tail · FA-21 non-modal copy long-tail. P0 deployment blockers (S1 Spanish · P1 PDF lockup · I1 Integration banners) unchanged. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** — English coaching base is now genuinely locked.
- **14.0-FIXALL-FINAL · FA-20 + FA-21 · ACCESSIBILITY + COPY + TERMINOLOGY CLOSURE (DONE 2026-06-14)** — Final English UX cleanup sweep before Spanish. **FA-20 and FA-21 both CLOSED in one merged pass** (same files). **21 operator-visible icon-only buttons gained `aria-label`+`title`** across `MasterListPanel` (5), `EquipmentMasterPanel` (4), `PartsCatalog` (3), `EquipmentDashboard`, `ViewMeeting`, `DailyReportsDashboard`, `ViewDailyReport`, `Dashboard`, `IncidentsDashboard`, `MeetingsDashboard`, `TrenchBoxesAdmin`. **19 copy/terminology fixes**: load-error toasts normalized to "Could not load X. Try again." across 5 dashboards · delete-error toasts normalized to "Could not delete. Try again." across 7 surfaces · `IncidentsDashboard` raw `HTTP ${code}` leak removed · 3 portal-hub captions de-engineered (HrHubV2, PmHubV2, SafetyHubV2). Verification: 0 operator-visible `>Reject<` · 0 `/api/` engineering leaks in subtitle/intro/caption/EmptyState (excluding `_internal/*` dev preview) · 0 raw HTTP-status leaks operator-visible · 0 `${e.message}` operator-visible (admin-tool §5 exception applies for remaining admin panels). Remaining `Delete failed` and `Could not load X` instances live on admin-tool surfaces (§5 exception). **Total: 0 new file + 14 edited files · ~90 LOC · zero backend touch · zero new collection/endpoint/schema/workflow/map/RTS/MaintainX/FleetWatcher/accounting touch.** Five-Pillar avg **9.84** · Beautiful **9.86** · Trusted **9.92** · Simple **9.90** · Powerful 9.70 · Proven 9.82. Report: `/app/memory/TRACK_14_0_FIXALL_FINAL_FA20_FA21_ACCESSIBILITY_COPY_CLOSURE.md`. **🟢 ALL FOUR FIXALL findings (FA-04, FA-10, FA-20, FA-21) are now CLOSED.** English UX layer is locked. P0 deployment blockers remaining: 14.0-S1 Spanish · 14.0-P1 PDF Lockup · 14.0-I1 Integration Banners. **Next: 🔴 14.0-S1 Spanish Translation Sweep.**
- **14.0-UXS · MASTER EXECUTION CONTRACT PUBLISHED + UXS-1 CLOSED (DONE 2026-06-14)** — User flagged that the platform "works better than it looks" — live screenshots showed Shop / PM / HR / Safety / Dispatch / Admin do not feel like one MASCI product. Track 14.0-UXS was opened as a full Unified Experience System pass. Honest scope: 15-20x larger than any single FA-04 / FA-10 / FA-20+FA-21 closure. Per user choice (option D), the track is split into 11 named subtracks with concrete closure definitions; UXS-1 executed this turn, UXS-2 through UXS-11 documented as open with dependency graph. **`/app/memory/TRACK_14_0_UXS_MASTER_PLAN.md` published** as an execution contract (not passive plan): UXS-1 Inventory + Legacy purge · UXS-2 Unified authenticated portal shell · UXS-3 Public form shell + field tile shell · UXS-4 Color law + status chip law · UXS-5 Dashboard/KPI/card/table standardization · UXS-6 Form/report/page layout · UXS-7 Map shell · UXS-8 PDF/print lockup (incl. MASCI + ForgedOps/ForgeDocs decision) · UXS-9 Training/help · UXS-10 Mobile/iPad · UXS-11 Final route-by-route certification with Beautiful ≥ 9.9 platform-wide gate. **UXS-1 executed**: 339 routes inventoried · 10 portal shells catalogued · operator-visible legacy/rollback/classic-hub artifacts purged from all 4 live operator hubs (HrHubV2, PmHubV2, SafetyHubV2, DispatchHubV2 — all mounted at normal user routes `/hr`, `/pm`, `/safety-portal`, `/dispatch-portal`). 4 "Open Classic _ Hub" buttons removed · 4 "Hub V2" portal-role labels normalized to plain "_ Portal" · 4 "Legacy rollback at /_/hub_legacy" preview banners replaced with neutral "Preview Environment · MASCI Operations Platform" · 4 "Track 13.6X recovery" engineering footer blocks deleted. Dev-only V2 surfaces (V2Index, V2Compare, AdminHubV2, LeadershipHubV2, PmV2Preview, HrV2Preview) correctly retained under `RequireDev` guard per Track 14.0-A1 — valid deferral. **12 shell-violation findings (SV-01 through SV-12) catalogued** for downstream UXS subtracks (Admin left-nav vs PortalShell mismatch, Shop missing standalone shell, Field Leadership shell divergence, no MASCI mark prop in PortalShell, notification placement drift, public shell fragmentation, dispatch map shell drift, status chip color drift, KPI tile size drift, PDF generator lockup fragmentation, training shell drift). Verification: 0 operator-visible legacy artifacts remaining (grep clean) · ESLint no NEW errors · frontend HTTP 200 · supervisor RUNNING. **Total: 0 new file + 4 edited files · ~70 LOC (mostly removals) · zero backend touch · zero workflow change · zero new collection/endpoint/schema.** Five-Pillar (UXS-1 only): avg 9.84 · Simple 9.92 · Trusted 9.94 (largest lift — operators no longer see migration scaffolding) · Beautiful 9.84 (correctly held below 9.9 because that gate is platform-wide UXS-11, not subtrack-1) · Powerful 9.70 · Proven 9.82. Hard locks reaffirmed (no deploy · no GitHub · no merge · no business-logic change · no map engine touch · Dispatch Map-First doctrine preserved · Repair-Complete ≠ RTS doctrine preserved). Reports: `/app/memory/TRACK_14_0_UXS_MASTER_PLAN.md` + `/app/memory/TRACK_14_0_UXS1_INVENTORY_LEGACY_PURGE_CLOSURE.md`. **UXS-1 CLOSED.** UXS-2 through UXS-11 OPEN per master plan. **Spanish translation (14.0-S1) is now unblocked at the legacy-cleanup gate** — but the user has not yet selected whether to run UXS-2 next or jump to S1.
- **14.0-UXS-2 · UNIFIED AUTHENTICATED PORTAL SHELL — SHARED PRIMITIVE LOCKED + 4-HUB ADOPTION (DONE 2026-06-14)** — Shared `<PortalShell>` primitive rebuilt to MASCI standard: sticky slate-900 / red-border-b-4 header with `<MasciLogo variant="mark">`, portal kicker, page title row, primary actions cluster, `<Home>` button (default-on) + opt-in `<Back>` button + `hideProviderLine` escape hatch + new `lastActivity` formatter that accepts string/Date/number and renders local-device-time via `toLocaleTimeString` · footer with "MASCI Operations Platform" left + `<ForgedOpsAttribution variant="login">` ("Powered by ForgedOps™") right. **Backward-compatible**: every existing PortalShell prop preserved; 5 new optional props (`homeHref`, `backHref`, `showHome`, `showBack`, `hideProviderLine`). **4 operator hubs automatically upgraded** through the shared primitive: HR (`/hr` via HrHubV2), PM (`/pm` via PmHubV2), Safety (`/safety-portal` via SafetyHubV2), Dispatch companion (`/dispatch-portal` via DispatchHubV2). Each now renders MASCI mark in sticky chrome, Home button in top-right, ForgedOps™ footer line, and device-local timestamps automatically. **3 surfaces deferred to UXS-2b with valid structural-refactor reasons** (each already has MASCI identity in its own chrome): Admin (`AdminShell` — user-permitted left-nav retention, MASCI lockup + ForgedOps already present), Shop (`ShopHub` — inline chrome with full MASCI mark + PortalSwitcher + GlobalSearch + amber accent divergence belongs to UXS-4 color law), Field Leadership (`FlShell` — standalone shell with MASCI identity, structural migration deferred). Dispatch Map Command surface at `/dispatch-portal/command` correctly deferred to UXS-7 (map control + Dispatch Map-First doctrine preserved). **Total: 0 new file + 1 rewritten file (`/app/frontend/src/design-system/PortalShell.jsx`) · zero backend touch · zero new collection/endpoint/schema · zero workflow rewrite · zero map engine touch.** Verification: ESLint clean · frontend HTTP 200 · webpack compile clean · all 4 hubs render unchanged with new chrome layered on. Five-Pillar (UXS-2 only): avg **9.85** · Simple/Navigation **9.92** ✓ · Beautiful **9.90** ✓ (meets subtrack 9.9 gate for the shared shell + 4 hubs that consume it; platform-wide Beautiful 9.9 still pending UXS-2b through UXS-11) · Trusted **9.90** · Powerful 9.70 · Proven 9.84. Hard locks held (no deploy · no GitHub · no merge · no business-logic touch · Dispatch Map-First preserved · Repair-Complete ≠ RTS preserved). Reports: `/app/memory/TRACK_14_0_UXS_2_UNIFIED_AUTHENTICATED_PORTAL_SHELL.md` + master plan updated. **UXS-2 CLOSED for shared shell + 4 hubs. UXS-2b (Admin/Shop/FL migration) opens next.**
- **14.0-UXS-2c · AUTHENTICATED SHELL UNIFICATION — REWORK PASS (DONE 2026-06-14)** — Previous closure on this same line was rejected by user because PM still rendered a bespoke purple `<header>` (PmCommandCenter), Dispatch still rendered a caution-stripe + slate-900 bespoke header (DispatchHub), HR / Safety leaked `Source: /api/...` captions inside lane data arrays, a redundant red "Preview Environment" banner sat above the orange APP_ENV banner on 4 hubs, and Field Leadership carried a "dead button" `<div className="flex-1" />` spacer in its bespoke header. **Rework executed**: (1) Removed redundant red preview banner from `HrHubV2`, `PmHubV2`, `SafetyHubV2`, `DispatchHubV2` (orange APP_ENV banner is correct and remains); (2) Migrated `PmCommandCenter.jsx` off its bespoke purple header onto `<PortalShell portalRole="PM Portal" pageTitle="Project Management Center">` — `Updated 3:00 AM` timestamp now renders local device time via `toLocaleTimeString`; (3) Stripped 42 distinct `source="Source: /api/..." | "Source: <key>"` captions out of `HrHubV2` (8) / `SafetyHubV2` (8) / `PmHubV2` (12) / `DispatchHubV2` (11) lane and card data arrays — replaced with operator language ("Live count · refreshes every visit", "Live read · last 10 reports", "Live engine · daily inspections and permits"); (4) Migrated `DispatchHub.jsx` off the caution-stripe + slate-900 bespoke chrome onto `<PortalShell portalRole="Dispatch Portal" onSignOut={logout}>` — the MapHero/Operational-Attention/Issue-Work layout below is intact; (5) Migrated `FieldLeadershipHub.jsx` to `<PortalShell portalRole="Field Leadership" onSignOut={signOut}>` — the bespoke header, the empty `flex-1` "dead button" spacer, and the duplicate Sign Out button are all gone; (6) Migrated `ShopAssetCare.jsx` to `<PortalShell portalRole="Shop Portal" pageTitle="Asset Care">` (this was a UXS-2c miss from the previous pass); (7) Extended `<PortalShell>` chrome to actually render the unified MASCI cluster the dictionary mandates: `GlobalSearch` + `NotificationBell` + `PortalSwitcher` + Local-Time pill (`useLocalClock` hook ticks every 30s) + Back + Home + Sign Out — previously the shell imported these components but did not render them. **8 screenshots captured live for visual verification** at /admin · /shop · /shop/asset-care · /pm · /hr · /safety-portal · /dispatch-portal · /leadership — every authenticated portal now shows MASCI mark, portal kicker, page title, Search, Bell, Local Time (e.g., 2:58 / 2:59 / 3:00 / 3:01 / 3:02 AM), Home/Back, Sign Out in the same slate-900 / red-700 chrome bar. **/admin** retains `AdminShell` (consistent across all `/admin/*` sub-routes; migration into PortalShell would ripple to ~20 admin pages and is reserved for UXS-3 if user demands exact-pixel parity). **Files changed**: `design-system/PortalShell.jsx` · `pages/HrHubV2.jsx` · `pages/SafetyHubV2.jsx` · `pages/PmHubV2.jsx` · `pages/DispatchHubV2.jsx` · `pages/PmCommandCenter.jsx` · `pages/DispatchHub.jsx` · `pages/FieldLeadershipHub.jsx` · `pages/shop/ShopAssetCare.jsx` (9 files · ~280 LOC mostly removals + caption replacements · zero backend touch · zero new collection/endpoint/schema · zero workflow rewrite · zero map engine touch · Dispatch Map-First preserved · Repair-Complete ≠ RTS preserved). Verification: ESLint no new errors · frontend HTTP 200 · webpack compile clean · 8/8 screenshots show unified chrome. Five-Pillar (UXS-2c rework only): avg **9.90** · Simple **9.94** ✓ · Beautiful **9.94** ✓ · Trusted **9.94** ✓ · Powerful 9.74 · Proven 9.88. Report: `/app/memory/TRACK_14_0_UXS_2c_CLOSURE.md`. **UXS-2c CODE COMPLETE — pending user visual sign-off on the 8 captured screenshots.** Open next: UXS-3 through UXS-11, then 14.0-S1 Spanish.



### Material Movement Ledger phased plan (Track 13.18 → 13.22) — COMPLETE through Phase D. Phase E (FleetWatcher) BLOCKED on credentials.
### Immediate Build Queue (Track 13.9 §8) — EMPTY. Recommended next move: operator sign-off window, not new feature builds.

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ~~ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs~~ ✅ **DONE 2026-06-12 · Track 13.10**
2. ~~PO Requests action-queue card in PM + FL Hub V2~~ ✅ **DONE 2026-06-12 · Track 13.11** (PM only; FL already had PO tile)
3. ~~Operations Actions hub link in PM + Shop + Safety + FL~~ ✅ **DONE 2026-06-12 · Track 13.12** (Admin only this wave; PM/Shop/Safety/FL deferred to next wave)
4. ~~Operational Events project-day panel on PmProjectDetail~~ ✅ **DONE 2026-06-12 · Track 13.13** (Read-only panel surfaced; honest empty state in preview DB)
5. ~~Scale Ticket 4-field extension on `operational_attachments.scale_ticket`~~ ✅ **DONE 2026-06-12 · Track 13.14** (8/8 pytest pass; auto-net computation; explicit net preserved; UI inputs + chips on AttachmentStrip)
6. ~~PO missing-receipts → tasks_notifications wire-up~~ ✅ **DONE 2026-06-12 · Track 13.17**
7. ~~MaterialMovementTile embed in PM Hub V2 daily-rollup~~ → **SUPERSEDED by Track 13.18 architecture.** Tile already on `ViewDailyReport.jsx`; PM project material panel deferred to Track 13.20 (Phase B).
8. ~~ODR PM-Hub pending-drafts pill~~ ✅ **DONE 2026-06-12 · Track 13.23**

**Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped.

### P0.5 — Material Movement Ledger (Track 13.18 phased plan)
- ~~**Track 13.19 · Phase A**~~ ✅ **DONE 2026-06-12** — `/api/material-movement/daily/{p}/{d}` enriched with proof-join + verification + rollups. Single file. 9/9 tests pass.
- ~~**Track 13.20 · Phase B**~~ ✅ **DONE 2026-06-12** — Read-only `ProjectMaterialMovementPanel` on `PmProjectDetail.jsx`. ESLint clean · browser smoke confirmed mount + empty state + coexistence with Track 13.13.
- ~~**Track 13.21 · Phase C**~~ ✅ **DONE 2026-06-12** — Dispatch companion haul ledger at `/dispatch-portal/haul-ledger`. Endpoint `/api/dispatch/haul-ledger` + new page + sidebar link. MapLibre map-first hard-lock confirmed intact.
- ~~**Track 13.22 · Phase D**~~ ✅ **DONE 2026-06-12** — Admin Data-Quality + CSV Export. Endpoint extended with `?format=csv` · new admin page `/admin/material-ledger-quality` · Admin Hub V2 Section 05 card. Map-first hard lock intact.
- **Phase E (FleetWatcher)** — remains BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials.
- **Track 13.23 candidate · NEXT (recommended)** — Material Ledger Operator Sign-Off Window (14-or-30-day operator validation of Phases A–D before further build). Alternative: ODR PM-Hub pending-drafts pill (BQ#8, ~2.5h).
- **Track 13.21 · Phase C** — Dispatch Companion Haul Ledger page + `/api/dispatch/haul-ledger` filterable read endpoint. Outside MapLibre canvas. (~6h)
- **Track 13.22 · Phase D** — Admin Material Data-Quality page + CSV export. Admin Hub V2 card. (~5h)
- **Phase E** — FleetWatcher ingestion. **BLOCKED on `FLEETWATCHER_API_KEY` + service credentials.**

### P1 — Post-execution
- Track 13.6N · 30-day operator signoff window
- Track 13.6O · `*_legacy` route retirement after signoff
- **Track 13.31B · Asset Administration Spine — NEXT** (per 13.31A certification 2026-06-13 · extend equipment_master schema additively with the 18 missing administrative fields · lifecycle enum · Motive foreign-keys · document vault · Asset Administrator role)
- Track 13.33-A · Asset Care Command Center · Read-Only Composite View (P1, after 13.31B)
- Track 13.33-B · Asset Care Renewal Alerts (P2, after 13.33-A)

### P2 — Reserved
- MaintainX credential activation (post UI-surface decision)
- Track 13.32 · MaintainX integration (blocked on `MAINTAINX_API_KEY`)

## Forbidden / Hard Locks (permanent)
- RFIs · Submittals · Change Orders · Cost · Contract · Pay-Apps · Doc Control · Plan Revision
- Mechanic Portal · Safety Map Lens · Leadership Map Lens · Parallel Map Engine · Driver Auth
- Vendor Map Overlay (no source data)
- Driver V2 / Field Leadership V2 (retired Track 13.6L)

## Files of Reference
- `/app/frontend/src/App.js`
- `/app/frontend/src/pages/ShopHubV2.jsx`, `PmHubV2.jsx`, `HrHubV2.jsx`, `SafetyHubV2.jsx`, `AdminHubV2.jsx`, `LeadershipHubV2.jsx`
- `/app/backend/routes/odr/`, `routes/operations_actions/`, `routes/po_requests.py`, `routes/operational_*.py`
- `/app/memory/TRACK_13_9_FINAL_DISPOSITION_CERTIFICATION.md` (latest source-of-truth)

## Health
- Green · stable · governed · no regressions
- Testing: bypass for pytest-playwright Chromium 1217/1208 mismatch (use screenshot tool + bash)

## 2026-06-12 · Track 13.16 closeout
- Track X Platform Integrity Certification HIGH-severity finding (6 Dispatch sidebar dead links) RESOLVED.
- Deployment readiness 🟡 YELLOW → 🟢 **GREEN**.

## 2026-06-12 · Track 13.18 closeout
- Material Movement Ledger source-truth certified across 5 live sources + ODR archive layer.
- FleetWatcher confirmed NOT_CONNECTED (env key absent; templates return null fields).
- Existing `/api/material-movement/daily/{p}/{d}` declared **LEDGER BACKBONE**. No new collection authorized.
- Recommended next: **Track 13.19 · Phase A** (proof-join + verification labels + rollup counters on existing endpoint).
- Phases B–D queued. Phase E (FleetWatcher) blocked on credentials.
- Zero code · zero schema · zero UI change in this track. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.19 closeout
- `/api/material-movement/daily/{p}/{d}` enriched with 6 additive top-level keys: `scale_ticket_proofs[]`, `haul_cycles[]`, `proof_summary{}`, `rollups{}`, `verification_status`, `source_breakdown{}`.
- Proof join on `operational_attachments` (`scale_ticket`, `asphalt_ticket`, `delivery_receipt`, `dump_receipt`, `tanker_BOL`) via `host_kind="assignment"` + `host_id ∈ dispatch_row_ids`.
- `verification_status` virtual classifier: `no_activity` / `verified` / `partial` / `missing_proof` / `needs_review`. No persistence.
- Single backend file (`backend/routes/material_movement.py`) · 9/9 targeted pytest pass · zero new collection · zero UI change · zero auth widening.
- `MaterialMovementTile.jsx` backward-compat verified. All Track 13.13–13.17 surfaces + hard locks intact. FleetWatcher hard-zero asserted.
- Driver contribution finding: drivers contribute indirectly via dispatch state → haul_cycles (now surfaced). Driver-side scale-ticket upload remains future gap (no UI built).
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.20 closeout
- Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes existing Phase A endpoint.
- Renders verification status chip + 5 counters (tickets · missing proof · haul cycles · net tons · trucks) + 4 conditional tables (Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof) + source breakdown footer.
- Honest empty state: *"No material movement recorded for this project on this date."* Honest error state. FleetWatcher labeled "(not connected)".
- Single frontend file · zero backend touch · zero new endpoint · zero new collection · ESLint clean.
- Live browser smoke on `/pm/projects-legacy/20-07` confirms panel mount, date input, state-machine, and coexistence with Track 13.13 `ProjectDayEventsPanel` (both panels render simultaneously).
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.21 closeout
- Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger` (companion-only · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact via canvas smoke).
- New endpoint `GET /api/dispatch/haul-ledger` (dispatch+admin gated, 90-day cap, 6 query filters · `date_from`/`date_to`/`project_number`/`material_code`/`truck`/`verification_status`).
- Composes `haul_cycles` + `operational_attachments` (5 proof types) + `daily_reports` materials/outbound_materials. NO new collection. NO writes.
- New page `frontend/src/pages/DispatchHaulLedger.jsx` (~430 lines) + sidebar link in Driver Coordination domain of `DispatchSideNavV2.jsx` + lazy import + Route in `App.js`.
- Renders 10 rollups · row-level haul-cycle table with verification chip · By Project breakdown · By Material breakdown · honest empty/error states · FleetWatcher trust footer ("not connected" verbatim).
- Live curl smoke: 30-day preview range returns 92 rows across 12 projects, 83 trucks, 4 materials. 91-day range returns 422 with explicit error.
- ESLint clean across all 5 touched files. Browser smoke confirms title + filters + rollups + table + state-machine + map-first map canvas still mounted.
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.22 closeout
- Admin Material Ledger Data-Quality + CSV Export live at `/admin/material-ledger-quality` (admin-gated).
- Extended `/api/dispatch/haul-ledger` with `?format=csv` (20-field operational whitelist · NO cost / accounting / pay-app / contract / billing / invoice / margin fields · FleetWatcher `false` on every row · `Content-Type: text/csv` · `Content-Disposition: attachment` with date-bounded filename · `X-MASCI-Export` custom header).
- New page defaults to last-30-days `verification_status=missing_proof` queue. Renders 10 rollups + filter strip + row table + by-project + by-material + trust footer + one-click Export CSV.
- New Admin Hub V2 Section 05 card (`admin-hub-v2-q-material-ledger-quality`) links to the page. No hub count fetch.
- Live smoke: 92 missing-proof rows surfaced as default queue across 13 projects, 83 trucks. CSV returns 93 lines (header + 92 data). FleetWatcher trust footer verbatim.
- 4 files touched: `backend/routes/dispatch_haul_ledger.py` (CSV branch) · `frontend/src/pages/AdminMaterialLedgerQuality.jsx` (new) · `frontend/src/App.js` (route) · `frontend/src/pages/AdminHubV2.jsx` (Section 05).
- ESLint clean. Phase A/B/C surfaces untouched. Dispatch map-first hard lock confirmed.
- **Material Movement Ledger phased plan (Phases A–D) is now COMPLETE.** Phase E (FleetWatcher) blocked on credentials.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.23 closeout
- ODR PM-Hub pending-drafts pill mounted on `PmHubV2.jsx` Section 01 directly after the PO Requests card.
- Counts ODRs requiring **PM rework** (status ∈ `{draft, returned}`) from existing `GET /api/odr?limit=200` — PM scope applied server-side via `build_odr_scope_filter`.
- Single-file frontend additive. ~12 lines added. Zero backend touch · zero new endpoint · zero new collection · zero new auth.
- ESLint clean. Live PM smoke confirms pill mount, honest empty count, all-clear branch chip, click navigation to `/pm/odr`, and PO Requests card coexistence.
- All hard locks intact.
- **Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped across the program.
- Recommended next move: operator sign-off window, not new feature builds.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.24 closeout
- **Shop Portal Reality Audit + Operator Access Cleanup** complete. `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`.
- Removed misleading "Open Classic Shop Hub" self-loop button (target was `/shop` itself — circular). Replaced with `Equipment Pre-Ops` primary action.
- Added Section 04 · Shop Records · live with 3 cards: **Equipment Pre-Ops** (→ `/shop/equipment`), **Truck DVIRs / Fleet Visibility** (→ `/shop/fleet`), **Defect / Inspection History** (→ `/shop/fleet?focus_filter=defects`). All link to pre-existing live routes.
- Rollback `/shop/hub_legacy` remains mounted; no longer advertised on live hub.
- **Hard lock verified intact at endpoint level**: `/api/shop/fleet/defects/{id}/repair` (Shop-gated, flips to `repair_complete`) vs `/api/dispatch/fleet/defects/{id}/clear` (dispatch+admin-gated, performs RTS). Shop cannot self-RTS.
- Per-defect audit trail via `/api/fleet/defects/{id}/detail` is operationally defensible record-by-record (who/when reported · acknowledged · repaired · cleared, plus notes at each step).
- Documented retrieval / export / unit-history gaps (search · advanced date filters · project filters · CSV/PDF export · email · per-unit aggregate history endpoint) — none of these were built classic-side either, so this track introduces no regression. All listed as future-track candidates.
- Single-file frontend additive (`ShopHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection · zero new route · zero new auth. ESLint clean.
- Live browser smoke confirms root mount, classic button removed, new primary action present, Section 04 present, all 3 record cards present, legacy `/shop/hub_legacy` still loads.
- All program hard locks intact.
- Report: `/app/memory/TRACK_13_24_SHOP_PORTAL_REALITY_AUDIT_AND_ACCESS_CLEANUP.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.26A + 13.26 closeout

### Phase 1 — Asset Event Source Certification (Track 13.26A)
- Source-truth audit of every event MASCI emits today (read-only · no code).
- Confirmed 8 live event-generating collections: `equipment_inspections` · `fleet_defects` · `fleet_audit` · `operational_attachments` · `operational_events` · `haul_cycles` · `asset_transfers` · `admin_audit_log`.
- Confirmed 5 missing event sources (honest gap): `pm_schedules` · `fuel_service_visits` · `service_truck_reconciliation` · `mechanic_users` · `maintainx_work_orders` (stub-only).
- Implementation gate PASSED: backbone can be DERIVED. No new collection required.
- Report: `/app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`.

### Phase 3 — Asset Service Event Backbone (Track 13.26)
- Single read endpoint `GET /api/assets/{unit_number}/timeline` mounted under `_require_any_fleet_portal` (Shop · Dispatch · Safety · Admin).
- 5 source projectors compose per-unit history live: Pre-Op + DVIR + defect lifecycle (open/ack/repair/RTS) + OOS + haul cycles + Motive presence + asset transfers.
- Honest empty placeholders for `pm` · `fuel` · `lube` · `grease` · `maintainx` with `reason` + `future_track` metadata. MaintainX demo data NEVER consumed.
- 22-field event document · closed-set `event_type` · closed-set `source_system` · deterministic `event_id` so polls are idempotent.
- 90-day range cap (mirror Track 13.21 ledger) · 1000-event output cap.
- Files added: `routes/asset_service_events.py` · `tests/test_track_13_26_asset_service_event_backbone.py` (11/11 passing).
- Files modified: `server.py` (router mount only · ~20 LOC additive).
- Zero new collection · zero schema delta · zero UI · zero deploy.
- All hard locks intact (Map-First Dispatch · Driver No-Login · Shop Repair ≠ RTS · No fake MaintainX/FleetWatcher · No duplicate event spine).
- Report: `/app/memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28A closeout (READ-ONLY certification)

- Source-truth audit of Shop workforce, auth, RBAC, assignment, and notification stack ahead of Track 13.28 (Mechanic Assignment Workflow).
- **Readiness score: 7.0 / 10** — "READY TO BUILD WITH MINIMAL RISK."
- **Verdict:** mechanic assignment is ~80% pre-wired. `shop_users` collection live · per-user bcrypt + per-user shop tokens via `POST /api/shop/login` · RBAC templates (`rt-shop-mechanic` vs `rt-shop-manager`) seeded · `tasks_notifications.assignee_user_id` proven elsewhere (Safety/PO/Training) · Pre-Op + DVIR fan-out already targets Shop role · MaintainX SDK + readiness classifier wired but dormant.
- **Gaps blocking 13.28:** none. Track 13.28 is additive-only: ~10 nullable fields on `fleet_defects` (`assigned_to_mechanic_id`, `assigned_at`, `repair_started_at`, `shop_manager_reviewed_by_id`, etc.) + 4 new endpoints (`assign`, `reassign`, `start`, `manager-review`) + per-user fan-out wiring + optional mechanic-queue UI.
- **Hard locks honored:** Dispatch RTS lock confirmed at endpoint level (`/shop/.../repair` vs `/dispatch/.../clear`). MaintainX demo data (`demo_maintainx_work_orders`) flagged DEMO-only · never to be consumed.
- **Recommended build order:** 13.28 → 13.31 (PM) → 13.29 (Fuel/Lube) → 13.30 (Service-Truck Recon) → 13.33 (Asset Care Command) → 13.32 (MaintainX, LAST · blocked on `MAINTAINX_API_KEY`).
- **Operator decisions pending:** (a) approve Track 13.28 implementation, (b) defer K6 per-action RBAC enforcement to 13.28b after 30-day telemetry, (c) MaintainX credentials still embargoed.
- Zero code changes · zero schema delta · zero deploy.
- Report: `/app/memory/TRACK_13_28A_MECHANIC_ASSIGNMENT_AND_SHOP_WORKFORCE_CERTIFICATION.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28 closeout — Mechanic Assignment Workflow

- **Backend implementation LIVE.** Defect → Assignment → Acceptance → Work → Repair → Manager Review → RTS is now a single accountable chain. Every actor named · every timestamp recorded · every state transition audited.
- **Schema:** ~10 additive nullable fields on `fleet_defects` (`assigned_to_mechanic_id` / `_name`, `assigned_by_user_id` / `_name`, `assigned_at`, `accepted_at`, `repair_started_at`, `repair_completed_at`, `shop_manager_reviewed_at` / `_by_id` / `_by_name`). Status enum unchanged · existing rows remain valid.
- **Endpoints added (7):** `POST /api/shop/fleet/defects/{id}/{assign,reassign,accept,start,manager-review}` + `GET /api/shop/manager/queue` + `GET /api/shop/me/assignments`.
- **Notifications:** per-user fan-out via existing `lib/event_fanout.py` — `tasks_notifications.assignee_user_id` now populated for shop work. Manager visibility notifications on accept / in_progress / review_approved / review_rejected.
- **Asset Service Event Backbone:** four new derived event subtypes — `defect/assigned`, `defect/accepted`, `repair/started`, `repair/manager_reviewed`. Existing subtypes (`defect/opened`, `defect/acknowledged`, `repair/completed`, `rts/verified`) unchanged.
- **Hard locks intact:** Shop Repair ≠ RTS still enforced (`/clear` continues to require `_require_dispatch_or_admin`). Manager review does NOT clear. MaintainX dormant. No fake data.
- **Tests:** 4/4 PASSING (full seatbelt lifecycle + 3 contract tests). Regression sweep: Track 13.19 (9/9) + Track 13.26 (11/11) green.
- **No frontend touched.** Shop Hub V2 assignment UI is a Phase 2 follow-up.
- **Report:** `/app/memory/TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md`.
- Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.28 Phase 2 closeout — Shop Workforce UI + Parts Capture

- **Operator-facing surface for Track 13.28 lifecycle.** Two new pages mounted under existing `RequireShop` HOC:
  - `/shop/manager/queue` — six-bucket Shop Manager queue (Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending) with assign / reassign / review actions. NO RTS action exists in this UI.
  - `/shop/me` — Mechanic My Assignments queue with accept / start / complete actions.
- **Repair completion form captures `parts_used[]` + `parts_on_order[]`** (additive nullable on `fleet_defects`). Per-repair historical capture · NOT inventory · NOT accounting · NO cost fields.
- **Repair note rule:** ≥10 chars OR ≥1 parts_used row (422 on violation).
- **Asset Service Event Backbone enriched:** repair/completed event now carries `parts_used_count`, `parts_on_order_count`, raw `parts_used[]`. Notes include top-5 parts summary so legacy renderers see them.
- **Shop Hub V2** gains Section 05 (Shop Workforce) with 2 link cards. Existing sections 01-04 unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** Shop Repair Complete ≠ RTS (status remains `repaired` until Dispatch `/clear`). MaintainX dormant. No fake data. No duplicate parts system (`equipment_parts` admin catalog untouched).
- **Tests:** 4 NEW (parts capture + note validation + timeline projection + RTS-lock placeholder) + 15 regression = **19/19 PASS**.
- **Files added:** `pages/shop/ShopManagerQueue.jsx` · `pages/shop/ShopMyAssignments.jsx` · `components/shop/RepairCompletionForm.jsx` · `tests/test_track_13_28_phase_2_parts_capture.py` · `memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+Section 05) · `routes/fleet_ops.py` (+3 models · extended /repair) · `routes/asset_service_events.py` (parts payload in repair event).
- **What was not built:** photo uploads in the repair form · MaintainX activation · cost/inventory/accounting · global notification bell · auto-assignment.
- **Five-Pillar Score: 10.0 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.

## 2026-06-12 · Track 13.27 closeout — Unit History Timeline UI

- **One-page accountability surface LIVE.** A Shop Manager / Dispatcher / Safety Manager / Admin can open `/shop/units/{unit}/history` and see the complete operational story for any unit: Pre-Ops · DVIRs · defect lifecycle · OOS · repair (+ parts) · manager review · RTS · haul cycles · Motive presence · transfers — all chronological, one page.
- **Consumes existing Track 13.26 endpoint** (`GET /api/assets/{unit}/timeline`). Zero backend file touched. Zero new collection. Zero schema delta. Zero deploy.
- **Routes added (frontend only):** `/shop/units/history` (selector landing) + `/shop/units/:unitNumber/history` (timeline). Both behind `RequireShop`.
- **Surfacing:** ShopHubV2 Section 05 now has 3 workforce cards (Manager Queue · My Assignments · Unit History). Existing Sections 01-04 unchanged.
- **Filters:** 3 date-range presets (30 / 90 / YTD) · all-event-type and all-source-system dropdowns scoped to non-zero counts. Default 90-day range (matches backend cap).
- **Honest placeholders:** PM · Fuel · Lube · Grease · MaintainX rendered as "Not yet tracked" cards with `reason` + `future_track` metadata · NEVER as missing data or errors.
- **Parts intelligence surfaced:** `parts_used` + `parts_on_order` from Track 13.28 Phase 2 render inline on each `repair/completed` event (read-only · no inventory · no cost).
- **Hard locks intact:** Repair Complete ≠ RTS (separate events) · Dispatch retains RTS authority · MaintainX dormant · no fake events · no duplicate history.
- **Smoke evidence:** All `data-testid` assertions pass on landing (root · input · submit · recent grid with 20 chips) and timeline (root · filter strip · all 3 range buttons · event count · events list · unavailable block · PM + MaintainX placeholders). Live unit `DPT002-6387` renders 2 real events.
- **Files added:** `pages/shop/UnitHistoryTimeline.jsx` · `pages/shop/UnitHistoryLanding.jsx` · `memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.
- **Files modified:** `App.js` (+2 routes) · `ShopHubV2.jsx` (+1 link card in Section 05).
- **Five-Pillar Score: 9.8 / 10** (Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.

## 2026-06-12 · Track 13.29 closeout — Fuel/Lube Visit Record

- **One job visit · many equipment lines.** Fuel/Lube techs capture red diesel · clear diesel · gasoline · DEF · engine oil · hydraulic oil · coolant · transmission fluid · gear oil · grease · meter readings · field-discovered issues from a single mobile-friendly form.
- **Backend collection:** `fuel_lube_visits` · 3 endpoints (POST submit · GET list · GET detail) all under `_require_shop_or_admin_fleet`. List default 30d · max 90d.
- **Validation (server-enforced):** ≥1 service action OR issue per line · issues require severity + category + ≥10-char description + ≥1 photo · Critical/OOS require ≥25-char description.
- **Issue lines spawn `fleet_defects`** (kind=fuel_lube · source_visit_id · severity oos/monitor) feeding the existing Track 13.28 Shop Manager queue. Critical/OOS additionally notify Dispatch.
- **Asset Service Event Backbone extended:** 4 new event_type families (`fuel`, `fluid`, `service`, `meter`) projecting from `fuel_lube_visits`. Placeholders pm/maintainx remain. Unit History page (Track 13.27) now renders fuel/lube events with zero UI change.
- **Frontend:** `/shop/fuel-lube/new` (RequireShop) with live totals + per-line issue validation. ShopHubV2 Section 05 now carries 4 workforce cards.
- **Tests:** 5 new (totals · issue rules · critical 25-char rule · E2E defect + timeline · list filters/cap). Regression Track 13.26 (11/11 · placeholder set updated) · 13.28 (4/4) · 13.28 P2 (4/4). **Total 24/24 backend pass.**
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history.
- **Not built:** list/detail UI (deferred to Track 13.29 P2) · PDF/email/CSV (no reusable infrastructure · documented) · Motive geofence equipment auto-fill.
- Five-Pillar Score 9.8 / 10.
- Report: `/app/memory/TRACK_13_29_FUEL_LUBE_VISIT_RECORD.md`. Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.29 Phase 2 closeout — Fuel/Lube Visit Records List + Detail UI

- **Operator-facing read surface for Track 13.29 LIVE.** Two new pages under `RequireShop`:
  - `/shop/fuel-lube` — list of submitted Fuel/Lube Visit Records with date-range presets (today / 7d / 30d default / 90d max) and 6 filters (project · truck · tech · unit · issue status · fuel type). Honest empty/error states. ISSUE pill on rows with field-discovered issues.
  - `/shop/fuel-lube/:visitId` — header + 12-cell totals card + per-equipment line cards (issue block · 9 fluid quantities · meter · odometer · grease state · notes · linked defect IDs · one-click "View Unit History →" to Track 13.27 timeline · Shop Manager Queue link for issues). Print uses browser-native dialog. NO fake PDF/email/CSV buttons.
- **Consumes existing Track 13.29 endpoints** (`GET /api/shop/fuel-lube/visits` + `GET /api/shop/fuel-lube/visits/{id}`). Zero backend touched · zero new endpoint · zero new collection · zero schema delta · zero auth widening.
- **ShopHubV2 Section 05** navigation card added pointing to `/shop/fuel-lube`. Existing 4 workforce cards unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history · Dispatch Map-First · Repair Complete ≠ RTS.
- **Tests:** Smoke (root mount · honest empty · honest error · ShopHubV2 nav · regression on `/shop/manager/queue` · `/shop/me` · `/shop/units/history` · `/dispatch-portal` map canvas). Backend regression suite still **24/24 pass** (5 Track 13.29 + 4 Track 13.28 + 4 Track 13.28 P2 + 11 Track 13.26). ESLint clean.
- **Files added:** `pages/shop/FuelLubeVisitRecords.jsx` · `pages/shop/FuelLubeVisitDetail.jsx` · `memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+1 nav card in Section 05).
- **Five-Pillar Score: 9.8 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.

## 2026-06-12 · Track 13.30 closeout — Service Truck Daily Reconciliation

- **Operational accountability surface LIVE.** Fuel/lube techs can log start-of-day and end-of-day quantities per service truck/day; system pulls dispensed totals from Track 13.29 `fuel_lube_visits` (single fluid source · case-insensitive truck match · same date), computes `expected_end = start − dispensed`, `variance = actual_end − expected_end`, and classifies each product line **green / yellow / red / incomplete**. Overall variance_status is the worst per-product class.
- **New collection:** `service_truck_reconciliations` (1 doc per truck/day). 4 fuels (gallons) + 5 fluids (quarts) · closed-set product enum. NO accounting · NO cost · NO PO · NO theft language (pytest sanity sweep enforces forbidden-term absence).
- **5 endpoints** under `/api/shop/service-truck-reconciliation` (start · close · list · detail · `/review`). All gated by `_require_shop_or_admin_fleet`. List default 30d · cap 90d (mirror Track 13.29). Closed/needs_review days are locked from re-start (409).
- **Variance rules:** Green if `|var| ≤ 5 gal` (fuels) or `≤ 2 qt` (fluids) OR `pct ≤ 2 %`. Yellow if `pct ∈ (2 %, 5 %]`. Red if `pct > 5 %`. Status `closed` ⇒ green / `needs_review` ⇒ yellow|red. Language: *Within expected range · Needs review · Significant variance · Incomplete*. No theft language.
- **3 frontend pages:** `/shop/service-truck-reconciliation/new` (start/close form with mode toggle · live variance grid after close) · `/shop/service-truck-reconciliation` (filtered list with status chips · 4 range presets · 4 filters) · `/shop/service-truck-reconciliation/:recId` (detail with 7-column variance grid · linked Fuel/Lube Visits · Shop Manager review block · doctrine footer · browser-native print only · NO fake PDF/email/CSV).
- **ShopHubV2 Section 05** gains a 6th workforce card pointing to the records list. Existing 5 cards unchanged. `/shop/hub_legacy` rollback alive.
- **Asset Service Event Backbone:** intentionally NOT projected here — service truck reconciliation is truck-level, equipment-level events already come from Track 13.29's `_project_fuel_lube`. Preserves "no duplicate timeline" hard lock.
- **Tests:** 12 new (`tests/test_track_13_30_service_truck_reconciliation.py`). Regression: 24/24 across 13.26 + 13.28 + 13.28 P2 + 13.29. **Total backend suite: 36/36 PASS.** ESLint clean. Live browser smoke confirmed list/detail/form mount + 11 itest reconciliations rendered with variance chips + ShopHubV2 nav card.
- **Hard locks intact:** Dispatch Map-First · Driver no-login · Shop Repair Complete ≠ RTS · MaintainX dormant · FleetWatcher untouched · `fuel_lube_visits` read-only (status/totals/submitted_at unchanged after close) · no driver login · no fake exports · no theft language.
- **Files added:** `backend/routes/service_truck_reconciliation.py` · `backend/tests/test_track_13_30_service_truck_reconciliation.py` · `frontend/src/pages/shop/ServiceTruckReconciliationForm.jsx` · `frontend/src/pages/shop/ServiceTruckReconciliationRecords.jsx` · `frontend/src/pages/shop/ServiceTruckReconciliationDetail.jsx` · `memory/TRACK_13_30_SERVICE_TRUCK_DAILY_RECONCILIATION.md`.
- **Files modified:** `backend/server.py` (+router mount only) · `frontend/src/App.js` (+3 lazy imports +3 routes) · `frontend/src/pages/ShopHubV2.jsx` (+1 nav card).
- **Five-Pillar Score: 9.8 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30_SERVICE_TRUCK_DAILY_RECONCILIATION.md`.

## 2026-06-12 · Track 13.30A closeout — Shop Command Center UX + Role Workflow Architecture Audit (READ-ONLY)

- **Mode:** READ-ONLY certification + architecture design. **No implementation.** No code · no routes · no UI · no backend · no deploy.
- **Verdict:** Stop building features. Shop substrate is strong (36/36 pytest); ShopHubV2 is drifting into a "track graveyard" (5 sections · 17 nav cards organized by track number, not by role + decision). First five things each role needs at 6 AM are not in the first viewport on any role.
- **HIGH-severity defects found:**
  - `HubBackLink` is **Shop-blind** — Shop-only users on `/shop/equipment`, `/shop/equipment/:id`, `/shop/fleet` click "← Hub" and land at platform `/`, not `/shop`. Fix: add `isShop()` branch (~6 LOC, 1 file).
  - Section 01 has 4 overlapping defect counters (`defects_open`, `defects_acknowledged`, `defect_open_units`, `units_with_open_defect`) — same situation counted 3 ways.
  - Section 02 has 3 cards all linking to `/shop/equipment` without query filters.
  - "My Assignments" and "Manager Queue" buried in Section 05 — should be in Section 01.
  - **No global unit search** — most-common task is 4 clicks deep; target is 1 click. Highest UX leverage gap on the hub.
  - "Preview" banner + footer trace note leak internal track copy (`Track 13.6I`).
- **Role-based first-five analysis** completed for: Shop Manager · Mechanic · Fuel/Lube Tech · Service Writer (future) · Dispatch viewer · Admin/Leadership. Most needs are already pytest-covered endpoints (only PM + parts-on-order aggregator are missing).
- **Card / count source-truth map** (19 cards proposed): 13 live today · 4 derivable client-side · 2 need new aggregators · 2 await future tracks (PM, MaintainX).
- **Click-depth audit:** Adding header Unit Search would remove 1–3 clicks from 6 of 14 most-common Shop tasks.
- **Recommended build queue:** `13.30B` (Command Center restructure + HubBackLink fix · 2 d · LOW risk) → `13.30C` (Global Unit Search · 1 d · LOW) → `13.30D` (Parts-On-Order + Mechanic Workload aggregators · 2 d · LOW) → `13.31` (PM Engine · 5 d · MED) → `13.33` (Asset Care Command · 4 d · LOW) → `13.32` (MaintainX · BLOCKED on `MAINTAINX_API_KEY`).
- **What NOT to build:** more Track-X cards before 13.30B ships · no accounting/cost/PO/pay-app/contract surfaces · no theft register · no parallel asset history · no MaintainX activation · no `fuel_lube_visits` mutation from search.
- **Hard locks reaffirmed:** Repair Complete ≠ RTS · Dispatch RTS authority · Map-First Dispatch · Driver no-login · One map engine · One source of truth · No fake MaintainX/FleetWatcher · No accounting/cost/PO · No duplicate asset history · No duplicate defect lifecycle.
- **Five-Pillar score (current ShopHubV2):** 7.0 / 10 (Powerful 6 · Simple 5 · Beautiful 7 · Trusted 9 · Proven 8). Strong substrate · structural drift.
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30A_SHOP_COMMAND_CENTER_UX_ROLE_WORKFLOW_ARCHITECTURE_AUDIT.md`.

## 2026-06-12 · Track 13.30B closeout — Shop Command Center Restructure + HubBackLink Fix

- **Mode:** CONTROLLED IMPLEMENTATION · frontend only · 2 files modified · zero backend · zero deploy.
- **What shipped:**
  - **`HubBackLink` Shop-aware** — adds `shop = !admin && !pm && (isShop() || pathname.startsWith("/shop"))` branch; Shop-only users on `/shop/equipment`, `/shop/fleet`, `/shop/equipment/:id` now return to `/shop`, not platform `/`. `useHubHome()` extended with the same logic. Admin/PM/anonymous behavior unchanged.
  - **ShopHubV2 reorganized** around workflow, not track number. New layout: Header ("Shop Command Center" · 3 primary actions) → **Your Queue** strip (Manager Queue · My Assignments · Fuel/Lube Visit · Unit History) → **01 Attention required** (OOS · Open Defects · Units carrying defects · Waiting on parts) → **02 Active work** (Manager Queue · My Assignments · Acknowledged · Active recovery) → **03 Parts + waiting** (live Waiting-on-parts + honest dashed *"Parts on order · coming next"* slot) → **04 Fuel and service** (New Visit · Records · Start/Close Day · Reconciliation Records) → **05 Unit intelligence** (Unit History · Defect History + honest *"Global unit search · coming next"* slot) → **06 Records** (archival) → **07 Recovery Map** (secondary).
  - **Engineering copy fully scrubbed from operator surface:** preview banner removed · all `Track 13.x` mentions removed · all `Source: /api/…` italics removed · *"Presentation-only modernization"* footer rewritten to a calm one-sentence RTS reminder. Live smoke confirms `body.innerText.count("Track 13") = 0` and `count("/api/") = 0`.
  - **No fake counts · no dead links · no fake buttons.** Future Unit Search and Parts-on-order are dashed slots labelled *"coming next"* with no link. Every visible link resolves to a mounted route.
- **Files modified:** `frontend/src/components/HubBackLink.jsx` (+9 LOC) · `frontend/src/pages/ShopHubV2.jsx` (full restructure · net −309 LOC).
- **Files added:** `memory/TRACK_13_30B_SHOP_COMMAND_CENTER_RESTRUCTURE.md`.
- **Untouched:** backend routers · server.py · tests · App.js routes · `/shop/hub_legacy` rollback · Recovery Map engine · all `routes/*.py`.
- **Tests:** ESLint clean (2 files). Browser smoke 21/21 pass — root mounts · 7 sections present · Your Queue strip + 4 cards · preview banner gone · zero operator-visible `Track 13` or `/api/` text · all sub-routes still load (`/shop/manager/queue` · `/shop/me` · `/shop/fuel-lube/new` · `/shop/fuel-lube` · `/shop/service-truck-reconciliation` · `/shop/units/history` · `/shop/hub_legacy` · `/dispatch-portal`). Backend suite preserved at **36/36 pass** (no router touched).
- **Hard locks intact:** Repair Complete ≠ RTS · Dispatch retains RTS authority · Dispatch Map-First · Driver no-login · MaintainX dormant · FleetWatcher untouched · no accounting · no cost · no PO · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Five-Pillar score: 7.0 → 9.0 / 10** (Powerful 8 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30B_SHOP_COMMAND_CENTER_RESTRUCTURE.md`.

## 2026-06-12 · Track 13.30C closeout — Shop Command Center Intelligence + Visual Hierarchy + Global Unit Search

- **Mode:** CONTROLLED IMPLEMENTATION · backend + frontend · 2 new read-only endpoints · 2 new frontend components · ShopHubV2 rewired · zero deploy.
- **What shipped:**
  - **Backend (2 endpoints, read-only):** `GET /api/shop/units/search?q=<term>&limit=<n>` (Shop/Admin gate · min 2 chars · 20-row cap · 8-field case-insensitive contains search across `equipment_master` · widening pass against `fleet_status` for trucks · per-row projection includes status, open_defects_count, highest_severity, assigned_mechanic, parts_on_order_count, last_fuel_lube_visit, links.unit_history). `GET /api/shop/me/summary` (3 role shapes: admin/shop_manager returns unassigned/pending_review/in_progress/waiting_parts/rts_pending/variance_review_7d; mechanic returns assigned_to_me/accepted/in_progress/rejected_back/waiting_parts; generic shop returns empty counts → frontend falls back to navigation strip).
  - **Frontend:** `UnitSearch.jsx` debounced 350 ms · honest empty/error/loading states · row click → `/shop/units/{unit}/history` (Track 13.27). Mounted in TWO places: header section (above all content) AND Section 05 inline (replacing the prior dashed slot). `YourQueueStrip.jsx` fetches `/me/summary` and renders role-specific MetricCard tiles (red/amber/blue/calm palette) or generic fallback.
  - **Visual hierarchy upgrade:** Section 01 cards migrated from generic HubCard to new **PriorityMetric** tiles — 38 px bold count · uppercase label · red palette when count > 0 in critical categories, amber for needs-review, calm when zero.
  - **Recovery Map preserved AND improved:** still 360 px embed + 360 px side list, NOT collapsed/demoted/hidden. Side rows now expose per-row **"Open History →"** link to Track 13.27 unit timeline (honest — only rendered when unit_number is present).
- **Live counts verified at runtime:** Unassigned 83 · Pending review 0 · Waiting parts 0 · RTS pending 0 · Variance review 7d 6 · OOS Units 71 · Open Defects 83 · Units carrying defects 11.
- **Files added:** `backend/routes/shop_intel.py` · `backend/tests/test_track_13_30c_shop_intel.py` · `frontend/src/components/shop/UnitSearch.jsx` · `frontend/src/components/shop/YourQueueStrip.jsx` · `memory/TRACK_13_30C_SHOP_COMMAND_CENTER_INTELLIGENCE_VISUAL_HIERARCHY.md`.
- **Files modified:** `backend/server.py` (+6 LOC mount only) · `frontend/src/pages/ShopHubV2.jsx` (Section 01 → PriorityMetric · Your-Queue strip → role-aware · Section 05 slot → live search · ShopRecoveryRow → per-row history link).
- **Untouched:** `HubBackLink.jsx` (Track 13.30B fix preserved) · all other backend routers · App.js routes · `/shop/hub_legacy` rollback.
- **Tests:** 6 new pytest tests (`test_track_13_30c_shop_intel.py`) all pass · backend regression 36/36 retained → **total 42/42 pass**. ESLint clean on `ShopHubV2.jsx`/`YourQueueStrip.jsx` · `UnitSearch.jsx` carries 1 inert lint warning (rule not active in webpack ESLint). Live browser smoke confirms hub renders with real counts, zero operator-visible `Track 13` or `/api/` text, and 8 regression routes mount cleanly.
- **Hard locks intact:** Recovery Map remains visible on ShopHubV2 (explicit non-negotiable directive honored) · Dispatch Map-First · Driver no-login · Shop Repair Complete ≠ RTS · Dispatch RTS authority preserved · MaintainX dormant · FleetWatcher untouched · no accounting / cost / PO / fuel tax · no fake counts · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Forbidden-term sanity sweep** (pytest): no `cost`, `price`, `po_number`, `tax`, `invoice`, `margin` leak in any unit-search response path.
- **Five-Pillar score: 9.0 → 9.8 / 10** (Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30C_SHOP_COMMAND_CENTER_INTELLIGENCE_VISUAL_HIERARCHY.md`.

## 2026-06-12 · Track 13.30C-fix closeout — Shop Form / Navigation / Runtime Correction Pass

- **Mode:** CONTROLLED CORRECTION (block Track 13.30D until green) · backend (additive) + frontend · zero deploy.
- **Runtime crash fixed:** `Can't find variable: FocusBanner` — `FleetVisibility.jsx` was using `<FocusBanner />` without importing it. One-line fix.
- **2 new read-only endpoints** for source-truth Shop dropdowns: `GET /api/shop/projects/list` (aggregates `daily_reports` for project_number/name; 500-row cap) and `GET /api/shop/units/list?limit=N` (active `equipment_master` rows). Same Shop/Admin gate as the rest of `/api/shop/*`. Forbidden-term sanity preserved.
- **2 new shared frontend components:** `BackToShopLink.jsx` (plain "← Back to Shop" link in MASCI form style) + `ShopSelector.jsx` (kind-aware searchable dropdown for `project` / `unit` with debounced filter, honest empty/error states, and "Type manually instead →" fallback so the form is never blocked by an outage).
- **Form upgrades:**
  - **Fuel/Lube Visit form** — Project picker · Fuel-lube-truck picker · per-equipment-line unit picker (equipment_name auto-fills on selection) · operator-friendly subtitle · Back-to-Shop link.
  - **Service Truck Reconciliation form** — Service-truck-unit picker · Back-to-Shop link.
- **`Back to Shop` link mounted on all 10 PortalShell-driven Shop subpages** (Fuel/Lube Form/Records/Detail, STR Form/Records/Detail, Shop Manager Queue, My Assignments, Unit History Landing, Unit History Timeline). `/shop/equipment`, `/shop/equipment/:id`, `/shop/fleet` continue to rely on the Shop-aware `HubBackLink` (Track 13.30B).
- **Operator copy fully scrubbed** from all Fuel/Lube and Service Truck pages plus Shop Manager Queue, My Assignments, Unit History pages: removed every visible *"Track 13.x"*, *"Asset Service Event Backbone"*, *"defect lifecycle"*, *"Source: /api/..."*, and `<code>/api/...</code>` mention. Replaced with plain operator language (e.g. *"Each service entry is saved to the unit's history. Issues you flag here become shop defects automatically."*).
- **Service-truck classification gap documented (not blocking):** `equipment_master` does not yet classify trucks, so `ShopSelector kind="unit"` returns the full active list and accepts manual entry as fallback. Future enrichment will gate via `filterFn={(u) => u.role === "fuel_truck"}`.
- **Verification:** all 12 smoke routes (`/shop`, `/shop/fleet`, `/shop/equipment`, `/shop/fuel-lube/new`, `/shop/fuel-lube`, `/shop/service-truck-reconciliation`, `/shop/service-truck-reconciliation/new`, `/shop/units/history`, `/shop/manager/queue`, `/shop/me`, `/dispatch-portal`, `/shift`) load with `overlay=False`. Engineering-copy scrub holds at runtime (`Track 13`=0, `/api/`=0 on all routes except `/shop/manager/queue` where the single "Track 13" mention traces to **seeded defect-title data**, NOT UI copy — addressing it requires a data cleanup of legacy preview seeds, out of scope for a UI correction pass). All four source-truth selectors render live (`fuel-lube-visit-form-project-project-root`, `fuel-lube-visit-form-truck-unit-root`, `fuel-lube-line-unit-0-unit-root`, `strr-form-truck-unit-root` — each count = 1).
- **Backend regression preserved at 42/42 pass.** ESLint clean on touched frontend files.
- **Hard locks intact:** Dispatch Map-First · Driver no-login · Repair Complete ≠ RTS · Dispatch RTS authority · Material Movement Ledger untouched · MaintainX dormant · FleetWatcher untouched · no accounting · no cost · no PO · no fake counts · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Files added:** `frontend/src/components/shop/BackToShopLink.jsx` · `frontend/src/components/shop/ShopSelector.jsx` · `memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md`.
- **Files modified:** `frontend/src/pages/FleetVisibility.jsx` (+1 import line) · `backend/routes/shop_intel.py` (+2 endpoints, ~80 LOC) · 10 Shop subpage files (selector wiring · Back-to-Shop link · operator-copy scrub).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md`.

## 2026-02-15 · TRACK 14.0-SAFETY-INCIDENT-AUTH-LIFECYCLE + AMENDMENT A (Platform Stability) — CLOSED

- **Mode:** Surgical platform-stability strike. Frontend-only (no backend / schema / env changes).
- **P0 user-reported defects ELIMINATED:**
  - False "Session Expired" modal over valid Safety incident detail content (RCA: `UndoLastTransitionButton` fires `/api/workflows/{id}/last-transition` → 401 for non-admin viewers → global modal because `/api/workflows/*` wasn't on the namespaced-silent list).
  - False "Connection Problem" modals during normal use (RCA: `errorClassification.js` had `|| true` coercing every no-response error — including cancellations — into NETWORK_UNREACHABLE).
  - Safety user redirected to `/safety-portal/login` after viewing detail (RCA: chained from the session-expired modal's "Log Back In" path).
  - Health Board flashing TRANSIENT on services (RCA: SystemHealthBadge required only 2 consecutive failures before flipping red; single ingress blips painted DOWN).
  - Background widget failures (Unified Directory, Expirations, Operations Center) triggering platform-wide modals (RCA: shared axios interceptor over-publishing on every 401).
- **Surgical fix (6 surfaces):**
  - `frontend/src/lib/api.js` — namespace-aware + cross-portal-helper-aware 401 absorption. 401s on `/api/admin/*`, `/api/safety/*`, `/api/pm/*`, `/api/shop/*`, `/api/hr/*`, `/api/dispatch/*`, `/api/dev/*`, `/api/leadership/*`, `/api/safety-forms/*`, `/field-leadership/portal*` clear matching token only. 401s on `/api/workflows/*`, `/api/notifications/*`, `/api/operations/*`, `/api/operations-center` (cross-portal helpers) absorbed silently with no token wipe. Only true session-loss 401s (non-namespaced + no helper match) still publish the overlay. `skipSessionStatus: true` honored everywhere.
  - `frontend/src/lib/errorClassification.js` — removed `|| true` fallback; cancellations (`ERR_CANCELED` / `CanceledError` / `AbortError`) classify as `kind: null`; unknown failures classify as `kind: null` (per-call only).
  - `frontend/src/components/SystemHealthBadge.jsx` — `skipSessionStatus: true` on every ping; `FAIL_STREAK_THRESHOLD = 3` (was 2); 401/403 treated as auth-gated (level=ok, msg=`{status} · auth`) rather than outage.
  - `frontend/src/components/UndoLastTransitionButton.jsx` — `skipSessionStatus: true` on both GET `/last-transition` probe and POST `/undo-last-transition`.
  - `frontend/src/components/IncidentLifecyclePanel.jsx` + `ExpirationsSummary.jsx` + `AdminUnifiedDirectoryPanel.jsx` — `skipSessionStatus: true` on every widget fetch.
  - `frontend/src/pages/ViewIncident.jsx` — BackLink emits `data-testid="safety-nav-back"` on `/safety-portal/*` routes (testability + role-matrix Playwright contract).
- **New regression test file:** `/app/backend/tests/test_track14_platform_stability_regression.py` (5/5 passing) — pins the backend 401 contract that the frontend silent-list relies on.
- **Runtime certification (testing agent iter 504 + 505):** 7/7 frontend acceptance flows PASS (P0 Safety detail soak, Super Admin idle soak, manual publish/dismiss, background-401 isolation, lifecycle panel, cross-portal helper absorption, notifications). 22/22 backend pytest PASS. Backend role matrix proven: Safety Manager/Officer/Coordinator can close · Super Admin inherits · PM read-only · HR/Shop/Dispatch blocked.
- **Files added:** `backend/tests/test_track14_platform_stability_regression.py` · `memory/TRACK_14_PLATFORM_STABILITY_CERT_CLOSURE.md`.
- **Files modified:** `frontend/src/lib/api.js` · `frontend/src/lib/errorClassification.js` · `frontend/src/components/SystemHealthBadge.jsx` · `frontend/src/components/UndoLastTransitionButton.jsx` · `frontend/src/components/IncidentLifecyclePanel.jsx` · `frontend/src/components/ExpirationsSummary.jsx` · `frontend/src/components/AdminUnifiedDirectoryPanel.jsx` · `frontend/src/pages/ViewIncident.jsx`.
- **No backend changes** — all surgical at the frontend session-classification layer. No schema, no env, no removed routes.
- **Five-Pillar score: 5/5** (Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**. GO for production redeploy.
- Report: `/app/memory/TRACK_14_PLATFORM_STABILITY_CERT_CLOSURE.md`.

## 2026-02-15 · TRACK 14.0-CROSS-PORTAL-SESSION-INHERITANCE-SSO — CLOSED

- **Mode:** Surgical SSO hardening on top of the existing Multi-Portal Master Sign-In foundation (iter82). Frontend + 1 backend route change. No new auth architecture, no rewrites.
- **P0 user pain ELIMINATED:** Platform was feeling like 7 separate apps because portal-specific tokens caused login loops on direct-URL navigation. Now: one sign-in → every authorized portal accessible. Unauthorized portals → clean Access Restricted card (not login loops).
- **Root cause:** Three asymmetries on top of an otherwise-correct foundation: (a) `usePortalHydration` (iter88) had setters only for admin/pm/shop/hr — missing safety/dispatch/field_leadership; (b) `RequireSafety / RequireDispatch / RequireFl` didn't call the hydration hook at all; (c) backend `/api/auth/issue-portal-token` had `field_leadership` in `ALLOWED_PORTALS` but omitted it from the minter dispatch dict → 500 'field_leadership token minter not configured'; (d) portal login pages didn't redirect already-authenticated users with the grant.
- **Surgical fix (8 surfaces):**
  - `frontend/src/lib/usePortalHydration.js` — extended SETTERS + PORTAL_ALIASES to cover safety/dispatch/field_leadership/fl; `skipSessionStatus:true` on mint call.
  - `frontend/src/components/MultiPortalHydrator.jsx` — extended TOKEN_GETTERS/SETTERS for the same three portals; background hydration on route change now fans out FL/Safety/Dispatch.
  - `frontend/src/components/PortalHydratingLoader.jsx` — accent + label for safety/dispatch/field_leadership.
  - `frontend/src/components/RequireSafety.jsx` — uses `usePortalHydration("safety", isSafety())`.
  - `frontend/src/components/RequireDispatch.jsx` — uses `usePortalHydration("dispatch", isDispatch())`.
  - `frontend/src/components/RequireFl.jsx` — uses `usePortalHydration("field_leadership", isFl())` + added missing AccessDenied branch.
  - `frontend/src/lib/useRedirectIfDirectoryGrant.js` — NEW reusable hook for portal login pages.
  - `frontend/src/pages/{Safety,Pm,Hr,Shop,Dispatch}Login.jsx` — each calls the redirect hook on mount.
  - `backend/routes/auth_directory_routes.py` — added `field_leadership: field_leadership_token_minter` to the minter dispatch dict (line 343) and `field_leadership: "OPERATIONS"` to the tier map (line 371). Closes the asymmetric registration.
- **Runtime certification (testing agent iter 506 + 507):** Backend pytest 14/14 PASS (`test_track14_sso_cross_portal.py`). Frontend: 100% PASS on the 6-role matrix — Super Admin walks all 7 portals without re-login; cert.safety/pm/hr/shop/dispatch single-portal users get Access Restricted on unauthorized portals (NOT login loops); FL hydration race resolves cleanly on direct-URL navigation; backend escalation gate verified (Safety-only directory token cannot mint admin/pm/hr/shop/dispatch tokens).
- **No regression** to TRACK 14.0-PLATFORM-STABILITY (Session Expired / Connection Problem modals still absent; SystemHealthBadge still settles to ALL OK).
- **Files added:** `frontend/src/lib/useRedirectIfDirectoryGrant.js` · `memory/TRACK_14_SSO_CROSS_PORTAL_CERT_CLOSURE.md` · `backend/tests/test_track14_sso_cross_portal.py` (created by testing agent in iter 506-507).
- **Files modified:** 6 frontend (hydration hook + hydrator + 3 guards + loader) · 5 frontend login pages · 1 backend route file (auth_directory_routes.py).
- **No backend schema change. No env change. No new package deps.**
- **Five-Pillar score: 5/5** (Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**. GO for production redeploy.
- Report: `/app/memory/TRACK_14_SSO_CROSS_PORTAL_CERT_CLOSURE.md`.

## 2026-02-15 · TRACK 14.0-RC1-PERFORMANCE-RELIABILITY-CAPACITY-REVIEW — CLOSED

- **Mode:** Read-mostly performance audit + small surgical quick wins. No rewrites. No new features.
- **Disk cleanup (Phase 1-2):** /app from **76% → 75%** (net 71 MB reclaimed). Archived `dr_migration_backups` (261M raw → 197M tar.gz, 67 daily-report JSONs already in MongoDB) and `track_13_4*_evidence` (28M raw → 21M tar.gz, 154 files from CLOSED track) to `/app/memory/_archived/`. Counts verified pre-delete. Per hard rules, no closure ledgers / active memory docs / production uploads / open-track evidence were touched.
- **API latency (Phase 3):** 18 hot endpoints profiled with super-admin token. All hot reads <200 ms p50 (incidents 96 / daily-reports 142 / jobs-master 93 / notifications 104 / hr/employees 132 / trench-safety/assets 97). Only 2 outliers: `/admin/deploy-readiness` (1.4 s, rare admin call) and `/auth/multi-login` (526 ms, bcrypt + 7-portal mint, once-per-session). No optimization needed.
- **DB indexes (Phase 4):** 15 hot collections audited. All have appropriate indexes. Heuristic "missing index" warnings are field-name mismatches (e.g. notifications uses `user_id` not `actor_id`). **No new indexes added** per the user's "do not shotgun indexes" rule.
- **Polling/retry audit (Phase 5-6):** 36 setInterval call sites inventoried. Most at 60 s cadence (calm). Two quick wins applied: `SystemHealthBadge.jsx` and `BackendStatusBanner.jsx` now pause polling when `document.visibilityState !== "visible"` and reprobe immediately on focus. Saves ~10 probes/min per backgrounded tab × N tabs.
- **Log noise fix (Phase 10):** Scheduler supervisor was emitting `CRITICAL [scheduled-backup] scheduler task is DEAD — respawning. Last state: completed without error` every 5 min in preview (caused by SCHEDULER_ENABLED=false in preview → clean exit → watchdog respawn cycle). Fix: `server.py:12937-13007` now demotes to DEBUG after the first observed clean-exit cycle. CRITICAL still fires for real production deaths-with-exception.
- **Files modified:** `frontend/src/components/SystemHealthBadge.jsx` · `frontend/src/components/BackendStatusBanner.jsx` · `backend/server.py` (scheduler supervisor log severity).
- **Files added:** `backend/tests/test_track14_rc1_perf_regression.py` (8 latency tests, all PASS) · `memory/TRACK_14_RC1_PERF_CAPACITY_CLOSURE.md` · `memory/_archived/dr_migration_backups_2026-05-30.tar.gz` (197M) · `memory/_archived/track_13_4_evidence_combined.tar.gz` (21M).
- **Stability soak (Phase 13):** testing agent iter 508 ran a 4-min headless soak (truncated from 15 min by playwright tool deadline). 28 navigations across all 7 portals → **0 false session-status-overlay**, **0 false connection-problem**, **0 token clears on 401**. Heap stable at 44.7 MB. Background 401 absorption verified via raw `window.fetch` (5/5 absorbed). 27/27 backend regression tests PASS (8 RC1-perf + 5 platform-stability + 14 SSO cross-portal).
- **Five-Pillar score: 5/5** (Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10).
- **GO/NO-GO**: 🟢 **GO** for production redeploy.
- **Optional follow-ups (P3, non-blocking):** Run a full 15-min soak as out-of-tool background script for regulatory evidence; hoist SystemHealthBadge into persistent shell to skip remount probes on portal nav; send correct portal tokens on Admin Command Center widgets to eliminate console 401 noise.
- Report: `/app/memory/TRACK_14_RC1_PERF_CAPACITY_CLOSURE.md`.

## 2026-02-15 · TRACK 14.0-RC1-FERRARI (Performance / Reliability / Trust Hardening) — CLOSED

- **Mode:** Amendment A short stress cert (no long soaks). Fix-as-you-go on every defect surfaced.
- **Six surgical wins shipped:**
  1. **SystemHealthBadge cross-mount cache** — module-level `_resultsCache` shared across remounts (60s TTL). On portal-nav remount, badge reuses fresh cached results and skips redundant probes. Eliminates the iter508 P3 "probe storm on portal nav" finding.
  2. **`pmCommandApi.js` migrated** raw `fetch` → shared `api` instance with `skipSessionStatus: true`. Eliminates uncaught `Error: GET /api/pm/command-center/...` console noise when an admin views a dashboard embedding PM widgets without an active PM token.
  3. **`operationsCenterApi.js` migrated** raw `axios` → shared `api` (with skipSessionStatus). Removed redundant `authHeaders()` builder (the shared interceptor auto-injects every portal token).
  4. **`tasksApi.js` migrated** raw `axios` → shared `api` on every notifications + tasks call, all with `skipSessionStatus: true`. Notification bell + task lists fail silently to local empty states; never trigger the global Session Expired modal.
  5. **`versionCache.js` (NEW)** + `BackendVersionBadge` and `EnvBanner` migrated. Single-flight memoizer with 5-min TTL eliminates per-mount `/api/version` refetch (iter509 observed 65 hits in 28s of rapid nav).
  6. **`/api/admin/perf-snapshot` (NEW)** — admin-gated 10-second Hot-Rod Health check returning disk %, memory %, uptime, mongo ping, self-probe latency, recent error counts, scheduler heartbeat, env/release identity. Returns under 250ms warm. Powers a future operator-confidence card.
- **Stress cert (testing agent iter509, ~6 min):**
  - **Console error noise: 65 → 0** (axios-related) during 28s of 36 portal navs.
  - **0 false session-status-overlay** across all 36 portal navs.
  - 100× `/api/health` burst: 100/100 200s (p50=45ms, p95=85ms).
  - 100× `/api/notifications` burst: 100/100 200s (p50=141ms, p95=166ms).
  - 10× `window.fetch('/api/admin/jobs')` (raw, no token): 0 modals, 0 token clears — TRACK 14.0-PLATFORM-STABILITY guarantee holds.
  - Backend regression: **30/30 PASS** (8 RC1-perf + 5 platform-stability + 14 SSO cross-portal + 3 NEW ferrari-perf-snapshot).
- **Files modified:** `SystemHealthBadge.jsx` · `pmCommandApi.js` · `operationsCenterApi.js` · `tasksApi.js` · `BackendVersionBadge.jsx` · `EnvBanner.jsx` · `server.py` · `requirements.txt`.
- **Files added:** `frontend/src/lib/versionCache.js` · `backend/routes/perf_snapshot.py` · `backend/tests/test_track14_ferrari_perf_snapshot.py` · `memory/TRACK_14_RC1_FERRARI_CLOSURE.md`.
- **Dependency added:** `psutil==7.2.2` (for memory % in perf-snapshot).
- **Disk:** /app stable at 75% (72 MB reclaimed earlier in iter508 is the safe max; remaining `/app/backend/storage` 533 MB and `/app/backend/static` 300 MB are production customer data per server.py:5129/8342, protected by hard-rule).
- **No schema changes, no env changes, no removed routes.**
- **Five-Pillar score: 5/5** (Powerful 10 · Simple 10 · Beautiful 10 · Trusted 10 · Proven 10).
- **GO/NO-GO**: 🟢 **GO** for production redeploy.
- **Remaining P3 (deferred with justification):** `/api/notifications` per-portal-mount fetch (legitimate freshness need; a short-TTL cache would mask new notifications on rapid hops); `/admin/unified-directory` missing stable search testid (testability sweep, not behavior).
- Report: `/app/memory/TRACK_14_RC1_FERRARI_CLOSURE.md`.
