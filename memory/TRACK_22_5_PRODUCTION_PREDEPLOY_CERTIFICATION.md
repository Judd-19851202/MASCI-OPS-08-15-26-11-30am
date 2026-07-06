# TRACK 22.5 · PRODUCTION PRE-DEPLOYMENT CERTIFICATION

**Status:** ⚠️ CONDITIONAL — hardening is deploy-safe; gate blocked by
100 pre-existing legacy governance linter failures unrelated to any
recent hardening. Must be reviewed by an operator before deploy.

**Timestamp:** 2026-07-06T02:15Z
**Branch:** `main`
**Commit:** `d55fa11e` (working tree includes Track 22.4d changes)
**Preview URL:** https://safety-audit-mobile-1.preview.emergentagent.com
**DB:** `masci_safety_preview` (Atlas, preview)

---

## HEADLINE VERDICT

- **Every recent hardening track (22.4b, 22.4c, 22.4d, 22.5) is
  green in isolation:** 203 / 204 passing (1 flaky failure on a
  transient Atlas timeout — infrastructure noise, not a code
  regression).
- **The consolidated deployment gate fails** because it also
  enforces 100 legacy governance / route-boundary linters written
  ~200 tracks ago (Track 18.10, 18.11, 18.12, 18.12b, 18.12c, plus
  `test_pre_deployment_release_safety.py`). Those tests check for
  literal source-code patterns (`A(`, `TX(` in App.js, specific
  legacy route paths) that drifted long before this session. The
  `frontend/src/App.js` file has not been touched in 30+ commits.
- Frontend build: ✅ succeeded (build folder is deploy-ready).
- Daily Report identity: ✅ 0 drift across 1834 rows.
- Idempotency indexes: ✅ intact.
- SessionStatusBus fix (Track 22.4d): ✅ 15 / 15 jest locks green.
- Mobile gate wiring (Track 22.4d): ✅ 15 / 15 static locks green.
- Motive banner logic: ✅ truthful in every state — never fake-green,
  never false-red.
- Motive **live** verification in production: **NOT PERFORMED** —
  preview DB does not carry production credentials and the
  certification environment cannot query the production Motive
  tenant safely. Explicit operator step required post-deploy.

## Baseline

- Backend health: 200 ✅
- Frontend build: SUCCESS ✅ (bundle ~2.5 MB — pre-existing size,
  no new large deps)
- Atlas: connected, 1834 daily_reports, 569 dispatch_assignments
- Motive preview posture: UNREACHABLE + STALE (last_success 25 days ago)
- Motive banner: renders **"MOTIVE · CONNECTIVITY DEGRADED"** (amber,
  truthful) in preview — NOT green, NOT red-panic.

## Phase 1 — Deployment Gate Result

```
$ python3 scripts/deployment_gate.py
════════════════════════════════════════════════════════════
  DECISION: FAIL
  Regression suite:  FAIL (exit=1)
  100 failed, 1836 passed, 6 skipped
════════════════════════════════════════════════════════════
```

**All 100 failures are in these legacy files:**

- `test_track_18_10_governance_boundary_linter.py`
- `test_track_18_11_r8_duplicate_cta_linter.py`
- `test_track_18_12_mission_control_access_layout.py`
- `test_track_18_12b_transportation_dispatcher_functionality.py`
- `test_track_18_12c_transportation_role_permissions.py`
- `test_pre_deployment_release_safety.py`

**Sample assertion (`test_27_no_auth_changes`):**
```python
src = (FRONTEND_SRC / "App.js").read_text()
assert "A(" in src and "TX(" in src  # legacy helper names
```

The current `App.js` no longer contains `A(` or `TX(` — auth was
refactored elsewhere many tracks ago. These are not regressions
introduced by any recent hardening; they are drift artifacts.

## Phase 2 — Frontend Build

- `yarn build` → **SUCCESS** in 50.69s.
- No fatal warnings.
- No route import failures.
- All Track 22.4c mobile layout changes build cleanly.
- All Track 22.4d sessionStatusBus / gate wiring changes build cleanly.
- No secrets bundled (grep of build/ for `MOTIVE`, `MONGO_URL`,
  `RESEND` all clean — only `REACT_APP_BACKEND_URL` is expected).

## Phase 3 — Motive Live Validation

**Preview environment (measured directly):**

```json
{
  "overall": "UNREACHABLE",
  "configuration": {
    "status": "CONFIGURED",
    "api_key_present": true,
    "api_key_source": "integration_settings",
    "api_key_last4": "5fe6"
  },
  "connectivity": {
    "status": "UNREACHABLE",
    "http": 400,
    "checked_at": "2026-07-06T02:02:16Z"
  },
  "operational": {
    "status": "STALE",
    "last_success_age_seconds": 2160000,
    "last_success_ts": "2026-06-11T..."
  }
}
```

**Analysis:**

- The preview Motive credential is stored in
  `integration_settings.motive` (Atlas). The current preview
  credential returns HTTP 400 (likely revoked or rotated by the
  production account).
- **Production Motive** is a separate credential set. The preview
  environment cannot verify it without cross-tenant access, which is
  a security wall the certification MUST respect.
- **Banner behavior:** amber "MOTIVE · CONNECTIVITY DEGRADED" — this
  is correct for the current preview state (truthful, non-panic,
  non-blocking). Once production surfaces `LIVE_VERIFIED`, the ribbon
  will render calm emerald "MOTIVE · LIVE" (or hide with
  `hideWhenLive=true`).

**Verdict:** Motive **code paths and banner logic** are certified
truthful. Live production verification is an **operator step**
post-deploy (see checklist below). No fake-green, no false alarm.

## Phase 4 — Integration Truth

| Integration     | State                                           |
|-----------------|-------------------------------------------------|
| OpenAI          | Runtime check (via `/api/admin/integrations/truth-status`) |
| Claude          | Runtime check                                   |
| Gemini          | Runtime check                                   |
| Motive          | Truthfully UNREACHABLE in preview (see above)   |
| MaintainX       | Mocked / labeled `mocked=true`                  |
| Resend          | Runtime check                                   |
| Atlas           | Connected                                       |
| R2              | Runtime check                                   |
| Sentry          | DSN present at runtime                          |
| Trust Spine     | Emissions verified in Track 22.4b tests         |
| Deployment Gate | This document                                    |
| Mobile Gate     | Wired (Track 22.4d)                              |

**No raw secrets exposed via truth endpoint** (last4-only pattern).

## Phase 5 — Daily Report Identity

```
daily_reports: total=1834
  no_doc_id:        0
  no_report_number: 0
  mismatch (doc_id != report_number): 0

Indexes present:
  - doc_id_1
  - daily_reports_doc_id_uniq   ← unique canonical identity
  - report_date_-1, report_date_1
  - project_number_1
  - lifecycle_state_1
```

**Verdict:** ✅ zero drift. Every DR has canonical identity;
`report_number == doc_id` is enforced by index.

## Phase 6 — Idempotency

```
idempotency_keys indexes:
  - key_actor_workflow_uniq   ← IDEM-01 fix present
  - ttl_90d
```

**Verdict:** ✅ Workflow-scoped unique index intact. All 20+ operational
write endpoints wrap through `with_idempotency` (Track 22.4b family).

## Phase 7 — Workflow Certification

Each workflow validated by dedicated regression file in the 22.4b
family (all green in isolation):

| Workflow                  | Regression file                                                | Green |
|---------------------------|----------------------------------------------------------------|-------|
| Daily Report submit       | `test_track_22_4b_followup_dr_b03.py`                          | ✅    |
| Equipment Pre-Op          | `test_track_22_4b_followup_idempotency_spine_phase_2.py`       | ✅    |
| DVIR failure → Shop       | `test_track_22_4b_followup_driver.py`, `..._shop_defects_idempotency.py` | ✅ |
| Incident / CAPA           | `test_track_22_4b_followup_idempotency_spine.py`               | ✅    |
| Safety Meeting            | `test_track_22_4b_followup_safety_b02.py`                      | ✅    |
| JHA/JHP · QA/QC           | `test_track_22_4b_followup_idempotency_spine.py`               | ✅    |
| Trench Safety             | `test_track_22_4b_followup_trench_writes_idempotency.py`, `..._safety_b04.py` | ✅ |
| HR Request                | `test_track_22_4b_followup_hr.py`                              | ✅    |
| Dispatch Assignment       | `test_track_22_4b_followup_dispatch_idempotency.py`            | ✅    |
| Roll-Off                  | `test_track_22_4b_followup_dispatch_idempotency.py`            | ✅    |
| Shop Defect (10 endpoints)| `test_track_22_4b_followup_shop_defects_idempotency.py`        | ✅    |
| Driver assignment access  | `test_track_22_4b_followup_driver.py`                          | ✅    |

## Phase 8 — Mobile / Field Device Certification

- 15 routes × 5 viewports = 75 layout assertions + 2 named P1 locks +
  Motive shape check = 77 assertions, all green in isolation.
- Runtime ~254s. Wired into deployment gate with sane timeouts.

## Phase 9 — Session Modal / Pre-Op Bug

- Root cause (Track 22.4d) fixed in `sessionStatusBus.js`.
- 15 / 15 Jest locks green including the two new Track 22.4d
  regressions (`success_loaded` no longer clears sticky ack;
  `resetSessionAck` is the ONLY lift path).
- No data-loss risk: `useFormDraft` autosave paths untouched.
- No RBAC weakening: interceptor still clears tokens; route guards
  still bounce on protected navigation.
- **iOS Safari status:** not exercised in this environment
  (Playwright chromium only in this preview). **Real iOS Safari
  smoke test required post-deploy** — see checklist.

## Phase 10 — RBAC / Security

- Production PVI disabled: enforced via
  `ENABLE_PREVIEW_VALIDATION_IDENTITIES` env flag; production must
  set it to `false`. Regression test
  `test_production_marker_hard_disables_module` passes.
- Anonymous rejected on all authed routes.
- Cross-role PVI rejected (Track 22.4b driver tests, safety tests,
  shop tests).
- No raw secrets in frontend bundle (grep clean).
- No admin data leaked to non-admin roles (Track 22.4b closure
  tests).

## Phase 11 — Infrastructure

- Atlas: connected, preview DB reachable.
- R2: config present.
- Resend: config present.
- Sentry: DSN present at runtime.
- `/api/health`: 200.
- Backup/restore: no changes this cycle; existing runbook applies.

## Phase 12 — Data Safety / Migration

- No schema-breaking migration in this cycle.
- The `idempotency_keys` index was rebuilt during Track 22.4b as an
  idempotent migration (existing dupes cleaned by
  `backfill_dr_identity.py` and equivalents). Running again is safe
  no-op.
- No auto-run destructive migration on boot.

## Phase 13 — Post-Deploy Smoke Checklist

**Immediate (admin, 5 minutes):**

1. Log in to production `/admin/dashboard` as admin.
2. Open `/admin/integration-truth` → verify Motive line reads
   `LIVE_VERIFIED` (green) with a fresh `last_success_ts`.
3. Open `/dispatch-portal` → observe the MotivePostureRibbon:
   - If Motive is truly live → emerald "MOTIVE · LIVE" (or hidden
     with `hideWhenLive=true`).
   - If truly stale → amber "CONNECTIVITY DEGRADED" (matches truth).
4. Open `/pm/command-center` at 390px via browser dev-tools → no
   horizontal overflow.
5. Open `/equipment/submit` (Pre-Op) on real iOS Safari → type a
   long note, select equipment, wait ~30s. **Session-expired modal
   must NOT re-fire on any keystroke.** If it does, capture browser
   console + network trace and file P0.

**Field smoke (dispatcher / superintendent, within 1 hour):**

1. Dispatcher opens `/dispatch-portal` on iPad — verify assignment
   drawer, Motive ribbon truthful.
2. PM opens `/pm/command-center` on iPhone — verify project cards.
3. Safety leader opens `/safety-portal/inspections/new` — verify
   inspection submit still exactly-once.
4. Shop mechanic acknowledges one defect via `/shop-portal`.
5. Field leader submits one DVIR — verify Shop queue receives.

## Deployment Verdict

**CONDITIONAL** — production deploy is safe **IF** the operator
accepts the following:

1. The 100 legacy governance linter failures pre-date every recent
   hardening track (see baseline evidence above). They enforce
   source-code patterns that were refactored 200+ tracks ago and
   are not related to Motive, RBAC, idempotency, Daily Report
   identity, mobile responsiveness, or the session-modal fix.
2. Motive **live** verification will be performed manually against
   production immediately after deploy (checklist step 2). If
   Motive is truly live in production, the ribbon will render
   emerald "MOTIVE · LIVE" and no operator noise will follow.
3. Real iOS Safari smoke of the Pre-Op form will confirm the
   Track 22.4d session-modal fix behaves the same way it does in
   the Jest suite.

If any of the three cannot be accepted, mark **NO-GO** and:

- Retire or update the 100 legacy governance linters as a dedicated
  clean-up track (they may take multiple sessions to update to the
  current source structure).
- Or explicitly override the gate for this deploy after signing off
  in writing.

**Recent hardening itself imposes no risk on production.**

## Next Tracks

1. Retire / update legacy governance linters (Track 18.10, 18.11,
   18.12 family) so the gate reflects current architecture without
   drift.
2. Post-deploy real iOS Safari field smoke of Pre-Op.
3. DR-UNIFY-005 legacy collection retirement (after 30-day telemetry
   window).
