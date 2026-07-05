# Technical Debt Register — MASCI Operations Platform

**Doctrine:** Track 20.6A — Technical Debt & Failure Discovery Amendment.


## 🟢 DR-UNIFY-002 · Debt Closures (2026-02-15)

The following debt items opened by DR-UNIFY-001 are RESOLVED:

- ✅ **DEBT-DRUNIFY-01** · Orphaned Admin OI file — root-level `pages/AdminOperationalIntelligence.jsx` DELETED (zero imports verified).
- ✅ **DEBT-DRUNIFY-02** · Orphan admin route `/admin/ods-intelligence` — now `<Navigate replace to="/admin/operational-intelligence">`.
- ✅ **DEBT-DRUNIFY-03** · Speculative `/executive/ods-intelligence` — now `<Navigate replace to="/admin/operational-intelligence">`. Executive Dashboard NOT claimed until a real Executive Portal is defined (DR-UNIFY-005 · future).
- ✅ **DEBT-DRUNIFY-06** · Non-unified Approved Reports list — new `/api/daily-reports/approved` returns union of legacy + modern with `source` badge.
- ✅ **DEBT-DRUNIFY-07** · P0 admin-token auth 401 — `require_admin_pm_or_hr_read` + `_require_hr_or_admin_for_queue` now use `_is_valid_directory_admin_token_async`. Verified live with 101-char directory admin token.

## 🟠 Debt Remaining for DR-UNIFY-003

- **DEBT-DRUNIFY-04** · Internal V2 naming in filenames + testids — remains internal-only per doctrine. Rename in DR-UNIFY-003 (frontend) alongside collection renames.
- **DEBT-DRUNIFY-05** · Feature flags `dr_v2_optin`, `REACT_APP_DR_V2_ENABLED`, `DR_V2_AI_ENABLED` — retire post-cutover in DR-UNIFY-004.
- **DEBT-DRUNIFY-08** · V2 shell not merged into V1 form — merge in DR-UNIFY-003.
- **DEBT-DRUNIFY-09** · Mongo `dr_v2_*` collection renames — DR-UNIFY-003 (with idempotent migration script).
- **DEBT-DRUNIFY-10** · Legacy break-glass `POST /api/admin/login` — LOW priority. DR-UNIFY-003.



## 🟠 DR-UNIFY-001 · Single-System Consolidation Debt (opened 2026-02-15)

**Origin:** DR-ROI/ODS work introduced parallel `dr_v2_*` surfaces that risked becoming a permanent product fork. User amendment locked the one-system rule. Full audit: `/app/memory/DR_UNIFY_001_SINGLE_SYSTEM_AUDIT.md`.

### DEBT-DRUNIFY-01 · Orphaned Admin OI file
- **File:** `/app/frontend/src/pages/AdminOperationalIntelligence.jsx` (root-level)
- **Duplicate of:** `/app/frontend/src/pages/admin/AdminOperationalIntelligence.jsx` (canonical, nav-linked)
- **Exit criteria:** file removed after DR-UNIFY-002 verifies zero remaining imports.
- **Owner:** front-end.
- **Track:** DR-UNIFY-002.

### DEBT-DRUNIFY-02 · Orphaned admin route `/admin/ods-intelligence`
- **Location:** `AppRoutes.jsx:1223`.
- **Reason:** no nav entry; duplicate of `/admin/operational-intelligence`.
- **Exit criteria:** route converted to `<Navigate to="/admin/operational-intelligence" replace />` in DR-UNIFY-002.
- **Track:** DR-UNIFY-002.

### DEBT-DRUNIFY-03 · Speculative executive route `/executive/ods-intelligence`
- **Location:** `AppRoutes.jsx:1224`.
- **Reason:** no nav entry, no role guard, no hub, no exec token infrastructure. Speculative surface.
- **Exit criteria:** route converted to a Navigate redirect OR deleted in DR-UNIFY-002. `ExecutiveOperationalIntelligence.jsx` file kept as scaffold for a future real Executive Portal track (DR-UNIFY-005).
- **Track:** DR-UNIFY-002.

### DEBT-DRUNIFY-04 · Internal V2 naming in filenames and testids
- **Files:** `pages/daily-report-v2/*`, `components/DrV2ApprovedReportsPanel.jsx`, `lib/dailyReportV2*.js`, `lib/drV2Api.js`.
- **Reason:** internal iteration marker; risks user confusion if it leaks to nav/URLs.
- **Exit criteria:** rename to non-versioned names in DR-UNIFY-002 (frontend) and DR-UNIFY-003 (backend routes + Mongo collections).
- **Track:** DR-UNIFY-002 / DR-UNIFY-003.

### DEBT-DRUNIFY-05 · Feature flags `dr_v2_optin` / `REACT_APP_DR_V2_ENABLED` / `DR_V2_AI_ENABLED`
- **Reason:** intentional rollout flags; must be retired after cutover per user's Rule 9 (no permanent product forks).
- **Exit criteria:** flags removed after DR-UNIFY-004 deployment cert.
- **Track:** DR-UNIFY-004.

### DEBT-DRUNIFY-06 · Non-unified Approved Reports list
- **Endpoint:** `/api/dr-v2/reports/approved` currently surfaces only `dr_v2_drafts` with an accept entry.
- **Gap:** does not include legacy `daily_reports` approved via lifecycle transitions.
- **Exit criteria:** endpoint returns union of both sources with `source: "legacy" | "modern"` badge, aliased to `/api/daily-reports/approved` in DR-UNIFY-002.
- **Track:** DR-UNIFY-002.

### DEBT-DRUNIFY-07 · Admin token gate 401 (P0 · dormant since TRACK 15.32)
- **Root cause:** `require_admin_pm_or_hr_read` calls sync stub `_is_valid_admin_token` (retired in TRACK 15.32, always returns False). Admin tokens are silently rejected on `/api/dr-v2/*` and `/api/admin/daily-*`.
- **Also affects:** `require_admin_or_pm_read` (server.py:549) likely has the same bug — needs audit.
- **Exit criteria:** switch to `_is_valid_directory_admin_token_async` (matching `require_admin`). See `/app/memory/DR_UNIFY_001_P0_ADMIN_TOKEN_401.md`.
- **Track:** DR-UNIFY-002 (before Wave-2 live smoke can pass).

### DEBT-DRUNIFY-08 · V2 field shell not merged into V1 form
- **File:** `pages/daily-report-v2/DailyReportV2.jsx` runs as a separate flagged surface.
- **Exit criteria:** shell content merged into `pages/NewDailyReport.jsx` as a native upgrade; V2 route redirects; pilot opt-in flag retired.
- **Track:** DR-UNIFY-002.

### DEBT-DRUNIFY-09 · Collection renames pending
- **Collections:** `dr_v2_drafts`, `dr_v2_ai_audit_entries`, `dr_v2_ai_approvals`, `dr_v2_bilingual_audit`.
- **Exit criteria:** rename to `daily_report_*` variants via idempotent migration script in DR-UNIFY-003.
- **Track:** DR-UNIFY-003.

### DEBT-DRUNIFY-10 · Legacy break-glass `POST /api/admin/login` degraded
- **Symptom:** returns empty/no-op token in preview (retired alongside TRACK 15.32).
- **Docs:** `/app/memory/test_credentials.md` still describes the endpoint as functional.
- **Exit criteria:** either restore the endpoint to issue a valid directory admin token, or delete it and update docs.
- **Priority:** LOW (normal admins use `/api/auth/multi-login`).
- **Track:** DR-UNIFY-003.


Every failure, warning, regression, broken test, import error, compile
issue, dependency issue, environment issue, or architectural defect
discovered during any audit / promotion / certification MUST be
classified into exactly one of:

- **A — Fix Now:** small, low-risk, inside current track. MUST be
  corrected before certification.
- **B — Blocks Deployment:** production risk. Current track cannot
  close until resolved.
- **C — Existing Technical Debt:** verified pre-existing. Does not block
  current work. MUST generate a Debt ID and enter this register.
- **D — False Positive:** proven not to be an issue. Evidence required.

**"No action" is NOT an allowed outcome.**

## Active Register

| ID | Title | Class | Owner | Priority | Target Track | Status |
|---|---|---|---|---|---|---|
| TD-19.62-A01 | Duplicate `label:` keys in `FleetUnitThread.jsx :: deriveRelationships` (5 instances · pre-existing lint debt surfaced when Track 19.62 extended the file) | **A** — Fix Now | Fleet-Thread team | P2 | 19.62 | **FIXED** (2026-08-03) |
| TD-20.6A-001 | `test_vocabulary_unauth_401` returns 200 instead of 401 in live e2e | **C** — pre-existing test/env debt | Safety-Records team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · fresh session isolation + live 401 verified · see `TRACK_20_6B_FIX_REPORT_TD_20_6A_001.md`) |
| TD-20.6A-002 | `test_vocabulary_hr_sees_all_lanes` uses strict-equality assertion that broke when Track 19.59 additively added the `vendor` lane | **C** — pre-existing test debt from Track 19.59 | Safety-Records team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · superset assertion + certified-set guardrail · see `TRACK_20_6B_FIX_REPORT_TD_20_6A_002.md`) |
| TD-20.7-B01 | `PhotoUpload.jsx` "Take Photo" button silently no-oped on desktops without a webcam / permission-blocked / HTTP contexts (reported by a real field user on the Daily Report) | **B** — Blocks Deployment | Universal-Photo team | P0 | 20.7 | **FIXED** (2026-08-04) |
| TD-20.7-C01 | `test_daily_reports.py` + `test_job_photos.py` legacy suites hit endpoints without the multi-login token introduced in TRACK 15.32; they fail with 401/410 regardless of Track 20.7. Confirmed identical failure count before and after Track 20.7 via `git stash` baseline run. | **C** — pre-existing test debt from TRACK 15.32 auth-model migration | Testing team | P3 | 20.6B (test hardening) | **CLOSED** (2026-08-04 · migrated to `/api/auth/multi-login` + admin/hr/safety triple-token fixture · additive R2/data URL accept-list · see `TRACK_20_6B_FIX_REPORT_TD_20_7_C01.md`) |
| TD-20.6B-A01 | Auto-email dispatcher (`_dispatch_auto_email`) had no synthetic-test-record short-circuit, allowing any preview-environment test run against `POST /api/daily-reports` (or any workflow submit) to trigger real Resend emails to the assigned PM + always-CC list | **A** — Fix Now | Operations Trust team | P1 | 20.6B | **FIXED** (2026-08-04 · added `project_name.startswith("TEST_")` short-circuit with trust-spine `status="skipped"` audit) |
| TD-20.8-D01 | Track 20.8 human-walkthrough smoke script initially probed `/dispatch` and observed 404. Investigation showed the canonical dispatch portal route is `/dispatch-portal` (per `frontend/src/App.js:1076`). Live curl of `/dispatch-portal` returns 200. | **D** — False Positive | Testing team | P3 | 20.8 | **CLOSED** (2026-08-04 · evidence: `curl -s -o /dev/null -w "%{http_code}\n" https://safety-audit-mobile-1.preview.emergentagent.com/dispatch-portal` → 200) |
| TD-20.8-A01 | `test_approve_without_employee_linkage_blocked` was skipping via a permissive `pytest.skip` branch that hid a payload bug (missing `record_type` field → 422 validation → skip fired) — the certified employee-linkage gate was never actually exercised. | **A** — Fix Now | Testing team | P1 | 20.8 | **FIXED** (2026-08-04 · added `record_type` to payload · removed the skip branch · added hard assertions on both halves of the certified contract [pending_match creation + blocked approval] · live-verified via preview curl · see `TRACK_20_8_FIX_REPORT_TD_20_8_A01.md`) |
| TD-20.9-A01 | `MasterListPanel.jsx::restoreRow` was called from the archive-tab restore button but never defined. Every restore click threw `ReferenceError: restoreRow is not defined`. Caught by the real ESLint 9 gate introduced in Track 20.9. | **A** — Fix Now | Frontend team | P1 | 20.9 | **FIXED** (2026-08-04 · added missing `restoreRow` async function using the same pattern as other row mutations in the file · lint clean · see `TRACK_20_9_CLEANUP_REPORT.md`) |
| TD-20.9-A02 | `TrenchBoxPosterCard.jsx` imported `useBranding` at top of file but never called it, then referenced `branding.safety_email` / `branding.support_email` / `branding.platform_display_name` in JSX. Every render threw `ReferenceError: branding is not defined`. Caught by real ESLint 9. | **A** — Fix Now | Frontend team | P1 | 20.9 | **FIXED** (2026-08-04 · added `const branding = useBranding();` inside component body before any `branding.*` reference · see `TRACK_20_9_CLEANUP_REPORT.md`) |
| TD-20.9-C01 | 708 duplicate keys in `frontend/src/lib/i18n.js` bilingual dictionary (silent last-write-wins on translations). Batch-fixing 700+ dedupes pre-deploy is high-risk to actual translations. | **C** — Existing Tech Debt | i18n team | P2 | 21.x (bilingual cleanup) | **OPEN** |
| TD-20.9-C02 | 188 `react/no-unescaped-entities` errors across ~80 frontend files (cosmetic quote-escape). Auto-fixable via `eslint --fix`, but touching 188 files pre-deploy is unnecessary risk. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x (lint polish) | **OPEN** |
| TD-20.9-C03 | 78 unused `eslint-disable` directive warnings — legacy comments no longer suppressing anything. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |
| TD-20.9-C04 | 6 `react/no-unstable-nested-components` errors (in-render component defs cause re-mount + state loss on every parent render). Real render-perf bugs but not runtime crashes. | **C** — Existing Tech Debt | Frontend team | P2 | 21.x (careful refactor) | **OPEN** |
| TD-20.9-C05 | 5 `no-empty` in `GlobalSearch.jsx` — intentional `catch {}` around `localStorage` for private-browsing safety. Rewrite to `catch { /* storage unavailable */ }`. | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |
| TD-20.9-C06 | 6 misc lint findings (3× `no-console`, 2× `no-await-in-loop`, 1× `no-unused-vars`, 1× `no-regex-spaces`, 1× `react/no-unknown-property`). | **C** — Existing Tech Debt | Frontend team | P3 | 21.x | **OPEN** |
| TD-21.0-C01 | 25 stale root `.md` audit docs pending archive to `/app/memory/_archived/` | **C** — repo hygiene | Docs team | P3 | 21.z | **OPEN** |
| TD-21.0-C02 | 12 legacy frontend pages behind `/legacy/*` router (no primary-nav link) | **C** — post-deploy retire | Frontend team | P3 | 21.y | **OPEN** |
| TD-21.0-C03 | 5 legacy Mongo collections (`db.legacy_*` / `db.deprecated_*`) — historical reads only | **C** — post-deploy retire | Data team | P3 | 19.62 Phase B / 21.x | **OPEN** |
| TD-21.0-C04 | ~40 iter### legacy test files using retired shared-password admin login (pre-Track-15.32) | **C** — test cleanup | Testing team | P3 | 21.x | **OPEN** |
| TD-21.0-C05 | `backend/server.py` = 15,986 lines · Phase-2 modularization plan documented in Track 20.9 | **C** — architecture debt | Backend team | P2 | 21.x | **OPEN** |
| TD-21.0-C06 | `frontend/src/App.js` = 1,283 lines · Phase-2 route-group extraction plan documented | **C** — architecture debt | Frontend team | P2 | 21.y | **OPEN** |
| TD-21.0-C07 | CORS `allow_methods=["*"]` / `allow_headers=["*"]` tightening | **C** — Phase-2 hardening | Backend team | P3 | 21.a | **OPEN** |
| TD-21.2E-A01 | Track 20.6B `TEST_`-prefix email gate was insufficient: 72 non-`TEST_` payloads across 36 test files (57 distinct project_name literals) submitted workflow records via `requests.post` and reached `_dispatch_auto_email`, firing live Resend calls in preview (`AUTO_EMAIL_REPORTS=true` + real `RESEND_API_KEY`). Root cause + full inventory: `memory/TRACK_21_2E_EMAIL_SAFETY_CLOSEOUT.md` + `memory/track_21_2e/NON_TEST_PAYLOAD_INVENTORY.md`. | **A** — Fix Now | Backend | P0 | 21.2E | **FIXED** (2026-07-04 · SDK-level kill switch installed in `server.py` behind `EMAIL_SAFETY_MODE` env guard · `auto_email_enabled()` honors safety mode · `_dispatch_auto_email` short-circuits before recipients_for_record_async · preview `.env` set to `strict` · unit lock test 11/11 green · zero production drift). |
| TD-21.2-C03 | 5 same-named React component filenames at different paths (`EmptyState.jsx`, `StatusBadge.jsx`, `DraftStatusPill.jsx`, `HelpTip.jsx`, `SideNavV2.jsx`) — two independent implementations each. Consolidation requires behavior-parity proof (merge policy). | **C** — Existing Tech Debt | Frontend | P2 | 21.y | **OPEN** (documented in `TRACK_21_2_PHASE3_DEEP_SWEEP_REPORT.md`) |
| TD-21.2-C04 | 68 MongoDB collection names referenced only once across the backend. Per-collection retention review required to determine dead vs single-use audit. | **C** — Existing Tech Debt | Backend | P2 | 21.2z | **OPEN** |
| TD-21.2-C05 | 168 env vars referenced via `os.environ.get(x, default)` are not declared in `backend/.env`. All have safe defaults; no runtime failure. Documentation debt only. | **C** — Documentation Debt | Backend / Ops | P3 | 21.2z | **CLOSED** (2026-07-04 · Track 21.3 Phase A · full classification in `TRACK_21_3_ENV_VAR_CENSUS.md` · new `backend/.env.example` canonical template committed) |
| TD-21.2E1-C01 | R2 object storage may accumulate `TEST_*` prefixed blobs during regression runs. | **C** — Existing Tech Debt | Backend | P2 | 21.2z (Storage Hygiene) | **RETIRE-WITH-PLAN** (2026-07-04 · Track 21.3 Phase C · janitor script spec in `TRACK_21_3_STORAGE_HYGIENE_REPORT.md`; execution queued for Ops sign-off) |
| TD-21.2-C04 | 68 MongoDB collection names referenced only once across the backend. | **C** — Existing Tech Debt | Backend | P2 | 21.2z | **RECLASSIFIED** (2026-07-04 · Track 21.3 Phase D · ~60 Class-D scanner false positives · ~5 Class-E audit-only collections · ~3 Class-C RETIRE-LATER queued for Ops) |
| TD-21.3-C01 | CORS wildcard `allow_methods=["*"]` / `allow_headers=["*"]` broadened side-effect surface. | **C** — Existing Tech Debt | Backend | P2 | 21.3 | **CLOSED** (2026-07-04 · Track 21.3 Phase B · replaced with explicit allow-lists of methods (7) + headers (12) + expose_headers (4). Preflight verified via safe curl smoke under `EMAIL_SAFETY_MODE=strict`. `TRACK_21_3_CORS_HARDENING_REPORT.md`) |
| TD-21.2E1-C01 | R2 object storage may accumulate `TEST_*` prefixed blobs during regression runs. Blobs are size-bounded (25 MB) and carry the `TEST_` sentinel in payload metadata → sweep-safe. | **C** — Existing Tech Debt | Backend | P2 | 21.2z (Storage Hygiene) | **OPEN** (documented in `TRACK_21_2E1_SIDE_EFFECT_GUARDRAIL.md`; nightly janitor recommended) |
| TD-21.2E1-C02 | Sentry receives error events from test-triggered code paths in preview. Desired behavior for regression triage. If undesired for a specific test class, add SENTRY_ENVIRONMENT=test filter upstream. | **C** — Existing Tech Debt (documented, not a safety defect) | Ops | P3 | 21.2z | **OPEN** |
| TD-21.2E-C01 | Follow-up defense-in-depth: canonicalize 72 non-`TEST_` payload literals across 36 test files. | **C** | Backend / Test | P1 | 21.2E-1 | **CLOSED** (2026-07-04 · Track 21.2E-1 idempotent canonicalizer rewrote 59 literals · 13 duplicates safely skipped · 3 additional `job_name` offenders fixed in Phase 3 · 0 residual · 15/15 permanent guardrail assertions green · full recertification in `TRACK_21_2E1_EMAIL_SAFETY_RECERTIFICATION.md`) |
| TD-21.2-A02 | 4 backend test files hard-crashed pytest collection with `from tests.conftest import URL, ADMIN_TOKEN` (no soft-skip). Broke the regression envelope for the 4 modules. | **A** — Fix Now | Backend / Test | P0 | 21.2 | **FIXED** (2026-07-04 · wrapped in `try/except ImportError` + `pytest.skip(allow_module_level=True)` — same pattern the other 6 preview-URL-dependent files already used) |
| TD-21.2-D01 | Phase 2A scan v1 reported 393 backend endpoints "without auth" and 17 uploads without auth. Root cause: my AST scanner didn't recognize `actor: Dict[str, Any] = _actor_dep()` (indirect `Depends(require_actor)` via a helper closure). Manual review confirmed 100% of the "gaps" are either certified public workflow endpoints (Daily Reports, JHA, calculators, dropdowns) or the `_actor_dep()` pattern. Zero real gaps. Scanner v2 corrected. | **D** — False Positive | n/a | n/a | 21.2 | **DOCUMENTED** (2026-07-04 · `memory/track_21_2/RECONCILIATION_MATRIX.md` Class-D ledger) |
| TD-21.0-C08 | `require_admin_pm_or_hr_read` still uses retired sync-HMAC admin validator | **C** — auth cleanup | Backend team | P2 | 21.x | **OPEN** |
| TD-20.9-C01 | (see below — closed by Track 21.1) | **C** | i18n team | P2 | 21.1 | **CLOSED** (2026-07-04 · dedup completed; orphan value-lines pruned; `no-dupe-keys` clean) |
| TD-20.9-C02 | (see below — closed by Track 21.1) | **C** | Frontend team | P3 | 21.1 | **CLOSED** (2026-07-04 · 188 unescaped entities converted to HTML entities via safe positional codemod) |
| TD-20.9-C05 | (see below — closed by Track 21.1) | **C** | Frontend team | P3 | 21.1 | **CLOSED** (2026-07-04 · 5 `catch {}` in `GlobalSearch.jsx` given intent-documented no-op comments) |
| TD-21.1-C01 | 6 `react/no-unstable-nested-components` sites tagged with intent-documented `// eslint-disable-next-line` markers pointing at Track 21.y refactor. Behavior preserved (zero-drift); hoisting deferred to avoid closure/testId regression risk. Sites: `OpenItemsPanel.jsx`, `ui/calendar.jsx` (×2), `SafetyFormsRecords.jsx`, `TrenchBoxesAdmin.jsx`, `transportation/_orientation.jsx`. | **C** — Existing Tech Debt | Frontend team | P2 | 21.y (careful refactor) | **OPEN** |
| TD-21.1-C02 | 1 `react/no-unknown-property` on cmdk `cmdk-input-wrapper` attribute (vendor pattern from shadcn/ui). Marked with in-file eslint-disable pending vendor upgrade. | **C** — Existing Tech Debt | Frontend team | P3 | 21.y | **OPEN** |
| TD-21.1-D01 | Previous session's `i18n.js` dedup left 10 value-only orphan lines and 9 duplicate keys unresolved; frontend build was actually broken (webpack + eslint parse error) despite the handoff claiming "build clean". Fixed during Track 21.1 by pruning orphans and removing earlier duplicate occurrences (keeping the runtime-effective later ones per JS last-write-wins semantics). | **A** — Fix Now (surfaced by Track 21.1) | Frontend team | P0 | 21.1 | **FIXED** (2026-07-04) |
| TD-22.1-C01 | `backend/server.py` = 16,094 lines. Modularization requires a full endpoint-parity harness (route set · Depends-chain · scheduler start-order · SDK-patch import ordering · startup/shutdown event count · health-endpoint bodies). Zero-Drift mandate blocks any move without parity proof. | **C** — Architecture Debt (deferred with plan) | Backend team | P1 | 22.1 | **PARTIAL — CLOSED for Phase 1 + Phase 1b** (2026-07-04 · Track 22.1 extracted health probes + rate-limiting · Track 22.1B extracted email dispatch scaffolding with SHA-256 bytecode fingerprint lock on the un-moved 473-line dispatcher body · server.py 16,117 → 16,028 · 179/179 lock envelope) |
| TD-22.1b-C01 | `_dispatch_auto_email` + Resend SDK monkey-patch import-ordering | **C** — Architecture Debt (deferred with plan) | Backend team | P2 | 22.1b | **PARTIAL — CLOSED for scaffolding** (2026-07-04 · Track 22.1B extracted `_filename_for`, `_is_severe_incident`, `_KIND_TO_COLLECTION`, `_AUTO_EMAIL_DISPATCH_TASKS`, `schedule_auto_email`, plus new `register_dispatcher` indirection · dispatcher body remains inline in server.py and is bytecode-locked · SDK-patch import order preserved · 17/16 new assertions · zero drift) |
| TD-22.1c-C01 | Scheduler bootstrap (51 startup handlers, 39 create_task chains) | **C** — Architecture Debt (deferred with plan) | Backend team | P2 | 22.1c | **CLOSED for Inventory + Bytecode Lock** (2026-07-04 · Track 22.1C · full 51-handler inventory JSON · SHA-256 bytecode fingerprints on the 4 email-capable scheduler handlers + Track 22.1B dispatcher · new `verify_locked_bytecode(app)` utility · zero handler moved · 195/195 lock envelope) |
| TD-22.1c2-C01 | FastAPI `@app.on_event` deprecation — 51 startup + 1 shutdown handlers should migrate to `lifespan` context manager | **✅ RESOLVED** | Backend team | — | Tracks 22.1D · 22.1E · 22.1F · 22.1G · 22.1H · 22.1I · 22.1I.1 · 22.1J · 22.1L · 22.1K | **🎉 100% LIFECYCLE ARCHITECTURE COMPLETE** (2026-07-04 · Tracks 22.1D through 22.1K delivered · Track 22.1K retired the sole `@app.on_event("shutdown")` handler into `SHUTDOWN_STEPS.shutdown` and introduced the phase-4 shutdown orchestrator plus permanent CI guardrails · 51 startup + 1 shutdown callables all live in `LIFECYCLE_STEPS` / `SHUTDOWN_STEPS` · on_startup = 0 · on_shutdown = 0 · migration progress live at `GET /api/admin/platform/status.migration_progress.lifecycle_complete` = **true** · `startup_migration_pct = shutdown_migration_pct = 100.00%` · CI enforces zero-legacy going forward via `test_no_legacy_(startup|shutdown)_decorators_anywhere_in_backend`) |
| TD-22.1h-D01 | `_start_safety_digest_cron` double-registered on `@app.on_event("startup")` in source (traced to at least Track 22.1F) — caused one wasted `asyncio.create_task(...)` per boot; singleton-lock prevented duplicate email dispatch | **D** — False Positive at ship time (singleton-lock masked the impact) but genuine code hygiene defect | Backend team | P3 | 22.1h | **CLOSED** (2026-07-04 · Track 22.1H removed the second decorator during the email-scheduler cutover · handler now fires exactly once per boot · verified by `test_no_duplicate_registrations`) |
| TD-22.1f-C01 | Platform Operations API foundation delivered — `GET /api/admin/platform/status` backed by `lib/platform_status.py` · admin-only (`require_admin_strict`) · read-only · zero-secret · lifecycle/bytecode/email-safety/CORS/route attestation | **C** — Architecture Debt (delivered) | Backend team | P2 | 22.1f | **CLOSED** (2026-07-04 · Track 22.1F · 15/15 lock assertions · 401 on unauth / bogus · 9 banned substrings verified absent from payload · AST-verified no `import resend` in `lib/platform_status.py`) |
| TD-22.1d-C01 | ~158 `include_router(...)` calls inline in server.py | **C** — Architecture Debt (deferred with plan) | Backend team | P2 | 22.1d | **OPEN — DEFERRED WITH PARITY GATE** (2026-07-04 · route-set parity gate available from Track 22.1 harness) |
| TD-22.1e-C01 | Auth helpers (`require_admin_dep`, `_actor_dep`, portal-token helpers, JWT/MFA helpers) inline in server.py | **C** — Architecture Debt (deferred with plan) | Backend team | P2 | 22.1e | **OPEN — DEFERRED WITH PARITY GATE** (2026-07-04 · dependency-chain parity gate + HTTP fixture regression per portal) |
| TD-22.2-C01 | `frontend/src/App.js` = 1,283 lines · 385 routes · 180 lazy imports · portal-token guards. Route extraction requires a full route-parity harness (route-path set · lazy-target set · guard mapping · fallback mapping · bundle-size delta · Playwright smoke). | **C** — Architecture Debt (deferred with plan) | Frontend team | P1 | 22.2 | **OPEN — DEFERRED WITH PARITY GATE** (2026-07-04 · full 6-gate spec in `TRACK_22_0_EXECUTIVE_SUMMARY.md`) |

## Detail

Full one-page reports for each debt item:

- `memory/TECH_DEBT_TD_20_6A_001_vocabulary_unauth.md`
- `memory/TECH_DEBT_TD_20_6A_002_vocabulary_hr_lanes.md`

## Rules for future entries

Every future entry must specify:

1. **Debt ID** — format `TD-<track>-NNN` (auto-numbered per track).
2. **Root cause** — what failed, why, when, which track introduced it.
3. **Impact** — production / preview / test-env-only.
4. **Risk** — probability × severity if left unfixed.
5. **Owner** — responsible team or subsystem.
6. **Proposed Track** — where it will be fixed.
7. **Priority** — P0 (blocker) / P1 (high) / P2 (medium) / P3 (low).
8. **Status** — OPEN / IN PROGRESS / FIXED / DEFERRED / WONTFIX.

## Certification rule

No certification report may contain language such as:

- "Pre-existing issue"
- "Known failure"
- "Ignored"
- "Left as-is"
- "Not addressed"
- "Outside scope"

...unless it ALSO includes the full classification above and a link
back to this register.

## Lock-test rule

Every future certification lock test must verify:

- No uncategorized failures.
- No uncategorized technical debt.
- Every discovered issue has: owner · priority · disposition · target
  track.

## Phase 1 · Final Completion — Debt IDs surfaced 2026-02-05

Every item classified under the Defect Constitution (fix-or-block-with-owner). Full detail: `PHASE_1_OPEN_ITEM_MATRIX.md`.

| ID | Title | Class | Owner | Priority | Target Track | Exit Criteria | Status |
|---|---|---|---|---|---|---|---|
| TD-P1-C-1 | App.js 1,283-line monolith · 385 routes · needs modularization into `frontend/src/app/*` | **C** — Engineering Debt | Next-session executor | P1 | Track 22.2 Phase B | Parity harness JSON-diff empty + Playwright per-portal green + bundle `after ≤ before` + 385 routes preserved | **CLOSED** (2026-02-05 · Track 22.2 Phase B · App.js: 1283 → 94 lines · 385 routes preserved · bundle −218 B · Playwright green · see `TRACK_22_2_*.md`) |
| TD-P1-C-2 | 110 `react-hooks/exhaustive-deps` ESLint warnings across frontend | **C** — Engineering Debt | Frontend hygiene track lead | P3 | Track 22.6 (proposed) | 0 ESLint warnings on `yarn build` | **OPEN · owned** — Mechanical auto-fix can introduce infinite re-render loops; must review each `useEffect` deps array intent per warning. |
| TD-P1-C-3 | Tailwind arbitrary-class ambiguity: `duration-[400ms]` | **C** — Engineering Debt | Frontend hygiene track lead | P4 | Track 22.6 | Replace with numeric duration or explicit CSS var | **OPEN · owned** — Cosmetic; requires locating usage + selecting replacement semantics. |
| TD-P1-C-4 | Starlette upstream `python_multipart` PendingDeprecation | **C** — Engineering Debt | Backend track lead | P3 | Track 22.4B (proposed) | 0 PendingDeprecationWarning on backend boot | **OPEN · owned** — External dependency; requires Starlette upstream version bump + full lock-envelope regression. |
| TD-P1-C-5 | App.js documentation-preserved comment blocks (lines 5, 87–93, 565) | **C** — Documentation-Preserved | Track 22.2 Phase B executor | P4 | Track 22.2 Phase B | Comments consolidated into per-feature module headers during route extraction | **OPEN · owned** — Immediate deletion would drop context needed by lock tests iter333/335/336 (scan `NewIncident.jsx`). |
| TD-P1-C-6 | `browserslist` caniuse data 7 months old (build warning) | **C** — DevOps Debt | DevOps | P4 | Any future frontend build | `npx update-browserslist-db@latest` in container image | **OPEN · owned** — Cosmetic build warning; zero functional impact. |


**Signed:** E1 · Track 20.6A · Elite Consistency · Zero-Drift · Six
Pillars.

---

## 2026-07-05 · ODS-001 Follow-ups

- **[P1] Google Gemini adapter is a scaffold.** `services/ai_gateway/adapters/google_adapter.py` returns fallback envelope. Wire real SDK when `GOOGLE_AI_API_KEY` is provisioned. Interface is complete; no schema/route change required.
- **[P1] Photo Vision (DR-ROI-001D).** OpenAI + Google vision paths are scaffolded (`vision()` on each adapter). Real wiring lands in DR-ROI-001D. `photo_vision` task type is registered in the router.
- **[P1] V1 daily_report → spine ingestor.** V1 has richer structured `production[]`/`constraints[]` rows than V2 today. Ingestor interface reserved (`ingest_dr_v1(...)` planned). Zero schema change required to add.
- **[P1] HR / Equipment / Safety / QA ingestors.** Each has canonical collections; adapters reserved.
- **[P2] Cross-project admin/executive rollups.** Snapshot aggregation over multiple `(project_id, date)` pairs. Task types `pm_brief` and `executive_brief` already routed through the gateway.
- **[P2] Timeline UI.** Schema derived directly from `operational_facts`; documented in `ODS_001_OPERATIONAL_TIMELINE_FOUNDATION.md`.
- **[P2] Legacy DR-V2 audit-log migration.** Pre-Phase-C entries live inside `dr_v2_ai_approvals.log[]` array. Post-Phase-C entries live in the new `dr_v2_ai_audit_entries` collection. If we promote out of preview, add a one-time backfill.
- **[P2] Sentry lazy-init (Track 22.7).** Unchanged.

---

## 2026-07-05 · DR-ROI-001D Follow-ups

- **[P1] Live vision e2e with real image bytes.** Interface + graceful failure proven; a full end-to-end call with an actual R2-fetched image + confidence ≥ 0.6 has not been exercised in this session. Recommended smoke: POST `/analyze` with `photo_base64` for a real photo once the OpenAI vision entitlement on EMERGENT_LLM_KEY is confirmed.
- **[P1] R2 fetch → base64 for background analysis.** Right now the analyze endpoint requires `photo_base64` in the request body. Add a helper that, given a `photo://` ref, fetches the object from R2 and passes bytes to the vision adapter — allows the frontend to just send `{ photo_id }`.
- **[P2] Orphan cleanup.** Deleting a photo doesn't cascade to `dr_v2_photo_intelligence`. Add a nightly cleanup that removes intel docs whose `photo_id` no longer resolves to a photo.
- **[P2] Photo-linked evidence trace in operational_narrative agent.** Agent prompt does not yet explicitly reference the new `photo_evidence_links[]` payload on production/delay/safety facts. Low-risk enhancement.

---

## 2026-02 · AI-CONFIG-001 Follow-ups

- **[P1] DR-UNIFY-003 collection renames.** `dr_v2_drafts` → `daily_reports_drafts` and related route aliases are
  queued and untouched by this track. AI-CONFIG-001 resolver is name-agnostic — it does not read these collections.
- **[P1] Background task queue for ODS ingestion.** With AI enabled at scale, per-report ingestion should move to
  a queue to keep POST latency flat. Interface reserved (`ingest_dr_v1_report` is already idempotent). Not a blocker
  for AI-CONFIG-001.
- **[P2] Per-tenant admin UI for `tenant_ai_capabilities`.** Today the collection is edited via Mongo. Ship a
  supervisor-console screen so ops can flip tenant flags without shell access. Non-blocking; env defaults cover the
  short term.
- **[P2] `GET /api/ai/gateway/status` tenant-scope variant.** Current endpoint reports deployment posture only.
  Add `GET /api/ai/gateway/status?tenant_id=…` (admin only) that also merges the tenant doc + resolves each module.
  Useful for support workflows.
- **[P3] Env consolidation.** `DR_V2_AI_ENABLED`, `DR_V2_PHOTO_VISION_ENABLED`, and the per-module `DR_*_ENABLED`
  legacy flags in `backend/.env` are workflow flags separate from the AI switchboard. Consider mapping them into
  `MODULE_ENV_MAP` in a follow-up so all AI gating flows through one resolver — for now they are documented in
  `AI_CONFIG_001_SECRET_CONTRACT.md` §3.5.

---

## 2026-02 · AI-ADMIN-001 Follow-ups

- **[P2] Live-provider probe.** `POST /api/admin/ai/providers/{p}/test` today reports
  readiness (flag on + key present). A follow-up should issue a bounded live probe
  behind an explicit flag with a cost/timeout budget so operators can verify a
  key actually works. Deliberately deferred to keep AI-ADMIN-001 zero-cost by default.
- **[P2] Tenant-admin scoped role.** Today only super-admins can flip tenant flags.
  When multi-tenant expands beyond MASCI, add a `require_tenant_admin` gate scoped
  to a single `tenant_id` so tenant owners can self-serve without super-admin access.
- **[P3] Audit index.** Add compound index on
  `tenant_ai_capability_audit.{tenant_id, timestamp}` when audit volume grows
  past ~1k entries per tenant. Not needed today (typical volume < 20/month/tenant).
- **[P3] Batch tenant update.** A safe `PATCH /api/admin/ai/tenants/bulk` could
  enable rolling-out a module to N tenants in one call. Explicit non-goal today
  to preserve per-tenant audit clarity — every mutation is one tenant, one row.

---

## 2026-02 · DR-CUTOVER-002 Follow-ups

- **[P2] PDF renderer inclusion.** `dr_v2_pdf.py` should render a "Daily Operational Summary" block
  before the signature block, conditional on `record.get("daily_operational_summary")`. Requires
  a golden-file PDF comparison test — kept out of this track to isolate risk.
- **[P2] Email template inclusion.** Extend the daily-report email body block to render the accepted
  summary when present. Strictly additive; won't affect existing deliveries.
- **[P2] Live-LLM polish path.** A future middleware wrapper around the deterministic composer output
  can hand the text to an LLM for a style pass — with a hard constraint that the LLM must NOT
  introduce any new fact (validated by cross-check against the composer's evidence_refs).
- **[P3] Photo Intelligence integration.** When enabled, could enrich the summary with per-photo
  observations. Currently the composer surfaces photo counts and captions only — no vision call.

---

## 2026-02 · DR-UNIFY-003 Follow-ups

- **[P1] DR-UNIFY-004 — Live migration + deployment cert.** Execute the migration `--live` against
  preview, verify, then repeat against production with Atlas snapshot. Byte-compare canonical vs.
  deprecated PDF variants. Move service reads (`dr_ai/cache.py`, `photo_intelligence/store.py`,
  `ods_spine/ingest.py`) onto `resolve_read_collection_name`.
- **[P2] DR-UNIFY-005 — Legacy cleanup.** After 30 days of clean production telemetry, drop the
  legacy `dr_v2_*` collections and rename the backend module filenames (`routes/dr_v2_*.py` →
  `routes/daily_report_*.py`). Sweep dead frontend files (`ExecutiveOperationalIntelligence.jsx`,
  `pages/daily-report-v2/**`, `lib/dailyReportV2*.js`) once no imports remain.
- **[P3] localStorage sweep.** Purge the harmless-but-dead `dr_v2_optin` key from any devices that
  still have it set (client-side no-op cleanup).
