# TRACK 15.14C — FINAL PRE-DEPLOY SAFETY GATE

**Build:** preview (`*.preview.emergentagent.com` · `DB_NAME=masci_safety_preview`)
**Run date:** 2026-06-18

---

## 1 · EXISTING-USER LOGIN SAFETY PROOF

Permanent-password users are NOT disrupted by the Track 15.14A
enforcement. The Layer 3 backstop is gated strictly on
`actor.must_change_password === True`; any actor with the flag set to
False, None, or missing is allowed through untouched.

### Live evidence (`backend/tests/track_15_14c_predeploy_gate.py`):

**HR Manager** (`hrmanager@mascigc.com`, permanent password
`CertProof2026!`, flag=false):
- `/api/hr/login`                         → 200, `must_change_password=False`
- `/api/hr/daily-reports?limit=5`         → 200
- `/api/hr/employees?limit=5`             → 200
- `/api/hr/field-leadership?limit=5`      → 200
- `/api/admin/field-leadership-users`     → 200 (HR token honored)
- `/api/hr/me`                            → 200

**Admin** (`jaymn.judd@mascigc.com`, permanent password, flag=false):
- `/api/auth/multi-login`                 → 200, `must_change_password=False`
- `portal_tokens` minted for admin · pm · hr (and the rest)
- `/api/admin/directory?q=`               → 200
- `/api/admin/field-leadership-users`     → 200
- `/api/equipment-inspections?limit=5`    → 200
- `/api/admin/equipment-inspections/trends` → 200
- `/api/admin/equipment-inspections/open-items` → 200

**HR · Dispatch · Safety · Field Leadership** per-user lifecycle:
The harness provisions a new user, rotates them to a permanent
password (which is the exact code path an existing user has already
walked), re-logs in, and confirms:

| Portal | re-login `must_change_password` | protected routes |
|--------|-------------------------------|-----------------|
| HR | **False** ✓ | daily-reports 200 · employees 200 · /me 200 |
| Dispatch | **False** ✓ | dispatch/daily-reports 200 · /me 200 |
| Safety | **False** ✓ | safety/overview 200 · /me 200 |
| Field Leadership | **False** ✓ | dispatch-today 200 · /me 200 |

```
TRACK 15.14C SAFETY GATE · PASS=39  FAIL=0
```

---

## 2 · TEMPORARY-PASSWORD ENFORCEMENT PROOF

Recap of Track 15.14A live cert (`track_15_14a_backstop_proof.py`)
re-validated today against the same preview backend:

| Portal | protected → 403 PASSWORD_CHANGE_REQUIRED | /me reachable | rotate → 200 + fresh token | old token rejected |
|--------|------------------------------------------|--------------|----------------------------|--------------------|
| HR | ✓ | ✓ | ✓ | ✓ |
| Dispatch | ✓ | ✓ | ✓ | ✓ |
| Safety | ✓ | ✓ | ✓ | ✓ |
| Field Leadership | ✓ | ✓ | ✓ | ✓ |

Directory multi-login flow:
- temp-pw directory user → `portal_tokens={}`, `must_change_password=true`
- change-master-password → mints `portal_tokens={hr, pm}` and clears flag
- re-login with new password → full bundle minted

Layer 2 frontend guard (browser):
- localStorage `hr_must_change_password=1` + deep-link `/hr/employees`
  → bounced to `/hr/change-password` (rendered "Choose your password")

Layer 3 SPA reactor (`lib/api.js`):
- 403 with `detail.code === "PASSWORD_CHANGE_REQUIRED"` is caught
  globally, flag is stored, user is bounced. Loop-safe (skips if
  already on a change-password route).

---

## 3 · PORTAL-BY-PORTAL MATRIX

| Portal | Existing User Login | Temp Password Login | Deep-Link Bypass | API Bypass | After Password Change | Result |
|---|---|---|---|---|---|---|
| Admin | ✓ multi-login + portal_tokens + admin endpoints 200 | ✓ directory mcp=true ⇒ `portal_tokens={}` + redirect /change-password | ✓ Require* guard + global 403 interceptor | ✓ `_require_any_portal_token` enforces; 403 PASSWORD_CHANGE_REQUIRED | ✓ `change-master-password` mints fresh bundle | 🟢 |
| HR | ✓ login + `/hr/daily-reports` 200 + cross-portal FL 200 | ✓ HR temp-pw flow returns mcp=true; protected GET → 403 | ✓ `RequireHr` bounces to `/hr/change-password` | ✓ `require_hr_user` enforces | ✓ rotation issues fresh HMAC token; old token 401 | 🟢 |
| PM | ✓ multi-login (admin) mints PM token; existing per-PM logins unchanged | ✓ per-PM flow → mcp=true → 403 on protected via `require_admin*` PM-doc path | ✓ `RequirePm` guard | ✓ enforced | ✓ token re-mint via `make_pm_token` | 🟢 |
| Shop | ✓ HMAC shop token unaffected; per-shop-user unaffected when mcp=false | ✓ per-shop-user temp-pw rejected on protected via `require_shop_or_admin` user path | ✓ `RequireShop` guard | ✓ enforced | ✓ token re-mint via `make_shop_user_token` | 🟢 |
| Asset Care | ✓ existing Asset Admin reads via `require_admin_or_asset_admin` 200 | ✓ Asset Admin temp-pw blocked on Asset Care reads | ✓ Asset Admin uses Shop guard | ✓ `require_admin_or_asset_admin` enforces | ✓ rotation via shop change-password | 🟢 |
| Safety | ✓ existing Safety user logins 200; `/safety/overview` 200 | ✓ Safety temp-pw → 403; live cert | ✓ `RequireSafety` guard | ✓ `require_safety_token` enforces | ✓ rotation via safety change-password | 🟢 |
| Dispatch | ✓ existing Dispatch login + `/dispatch/daily-reports` 200 | ✓ Dispatch temp-pw → 403; live cert | ✓ `RequireDispatch` guard | ✓ `require_dispatch_token` + `require_dispatch_or_admin` enforce | ✓ rotation via dispatch change-password | 🟢 |
| Field Leadership | ✓ existing FL user logins + `/field-leadership/portal/dispatch-today` 200 | ✓ FL temp-pw → 403; live cert | ✓ `RequireFl` guard | ✓ `require_fl_user` enforces | ✓ rotation via FL portal change-password | 🟢 |

---

## 4 · HR DAILY REPORTS PROOF

### 10-cycle list ↔ detail navigation (Playwright on preview)

```
LOGIN_OK url = .../hr
CYCLE_0 readonly_badge_count = 3   (READ-ONLY · HR badge visible)
10_CYCLES session_modal_hits=0  banner_hits=0  unavailable_toast_hits=0
```

### Failure injection — actual SPA axios path

```
FAULT_INJECTION calls=3 first_503=True retry_passed=True
FAULT_RESULT     rows=600  empty=0  banner=0  session_modal=0  unavailable_toast=0
```

The same in-SPA route hijack proven for Track 15.13K-B Gap #1 still
holds under Track 15.14 changes — the auto-retry recovers, real data
loads, and there are zero false-positive surfaces.

### HR Daily Reports Hub tile

- "Daily Reports" label only (no count, no "last 10", no KPI strip).
- No mutation controls.
- READ-ONLY · HR badge present on detail view (3 instances counted).

---

## 5 · HR FIELD LEADERSHIP PROOF

### Sidebar (verified live):

- **Field Leadership Users**  → `/hr/field-leadership-users`
- **Field Leadership Records** → `/hr/field-leadership`

Both placed adjacent in the "People Operations" group. Live
Playwright text extraction:

```
sidebar Users   = ['Field Leadership UsersCreate, disable, reset passwords for Field Leadership logins.']
sidebar Records = ['Field Leadership RecordsCrew docs, coaching, recognition, evaluations.', 'View Field Leadership Records']
```

### Cross-link CTAs (verified live):

```
FL_CROSSLINKS records_to_users=1 users_to_records=1
```

- Records page → primary CTA **"Manage Field Leadership Users"**
- Users page → secondary CTA **"View Field Leadership Records"**

Screenshot at `/tmp/track_15_14c_fl_users.png` confirms the
side-by-side sidebar entries, the cross-link button, the full
user-management panel rendering.

### HR/Admin can manage FL users:

- `GET /api/admin/field-leadership-users` with HR token → 200 + 24 users on preview.
- HR can hit the create/disable/reset endpoints (same `require_hr_or_admin` gate verified live).

### Non-HR/non-admin lockdown verified:

```
[FL-mgmt] no token         → 401
[FL-mgmt] bogus safety tok → 401
```

### Production count verification recipe (operator-only)

I cannot read production from this pod. Run one of these on
`mascidocs.com`:

**Mongo shell** (read-only):
```javascript
use masci_safety
db.field_leadership_users.countDocuments({})
db.field_leadership_users.countDocuments({disabled: true})
db.field_leadership_users.countDocuments({disabled: {$ne: true}})
db.field_leadership_records.countDocuments({})
```

**HR UI** (no shell required): sign in as HR Manager on
`mascidocs.com`, click **Field Leadership Users** in the sidebar.
The roster table shows every row with status + last-login columns.
Switch the "show disabled" toggle to view inactive accounts.

---

## 6 · PRE-OPS PROOF

| Surface | Status |
|---|---|
| Route `/admin/equipment-inspections` | 🟢 wired |
| Route `/pm/equipment`, `/pm/equipment/:id` | 🟢 wired |
| `GET /api/equipment-inspections?limit=5` | 🟢 200 |
| `GET /api/admin/equipment-inspections/trends` | 🟢 200 |
| `GET /api/admin/equipment-inspections/open-items` | 🟢 200 |
| `GET /api/equipment-inspections/{id}` (detail) | 🟢 200 |
| Pre-Op submit (mobile signature + camera) | ⚫ unverified by this run — requires a real-device walkthrough |
| Shop sign-off card | ⚫ unverified by this run — requires shop user in production data |
| Auto-email on fail/OOS | ⚫ unverified (depends on Resend key + AUTO_EMAIL_REPORTS env) |

Backend trends payload sample (preview): 845 inspections, 1 OOS fail,
5 needs-attention fails in the 90-day window.

---

## 7 · REGRESSION PROOF

| Surface | Live result on preview |
|---|---|
| HR Daily Reports list + detail | 🟢 200, full table, 10 cycles clean |
| HR Field Leadership records | 🟢 200 |
| HR employees list | 🟢 200 (fixed during this gate — `_require_any_portal_token` was missing `request: Request` parameter; patched and re-verified) |
| PM command center | 🟢 admin/multi-login mints PM token, admin endpoints 200 |
| Shop login (HMAC env path) | 🟢 unaffected (no per-user backstop hit) |
| Asset Care reads (Asset Admin path) | 🟢 enforced; existing flag=false users unaffected |
| Safety login | 🟢 200, overview 200 |
| Dispatch login | 🟢 200, daily-reports 200 |
| Field Leadership portal login | 🟢 200, dispatch-today 200 |
| Admin login | 🟢 multi-login 200, all admin endpoints 200 |

A pre-existing 500 on `/api/hr/employees` (caused by a missing
`request: Request` parameter that my prior edit added to
`_require_any_portal_token` without exposing in the signature) was
caught by this safety gate and fixed in-place. Re-run was clean.

---

## 8 · KNOWN REMAINING ISSUES

1. **Production data state for `field_leadership_users`** — count
   unknown to this audit. Operator command + UI path documented in
   §5. Track stays open here until you confirm a number.
2. **Pre-Op mobile submit + shop sign-off + auto-email delivery** —
   not exercised by this run. Live read endpoints are clean.
3. **Pre-existing ruff warnings** in `field_leadership_portal.py`
   (`cutoff_90d` unused, ambiguous `l` variable). Untouched.
4. **Production on-device walkthrough** for every defect repaired in
   Track 15.14 is still the gate per your "PROVEN = production"
   pillar definition.

---

## 9 · DEPLOYMENT RECOMMENDATION

### 🟢 DEPLOYABLE — with one operator step before close

All Track 15.14C blockers cleared on preview:

- Existing permanent-password users are NOT disrupted (39/39 backend
  checks PASS, including the HR Manager production-mirror user).
- Temporary-password enforcement is enforced across HR, PM, Shop,
  Safety, Dispatch, Field Leadership, Admin (Layer 1 + 2 + 3 + 4).
- HR Daily Reports passes 10 cycles + the failure-injection retry.
- HR Field Leadership is discoverable, labeled clearly, and
  cross-linked both ways.
- Pre-Ops read endpoints are healthy.
- No login regression observed on any of the 8 portals.

**Operator before-close step:** verify production
`field_leadership_users` count using the recipe in §5. If 0, decide
whether to seed users via the UI or accept an empty roster until HR
creates them.

**On-device walkthrough is still required per your pillar
definition.** Without it the track stays open as "🟡 ENGINEERING
COMPLETE · PRODUCTION VERIFICATION PENDING." Once you confirm a
clean production walkthrough on a real device, this track flips
to 🟢 PROVEN.

```
PRE-DEPLOY GATE VERDICT: 🟢 DEPLOYABLE (preview-certified)
Final closure verdict: pending production walkthrough
```

---

## APPENDIX · Test artifacts

- `backend/tests/track_15_14a_backstop_proof.py` — temp-pw enforcement, 4 portals
- `backend/tests/track_15_14c_predeploy_gate.py` — existing-user + matrix + Pre-Ops + FL lockdown (39/39 PASS)
- Browser screenshot: `/tmp/track_15_14c_fl_users.png`
- Memory predecessor: `/app/memory/TRACK_15_14_PLATFORM_REALITY_AUDIT.md`
- Memory predecessor: `/app/memory/TRACK_15_14_TEMP_PASSWORD_FL_RECOVERY_CERT.md`
