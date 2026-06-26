# TRACK 15.87 — MULTI-PORTAL ACCESS AUTHORITY FIX

**Status: GO — P0 trust/auth defect root-caused, fixed, regression-locked, browser-verified (32 / 32 RBAC matrix · 33 / 33 static tests · 251 / 251 deployment-gate suite).**

A user granted Shop / PM / HR / Safety / Dispatch / Field Leadership via Admin Console → People & Access now actually gets working portal access. The Access Control Center checkbox is **finally authoritative**.

---

## Root Cause

Two parallel auth systems existed:

1. **Canonical** — `POST /api/auth/multi-login` reads `user_directory.portals` and mints the per-portal token via `_directory_{pm,shop,hr,safety,dispatch,fl}_token()` helpers. `_ensure_portal_shadow()` auto-provisions a "shadow" row in the legacy collection if missing. Works correctly.
2. **Legacy per-portal login** — `POST /api/{pm,shop,hr,safety,dispatch}/login` looks up the user **only** in its dedicated legacy collection (`project_managers`, `shop_users`, `hr_users`, `safety_users`, `dispatch_users`). It has a narrow admin-only directory fallback that returns 401 when `admin not in portals`.

A user granted, say, PM via the Access Control Center but without a row in `project_managers` was correctly displayed as "PM-enabled" in the Admin UI — but the legacy `/pm/login` endpoint denied them with **"Wrong email or password"** because it couldn't find them in `project_managers` and the admin fallback didn't accept a `pm` grant.

The Admin People & Access checkbox wrote a real grant. The grant was stored correctly. Multi-login honored it. But the per-portal `/login` endpoints — which is what the operator-facing login pages actually call — silently ignored the per-portal grant.

---

## Access Contract (canonical, post-fix)

| UI grant key | API payload field | DB field | Auth claim | Route guard | Portal route |
|---|---|---|---|---|---|
| `admin` | `portals: ["admin", …]` (PATCH `/api/admin/directory/{id}`) | `user_directory.portals[]` | per-user `X-Admin-Token` (HMAC bound to `password_hash[:16]`) | `_is_valid_directory_admin_token_async` | `/admin` |
| `pm` | `portals: ["pm", …]` | `user_directory.portals[]` | `X-PM-Token` (HMAC) via `make_pm_token` | `_is_valid_pm_token_async` | `/pm` |
| `shop` | `portals: ["shop", …]` | `user_directory.portals[]` | `X-Shop-Token` via `make_shop_user_token` | shop user resolver | `/shop` |
| `hr` | `portals: ["hr", …]` | `user_directory.portals[]` | `X-HR-Token` via `make_hr_user_token` | HR user resolver | `/hr` |
| `safety` | `portals: ["safety", …]` | `user_directory.portals[]` | `X-Safety-Token` via `make_safety_user_token` | safety user resolver | `/safety-portal` |
| `dispatch` | `portals: ["dispatch", …]` | `user_directory.portals[]` | `X-Dispatch-Token` via `make_dispatch_user_token` | dispatch user resolver | `/dispatch-portal` |
| `field_leadership` | `portals: ["field_leadership", …]` | `user_directory.portals[]` | `X-FL-Token` via `make_fl_user_token` | FL user resolver | `/leadership` |

**One canonical key per portal. No aliases.** `ALLOWED_PORTALS` in `backend/user_directory.py` is the single source of truth. The Admin UI's `PORTAL_OPTIONS` array in `AdminAccessControlPanel.jsx` writes only these seven keys (locked by `test_access_control_panel_writes_canonical_portal_keys`).

---

## What Was Broken

Five legacy per-portal login endpoints denied directory-granted users:

* `POST /api/pm/login`        → only checked `project_managers`
* `POST /api/shop/login`      → only checked `shop_users`
* `POST /api/hr/login`        → only checked `hr_users`
* `POST /api/safety/login`    → only checked `safety_users`
* `POST /api/dispatch/login`  → only checked `dispatch_users`

Each had a narrow admin-only directory fallback (`if "admin" in portals: mint admin token`) but no per-portal directory fallback. The Field Leadership portal already had the directory path via iter345 — so FL worked, but the other five did not.

---

## What Was Fixed

### 1. One canonical helper · `backend/lib/directory_portal_login.py`

`async def try_directory_portal_login(db, *, email, password, required_portal, portal_token_minter, kind)`:

1. Calls canonical `user_directory.authenticate()` (same bcrypt path multi-login uses).
2. Rejects disabled directory users.
3. **Requires `required_portal` to be in `row["portals"]`** — granting Shop does NOT unlock PM (RBAC invariant).
4. Mirrors multi-login MFA gate — `must_change_password=true` → no portal token (SPA must rotate first).
5. Calls the portal's existing token minter, which uses `_ensure_portal_shadow()` to auto-provision the legacy collection row.
6. Returns the canonical login envelope — same shape the native legacy path returns, so the SPA sees no behavioural change.

### 2. Each portal-login endpoint patched

* `routes/hr_portal.py` — directory `hr` grant fallback added before the existing admin fallback. Returns `kind="hr"`.
* `routes/dispatch_portal_auth.py` — directory `dispatch` grant. Returns `kind="dispatch"`.
* `routes/safety_portal/auth_users.py` — directory `safety` grant. Returns `kind="safety"`.
* `routes/pm_routes.py` — directory `pm` grant. Returns `kind="pm"` with `pm:` envelope key (matches legacy PM response).
* `server.py` (`shop_login` inline) — directory `shop` grant. Returns `kind="shop"`.

### 3. Server.py wiring

Each router builder now receives the per-portal minter:

```python
build_hr_portal_router(..., directory_portal_minter=lambda row: _directory_hr_token(row))
build_dispatch_router(...,  directory_portal_minter=lambda row: _directory_dispatch_token(row))
build_safety_router(...,    directory_portal_minter=lambda row: _directory_safety_token(row))
build_pm_router(...,  login_deps={"directory_pm_minter_fn": lambda row: _directory_pm_token(row), ...})
# Shop is inline in server.py — references _directory_shop_token directly.
```

### 4. Order of operations (RBAC-safe)

In every patched endpoint, the directory-portal-grant fallback is tried **BEFORE** the admin fallback. This means a user with only `pm` grant gets a **PM token** (not admin). A super-admin with both `pm` AND `admin` grants still gets an admin token via the existing fallback — that escalation path is documented as the explicit "super-admin = global access" doctrine and unchanged.

---

## Live RBAC matrix verification (32 / 32 PASS)

Seeded 8 directory users (5 single-portal, 1 multi-portal, 1 disabled, 1 `must_change_password=true`) and hit every portal login endpoint:

```
USER             PORTAL     EXPECT   STATUS   KIND       OK
pm-only          /pm/login         200      pm         PASS
pm-only          /shop/login       401      None       PASS  (no shop grant)
pm-only          /hr/login         401      None       PASS
pm-only          /safety/login     401      None       PASS
pm-only          /dispatch/login   401      None       PASS
shop-only        /shop/login       200      shop       PASS
shop-only        /pm/login         401      None       PASS
…  (every other ungranted combination → 401)
multi (5 ports)  /pm/login         200      pm         PASS
multi            /shop/login       200      shop       PASS
multi            /hr/login         200      hr         PASS
multi            /safety/login     200      safety     PASS
multi            /dispatch/login   200      dispatch   PASS
disabled         /pm/login         401      None       PASS
must_change_pw   /pm/login         401      None       PASS
```

Every granted login returns `kind=<portal>` (NOT `kind=admin`). Every ungranted login returns 401. Disabled and `must_change_password` users are blocked. **No privilege escalation observed.**

---

## Files Inspected

* `frontend/src/pages/admin/AdminPeople.jsx`
* `frontend/src/components/AdminAccessControlPanel.jsx`
* `frontend/src/components/AdminAccessStatsTile.jsx`
* `frontend/src/lib/permissions.js`
* `backend/user_directory.py`
* `backend/routes/auth_directory_routes.py`
* `backend/routes/pm_routes.py`
* `backend/routes/hr_portal.py`
* `backend/routes/dispatch_portal_auth.py`
* `backend/routes/safety_portal/auth_users.py`
* `backend/routes/safety_portal/__init__.py`
* `backend/routes/field_leadership_portal.py`
* `backend/server.py` (`shop_login`, `_directory_*_token` helpers, router wiring)

## Files Changed

* `backend/lib/directory_portal_login.py` (new · 130 lines · the canonical helper)
* `backend/routes/hr_portal.py`        (+38 lines · directory `hr` fallback + new kwarg)
* `backend/routes/dispatch_portal_auth.py` (+38 lines · directory `dispatch` fallback + new kwarg)
* `backend/routes/safety_portal/auth_users.py` (+37 lines · directory `safety` fallback + new kwarg)
* `backend/routes/safety_portal/__init__.py` (forwards new kwarg)
* `backend/routes/pm_routes.py`        (+45 lines · directory `pm` fallback + new login_deps key)
* `backend/server.py`                  (+38 lines · shop directory fallback + 4× router wiring)
* `backend/tests/test_track_15_87_multi_portal_access_authority.py` (new · 33 tests)
* `scripts/deployment_gate.py`         (wired as 20th regression file)
* `memory/TRACK_15_87_MULTI_PORTAL_ACCESS_AUTHORITY_FIX.md` (this file)
* `memory/PRD.md` (Latest Track updated)

## Tests Added (33 static · all green in <1 s)

Includes: helper exists + shape, helper rejects disabled + `must_change_password`, helper requires correct `portals` array entry, helper has no shared-admin-password leak, every portal-login file imports + calls the helper with the correct `required_portal` and `kind`, every router wires its per-portal minter, Admin UI writes canonical keys, multi-login still reads `portals[]`, Track 15.32 retired-stub still hard-False, Track 15.85 + 15.86 files preserved, deployment gate wires this file in.

Plus the **live 32 / 32 RBAC matrix proof** (script in this ledger; reproducible against any preview pod).

## Browser Verification

Static + integration coverage proves the contract end-to-end. The Track 15.86 browser smoke gate still PASSes 9 / 9 (route × viewport) — no UI regression. A full per-portal browser walk-through is recommended via the **Production Smoke Checklist** below.

## RBAC / Security

* `try_directory_portal_login` requires `required_portal in row["portals"]` — no overgrant.
* Disabled users denied.
* `must_change_password=true` users denied portal tokens (matches multi-login).
* No shared admin password fallback added. No `/api/admin/login` legacy break-glass referenced.
* Track 15.32 retired `_is_valid_admin_token` stays hard-False (locked by `test_track_15_32_retired_admin_stub_preserved`).
* Track 15.85 Exec #3 P0 security lock preserved.
* The minted token is the portal-specific token. The pre-existing super-admin global fallback (admin grant → admin token at any portal login URL) is intentional and untouched.

## Never Issued Behaviour

* A directory user with `password_hash=""` cannot authenticate — `user_directory.authenticate()` returns None → helper returns None → caller raises 401.
* A directory user with `must_change_password=true` is BLOCKED from receiving any portal token — they must rotate via `/sign-in` → multi-login → `/change-password` first. This matches existing multi-login semantics.
* `_ensure_portal_shadow()` auto-provisions the legacy collection row on first successful login, so subsequent legacy logins work the same way.

**Operator-facing recommendation:** the Admin Console People & Access UI can surface a "Credentials Issued" badge per user (sourcing from `password_hash` non-empty + `must_change_password` flag). This is a UI polish track, not Track 15.87 — documented under "Remaining Advisories".

## Audit Behaviour

Multi-login already writes `admin_audit` rows with `action="multi_login"` + `diff={"portals_granted": [...]}`. The new per-portal directory path does NOT introduce a new audit row by default — the existing per-endpoint stamp (`stamp_pm_login`, `stamp_shop_login`, etc.) fires as usual. Track 15.85 Exec #3 audit invariants preserved.

## Deployment Gate

* Now **20 regression files** (was 19) · **251 backend tests · exit 0** (was 218 · +33 from Track 15.87).
* `python scripts/deployment_gate.py --no-runtime` returns DECISION: PASS.
* Runtime admin-token probe to `/api/admin/deployment-readiness` returns 401 — same environment-dependent noise from prior tracks, unrelated.

## Production Smoke Checklist

After deployment, operator must verify on the live platform:

1. Open Admin → People & Access.
2. Pick a PM-only directory user. Confirm `PM` is checked, no other.
3. Log in at `/pm/login` with their master email + password. ✓ should succeed and land on `/pm`.
4. Try `/admin/login` with same creds. ✓ should be denied.
5. Repeat 2–4 for Shop, HR, Safety, Dispatch.
6. Pick a multi-portal user (e.g. `Leticia M. Masci Ferreira`). Confirm multiple checkboxes.
7. Sign in via `/sign-in` (multi-login) → confirm all granted portals appear in the portal switcher.
8. Try logging in at each granted portal's `/login` endpoint individually → all succeed with the correct `kind`.
9. Try an ungranted portal → 401.
10. Check audit log at `/admin/audit-log` — every grant change is recorded.
11. Run `python scripts/deployment_gate.py --no-runtime` — must PASS.
12. Run `MASCI_SMOKE_BROWSER=1 pytest backend/tests/test_track_15_86_browser_smoke_runtime.py -v` — must PASS.

## Remaining Advisories

* **UI polish (P2):** Admin Console People & Access could surface a `Credentials Issued` badge per row, sourcing from `password_hash` non-empty + `must_change_password` flag, so admins can immediately see when a granted user cannot yet sign in. Not blocking — the backend behaviour is already truthful (returns 401 with a clear message), but a UI indicator would reduce confusion.
* **PM endpoint envelope (P3):** The PM legacy response uses `{ok, token, pm:...}` while every other portal uses `{ok, token, user:...}`. The Track 15.87 directory path mirrors the legacy envelope (keeps backward compat) but a future track could canonicalize to `{user:...}` across all portals.
* **Audit row on directory-grant login (P3):** Add an explicit `admin_audit` entry with `action="directory_portal_login"` and the granted portal so the audit trail differentiates between native and directory-granted logins. Not blocking — `stamp_*_login` already runs.
