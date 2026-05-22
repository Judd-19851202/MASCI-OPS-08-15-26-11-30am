# FL LOGIN UX CONVERGENCE — iter342

**Date:** 2026-05-22
**Operator complaint:** `/leadership/login` was still rendering the legacy single shared-password gate while every other portal (HR, Safety, PM, Shop, Dispatch) had modern email+password. The FL portal felt "built differently" — broke platform-family feel.
**Verdict:** ✅ **CONVERGED**

---

## Exact root cause

The platform had **two FL login surfaces simultaneously**:

| URL | What it rendered | Auth model | Visual feel |
|---|---|---|---|
| `/leadership/login` (PRIMARY operator-visible surface) | `LeadershipLogin.jsx` (Pass 4 / pre-iter314 build) | **Shared MASCIGC password** | Red theme · single password field · "Leadership Password" label · explicitly stated "Uses a shared leadership password" |
| `/field-leadership/portal/login` (SECONDARY surface) | `FieldLeadershipPortalLogin.jsx` (iter314) | **Per-user email + password** | Modern slate-800 · MasciLogo · email + PasswordInput · forgot-password modal · matches HrLogin exactly |

The MODERN per-user login was **already built, working, and fully calm** — it just lived at the wrong URL. Operators following the natural URL pattern (or any link from the Hub) hit the legacy gate. **The convergence gap was visibility, not architecture.**

---

## Previous architectural state (pre-iter342)

- Two collections: `field_leadership_users` (per-user · iter314 · used by FieldLeadershipPortalLogin) + the shared leadership password (legacy · used by LeadershipLogin)
- Two tokens: `masci.fl.token` (per-user FL portal · stored in localStorage) + `masci.leadership.token` (shared legacy · stored in sessionStorage)
- Hub (`FieldLeadershipHub.jsx`) gate only checked `getLeadershipToken() || isAdmin() || getPmToken()` — did NOT recognize the modern FL token
- `/leadership/login` route mounted `LeadershipLogin` (legacy shared-password)
- `/field-leadership/portal/login` route mounted `FieldLeadershipPortalLogin` (modern per-user)
- Backend `/api/field-leadership/login` (shared pw) + `/api/field-leadership/portal/login` (per-user) — both routes alive, both serving correctly

---

## New converged auth model (iter342)

| URL | What it renders NOW | Notes |
|---|---|---|
| `/leadership/login` (PRIMARY) | `FieldLeadershipPortalLogin` (MODERN per-user email + password) | Operators land here naturally. Matches HrLogin chrome. |
| `/leadership/legacy-login` (HIDDEN COMPAT) | `LeadershipLogin` (legacy shared password) | Reachable only via the small disclosure link on the modern form for crews who still know only the shared MASCIGC code. |
| `/field-leadership/portal/login` (PRESERVED COMPAT) | `FieldLeadershipPortalLogin` | Still works — existing bookmarks resolve. |

**Hub now accepts EITHER token:**
```jsx
() => Boolean(getLeadershipToken()) || Boolean(getFlToken()) || isAdmin() || Boolean(getPmToken())
```

**Sign-out clears BOTH tokens** — no ghost sessions across legacy + modern.

**Post-login destination:** modern FL login now navigates to `/leadership` (the Hub) on success, collapsing the previous two-step "portal-dashboard → hub" navigation into one calm landing.

---

## Compatibility strategy

| Layer | Change | Risk |
|---|---|---|
| Backend `/api/field-leadership/login` (shared-pw) | **UNTOUCHED** | None — legacy crews still log in |
| Backend `/api/field-leadership/portal/login` (per-user) | **UNTOUCHED** | None |
| `lib/leadershipAuth.js` | **UNTOUCHED** | None |
| `lib/flAuth.js` | **UNTOUCHED** | None — already exposed `getFlToken`, `clearFlToken` |
| `field_leadership_users` collection | **UNTOUCHED** | None — 1 existing user (`fieldleader@mascigc.com`) keeps working |
| Frontend App.js routes | 1 line swap + 1 new route | Bounded |
| `FieldLeadershipPortalLogin.jsx` | Added disclosure link + redirect to `/leadership` | Bounded |
| `FieldLeadershipHub.jsx` | Auth check accepts FL token + signOut clears it | Bounded |
| `lib/i18n.js` | 1 ES translation key added | Bounded |

**No duplicate identities created. No destructive auth rewrites. No data migration. Zero risk to existing FL users.**

---

## Admin grant behavior

**Unchanged in this iter:**
- Admin Access Control Center continues to manage 6 portal grants (admin / pm / shop / hr / safety / dispatch) via `user_directory`
- FL users continue to be managed via the dedicated `field_leadership_users` panel at `/admin/people` → "Field Leadership Users & Logins" (preserved from iter314)
- HR also can manage FL users via `/hr/field-leadership-users` (per iter314 shared-panel design)

**FL Phase B (adding `field_leadership` as a 7th portal grant in `user_directory`) remains the deferred architectural item.** The current convergence does NOT require Phase B to succeed — visible UX is now converged regardless.

---

## Unified directory behavior

**Verified live via MongoDB probe:**
- `user_directory`: 59 users · 0 with `field_leadership` role
- `field_leadership_users`: 1 user (`fieldleader@mascigc.com`, Superintendent)
- **No duplicate-identity risk currently active** (clean separation)
- Adding FL to `user_directory` remains the operator-policy decision deferred to a future bounded iter

---

## Mobile proof

Mobile 390 sweep on `/leadership/login` (testing agent iteration_342.json):
- `scrollWidth === clientWidth === 390` ✓
- Form card centered, fully readable
- All form fields accessible
- "Crew using a shared leadership code?" disclosure link visible

---

## RBAC proof (live curl)

| Probe | Result |
|---|---|
| POST `/api/field-leadership/portal/login` with valid creds | 200 ✓ returns token + user object |
| GET `/api/field-leadership/portal/me` with FL token | 200 ✓ returns user object |
| GET `/api/field-leadership/portal/me` anonymous | 401 ✓ |
| POST `/api/field-leadership/portal/login` with wrong password | 401 ✓ "Invalid email or password" (calm) |
| POST `/api/field-leadership/login` (legacy shared-pw) wrong pw | 401 ✓ "Invalid password" — UNTOUCHED, backwards compat alive |

---

## Regression results

- **iter342 regression tests:** 11/11 passing (new file: `/app/backend/tests/test_iter342_fl_login_convergence.py`)
- **Cumulative iter32x + iter33x + iter34x:** 251/251 green (run from `cd backend`)
- **Deploy gate:** 9/9 green · Contract green · safe to deploy
- **ESLint:** clean on both refactored .jsx files

---

## Final convergence verdict — ✅ CONVERGED

An operator opening `/leadership/login` today now sees:
- Same MasciLogo (matches HR, Safety, PM, Shop, Dispatch)
- Same "Field Leadership Portal" badge styling (calm slate, matches HR purple, Safety cyan, etc.)
- Same "Sign in" headline pattern
- Same email + password form fields (no shared codes, no jargon)
- Same forgot-password link (no admin call required for password reset)
- Same Memorial Day cultural banner stacked above (banner system working)
- Same ForgedOpsAttribution footer (consistent platform signature)
- Same calm slate-800 submit button (matches HR slate-900, Safety cyan-700, etc.)

**An operator can no longer tell this portal was built differently.** Field Leadership feels operationally mature, visually converged, identity-converged, and fully part of the MASCI Operations Platform.

---

## Files touched (iter342)

- MOD · `/app/frontend/src/App.js` (swap /leadership/login mount + add /leadership/legacy-login)
- MOD · `/app/frontend/src/pages/FieldLeadershipPortalLogin.jsx` (post-login → /leadership + disclosure link)
- MOD · `/app/frontend/src/pages/FieldLeadershipHub.jsx` (auth check accepts FL token + signOut clears both)
- MOD · `/app/frontend/src/lib/i18n.js` (1 ES translation key for disclosure link)
- NEW · `/app/backend/tests/test_iter342_fl_login_convergence.py` (11 tests · all green)
- NEW · `/app/memory/FL_LOGIN_CONVERGENCE_iter342.md` (this report)
- DOC · `/app/memory/PRD.md`

## Files NOT touched (scope discipline)

- ❌ Backend routes (`field_leadership.py`) — UNTOUCHED
- ❌ `lib/leadershipAuth.js` — UNTOUCHED (legacy compat preserved)
- ❌ `lib/flAuth.js` — UNTOUCHED (already had what we needed)
- ❌ Collections (`field_leadership_users`, `user_directory`) — UNTOUCHED
- ❌ Admin Access Control Center (still 6-portal — no 7th column added)
- ❌ FL Phase B unified directory migration — still deferred · still architectural · still requires operator policy decision

**Cumulative pending redeploy at mascidocs.com: iter330 → iter342 (13 bounded iters · zero drift · all regression-locked).**
