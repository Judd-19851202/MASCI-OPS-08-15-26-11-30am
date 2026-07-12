# TRACK 15.14A/B — TEMP-PASSWORD ENFORCEMENT + FL RECOVERY · CERT REPORT

**Build:** preview (`*.preview.emergentagent.com`, `DB_NAME=masci_safety_preview`)
**Run date:** 2026-06-18
**Author:** main agent (preview proof). Production verification still required by operator.

---

## OBJECTIVE RECAP

Per directive, fix BOTH defects with permanent, layered enforcement:

- Track 15.14A — Temporary password enforcement, all 4 layers, all portals
  including Admin.
- Track 15.14B — Field Leadership UX recovery (records ↔ users cross-link,
  unambiguous labels, no isolated workflows).

---

## REPAIR REPORT — what code was changed (and why)

### Backend (Layer 3 backstop · primary safeguard)

- **NEW** `/app/backend/auth_must_change.py`
  Shared `enforce_password_change_required(request, actor)` helper.
  Allow-list of path suffixes (`/me`, `/change-password`, `/logout`,
  `/forgot-password`, `/reset-password`, `/reset/{token}` substrings).
  Raises HTTP **403** with body
  `{"detail":{"code":"PASSWORD_CHANGE_REQUIRED", "message": "..."}}`
  whenever `actor.must_change_password=True` AND the path is not on
  the allow-list.

- Patched portal auth dependencies to call the helper after token
  resolution (the only place we have an authoritative `actor` dict
  with the flag bound to it):
  - `routes/hr_portal_deps.py` :: `_require_hr_user`
  - `routes/safety_portal/_deps.py` ::
    `_require_safety_token`, `_require_safety_or_admin`,
    `_require_safety_or_admin_fleet`, `_require_safety_admin_or_pm`,
    `_require_safety_or_hr_or_admin`
  - `routes/dispatch_portal_auth.py` ::
    `_require_dispatch_token`, `_require_dispatch_or_admin`
  - `routes/field_leadership_portal.py` ::
    `require_fl_user`, `require_hr_or_admin`
  - `routes/integrations/_deps.py` :: `_require_any_portal_token`
  - `server.py` ::
    `require_admin`, `require_admin_async` (PM-doc paths),
    `require_shop_or_admin` (per-shop-user path),
    `require_safety_or_admin` (safety-user path),
    `require_admin_or_asset_admin` (shop-user paths),
    `require_admin_pm_or_hr_read` (PM + HR paths)

  Notes:
  • Admin token is env-bound HMAC (no per-admin record), so the
    enforcement for super-admins flows through the directory-user
    multi-login suppression instead (Layer 1, below).
  • Shop/Safety/Dispatch HMAC tokens (env-derived shared) cannot
    carry a per-user flag and were intentionally left as-is.

### Backend (Layer 1 · multi-login + MFA suppression)

- `routes/auth_directory_routes.py` :: `multi_login` — when
  `row.must_change_password=True`, return `portal_tokens={}` plus the
  `session_token`. Audit row written: `multi_login_temp_pw_blocked`.
- `routes/mfa_routes.py` :: `mfa_verify_login` — same suppression on
  the MFA verify-login path. Audit event: `LOGIN_TEMP_PW_BLOCKED`.

### Backend (Layer 4 · change-master-password mints fresh portal_tokens)

- `routes/auth_directory_routes.py` :: `change_master_password` —
  after `ud.self_change_password`, re-mints the full portal-token
  bundle via the existing `_mint_all()` helper and returns
  `{ok, portal_tokens, user, must_change_password: false}`. Removes
  the need for a second login round-trip after rotation.

### Backend (no change required for old-token invalidation)

- Per-portal HMAC tokens are bound to the first 16 chars of the
  bcrypt `password_hash` (HR / PM / Shop / Safety / Dispatch / FL).
  Rotating the password mutates the hash, which invalidates the old
  token by construction. Verified live in cert run.

### Frontend (Layer 2 · route guards)

- **NEW** `/app/frontend/src/lib/mustChangePassword.js`
  Per-portal flag storage (`{portal}_must_change_password` in
  localStorage), `getMustChange()`, `setMustChange()`,
  `clearAllMustChange()`, `redirectToChangePassword(portal)`.
- Updated every per-portal guard to consult the flag and bounce to
  the right `/change-password` before rendering protected children:
  `RequireHr`, `RequirePm`, `RequireShop`, `RequireSafety`,
  `RequireDispatch`, `RequireFl`, `RequireAdmin`.

### Frontend (Layer 1 client + Layer 4 SPA)

- `pages/SignIn.jsx` — multi-login, MFA, and passkey paths now check
  `data.must_change_password` and route the user to `/change-password`
  before `landingFor()` runs.
- `pages/HrLogin.jsx`, `PmLogin.jsx`, `ShopLogin.jsx`,
  `SafetyLogin.jsx`, `DispatchLogin.jsx`,
  `FieldLeadershipPortalLogin.jsx` — each now writes the
  `setMustChange(portal, …)` flag at login time.
- **NEW** `pages/DirectoryChangePassword.jsx` — unified
  `/change-password` page for directory (`/sign-in`) users; calls
  `/api/auth/change-master-password`, fans out the freshly-minted
  portal_tokens via `applyMultiLoginResponse`, clears every
  must-change flag, then `landingFor(user)`.
- Per-portal change-password pages now clear their per-portal flag
  on success:
  `HrChangePassword`, `PmChangePassword`, `ShopChangePassword`,
  `SafetyChangePassword`, `DispatchChangePassword`,
  `FieldLeadershipPortalChangePassword`.

### Frontend (Layer 3 SPA reactor)

- `lib/api.js` — global response interceptor now detects HTTP 403
  with `detail.code === "PASSWORD_CHANGE_REQUIRED"`, identifies the
  source portal from the request header (`X-HR-Token` etc.) or the
  URL, stores the flag, and bounces to the correct change-password
  route. Idempotent (no bounce loop while already on that route).

### Frontend (Track 15.14B · Field Leadership UX)

- `components/hr/sidebar/HrSideNavV2.jsx` —
  Renamed "Field Leadership" → "Field Leadership Records".
  Renamed "FL Portal Accounts" → "Field Leadership Users".
  Placed both items adjacent in the "People Operations" group.
- `pages/HrFieldLeadership.jsx` — added a top banner with a primary
  CTA: "Manage Field Leadership Users" → `/hr/field-leadership-users`.
- `pages/HrFieldLeadershipUsers.jsx` — added a top banner with a
  secondary CTA: "View Field Leadership Records" → `/hr/field-leadership`.
  Data-testids: `hr-fl-records-to-users`, `hr-fl-users-to-records`.

---

## CERTIFICATION REPORT — runtime proof

### Backend backstop · 4 portals · LIVE preview
`backend/tests/track_15_14a_backstop_proof.py` exercises the full
create → temp-pw login → protected-call → change-password → re-call
loop against the deployed preview backend.

```
── [HR]        protected route → 403 PASSWORD_CHANGE_REQUIRED   ✓
               /me reachable while flag is true                 ✓
               change-password returned a fresh token           ✓
               protected route 200 OK with new token            ✓
               old token rejected (401) — hash-binding works    ✓
── [Dispatch]  same sequence on /api/dispatch/daily-reports     ✓✓✓✓✓
── [Safety]    same sequence on /api/safety/overview            ✓✓✓✓✓
── [FL]        same sequence on /api/field-leadership/portal/dispatch-today  ✓✓✓✓✓

Track 15.14A · BACKEND BACKSTOP CERTIFICATION · PASS
```

### Directory / multi-login suppression · LIVE preview

```
Create directory user (mcp=true, portals=[hr,pm]) ............ 200 OK
multi-login                                                  → ok=True
                                                                mcp=True
                                                                portal_tokens={}
                                                                session_token_present=True
change-master-password (with x_directory_token)              → ok=True
                                                                mcp=False
                                                                portal_tokens.keys=['hr','pm']
re-login with new password                                   → ok=True
                                                                mcp=False
                                                                portal_tokens.keys=['hr','pm']
```

### Frontend deep-link bypass · LIVE preview (Playwright)

```
DEEP_LINK_AFTER_MCP_SET end_url =
  https://backup-forensics.preview.emergentagent.com/hr/change-password
deep_link_blocked_by_guard = True
```

(localStorage flag set, then navigated to `/hr/employees`; guard
bounced to `/hr/change-password`; screenshot saved at
`/tmp/track_15_14b_deeplink_guard.png` showing the "Choose your
password" page.)

### Field Leadership UX · LIVE preview (Playwright)

```
sidebar Users   = ['Field Leadership Users …']
sidebar Records = ['Field Leadership Records …', 'View Field Leadership Records']
hr-fl-users-page         visible_count = 1
hr-fl-records-to-users   visible_count = 1   (Records → Users CTA)
hr-fl-users-to-records   visible_count = 1   (Users → Records CTA)

OVERALL_TRACK_15_14B_BROWSER_PROOF = PASS
```

### Non-HR/non-admin cannot manage FL users · LIVE preview

- `GET /api/admin/field-leadership-users` with `X-Safety-Token` → 401
  ("Admin or HR login required" from `require_hr_or_admin` closure).
- `GET /api/admin/field-leadership-users` with no token → 401.
- `GET /api/admin/field-leadership-users` with `X-HR-Token` → 200 + payload
  (24 users on preview, audited previously).

### Old/temp-pw HR Manager session sanity

- `hrmanager@mascigc.com` (CertProof2026!) continues to log in, no
  forced rotation, normal landing. (Flag = false on this user.)

---

## REGRESSION REPORT

- Existing backend ESLint / ruff: 2 pre-existing FL warnings
  (`cutoff_90d` unused + `l` shadow) — present before this track,
  not introduced by these edits, left alone per repair-track scope.
- All existing per-portal smoke tests pass (HR sanity GETs, FL admin
  endpoint, daily-reports, asset-care reads).
- Track 15.13K-B Gap #1 in-SPA failure injection — unchanged and
  still PROVEN (HR Daily Reports retry still recovers).

---

## PRODUCTION FIELD LEADERSHIP COUNT — operator-only step

I cannot read the production DB from this preview pod. To verify the
real Field Leadership population on `mascidocs.com`, please run from
a production-authorized shell:

```javascript
// production Mongo shell
use masci_safety
db.field_leadership_users.countDocuments({})
db.field_leadership_users.countDocuments({disabled: true})
db.field_leadership_users.countDocuments({disabled: {$ne: true}})
db.field_leadership_records.countDocuments({})
```

OR sign in as `hrmanager@mascigc.com` on `mascidocs.com` and read
the counts directly from `/hr/field-leadership-users` (the
`AdminFieldLeadershipUsersPanel` lists every row with status + last
login).

---

## DEPLOYMENT RECOMMENDATION

I am NOT marking this track Proven, Certified, or Deployable.

Per Five Pillars + your "PROVEN means real production" directive,
the gate that still has to be opened is:

1. Deploy current preview build to `mascidocs.com`.
2. From your real device, exercise:
   - HR Manager logs in via per-portal `/hr/login` (no temp pw).
   - HR Manager creates a new FL user with a temp password.
   - That FL user signs in via `/field-leadership/portal/login`,
     gets forced into change-password, picks a new one, and lands
     on the dashboard.
   - Same recipe via the master `/sign-in` (multi-portal) flow.
   - Deep-link bypass on the new account: paste a protected URL
     before rotating — must bounce to change-password.
3. Verify on the production HR sidebar:
   - "Field Leadership Records" exists.
   - "Field Leadership Users" exists.
   - Each page surfaces the cross-link button to the other.
4. Verify no regression on the HR Daily Reports flow
   (Track 15.13K-B still holds).

Until you confirm step-by-step success on production, this track
remains **🟡 OPEN — engineering complete, awaiting production
verification**.
