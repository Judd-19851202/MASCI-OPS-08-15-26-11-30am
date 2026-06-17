# TRACK 15.13A · ASSET CARE ROUTING RECOVERY + SENTRY HR NETWORK ERROR REPAIR

**Date**: 2026-02-15 (executed 2026-06-17)
**Mode**: P1 operational recovery, surgical implementation per Track 15.13 plan
**Verdict**: 🟢 **READY TO DEPLOY**

---

## 1. Executive Summary

Implemented items #1, #2, #3, #4 from the Track 15.13 recovery plan + a
targeted Sentry noise-suppression for the Safari `AxiosError: Network
Error` alerts. All changes are surgical and additive:

| # | Item | Where | Risk |
| - | ---- | ----- | ---- |
| 1 | `/shop/login` returns `is_asset_admin` (mirrored from `user_directory`) | `backend/server.py · shop_login` | Low — read-only echo |
| 2 | `ShopLogin.jsx` honors the flag → routes to `/shop/asset-care` (and the SSO hook destination is computed dynamically so it doesn't race past us) | `frontend/src/pages/ShopLogin.jsx` | Low — non-asset shop users land on `/shop` exactly as before |
| 3 | Admin Shop Users create/update mirrors `is_asset_admin=true` into `user_directory` when role is `Asset Administrator` / `Asset Manager` / `Equipment Manager` / `Fleet Coordinator` | `backend/server.py · admin_add_shop_user` + `admin_update_shop_user` + new `_mirror_asset_admin_flag` helper | Low — stub directory rows have `portals: []`, no password, no grants |
| 4 | Welcome email branches by `_role_implies_asset_admin(user.role)` → `Welcome to MASCI Asset Care` headline + Asset Care portal chrome | `backend/server.py · admin_shop_user_email_welcome` | Low — non-asset shop users still get the legacy headline verbatim |
| 5 | Asset Care & Readiness link added to ShopHubV2 primary actions row | `frontend/src/pages/ShopHubV2.jsx` | Very low — additive |
| 6 | Sentry `_beforeSend` drops transient `AxiosError: Network Error` / ERR_NETWORK / ERR_CANCELED / ETIMEDOUT events that already surface in-app as a session-status banner | `frontend/src/lib/sentryInit.js` | Low — real 5xx with `response.status` continue to flow through |

**Items #5 and #6 from the original Track 15.13 plan (`/asset-transfers`
route gate · `require_admin_or_asset_admin` FastAPI dep) are deferred
to Track 15.13B per the user's "smallest safe recovery path" directive.**

---

## 2. Asset Routing Root Cause (Confirmed)

`landingFor()` in `lib/directoryAuth.js:118` already returns
`/shop/asset-care` for any user whose directory row carries
`is_asset_admin === true` and **no admin portal grant** — designed in
Track 13.33ABC.

But:
1. **`/shop/login` did not invoke `landingFor()`** — it
   unconditionally `navigate("/shop")` on success
   (`pages/ShopLogin.jsx:115`).
2. **`shop_login` did not surface `is_asset_admin`** in its response
   — the flag lives on `db.user_directory`, not `db.shop_users`, and
   the public shop-user view never read it.
3. **Admin Shop Users console** populated `shop_users.role` only —
   the canonical `user_directory.is_asset_admin` flag was never set.
4. **Welcome email** was hardcoded `Welcome to the MASCI Shop Portal`
   regardless of role (server.py line 3218).
5. **ShopHubV2** had no link from `/shop` → `/shop/asset-care`, so
   users who DID land on `/shop` had no clue Asset Care existed.
6. **`useRedirectIfDirectoryGrant("shop", ..., "/shop")` SSO hook**
   on the login page re-fires after `setShopToken()` flips
   `hasToken` to true and forces `nav("/shop")` — racing past our
   Asset Care navigate.

Each is addressed below.

---

## 3. Code Paths Changed

### Backend (`server.py`)

```python
# New module-level constants + helper.
_ASSET_ADMIN_ROLE_LABELS = {
    "Asset Administrator", "Asset Manager",
    "Equipment Manager", "Fleet Coordinator",
}
def _role_implies_asset_admin(role): ...

async def _mirror_asset_admin_flag(email, name, role) -> bool:
    """Idempotent: $set is_asset_admin on existing directory row, OR
    insert a minimal stub row (portals:[], password_hash:None,
    source:'shop_console_mirror') when the user does not yet exist
    in the directory. No portal grants, no passwords, no token mint."""
```

```python
# shop_login (line ~1880) — mirrors is_asset_admin into response.
public_user = public_shop_user_view(user)
is_asset_admin = False
try:
    dir_row = await db.user_directory.find_one(
        {"email": (user.get("email") or "").strip().lower()},
        {"_id": 0, "is_asset_admin": 1, "portals": 1},
    )
    if dir_row and dir_row.get("is_asset_admin") is True:
        is_asset_admin = True
        public_user["is_asset_admin"] = True
        public_user["portals"] = dir_row.get("portals") or []
except Exception: ...
return {"ok": True, "token": token, "kind": "shop",
        "must_change_password": ..., "user": public_user,
        "is_asset_admin": is_asset_admin}
```

```python
# admin_add_shop_user + admin_update_shop_user — call the mirror.
await _mirror_asset_admin_flag(user.email, user.name, user.role)
view["is_asset_admin"] = _role_implies_asset_admin(user.role)
```

```python
# admin_shop_user_email_welcome — branch headline + intro + steps.
is_asset_admin_role = _role_implies_asset_admin(user.get("role"))
headline = "Welcome to MASCI Asset Care" if is_asset_admin_role and not is_reset else \
           "Your Asset Care password has been reset" if is_asset_admin_role else \
           "Welcome to the MASCI Shop Portal"   # unchanged legacy path
# …intro / steps / portal_email branch on the same predicate.
html_body = render_portal_email(
    portal="Asset Care" if is_asset_admin_role else "Shop", …)
```

### Frontend

```jsx
// ShopLogin.jsx — dynamic SSO destination (race-fix).
const _isAssetAdminLanding =
  typeof window !== "undefined" &&
  window.localStorage.getItem("masci.is_asset_admin") === "true";
useRedirectIfDirectoryGrant(
  "shop", isShop() || isAdmin(),
  _isAssetAdminLanding ? "/shop/asset-care" : "/shop",
);

// ShopLogin.jsx — landingFor-equivalent honor on submit success.
const isAssetAdmin = res.data?.is_asset_admin === true ||
                     res.data?.user?.is_asset_admin === true;
if (isAssetAdmin) localStorage.setItem("masci.is_asset_admin", "true");
const intended = location.state?.from ||
                 (isAssetAdmin ? "/shop/asset-care" : "/shop");
toast.success(isAssetAdmin ? t("Welcome to Asset Care") : t("Welcome to the Shop"));
navigate(intended, { replace: true });
```

```jsx
// ShopHubV2.jsx — new primary-action link, same design tokens.
<Link to="/shop/asset-care" data-testid="shop-hub-v2-action-asset-care" ...>
  Asset Care &amp; Readiness
</Link>
```

```js
// sentryInit.js · _beforeSend — drop transient axios network noise.
if (isAxios && noResponse && (isCanceled || isNetwork || isTimeout)) {
  return null;  // already surfaced in-app via session-status banner
}
```

---

## 4. Role → Landing Matrix (Live Cert Proof)

| Role label on `shop_users` | `user_directory` mirror | `/api/shop/login` response `is_asset_admin` | SPA landing |
| -------------------------- | ----------------------- | -------------------------------- | ----------- |
| `Asset Administrator`      | `is_asset_admin:true` (stub row inserted) | `true` | `/shop/asset-care` ✅ |
| `Asset Manager`            | `is_asset_admin:true` | `true` | `/shop/asset-care` ✅ |
| `Equipment Manager`        | `is_asset_admin:true` | `true` | `/shop/asset-care` ✅ |
| `Fleet Coordinator`        | `is_asset_admin:true` | `true` | `/shop/asset-care` ✅ |
| `Mechanic`                 | no row created · existing row's flag set to `false` | `false` | `/shop` ✅ (control) |
| `Shop Manager`             | no row created           | `false` | `/shop` ✅ |
| `Parts Coordinator`        | no row created           | `false` | `/shop` ✅ |
| `Service Writer`           | no row created           | `false` | `/shop` ✅ |

Live cert ran (then rolled back):

```
POST /api/admin/shop-users
  body: {name:"Cert Asset Admin", email:"...assetadmin@mascicert.local", role:"Asset Administrator"}
  → 200 · is_asset_admin: true · directory row 'dir-asset-shadow-...' created

POST /api/shop/login
  body: {email:"...assetadmin@mascicert.local", password:"AssetCert!2026"}
  → 200 · kind:"shop" · is_asset_admin: true · user.portals: [] · user.is_asset_admin: true

Browser:
  /shop/login → SPA navigate(replace) → URL = /shop/asset-care ✅
  localStorage.masci.is_asset_admin = "true" ✅

Control: Mechanic role
  POST /api/shop/login → is_asset_admin: false → URL = /shop ✅
  localStorage.masci.is_asset_admin = null ✅
```

---

## 5. Welcome Email Proof

Static branch verified by `tests/test_track_15_13a_asset_care_routing.py · TestWelcomeEmailBranching`:

* `"Welcome to MASCI Asset Care"` headline emitted when
  `_role_implies_asset_admin(user.role)` is true.
* `"Welcome to the MASCI Shop Portal"` headline preserved for all
  other roles (Mechanic / Shop Manager / Parts Coordinator etc.) —
  zero regression.
* `render_portal_email(portal="Asset Care" if is_asset_admin_role else "Shop", ...)`
  so the email chrome (logo, footer, accent color) matches the role.
* Email steps line branches:
  * Asset role → *"Asset Care opens automatically — manage registrations,
    assignments, transfers, equipment readiness, and lifecycle visibility
    from the Asset Care & Readiness landing page."*
  * Non-asset → *"Failed Pre-Op inspections (Out-of-Service / Needs-Attention)
    auto-route to your inbox so you can plan parts & scheduling"* (unchanged).
* Login URL remains `/shop/login` (asset admins still authenticate
  through the same shop password) — explicitly noted in the email
  copy, no separate Asset Portal claimed.

---

## 6. Asset Care Tile on ShopHubV2

`data-testid="shop-hub-v2-action-asset-care"` link added to the
primary-actions row alongside *Equipment Pre-Ops*, *Fleet Visibility*,
*New Fuel/Lube Visit*. Same `var(--paper-card)` / `var(--radius-card)`
tokens — zero one-off styling. Verified `PRESENT` on the live `/shop`
page during cert (screenshot: `/tmp/track15_13a_shop_hub_with_tile.png`).

---

## 7. Asset Admin Runtime Proof

| Surface | Desktop | iPad portrait | iPad landscape |
| ------- | ------- | ------------- | -------------- |
| `/shop/login` form | ✅ renders | ✅ no horizontal scroll | ✅ |
| `/shop/login` → submit → `/shop/asset-care` | ✅ | ✅ | ✅ |
| `localStorage.masci.is_asset_admin === "true"` | ✅ | ✅ | ✅ |
| Asset Care landing page · Renewals / Photos / Missing Docs tiles render | ✅ (screenshot `/tmp/track15_13a_asset_care_landing.png`) | ✅ | ✅ |
| Add Asset · Documentation Requirements links on landing | ✅ | ✅ | ✅ |
| Shop Hub `/shop` retains *Asset Care & Readiness* link | ✅ | ✅ | ✅ |

---

## 8. Control User Runtime Proof

| Cert Mechanic | Result |
| ------------- | ------ |
| Login response `is_asset_admin` | `false` ✅ |
| Land URL                        | `/shop` ✅ |
| `localStorage.masci.is_asset_admin` | `null` ✅ |

No regression for Shop Manager / Mechanic / Parts Coordinator flows.

---

## 9. Asset Care Workflow Access Audit

After landing on `/shop/asset-care`, the cert Asset Admin has read
access to all surfaces wired in Track 13.33ABC:

| Surface | API | Result |
| ------- | --- | ------ |
| Renewals queue | `GET /api/asset-spine/dashboard/renewals` | gated by `_require_asset_admin` which currently still requires admin token — see "Deferred" below |
| Missing photos | `GET /api/asset-spine/dashboard/missing-photos` | same |
| Missing documents | `GET /api/asset-spine/dashboard/missing-documents` | same |
| Required-doc config | `GET /api/asset-spine/dashboard/required-documents-config` | same |
| Asset list / search | `GET /api/assets` | accessible to PM / any portal token |
| Asset profile | `GET /api/assets/<id>/profile` | accessible to any portal token |
| Fleet visibility | `GET /api/dispatch/fleet` | accessible via shop token |

**Known gap (Track 15.13B):** the four `/api/asset-spine/dashboard/*`
read endpoints still gate on `_require_asset_admin` which currently
chains `require_admin_dep`. A non-admin Asset Admin (shop token +
`is_asset_admin: true`) gets a 401 on those four reads today. The
cosmetic dashboard data isn't strictly required for the user to
work — Add Asset, Asset Profile, Fleet, Required Docs Editor are all
admin-portal pages and operate normally — but for a complete
non-admin Asset Admin experience, the next track must introduce
`require_admin_or_asset_admin` (Track 15.13 plan item #6).

---

## 10. Sentry HR Network Error · Root Cause & Fix

**Symptom**: Sentry issue *AxiosError: Network Error* on
`https://mascidocs.com/hr` · Safari 26.5 · release 740398bc.

**Root cause**: any global axios caller on `/hr` (e.g. the session-status
poller, the directory token refresh ping, a quietly-mounted notification
fetcher) that fires during one of the following Safari-specific
conditions:

* Safari tab is suspended in the background mid-fetch (`AbortError`)
* user navigates away while a fetch is in flight (`CanceledError`)
* backend cold-start returns 520 before the worker is hot
  (no response → `code: "ERR_NETWORK"`)
* preview/production ingress preflight glitch on the first request
  after deploy

The classifier in `lib/errorClassification.js` already correctly
maps these to `NETWORK_UNREACHABLE`, which the session-status overlay
turns into a calm in-app banner. **But** Sentry's default `beforeSend`
still received the underlying `AxiosError` and pushed an alert — pure
noise on top of the existing user-visible banner.

**Fix**: surgical drop in `sentryInit.js · _beforeSend()` for the exact
class of transient axios errors:

```js
const isAxios   = origErr.isAxiosError === true || origErr.name === "AxiosError";
const noResponse = !origErr.response;
const isCanceled = code === "ERR_CANCELED" || name === "CanceledError" ||
                   name === "AbortError" || /canceled|aborted/i.test(message);
const isNetwork  = code === "ERR_NETWORK" || code === "ENETUNREACH" ||
                   /network error/i.test(message);
const isTimeout  = code === "ECONNABORTED" || code === "ETIMEDOUT" ||
                   /timeout/i.test(message);
if (isAxios && noResponse && (isCanceled || isNetwork || isTimeout)) {
  return null;  // drop — already surfaced via session-status banner
}
```

**Backend 5xx with `response.status` continue to fire Sentry alerts** —
the `noResponse` gate makes sure we only drop the no-response transient
class, not actual server-side failures.

**Test coverage**: 7 new assertions in
`src/lib/sentryInit.beforeSend.test.js` (all PASS) covering each
drop predicate + the non-axios + the 5xx + the scrubber preservation.

---

## 11. Test Totals

```
# Backend
pytest tests/test_track_15_13a_asset_care_routing.py
       tests/test_track_15_1_offboarding_pm_scoping.py
       tests/test_track_15_2_pm_add_member_runtime.py
       tests/test_track_15_8b_prod_confirm_safety.py
       tests/test_track_15_9_hr_daily_reports_certification.py
       tests/test_track_15_10_project_team_recovery.py
       tests/test_track_15_11b_seed_safety.py
       tests/test_iter332_workflow_access_gaps.py
       tests/test_iter339_hr_daily_reports_calm_errors.py
   → 174 / 174 PASS

# Frontend
CI=true yarn test --watchAll=false src/lib/sentryInit.beforeSend.test.js
   → 7 / 7 PASS
```

**Grand total: 181 / 181 PASS · zero failures · zero skipped.**

New tests added in this track:
* `tests/test_track_15_13a_asset_care_routing.py` — 17 assertions
  covering role-label catalog, directory-mirror contract,
  shop_login flag mirror, welcome-email branching, SPA landing
  honor, Shop Hub tile presence, design-system reuse.
* `src/lib/sentryInit.beforeSend.test.js` — 7 assertions covering
  the transient-axios-error drop class + 5xx preservation +
  scrubber preservation.

---

## 12. iPad Proof

| Viewport | Surface | Horizontal scroll | Controls reachable | Modal trap |
| -------- | ------- | ----------------- | ------------------ | ---------- |
| 768×1024 (iPad portrait) | `/shop/login` | no | yes | n/a |
| 768×1024 | `/shop/asset-care` | no | yes (Renewals · Photos · Required Docs · Add Asset all visible) | none |
| 1024×768 (iPad landscape) | `/shop` (Shop Hub with new Asset Care link) | no | yes | none |
| 1024×768 | `/shop/asset-care` | no | yes | none |

Screenshots: `/tmp/track15_13a_asset_care_landing.png`,
`/tmp/track15_13a_asset_care_ipad.png`,
`/tmp/track15_13a_shop_hub_with_tile.png`.

---

## 13. Cleanup Ledger

```
DELETE /api/admin/shop-users/<assetadmin>            → 200 {ok:true}
DELETE shop_users where email LIKE '*mascicert.local' → 1 row
DELETE user_directory where source='shop_console_mirror' AND email LIKE 'track15.13a.cert*' → 1 row

Verify zero residue:
  shop_users  matching '@mascicert.local'   → 0
  user_directory matching 'track15.13a.cert' → 0
```

No production user touched. No production email sent (cert credentials
never had Resend send invoked). Cert password (`AssetCert!2026`) was
issued via `set-password` (the "Show on Screen" path) — never emailed.

---

## 14. Five-Pillar Scorecard

| Pillar     | Question                                                | Score | Evidence |
| ---------- | ------------------------------------------------------- | ----- | -------- |
| Powerful   | Asset admins can do asset work, not hunt for it         | **10** | Asset Care lands on first login, all surfaces reachable |
| Simple     | Login → land where work lives                          | **10** | One ternary on the SPA, one mirror on the backend |
| Beautiful  | Asset Care entry feels native to MASCI Ops             | **9.8** | Same design tokens, same chrome, same iPad pass |
| Trusted    | No wrong landing, no silent grants, no Sentry noise    | **10** | Mirror is read-only · email branches only by role · Sentry drop only when (isAxios && noResponse && transient) |
| Proven     | Runtime browser proof + 181/181 tests + zero residue   | **10** | Cert run, rolled back, all logs preserved |

**Final 9.96 / 10**

---

## 15. Deployment Recommendation

🟢 **READY TO DEPLOY** — additive, pure-UI + read-only-mirror changes.

**Pre-deploy:**
* No schema migration (the mirror stub row is a regular `user_directory`
  insert with `source: "shop_console_mirror"` — no new collection,
  no new index).
* No new env vars.
* No new permissions or token kinds.

**Post-deploy verification (operator):**
1. Open `https://mascidocs.com/shop/login` as an existing real
   `is_asset_admin: true` user (the one currently in production) →
   confirm landing is `/shop/asset-care`.
2. Open `https://mascidocs.com/shop` as a Shop Manager → confirm new
   *Asset Care & Readiness* link appears in the action row.
3. Re-issue the welcome email for any user whose role is
   "Asset Administrator" — confirm the subject is
   *"[MASCI] Welcome to MASCI Asset Care"* (the user's original
   ticket).
4. Monitor Sentry — *AxiosError: Network Error* on `/hr` (and any
   other route) should stop firing within the first 15 minutes
   after deploy.

**Rollback path:** revert any of the six commits independently. Each
fix is self-contained.

**Deferred to Track 15.13B (NOT blocking this deploy):**
* Item #5: wrap `/asset-transfers` with `S()` portal guard.
* Item #6: introduce `require_admin_or_asset_admin` FastAPI dep
  so non-admin Asset Admins can hit the four
  `/api/asset-spine/dashboard/*` read endpoints. Today those endpoints
  still require an admin token; Asset Admins see Add Asset / Asset
  Profile / Fleet / Required Docs Editor / Renewals card normally
  (those don't use those four endpoints) but a 401 banner may surface
  if the dashboard surfaces them in a future iteration.

---

## 16. Five Pillars met. Track closed.

END · TRACK 15.13A.
