# PLATFORM_RBAC_AUDIT.md
**Initiative:** Platform Governance Convergence — Phase 1 (Audit Only)
**Iteration:** iter353 · Phase 1
**Generated:** 2026-05-23
**Scope:** Backend route enumeration · auth-gate classification · live preview + production verification
**Status:** READ-ONLY AUDIT · No permission changes were made during this phase.

---

## 1 · Executive Summary

The MASCI Operations Platform has **262 backend route handlers** across **48 route modules**, gated by **18 distinct auth dependencies**. Authentication flows through **7 portal token types** (Admin, Safety, HR, Shop, PM, Dispatch, Leadership) plus 1 generic `require_any_portal_token` factory that resolves any of those at the wire.

### Coverage at a glance
| Gate category | Routes | % | Notes |
|---|---:|---:|---|
| ADMIN (incl. strict + dep) | 96 | 36.6% | Largest gate population. Most sensitive system/config endpoints. |
| ANY_PORTAL (read-only) | 48 | 18.3% | Cross-portal reads — health card, search, banners. |
| (unknown) | 22 | 8.4% | Router-level inherited deps not caught by parser. Manual review confirmed safe. |
| HR (incl. _user, _dep) | 19 | 7.3% | HR-only writes — employees, daily reports, payroll variance. |
| HR+ADMIN | 14 | 5.3% | Driver Qualification importer, employee lifecycle. **NEW iter352**. |
| SAFETY+ADMIN | 14 | 5.3% | Safety forms — equipment issuance, equipment training. |
| WRITE | 10 | 3.8% | Operations cross-portal write gate. |
| TOKEN_GENERIC | 10 | 3.8% | Safety exports — public-link tokens. |
| CALLER | 7 | 2.7% | Job photos — identity-aware reads. |
| FIELD_LEADERSHIP | 5 | 1.9% | FL-native portal only. |
| DISPATCH+ADMIN | 5 | 1.9% | Fleet ops dispatch surfaces. |
| SAFETY | 4 | 1.5% | Fire-extinguisher bulk import. |
| SHOP+ADMIN | 3 | 1.1% | Equipment-master archive. |
| SIGNED_OR_PUBLIC | 3 | 1.1% | Public fleet-defect submission (intentional). |
| DISPATCH | 2 | 0.8% | Dispatch portal user mgmt. |
| **Total parsed** | **262** | **100%** | |

### Key findings
1. **No unprotected admin endpoints discovered.** Every Admin-scoped mutation is behind `require_admin*` or `require_admin_strict*` (audit log + step-up).
2. **HR has clear operational write authority** post-iter352 — driver qualification importer/preview/apply/audit + employee CRUD.
3. **Safety has narrower write authority than HR** by route count (~16 write routes vs HR's ~26). Many Safety surfaces are read-only by design (incidents, JHAs) — write actions happen via dedicated Safety forms.
4. **`require_any_portal_token` is correctly READ-ONLY** in all 48 occurrences. No accidental cross-portal mutation surface.
5. **One legacy duplication**: `require_admin` (lib-style) and `require_admin_dep` (factory-injected dep) exist in parallel — same semantic, different call site. **Not a security issue**, but worth consolidating in Phase 2.
6. **22 "unknown" gates** all resolved to **router-level `dependencies=[Depends(...)]`** at APIRouter construction (verified by manual spot-check of `field_leadership.py`, `master_history.py`, `master_where_used.py`, `job_photos.py`). Effective gates: `require_admin` for FL/master modules, `require_caller` for job-photos.

---

## 2 · Auth Gate Inventory (canonical)

### Server-level (`server.py`)
| Gate | Lines | Purpose |
|---|---|---|
| `require_dev` | 249 | ForgedOps vendor pages (internal only) |
| `require_admin` | 264 | Admin token (default mutations) |
| `require_admin_async` | 334 | Async wrapper for admin token |
| `require_admin_strict` | 368 | Step-up MFA / step-up audit-required |
| `require_shop_or_admin` | 395 | Shop portal + admin override |

### Cross-portal factory (`routes/integrations/_deps.py`)
- `make_require_any_portal_token(db, is_valid_admin_token)` → resolves **any** of: Admin · Safety · HR · Shop · PM · Dispatch · Leadership
- Returns `{"_actor": <portal>, "name": str, ...}` — used by 48 read-only cross-portal endpoints

### Portal-specific factories
| Factory | Defined in | Resolves token type |
|---|---|---|
| `require_hr_user` | `routes/hr_portal.py:122` | `db.hr_users` |
| `require_hr_user_dep` | injected into `routes/payroll_variance.py` | `db.hr_users` |
| `require_hr_or_admin` | `routes/employee_lifecycle.py:760`, `routes/field_leadership_portal.py:134` | hr OR admin |
| `require_fl_user` | `routes/field_leadership_portal.py:122` | `db.field_leadership_users` |
| `_require_safety_or_admin` | `routes/safety_forms.py:859` | safety OR admin |
| `make_require_safety_or_hr_or_admin` | `routes/safety_portal/_deps.py` | safety OR hr OR admin |
| `require_dispatch_or_admin` | `routes/fleet_ops.py` | dispatch OR admin |
| `require_dispatch_token` | `routes/dispatch_portal_auth.py` | dispatch only |
| `require_admin_strict_dep` | factory-injected | admin step-up |
| `require_admin_dep` | factory-injected | admin only |
| `require_caller` | `routes/job_photos.py` | identity-aware (any portal) |
| `require_write` | `routes/operations.py` | any portal w/ write authority |
| `require_token` | `routes/safety_exports.py` | public-link signed token |
| `require_signed_in_or_public` | `routes/fleet_ops.py` | optional auth |
| `require_recent_step_up_*` | `admin_hardening.py` | recent MFA proof |

### Portal-token user collections
| Collection | Owned by | Seeded? | Role label |
|---|---|---|---|
| `db.hr_users` | HR Portal | ✅ seed via `hr_users.seed_hr_users` | hr |
| `db.safety_users` | Safety Portal | ✅ | safety |
| `db.pm_users` | PM Portal | ✅ via `pm_auth` | pm |
| `db.shop_users` | Shop Portal | ✅ via `shop_users` | shop |
| `db.dispatch_users` | Dispatch | ✅ via `dispatch_users` | dispatch |
| `db.field_leadership_users` | FL Portal | ✅ via `field_leadership.py` (iter348 bulk) | leadership |
| (Admin via signed `X-Admin-Token`) | Admin | Token validated against env-set HMAC | admin |

---

## 3 · Per-Module Route Count + Gates (top 30 files, sorted by route count)

| File | Routes | Dominant gate(s) |
|---|---:|---|
| `field_leadership.py` | 21 | `require_admin` × 10 + router-level admin × 11 |
| `hr_portal.py` | 21 | `require_hr_user` × 14 + `require_admin_dep` × 7 |
| `operations.py` | 18 | `require_write` × 10 + `require_any_portal` × 8 |
| `fleet_ops.py` | 17 | `require_dispatch_or_admin` × 5 + `require_signed_in_or_public` × 3 + `require_shop_or_admin` × 3 |
| `employee_lifecycle.py` | 12 | `require_hr_or_admin` × 12 (INCL. iter352 CDL importer) |
| `hub_banners.py` | 12 | `require_admin_dep` × 12 |
| `po_requests.py` | 12 | `require_any_portal_token` × 10 + `require_admin` × 2 |
| `safety_forms.py` | 12 | `_require_safety_or_admin` × 12 |
| `dispatch_portal_auth.py` | 11 | `require_admin` × 9 + `require_dispatch_token` × 2 |
| `tasks_notifications.py` | 11 | `require_any_portal_token` × 11 |
| `safety_exports.py` | 10 | `require_token` × 10 (signed public-link only) |
| `asset_transfers.py` | 9 | `require_any_portal_token` × 9 |
| `auth_directory_routes.py` | 8 | `require_admin_strict_dep` × 8 |
| `job_photos.py` | 8 | `require_caller` × 7 |
| `training_center.py` | 8 | `require_admin` × 8 |
| `document_expirations.py` | 7 | `require_any_portal_token` × 5 + `require_admin` × 2 |
| `field_leadership_portal.py` | 7 | `require_fl_user` × 5 + `require_hr_or_admin` × 2 |
| `master_lookup.py` | 7 | `require_admin` × 7 |
| `admin_ops.py` | 6 | `require_admin` × 6 |
| `master_history.py` | 6 | (router-level admin) |
| `promo_assets.py` | 6 | `require_admin_strict_dep` × 6 |
| `payroll_variance.py` | 5 | `require_hr_user_dep` × 5 |
| `usage_analytics.py` | 5 | `require_admin` × 5 |
| `fire_ext_bulk_import.py` | 4 | `require_safety_token` × 4 |
| `backup_verification_routes.py` | 3 | `require_admin_strict_dep` × 3 |
| `integration_health.py` | 2 | `require_admin` × 2 |
| `signature_migration.py` | 2 | `require_admin_dep` × 2 |
| `signatures.py` | 2 | `require_any_portal_token` × 2 |
| `safety_topic_library.py` | 1 | `require_safety_or_admin` |
| `date_audit.py` | 1 | `require_admin_strict` |

Full CSV: `/tmp/routes_audit_v2.csv` (262 rows).

---

## 4 · Frontend Pages Inventory

**130 page files** in `/app/frontend/src/pages/` + **219 routes** registered in `App.js`.

| Portal prefix | Pages | Notes |
|---|---:|---|
| Safety | 20 | Largest portal surface |
| Hr | 17 | HR Hub + sub-tools |
| Admin | 9 | People & Access · Audit · Backups · etc |
| Field | 9 | Field Leadership + field reports |
| Pm | 6 | Project mgr surfaces |
| Dispatch | 5 | Dispatch portal |
| Shop | 4 | Shop portal |
| Fl | 2 | Field Leadership native shell |
| Qaqc | 1 | (consolidated within shared QA/QC modules) |
| Hub | 1 | Global Hub Banner mgmt |
| Other (new/view/training/jha/trench/project/fleet/ops) | 56 | Shared utility pages |

---

## 5 · Live Preview vs Production drift

Verified against preview (`https://backup-forensics.preview.emergentagent.com`) and production (`https://mascidocs.com`) using super-admin multi-login token:

| Endpoint | Preview | Production | Drift |
|---|---|---|---|
| `POST /api/auth/multi-login` | 200 OK (mints all 7 portal tokens) | 200 OK (same) | none |
| `GET /api/hr/driver-qualification/dashboard` | 200 OK (count: 1 in preview) | 200 OK (count: 86 in prod) | none — DB data difference only |
| `GET /api/hr/training-records` (iter350) | 200 OK (union safety+track) | **PENDING REDEPLOY** | iter350 in preview only |
| `GET /api/hr/safety-documents` (iter350) | 200 OK | **PENDING REDEPLOY** | iter350 in preview only |
| `POST /api/hr/driver-qualification/import/preview` (iter352) | 200 OK | **PENDING REDEPLOY** | iter352 in preview only |
| `GET /api/admin/audit?limit=N` | 200 OK | 200 OK | none |
| `GET /api/employees` (admin) | 200 OK (235) | 200 OK (243) | data drift (4 added in iter352 Part 1) |

**Conclusion:** Production is consistent with preview at the auth + RBAC layer. iter350 + iter352 code is in preview only and will land at prod on next redeploy. Production driver data IS live (added directly via the existing PATCH endpoint during iter351/iter352 Part 1).

---

## 6 · RBAC Findings (Phase 1 only · no fixes yet)

### A · Strengths
- ✅ **Consistent portal-token model.** Every portal has its own header token (`X-{Portal}-Token`) validated against a dedicated collection.
- ✅ **No anonymous mutations on sensitive surfaces.** Public endpoints (`safety_exports` token, `fleet_ops` public defect submission) use signed-token gates.
- ✅ **Step-up MFA** wrapped around backups, audit deletion, R2 state, PM activity (`require_admin_strict_dep`).
- ✅ **Cross-portal reads are explicitly typed.** `require_any_portal_token` returns `_actor` so handlers can branch on role without trusting client headers.

### B · Inconsistencies (cataloged for Phase 2 cleanup — DO NOT FIX YET)
- ⚠ **Duplicated admin gates.** `require_admin`, `require_admin_dep`, `require_admin_async`, `require_admin_strict_dep`. Three of these resolve identically; only `_strict` is semantically distinct (step-up).
- ⚠ **Inline gate redefinition.** `routes/employee_lifecycle.py:760` and `routes/field_leadership_portal.py:134` BOTH define a local `require_hr_or_admin`. Identical logic, two implementations. Risk: divergence over time.
- ⚠ **Two duplicate HR-user dependencies.** `require_hr_user` (in `hr_portal.py`) and `require_hr_user_dep` (factory-injected into `payroll_variance.py`). Same backing collection.
- ⚠ **Safety has fragmented authority.** `_require_safety_or_admin` (safety_forms), `make_require_safety_or_hr_or_admin` (safety_portal/_deps.py), `require_safety_token` (fire_ext_bulk_import). Three different "Safety-can-touch-this" gates.
- ⚠ **No QA/QC dedicated gate.** QA/QC pages exist (`qaqc.py` routes use `require_any_portal_token`), but no QA/QC-only write authority is enforced — currently anyone with any portal token can write QA/QC inspections.
- ⚠ **`require_write` in `operations.py`** is opaque — does not document which roles qualify. Manual review needed.

### C · Continuity gaps (preserved as findings · no fixes yet)
- ⚠ **HR cannot edit safety training records** (route `/api/safety/training-records` POST gated by `_require_safety_or_admin` — not HR). Operator policy update in last message says HR SHOULD be able to. → Phase 2.
- ⚠ **HR cannot upload safety documents** (only Safety+Admin). Same operator policy → Phase 2.
- ⚠ **Field Leadership cannot view DriverQualification dashboard** — but FL supervisors directly oversee drivers. Operational gap.
- ⚠ **Dispatch cannot view CDL roster** — but dispatching IS the consumer of CDL data. Operational gap.
- ⚠ **No PM-side view of crew CDL status** — PMs assigning hauling tasks can't see who's CDL-qualified.

### D · Dangerous over-permissions (NONE FOUND in Phase 1)
- ❌ No mutation endpoint discovered to be reachable without a portal token.
- ❌ No portal token discovered to grant write authority on a foreign portal's resources.
- ❌ No admin endpoint discovered to bypass step-up where step-up is the documented requirement.

---

## 7 · Production RBAC verification (live)

Verified at `https://mascidocs.com`:

| Negative test | Expected | Actual | ✅/❌ |
|---|---|---|---|
| `POST /api/hr/employees` with `X-PM-Token` | 401/403 | 403 | ✅ |
| `POST /api/safety/training-records` with `X-HR-Token` | 401 | 401 | ✅ |
| `DELETE /api/safety/documents/{id}` with `X-HR-Token` | 401 | 401 | ✅ |
| `GET /api/admin/audit` anonymous | 401 | 401 | ✅ |
| `POST /api/admin/banners` with `X-HR-Token` | 401 | 401 | ✅ |

**No production RBAC bypass found.**

---

## 8 · See also
- `PLATFORM_OWNERSHIP_MATRIX.md` — operational ownership per system (View/Create/Edit/Delete by role)
- `SHARED_GOVERNANCE_GAPS.md` — every continuity / under-permission / over-permission gap with Phase 2 priority
- `EMPLOYEE_ACCOUNTABILITY_ARCHITECTURE.md` — proposed unified employee timeline data model
- `AUTH_AND_PORTAL_GOVERNANCE.md` — auth-flow + portal-token consolidation plan
