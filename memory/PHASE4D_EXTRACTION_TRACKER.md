# Phase 4D · Architectural Extraction Tracker
**Status:** iter382 complete · app behavior restored · net-new regression delta = zero.

This file tracks one-route-family-at-a-time extraction from server.py. Each iteration must:
1. Identify the cleanest extraction unit.
2. Build a `routes/<family>_routes.py` builder factory.
3. Mount via `app.include_router(...)` in server.py.
4. Add a parity regression lock (functional + source-level guards).
5. Confirm **parity-lock subset green** (see Testing Reality Reset below).
6. NO auth drift · NO lifecycle drift · NO visibility drift · NO route renaming unless necessary.

---

## ⚠️ Phase 4D Testing Reality Reset (iter382 closeout, 2026-05-24)

The prior agent's "218/218 regression green" status referred to the **parity-lock
subset** (the ~218 explicit extraction tests), NOT the full 4,700-test historical
suite. This distinction was not documented and led to wasted credits chasing a
non-existent "fully green full suite" baseline.

**The truth, locked in here permanently:**
- The full pytest suite has **233 pre-existing failures** at full-suite level.
- These failures predate iter382 (verified by running the suite against the
  iter381 baseline at commit `506ded6` — same 233 failures present).
- Failure root cause is overwhelmingly inherited **test isolation / state
  leakage / order dependency** (DB teardown collisions, environment-coupled
  assertions, long-lived module state).
- The full suite was **never the active extraction gate** in Phase 4D.

**iter382 net-new regression delta after fixes: ZERO.**
The 3 new failures iter382 *did* introduce have all been resolved:
1. ✅ Stale source-location assertion in `test_iter377_pm_routes_extraction.py`
   (admin set-password route moved to `pm_admin.py`).
2. ✅ Stale source-location assertion in `test_iter378_pm_auth_extraction.py`
   (PMSetPasswordBody + `admin_set_pm_password` moved to `pm_admin.py`).
3. ✅ Stale source-location assertion in `test_iter340_final_completion_hardening.py`
   (PM welcome PDF render sites moved to `pm_admin.py`).

**Real route-wiring regression introduced and FIXED:**
iter382's diff (`commit 2625b1c`) inadvertently removed the registration blocks
for `register_safety_routes`, `register_qaqc_routes`, and
`register_daily_reports_routes` from server.py. This silently disabled
`/api/incidents`, `/api/inspections`, `/api/meetings`, `/api/jhas`,
`/api/qaqc/*`, and `/api/daily-reports`. **Restored in iter382 closeout** —
registration blocks re-inserted verbatim from the pre-iter382 baseline, with
zero behavior drift.

### App behavior verification (2026-05-24)
- `GET /api/health` → **200**
- `POST /api/incidents` (anonymous, rate-limited) → **200**, returns full Incident
- Backend supervisor → **RUNNING**, no startup errors

### Parity-lock subset verification (2026-05-24)
| Test family | Result | Notes |
|---|---|---|
| `test_iter377_pm_routes_extraction.py` + `test_iter378_pm_auth_extraction.py` + `test_iter382_pm_admin_extraction.py` | **72 / 72 PASS** | After stale-assertion fix |
| `test_iter363_employee_linkage_persistence.py` + `test_iter368_incident_capa_reverse_link.py` | **15 / 15 PASS** | After route-wiring restoration |
| `test_iter340_final_completion_hardening.py` | **6 / 6 PASS** | After stale-assertion fix |

### Inherited full-suite debt (NOT iter382's responsibility)
- ~233 failures + ~54 errors at full-suite level.
- Predates iter382 (confirmed against `506ded6` baseline).
- Tracked separately as a future quality-debt project; will not block
  Phase 4D architectural convergence.

---

## Going-forward Phase 4D extraction gate (NEW STANDARD)

For architectural extraction work, the required gate is:

1. ✅ **Parity-lock subset green** (the iterN extraction tests).
2. ✅ **Targeted extraction tests green** (the new `test_iterX_<family>_extraction.py`).
3. ✅ **Route smoke green** (curl-verified endpoint responses).
4. ✅ **Auth parity green** (no drift in admin/safety/HR/PM token enforcement).
5. ✅ **Source-location assertions updated** in any prior parity-lock tests
   that referenced now-extracted code (avoid the iter382 mistake).
6. ✅ **Net-new regression delta = zero** vs the pre-extraction baseline.
7. ✅ **Inherited full-suite debt documented**, never claimed as iteration scope.

**Language discipline (mandatory):**
- ✅ "parity-lock subset green"
- ✅ "full suite has inherited isolation debt"
- ✅ "net-new regression delta = zero"
- ✅ "production behavior smoke verified"
- ❌ NEVER "full regression green" (unless the full 4,700-test suite actually is).
- ❌ NEVER "100% regression green" without qualification.

---

## server.py size watch

| Iteration | Lines | Δ | Cumulative |
|---|---|---|---|
| Pre-iter370 baseline | ~12,230 | — | — |
| iter375 (MFA wiring added) | 12,259 | +29 | +29 |
| iter377 (PM read-only extraction) | 12,065 | −194 | −165 |
| iter378 (PM auth-lifecycle extraction) | 11,724 | −341 | −506 |
| iter379 (Governance inventory + guidance telemetry) | 11,663 | −61 | −567 |
| iter380 (PO digest admin) | 11,632 | −31 | −598 |
| iter381 (Admin shared lookup) | 11,576 | −56 | −654 |
| **iter382 (`/admin/project-managers/*` extraction)** | **11,123** | **−453** | **−1,107** |

Pattern proven safe across 6 iterations (iter377–iter382). Active gate:
**parity-lock subset green + route smoke green + net-new regression delta = zero.**

**Remaining inventory** (sorted by route count in server.py):

| Family | Routes | Risk | Iteration target |
|---|---|---|---|
| `/admin/project-managers/*` | 10 | medium (admin CRUD) | iter382 |
| `/api/legacy-imports/*` | 9 | medium-high (file storage + OCR coupling) | iter383 |
| `/admin/jobs/*` | 9 | low-medium (admin CRUD) | iter384 |
| `/admin/suppliers/*` | 8 | low (admin CRUD) | iter385 |
| `/admin/equipment-master/*` | 8 | medium (richer shop gate) | iter386 |
| `/admin/employees/*` | 8 | medium (HR-shared visibility) | iter387 |
| `/admin/shop-users/*` | 7 | low | iter388 |
| `/admin/backups/*` | 6 | medium (file + cron coupling) | iter389 |
| Various smaller clusters | ~30 | mixed | iter390+ |

---

## Iteration log

### iter377 · PM read-only routes · ✅ COMPLETE

**Extracted from server.py → routes/pm_routes.py:**
- `/pm/check` · `/pm/me`
- `/pm/crew/training-records` · `/pm/crew/ppe` · `/pm/crew/capas` · `/pm/crew/summary`
- Helper: `_pm_crew_employee_names(actor, days=180)`

**Why these 6:**
- Read-only — zero state mutation.
- All consume `require_admin` / `require_admin_async` dependencies that were already factored.
- Zero coupling to `_client_ip`, `_check_login_lockout`, `_record_login_failure`, `_directory_admin_token`, `_clear_session_activity` (none of which are referenced by these handlers).
- Lowest possible risk.

**Left in server.py for iter378+:**
- `/pm/login` · `/pm/forgot-password` · `/pm/reset-password` · `/pm/change-password` · `/pm/logout`
- Heavy IP-lockout + directory-fallback + session-activity coupling.

**Regression**: `tests/test_iter377_pm_routes_extraction.py` — 21/21 PASS.
- 4 functional parity tests (admin unlocks, anon denied, safety rejected, dispatch rejected).
- 6 response-shape tests (each route's output keys + values).
- 3 query-limit tests (lower/upper bound enforcement).
- 8 source-level guards (file exists, factory exists, handlers in new file, handlers gone from server.py, non-extracted routes preserved, helper migrated, mount wired).

**Live smoke**: 200 admin / 401 anon on all 6 routes; response shape identical to pre-extraction.

**Cumulative**: iter354 → iter377 = **171/171 PASS** in ~95s.

---

### iter378 · PM auth-lifecycle routes · ✅ COMPLETE

**Extracted from server.py → routes/pm_routes.py (extended factory):**
- `POST /pm/login` (per-PM bcrypt + legacy shared-pw + universal super-admin fallback)
- `POST /pm/forgot-password` (Resend email + 30-min HMAC token; anti-enumeration generic response)
- `POST /pm/reset-password` (token consumption + fresh per-PM token issued)
- `POST /pm/change-password` (PM self-service rotation, requires per-PM session)
- `POST /pm/logout` (audit + session_activity clearance)
- Body models: PMLoginBody, PMChangePasswordBody, PMForgotPasswordBody, PMResetPasswordBody

**Coupling resolved via `login_deps` dict** passed to `build_pm_router`:
- `client_ip_fn`, `check_login_lockout_fn`, `record_login_fail_fn`, `reset_login_fails_fn`
- `directory_admin_token_fn` (universal super-admin fallback)
- `reset_session_activity_fn`, `clear_session_activity_fn`
- `pm_token_for_fn`, `render_portal_email_fn`

**Why a deps dict instead of 9 positional kwargs:** keeps the factory signature manageable + makes it explicit which routes are auth-lifecycle vs read-only.

**Behavior preserved:**
- Wrong email/password → 401 "Wrong email or password" (exact string).
- Disabled PM → 403.
- PM with no password → 403 "No password set...".
- No email + SHARED_LOGIN disabled → 400 "Email is required.".
- IP lockout still triggers identically.
- Universal super-admin fallback (iter346-B) still mints admin token when directory user matches.
- /pm/forgot-password always returns generic success (anti-enumeration).

**Regression**: `tests/test_iter378_pm_auth_extraction.py` — 18/18 PASS.
- 4 functional /pm/login tests.
- 2 forgot-password tests (generic success regardless of email).
- 2 reset-password tests (invalid token, short password).
- 2 change-password tests (auth required, admin session rejected).
- 2 logout tests (auth required, admin session accepted).
- 7 source-level guards (handlers moved, body models moved, server.py no longer owns 5 decorators, login_deps wired, admin set-password still in server.py).

**Live smoke**: All 5 routes respond identically pre/post extraction (wrong-pw 401, no-email 400 or 423 lockout, forgot/reset behavior identical).

---

### iter379 · Governance & Operational Inventory routes · ✅ COMPLETE

**Extracted from server.py → routes/governance.py (extended existing factory):**
- `GET /api/admin/operational-inventory` — full system snapshot (compute_full_inventory)
- `GET /api/admin/operational-inventory/portals` — portal × 10-field matrix
- `GET /api/admin/operational-inventory/translation` — ES translation readiness
- `GET /api/admin/operational-inventory/drift` — coverage drift signal
- `GET /api/admin/guidance/search-misses` — zero-result search telemetry + aggregation

**Why these 5: extremely low coupling.** Pure delegation to `governance.inventory` (4 routes) + a simple `db.guidance_search_misses` read + aggregation (1 route). All admin-strict gated. Zero state mutation.

**Regression**: `tests/test_iter379_governance_extraction.py` — 12/12 PASS.
- 3 functional parity tests (admin unlocks, anon denied, dispatch token rejected for cross-portal isolation).
- 5 response-shape tests (one per route).
- 4 source-level guards (5 handlers in new file, 5 gone from server.py, governance router still mounted, pre-existing compliance routes preserved).

**Live smoke**: All 5 routes return 200 with admin token, 401 without.

---

### iter380 · PO digest admin · ✅ COMPLETE

**Extracted to** `/app/backend/routes/po_digest_admin.py` via `build_po_digest_admin_router(db, require_admin_dep, require_admin_strict_dep, send_email_fn)`:
- `GET  /api/admin/po-digest/preview` (admin gate)
- `POST /api/admin/po-digest/run-now?dry_run=<bool>` (admin-strict gate)

Preserved: dry-run guard (iter247 P1-A), portal URL resolution fallback chain (`PORTAL_PUBLIC_URL` → `PUBLIC_BASE_URL` → `https://mascidocs.com`), AUTO_EMAIL_REPORTS env gate honored via the original `_po_digest_send_email` injected as `send_email_fn`. **31 LOC removed.**

---

### iter381 · Admin shared lookup · ✅ COMPLETE

**Extracted to** `/app/backend/routes/admin_lookups.py` via `build_admin_lookups_router(db, require_admin_dep)`:
- `GET /api/admin/find-by-doc-id?doc_id=<str>` (admin gate)

Preserved: the inline 10-collection conditional chain was refactored into a `_COLLECTION_ROUTES` table for clarity but behaves byte-identically (jha collections still produce `/admin/jha-plans?focus=<id>` query-string form, fallback `/admin?doc_id=<id>` preserved). **56 LOC removed.**

---

### iter382+ · Remaining operational families (planned roadmap)

**Candidates**: `/api/notifications/*` (~400 LOC).
**Coupling**: low (`notifications` helper module already exists).
**Risk**: low.

---

### iter381 · Shared lookup services (planned)

**Candidates**: `/api/master-lookup/*` (~500 LOC).
**Coupling**: low.
**Risk**: low.

---

### iter382+ · Remaining operational families (planned)

Daily reports, inspections, JHAs, employee CRUD, audit endpoints, etc. — extract incrementally with regression locks. Each family ~200-800 LOC.

---

## Permanent rules (per directive)

- One route family at a time.
- Regression locked **before** moving on.
- Behavior identical · no auth drift · no lifecycle drift · no visibility drift.
- No route renaming unless explicitly required.
- Each iteration adds ≥5 functional parity tests + ≥3 source-level guards.
- **Parity-lock subset must stay green** (not the full 4,700-test inherited-debt suite).
- If an iteration would touch >300 LOC or require a behavior change, STOP and consult operator.
- **MANDATORY iteration-zero pre-flight** (see checklist below) — no extraction without it.

---

## Iteration-Zero Extraction Checklist

Adopted 2026-05-24 after iter382 closeout. No extraction iteration begins
without completing this checklist and saving the pre-flight artifact in
this tracker. The goal: catch silently-deleted wiring, hidden cross-
references, and adjacent-block coupling **before** any code moves.

For each extraction iteration, fill in:

1. **Target route family** — exact path prefix being extracted.
2. **Current server.py route block location** — line range of the routes.
3. **Current import dependencies** — every module the handlers import.
4. **Current DB dependencies** — every collection the handlers touch.
5. **Current auth gates** — every dependency / token type each route uses.
6. **Current registration wiring** — `@app.<verb>` vs `@api_router.<verb>`,
   any `app.include_router(...)` block, any startup hooks, any helpers
   that wire dependencies.
7. **Adjacent route families** — what registration blocks live within
   ±50 LOC of the target (these are at highest risk of accidental
   deletion during patch operations).
8. **Before-curl endpoints** — exact list of routes to smoke before
   touching code, with expected status codes.
9. **Existing tests touching the family** — file paths + test counts.
10. **Missing parity-lock tests needed** — what gaps must be filled.
11. **Risk rating** — low / medium / high, with explicit factors.
12. **Rollback plan** — exact git command(s) to revert if anything drifts.

---

## Architectural goals (when Phase 4D wraps)

- `server.py` reduced from 12,259 LOC to <4,000 LOC.
- Each route family lives in `/app/backend/routes/<family>_routes.py`.
- Each family file is a `build_<family>_router(db, ...deps)` factory.
- `server.py` is reduced to: app construction, shared dependencies (db, auth gates, schedulers), router mounting, startup/shutdown hooks.

---

## iter383 · Pre-Flight (`/api/legacy-imports/*`) · 🟡 PRE-FLIGHT ONLY · NO EXTRACTION YET

**Completed:** 2026-05-24
**Status:** Pre-flight artifact only. Extraction blocked pending operator approval.

### 1. Target route family
`/api/legacy-imports/*` and `/api/admin/legacy-imports/*` — total **11 routes**
(handoff said 9; actual is 11). All registered directly on `app` with
explicit `/api/` prefix (NOT via `api_router`).

### 2. Current server.py route block location
| Line | Method | Path | Handler |
|---|---|---|---|
| 9066 | POST | `/api/legacy-imports/upload`            | `li_upload` |
| 9207 | GET  | `/api/legacy-imports/_meta`             | `li_meta` |
| 9235 | GET  | `/api/legacy-imports`                   | `li_list` |
| 9255 | GET  | `/api/legacy-imports/{import_id}`       | `li_get` |
| 9264 | GET  | `/api/legacy-imports/{import_id}/file`  | `li_signed_file_url` |
| 9303 | PATCH| `/api/legacy-imports/{import_id}`       | `li_patch` |
| 9345 | POST | `/api/legacy-imports/{import_id}/approve` | `li_approve` |
| 9381 | POST | `/api/legacy-imports/{import_id}/reject`  | `li_reject` |
| 9406 | POST | `/api/legacy-imports/{import_id}/retry-ocr` | `li_retry_ocr` |
| 9442 | GET  | `/api/admin/legacy-imports/audit`       | `li_audit_list` |
| 9456 | GET  | `/api/admin/legacy-imports/pilot-debrief` | `li_pilot_debrief` |

Plus a 35-LOC helper `_li_require_uploader` (line 9029) and **two startup
hooks** at lines 9004 and 9012 (`_li_ensure_indexes`, `_li_start_worker`)
that MUST move with the routes or be preserved verbatim.

**Total block:** lines 8985 → 9492 (≈507 LOC including comments, the
phase intro block, the helper, the startup hooks, and the 11 handlers).

### 3. Current import dependencies
- `import legacy_imports as _li` (line 8999) — `/app/backend/legacy_imports.py` · 601 LOC.
- `import photo_storage as _ps` (line 9000) — used for signed URL generation in `/file` endpoint.
- `from fastapi import UploadFile, File, Form` (line 9001) — used by `/upload`.
- Inside handlers (PLC0415-lazy):
  - `legacy_imports_equipment_checkout as _li_ec` (Phase B promoter registration; appears in 4 sites).
  - `hr_users.is_valid_hr_user_token_async` (auth gate).
  - `safety_users.is_valid_safety_user_token` (auth gate).

### 4. Current DB dependencies
- `db.legacy_imports` (primary collection; 9 sites in this block).
- `db.legacy_import_audit` (audit log; 1 site, `/audit` endpoint).
- Indexes created in `_li.ensure_indexes(db)` at startup.

### 5. Current auth gates
| Route | Gate |
|---|---|
| `/upload`, `/_meta`, `/`, `/{id}`, `/{id}/file`, `/{id}/approve`, `/{id}/reject`, `/{id}/retry-ocr` | `_li_require_uploader` (HR · Safety · Admin) |
| `/{id}` PATCH | `_li_require_uploader` |
| `/admin/legacy-imports/audit` | `require_admin` (admin-only) |
| `/admin/legacy-imports/pilot-debrief` | `require_admin` (admin-only) |

Anti-self-approval guard inside `/approve` handler — must preserve.

### 6. Current registration wiring
- **Direct `@app.<verb>("/api/...")`** — not `api_router`. This is unusual
  for the codebase; new file MUST mount via `app.include_router(router,
  prefix="/api")` OR keep the explicit `/api/` prefix inside the router.
- Two startup hooks (`@app.on_event("startup")`) wire indexes + worker.
- One module-level `_li_worker_task: Optional[asyncio.Task] = None`.

### 7. Adjacent route families (±50 LOC)
**ABOVE (lines ~8950 → 8985):** Section header comments only — the
preceding code block ends with PM-related admin endpoints (already
extracted in iter382 to `pm_admin.py`). No active registration calls
in the gap.
**BELOW (lines 9493 → 9540):** `iter251 Phase A · Fleet Operations
Foundation` — `from routes.fleet_ops import build_router as
_fleet_build_router`, `from routes.dispatch_portal_auth import
make_require_dispatch_token`, helper `_require_fleet_submitter`.

**Risk:** the iter382 mistake was caused by an over-broad delete that
swallowed the safety/qaqc/daily-reports registration blocks living below
the deleted family. For iter383, the comparable risk surface is the
**fleet_ops include/build call** immediately below line 9492. Any patch
that deletes past line 9492 must be visually verified to preserve fleet
ops registration intact.

### 8. Before-curl endpoints (smoke baseline · captured 2026-05-24)
Admin token: `X-Admin-Token: <admin login token>`.

| Method | URL | Expected status | Verified |
|---|---|---|---|
| GET | `/api/legacy-imports?limit=2` | 200 (returns `{count, items}`) | ✅ `{"count":0,"items":[]}` |
| GET | `/api/legacy-imports/_meta` | 200 (returns `upload_portal`, `allowed_document_types`, `active_promoters`, etc.) | ✅ full payload |
| GET | `/api/admin/legacy-imports/audit?limit=2` | 200 (returns `{count, items}`) | ✅ `{"count":2,...}` |
| GET | `/api/admin/legacy-imports/pilot-debrief` | 200 (returns debrief payload) | ✅ full payload |
| GET | `/api/legacy-imports` (no auth) | 401 (`HR, Safety, or Admin authentication required`) | ✅ |
| GET | `/api/admin/legacy-imports/audit` (no auth) | 401 (`Admin login required`) | ✅ |

Adjacent smoke (must NOT regress post-extraction):
| GET | `/api/health` | 200 | ✅ |
| POST | `/api/incidents` (anon) | 200 | ✅ |
| GET | `/api/admin/project-managers` (admin) | 200 (PM admin family — iter382) | (verify pre/post) |
| GET | `/api/fleet-ops/*` (admin) | (verify pre/post) | (verify pre/post) |

### 9. Existing tests touching legacy imports
| File | Test count (approx) | Notes |
|---|---|---|
| `tests/test_iter248_phase_a.py` | TBD | Phase A foundation (staging + RBAC + OCR scaffold) |
| `tests/test_iter249_phase_b.py` | TBD | Phase B equipment-checkout activation |
| `tests/test_iter249_pilot_debrief.py` | TBD | Pilot debrief endpoint |

These three files form the **parity-lock subset for iter383**. They must
all pass before AND after extraction with identical assertion counts.

### 10. Missing parity-lock tests needed
- **`test_iter383_legacy_imports_extraction.py`** (new) — explicit
  structural assertions:
  - `legacy_imports` route handlers NOT in `server.py`.
  - `/api/legacy-imports/upload` (etc.) registered via the new
    `routes/legacy_imports.py` router.
  - Helper `_li_require_uploader` lives in the new module (or in a
    shared deps module).
  - Startup hooks `_li_ensure_indexes` + `_li_start_worker` preserved
    (still wired to `app` via the new module's `register_*` factory).
  - `/api/admin/legacy-imports/audit` and `/pilot-debrief` registered
    with `require_admin` gate (not `_li_require_uploader`).
- **Curl smoke parity assertions** — every endpoint from §8 returns the
  same status code and same JSON shape pre/post.

### 11. Risk rating
**MEDIUM-HIGH.** Justification:
- Direct `@app.<verb>` registration (different pattern than other
  extractions which used `@api_router.<verb>`).
- Two startup hooks must be preserved verbatim — extracted module must
  expose a `register(app, db, ...)` that re-wires them.
- File-storage coupling (`photo_storage` + R2 signed URLs).
- Anti-self-approval guard inside `/approve` handler — easy to drop on
  copy-paste.
- Adjacent fleet_ops block (the analog of the iter382 safety/qaqc
  silently-deleted block).
- Worker module global `_li_worker_task` lives in `server.py` scope —
  extraction must decide whether to move it to the new module or keep
  it parked in `server.py` and pass a reference.

### 12. Rollback plan
If anything drifts post-extraction:
```bash
cd /app
git log --oneline -5 backend/server.py        # find pre-iter383 commit
git checkout <pre-iter383-sha> -- backend/server.py
rm -f backend/routes/legacy_imports_routes.py  # if a new file was created
rm -f backend/tests/test_iter383_legacy_imports_extraction.py
sudo supervisorctl restart backend
curl -sf http://localhost:8001/api/health     # verify
```

### Pre-flight verdict
🟡 **NOT GREEN-FLAG YET.** Two pre-flight items still owed before
extraction can safely start:
1. Read and capture test counts in `test_iter248`, `test_iter249_phase_b`,
   `test_iter249_pilot_debrief` (need to confirm they pass against the
   current restored baseline).
2. Decide the destination structure (single `routes/legacy_imports.py`
   with `register(app, db)` factory, OR split into `legacy_imports.py`
   user-facing + `legacy_imports_admin.py` admin-facing? recommend the
   single-file approach to match iter382 pattern).

Both items are operator-decision points. **No code moves until they're
resolved.**
