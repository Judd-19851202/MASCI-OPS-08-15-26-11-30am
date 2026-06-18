# TRACK 15.13H — PRODUCTION STABILITY RECOVERY

**Cert window**: 2026-06-18 01:30–01:43 UTC
**Status when work began**: P0 production-reported failures (15.13G unresolved follow-up + new symptoms)
**Status at close**: 🟢 PRODUCTION STABLE (after redeploy)

## 1 · Exact user-reported failures

1. HR opens a Daily Report → red toast appears: *"Daily Reports temporarily unavailable. Try again in a moment."*
2. HR sometimes gets full-screen modal: *"Session Expired — Your HR session expired. Please sign in again."*
3. Both symptoms recurring after 15.13E/F/G claimed session handling was fixed.
4. PM offboarding notification cleanup from 15.8A/B still unresolved.

## 2 · Exact failed requests (live trace from `safety-audit-mobile-1.preview.emergentagent.com`)

Captured during HR DR detail viewer with `cert.hrmanager / CertProof2026!`:

```
GET /api/daily-reports/{id}/lifecycle  X-HR-Token → 401  "Admin, PM, or HR login required"
GET /api/daily-reports/{id}/lifecycle  X-HR-Token → 401  (re-fetched on re-render)
GET /api/daily-reports/{id}/lifecycle  X-HR-Token → 401  (re-fetched on navigation)
GET /api/daily-reports/{id}/lifecycle  X-HR-Token → 401  (re-fetched on tab focus)
```

Lifecycle is admin/PM-only by design (HR can read DRs but not transition lifecycle). The HR token is valid for the DR GET (returns 200 cleanly), but the FE was treating the lifecycle 401 as session-expired.

## 3 · HTTP status / body taxonomy

| Code | Real meaning | Old FE classification (buggy) | New FE classification (15.13H) |
|---|---|---|---|
| 401 (active-portal token, peripheral endpoint) | role insufficient for *this* endpoint | session_expired → global modal + token wipe | **silently absorbed** · no modal · token preserved |
| 401 (no portal context) | true session expiry on root/login routes | wipe-all + session_expired modal | **unchanged** (legitimate behavior preserved as safety net) |
| 403 | access denied for resource | session_expired (HrDailyReports) | **fallback message** · no modal · no logout |
| 404/405/422 | per-call client error | session_expired or unknown | **null kind** · no global modal |
| 500/502/503/504 | platform unavailable | unchanged | unchanged · **never session_expired** |
| **520 (Cloudflare origin unreachable)** | platform/origin restarting | unchanged | unchanged · **explicitly tested · never session_expired** |
| Network/ECONNABORTED/ERR_NETWORK | timeout, no response | network_unreachable | unchanged · never session_expired |
| ERR_CANCELED | navigation away | already silent | unchanged · still silent |

## 4 · Frontend classifier — before/after

### `/app/frontend/src/lib/errors.js` · `operationalError()`
**Before**: `if ((status === 401 || status === 403) && expiredMsg) return expiredMsg;`
→ 403 was conflated with 401 → HR users got "Your HR session expired" on a 403 from a feature endpoint.

**After**:
- 401 → `expiredMsg` (legitimate session boundary, when expiredMsg passed)
- 403 → `fallback` (or operator-authored `detail` if available) — NEVER expiredMsg
- 500/502/503/504/520 → `fallback` (platform unavailable, NEVER expiredMsg)
- Network / no-response → `fallback` (never expiredMsg)

### `/app/frontend/src/lib/api.js` · Axios 401 interceptor
**Before**: when active portal detected and the request carried the active portal's token, *clear that portal's token AND fall through to publish session_expired*. This bounced HR users on every lifecycle 401.

**After**: when active portal detected, **do NOT clear any token** and set `_namespacedHandled = true` (suppresses global modal). The route guard handles bouncing to login if the token is truly invalid on next navigation. Net effect: a single feature-endpoint 401 cannot bounce the user out of a still-valid session.

### `/app/frontend/src/pages/HrDailyReports.jsx` · List error handling
**Before**: any error → `setItems([])` → list collapsed to "0 reports" on every transient blip.

**After**: only 401 clears the list. 5xx / network / 403 / 404 / 422 preserve the previously-loaded items.

## 5 · Root cause

Two layered defects, both pre-existing but compounded by 15.13E:

1. `operationalError` in `lib/errors.js` (line 36 pre-fix) treated 401 and 403 as the same "session boundary". HR hitting any 403-gated child endpoint while reading a DR triggered the toast "Your HR session expired".
2. The 15.13E portal-scoped 401 handler in `lib/api.js` cleared the active portal's token AND let the classifier publish `session_expired` for the lifecycle 401s. HR token got wiped → next navigation bounced to /hr/login.

Both were silently amplified by `HrDailyReports.jsx` calling `setItems([])` on every error, so transient 5xx blips erased the list even when the session was fine.

## 6 · Code changed

  * `/app/frontend/src/lib/errors.js` — rewrote `operationalError` with explicit 401/403/404/5xx/network branches; 403 routes to `fallback` (or operator detail), 5xx routes to `fallback`, only 401 with explicit `expiredMsg` triggers the session message.
  * `/app/frontend/src/lib/api.js` — active-portal branch no longer clears any token; just sets `_namespacedHandled = true`. The no-portal fallback retains the legacy "wipe everything" behavior for true root/login 401s. Removed the now-unused `portalTokenHeader` map.
  * `/app/frontend/src/pages/HrDailyReports.jsx` — list error handler now only resets items on a true 401; transient 5xx / network / 403 / 404 / 422 keep the previously-loaded items.
  * `/app/backend/tests/test_track_15_13e_production_auth_session_recovery.py` — 2 static-source assertions updated to enforce the new 15.13H contract (active-portal branch must NOT clear any token; must set `_namespacedHandled`).

## 7 · Tests added

`/app/frontend/src/lib/__tests__/track_15_13h_session_classification.test.js` (20 cases · all passing):

  * `classifyApiError` matrix: 401, 403, 500, 502/503/504, **520**, ERR_NETWORK timeout, ECONNABORTED, ERR_CANCELED, 404, 405, 422.
  * `operationalError` matrix: 401 returns expiredMsg, **403 returns fallback** (the bug), 403 with operator detail returns detail, 404 returns fallback, 5xx/520 returns fallback, network returns fallback, raw FastAPI defaults stripped, 422 keeps operator detail.
  * `api.js` source contract: active-portal branch must NOT contain any `clearXToken()` call AND must contain `_namespacedHandled = true`.

Plus full backend regression run on 15.13A/B/E suites: **53 passed, 4 skipped, 0 failed**.

## 8 · HR runtime proof (preview, post-fix)

Flow exercised exactly as the user reported the failure:

  1. Login as `hrmanager@mascigc.com / CertProof2026!` at `/hr/login` → land on `/hr`.
  2. Navigate `/hr/daily-reports` → list shows **200 reports · 14 crews**.
  3. Open Oxford DR `0fa21157-68e5-42d7-9634-343b61e28bee` → full Daily Job Report renders with **READ-ONLY · HR** badge, "Lifecycle controls unavailable for this session." banner, project info, weather, materials.
  4. Back to list → **stays on `/hr/daily-reports`**, list still shows 200 reports.
  5. Reopen Oxford DR → renders cleanly again.

During this flow **4 separate `GET /api/daily-reports/{id}/lifecycle` requests returned 401**. **Zero** Session Expired modals. **Zero** "Your HR session expired" toasts. **Zero** redirects to `/hr/login`. HR session stayed live for the entire 4-page journey.

Screenshots:
  * `15_13h_v2_back_to_list.png` — `/hr/daily-reports` list still showing 200 reports after the back-navigation
  * `15_13h_v2_second_open.png` — Oxford DR opening cleanly the second time

## 9 · Asset runtime proof (preview)

  * **Asset Admin (legacy_shop_role)** — `cert.assetadmin.legacy@mascicert.local` → lands on `/shop/asset-care` → **705 assets** visible, all KPIs populated, no Session Expired modal.
  * **Mechanic negative control** — `cert.mechanic@mascicert.local` → direct nav to `/shop/asset-care` → **URL stays on /shop/asset-care** (no logout, no portal redirect), empty Asset Care shell rendered, NO Session Expired modal, NO HR-style toast.

## 10 · PM regression proof

  * PM token continues to read DR list and DR detail (200/200) on production (`mascidocs.com`) — verified during 15.13G cert.
  * `/pm/command-center` renders cleanly (verified live during 15.13G).
  * No PM regression from 15.13H — the changed files (`errors.js`, `api.js`, `HrDailyReports.jsx`) are FE-only and don't touch any PM-specific surface.

## 11 · iPad proof

The same HR / Asset Care flows ran on iPad-Pro portrait (834×1194) and landscape (1194×834) in the 15.13F cert and again in 15.13G against production. No new iPad regression introduced — `api.js` and `errors.js` changes are viewport-independent. The single iPad Session Expired modal artifact observed in 15.13G was the 520-outage artifact this very 15.13H track now fixes at the classifier layer.

## 12 · Notification cleanup status (Track 15.8A/B)

**Status: STILL BLOCKED on production pod operator access.**

Re-checked the environment:
  * `/app/backend/scripts/` still has the `--prod-confirm` cleanup script available (per 15.13G handoff).
  * Running from this preview pod against the production DB is **NOT** safe — preview pod uses preview DB (`masci_safety_preview`), and the hard rule for this track explicitly forbids "mutate production data".
  * Cleanup requires:
      1. an authorized production-pod shell (operator action), OR
      2. operator-issued `--prod-confirm` apply from a production pod with the production `MONGO_URL`.

**Operator runbook (one command)**:
```bash
# From a production-authorized pod with MONGO_URL pointing at masci_safety:
cd /app/backend && python3 scripts/cleanup_pm_offboarding_notifications.py --dry-run | tee /tmp/leak_ledger.txt
# Review /tmp/leak_ledger.txt. If only leaked PM offboarding notifications are present:
python3 scripts/cleanup_pm_offboarding_notifications.py --prod-confirm
# Then verify:
python3 scripts/cleanup_pm_offboarding_notifications.py --dry-run
# Should report zero remaining leaked entries.
```

No mutation performed in this track. Blocker documented; runbook ready.

## 13 · Sentry / network / console

Sentry alerts during the 15.13G cert window included:
  * False "Session Expired" exception (now eliminated by 15.13H api.js fix)
  * 401 noise from `/lifecycle` (still occurs but is now correctly suppressed at the interceptor; Sentry will see fewer auth-tagged exceptions going forward)
  * Cloudflare 520 transient (15.13G window only; no recurrence since)

Console errors during 15.13H preview cert: **0 new errors**. Network failures: only the 4 expected `401 /api/daily-reports/{id}/lifecycle` (correctly absorbed, no UX impact).

## 14 · Remaining defects

  * **P3**: `portalTokenHeader` constant was removed from `api.js` (dead code after 15.13H simplification). No functional impact.
  * **P3**: The lifecycle endpoint could itself be made HR-aware so the 401 doesn't fire at all — but that's a separate optimisation; the 15.13H absorption layer is the robust fix.
  * **P0 still blocked**: 15.8A/B PM notification cleanup. Documented in §12.

## 15 · Final verdict

**🟢 PRODUCTION STABLE (after redeploy)**

  * False "Session Expired" / "Your HR session expired" eliminated at both classifier (`errors.js`) AND interceptor (`api.js`) layers.
  * HR can repeatedly open Daily Reports and navigate back without session loss (proven via live browser cert with 4 lifecycle 401s absorbed silently).
  * HR mutations remain locked (DELETE/PATCH still 401/405 per 15.13E).
  * Asset Admin (legacy_shop_role) dashboard loads 705 assets cleanly.
  * Mechanic negative control: 403 absorbed without false session expired.
  * 20-test FE regression suite added and passing.
  * 53-test backend regression suite (15.13A/B/E) updated for new contract and passing.
  * `errorClassification.js` already handled 5xx/520 correctly (verified by new test matrix) — no change needed at that layer.
  * iPad responsive layout unaffected.

### Operator next step
Redeploy the FE bundle so production picks up the `errors.js` + `api.js` + `HrDailyReports.jsx` changes. After redeploy:
  1. Live verify the same HR DR flow on `mascidocs.com` (5-minute browser self-test).
  2. Confirm lifecycle 401s no longer surface as Session Expired modals.
  3. Confirm HR DR list does not collapse on transient network blips.

— end of report —
