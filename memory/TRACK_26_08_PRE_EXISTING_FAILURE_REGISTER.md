# TRACK 26.08 — PRE-EXISTING FAILURE REGISTER

**Date:** 2026-07-08 UTC · **Preceding gate:** Track 26.08 Daily Report Draft/Restore/Continuity
**Rule:** every failure documented with runtime evidence, git-blame proof, and production-impact analysis. Nothing dismissed casually.

---

## Register — 4 test cases across 3 files

### PF-1 · `src/lib/errorClassification.test.js › 500 → backend_unavailable`

| Field | Value |
|---|---|
| **Test file** | `frontend/src/lib/errorClassification.test.js:40` |
| **Test name** | `classifyApiError · failure paths › 500 → backend_unavailable` |
| **Failure msg** | `Expected: "MASCI Services Temporarily Unavailable"` / `Received: "Services Temporarily Unavailable"` |
| **When it started failing** | **2026-06-22** — commit `2810054e` changed `errorClassification.js:58` from `"MASCI Services Temporarily Unavailable"` → `"Services Temporarily Unavailable"` (rebrand copy edit; test assertion not updated). **~16 days before Track 26.08.** |
| **Fails on main pre-Track-26.08** | ✅ YES — `errorClassification.js:58` unchanged by Track 26.08 (git diff empty for that file). Test failed before my track started. |
| **Production impact** | 🟢 **NONE — cosmetic label drift**. The 500 modal renders with the correct kind, status, retryable, body, and action. Only the two-word title prefix `"MASCI "` was dropped. Users see `"Services Temporarily Unavailable"` (correct) instead of `"MASCI Services…"`. No behavior, routing, or data change. |
| **Domain** | UI error-classification helper. **Zero touch to** Daily Reports · Admin · OCC · Email · AI · PDF · Safety · Dispatch. |
| **Severity** | **P3** (test-assertion drift, cosmetic source label) |
| **Owner / fix track** | Follow-up minor track — update the two test string assertions (2 lines) to match the current source. Not Track 26.08. |

### PF-2 · `src/lib/errorClassification.test.js › unknown error shape → network_unreachable`

| Field | Value |
|---|---|
| **Test file** | `frontend/src/lib/errorClassification.test.js:82` |
| **Test name** | `classifyApiError · failure paths › unknown error shape → network_unreachable (conservative)` |
| **Failure msg** | `Expected: "network_unreachable"` / `Received: null` |
| **When it started failing** | **2026-06-15** — commit `6ef970c3` (Track 14.0-PLATFORM-STABILITY) intentionally CHANGED the "unknown error" branch from `NETWORK_UNREACHABLE` → `null` to STOP false-positive disconnect overlays. Source comment at line 134-141 explicitly documents this: *"Removed the `\|\| true` fallback that previously coerced EVERY no-response error into a NETWORK_UNREACHABLE overlay… the single most important change preventing false-positive disconnect storms."* **~23 days before Track 26.08.** |
| **Fails on main pre-Track-26.08** | ✅ YES — `errorClassification.js` untouched by Track 26.08. This test represents the OLD contract; the source represents the CORRECT NEW contract. |
| **Production impact** | 🟢 **NONE — the fix in Track 14.0 IMPROVED production stability** by preventing false-positive "Connection Problem" modals. The test is stale, not the source. Reverting the source to satisfy the test would REGRESS the platform. |
| **Domain** | UI error-classification helper. **Zero touch to** Daily Reports · Admin · OCC · Email · AI · PDF · Safety · Dispatch. |
| **Severity** | **P3** (stale-test alignment; source is intentionally divergent per doctrine comment) |
| **Owner / fix track** | Follow-up minor track — update this test to expect `kind: null` for unknown errors, matching Track 14.0 doctrine. Not Track 26.08. |

### PF-3 · `src/lib/__tests__/track_15_13h_session_classification.test.js › 520 (Cloudflare) → backend_unavailable`

| Field | Value |
|---|---|
| **Test file** | `frontend/src/lib/__tests__/track_15_13h_session_classification.test.js:66` |
| **Test name** | `TRACK 15.13H · classifyApiError contract › 520 (Cloudflare origin unreachable) → backend_unavailable` |
| **Failure msg** | `Expected: "MASCI Services Temporarily Unavailable"` / `Received: "Services Temporarily Unavailable"` |
| **When it started failing** | **2026-06-22** — same commit `2810054e` as PF-1. The "MASCI" prefix drop affected BOTH tests that assert against the title text. |
| **Fails on main pre-Track-26.08** | ✅ YES — same source file, same untouched-by-26.08 confirmation. |
| **Production impact** | 🟢 **NONE — cosmetic**. The Cloudflare 520 → BACKEND_UNAVAILABLE routing is correct; kind + retryable + status + body all pass. Only the title's "MASCI " prefix is missing. |
| **Domain** | UI error-classification. **Zero touch to** Daily Reports · Admin · OCC · Email · AI · PDF · Safety · Dispatch. |
| **Severity** | **P3** (test-assertion drift, same cosmetic label as PF-1) |
| **Owner / fix track** | Follow-up minor track — one-line assertion update. Bundle with PF-1. |

### PF-4 · `src/pages/__tests__/Hub.track_15_4.test.jsx › Test suite failed to run`

| Field | Value |
|---|---|
| **Test file** | `frontend/src/pages/__tests__/Hub.track_15_4.test.jsx:21` |
| **Test name** | (suite-load failure; no individual tests ran) |
| **Failure msg** | `Cannot find module '@testing-library/react' from 'src/pages/__tests__/Hub.track_15_4.test.jsx'` |
| **When it started failing** | **Ever since the test file was created.** `grep -c "@testing-library" /app/frontend/package.json` = **0**. The `@testing-library/react` dependency was never added to package.json. This test suite has NEVER been able to load in this codebase. Predates Track 26.08 by an unknown-but-large delta. |
| **Fails on main pre-Track-26.08** | ✅ YES — infrastructure gap independent of any source change. `Hub.jsx` source untouched by Track 26.08. |
| **Production impact** | 🟢 **NONE — this test has NEVER run, so it has never caught a regression or blocked a deploy. Its non-existence in the pass rate is the status quo.** |
| **Domain** | Hub landing page component render smoke test. **Zero touch to** Daily Reports · Admin · OCC · Email · AI · PDF · Safety · Dispatch. |
| **Severity** | **P3** (test-infrastructure gap — the file was written before the dep was installed) |
| **Owner / fix track** | Follow-up minor track — either `yarn add -D @testing-library/react @testing-library/jest-dom` or delete the orphan test file. Not Track 26.08. |

---

## Track 26.08 delta — proof of non-relation

```
$ git blame -L 58,58 frontend/src/lib/errorClassification.js
2810054e7 (2026-06-22 17:33:20)  title: "Services Temporarily Unavailable",

$ git blame -L 161,163 frontend/src/lib/errorClassification.js
6ef970c3c (2026-06-15 15:41:29)  if (noResponse) { return { kind: null, ... } }

$ grep -c "@testing-library" /app/frontend/package.json
0

$ git diff HEAD -- frontend/src/lib/errorClassification.js frontend/src/pages/Hub.jsx
(empty — Track 26.08 did not touch either file)
```

Track 26.08 file surface (verifiable):
```
M  frontend/src/lib/resiliency/DraftRestorePrompt.jsx   ← G-1 project+date display
M  frontend/src/lib/crewMemory.js                        ← G-2 per-actor storage key
M  frontend/src/lib/resiliency/DraftStatusPill.jsx       ← G-3 seven contract states
M  frontend/src/pages/NewDailyReportV3.jsx               ← G-3 pill state wiring
A  frontend/src/lib/__tests__/track_26_08_*.test.jsx    ← 15 new PASS tests
```

No overlap with the failing tests' source files.

---

## Aggregate impact matrix

| PF# | Daily Reports | Admin | OCC | Email | AI | PDF | Safety | Dispatch | Deploy blocker? |
|---|---|---|---|---|---|---|---|---|---|
| PF-1 | – | – | – | – | – | – | – | – | 🟢 no |
| PF-2 | – | – | – | – | – | – | – | – | 🟢 no |
| PF-3 | – | – | – | – | – | – | – | – | 🟢 no |
| PF-4 | – | – | – | – | – | – | – | – | 🟢 no |

Zero rows touch the Daily Report critical path or any production-critical subsystem.

---

## Verdict

# 🟢 **GO — none of the 4 pre-existing failures are production-impacting**

Two are stale test assertions against post-rebrand/post-Track-14.0-intentional source (PF-1, PF-2, PF-3 — all cosmetic label + doctrine drift). One is a test infrastructure gap that has never loaded (PF-4). None affect Daily Reports · Admin · OCC · Email · AI · PDFs · Safety · Dispatch.

Track 26.08 is safe to deploy to production. The 4 pre-existing failures should be swept in a **follow-up minor track — "Track 26.09 · Frontend Test Suite Hygiene"** (out of scope now, 5-line update + optional `yarn add -D @testing-library/react`). I have NOT fixed them in this deploy to respect the "focus only on Daily Report draft, autosave, restore, status, and continuity" scope discipline in the Track 26.08 mandate.

If you want me to sweep them now before deploy, say the word — the fix for PF-1/PF-2/PF-3 is 5 lines total, PF-4 is either `yarn add` or delete.

_End of Track 26.08 Pre-existing Failure Register._
