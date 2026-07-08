# TRACK 26.09 — FRONTEND TEST SUITE HYGIENE

**Date:** 2026-07-08 UTC · **Preceding gate:** Track 26.08 pre-existing failure register (4 known failures) · **Standard:** relentless-ownership sweep — no fake green, no loose ends

---

## 🟢 EXECUTIVE VERDICT: **DONE**

All 4 known failures fixed. 1 additional stale-copy assertion discovered mid-sweep (PF-5) also fixed in the same track. Full frontend test suite: **216/216 tests pass · 11/11 suites pass · zero failures · zero skips · zero orphans**. Zero production behavior drift. Track 26.08 remains **GO**.

---

## 1 · TEST COMMANDS RUN

```
# per-suite regression
$ cd /app/frontend && CI=true yarn test --watchAll=false \
    --testPathPattern='(errorClassification|track_15_13h|Hub.track_15_4|track_26_08)'
→ Test Suites: 4 passed · Tests: 82 passed · Time: 4.077 s

# full frontend suite (relentless-ownership sweep)
$ cd /app/frontend && CI=true yarn test --watchAll=false
→ Test Suites: 11 passed · Tests: 216 passed · Time: 5.482 s
```

---

## 2 · FIX MATRIX

| ID | Before status | Root cause | Fix | After status | Files touched |
|---|---|---|---|---|---|
| **PF-1** | FAIL — `Expected "MASCI Services…" / Received "Services…"` | 2026-06-22 rebrand copy edit (commit `2810054e`) dropped the "MASCI " prefix in `errorClassification.js:58`; test assertion never updated | Aligned the assertion at `errorClassification.test.js:41` to `"Services Temporarily Unavailable"` + inline TRACK 26.09 doctrine comment citing the source line | ✅ PASS | `src/lib/errorClassification.test.js` |
| **PF-2** | FAIL — `Expected "network_unreachable" / Received null` | Track 14.0-PLATFORM-STABILITY (2026-06-15 commit `6ef970c3`) intentionally removed the `\|\| true` fallback that used to coerce EVERY no-response error into a global `NETWORK_UNREACHABLE` overlay; the new contract returns `kind: null` so callers render a local toast instead of a false-positive disconnect modal | Aligned the assertion at `errorClassification.test.js:82` to `expect(r.kind).toBeNull()` + `expect(r.status).toBeNull()` + `expect(r.title).toBe("")`; renamed the test to `unknown error shape → kind:null (Track 14.0 stability contract)` and added a doctrine comment linking to source lines 134-141 | ✅ PASS | `src/lib/errorClassification.test.js` |
| **PF-3** | FAIL — `Expected "MASCI Services…" / Received "Services…"` | Same 2026-06-22 rebrand as PF-1 | Aligned the assertion at `track_15_13h_session_classification.test.js:69` + doctrine comment | ✅ PASS | `src/lib/__tests__/track_15_13h_session_classification.test.js` |
| **PF-4** | FAIL — `Cannot find module '@testing-library/react'` (test suite couldn't even load) | Three separate blockers: (a) `@testing-library/react` + `@testing-library/jest-dom` never installed, (b) Jest had no `@/` alias resolver, (c) `react-router-dom` v7's ESM-first exports don't play with CRA/craco default Jest CJS resolver | Three-part surgical fix — see §3 | ✅ PASS · **31/31 Hub tests running end-to-end** | `package.json` (deps), `craco.config.js` (Jest moduleNameMapper + transformIgnorePatterns), `Hub.track_15_4.test.jsx` (react-router-dom virtual mock) |
| **PF-5** ⭐ NEW | FAIL — `Field reporting … dispatch, and project …` not found | Hub.jsx source now says `"transportation"` (recent rebrand from `"dispatch"`), test still asserted the old copy | Aligned the regex at `Hub.track_15_4.test.jsx:70` to `"transportation"` + inline PF-5 doctrine comment | ✅ PASS | `src/pages/__tests__/Hub.track_15_4.test.jsx` |

---

## 3 · PF-4 UNPACKED (three-part fix)

1. **Dependency install** — `yarn add --dev @testing-library/react@^14.3.1 @testing-library/jest-dom@^6.6.3`. These were referenced by the test file but never in `devDependencies`. Now landed at `@testing-library/react@14.3.1` + `@testing-library/jest-dom@6.9.1`.

2. **Jest config in `craco.config.js`** — added a `jest.configure` hook that:
   - injects `moduleNameMapper: { "^@/(.*)$": "<rootDir>/src/$1" }` so tests can use the `@/` alias exactly like Webpack (`Hub.jsx` transitively imports `@/components/MasciLogo`, `@/lib/i18n`, etc.).
   - widens `transformIgnorePatterns` to let babel-jest transform `react-router`, `react-router-dom`, `axios`, `lucide-react`, `@radix-ui`, `nanoid`, `@dnd-kit`, `use-sync-external-store` — every ESM-first package Hub.jsx transitively pulls.

3. **`react-router-dom` v7 mock in the test file** — added `jest.mock("react-router-dom", () => ({ MemoryRouter, Link, NavLink, useNavigate, useLocation, useParams, Outlet, __esModule: true }), { virtual: true })` so the test never touches the real ESM entry (which the CJS resolver couldn't consume). The mock preserves the router API surface Hub.jsx actually uses.

Result: **the previously-orphan Hub test suite now executes 31 real assertions** covering hero headline copy, Project Systems title, launcher buttons (Basecamp / OnStation / ForgedOps Plans) with correct URLs / `target=_blank` / `rel=noopener noreferrer`, Field Leadership card contract, forbidden internal labels (Track 15.6 lockdown), single-click-target invariant, and non-clickable capability items. **This coverage was previously silently absent from every CI run.**

---

## 4 · FILES CHANGED (exhaustive)

```
M  frontend/craco.config.js                                              (+18 · Jest alias + transformIgnorePatterns)
M  frontend/package.json  +  frontend/yarn.lock                          (yarn add -D @testing-library/react @testing-library/jest-dom)
M  frontend/src/lib/errorClassification.test.js                          (PF-1 + PF-2 assertion realignment · +11 -2)
M  frontend/src/lib/__tests__/track_15_13h_session_classification.test.js (PF-3 · +2 -0)
M  frontend/src/pages/__tests__/Hub.track_15_4.test.jsx                  (PF-4 mock + PF-5 copy · +21 -2)
A  memory/TRACK_26_09_FRONTEND_TEST_SUITE_HYGIENE.md                     (this report)
```

**Production source files touched:** 0. Every change is confined to test files, test config, and devDependencies.

---

## 5 · RELENTLESS-OWNERSHIP SWEEP — WHAT WAS DISCOVERED

While fixing PF-1 through PF-4, the sweep found:

- **PF-5** — Stale copy assertion in `Hub.track_15_4.test.jsx` (dispatch → transportation drift). Same category as PF-1/PF-3 (rebrand-copy edit test not updated). ✅ Fixed in-track.
- **PF-6 (formally deferred)** — See §7 register.

No additional broken tests. No skipped tests. No `test.skip` / `xtest` / `it.skip` anywhere in the touched suites. No unowned orphans.

---

## 6 · PROOF OF ZERO PRODUCTION BEHAVIOR DRIFT

- ✅ **Zero source files under `frontend/src/pages/`, `frontend/src/lib/*.js` (non-test), or `backend/**` were modified in Track 26.09.** Every change is under `src/lib/*.test.js`, `src/lib/__tests__/`, `src/pages/__tests__/`, `craco.config.js`, `package.json`, or `yarn.lock`.
- ✅ **Track 26.08 Daily Report files (`crewMemory.js`, `DraftRestorePrompt.jsx`, `DraftStatusPill.jsx`, `NewDailyReportV3.jsx`) not touched by Track 26.09.** Verified via `git log --oneline -3 -- <paths>` returning only the Track 26.08 commits.
- ✅ **PF-2 doctrine preserved** — I did NOT revert `errorClassification.js:161-163` back to `NETWORK_UNREACHABLE`. The Track 14.0-PLATFORM-STABILITY behavior (return `null` on unknown error) remains the production contract; only the test was aligned to it.
- ✅ **All 216 tests pass** including the 15 Track 26.08 regression locks (G-1 / G-2 / G-3), the 6 Daily Report payload repair tests, the 5 resiliency queue tests, and the 41 error-classification tests.
- ✅ **Backend Daily Report path not exercised by this track** — no backend code touched, no API contract touched, no schema touched.

---

## 7 · REGISTER OF FORMALLY DEFERRED FINDINGS

| Defect ID | Severity | Evidence | Production impact | Owner | Target track | Target date | Reason not fixed in 26.09 |
|---|---|---|---|---|---|---|---|
| **PF-6** | **P3** | The `errorClassification.test.js` timeout scenario `ECONNABORTED (timeout) → network_unreachable` passes today (the timeout branch of `classifyApiError.js` still returns `NETWORK_UNREACHABLE` legitimately). No defect — noted here only because the sweep verified the pass-path is real, not a coincidence with PF-2. | None | — | — | — | Not a defect; recorded as observation |
| **PF-7 (Documentation)** | **P3** | The new Jest `transformIgnorePatterns` allowlist is deliberately narrow. If a future dependency ships ESM-first (e.g. a new `@radix-ui` sub-package), a new test that imports it transitively will fail with the same "Cannot use import statement outside a module" error until the pattern is widened. | None (deferred future dependency, not current) | Any test author adding a new ESM-first dep | Ad hoc — extend `craco.config.js` allowlist per new dep | On-demand | Cannot pre-fix a future dependency; documented so the next author knows the mechanism |

Both deferrals are **not broken tests** — PF-6 is a passing test verified as intentional, and PF-7 is a doc note for future authors. **No known broken/stale/orphaned/skipped test remains unowned.**

---

## 8 · TRACK 26.08 STATUS AFTER 26.09

Track 26.08 (Daily Report Draft/Restore/Continuity):

- ✅ All 15 Track 26.08 regression tests continue to pass (G-1 restore-prompt scope, G-2 crew-memory per-actor, G-3 pill contract states).
- ✅ No Daily Report source file was touched in Track 26.09.
- ✅ Zero production-behavior drift on the DR path.
- ✅ Zero pre-existing failures remain unowned.
- 🟢 **Track 26.08 remains GO for production deploy.**

---

## 9 · FINAL VERDICT

# 🟢 **DONE — no known broken tests remain in the frontend suite**

| Slice | Verdict |
|---|---|
| PF-1 (`errorClassification.test.js` MASCI-title) | ✅ FIXED |
| PF-2 (`errorClassification.test.js` unknown→null contract) | ✅ FIXED (test aligned to Track 14.0 doctrine; source unchanged) |
| PF-3 (`track_15_13h_session_classification.test.js` MASCI-title) | ✅ FIXED |
| PF-4 (`Hub.track_15_4.test.jsx` orphan suite) | ✅ FIXED · **31 real assertions now running** (previously 0) |
| PF-5 (Hub subheadline dispatch→transportation, sweep-discovered) | ✅ FIXED |
| Track 26.08 tests | ✅ 15/15 still pass |
| Full suite | ✅ **216/216 · 11/11 suites · 0 failures · 0 skips · 0 orphans** |
| Production behavior drift | ✅ **zero** — no source files touched, no API/schema touched |
| Track 26.08 GO status | ✅ **remains GO** |

Done means done. Every known broken test is owned. Every fix is anchored to source-line evidence. Every deferred item is formally tracked with severity, owner, and target — none silently ignored.

**Next Action Items:**
- 🟢 Redeploy production to push Track 26.08 (Daily Report draft continuity) + Track 26.09 (test hygiene) changes to mascidocs.com — via "Save to Github" → production build picks up automatically. Note: the test-hygiene changes have no user-facing impact; they're safe to bundle with the 26.08 deploy or ship independently.
- 🟡 Track 26.07 Atlas payload still awaiting user's alert body to definitively close the MongoDB query-targeting hardening.
- ⚪ Track 25 Admin OS resumption still paused per prior directive.

_End of Track 26.09 Frontend Test Suite Hygiene report._
