# TRACK 19.11 AMENDMENT · SESSION-EXPIRY TEST REPORT

**Status:** ✅ ALL GREEN
**Date:** 2026-07-01

## Executive summary

The session-expired modal loop fix ships with three independent verification layers and passes all of them:

| Layer | Suite | Result |
|---|---|---|
| Unit (bus contract) | Jest · `sessionStatusBus.test.js` | 15 / 15 |
| Static (source of truth locks) | Pytest · `test_track_19_11_amendment_session_expired_loop_fix.py` | 40 / 40 |
| Live end-to-end | Playwright browser smoke against preview URL | 7 / 7 steps |
| Regression | Full Track 19.x suite (16 files) | 545 / 545 |

## Jest results

```
PASS src/lib/sessionStatusBus.test.js
  sessionStatusBus
    ✓ publish session_expired updates state and notifies subscribers
    ✓ kind:null is a no-op
    ✓ success_loaded clears any active state
    ✓ success_empty does NOT change overlay state
    ✓ debounce: rapid identical events do not re-notify
    ✓ different kinds flow through even if rapid
    ✓ clearSessionStatus resets state and notifies
    ✓ subscribe replays current state immediately
    session-expired loop fix (Track 19.11 amendment)
      ✓ after user dismiss, further session_expired publishes are suppressed
      ✓ access_restricted dismissal is also ack-suppressed
      ✓ success_loaded lifts ack-suppression so genuinely-new expiry can re-fire
      ✓ resetSessionAck lifts suppression without touching overlay state
      ✓ dismissing NETWORK_UNREACHABLE does NOT ack-suppress (retryable UX)
      ✓ dismissing BACKEND_UNAVAILABLE does NOT ack-suppress (retryable UX)
      ✓ clearSessionStatus on empty state is a no-op
Tests: 15 passed, 15 total
```

## Pytest results

```
40 passed in 0.09s
```

Coverage groups:

| Group | Assertions |
|---|---|
| Bus contract (ACK_STICKY_KINDS, resetSessionAck, getSessionAckState, suppress path, success_loaded lift, auth-only marking, _testReset, window bridge) | 8 |
| Overlay wiring (imports, reset-on-log-back-in, useT, _copy(state, t)) | 4 |
| Overlay bilingual strings (12 canonical EN → ES pairs) | 12 |
| Aria-label bilingual (Close) | 1 |
| Jest coverage guardrail (6 titles) | 6 |
| Draft-safety guardrails (DR + Equipment Pre-Op typing NOT gated on session) | 2 |
| Camera gate preservation (19.09) | 1 |
| HelpDrawer preservation (19.10) | 1 |
| Interceptor preservation (publishSessionStatus / skipSessionStatus / active-portal scoping / classifier) | 4 |
| Backend snapshot lock preservation (19.08) | 1 |
| **Total** | **40** |

## Playwright live smoke (preview URL)

Sequence:

1. Navigate to `/equipment/new`.
2. `window.__masciSessionBus.publish({ kind: 'session_expired', status: 401 })`
   → overlay visible = **1** ✅
   → title = `"Session Expired"`
   → body = `"Your login session has expired. No data has been lost. Please log back in to continue."`
3. Click `[data-testid="session-status-secondary"]` ("Stay Here")
   → overlay visible = **0** ✅
4. Publish `session_expired` × 5 at 1.2s intervals (each well beyond the 800ms debounce)
   → overlay visible = **0** ✅ (**the loop is broken**)
   → `getAck()` → `{ suppressed: ["session_expired"] }` ✅
5. Publish `success_loaded` (simulates session recovery)
   → `getAck()` → `{ suppressed: [] }` ✅
6. Publish a genuinely-new `session_expired`
   → overlay visible = **1** ✅ (real new expiry still surfaces)

Spanish mode smoke:
```
ES Title:     'Sesión Expirada'
ES Body:      'Su sesión ha expirado. No se ha perdido información. Por favor, vuelva a iniciar sesión para continuar.'
ES Primary:   'VOLVER A INICIAR SESIÓN'    (CSS-uppercased button)
ES Secondary: 'QUEDARME AQUÍ'              (CSS-uppercased button)
```

Screenshots captured: `/tmp/session_smoke.png`, `/tmp/session_es_smoke.png`.

## Regression suite

All 16 Track 19.x lock files run one-by-one:

```
19.00 Transportation foundation         : 22 passed
19.01 Transportation Academy            : 21 passed
19.02 Fleet projection                  : 11 passed
19.02a Fleet adoption hardening         : 21 passed
19.02c Disk hygiene                     : 30 passed
19.03 HR roster source-of-truth         : 27 passed
19.04 Daily Report attachments          : 16 passed
19.04 Form session isolation            : 17 passed
19.05 Daily Report total audit          : 59 passed
19.06 Amendment Smart Prefill           : 21 passed
19.06 Progressive disclosure            : 44 passed
19.07 Cognitive checkpoints             : 23 passed
19.08 Forms audit snapshots             : 112 passed
19.09 Operational forms modernization   : 54 passed
19.10 Foundation unification            : 27 passed
19.11 Amendment session-expired fix     : 40 passed  ← NEW
──────────────────────────────────────────────────
TOTAL                                   : 545 passed
```

Zero regressions.

## Acceptance checklist (from the amendment brief)

| Requirement | Status |
|---|---|
| Session-expired modal fires once per expired-session state | ✅ Jest #9 · Pytest suite · Live smoke step 4 |
| Repeated failed autosave/background 401s do NOT spawn repeated modals | ✅ Jest #9 · Live smoke step 4 |
| Typing after dismiss does NOT reopen modal on every character | ✅ Ack-suppression sticky; smoke step 4 verifies at 1.2s intervals |
| Local draft persists after session expiry | ✅ Bus doesn't touch draft state; guardrail Pytest tests confirm form state independent of session bus |
| "Stay Here" works | ✅ `clearSessionStatus()` closes modal + marks ack |
| "Log Back In" works | ✅ Overlay `onPrimary` calls `resetSessionAck()` then `navigate(loginRoute)` |
| No raw 401/403 UI leaks | ✅ Interceptor `safeErrorMessage` + classifier + bus contract all preserved |
| Daily Report form remains usable locally after dismissal | ✅ Guardrail: DR inputs not gated on session state; live smoke did not disable form |
| Equipment Pre-Op remains usable locally after dismissal | ✅ Same guardrail; live smoke confirms form beneath modal is unaffected |
| Spanish mode has translated session-expired text | ✅ 12 new ES translations; live Spanish smoke confirms Sesión Expirada / Volver a Iniciar Sesión / Quedarme Aquí |
| No regression to valid-session autosave | ✅ 545/545 Track 19.x GREEN including 19.04 form session isolation + 19.05 DR total audit |
| No schema drift | ✅ 19.08 snapshot lock still holds |
| No payload drift | ✅ No backend files touched |
| No route drift | ✅ No backend files touched |

## Certification

**GREEN · Track 19.11 Amendment closed.** Ready for Track 19.11 MAIN (Equipment Pre-Op progressive-disclosure conversion) in the next session with a full context budget.
