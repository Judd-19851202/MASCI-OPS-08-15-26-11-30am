# MASCI Hub — Authorization Matrix

> **Read-only audit (Phase A, Initiative 5).** No code changes yet — this
> doc is the source of truth for "who can do what" so we can tighten
> deliberately rather than by accident.
>
> Generated: 2026-02-XX · Last updated: this turn

## 1. Token namespaces

The platform issues **disjoint, namespace-tagged HMAC tokens** (one per portal). A token from one namespace is NEVER valid in another.

| Namespace | Login route | Header name(s) | Identity model |
|---|---|---|---|
| **Admin** | `POST /api/admin/login` | `X-Admin-Token` | Single shared password (`ADMIN_PASSWORD`) → deterministic HMAC. Stateless. |
| **PM (legacy shared)** | `POST /api/pm/login` (shared) | `X-PM-Token` (no `.`) | Single shared password (`PM_PASSWORD`). Gated by `PM_SHARED_LOGIN_ENABLED` env-flag. |
| **PM (per-user)** | Issued via Admin UI | `X-PM-Token` (with `.`) | Per-PM record in `project_managers` collection; token = `pm_id.<HMAC>`. Per-user revocable. |
| **HR** | `POST /api/hr/login` | `X-HR-Token` | `hr_users` Mongo collection; bcrypt verification. |
| **Shop** | `POST /api/shop/login` | `X-Shop-Token` | `shop_users` Mongo collection; bcrypt. |
| **Dispatch** | `POST /api/dispatch/login` | `X-Dispatch-Token` | `dispatch_users` Mongo collection; bcrypt. |
| **Safety** | `POST /api/safety/login` | `X-Safety-Token` | Identity mirror; bcrypt. |
| **Field Leadership** | (sub-token issued from another portal) | `X-Field-Leadership-Token` | `user_directory`-backed. |
| **Developer (vendor)** | `POST /api/dev/login` | `X-Dev-Token` | `DEV_PASSWORD` env; ForgedOps LLC use only. |

**Locked down in iter180**: a PM token (any flavor) is REJECTED at `/api/admin/*` routes even if the legacy semi-admin path would have accepted it (`admin_namespace` flag in `require_*` deps).

## 2. require_* dependency taxonomy

All routes protected via FastAPI `Depends(...)` with one of:

| Dependency | Accepts | Denies | Sensitivity |
|---|---|---|---|
| `require_dev` | Dev token | Everyone else | Vendor-only |
| `require_admin` | Admin OR PM (non-strict) | Everyone else | **Tightened iter180**: PM rejected on `/api/admin/*` |
| `require_admin_strict` | Admin only | Everyone (incl. PM) | Backup/recovery, role mgmt |
| `require_admin_or_dispatch` | Admin OR Dispatch | Everyone else | Mixed-portal data |
| `require_admin_or_owner` | Admin OR owner-of-resource | Everyone else | HR write-up edits etc. |
| `require_hr` | HR token | Everyone else | HR portal |
| `require_hr_user` | HR token (named user) | Shared HR or others | HR mutations needing actor |
| `require_hr_or_admin` | HR or Admin | Everyone else | HR records readable by admin |
| `require_hr_or_pass` | HR or pass-through | (rarely used) | Legacy compatibility |
| `require_safety_token` | Safety token | Everyone else | Safety portal |
| `require_safety_or_admin` | Safety or Admin | Everyone else | Cross-read |
| `require_safety_or_hr_or_admin` | Safety, HR, Admin | Everyone else | Multi-sector ops |
| `require_safety_hr_admin` | Safety, HR, Admin | Everyone else | Same; legacy variant |
| `require_dispatch_token` | Dispatch | Everyone else | Dispatch portal |
| `require_any_portal_token` | Any valid portal token | Anonymous | Common feature gates |
| `require_field_leadership` | Field-Leadership token OR HR/Admin | Everyone else | FL portal |

## 3. Admin-only route classification (highest-risk surface)

> All routes below require `require_admin` OR `require_admin_strict`. Backend authorization is canonical. Frontend may additionally hide nav items but never gates protection.

### 3A — Super-sensitive (Admin-only, RECOMMEND step-up re-auth in future Initiative 5b)

| Route | Why super-sensitive |
|---|---|
| `POST /api/admin/directory/k4/convert` | Promotes a mirrored user to managed (grants password lifecycle access) |
| `POST /api/admin/directory/k4/assign-role-template` | Changes a user's RBAC role |
| `POST /api/admin/directory/k4/disable` | Disables a user (locks them out) |
| `POST /api/admin/directory/k4/set-password` | Resets a user's password |
| `POST /api/admin/pm-users` (create/update/delete) | Per-PM token lifecycle |
| `POST /api/admin/hr-users` (create/update/delete) | HR account lifecycle |
| `POST /api/admin/role-templates/*` | Role-template surface |
| `POST /api/admin/backups/run-now` | Triggers full backup |
| `GET /api/admin/backups/{filename}` | Downloads a backup zip |
| `DELETE /api/admin/backups/{filename}` | Deletes a backup |
| `POST /api/admin/r2/backup-now` | Forces R2 upload |
| Any route mutating `audit_events` directly | Tamper risk |

### 3B — Admin/Strict (no PM, no other portal)

`/api/admin/system-counters`, `/api/admin/dev-only-*`, `/api/admin/backups-scheduler-state`, `/api/admin/r2/*` (write paths), `/api/admin/lifecycle/*` (future after Initiative 3).

### 3C — Admin (PM allowed in legacy flows)

Read-only ops dashboards, fleet rollups, etc. PM tokens get filtered-by-project visibility.

## 4. HR-only route classification

| Route prefix | Sensitivity | Notes |
|---|---|---|
| `/api/hr/employees/*` (write) | HR-only | Personnel mutation |
| `/api/hr/payroll-variance/*` | HR-only | Compensation-sensitive |
| `/api/hr/field-leadership-records/*` (write) | HR-only | Write-ups, terminations |
| `/api/hr/employee-equipment/*` | HR + Admin | Equipment accountability |
| `/api/hr/time-verification/*` | HR-only | Payroll feed |
| `/api/hr/employees` (read) | HR + Admin | Directory read |
| `/api/hr/login`, `/api/hr/logout` | Anonymous → HR | Auth entry |

**Iter178**: HR Time Verification summary card FLSA-split bug fixed; backend authorization unchanged.

## 5. Frontend visibility — known stale-state risks

`EnforcePortalScope.jsx` (iter179) clears tokens cross-portal on login/logout. `PortalSwitcher.jsx` resets identity. `sessionReset.js` centralises token wiping.

| Risk | Status | Mitigation |
|---|---|---|
| Admin nav visible after HR login | ✅ FIXED iter179 | `clearAllSessions()` on multi-login |
| PM badge visible after admin logout | ✅ FIXED iter179 | Same |
| Blank shell on unauthorized route | ✅ FIXED iter181 | `NotFound.jsx` catch-all |
| Stale `currentPortal` in localStorage outliving token | ⚠️ Acceptable — `EnforcePortalScope` rechecks on every guarded route entry; nav menus hide when token absent |
| Direct URL to `/admin/...` while non-admin | ✅ Server returns 401; FE routes to NotFound |

## 6. Audit logging coverage

Already captured in `admin_audit` collection:

| Event | Audited? |
|---|---|
| Admin login success | ✅ |
| Admin login failure | ✅ (alert_events) |
| PM per-user login | ✅ |
| HR login | ✅ (since iter172) |
| Directory K4 mutation | ✅ |
| Role-template change | ✅ |
| Backup run / download / delete | ✅ |
| Denied access (401/403 on Admin endpoints) | **GAP** — not currently logged |
| Idle/absolute timeout invalidation | **GAP** — endpoint doesn't exist yet (Initiative 4) |
| Role-change-induced session invalidation | **GAP** — see § 8 |

## 7. Identified gaps (proposed for future Initiative 5b, awaiting your sign-off)

1. **Denied-access audit gap** — Admin endpoints currently log success but not denials. Recommend: log denied attempts with actor token-namespace + attempted route + IP.
2. **Step-up re-auth absent** — super-sensitive actions in § 3A take a single Admin token regardless of when it was issued. Recommend: add `auth_time` claim, require ≤5 min for the 7 routes listed in § 3A.
3. **Role change → existing tokens** — if a PM user's role-template is changed, their existing per-user token remains valid until natural expiry. Currently we have no natural expiry (until Initiative 4). After Initiative 4 lands, role-mutation should `revoke_user_sessions(user_id)` to force re-login.
4. **Bulk-delete safety** — Admin can `DELETE /api/admin/backups/{filename}` without confirmation. Recommend: require `?confirm=<filename>` query param matching path.
5. **Backup download links** — Admin downloads stream the zip directly. No per-download audit log row. Consider: log `backup_downloaded` events for chain-of-custody.

## 8. Acceptance status

| Initiative 5 acceptance criterion | Status |
|---|---|
| Admin-only sensitive actions inaccessible to non-authorized (backend-enforced) | ✅ Backend gates correct; confirmed via existing iter180 + iter179 tests |
| Legitimate Admin/HR users can still complete workflows | ✅ All 164 backend tests passing; no regression observed |
| Audit logs capture sensitive access and **denied attempts** | ⚠️ Success logged; **denials not logged** (gap § 7.1) |
| No stale nav leakage | ✅ Fixed iter179 |
| No regressions in permitted workflows | ✅ Verified preview |

## 9. Status of identified gaps (post-5b-broader implementation)

Per operator directive, **5b-broader** was implemented in iter187:

| Gap (from § 7) | Status |
|---|---|
| 1. Denied-access audit gap | ✅ Implemented — `record_access_denial` writes to `audit_events` for both `require_admin` and `require_admin_strict`. |
| 2. Step-up re-auth | ✅ Code wired into 7 super-sensitive K4 mutation routes via `require_recent_step_up_raise`. Currently a **pass-through no-op** in both preview and production because the master switch `ADMIN_STEP_UP_ENABLED` is unset. Flip on to enforce. |
| 3. Role-change-induced session invalidation | ⏸ Deferred to Initiative 5c — depends on Initiative 4 (session activity collection) being active. |
| 4. Bulk-delete confirmation | ✅ Implemented — `DELETE /api/admin/backups/{filename}` now requires `?confirm=<filename>` matching the path. |
| 5. Backup download chain-of-custody | ✅ Implemented — `GET /api/admin/backups/{filename}` writes a `backup_downloaded` audit row. |

Tests: `/app/backend/tests/test_iter187_admin_hardening_5b.py`.
