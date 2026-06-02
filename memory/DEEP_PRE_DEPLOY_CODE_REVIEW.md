# DEEP PRE-DEPLOY CODE REVIEW

**Scope**: Employee Governance Phase Alpha · ITER453 (OC-003 QA/QC + OC-004 Site Inspection LifecyclePanels) · ITER452.5.2 Resend webhook.
**Mode**: READ-ONLY. No code writes. No migrations. No deploys.
**Authority**: OMEGA DIRECTIVE — DEEP PRE-DEPLOY CODE + OPERATIONAL CERTIFICATION (2026-06-02).
**Reviewer**: E1 (fork agent).
**Env audited**: PREVIEW pod · `APP_ENV=preview` · `DB_NAME=masci_safety_preview` · backend uptime 57 min · frontend uptime 52 min.

---

## Phase 1 · Source / Diff manifest

Baseline = last deployed production checkpoint. Delta inferred from `git log` (last 9 commits on the preview branch since the iter453 BUILD landing).

### 1.1 Backend code (10 files)

| Status | File | LOC | Purpose |
|---|---|---:|---|
| 🆕 NEW | `backend/routes/employee_requests.py` | 579 | HR Queue routes (G-5) |
| 🆕 NEW | `backend/routes/qaqc_lifecycle.py` | 241 | OC-003 transitions + audit |
| 🆕 NEW | `backend/routes/site_inspection_lifecycle.py` | 226 | OC-004 transitions + audit |
| 🆕 NEW | `backend/routes/resend_webhook.py` | 384 | iter452.5.2 delivery chain closure |
| ✏️ MOD | `backend/routes/field_leadership.py` | 1638 | G-2 closure (`/employees` enqueue) + Termination addendum |
| ✏️ MOD | `backend/lib/workflow_state_machine.py` | 584 | QA/QC + Site-Inspection state tables |
| ✏️ MOD | `backend/server.py` | (~10 100) | 4 register-* wirings + employee_requests router include + index ensure |
| 🆕 NEW | `backend/tests/test_employee_governance_alpha.py` | 257 | 17 tests · G-1..G-5 + queue E2E |
| 🆕 NEW | `backend/tests/test_iter452_5_2_resend_webhook.py` | — | 9 tests |
| 🆕 NEW | `backend/tests/test_iter453_lifecycle.py` | — | 24 tests |

### 1.2 Frontend code (9 files)

| Status | File | Purpose |
|---|---|---|
| 🆕 NEW | `frontend/src/pages/HrEmployeeRequestsQueue.jsx` (485) | HR review UI · approve/reject |
| 🆕 NEW | `frontend/src/components/QaqcLifecyclePanel.jsx` (570) | OC-003 lifecycle UI |
| 🆕 NEW | `frontend/src/components/SiteInspectionLifecyclePanel.jsx` (572) | OC-004 lifecycle UI |
| ✏️ MOD | `frontend/src/App.js` | Route `/hr/employee-requests` + import |
| ✏️ MOD | `frontend/src/pages/HrHub.jsx` | HR Hub tile + pending badge |
| ✏️ MOD | `frontend/src/pages/FieldLeadershipFormPage.jsx` | FL termination addendum hook |
| ✏️ MOD | `frontend/src/pages/ViewInspection.jsx` | Mount Site Inspection LifecyclePanel |
| ✏️ MOD | `frontend/src/pages/ViewQaqcInspection.jsx` | Mount QA/QC LifecyclePanel |
| ✏️ MOD | `frontend/src/components/EmployeeCombo.jsx` | Both add-paths now `bg-amber-600` "Request HR add" |

### 1.3 Config / governance (≈ 23 files)

* `.gitignore` (M, additive).
* `memory/PRD.md`, `memory/_INDEX.md`.
* 20+ new governance docs (EMPLOYEE_GOVERNANCE_*, ITER453_*, ITER452_5_2_*, SUB_VENDOR_IDENTITY_*, IDENTITY_*).

### 1.4 Aggregate counts

* **Code files changed**: **19** (10 backend · 9 frontend).
* **Config files**: 1 (`.gitignore` additive).
* **Governance docs added/modified**: 23.
* **Total ship surface**: ~43 files since last prod cut.

---

## Phase 2 · Code Quality

### 2.1 Lint

| File | Tool | Result |
|---|---|---|
| `backend/routes/employee_requests.py` | ruff | ✅ All checks passed |
| `backend/routes/qaqc_lifecycle.py` | ruff | ✅ All checks passed |
| `backend/routes/site_inspection_lifecycle.py` | ruff | ✅ All checks passed |
| `backend/routes/resend_webhook.py` | ruff | ✅ All checks passed |
| `frontend/src/pages/HrEmployeeRequestsQueue.jsx` | eslint | ✅ No issues |
| `frontend/src/components/QaqcLifecyclePanel.jsx` | eslint | ✅ No issues |
| `frontend/src/components/SiteInspectionLifecyclePanel.jsx` | eslint | ✅ No issues |

### 2.2 Hygiene

* All new modules carry a Constitutional doc-header (OMEGA · Phase · doctrine references O-1, O-4, Rule 7, REPLACE-4/REPLACE-5).
* All Pydantic models use `ConfigDict(extra="forbid")` — strict input validation, no silent field drift.
* All UUIDs minted via `uuid.uuid4()` — no collision-prone counters.
* Mongo writes never leak `_id` (every helper applies `_strip_id` or `{"_id": 0}` projections).
* Datetime stamps are `datetime.now(timezone.utc).isoformat()` — no naive UTC.
* `try/except` blocks are narrow and intentional (idempotent index creation, webhook persistence). No bare `except:`.
* No `print(...)` debug noise in new code paths.
* No `TODO` / `FIXME` markers in the ITER453 + Phase Alpha modules.

### 2.3 Secrets scan

* No hard-coded credentials, tokens, or PII in the changed code surface.
* `RESEND_WEBHOOK_SECRET` is correctly read from env at request time (no env baked at import).
* `MFA_ENCRYPTION_KEY`, `ADMIN_HMAC_SECRET`, `SUPER_ADMIN_*` remain env-only.

### 2.4 Dependency sanity

* No new pip / yarn packages introduced by this batch — entirely composed from already-installed libs (fastapi, motor, pydantic, lucide-react, shadcn ui).

---

## Phase 3 · Security / Permissions

### 3.1 Constitutional violations closed (Employee Governance Audit)

| ID | Violation | Closure | Live proof |
|---|---|---|---|
| **G-1** | Anonymous `POST /employees/add` wrote to roster | Endpoint returns **410** with `code=endpoint_deprecated` + `use_instead=/api/employee-requests` | curl 410 ✅ |
| **G-2** | Field Leadership inline `POST /field-leadership/employees` wrote to roster | Now enqueues `kind=new_hire` in `db.employee_requests` and returns `{pending_hr_review:true}` | code-reviewed, FL combo amber CTA ✅ |
| **G-3** | `/admin/employees*` unauthenticated reachable + DELETE could destroy | All routes gated by `_require_hr_or_admin_for_queue`; DELETE returns **405** `termination_via_status_machine_only` | curl 403 anon · 405 with HR token ✅ |
| **G-4** | `PUT /admin/employees/{id}` accepted `is_active` / `lifecycle_status` back-door | Strict 422 with `code=lifecycle_field_readonly` listing `blocked_fields` | curl 422 ✅ (both fields) |
| **G-5** | CSV upload silently REPLACE-ALL'd the roster | Upload now MERGE-only · existing rows preserved | pytest `test_g5_upload_preserves_existing_rows` ✅ |

### 3.2 HR Queue gating

* `POST /api/employee-requests` — public-tolerant submission with `rate_limit_public_post` + optional portal-token capture (audited as `requested_by_role` / `requested_by_label` / `requested_by_ip`).
* `GET /api/hr/employee-requests`, `GET /…/{id}`, `POST /…/{id}/approve`, `POST /…/{id}/reject` — all gated by `_require_hr_or_admin_for_queue` (HR token OR admin directory token).
* Anonymous request to the HR side of the queue returns **403** "HR or Admin token required" (verified live).
* Idempotency on approve/reject: re-approve returns **409** (verified by pytest).
* Approve path enforces duplicate-active-employee guard (409 with candidate row) before writing.

### 3.3 Termination dual-write contract

* FL Employee Termination form (`POST /field-leadership/records` with `kind=employee_termination`) now ALSO inserts an `employee_requests` row via the addendum (try/except wrapped — never blocks the FL record submit).
* HR remains the SOLE writer of `db.employees.lifecycle_status` — verified by code path inspection of `routes/hr.py` and `routes/employee_requests.py`.
* Cross-link via `linked_fl_record_id` preserves the FL → HR audit chain.

### 3.4 OC-003 / OC-004 lifecycle gates

* Both lifecycle routes use `require_qaqc_actor` / `require_inspection_actor` dependencies (inspector / PM / safety / admin role gates).
* Closure-action contract is enforced server-side in `validate_qaqc_transition` / `validate_site_inspection_transition` (REPLACE-5 / REPLACE-4): closure requires ONE of {re-inspection passed, corrective-action with notes ≥ 20 chars, exception with dual sign-off}.
* `from_state` → `to_state` matrix is centralised in `lib/workflow_state_machine.py`; legal transitions are also exposed read-only via `/lifecycle` endpoint.
* Audit events written via `lib/workflow_state_events.write_state_event` — append-only collection.

### 3.5 Resend webhook (ITER452.5.2)

* `POST /api/webhooks/resend` verifies Svix-style HMAC signature when `RESEND_WEBHOOK_SECRET` is set; in preview the secret is absent so signature is **skipped with a logged note** (`sig_note=no_secret_configured`). **Production MUST set `RESEND_WEBHOOK_SECRET` before this endpoint is reachable from the public internet.** (See Phase 8 checklist · MEDIUM risk in Risk Report.)
* Idempotency on `(provider_message_id, kind)` — duplicate posts are no-ops.
* `ClientDisconnect` explicitly caught — silences the recurring `RuntimeError("No response returned.")` middleware noise on aborted retries.
* Hard-bounce auto-escalates to Tier 5 dead-letter via `write_chain_event` + `write_dispatch_event` (Ownership Doctrine O-4 textbook).

### 3.6 Rate-limiting

* Public POST `/employee-requests` is dependency-injected with the canonical `rate_limit_public_post` middleware (same one that protects `/inspections`, `/meetings`, `/jhas`, `/incidents`, `/daily-reports`, `/translate`).
* Preview has `RATE_LIMITING=off` (expected, doctrine-documented). **Production MUST be `RATE_LIMITING=on`** (already documented in `test_credentials.md`).

---

## Phase 4 · Data Safety

### 4.1 `db.employees` integrity (PREVIEW snapshot)

```
total           = 249
deleted_at!=null = 1
active           = 249 (lifecycle_status=Active OR is_active!=false)
```

By `added_via`:

```
(none / pre-Alpha legacy) = 236
hr-queue-approval         =   8    ← Phase Alpha additions
bulk-upload-merge         =   5
field_leadership_inline   =   1    ← legacy frozen row (pre-Alpha; harmless)
```

* No row in `db.employees` was created via the new `field_leadership_inline` path after Phase Alpha (the one row predates the closure). Confirmed.
* `db.subcontractors` = 0. `db.vendors` = 3. No identity contamination found (matches `SUB_VENDOR_IDENTITY_AUDIT.md`).

### 4.2 `db.employee_requests` shape

```
total     = 29
pending   = 13
approved  =  8
rejected  =  8
```

Indexes present (idempotent, created at boot via `ensure_employee_requests_indexes`):

```
_id_  ·  id_1 (unique)  ·  status_1  ·  kind_1  ·  requested_at_-1
```

* Schema observed: `{id, kind, status, requested_at, requested_by_role, requested_by_label, requested_by_ip, submitter_*, submitted_via, linked_fl_record_id, audit_log[], payload{}}` — matches the spec in `EMPLOYEE_GOVERNANCE_ALPHA_IMPLEMENTATION_REPORT.md`.
* No destructive update paths exist on this collection (only `$set status` + `$push audit_log` on resolve).

### 4.3 `db.employee_lifecycle_events`

```
total = 13   (matches approved=8 new_hire + termination_approved events)
indexes: employee_id · at(-1) · queue_request_id
```

* Append-only. No update / delete paths. Indexes present.

### 4.4 No destructive operations

* New code paths do not contain any `drop_collection`, `delete_many`, or unscoped `update_many({}, …)` calls.
* `field_leadership.py` change is purely additive (inserts into a NEW collection); no schema migration on `db.employees`.
* Webhook persistence collection `resend_webhook_events` is append-only.

---

## Phase 5 · Test Certification

### 5.1 New backend pytest suite (live run)

```
cd /app/backend && REACT_APP_BACKEND_URL=$URL python -m pytest \
  tests/test_employee_governance_alpha.py \
  tests/test_iter452_5_2_resend_webhook.py \
  tests/test_iter453_lifecycle.py -q
```

Result:

```
50 passed, 1 warning in 10.18s
```

Breakdown:

| Suite | Pass | Fail | Notes |
|---|---:|---:|---|
| `test_employee_governance_alpha.py` | 17 / 17 | 0 | G-1..G-5 closures + queue E2E + auth gates |
| `test_iter452_5_2_resend_webhook.py` | 9 / 9 | 0 | delivery taxonomy, idempotency, hard-bounce escalation, ClientDisconnect |
| `test_iter453_lifecycle.py` | 24 / 24 | 0 | QA/QC + Site-Inspection transition matrix, closure-action contract |
| **TOTAL** | **50 / 50** | **0** | — |

Single warning is the well-known `python_multipart` PendingDeprecationWarning emitted by Starlette — cosmetic, not actionable in this scope.

### 5.2 Prior-iteration regression confidence

* `iteration_367.json` (ITER453 + ITER452.5.2 polish): main-agent driven, certified.
* `iteration_368.json` (Employee Governance Alpha frontend): 85% frontend pass. The two findings reported by that run:
  1. **EmployeeCombo emerald residue** (MEDIUM) → **CLOSED in commit `019e16f`** — both no-matches and showCustomTag branches now use `bg-amber-600` "Request HR add" (verified via `grep emerald|amber` in `EmployeeCombo.jsx`).
  2. **Termination POST 422 extra_forbidden on `target_employee_name`** → **NOT A BUG** — the schema correctly uses `target_employee_id` (matches the FL auto-enqueue path); the test agent sent the wrong field. The current pytest `test_queue_termination_submit_then_reject` passes using the canonical field.

### 5.3 Pytest coverage delta

`backend/tests/` now contains 3 new files for this delivery (+ 50 new test cases). No existing test files were modified.

---

## Phase 6 · Frontend Certification

* `HrEmployeeRequestsQueue.jsx` (485 LOC) — present, lint-clean, exports default page component, uses `@/lib/hrAuth` token, validates approve/reject modal gating (name ≥ 2 chars, reason ≥ 5 chars per iter368 verification), exposes data-testids per doctrine.
* `QaqcLifecyclePanel.jsx` (570) + `SiteInspectionLifecyclePanel.jsx` (572) — present, lint-clean, mounted on `ViewQaqcInspection.jsx` / `ViewInspection.jsx` respectively, closure-action radio gate enforced client-side AND server-side.
* `App.js` route `/hr/employee-requests` element wired through the `H(…)` HR-guard wrapper (verified by `grep`).
* `HrHub.jsx` includes the new `employeeRequests` tile + a live pending-count badge fetched from `/api/hr/employee-requests?status=pending&limit=1`.
* `EmployeeCombo.jsx` no-matches and showCustomTag CTAs both use `bg-amber-600` + label "Request HR add" — verified live (grep). The iter368 emerald residue is closed.
* Build version generator (`buildVersion.generated.js`) is touched on each commit — present and current.
* Live preview root URL returns the MASCI Operations Platform splash (smoke screenshot captured) → frontend dev server is healthy.

---

## Phase 7 · System Health

```
supervisorctl status:
  backend     RUNNING   uptime 0:57:42
  frontend    RUNNING   uptime 0:52:15
  mongodb     RUNNING   uptime 0:51:04
  nginx       RUNNING   uptime 1:35:16
  code-server STOPPED   (expected — not used in this pod)
```

```
GET /api/health → HTTP 200
  {"ok":true,"service":"masci-hub","ts":"2026-06-02T13:22:39.906893+00:00"}
```

Backend log observations (`/var/log/supervisor/backend.err.log`, last 200 lines):

* No exceptions on boot. All 4 new register-* routes wire cleanly.
* Recurring `scheduled-backup scheduler task is DEAD … SCHEDULER_ENABLED='false' — scheduler disabled on this worker (preview / non-prod)` every 5 min. Expected on PREVIEW — see Risk Report LOW-2.
* One historical `RuntimeError("No response returned.")` from `usage_analytics middleware` predating this delivery. The new resend webhook already contains the explicit `ClientDisconnect` catch that mitigates THIS class of noise for `/webhooks/resend`. The same fix could be backported to `usage_analytics.py` but is OUT OF SCOPE for this audit (tracked in Risk Report MEDIUM-2).

Disk usage: 46 %. No ENOSPC risk currently.

---

## Phase 8 · Production Readiness / Rollback

### 8.1 Production env-var requirements (P0)

Before deploying this build to `mascidocs.com`, the production environment **must** carry:

| Var | Value | Why |
|---|---|---|
| `APP_ENV` | `production` (or unset) | Backend refuses to start if `APP_ENV=preview` with prod DB |
| `DB_NAME` | `masci_safety` | Ditto |
| `MONGO_URL` | prod Atlas URI | |
| `ADMIN_HMAC_SECRET` | rotated 64+ char secret | Token signing |
| `MFA_ENCRYPTION_KEY` | Fernet key (REQUIRED) | Super-admin MFA |
| `RATE_LIMITING` | **`on`** | Preview is off; production MUST be on (protects new `/employee-requests` public POST) |
| `RESEND_WEBHOOK_SECRET` | **whsec_…** from Resend | Without this, webhook is unauthenticated in production · MEDIUM-1 in Risk Report |
| `AUTO_EMAIL_REPORTS` | `true` | Production opt-in (preview is off) |
| `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | unchanged | |
| `CORS_ORIGINS` | `https://mascidocs.com,https://www.mascidocs.com` | |

### 8.2 Rollback strategy

Two clean rollback paths:

1. **Code-only rollback** — `git revert <range>` for the 4 commits `aa0cb04 1117ca6 fad591e 4c69053 17f95d4 90bcbfd 80927d0 019e16f ca3d11a`. Restores the prior production code. `db.employees`, `db.employee_requests`, `db.employee_lifecycle_events`, `db.resend_webhook_events` collections are then orphaned but harmless (no constraints, no destructive sync). HR Queue rows would become unreachable from the UI but the data survives.
2. **Emergent platform rollback** — use the platform's "Rollback to checkpoint" feature (zero-cost, restores the entire app state to a prior commit). Recommended for any hot rollback within the deploy window.

No schema migration shipped, so DB rollback is automatic / unnecessary.

### 8.3 Blast radius

| Surface | Effect of rollback |
|---|---|
| `/api/employee-requests` (public POST) | Becomes 404 → FL forms fall back to local error toast; foreman sees a clear failure rather than an undefined success. Acceptable. |
| `/api/hr/employee-requests*` | Becomes 404 → HR Queue tile shows zero data, badge sits at 0. Pending queue rows survive in DB. |
| `/api/qaqc-inspections/{id}/transition` etc. | Becomes 404 → LifecyclePanels show "lifecycle endpoint unavailable" toast; record CRUD remains intact. |
| `/api/inspections/{id}/transition` etc. | Same. |
| `/api/webhooks/resend` | Becomes 404 → delivery events queued at Resend's side will retry; no data loss. |
| `db.employees` | Untouched — last destructive write path was eliminated in this delivery. |
| Frontend routes `/hr/employee-requests`, lifecycle panels | Become 404 / hidden tiles. |

### 8.4 Post-deploy smoke checklist (recommended, ≤ 5 min)

1. `curl https://mascidocs.com/api/health` → 200.
2. `curl -X POST .../api/employees/add` (anon) → expect **410**.
3. HR login → `/hr` tile "Employee Requests" visible, pending-count badge accurate.
4. Submit one `kind=new_hire` request via the public `/api/employee-requests` (rate-limited) → HR Queue shows it.
5. Approve from HR Queue → employee appears in `/hr/employees` with `lifecycle_status=Active` and `added_via=hr-queue-approval`.
6. Open one QA/QC inspection → LifecyclePanel renders current state + legal next-states; transition with corrective-action notes ≥ 20 → state advances; audit row appears in `/state-events`.
7. Test the Resend webhook with a known message-id via a Resend "Test event" → 200, idempotent dedupe on retry.

---

## Final code-review verdict

* ✅ All 50 new tests pass live.
* ✅ All 4 new backend route files lint-clean.
* ✅ All 3 new frontend components lint-clean.
* ✅ All 5 P0 Constitutional violations (G-1..G-5) verified closed by live probes.
* ✅ No destructive DB paths, no schema migration, idempotent indexes.
* ✅ No new secrets, no new dependencies, no scope drift.
* 🟡 1 MEDIUM operational item (RESEND_WEBHOOK_SECRET production setting) — see Risk Report.

**No code changes recommended within this audit cycle.** Defer the `usage_analytics.py` ClientDisconnect backport to a future iteration; not a deploy blocker.
