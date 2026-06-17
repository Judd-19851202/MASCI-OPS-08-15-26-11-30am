# ASSET ADMIN RUNTIME TRACE · TRACK 15.13B

**Date**: 2026-02-15
**Trace target**: legacy Asset Administrator created BEFORE Track 15.13A landed — i.e. carrying only a `shop_users` row, no `user_directory` row.

---

## Step 1 — Provisioning state (pre-15.13A)

```
db.shop_users:
  { id: "...", email: "<asset admin email>", name: "...",
    role: "Asset Administrator", password_hash: "<bcrypt>",
    must_change_password: false }

db.user_directory:
  (no row — never created)
```

## Step 2 — `POST /api/shop/login`

**Pre-fix (15.13A)**: lookup `user_directory` by email → `None` → `is_asset_admin = false` → response landing flag = false → SPA routes to `/shop`. **🔴 WRONG**.

**Post-fix (15.13B)**: lookup `user_directory` by email → `None` → BUT the new fallback fires:

```python
if not is_asset_admin and _role_implies_asset_admin(user.get("role")):
    is_asset_admin = True
```

`_role_implies_asset_admin("Asset Administrator")` returns `True` → response carries `is_asset_admin: true` → SPA reads the flag → SPA navigates to `/shop/asset-care`. **🟢 CORRECT**.

### Live preview trace (post-fix)

```
$ curl POST /api/shop/login {"email":".../legacy.assetadmin/...", "password":"..."}
{
  "ok": true,
  "token": "...",
  "kind": "shop",
  "must_change_password": false,
  "user": {
    "id": "cert-legacy-assetadmin-01",
    "email": "track15.13b.legacy.assetadmin@mascicert.local",
    "name": "Legacy Asset Admin",
    "role": "Asset Administrator",
    "is_asset_admin": true                ← role-label fallback fired
  },
  "is_asset_admin": true                  ← top-level flag for the SPA
}
```

`db.user_directory.find_one({email: "track15.13b.legacy.assetadmin@mascicert.local"})` returned `None` — proving the fallback is what produced the `true` flag, not the directory mirror.

## Step 3 — SPA routing

```
ShopLogin.jsx line ~129:
  isAssetAdmin = res.data?.is_asset_admin === true || res.data?.user?.is_asset_admin === true
              → true
  localStorage.setItem("masci.is_asset_admin", "true")
  intended = location.state?.from || (isAssetAdmin ? "/shop/asset-care" : "/shop")
              → "/shop/asset-care"
  navigate(intended, { replace: true })
```

The SSO hook destination (`useRedirectIfDirectoryGrant`) re-reads
`localStorage.masci.is_asset_admin` after the flag is set and reuses the same
`"/shop/asset-care"` destination — no race.

## Step 4 — Landing page (`/shop/asset-care`)

Token gate (`<RequireShop>`) checks `isShop()` which reads
`masci.shop.token` from storage. The token was just set by
`setShopToken(res.data.token, { remember })` — passes.

`ShopAssetCare.jsx` mounts. Renewals + Photos + Required Docs + Add Asset
all render via existing 13.33ABC code paths.

---

## Cleanup ledger (this trace)

```
DELETE shop_users WHERE email = "track15.13b.legacy.assetadmin@mascicert.local"
  → 1 row removed
```

Zero residue.

END · ASSET ADMIN RUNTIME TRACE.
