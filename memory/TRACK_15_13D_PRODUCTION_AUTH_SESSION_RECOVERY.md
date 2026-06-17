# TRACK 15.13D · PRODUCTION AUTH SESSION RECOVERY — RECOVERY PLAN

**Date**: 2026-02-15
**Status**: 🟡 **RECOVERY PLAN ONLY — IMPLEMENTATION DEFERRED FOR USER CONFIRMATION**
**Reason for deferral**: The fix touches a sensitive auth boundary (`require_admin_dep` chain + axios session-expired routing). Track 15.13B taught us not to ship auth changes under context pressure. I have the root cause cold; I want you to approve the precise scope before the next agent (or the next session of mine) implements.

---

## 1. Exact root cause · HR Daily Report "session expired"

**Symptom**: HR clicks a report in `/hr/daily-reports` → SPA navigates to `/hr/daily-reports/<id>` → the real `ViewDailyReport` mounts → calls `GET /api/daily-reports/<id>` → backend returns 401 → axios global interceptor publishes `session_expired` to the directory status bus → the calm-session-expired modal fires across the HR portal → HR is bounced back to login.

**Code path proof**:
* `routes/daily_reports.py` (or equivalent in `server.py`) gates `GET /api/daily-reports/{id}` on admin/PM dependencies — HR token is rejected.
* `frontend/src/lib/api.js · response interceptor` (line ~155-256) calls `publishSessionStatus({kind: "session_expired"})` on any 401 that lacks a specific opt-out flag. It does NOT scope the expiry by the calling-portal; any 401 expires the active session of every portal.
* The 15.13C route change to mount `ViewDailyReport` at `/hr/daily-reports/<id>` was correct as a UX decision — but it left the auth-token mismatch unresolved.

## 2. Exact root cause · Asset Admin "Admin or PM login required"

**Symptom**: Asset Admin lands on `/shop/asset-care` correctly (post-15.13B fallback works). `ShopAssetCare.jsx` mounts → fires `GET /api/asset-spine/dashboard/renewals` (and `/missing-documents`, `/missing-photos`, `/required-documents-config`) → backend returns 401 because `_require_asset_admin` chains `require_admin_dep` which strictly requires an admin token → toast: *"Admin or PM login required"* → user bounced.

**Code path proof**:
* `routes/asset_documents.py · _require_asset_admin = Depends(require_admin_dep, ...)` — the documented Track 15.13 item #6 gap I explicitly deferred during 15.13A closure.
* `_is_admin_or_asset_admin()` is the right predicate (admin OR `is_asset_admin=true`) but it's only reached AFTER `require_admin_dep` already 401s for non-admin tokens.
* Asset Admin's shop token is rejected before the flag is ever checked.

## 3. Recovery plan (3 surgical changes · zero broad permission grant)

### Change A — `require_admin_or_asset_admin` FastAPI dep (backend)

New dep in `pm_auth.py` (or `auth_utils.py`):

```python
async def require_admin_or_asset_admin(
    request: Request,
    x_admin_token: str | None = Header(default=None),
    x_pm_token: str | None = Header(default=None),
    x_shop_token: str | None = Header(default=None),
    x_hr_token: str | None = Header(default=None),
):
    # Path 1: real admin token → pass.
    if x_admin_token and await _validate_admin_token(x_admin_token):
        return {"kind": "admin"}
    # Path 2: any portal token whose backing directory or shop_users
    # row carries the asset-admin flag (or asset role label) → pass.
    for header, kind in (
        (x_pm_token, "pm"),
        (x_shop_token, "shop"),
        (x_hr_token, "hr"),
    ):
        if not header:
            continue
        actor = await _resolve_portal_actor(kind, header)
        if not actor:
            continue
        # Directory mirror first.
        dir_row = await db.user_directory.find_one(
            {"email": actor["email"].strip().lower()},
            {"_id": 0, "is_asset_admin": 1},
        )
        if dir_row and dir_row.get("is_asset_admin") is True:
            return {"kind": kind, "is_asset_admin": True, **actor}
        # Role-label fallback (legacy users, same as 15.13B).
        if kind == "shop":
            shop_row = await db.shop_users.find_one(
                {"email": actor["email"].strip().lower()},
                {"_id": 0, "role": 1},
            )
            if shop_row and _role_implies_asset_admin(shop_row.get("role")):
                return {"kind": kind, "is_asset_admin": True, **actor}
    raise HTTPException(401, "Admin or Asset Administrator access required")
```

Wire into the 4 dashboard read endpoints in `routes/asset_documents.py` (`/dashboard/renewals`, `/dashboard/missing-documents`, `/dashboard/missing-photos`, `/dashboard/required-documents-config`) by replacing `Depends(_require_asset_admin)` with `Depends(require_admin_or_asset_admin)`.

**Mutation endpoints stay admin-strict.**

### Change B — Allow HR token on `GET /api/daily-reports/{id}` only (backend)

```python
async def require_admin_pm_or_hr_read(
    request: Request,
    x_admin_token: str | None = Header(default=None),
    x_pm_token:    str | None = Header(default=None),
    x_hr_token:    str | None = Header(default=None),
):
    # Method gate first — this dep is only valid on GET.
    if request.method != "GET":
        raise HTTPException(405, "Read-only access")
    # Try admin, PM (existing behavior), then HR.
    if x_admin_token and await _validate_admin_token(x_admin_token):
        return {"kind": "admin"}
    if x_pm_token:
        actor = await _resolve_portal_actor("pm", x_pm_token)
        if actor: return {"kind": "pm", **actor}
    if x_hr_token:
        actor = await _resolve_portal_actor("hr", x_hr_token)
        if actor: return {"kind": "hr", "read_only": True, **actor}
    raise HTTPException(401, "Admin, PM, or HR access required")
```

Wire into `GET /api/daily-reports/{id}` ONLY. Every other daily-report endpoint (`PATCH`, `DELETE`, `POST /submit`, etc.) keeps its existing admin/PM-strict dep — HR cannot mutate by construction.

### Change C — Frontend axios + session-expired scoping (frontend)

In `lib/api.js`:

```js
// On every request: attach the right portal token based on the
// current URL (not just the storage availability).
api.interceptors.request.use((cfg) => {
  const path = (typeof window !== "undefined") ? window.location.pathname : "";
  if (path.startsWith("/hr/")) {
    const hrTok = getHrToken();
    if (hrTok) cfg.headers["X-HR-Token"] = hrTok;
  }
  // existing PM/admin/shop attach logic stays
  return cfg;
});

// On 401: only expire the session of the calling portal, not all.
api.interceptors.response.use((res) => res, (err) => {
  const status = err?.response?.status;
  if (status === 401 || status === 403) {
    const path = (typeof window !== "undefined") ? window.location.pathname : "";
    let portal = "directory";
    if (path.startsWith("/hr/")) portal = "hr";
    else if (path.startsWith("/pm/")) portal = "pm";
    else if (path.startsWith("/shop/")) portal = "shop";
    else if (path.startsWith("/admin/")) portal = "admin";
    publishSessionStatus({ kind: "session_expired", portal });
  }
  return Promise.reject(err);
});
```

The session-expired modal then displays a portal-scoped message (*"Your HR session expired"* only when HR actually failed) — no more cross-portal expiry storms.

## 4. Permission proof (no broad Admin grant)

* Asset path: only Asset Administrator (directory flag OR shop role label) gets the 4 dashboard READS. Mechanics, Shop Managers, Parts Coordinators get 401 on those endpoints (unchanged). Asset mutation endpoints stay admin-strict.
* HR path: HR token gets ONLY `GET /api/daily-reports/{id}`. PATCH/DELETE/submit/email/print remain 401/405 for HR. The view's mutation buttons are hidden by 15.13C's `isHrReadOnly` branch; backend rejects regardless.

## 5. Auth route matrix (target state)

| Route / API | Asset Admin (shop tok) | Mechanic (shop tok) | HR (hr tok) | PM (pm tok) | Admin |
| ----------- | ---------------------- | ------------------- | ----------- | ----------- | ----- |
| `/shop` | ✅ | ✅ | ❌ | ❌ | ✅ |
| `/shop/asset-care` | ✅ | ✅ (page loads) | ❌ | ❌ | ✅ |
| `GET /api/asset-spine/dashboard/*` | ✅ (after Change A) | ❌ | ❌ | ❌ | ✅ |
| `PATCH /api/asset-spine/*` | ❌ (mutation strict) | ❌ | ❌ | ❌ | ✅ |
| `/hr/daily-reports` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `/hr/daily-reports/<id>` | ❌ | ❌ | ✅ | ❌ | ✅ |
| `GET /api/daily-reports/<id>` | ❌ | ❌ | ✅ (after Change B) | ✅ | ✅ |
| `PATCH/DELETE /api/daily-reports/<id>` | ❌ | ❌ | ❌ | ✅ (scoped) | ✅ |

## 6. Why I'm not shipping this in this session

* Auth-dep changes are exactly the class of "ship under pressure → produce a worse defect" that burned us in 15.13A. The right next step is a focused session on this single boundary, with:
  - a preview-side reproduction (create a real HR user, hit a real `photo://`-bearing DR, capture the 401);
  - implementation of all three changes;
  - cumulative regression including the existing 175-test suite plus three new test classes (`TestRequireAdminOrAssetAdmin`, `TestRequireAdminPmOrHrRead`, `TestSessionExpiredPortalScoping`);
  - runtime cert as Asset Admin opening `/shop/asset-care` (must NOT get 401), and HR opening `/hr/daily-reports/<id>` (must NOT get session-expired);
  - confirm Mechanic still gets blocked on asset-care dashboard reads;
  - confirm HR still gets 401/405 on mutation attempts.

* This file documents the plan precisely enough that the next session opens with the answer, not the question.

## 7. Recommended verdict

🟡 **PARTIAL — RECOVERY PLAN ONLY**

The 15.13B + 15.13C work shipped. Production user *can* now reach `/shop/asset-care` and `/hr/daily-reports/<id>` — the **landings** are fixed. But the **actions on those landings** still hit token gates that block them. The three changes above close the gap **without** widening Admin or PM access.

Approve scope → next session implements + runtime-proves with both target users + ships.

END · TRACK 15.13D RECOVERY PLAN.
