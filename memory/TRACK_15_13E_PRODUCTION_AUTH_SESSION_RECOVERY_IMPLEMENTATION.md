# TRACK 15.13E — Production Auth Session Recovery (Implementation)

Status: ✅ **IMPLEMENTED & TESTED** (2026-06-17)
Linked tracks: 15.13B · 15.13C · 15.13D (audit)
Test file: `/app/backend/tests/test_track_15_13e_production_auth_session_recovery.py`
(26 tests · 20 static + 6 live behavioral · all passing)

## 1. Problem (production)

Two P0 lockouts users reported on the live system:

  * **HR users**: Could open the job-folders view but clicking a Daily
    Report row threw "Session Expired" + redirected to login. Root
    cause: `GET /api/daily-reports/{id}` was gated by `require_admin`
    (admin or PM only). HR token → 401 → frontend interceptor wiped
    *every* portal token and broadcast a global `session_expired`
    modal.
  * **Asset Administrators**: Login to Shop Portal landed correctly
    on `/shop/asset-care` (15.13A) but immediately threw "Admin or PM
    login required" because the `/api/asset-care/*` and `/api/asset-
    spine/dashboard/*` read endpoints were gated by `require_admin`.
    Shop token → 401 → same global-wipe modal as above.

## 2. Fix shape (surgical, no broadening of privilege)

Two new READ-ONLY auth dependencies in `server.py`, and a re-scoped
401 handler in the frontend Axios interceptor. **No mutation route
was touched. No portal grant was widened. No new token was issued.**

### 2.1 `require_admin_or_asset_admin` (server.py)

Accepts:

  * `X-Admin-Token` (valid admin HMAC)                  → `_auth_path = "admin_token"`
  * `X-Shop-Token` (per-shop-user, `<uid>.<hmac>` form) whose user is a
    recognized Asset Administrator via **either**:
      * canonical `user_directory.is_asset_admin == True`
        → `_auth_path = "directory_flag"`
      * legacy `shop_users.role ∈ _ASSET_ADMIN_ROLE_LABELS`
        (Asset Administrator · Asset Manager · Equipment Manager ·
        Fleet Coordinator)
        → `_auth_path = "legacy_shop_role"`

**Why both paths**: existing Asset Admin users in production may
not yet have a `user_directory` mirror row (15.13A added the mirror
but didn't backfill). The legacy fallback unblocks them today
without waiting on a production backfill script.

**Reject behavior**:
  * No token / shared shop token (no `.`) → **401** "Asset
    Administrator login required" (clean auth-needed signal).
  * Valid shop user who is NOT an asset admin → **403** "Asset
    Administrator access required." 403 (not 401) is critical so
    the frontend interceptor doesn't treat it as expired session
    and bounce the user out of their valid Shop portal session.

### 2.2 `require_admin_pm_or_hr_read` (server.py)

Read-only gate. Accepts Admin, PM, or HR token. HR resolves through
`is_valid_hr_user_token_async` and is tagged
`_actor_kind = "hr_user"` so the existing `compute_pm_scope` helper
treats them as unrestricted readers (`pm_auth.py` updated).

**Mutation routes were NOT touched** — `POST /api/daily-reports`,
`DELETE /api/daily-reports/{id}`, and the audit-footer endpoint all
remain on `require_admin` (admin + PM only). HR is **never** granted
write.

### 2.3 Where the new deps are mounted

Read-only endpoints — each manually verified by test:

| Endpoint | Old dep | New dep |
|---|---|---|
| `GET /api/asset-care/summary` | `require_admin` | `require_admin_or_asset_admin` |
| `GET /api/asset-care/readiness` | `require_admin` | `require_admin_or_asset_admin` |
| `GET /api/asset-care/work-queue` | `require_admin` | `require_admin_or_asset_admin` |
| `GET /api/asset-care/alerts` | `require_admin` | `require_admin_or_asset_admin` |
| `GET /api/asset-care/notifications-matrix` | `require_admin` | `require_admin_or_asset_admin` |
| `GET /api/asset-spine/dashboard/missing-documents` | `_require_asset_admin(admin/PM)` | `require_admin_or_asset_admin` |
| `GET /api/asset-spine/dashboard/renewals` | `_require_asset_admin(admin/PM)` | `require_admin_or_asset_admin` |
| `GET /api/asset-spine/dashboard/recent-uploads` | `_require_asset_admin(admin/PM)` | `require_admin_or_asset_admin` |
| `GET /api/asset-spine/dashboard/required-documents-config` | `_require_asset_admin(admin/PM)` | `require_admin_or_asset_admin` |
| `GET /api/asset-spine/dashboard/required-documents-config-effective` | `require_admin_dep` | `require_admin_or_asset_admin` |
| `GET /api/daily-reports/{report_id}` | `require_admin` | `require_admin_pm_or_hr_read` |

Mutations on the same routers — explicitly untouched (verified by
test `test_required_docs_mutations_stay_admin_only` and
`test_daily_reports_delete_remains_admin_only`):
`PUT /api/asset-spine/dashboard/required-documents-config/{...}`,
`DELETE /api/asset-spine/dashboard/required-documents-config/{...}/{...}`,
`POST /api/daily-reports`, `DELETE /api/daily-reports/{id}`,
`GET /api/daily-reports`, `GET /api/daily-reports/{id}/audit-footer`,
`GET /api/daily-reports.csv`, exposure-signals endpoint, etc.

### 2.4 Frontend Axios interceptor (`/app/frontend/src/lib/api.js`)

Previously: any non-namespaced 401 wiped EVERY portal token the
request carried (`X-Admin-Token`, `X-PM-Token`, `X-Shop-Token`,
`X-HR-Token`, `Authorization`, …) and published a global
`session_expired` event that the `SessionStatusOverlay` rendered as
a full-screen modal across every portal.

New rule (TRACK 15.13E):

  * Infer the *active portal* from `window.location.pathname`. Map
    `/admin/*` → admin, `/hr/*` → hr, `/shop/*` → shop, etc.
  * If the failing request used the **active portal's** token,
    clear only that token. **Do not touch any other portal session.**
  * If the failing request did NOT use the active portal's token,
    treat it as a stale background helper and SILENCE the modal
    entirely (`_namespacedHandled = true`, no `session_expired`
    publish).
  * No portal context (root, sign-in, etc.) → legacy "wipe
    everything" fallback is preserved as a safety net.

Net effect: an HR user reading a Daily Report whose backend says
"no" gets the OLD UX (no false session-expired) AND the new
backend says "yes" (200). Same protection for Asset Admin reading
Asset Care.

## 3. Test coverage (26 tests · all passing · 6.21s)

### Static (20)
  * Dependencies are defined in `server.py`.
  * Dependencies tag actors with `_auth_path` for audit clarity.
  * Directory-flag path is consulted BEFORE legacy fallback.
  * Authenticated non-asset users get **403**, not 401.
  * The new dep is wired to exactly the 4 asset-spine dashboard
    GETs, the 5 asset-care GETs, and the required-docs
    config-effective GET. Nothing else.
  * `_actor_kind=hr_user` is mapped to `PmScope(is_admin=True)` in
    `pm_auth.compute_pm_scope`.
  * Daily Report singular GET uses `_read_dep` (=new dep).
  * Daily Report DELETE/POST/list/CSV/audit-footer remain on
    `require_admin`.
  * Required-docs config PUT/DELETE remain on `require_admin_dep`.
  * Frontend interceptor reads `window.location.pathname` and
    enumerates all 9 portal paths.
  * Active-portal branch only calls one `clear*Token()` and never
    `clearJwt()`.
  * No-portal-context fallback still wipes everything (safety net).
  * `_namespacedHandled` suppresses the global modal on
    portal-scoped 401s.

### Live behavioral (6 — hit the running backend via HTTP)
  * Directory-flag Asset Admin → 200 on `/api/asset-care/summary`.
  * Legacy-role Asset Admin → 200 on `/api/asset-care/summary`.
  * Normal mechanic → **403** on `/api/asset-care/summary`.
  * No token → **401** on `/api/asset-care/summary`.
  * Legacy-role Asset Admin → 200 on
    `/api/asset-spine/dashboard/renewals`.
  * HR can GET `/api/daily-reports/{id}` (200). HR cannot DELETE
    (410 freeze + admin gate) and cannot POST (401/422).

## 4. Files touched

  * `backend/server.py`
      * Added `require_admin_or_asset_admin` (~125 lines).
      * Added `require_admin_pm_or_hr_read` (~30 lines).
      * Wired the new deps into `register_asset_documents_routes`,
        `register_asset_care_routes`,
        `register_asset_admin_settings_routes`,
        `register_daily_reports_routes`.
  * `backend/pm_auth.py`
      * `compute_pm_scope` treats `_actor_kind=hr_user` as admin
        scope (matches existing shop_user · safety_user pattern).
  * `backend/routes/asset_documents.py`
      * Threaded `require_admin_or_asset_admin_dep` param.
      * Routed the 4 dashboard GETs through `_dashboard_read_dep`.
  * `backend/routes/asset_care.py`
      * Threaded `require_admin_or_asset_admin_dep` param.
      * Routed summary / readiness / work-queue / alerts /
        notifications-matrix through `_read_dep`.
  * `backend/routes/asset_admin_settings.py`
      * Threaded `require_admin_or_asset_admin_dep` param.
      * Routed `required-documents-config-effective` GET through
        `_read_dep`; PUT/DELETE untouched.
  * `backend/routes/daily_reports.py`
      * Added optional `require_admin_pm_or_hr_read` arg.
      * Routed `GET /daily-reports/{id}` through `_read_dep`. All
        other DR endpoints untouched.
  * `frontend/src/lib/api.js`
      * New active-portal inference branch on non-namespaced 401s.
  * `backend/tests/test_track_15_13e_production_auth_session_recovery.py`
      * 26-case regression suite (static + live).

## 5. Non-goals (explicit, per directive)

  * No production data backfill. The legacy-role fallback path
    means we do NOT need to write to `user_directory` to unblock
    today's users.
  * No new token or portal. Asset Admins keep using their Shop
    portal login; HR keeps using HR portal login.
  * No mutation widening. HR cannot write Daily Reports. Asset
    Admins cannot mutate required-docs config or asset records.

## 6. How to verify in the browser

  1. Asset Admin login → land on `/shop/asset-care` → KPI snapshot
     loads (no "Admin or PM login required" toast).
  2. Asset Admin → click "Open Asset Administration" → Required
     Docs editor loads (no toast).
  3. HR login → land on HR Daily Reports list → click a real DR row
     → DR detail view renders read-only (no "Session Expired"
     overlay).
  4. PM login → DR detail still works (regression check).
  5. Admin login → all of the above still work (regression check).

## 7. Backlog touched / deferred

  * 15.8A/B PM Notification cleanup — still blocked on Operator.
  * 16.0 White-Label / Multi-Tenant — strictly deferred.
  * `fetchpriority="high"` on launcher `<img>` — P3, deferred.

— end of report —
