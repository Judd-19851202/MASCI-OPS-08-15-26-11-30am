# TRACK 13.6K-DRIVER-CORRECTION — Driver V2 Reality Fix

**Date**: 2026-06-12
**Status**: COMPLETE — preview corrected, validated, zero drift.

---

## 1 · What was wrong
The 13.6J Driver Hub V2 preview at `/driver/hub_v2` invented a `SIGN IN` button as its primary action when no driver session was detected. Drivers in this platform **do not sign in**. The misread assumed driver auth existed because the page peeked at `getDriverToken()` — but that token is the **shift session** minted by the public no-login entry at `/shift`, not an account credential. Result: the V2 preview pointed drivers at a route (`/driver/login`) that does not match the real workflow.

## 2 · Existing real driver flow (verified from source)
- **Public self-start entry** — `/shift` → `/app/frontend/src/pages/driver/ShiftStart.jsx` (iter402). Title in the UI: **"Operational Check-In · Start your shift"**. UI copy: "No password. No app. Just check in." Driver picks driver name + truck (canonical dropdowns sourced from `GET /api/dispatch/driver/shift-lookups`), taps **"Start Shift"** → `persistDriverSession` mints the in-browser session → forwards to `/driver`. No accounts. No enrollment.
- **Dispatcher magic-link entry** — `/d/:token` → `/app/frontend/src/pages/driver/DriverMagicLanding.jsx` (iter393). 0 typed characters, 0 taps on the success path; exchanges the dispatcher-issued token, persists the session, forwards to `/driver`.
- **Tap-and-work surface** — `/driver` → `/app/frontend/src/pages/driver/DriverShift.jsx` (iter393). Big tap targets, lifecycle transitions, defect logging. Reads the in-browser driver session minted by either entry path above.

## 3 · Files inspected
- `/app/frontend/src/pages/driver/ShiftStart.jsx` (lines 1–80) — confirmed public self-start doctrine ("0 passwords. 0 accounts. 0 enrollment").
- `/app/frontend/src/pages/driver/DriverMagicLanding.jsx` (lines 1–60) — confirmed magic-link exchange flow.
- `/app/frontend/src/pages/driver/DriverShift.jsx` (lines 1–80) — confirmed `/driver` is the tap-and-work surface using `driverHeaders()`.
- `/app/frontend/src/lib/driverAuth.js` — confirmed `getDriverToken` reads the in-browser shift session, not an account credential.

## 4 · Backend routes inspected
- `/app/backend/routes/dispatch_driver.py` — public driver router. Real endpoints used by the existing flow:
  - `GET  /api/dispatch/driver/shift-lookups` (driver + equipment dropdown sources)
  - `POST /api/dispatch/driver/start-shift` (mints the in-browser shift session)
  - `GET  /api/dispatch/driver/my-assignment` (current active assignment for the session)
  - `POST /api/dispatch/driver/assignments/{id}/transition` (lifecycle transitions)
  - magic-link exchange endpoints under the same router
- No new backend routes were added; the corrected V2 preview reuses only the existing public surfaces.

## 5 · What was corrected
- `/app/frontend/src/pages/driver/DriverHubV2.jsx` rewritten (`overwrite=True`):
  - **Removed** the legacy `data-testid="driver-hub-v2-action-signin"` button and the `/driver/login` route reference.
  - **Replaced** the primary action with two reality-aligned states:
    - No shift session in this browser → **"START SHIFT"** primary CTA → routes to **`/shift`** (the real public self-start entry).
    - Shift session already in browser → **"OPEN MY SHIFT"** primary CTA → routes to **`/driver`** (the existing tap-and-work surface).
  - Secondary buttons point only at real existing routes (`/shift` for "Used a Link?" and "Report an Issue" routes to `/driver` when a session exists, otherwise `/shift`).
  - Footer copy explicitly documents the reality: "Drivers do not sign in. Public self-start lives at `/shift`. Dispatcher magic-link entry is `/d/:token`. Tap-and-work shift screen is `/driver`."
- `/app/frontend/src/App.js` — Driver V2 route mount unchanged (`/driver/hub_v2`, no auth gate change, preview only).

## 6 · What was preserved
- `/shift` — unchanged. Still the canonical public self-start.
- `/d/:token` — unchanged. Still the dispatcher magic-link entry.
- `/driver` — unchanged. Still the tap-and-work surface (DriverShift).
- All backend driver endpoints — unchanged.
- All driver session semantics — unchanged.
- 0 new fields, 0 new endpoints, 0 new auth, 0 invented workflows.

## 7 · Screenshots
- `/tmp/13_6k_driver_corrected.jpg` — `/driver/hub_v2` after correction (iPhone-ish 414×896 viewport): single-question headline, one giant red "START SHIFT" button, two real secondary actions ("Report an Issue", "Used a Link?"), explicit reality footer.
- After tapping START SHIFT → lands on `/shift` rendering the existing "Operational Check-In · Start your shift" page with Driver Name / Truck Number / Trailer Number / Company dropdowns and the "NO PASSWORD. NO APP. JUST CHECK IN." footer copy.

## 8 · Validation evidence
| Check | Result |
|---|---|
| No `SIGN IN` test-id present | ✅ count = 0 |
| No buttons containing "sign in / log in / login / password" | ✅ count = 0 |
| Exactly ONE primary action button | ✅ START SHIFT (1), OPEN MY SHIFT (0) for current no-session state |
| Primary action routes to a real existing route | ✅ `/shift` (ShiftStart.jsx renders) |
| `/shift` renders the existing Operational Check-In page | ✅ "Start your shift", "Truck Number", "no password / no app / just check in" |
| `/driver` (classic) unchanged | ✅ `driver-hub-v2-root` count on `/driver` = 0 |
| ≤ 2 taps to first action | ✅ Tap 1 = START SHIFT → /shift; Tap 2 = pick truck / driver and Start Shift (existing flow) |
| ≤ 30 seconds target | ✅ — `/shift` prefetches dropdowns; the corrected hub adds zero typed characters of its own |
| Other portals unchanged | ✅ — only one file (`DriverHubV2.jsx`) was modified |

## 9 · Remaining risks
- The corrected V2 preview is still **preview only**. No swap. Operator must explicitly approve promoting it before any `/driver` route change.
- Driver V2 currently adds zero value over `/shift` itself — the canonical entry point is already excellent. Operator should decide whether the hub layer is worth keeping. Recommended: **either retire `/driver/hub_v2` entirely**, or **only keep it as an explainer landing for first-time drivers who arrive at the root** (similar to a marketing page).

## 10 · Recommendation for Driver future
1. **Make `/shift` the canonical driver entry**. It is already optimized for ≤ 2 taps, ≤ 30 seconds, glove-friendly, sunlight-readable, and self-documenting. Promote it to `/driver-entry` or a friendly slug if needed for QR codes / posters.
2. **Retire `/driver/hub_v2`** unless operators explicitly want a one-tap "I'm here, what now?" landing that gates the choice between START SHIFT and OPEN MY SHIFT. If kept, never expand it beyond the current single-question form — the hub must never grow into a dashboard.
3. **Magic-link path stays as-is**. It already delivers 0 typed characters and 0 taps on success.
4. **Do NOT add SIGN IN / LOGIN / accounts / passwords to the driver workflow**. Doctrine reaffirmed: drivers check in, they do not log in.

---

*Status: APPROVED for operator review. Awaiting decision on Driver V2 future (keep / retire / promote).*
