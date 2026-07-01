# TRACK 19.11 AMENDMENT · SESSION-EXPIRED MODAL LOOP FIX

**Status:** ✅ GREEN · CERTIFIED · CLOSED
**Date:** 2026-07-01
**Scope:** Frontend-only bug fix. Zero backend / schema / route / payload / PDF / email / notification drift.

---

## 1. Field bug reported

On form pages (Daily Report, Equipment Pre-Op, DVIR), when a login session expires and the operator types into any input, the **"Session Expired" modal reopens repeatedly on virtually every keystroke.** Dismissing it via "Stay Here" briefly closes it, but the next keystroke reopens it seconds later. This creates an unusable form experience at 5:30 AM.

Field-critical: operators lose confidence in the platform; typed data feels at risk (even though drafts are safe); pencil-whipping temptation increases because "the app is fighting me."

## 2. Root cause

`sessionStatusBus.js` implements a **debounce-only** suppression window:

```js
const DEBOUNCE_MS = 800;
// same kind within 800ms → coalesce
```

This collapses parallel loaders correctly (three cards firing 401 in the same tick → one modal). It does **NOT** handle the field scenario:

1. User types → any background component that polls (`BackendStatusBanner`, `MultiPortalHydrator`, roster refetches, autosave-style effects) fires an API call.
2. Session is expired → axios interceptor publishes `session_expired`.
3. First publish → modal opens.
4. User clicks "Stay Here" → `clearSessionStatus()` sets `_state.kind = null`.
5. **BUT** `_lastEmitKind` and the debounce window aren't structured as sticky ack. `_lastEmitAt` is set to `now`.
6. User types again ~2s later. Next background poll → 401 → `publishSessionStatus({kind:"session_expired"})`.
7. Now `now - _lastEmitAt ≥ 800ms`, debounce **passes**, `_state.kind = "session_expired"`, subscribers re-fired, **modal re-opens.**
8. Loop continues on every keystroke that triggers any background request.

The debounce was built for "collapse parallel storms," not for "respect a user's dismissal for the lifetime of the expired-session state."

## 3. Fix

Add **sticky acknowledgment suppression** to the bus for auth kinds only. Once the user dismisses `session_expired` (or `access_restricted`), future publishes of that same kind are ignored until:

- `success_loaded` fires (session recovered — user re-authenticated and a real request succeeded), OR
- `resetSessionAck()` is called explicitly (login flow on mount, or the overlay's "Log Back In" primary action before nav).

`NETWORK_UNREACHABLE` and `BACKEND_UNAVAILABLE` are **NOT** ack-sticky — those are retryable transient conditions where re-opening the modal on the next failure is the correct UX.

### Files changed

| File | Change |
|---|---|
| `frontend/src/lib/sessionStatusBus.js` | Added `ACK_STICKY_KINDS`, `_ackSuppressed` set, `resetSessionAck()`, `getSessionAckState()`. `publishSessionStatus` short-circuits on ack-suppressed kinds. `clearSessionStatus` marks the dismissed auth kind as ack-suppressed. `success_loaded` lifts the entire ack set. `window.__masciSessionBus` gains `resetAck` + `getAck` for Playwright / diagnostics. |
| `frontend/src/components/SessionStatusOverlay.jsx` | Imports `resetSessionAck`. `onPrimary` for SESSION_EXPIRED now calls `resetSessionAck()` before navigating to the login route so a genuinely-new post-login 401 can raise the modal again. All 12 display strings routed through `useT()`. `aria-label="Close"` on the X button now bilingual. |
| `frontend/src/lib/sessionStatusBus.test.js` | +7 Jest test cases covering ack behavior (see §5). |
| `frontend/src/lib/i18n.js` | +12 ES translations for every string the overlay renders. |
| `backend/tests/test_track_19_11_amendment_session_expired_loop_fix.py` | NEW · 40 lock assertions covering bus contract, overlay bilingual, Jest coverage, draft safety guardrails, interceptor preservation, zero backend drift. |

### What the fix does NOT do (safety envelope)

- Does NOT extend an invalid session.
- Does NOT clear or restore tokens (interceptor still owns token lifecycle).
- Does NOT weaken the 401/403 auth signal — every failing request still causes token-clearing and route-guard bouncing.
- Does NOT touch autosave, draft-save, or local storage.
- Does NOT disable inputs.
- Does NOT clear form state.
- Does NOT hide a truly-new expiry event that fires after session recovery.

## 4. Behavior matrix (before → after)

| Scenario | Before | After |
|---|---|---|
| First 401 on a form page | Modal opens | Modal opens |
| User dismisses "Stay Here" | Modal closes | Modal closes |
| Background poll fires 401 800ms later | Modal reopens ❌ | Modal stays closed ✅ |
| Every subsequent keystroke → 401 → modal storm | Loop 🔥 | Silent (ack-suppressed) ✅ |
| Local draft state | Preserved | Preserved |
| Typing enabled | Yes | Yes |
| `success_loaded` after Log Back In | Ack still stuck | Ack lifted ✅ |
| Genuinely-new 401 after successful re-auth | Modal opens | Modal opens ✅ |
| 5xx / network events dismissed | Retryable next time | Retryable next time (unchanged) |
| Spanish mode text | English-only ❌ | Fully translated ✅ |

## 5. Test coverage

### Jest (`sessionStatusBus.test.js`) — 15/15 GREEN
- 8 original bus contract cases preserved.
- 7 NEW cases in `describe("session-expired loop fix (Track 19.11 amendment)")`:
  - Ack survives past debounce window
  - `access_restricted` ack-suppressed too
  - `success_loaded` lifts ack
  - `resetSessionAck` lifts without touching overlay state
  - `NETWORK_UNREACHABLE` NOT ack-sticky
  - `BACKEND_UNAVAILABLE` NOT ack-sticky
  - Empty-state clear is a no-op

### Pytest (`test_track_19_11_amendment_session_expired_loop_fix.py`) — 40/40 GREEN
- Bus contract shape (8)
- Overlay bilingual + reset wiring (5 + 12 param cases + 1)
- Jest coverage guardrail (6)
- Draft/typing safety guardrails on DR + Equipment Pre-Op (2)
- Track 19.09 camera gate preservation (1)
- Track 19.10 HelpDrawer preservation (1)
- Interceptor contract preserved (4)

### Live browser smoke (Playwright) — GREEN
- Publish → modal opens → dismiss → modal closes
- 5 subsequent publishes at 1.2s intervals (well past debounce) → **modal stays closed**
- `getAck()` reports `["session_expired"]`
- `success_loaded` → ack cleared
- Fresh `session_expired` → modal opens again
- Spanish mode: `Sesión Expirada` · `VOLVER A INICIAR SESIÓN` · `QUEDARME AQUÍ` — all rendered

### Full Track 19.x regression — 545/545 GREEN
All 15 Track 19.x lock suites pass with the amendment applied. Zero regressions.

## 6. Zero-drift certification

- **Schema drift:** ZERO — no backend models touched.
- **Route drift:** ZERO — no endpoints added/removed/renamed.
- **Payload drift:** ZERO — no new request/response fields.
- **PDF drift:** ZERO — WeasyPrint templates untouched.
- **Email drift:** ZERO — notification pipelines untouched.
- **Notification drift:** ZERO — Trust-Spine + integration surfaces untouched.
- **Fail-cascade drift:** ZERO — 19.09 camera gate + FAIL/OOS + DVIR block-reason preserved.
- **Bilingual drift:** ZERO — overlay now fully bilingual; 12 new ES translations added.
- **Trust-Spine drift:** ZERO — no audit/signature/evidence paths touched.
- **Autosave drift:** ZERO — draft mechanics untouched. Suppression is at the UX sink, not the API pipe.

## 7. Doctrine

Session expiry protects security. It does not punish the operator or destroy field work. When the user has been told once that the session expired and has acknowledged the message, the system trusts them to finish typing / signing / thinking without slamming the modal in their face on every background poll. Real auth failures still block real actions (submit will fail; navigate will bounce to login); the only thing suppressed is the *UX modal*, not the security enforcement.
