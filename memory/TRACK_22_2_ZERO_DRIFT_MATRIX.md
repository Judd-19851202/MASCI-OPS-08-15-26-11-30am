# Track 22.2 Phase B · Zero-Drift Matrix

**Date:** 2026-02-05
**Attestation:** Track 22.2 Phase B is user-behavior-identical to the pre-extraction baseline.

## Frontend

| Layer | Baseline | Post-extraction | Δ | Verified by |
|---|---:|---:|---:|---|
| `App.js` line count | 1,283 | **94** | −1,189 | `wc -l` |
| `App.js` byte count | 94,062 | **4,145** | −89,917 | `wc -c` |
| `App.js` `<Route ` token count | 386 (incl. `<Routes>` opener) | 1 | −385 | grep |
| `AppRoutes.jsx` line count | *(did not exist)* | 1,230 | +1,230 | `wc -l` |
| `AppRoutes.jsx` `<Route ` token count | 0 | 386 | +386 | grep |
| Total `<Route path=` declarations across all files | 385 | 385 | 0 | Extractor JSON |
| Unique route paths | 385 | 385 | 0 | Extractor JSON |
| Duplicate route paths | 0 | 0 | 0 | Extractor JSON |
| Guard aliases | 11 | 11 | 0 | Extractor JSON |
| Provider mounts (`*Provider`) | 1 | 1 | 0 | Extractor JSON |
| Chrome components | 15 | 15 | 0 | Extractor JSON |
| Lazy imports (unique set) | 180 | 180 | 0 | Extractor JSON |
| Eager route-target imports (unique set) | 138 | 138 | 0 (net-new `AppRoutes` for composition) | Extractor JSON |
| Route ordering (first-match) | preserved | preserved | 0 | Ordered-list equality |
| Guard distribution across roles | PUBLIC 143 · A 65 · AP 45 · SF 33 · H 28 · S 25 · P 22 · DP 10 · D 6 · FL 4 · APS 3 · TX 1 | identical | 0 | Extractor JSON |
| Load distribution | 204 lazy · 170 eager · 11 inline | identical | 0 | Extractor JSON |
| Main bundle (gzipped) | 1.14 MB | 1.14 MB (−218 B) | −218 B ✅ | `yarn build` log |
| JS chunk count | 193 | 193 | 0 | `ls build/static/js/*.js` |
| ESLint warning count | 110 | 110 | 0 | `yarn build` log |
| Compilation errors | 0 | 0 | 0 | `yarn build` log |

## Backend

| Layer | Baseline | Post-extraction | Δ | Verified by |
|---|---:|---:|---:|---|
| Routes | 1,441 | 1,441 | 0 | Runtime probe |
| Methods | 1,445 | 1,445 | 0 | Runtime probe |
| OpenAPI paths | 1,264 | 1,264 | 0 | Runtime probe |
| Middleware | 7 | 7 | 0 | Runtime probe |
| Lifecycle complete | true | true | 0 | `platform_status.lifecycle` |
| Startup / Shutdown migration | 100% / 100% | 100% / 100% | 0 | `platform_status.lifecycle` |
| Bytecode fingerprints checked | 9 | 9 | 0 | `verify_locked_bytecode` |
| Bytecode drift | [] | [] | 0 | `verify_locked_bytecode` |
| `EMAIL_SAFETY_MODE` | strict | strict | 0 | `platform_status.email_safety` |
| `resend_sdk_patched` | true | true | 0 | `platform_status.email_safety` |
| `live_emails_possible` | false | false | 0 | `platform_status.email_safety` |
| Track 22.* lock envelope | 254/254 pass | 254/254 pass | 0 | pytest |

## User-visible behavior

| Behavior | Baseline | Post | Δ |
|---|---|---|---:|
| `/` (public Hub) renders | ✅ | ✅ | 0 |
| `/sign-in` (master multi-workspace) renders | ✅ | ✅ | 0 |
| `/signin` deep-link falls back to `<NotFound/>` | ✅ | ✅ | 0 |
| `/admin/login` renders public form | ✅ | ✅ | 0 |
| Console errors on public routes | 0 | 0 | 0 |
| Preview banner shows | ✅ | ✅ | 0 |
| BrandingProvider red brand color applied | ✅ | ✅ | 0 |
| Suspense fallback = null (no flash) | ✅ | ✅ | 0 |
| `<BrowserRouter key={authTick}>` remount pattern | ✅ | ✅ | 0 |

## Session-scope code changes (complete list)

| File | Diff | Purpose |
|---|---|---|
| `frontend/src/App.js` | 1,283 → 94 lines (rewritten to thin shell) | Track 22.2 Phase B · monolithic routes moved out |
| `frontend/src/app/routing/AppRoutes.jsx` | 0 → 1,230 lines (new file) | Track 22.2 Phase B · route registry |
| `memory/track_22_2/extract_app_js_inventory.py` | +5 lines (walk both files) | Track 22.2 Phase B · parity harness compatibility |

## Attestation

🟢 **Zero drift confirmed.** Every user-visible metric, every backend metric, every route-set metric preserved. The two beneficial deltas (App.js −1,189 lines · main bundle −218 B) are architectural improvements, not behavior changes.
