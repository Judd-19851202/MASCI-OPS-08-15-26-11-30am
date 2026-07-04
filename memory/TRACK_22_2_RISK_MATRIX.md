# TRACK 22.2 · Risk Matrix

**Date:** 2026-02-04

| # | Risk | Likelihood | Impact | Mitigation | Class |
|---:|---|---|---|---|---|
| 1 | Route ordering change breaks first-match semantics of `<Routes>` (React Router v6) | Med | High | Preserve exact ordering per `APP_JS_INVENTORY.json.routes[].line`; harness diffs ordered path list | A |
| 2 | Chunk name change invalidates CDN caches, spikes cold-load latency | Med | Med | Use webpack magic-comment `/* webpackChunkName: "…" */` if chunk names shift; bundle report before/after | B |
| 3 | Lazy → eager (or vice-versa) accidentally flipped for a route | Low | Med | Harness compares `load` field per route; must match | B |
| 4 | Provider order change breaks context resolution (e.g., Toaster before BrandingProvider) | Low | High | Provider graph doc specifies exact outer→inner order | A |
| 5 | Boot-effect ordering change (`validateStoredTokens` → `usageTracker` → `purgeStaleDrafts`) | Low | Med | Extract effects into single hook; call once from App shell in same order | B |
| 6 | `<BrowserRouter key={authTick}>` remount pattern lost during shell rewrite | Med | High | Explicit test: rotate a token, confirm authTick bumps and router remounts | A |
| 7 | `<Suspense fallback={null}>` boundary displaced above/below `<Routes>` | Low | Med | Suspense wraps Routes exactly as today; harness inspects React tree via Playwright | B |
| 8 | Guard alias reused with same letter for different component (e.g., new `A` alias meaning "Academy" somewhere) | Low | High | Guards centralized in `guards/aliases.jsx`; no alias reuse anywhere else | A |
| 9 | `RequireX` internal logic quietly changed during extraction | Low | Critical | Guards are re-exported, not rewritten; no logic edits allowed | A |
| 10 | Bundle size regresses due to duplicated barrel imports | Med | Med | Bundle report gate; if regressed, prune barrel files | B |
| 11 | Comment-block deletions accidentally remove active code | Low | Med | Only delete lines flagged in DEAD_CODE_REPORT; every deletion diff reviewed | C |
| 12 | Analytics binder (`usageTracker`) no longer fires on route change | Low | Med | Playwright asserts `bindRouteChangeTracker` global hook is invoked on route transition | B |
| 13 | Playwright depth insufficient — regression escapes to prod | Med | High | Per-portal auth-gated smoke + deep-link + back/forward + refresh + console-clean + network-clean | A |
| 14 | Context budget exhausted mid-refactor → hybrid App.js + partial `src/app/` | Med | Critical | STOP per Constitution — this session already executed this fallback correctly | A |
| 15 | Email safety regressed by touching frontend chrome (`BackendStatusBanner` shows real backend URL) | Low | Low | Frontend can never send email; risk is informational only. Playwright asserts no `mailto:` links added | C |

## Class definitions
- **A · Constitutional blocker** — must be prevented / caught before merge
- **B · Test-gated** — must be caught by harness or Playwright
- **C · Informational** — recorded for auditor; does not block

## Overall risk posture
The refactor is well-defined and mathematically parity-checkable. The primary residual risk is **context exhaustion mid-execution**, which the Constitution addresses (option a for question 4: STOP with full inventory). That option has been exercised in this session.
