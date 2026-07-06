# TRACK 22.4D — MOBILE REGRESSION GATE + PLATFORM-WIDE LEAVE-SITE / UNSAVED-CHANGES AUDIT

**Status:** ✅ GO · 2026-07-06
**Two-part track:** (A) wire Track 22.4c Playwright mobile suite into
the deployment gate, and (B) root-cause the repeated
"session-expired / leave-site" modal that operators were seeing every
few keystrokes on Pre-Op and other long forms.

---

## PART A · MOBILE REGRESSION GATE

### Wiring

- **File touched:** `/app/scripts/deployment_gate.py`
- **Added to `REGRESSION_FILES`:**
  - `tests/test_track_22_4b_followup_*.py` (12 files — the whole
    idempotency + driver + safety-lifecycle + DR/HR identity family)
  - `tests/test_track_22_4c_mobile_responsiveness_sweep.py`
- **Per-test timeout bumped:** `--timeout 30` → `--timeout 90`
  (Playwright assertions round-trip a real browser).
- **Subprocess timeout bumped:** `600s` → `1200s` so the mobile
  family's ~250s worst-case runtime never triggers a spurious
  deploy-block.

### Gate Wiring Regression Lock

- **File created:** `/app/backend/tests/test_track_22_4d_gate_wiring.py`
- **15 static tests** that certify:
  - `deployment_gate.py` still loads as a valid Python module.
  - Track 22.4c mobile sweep is listed and on-disk.
  - Every Track 22.4b-followup file is listed and on-disk
    (parametrized × 11 test files).
  - Per-test timeout ≥ 60s.
  - Subprocess timeout ≥ 900s.
- **Result:** 15 / 15 pass.

### Failure Behavior

- Any Playwright horizontal-overflow assertion → `subprocess.run`
  returns non-zero → `run_regression()` returns
  `{"passed": False, ...}` → `deployment_gate.py` exits 1 → CI blocks.
- In envs without a Playwright chromium binary, the mobile sweep
  gracefully **skips** (its fixture calls `pytest.skip()` if the
  browser is missing). Gate still runs; other regressions still
  block. This is the correct policy — a gate should not be
  bypassed silently, but it should not falsely fail either on a
  build agent that never had a browser available. Nightly / final
  deploy tier runs the full sweep with browsers pre-installed.

### Command

```
python3 scripts/deployment_gate.py
```

The gate now covers **regression + runtime** as before, PLUS the
mobile responsiveness sweep at 5 viewports × 15 routes + 2 named P1
locks + Motive shape check.

---

## PART B · LEAVE-SITE / UNSAVED-CHANGES AUDIT

### Root Cause

**File:** `/app/frontend/src/lib/sessionStatusBus.js`
**Function:** `publishSessionStatus`, in the `success_loaded` branch
**Trigger:** ANY 2xx response — including public / anonymous endpoint
  responses (translations, i18n, health probes, public asset lookups,
  static resource fetches).
**Why it repeated:** The Track 19.11 amendment introduced sticky
  ack-suppression: once the user clicked "Stay Here" on the session
  modal, the ack silenced future 401s. BUT the same amendment also
  unconditionally cleared `_ackSuppressed` on every `success_loaded`
  event. The client-side axios interceptor fires `success_loaded` on
  every 2xx, including from public endpoints that don't require a
  valid token. So the sequence was:

  1. Session expires or a background poll hits an authed endpoint → 401.
  2. `SessionStatusOverlay` shows the modal.
  3. User clicks "Stay Here" → `clearSessionStatus()` → ack set.
  4. Any 2xx (translations, public GET, etc.) fires → `success_loaded`
     → **ack cleared**.
  5. Next keystroke re-fires the authed picker / poller → 401 → modal
     REOPENS.
  6. Loop forever until the user reloads.

  The user perceives this as "modal after every keystroke", though
  technically the modal reopens after every _successful_ background
  request that happens to be public.

### Exact Fix

`sessionStatusBus.js` — the `success_loaded` handler now clears the
visual overlay state but does **NOT** clear `_ackSuppressed`. Only
two paths lift the sticky ack:

1. `resetSessionAck()` (called by "Log Back In" primary action
   before it navigates to the login route).
2. A fresh page load (module-scope state reinitialized).

Semantics:

- **Data safety:** untouched. Drafts still autosave to IDB via
  `useFormDraft`. No dirty-form navigation blocker exists in the
  platform — the modal itself never blocked navigation.
- **Auth safety:** untouched. Token wipes in the interceptor still
  happen on 401. Route guards still bounce the user to /login on
  protected navigation. The modal is purely a UX signal.
- **Operator UX:** dismiss once, keep typing. No modal thrash.
  Explicit "Log Back In" still works. Reload still works.

### Files Touched

- `/app/frontend/src/lib/sessionStatusBus.js` (root cause fix +
  updated doctrine comment).
- `/app/frontend/src/lib/sessionStatusBus.test.js` (rewrote the
  previous "success_loaded lifts ack-suppression" test — it enshrined
  the exact wrong behavior — replaced with two Track 22.4d locks).

### Platform-Wide Sweep (audit result)

Grep across the entire frontend proves:

| Pattern                                     | Findings |
|---------------------------------------------|----------|
| `useBlocker`                                | 0 uses   |
| `history.block`                             | 0 uses   |
| React-Router `Prompt` as nav blocker        | 0 uses (only `DraftRestorePrompt` — a voluntary restore card, not a nav blocker) |
| `window.confirm` for unsaved changes        | 0 uses   |
| `beforeunload` with `event.returnValue`     | 0 uses (no browser-native leave-site prompt is triggered anywhere) |
| Dirty-form nav guards                       | 0 uses   |
| Global session/auth modal                   | 1 (`SessionStatusOverlay` — fixed) |
| Autosave lifecycle listeners                | `useFormDraft` — flushes silently to IDB, no prompt |

**Conclusion:** The `SessionStatusOverlay` was the sole source of the
repeated modal problem across every form. The fix in
`sessionStatusBus.js` closes the bug platform-wide in a single edit,
without touching data safety, autosave, RBAC, or Motive.

### Forms Audited (all clear post-fix)

| Form                          | Impacted by root cause | Post-fix |
|-------------------------------|------------------------|----------|
| Daily Report                  | yes (any 401)          | ✅ fixed |
| Equipment Pre-Op              | yes                    | ✅ fixed |
| DVIR                          | yes                    | ✅ fixed |
| Safety Meeting                | yes                    | ✅ fixed |
| JHA / JHP                     | yes                    | ✅ fixed |
| QA/QC                         | yes                    | ✅ fixed |
| Incident                      | yes                    | ✅ fixed |
| Trench Safety inspection      | yes                    | ✅ fixed |
| HR Request                    | yes                    | ✅ fixed |
| Dispatch Assignment drawer    | yes                    | ✅ fixed |
| Roll-Off assignment           | yes                    | ✅ fixed |
| Shop Defect forms             | yes                    | ✅ fixed |
| Field Leadership forms        | yes                    | ✅ fixed |
| Public / anonymous forms      | yes                    | ✅ fixed |
| Admin config forms            | yes                    | ✅ fixed |

Every form on the platform benefits from the single-file fix because
the `SessionStatusOverlay` is mounted **once globally** in `App.js`
and consumes the bus that every axios request already publishes into.

---

## Defects

| ID       | Sev | Status | Description                                                                      | Owner track |
|----------|-----|--------|----------------------------------------------------------------------------------|-------------|
| B-09     | P1  | ✅ FIXED | Session-expired modal reopening on every keystroke on long forms                | 22.4d       |
| P3-NAV-01| P3  | ✅ CLOSED (subsumed) | The Track 22.4c-deferred "leave-site modal" report — same root cause | 22.4d       |

## Regression Suite Growth

```
Handoff baseline:                       84
+ Trench Writes idempotency:             9
+ Shop Defects idempotency:              7
+ Driver track (B-06):                  14
+ Mobile responsiveness sweep (22.4c): 77
+ SessionStatusBus new locks (22.4d):    2 (Jest)
+ Gate wiring locks (22.4d):            15
──────────────────────────────────────────
Grand total across 22.4b + 22.4c + 22.4d: 208 tests (0 failures)
```

## Files Created

- `/app/backend/tests/test_track_22_4d_gate_wiring.py`
- `/app/memory/TRACK_22_4D_MOBILE_GATE_AND_NAV_AUDIT.md` (this file)
- `/app/memory/TRACK_22_4D_UNSAVED_CHANGES_FINDINGS.csv`
- `/app/memory/TRACK_22_4D_FORM_GUARD_MATRIX.csv`
- `/app/memory/TRACK_22_4D_NAVIGATION_EVENT_TRACE.csv`

## Files Changed

- `/app/scripts/deployment_gate.py` (mobile suite + 22.4b family wired; timeouts bumped)
- `/app/frontend/src/lib/sessionStatusBus.js` (root cause fix)
- `/app/frontend/src/lib/sessionStatusBus.test.js` (two new locks; one obsolete test rewritten)
- `/app/memory/PRD.md` (Track 22.4d summary appended)

## Verdicts

- **Pre-Op:** ✅ fixed. No modal spam. Draft autosave untouched.
- **Session-expired modal:** dismiss once, stays dismissed. Only
  "Log Back In" or full reload can re-arm it.
- **Unsaved-changes guard:** unchanged (there was never a
  cross-cutting dirty-form guard; `useFormDraft` keeps drafts safe
  in IDB regardless of navigation).
- **Autosave:** ✅ untouched. IDB flushes still happen on typing,
  visibility change, pagehide, beforeunload.
- **Data safety:** ✅ preserved. No draft-clearing paths were altered.
- **Motive:** unchanged / preserved.
- **RBAC:** unchanged. The fix touches purely UX signaling.

## Next Tracks

- Production Deployment Certification
- DR-UNIFY-005 when telemetry window confirms safe retirement
- Post-deploy field smoke checklist
