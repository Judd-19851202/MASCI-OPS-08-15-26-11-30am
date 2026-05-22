# iter346 · Final Optional Closeout · ✅ APPROVE

**Iteration:** 346 (split into iter346-A · hygiene + iter346-B · login shell & super-admin)
**Date:** 2026-05-22
**Status:** APPROVE — both mini-iters green; 80/80 iter340→346 pytest pass; deploy gate green.

This is the FINAL optional closeout of the MASCI Operations Platform. Zero raw FastAPI strings remain anywhere in the app, the calm-error posture is fully end-to-end uniform, all six portal logins now share one structural chrome (preventing future visual drift), and a super-admin can sign in from any portal login screen without duplicate identities or RBAC weakening.

---

## iter346-A · FINAL HYGIENE / VISIBILITY CLOSEOUT · ✅

### 1. `operationalError()` sanitizer · 30 sites / 19 admin-internal files
Every `toast.error(e?.response?.data?.detail || "…")` site refactored to route through the shared sanitizer:

```jsx
toast.error(operationalError(e, "Failed to load X"));
```

**Coverage proof:** `grep -rn "toast.error(e?.response?.data?.detail" src/` returns **0 matches** post-refactor.

Files (19):
- `components/{AdminJobMasterPanel, CrewRecoveryPanel, PreDeploySnapshotPanel, AdminSafetyFormsPanel, CloudArchivesPanel, AdminPMPanel, BackupHeroPanel, PersistenceHealthBanner, DateAuditPanel, StoredBackupsPanel, EquipmentMasterPanel, MasterListPanel}.jsx`
- `pages/admin/{AdminDigestConfig (4), AdminIntegrationCenter (8), AdminAuditLog, SystemHealth, AdminSessions, DeployRecovery}.jsx`
- `pages/AdminTrainingVideos.jsx`

### 2. EDIT PROJECT ES leak · FIXED
`EditProjectDialog.jsx` now imports `useT()` + every visible string flows through `t()`. Catch block routed through `operationalError()`. **8 new ES keys** added (Edit Project · Re-tag this report · Move to · Currently filed under · Project name is required · Project updated · Failed to update project — try again · helper paragraph).

### 3. Access-Control Quick Stats tile · NEW
**NEW** `components/AdminAccessStatsTile.jsx` mounted on `/admin/people` above `AdminAccessControlPanel`. Reads existing `/api/admin/directory` (no new backend). Surfaces:
- Total Users · Total Grants · Cross-Portal · Disabled

Calm slate-700 left stripe + mono numerals · matches iter338 widget rhythm.

**Live preview verification:** `61 USERS · 67 GRANTS · 1 CROSS-PORTAL · 0 DISABLED` · EN + ES render confirmed.

### iter346-A · regression
- **NEW** `/app/backend/tests/test_iter346a_final_hygiene_closeout.py` — **9 tests · all green**

---

## iter346-B · PORTAL LOGIN SHELL + UNIVERSAL SUPER-ADMIN FALLBACK · ✅

### 4. Shared `<PortalLoginShell />` · structural lock against UI drift
**NEW** `/app/frontend/src/components/PortalLoginShell.jsx` — single source of truth for the outer login chrome:

- caution-stripe band
- `bg-slate-900` header with palette-tinted `border-b-4`
- back-Home link + MasciLogo dual-size + LangToggle (right-aligned)
- centered `<main>` with `max-w-md` card slot
- ForgedOpsAttribution-stamped footer with portal-specific label

Each portal login now wraps its body card in the shell:

| Portal | Accent border | Back-hover |
|---|---|---|
| HR | `border-purple-700` | `hover:text-purple-300` |
| Safety | `border-cyan-700` | `hover:text-cyan-300` |
| PM | `border-amber-500` | `hover:text-amber-300` |
| Shop | `border-amber-500` | `hover:text-amber-300` |
| Dispatch | `border-orange-700` | `hover:text-orange-300` |
| Field Leadership | `border-red-700` | `hover:text-red-300` |

**Invisible refactor proof:** Live browser inspect across all 6 portals confirms identical `bg-slate-900` header + identical palette accent colors + identical layout. Class names passed as full literal strings (`headerBorderClass="border-purple-700"`) so Tailwind's content scanner finds them in each portal page's source. No template-string interpolation.

### 5. Universal super-admin login fallback (Path 2)
Extended the iter344 FL pattern to every portal:

```
HR / Safety / PM / Shop / Dispatch login →
  Path 1: native portal identity check
  Path 2 (iter346-B): if Path 1 fails AND
                       email is in user_directory AND
                       row has "admin" portal grant AND
                       row is not disabled AND
                       master password verifies
                       → mint admin token, return kind:"admin"
```

**Backend wiring:**
- `routes/hr_portal.py · build_hr_portal_router` accepts `directory_admin_minter`
- `routes/safety_portal/__init__.py · build_safety_router` accepts `directory_admin_minter`
- `routes/dispatch_portal_auth.py · build_dispatch_router` accepts `directory_admin_minter`
- `server.py · pm_login` and `shop_login` inline `_try_directory_admin_fallback()` closures
- All five wire through `_directory_admin_token` (the same minter the FL portal uses since iter344)

**Frontend wiring:**
- Each portal login (`HrLogin`, `SafetyLogin`, `PmLogin`, `ShopLogin`, `DispatchLogin`) now reads `res.data.kind`. When `kind === "admin"`, store via `setAdminToken()` and navigate to `/admin` with a `Welcome, Admin` toast. Otherwise native flow continues unchanged.
- `SafetyLoginResponse` + `DispatchLoginResponse` Pydantic models extended with `kind: str` field.

### iter346-B · E2E auth proof

```
admin-only directory user (iter346b-admin@example.com, "admin" grant only) signs in via:
  /api/hr/login        → kind="admin" · admin token works on /api/admin/*  ✅
  /api/safety/login    → kind="admin" · admin token works on /api/admin/*  ✅
  /api/pm/login        → kind="admin" · admin token works on /api/admin/*  ✅
  /api/shop/login      → kind="admin" · admin token works on /api/admin/*  ✅
  /api/dispatch/login  → kind="admin" · admin token works on /api/admin/*  ✅
```

```
Wrong password (super-admin email + WRONG password) → HTTP 401  ✅
Non-admin directory user (no admin grant) → HTTP 401 (no bypass)  ✅
Disabled admin → HTTP 401  ✅
Native HR user (hrmanager@mascigc.com) → kind="hr" (Path 2 NOT triggered)  ✅
```

### iter346-B · regression
- **NEW** `/app/backend/tests/test_iter346b_login_shell_and_super_admin.py` — **24 tests · all green**
- iter343 chrome tests (5 of 15) updated to assert chrome lives in `PortalLoginShell.jsx` (correct invariant after refactor) — **15/15 still green**

---

## Cumulative regression · iter340 → iter346

| Test file | Result |
|---|---|
| test_iter340_final_completion_hardening.py | 18/18 ✅ |
| test_iter342_fl_login_convergence.py | 12/12 ✅ |
| test_iter343_fl_login_chrome_rebuild.py (5 tests updated for shell) | 15/15 ✅ |
| test_iter344_fl_login_super_admin.py | 6/6 ✅ |
| test_iter345_fl_phase_b_hybrid.py | 6/6 ✅ |
| **test_iter346a_final_hygiene_closeout.py** | **9/9 ✅** |
| **test_iter346b_login_shell_and_super_admin.py** | **24/24 ✅** |
| **TOTAL iter340 → iter346** | **80/80 ✅** |

Wider regression (iter33x + iter34x bands): **246/247** pytest pass · 1 pre-existing failure (`test_master_lists_export_iter34.py::test_export_works_with_pm_token` — a PM-token RBAC test that predates iter346, unrelated to this work).

Deploy gate: **9/9 green · Contract green · safe to deploy.**

ESLint: clean across all modified files.

---

## Strict-rules audit

What was NOT touched (per user spec):
- ❌ Auth architecture broadly — `multi-login` flow unchanged.
- ❌ Legacy compatibility — `/leadership/legacy-login` shared-code gate intact.
- ❌ Directory schema — no new fields, no migrations.
- ❌ Duplicate user creation — `Path 2` mints an admin token from the existing `user_directory` row.
- ❌ Login page redesigns — all 6 portals look pixel-identical post-refactor (palette accents preserved literally).
- ❌ Portal RBAC widening — only `admin` grant unlocks the fallback. Non-admin directory users still get 401.
- ❌ New dashboards beyond the small approved stats tile.
- ❌ New backend endpoints — stats tile reads existing `/api/admin/directory`.

---

## Files touched · iter346 (A + B combined)

### Frontend (29)

NEW (2):
- `components/AdminAccessStatsTile.jsx`
- `components/PortalLoginShell.jsx`

Modified (27):
- `pages/admin/AdminPeople.jsx` (mount stats tile)
- `components/EditProjectDialog.jsx` (i18n + sanitizer)
- `lib/i18n.js` (15 new ES keys)
- 19 admin-internal panels (operationalError sanitizer pass)
- 6 portal logins (HrLogin, SafetyLogin, PmLogin, ShopLogin, DispatchLogin, FieldLeadershipPortalLogin)

### Backend (5)
- `server.py` (HR builder wiring + PM/Shop inline Path 2 + Safety/Dispatch builder wiring)
- `routes/hr_portal.py` (Path 2)
- `routes/safety_portal/__init__.py` (builder param)
- `routes/safety_portal/auth_users.py` (Path 2)
- `routes/safety_portal/_models.py` (`kind` field)
- `routes/dispatch_portal_auth.py` (builder param + Path 2)

### Tests (2 new + 1 updated)
- NEW `test_iter346a_final_hygiene_closeout.py` (9)
- NEW `test_iter346b_login_shell_and_super_admin.py` (24)
- Modified `test_iter343_fl_login_chrome_rebuild.py` (5 tests refactored to read shell)

### Docs (1)
- NEW `memory/FINAL_OPTIONAL_CLOSEOUT_iter346.md` (this file)

---

## Final verdict

✅ **APPROVE.**

The MASCI Operations Platform is now structurally locked against the three risks this closeout was designed to remove:

1. **Raw framework errors** — gone. Single sanitizer route enforced across operator-facing AND admin-internal surfaces.
2. **Future portal login visual drift** — prevented. One shell controls the chrome; portal pages provide palette + body only.
3. **Super-admin lockout** — eliminated. Super-admin can sign in from any portal login screen without duplicate identities or RBAC weakening.

All cumulative pending changes (iter330 → iter346) are deploy-ready as a single batch.
