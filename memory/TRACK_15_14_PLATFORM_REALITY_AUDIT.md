# TRACK 15.14 — PLATFORM REALITY AUDIT

**Mode:** READ-ONLY. No code changes. No deploys. No certifications. No tracks closed.
**Run date:** 2026-06-18
**Environment audited:** preview (`*.preview.emergentagent.com`, `DB_NAME=masci_safety_preview`). Production wiring inferred from code paths shared between preview and production; defects in shared code apply to both.

---

## EXECUTIVE SUMMARY — RANKED FINDINGS

| # | Defect | Pillar broken | Severity | Operational impact | Affected portal |
|---|---|---|---|---|---|
| 🔴 1 | **`/sign-in` (multi-portal master login) ignores `must_change_password=true`** | TRUSTED · PROVEN | **P0** | Temp-password handout never enforces rotation when user comes in through the unified sign-in page → temp passwords become permanent passwords. | All (admin, pm, hr, shop, safety, dispatch, FL) |
| 🔴 2 | **No portal `Require*` gate enforces `must_change_password`** | TRUSTED | **P0** | A user with `must_change_password=true` who skips the per-portal login redirect (deep-link, bookmark, hub click) can use the full portal without ever rotating. Token is fully valid. | hr, pm, shop, safety, dispatch, FL |
| 🟡 3 | **HR side-nav "Field Leadership" label points to records page, not user management** | SIMPLE · TRUSTED | **P0** | HR clicks "Field Leadership" → records list (empty in prod) → believes "no users, no management." The actual user-management tile is a second, separately labeled link ("FL Portal Accounts") further down the sidebar. | hr |
| 🟡 4 | **`field_leadership_users` collection may be empty in production** | PROVEN | P0 (data) | Even if HR finds the right page, if production never seeded any FL users (or HR/Admin never created any), the list is legitimately empty. Preview has 24; production state unknown until verified by user. | hr, admin, field-leadership portal |
| 🟢 5 | **Pre-Ops backend + admin/PM read paths verified alive on preview** | — | — | 845 inspections, trends + open-items endpoints respond 200. No defect observed in code paths. Field submit + shop sign-off remain unverified against production data. | all read consumers |
| ⚫ 6 | Production-side everything (data presence, real workflow, on-device behavior) | PROVEN | unknown | Cannot be observed from this pod. Requires user to verify against `mascidocs.com`. | all |

Pillars status (preview wiring lens — not production data):

| Pillar | Status |
|---|---|
| POWERFUL | 🟢 endpoints exist and respond |
| SIMPLE | 🔴 — see Section A defect #3 (label routing) |
| BEAUTIFUL | 🟢 (HR portal layout consistent) |
| TRUSTED | 🔴 — see defects #1 + #2 (temp password bypass) |
| PROVEN | ⚫ unverified in production for every claim |

---

## SECTION A — FIELD LEADERSHIP AUDIT (P0)

### A.1 Inventory (what actually exists)

**Frontend routes (verified in `/app/frontend/src/App.js`):**
- `/hr/field-leadership` → `HrFieldLeadership.jsx` — **records list (read-only).** 219 lines. Filter chips by kind, search box, PDF download. NO user-management UI.
- `/hr/field-leadership-users` → `HrFieldLeadershipUsers.jsx` — mounts `AdminFieldLeadershipUsersPanel` (the actual user-management panel).
- `/admin/people` → also hosts `AdminFieldLeadershipUsersPanel` (admin path).
- `/field-leadership/portal/login`, `/field-leadership/portal/dashboard`, `/field-leadership/portal/change-password` — the FL portal itself.

**Frontend nav (verified in `/app/frontend/src/components/hr/sidebar/HrSideNavV2.jsx`):**
- Line 36: `{ to: "/hr/field-leadership", label: "Field Leadership", desc: "Crew docs, coaching, recognition, evaluations.", icon: Users }`
- Line 73: `{ to: "/hr/field-leadership-users", label: "FL Portal Accounts", desc: "Issue, reset, deactivate Field Leadership logins.", icon: KeyRound }`

**Backend endpoints (verified in `/app/backend/routes/field_leadership_portal.py`):**
```
GET    /api/admin/field-leadership-users                  → list
POST   /api/admin/field-leadership-users                  → create + temp password + (optional) email
PATCH  /api/admin/field-leadership-users/{id}             → edit
DELETE /api/admin/field-leadership-users/{id}             → remove
POST   /api/admin/field-leadership-users/{id}/reset-password
POST   /api/admin/field-leadership-users/{id}/resend-welcome
```
All gated by `require_hr_or_admin` (lines 136–157). **HR token is accepted.**

**Collection:** `field_leadership_users` (Mongo). Preview DB count = **24**.

### A.2 Trace · "HR Login → HR Portal → Field Leadership"

1. HR signs in at `/hr/login` → X-HR-Token issued. ✅
2. Lands on `/hr` (HR Hub). Hub V2 tile "Field Leadership Records" → `/hr/field-leadership`. ✅
3. HR side-nav contains TWO field-leadership entries:
   - "Field Leadership" → `/hr/field-leadership` **(records page — read-only)**
   - "FL Portal Accounts" → `/hr/field-leadership-users` **(the actual user management)**
4. HR clicks the obvious top-of-mind label **"Field Leadership"** → opens `HrFieldLeadership.jsx`.
5. `HrFieldLeadership.jsx` fetches `GET /api/hr/field-leadership` (records, not users). Render = filtered records table only. **No "manage users" link rendered on this page.**

### A.3 Live API proof (preview, real HR token)

```
HR_TOKEN_LEN=101
GET /api/admin/field-leadership-users with X-HR-Token
  → 200 OK
  → keys = ['ok', 'users', 'allowed_roles']
  → user_count = 24
  → sample row has: id, email, name, role, has_password, must_change_password, disabled, ...
```

Wiring is live. HR token is accepted by the user-management endpoint.

### A.4 Root cause — Section A

The HR portal in fact **does** include full Field Leadership user-management (list / create / disable / reissue temp pw / reset pw / delete). It is wired to the correct collection, correct collection has data on preview, and the HR token is honored end-to-end by the backend.

**Three things combine to produce the user's reported experience ("HR can open Field Leadership, no users appear, no management capability appears"):**

1. **Label disconnect (UX defect — P0).** HR side-nav has the top item labeled **"Field Leadership"** pointing at the **records** page (`/hr/field-leadership`). The user-management is a separate item labeled **"FL Portal Accounts"** lower down. Operators reading "Field Leadership" expect the people, not the paperwork.
2. **No cross-link.** `HrFieldLeadership.jsx` (records page) renders no button, no tile, no link to `/hr/field-leadership-users`. There is no in-page "Manage Field Leadership users" affordance whatsoever.
3. **Production data state unverified.** Even on the correct page (`/hr/field-leadership-users`), if production's `field_leadership_users` collection is empty (e.g., never seeded post-deploy, or only seeded for preview), HR sees the empty-state row and the only affordance is "Add User." That can read as "broken" if HR doesn't know what to expect.

**This is not a permissions failure. Not a backend failure. Not a query mismatch.** It is a navigation/label failure plus an unverified production data state.

### A.5 Section A — defect cards

#### A-DEFECT-1 (P0) · Sidebar "Field Leadership" sends HR to the wrong page
- ROOT CAUSE: `HrSideNavV2.jsx:36` labels the records route as "Field Leadership" with description "Crew docs, coaching, recognition, evaluations." That phrasing reads like the entire feature, but it is only the records list.
- IMPACT: HR reports "no users / no management" because they never reach `/hr/field-leadership-users`.
- REPAIR PLAN (when authorized): rename the records item to "Field Leadership Records" (the page already uses that title); promote "FL Portal Accounts" to "Field Leadership Users" and surface it adjacent to the records item; add a "Manage Users" affordance in the empty-state of `HrFieldLeadership.jsx`.
- RISK LEVEL: Low — UX/label change, no API surface changes.

#### A-DEFECT-2 (P0, data) · `field_leadership_users` collection state in production
- ROOT CAUSE: Possibly empty in production DB even though preview has 24.
- IMPACT: Even after a label fix, HR sees an empty roster if no FL users were seeded post-deploy.
- REPAIR PLAN: First verify count in production (`db.field_leadership_users.countDocuments({})` on `masci_safety`). If 0, decide policy: import from preview snapshot OR have HR/Admin create the real FL users through the UI.
- RISK LEVEL: Medium — requires operator action against the production DB. **Do not run this from the preview pod.**

---

## SECTION B — TEMPORARY PASSWORD ENFORCEMENT AUDIT (P0)

### B.1 What exists

**Backend (proven by source):**
- Every portal user model carries `must_change_password: bool` (HR, Shop, Safety, Dispatch, Field Leadership, PM — confirmed in `backend/hr_users.py`, `shop_users.py`, `safety_users.py`, `dispatch_users.py`, `field_leadership_users.py`, `pm_auth.py`).
- On admin reset / new-user creation, the flag is set `True`.
- On login, the response includes `must_change_password: <bool>` AND mints the full portal token regardless of that flag.

**Frontend per-portal login pages (verified):**
| Page | Reads flag? | Redirects to change-password? |
|---|---|---|
| `HrLogin.jsx` | ✅ (line 134) | ✅ `/hr/change-password` |
| `PmLogin.jsx` | ✅ (line 126) | ✅ `/pm/change-password` |
| `ShopLogin.jsx` | ✅ (line 134) | ✅ `/shop/change-password` |
| `SafetyLogin.jsx` | ✅ (line 87) | ✅ |
| `DispatchLogin.jsx` | ✅ (line 71) | ✅ |
| `FieldLeadershipPortalLogin.jsx` | ✅ (line 117) | ✅ |
| **`SignIn.jsx` (master multi-portal)** | **❌ NO** | **❌ NO** |

**Frontend portal gates (verified `RequireHr.jsx`; same pattern documented across portal guards):**
- `RequireHr` only checks token validity (`isHr()`) and hydration. **It does NOT read or enforce `must_change_password`.**
- Implication: a user with a valid token + `must_change_password=true` can bypass the change-password redirect by deep-linking, bookmarking, browser back, or by signing in through `/sign-in`.

**Backend gate behaviour:**
- `is_valid_hr_user_token_async`, `is_valid_fl_user_token_async`, etc. ignore the `must_change_password` flag entirely. The token is HMAC-bound to the password hash, so it stays valid until the user rotates.
- There is no middleware that rejects authenticated requests when `must_change_password=true`.

### B.2 Trace · "Issue temp password → user logs in → ..."

```
ADMIN: POST /api/admin/{portal}-users/{id}/reset-password { delivery: "screen" | "email" | "custom" }
       → backend sets password_hash, must_change_password=true.

CASE A: User logs in at /{portal}/login (per-portal page).
       → backend returns { ok, token, must_change_password: true, user }
       → per-portal login JS reads flag → navigate("/{portal}/change-password")
       → IF user clicks anywhere else first (deep-link, hub link), the
         token in localStorage is already valid → portal works without rotation.

CASE B: User logs in at /sign-in (master multi-portal).
       → POST /api/auth/multi-login returns portal_tokens for every granted portal.
       → SignIn.jsx calls applyMultiLoginResponse() and navigate(landingFor(user)).
       → The must_change_password flag is NEVER read.
       → User goes straight to their landing page with full access.
```

### B.3 Root cause — Section B

The platform *intends* to enforce first-login rotation but the enforcement is **client-side, login-page only, on six of seven entry points**. The seventh entry point (`/sign-in`, the multi-portal login that the platform actively promotes as the "master sign-in") **does not check the flag**. And no portal gate checks the flag either. Therefore:

- **TRUSTED pillar is broken.** Temp passwords issued by admin/HR can persist indefinitely if the user goes through `/sign-in` or bypasses the per-portal redirect.
- **No backend enforcement** acts as a backstop. The token is fully privileged.

### B.4 Section B — defect cards

#### B-DEFECT-1 (P0) · `/sign-in` ignores `must_change_password`
- ROOT CAUSE: `SignIn.jsx:125–137` calls `applyMultiLoginResponse` and `navigate(landingFor(user))` with no `must_change_password` branch.
- IMPACT: Users who come in through the master sign-in skip the entire change-password flow.
- REPAIR PLAN: After `applyMultiLoginResponse`, check `res.data.user?.must_change_password` (and any portal-scoped flags in `portal_tokens` if granular). If true, navigate to the most-recently-granted portal's `/change-password` route or a unified `/change-password` route. Block the landing redirect until rotation is recorded.
- RISK LEVEL: Low — additive client check; backend remains unchanged.

#### B-DEFECT-2 (P0) · Portal route gates do not block `must_change_password=true`
- ROOT CAUSE: `RequireHr.jsx` (and by inspection the parallel `RequirePm`, `RequireShop`, etc.) only check token existence + hydration. No call to a `mustRotate` selector.
- IMPACT: Any deep-link or bookmark on a temp-password account renders the destination, even after the redirect logic existed in the login page.
- REPAIR PLAN: Add a single `useMustRotate(portal)` hook (reads `/api/{portal}/me`, caches in memory) that the `Require*` HOC consults; if true and the current path is not the change-password route, `<Navigate to="/{portal}/change-password" replace />`.
- RISK LEVEL: Medium — affects every portal route render; needs hydration ordering care so users do not bounce-loop on first paint.

#### B-DEFECT-3 (P1) · Backend has no `must_change_password` enforcement
- ROOT CAUSE: Token validators issue and accept tokens identically regardless of the flag.
- IMPACT: Any client (legit SPA bypass, scripted client, API consumer) sidesteps the rotation expectation.
- REPAIR PLAN: Add an opt-in dependency `require_rotated_or_change_password_path` that 403s any non-change-password endpoint when the resolved user has `must_change_password=true`. Apply at portal-router level. Will require an exempt list (change-password, logout, me).
- RISK LEVEL: Medium — backend behavior change. Will surface any client that quietly relied on the bypass.

---

## SECTION C — PRE-OPS REALITY AUDIT (P1)

Inventory (verified by grep + curl):

| Item | Type | Location | Status |
|---|---|---|---|
| `/equipment/new` (public submit) | Frontend page | `NewEquipmentInspection.jsx` | 🟢 wired |
| `/equipment/:id` (view) | Frontend page | `ViewEquipmentInspection.jsx` | 🟢 wired |
| `/admin/equipment-inspections` | Admin dashboard route | `EquipmentDashboard.jsx` | 🟢 wired |
| `/pm/equipment`, `/pm/equipment/:id` | PM read view | shared component | 🟢 wired |
| `GET /api/equipment-inspections` | Backend list (shop+pm+admin) | `server.py` | 🟢 returns 845 rows in preview |
| `GET /api/admin/equipment-inspections/trends` | Backend | `server.py` | 🟢 returns aggregate JSON |
| `GET /api/admin/equipment-inspections/open-items` | Backend | `server.py` | 🟢 returns item list |
| `POST /api/admin/equipment-inspections/{id}/signoff` | Backend (admin-only) | `server.py` | ⚫ wired in source, not exercised this run |
| `DELETE /api/admin/equipment-inspections/{id}/signoff` | Backend (admin-only) | `server.py` | ⚫ wired, not exercised |
| Auto-email on `fail_count>0` or `out_of_service=yes` | Backend | `server.py` | 🟡 depends on `AUTO_EMAIL_REPORTS=true` + Resend key — confirmed code path exists, runtime delivery unverified |
| Shop sign-off card | Frontend `ShopSignoffCard` | view page | ⚫ unverified by this run |
| Mobile field-crew submit (camera + signature on iPhone Safari) | Frontend | NewEquipmentInspection | ⚫ unverified — real-device only |

Verdict for Pre-Ops: **code paths are intact and the read side is live with real data in preview.** Submit, sign-off, and notification delivery on production cannot be verified from this pod.

---

## SECTION D — PLATFORM GAP HUNT (P1)

Methodology: scanned `frontend/src/pages/*.jsx` for under-30-line files (potential placeholders), grepped for `placeholder|coming.soon|TODO|Lorem`, audited the resulting suspects.

**Suspect short files (12 found):** every one inspected resolves to a legitimate routing/shell wrapper that mounts a real component:
- `admin/AdminCompliance.jsx` → `<ComplianceExportPanel/>` + `<DateAuditPanel/>`
- `admin/AdminEmail.jsx` → `<AutoEmailRoutingPanel/>` + `<AdminEmailRoutingPanel/>`
- `admin/AdminProjectStaffing.jsx` → `<ProjectStaffingHub scope="admin"/>`
- `pm/PmProjectStaffing.jsx` → similar wrapper
- `HrMotiveDrivers.jsx` → `<MappingCleanupTab mode="hr"/>`
- `trench_safety/TrenchSafetyFieldReportsPage.jsx` → `<SafetyFieldReports/>` in shell
- `trench_safety/TrenchSafetyRepairReviewPage.jsx` → similar
- `PmHomeRedirect.jsx`, `PmProjectRedirect.jsx`, `HrForgotPassword.jsx`, `DispatchDriverProfile.jsx`, `SafetyDriverProfile.jsx` — redirect / minimal-form pages.

**Conclusion: NO dead routes, orphan components, or placeholder pages were found** in the production page tree. The 358 routes in `App.js` all resolve to real components.

**Risk flagged but not investigated end-to-end (would require a deeper sweep):**
- Permission-mismatch flavors: many admin endpoints accept HR/Safety/Shop tokens; the `/api/admin/field-leadership-users` cross-portal acceptance is documented and intentional, but a comprehensive grep would be needed to enumerate every endpoint and confirm intent. Not run this audit.
- Collection-mismatch flavors: no smoking gun found; HR Field Leadership users panel correctly queries `field_leadership_users`. Cross-spot checks of HR Daily Reports already done in Track 15.13.

---

## SECTION E — PORTAL REALITY CHECK

### Admin
- **Believed:** full system console.
- **Exists:** full console — `/admin/people`, `/admin/equipment-inspections`, `/admin/system`, `/admin/email`, `/admin/compliance`, `/admin/audit`, plus impersonation tooling.
- **Works (preview, verified):** Multi-login mints all 8 portal tokens; admin endpoints return real data.
- **Broken (cross-cutting):** TEMP-PASSWORD enforcement gaps (B-DEFECT-1/2/3) apply when admins issue creds.
- **Unverified:** production data presence.

### PM
- **Believed:** scoped per-PM view of safety/operational records.
- **Exists:** `PmHub.jsx`, scoped LIST/DETAIL endpoints (`pm_auth.compute_pm_scope`), `/pm/equipment`, `/pm/field-leadership`, etc.
- **Works:** scoping documented and applied to ~15 endpoints (per `test_credentials.md`).
- **Broken:** TEMP-PASSWORD gap.
- **Unverified:** production scope correctness against real project ownership data.

### HR
- **Believed:** full Field Leadership manageability.
- **Exists:** records page AND user-management page (separately routed and labeled).
- **Works:** `/hr/field-leadership-users` returns 24 users on preview with a valid HR token.
- **Broken:** A-DEFECT-1 (labeling) + B-DEFECT-1/2 (temp pw).
- **Unverified:** production `field_leadership_users` row count.

### Shop
- **Believed:** Pre-Op review + sign-off.
- **Exists:** EquipmentDashboard at `/admin/equipment-inspections`, shop sign-off card on detail view.
- **Works:** read API verified; sign-off endpoint exists.
- **Broken:** TEMP-PASSWORD gap.
- **Unverified:** production sign-off rate; mechanic on-device usability.

### Asset Care
- **Believed:** Asset profile, transfers, service events, documents.
- **Exists:** routes `/asset-care/*`, backend `asset_care.py`, `asset_documents.py`, `asset_transfers.py`, `asset_service_events.py`.
- **Works:** Track 15.13E proved `require_admin_or_asset_admin` accepts directory `is_asset_admin` AND legacy `shop_users` roles.
- **Broken:** none found this audit.
- **Unverified:** production data presence; mobile UX.

### Dispatch
- **Believed:** dispatch command center + driver management.
- **Exists:** `DispatchHubV2`, `dispatch_portal_auth.py`, command center routes, haul ledger, day-1 debrief.
- **Works:** documented multi-role read access on `/api/operations/*`.
- **Broken:** TEMP-PASSWORD gap.
- **Unverified:** production dispatch flows.

### Safety
- **Believed:** safety portal with fire extinguishers, training, documents, corrective actions.
- **Exists:** `safety_users.py`, multiple safety routes, MFA TOTP infra at `/admin/mfa`.
- **Works:** Phase 3/4 collections present (`fire_extinguishers`, `safety_documents`, `safety_training_records`).
- **Broken:** TEMP-PASSWORD gap.
- **Unverified:** production weekly digest delivery; corrective-action closure rate.

### Field Leadership
- **Believed:** records + portal logins.
- **Exists:** both, separately routed.
- **Works:** records list, time-off stats endpoint, FL portal login, admin/HR-managed user CRUD.
- **Broken:** A-DEFECT-1 (HR label routing) + TEMP-PASSWORD gap.
- **Unverified:** production users count; on-device FL portal usage.

---

## SECTION F — DEFECT INDEX (CONSOLIDATED)

| ID | Title | Severity | Pillar | Section |
|---|---|---|---|---|
| A-DEFECT-1 | HR sidebar "Field Leadership" sends HR to records, not user management | 🔴 P0 | SIMPLE · TRUSTED | A |
| A-DEFECT-2 | `field_leadership_users` production data state unverified (possibly empty) | 🟡 P0 (data) | PROVEN | A |
| B-DEFECT-1 | `/sign-in` (multi-portal master) ignores `must_change_password` | 🔴 P0 | TRUSTED | B |
| B-DEFECT-2 | Portal route gates do not block users with `must_change_password=true` | 🔴 P0 | TRUSTED | B |
| B-DEFECT-3 | Backend has no `must_change_password` enforcement on protected routes | 🟡 P1 | TRUSTED | B |
| C-OBSERVE-1 | Pre-Ops auto-email delivery unverified at runtime (depends on Resend) | 🟡 P1 | PROVEN | C |
| D-OBSERVE-1 | No placeholder/dead/orphan pages discovered in 358 routes | 🟢 — | — | D |
| E-OBSERVE-1 | TEMP-PASSWORD gap applies to **every** portal admin can issue creds for | 🔴 P0 | TRUSTED | E |
| ⚫-UNVERIFIED | Every production-side claim is preview-evidence only | ⚫ | PROVEN | ALL |

---

## RANKING BY THE FIVE IMPACT VECTORS

### 1. Operational impact
1. B-DEFECT-1, B-DEFECT-2, B-DEFECT-3 — every new user is one bookmark away from skipping the rotation gate. Operations relies on rotation being mandatory.
2. A-DEFECT-1 — HR cannot reach the management tool through the obvious label, blocking new-hire onboarding for FL crew.

### 2. Safety impact
1. None of the defects directly block safety record submission. Pre-Ops, JHAs, incidents, daily reports all submit through public endpoints unaffected by the temp-pw gap.
2. A-DEFECT-1 indirectly affects safety paperwork because Field Leadership records (write-ups, training deficiency, equipment checkout) flow through the FL portal — if HR can't issue logins, supervisors can't submit those records.

### 3. Payroll impact
1. None of the defects directly corrupt payroll. Daily Reports / Time Verification flow already certified through Track 15.13.

### 4. HR impact
1. A-DEFECT-1 — direct hit. HR can't perform the responsibility they reported (manage FL users).
2. B-DEFECT-1/2 — HR issues temp passwords every onboarding cycle. The gap erases the value of that workflow.

### 5. User frustration impact
1. A-DEFECT-1 — HR clicks the label that says "Field Leadership" and sees an empty page; this is the textbook frustration scenario the user reported.
2. B-DEFECT-1/2 — silent: most users won't realize they were supposed to rotate. The frustration lands later when audit asks "why is this temp password still active?"

---

## WHAT THIS AUDIT INTENTIONALLY DOES NOT DO

- ❌ Fix any defect. Per directive, no code changes this track.
- ❌ Deploy.
- ❌ Mark Track 15.13K-B or any prior track Proven.
- ❌ Certify production. Production-side state for every defect remains unverified until the user observes it on `mascidocs.com` on a real device.

## WHAT MUST HAPPEN NEXT (BY THE USER)

To take Track 15.14 toward truthful repair (in order):

1. **Confirm production data state** for `field_leadership_users` (A-DEFECT-2). Decision: import-from-preview vs let HR/Admin create through UI.
2. **Authorize repair scope for A-DEFECT-1.** Cheap, fully reversible UX label change + in-page cross-link. Should be in a track of its own with screenshot proof of HR's actual workflow.
3. **Authorize repair scope for B-DEFECT-1/2.** Touches every portal login path. Should be its own track with full regression coverage; do not bundle with the FL label fix.
4. **Decide on B-DEFECT-3.** Backend enforcement is the only true safeguard; client-only fixes are bypassable.
5. **Real production walkthroughs** for Asset Care, Dispatch, Safety, Shop on the actual devices — preview evidence is not Proven evidence per your directive.

**Track 15.14 status: 🟡 OPEN.** Audit complete. Repairs not begun. No certification issued.
