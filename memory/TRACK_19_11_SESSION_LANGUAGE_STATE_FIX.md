# TRACK 19.11 · Session Overlay Language / State Fix

**Status:** ✅ GREEN · CERTIFIED · CLOSED (Part A only — Part B reserved for next session)
**Date:** 2026-07-01
**Scope:** Frontend-only investigation + hardening. Zero backend / schema / route / payload / PDF / email / notification drift.

---

## 1. Field report

Operator saw a Spanish "Sesión Expirada" modal on a form page in preview. Concern raised:
1. Modal might be showing Spanish while the EN toggle is active (language-state bug).
2. Modal might still be reopening after dismiss (loop-fix might not have shipped).
3. Something in FormShell / form headers might be passing stale language into the overlay.
4. Combination of the above.

Directive: assume the worst until empirically disproven. Harden the overlay + language state + regression suite anyway.

## 2. Investigation

### 2.1 Component / bus topology
- **Bus:** `frontend/src/lib/sessionStatusBus.js` (Track 19.11 Amendment shipped previously — sticky ack-suppression for auth kinds).
- **Overlay:** `frontend/src/components/SessionStatusOverlay.jsx` (mounted ONCE globally in `App.js:448` inside a `<BrowserRouter>` scope).
- **Language state:** `frontend/src/lib/i18n.js` — module-level `_current`, persisted to `localStorage["masci.lang"]`, `useT()` uses `useSyncExternalStore(subscribe, getLang, getLang)` for React-safe re-render on change.
- **Language toggle:** `frontend/src/components/LangToggle.jsx` — uses `useT()`'s `setLang(l)`; testids `data-testid="lang-en"` and `data-testid="lang-es"`.

### 2.2 Grep audit for duplicate session-expiry UIs
```
grep -rn "Session Expired\|Sesión Expirada" src/
```
Result: **only one** rendering path (`SessionStatusOverlay.jsx`). `errorClassification.js` has hardcoded English `COPY.title/body/action` fields but they are metadata for the classifier — nothing in the app reads or renders `classification.title`. Confirmed via `grep -rn "classification.title\|err.title"` → zero hits.

### 2.3 Overlay language-following contract
- `useT()` returns `{ t: tStr, lang, setLang }`. `tStr` is a pure module reference that reads `_current` at call time.
- On language change: `setLang()` mutates `_current`, calls each subscriber. `useSyncExternalStore` re-renders the overlay.
- The overlay's render body calls `const { t } = useT();` then `const copy = _copy(state, t);` — so `_copy` runs FRESH on every render with the current `t`. No stale closure.
- `useCallback(onDismiss, [])` and `useCallback(onPrimary, [state.kind, location.pathname, navigate])` do NOT depend on `t`, and correctly do NOT call `t()` — they use `clearSessionStatus` / `resetSessionAck` / `navigate`.

**Conclusion:** the language-following contract is architecturally correct. The overlay MUST re-render on language toggle and MUST render in the current language.

### 2.4 Empirical verification (live Playwright against preview URL)

Eight live tests executed on `https://safety-audit-mobile-1.preview.emergentagent.com/equipment/new`:

| # | Test | Result |
|---|---|---|
| 1 | EN default → publish session_expired → title/primary/secondary all English, no ES leak | ✅ |
| 2 | Toggle to ES via `[data-testid="lang-es"]` → `localStorage["masci.lang"]="es"` | ✅ |
| 3 | Genuinely-new expiry after ES toggle → Spanish strings, no EN leak | ✅ |
| 4 | Dismiss in ES + 10 background publishes at 500ms intervals → modal stays closed; ack = `["session_expired"]` | ✅ |
| 5 | Type 20 chars with a concurrent 401 fired per keystroke → modal stays closed, form value preserved | ✅ |
| 6 | `success_loaded` → ack cleared | ✅ |
| 7 | Switch back to EN → new expiry English | ✅ |
| 8 | Reload page with persisted ES → new expiry Spanish | ✅ |

Cross-form smoke (dismiss + 5 spam publishes):

| Form | Route | Modal opens EN | Dismiss holds | Result |
|---|---|---|---|---|
| Daily Report | `/daily/new` | ✅ | ✅ | ✅ |
| Equipment Pre-Op | `/equipment/new` | ✅ | ✅ | ✅ |
| DVIR | `/fleet/dvir/new` | ✅ | ✅ | ✅ |
| Safety Meeting | `/meetings/new` | ✅ | ✅ | ✅ |

**Console errors across all 12 test scenarios: 0.**

## 3. Findings

### 3.1 The suspected bug does NOT exist

Empirical evidence:
- **Language-following works:** modal renders in the current active language on every open, and switches languages when the toggle is used.
- **Ack-suppression holds:** dismissed → 10 subsequent 401 publishes → modal stays closed.
- **Typing safe:** 20 concurrent 401s during typing → modal never re-opens, typed data preserved.
- **All 4 form routes clean:** DR / Equipment Pre-Op / DVIR / Safety Meeting all pass smoke.
- **Persistence intact:** ES setting survives page reload; next expiry renders Spanish.
- **Zero console errors** across every test.

The Spanish "Sesión Expirada" screenshot referenced in the user brief was produced by my own previous ES-mode Playwright smoke (the smoke run for the Track 19.11 Amendment session). No production regression exists.

### 3.2 Hardening opportunities identified (and taken)

Even though the bug did not reproduce, the user directive said "harden anyway." Applied hardening:

| # | Hardening | Applied |
|---|---|---|
| 1 | Lock `useT()` to `useSyncExternalStore` (reactive re-render on lang change) | Pytest assertion |
| 2 | Lock `setLang` to notify all listeners | Pytest assertion |
| 3 | Lock `setLang` persistence to localStorage under `masci.lang` | Pytest assertion |
| 4 | Lock `document.documentElement.lang` mirror for native spell-check | Pytest assertion |
| 5 | Lock render-body ordering: `const { t } = useT();` MUST precede `_copy(state, t)` | Pytest assertion |
| 6 | Lock `useCallback(onDismiss,[])` does not (incorrectly) use `t` | Pytest assertion |
| 7 | Lock `LangToggle` testids `lang-en` / `lang-es` for regression stability | Pytest assertion |
| 8 | Lock `LangToggle` uses `useT()` (single source of truth) | Pytest assertion |
| 9 | Lock exact EN↔ES dictionary mapping for every overlay string | Pytest parametrize (7 pairs) |
| 10 | Lock default language = `"en"` (canonical) | Pytest assertion |
| 11 | Lock `VALID = new Set(["en","es"])` (no accidental third-language drift) | Pytest assertion |
| 12 | Lock `LangToggle` mounted on all 4 hero-form pages | Pytest assertion |
| 13 | Lock `window.__masciSessionBus` full API surface (`publish`, `clear`, `get`, `resetAck`, `getAck`) | Pytest assertion |
| 14 | Cross-form Playwright smoke captured in the regression report | 4 forms · 12 assertions |
| 15 | Live language-following smoke captured in the regression report | 9 assertions |

### 3.3 UX observation (not a bug — noted for future)

The modal's z-1000 backdrop intercepts pointer events, so clicking the `LangToggle` (which lives in the header, but under the backdrop) while the modal is open is blocked. This is correct dialog-modal behavior per WAI-ARIA. However, at 5:30 AM, a Spanish-speaking operator who sees an unfamiliar English modal might want to switch to Spanish without dismissing. **P2 improvement (deferred, non-blocking):** consider embedding a compact `LangToggle` inside the modal header. Not required for GREEN.

## 4. Code changes

**None.** The code was architecturally correct; only the regression suite was extended:
- `backend/tests/test_track_19_11_amendment_session_expired_loop_fix.py` — +28 new assertions (+9 parametrized live-smoke labels)
- `memory/TRACK_19_11_SESSION_LANGUAGE_STATE_FIX.md` — this doc (NEW)
- `memory/TRACK_19_11_SESSION_OVERLAY_REGRESSION_REPORT.md` — NEW · captures the live smoke coverage

**Total pytest for Track 19.11 Amendment: 40 (original) + 28 (new) = 68 lock assertions.**

## 5. Zero-drift certification

- Schema drift: ZERO
- Route drift: ZERO
- Payload drift: ZERO
- PDF drift: ZERO
- Email drift: ZERO
- Notification drift: ZERO
- Fail-cascade drift: ZERO (19.09 camera gate still passes its lock test)
- HelpDrawer preservation: ZERO drift (19.10 lock test still GREEN)
- Bilingual drift: ZERO (overlay bilingual dictionary complete + locked)
- Autosave / draft drift: ZERO
- Trust-Spine drift: ZERO

## 6. Doctrine

**The overlay is language-following.** English is canonical; Spanish is an opt-in mode with a dictionary. The modal renders in the currently-active language on every open. Toggling language before a modal opens will render the modal in the new language. Toggling language while a modal is open is blocked by the modal backdrop (correct WAI-ARIA behavior); toggling after dismiss and before the next open will render the next modal in the new language.

**The overlay is loop-safe.** Once the user dismisses `session_expired` (or `access_restricted`), further background 401s of the same kind are ack-suppressed until either `success_loaded` proves session recovery or `resetSessionAck()` fires (explicit "Log Back In" flow).

**The overlay is draft-safe.** Zero disable-input paths; zero clear-form paths; zero touch of local storage draft state. Typing after dismiss is smooth and preserved. Autosave still fires; the failing 401 result is silenced at the UX sink but the underlying token clearing / route guarding is unchanged.

**The overlay is security-safe.** Ack-suppression is a UX-only silencer. The 401 response still causes token clearing in the interceptor; the invalid session remains invalid; the next protected action (submit / navigate) will still fail correctly.

Session expiry protects security. It does not punish the operator. Done means done.
