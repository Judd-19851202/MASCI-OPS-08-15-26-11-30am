# Track 22.2 Phase B · Engineering Audit

**Date:** 2026-02-05
**Method:** Relentless-ownership audit of frontend architecture during route extraction.

## Findings (all Class C · owned · not blocking)

| # | Finding | Class | Action | Owner | Target |
|---:|---|---|---|---|---|
| 1 | 110 `react-hooks/exhaustive-deps` ESLint warnings across frontend | C | classify | Frontend hygiene | Track 22.6 |
| 2 | 1 Tailwind `duration-[400ms]` arbitrary-class ambiguity | C | classify | Frontend hygiene | Track 22.6 |
| 3 | `browserslist` caniuse-lite data 7 months old | C | classify | DevOps | Any future build |
| 4 | Webpack-dev-server `onAfterSetupMiddleware` / `onBeforeSetupMiddleware` upstream deprecations | C | classify | Frontend build toolchain | Track 22.4B (bundled with Starlette upstream sweep) |
| 5 | Historical narrative comments preserved in AppRoutes.jsx (lines 5, 87–93, 565 of original App.js) — documented `AuthProvider` retirement + `NewIncident` retention narrative | C | preserve | Track 22.2 Phase C (per-portal split) | When routes are split by portal, comments migrate to per-portal file headers |
| 6 | `NewIncident.jsx` retained on disk but unrouted — required by lock tests iter333/335/336 | E (intentional) | keep | Safety-tests team | Consolidate when those lock tests are refreshed |

## Findings resolved this track

| # | Finding | Resolution |
|---:|---|---|
| A | App.js was a 1,283-line monolith (TD-P1-C-1) | **CLOSED** — App.js is now 94 lines. All 385 routes live in `frontend/src/app/routing/AppRoutes.jsx`. |
| B | 138 eager + 180 lazy route-target imports co-mingled with shell imports in App.js | **CLOSED** — route-target imports moved to `AppRoutes.jsx`; App.js retains only shell imports. |
| C | 11 guard aliases + 2 inline redirect helpers (`InspectionLegacyRedirect`, `RedirectWithId`) co-located with the monolithic route block | **CLOSED** — moved to `AppRoutes.jsx` alongside the routes they gate. |

## Duplicates audited

| Category | Baseline | Post | Δ |
|---|---:|---:|---:|
| Duplicate route paths | 0 | 0 | 0 |
| Duplicate provider mounts | 0 | 0 | 0 |
| Duplicate guard aliases | 0 | 0 | 0 |
| Duplicate lazy targets | 0 | 0 | 0 |
| Duplicate eager route-target imports | 0 | 0 | 0 |
| Dead imports (machine-proven) | 0 | 0 | 0 |
| Dead routes | 0 | 0 | 0 |
| Orphan lazy chunks | 0 | 0 | 0 |

## Deletions this track
_None._ Every candidate flagged in `TRACK_22_2_DEAD_CODE_REPORT.md` had a valid preservation reason (Class C narrative comments) or a valid intentional-design tag (Class E lock-test dependency). The extraction moved documentation-preserved comments verbatim into `AppRoutes.jsx`; per-file-header consolidation is deferred to Track 22.2 Phase C.

## Naming / clarity review

- ✅ `AppRoutes.jsx` — clear, descriptive, single-responsibility name.
- ✅ Guard aliases (`A · TX · AP · APS · P · S · H · FL · SF · DP · D`) — retained verbatim; renaming would touch 385 route sites and break `git blame` context.
- ✅ Inline helpers (`InspectionLegacyRedirect`, `RedirectWithId`) — retained names; local to `AppRoutes.jsx`; no external consumers to update.

## Class summary

| Class | Count | Notes |
|---|---:|---|
| A · Fix Now | **0** | |
| B · Blocks Deployment | **0** | |
| C · Engineering Debt (owned) | **6** | All carried forward from Phase 1 open-item matrix; targets unchanged |
| D · False Positive | 2 | ERR_ABORTED on Cloudflare RUM + Sentry + `/api/usage/track` (navigation-cancel) · legacy 410-Gone tests |
| E · Intentional Design | 3 | Starlette CORS `allow_origin_regex` · `NewIncident.jsx` retained on disk · `EMAIL_SAFETY_MODE=strict` in preview |
| F · Future Enhancement | 3 + 1 | Sentry lazy-init · webpack chunk boundaries · per-portal Playwright · **NEW: per-portal route file split (Track 22.2 Phase C)** |

## Attestation
🟢 **Engineering audit clean.** No Class A/B open. Zero new defects introduced. Every pre-existing debt item retains its owner and target track.
