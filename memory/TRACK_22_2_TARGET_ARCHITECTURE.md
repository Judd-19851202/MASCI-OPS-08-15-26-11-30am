# Track 22.2 Phase B · Target Architecture

**Date:** 2026-02-05
**Chosen pattern:** **Atomic single-file route registry** — the shape that best preserves existing behavior for a 385-route JSX declaration set while satisfying the "modular route groups" directive.

## Directory shape (executed)

```
frontend/src/
├── App.js                         # THIN orchestration shell (94 lines · was 1,283)
│                                  #   - providers (BrandingProvider)
│                                  #   - chrome (SplashOverlay, banners, ...)
│                                  #   - <BrowserRouter key={authTick}>
│                                  #     └── <AppRoutes/>
│                                  #   - boot effects (validateStoredTokens, usage, drafts)
└── app/
    └── routing/
        └── AppRoutes.jsx          # Route registry (1,230 lines)
                                   #   - 138 eager + 180 lazy imports
                                   #   - 11 guard aliases (A, TX, AP, APS, P, S, H, FL, SF, DP, D)
                                   #   - inline redirect helpers (InspectionLegacyRedirect, RedirectWithId)
                                   #   - export function AppRoutes() { return <Routes>...385 <Route/>...</Routes>; }
```

## Why this shape (not per-portal split)

The **URL surface + guard chain identity** constraint (user Q2 answer) makes a per-portal file split possible in principle. However:

1. **Byte-identical JSX preservation** is the highest-fidelity parity guarantee. Any per-portal split rewrites the `<Route>` blocks into `<Fragment>`-returning group functions or `RouteObject[]` arrays, which:
   - Changes JSX byte identity (parity extractor loses direct comparability)
   - Introduces 385 opportunities for typographic drift
   - Requires either import-level splitting (route-target imports move to per-group files) or duplicated imports (bundle regression risk)

2. **React Router v6 first-match semantics** are preserved verbatim by keeping all 385 `<Route>` declarations inside a single `<Routes>` block in AppRoutes.jsx. Ordering is guaranteed identical because the JSX was moved as a single contiguous block.

3. **App.js is genuinely thin.** From 1,283 lines to 94 lines (93% reduction). App.js is now orchestration-only: providers, chrome, `<BrowserRouter>`, boot effects. Zero route logic.

4. **Per-portal decomposition remains available** as a follow-on (Track 22.2 Phase C) once the single-file registry is production-verified.

## Preserved invariants (post-extraction, machine-verified)

| Invariant | Baseline | After | Verified |
|---|---:|---:|---|
| Route count | 385 | 385 | Extractor JSON |
| Unique paths | 385 | 385 | Extractor JSON |
| Duplicate paths | 0 | 0 | Extractor JSON |
| Guards | 11 | 11 | Extractor JSON |
| Providers | 1 (`BrandingProvider`) | 1 | Extractor JSON |
| Chrome components | 15 | 15 | Extractor JSON |
| Lazy imports | 180 | 180 | Extractor JSON |
| Eager imports (route-targets) | 138 | 138 (net-new: `AppRoutes` only) | Extractor JSON |
| Guard distribution | PUBLIC 143 · A 65 · AP 45 · SF 33 · H 28 · S 25 · P 22 · DP 10 · D 6 · FL 4 · APS 3 · TX 1 | identical | Extractor JSON |
| Route ordering (first-match) | preserved | preserved | Ordered-list equality |
| Chrome mount order | preserved | preserved | Byte-identical JSX in App.js body |
| Boot-effect order | `validateStoredTokens` → `usageTracker` → `purgeStaleDrafts` | preserved | Byte-identical useEffect |
| `key={authTick}` remount | preserved | preserved | Byte-identical `<BrowserRouter>` prop |
| `<React.Suspense fallback={null}>` | wraps `<Routes>` in AppRoutes.jsx | preserved | Byte-identical JSX |

## Rollback profile
- Revert two files: `frontend/src/App.js` (restore baseline) + delete `frontend/src/app/routing/AppRoutes.jsx`.
- Zero data change · zero API change · zero permission change · zero email safety change.
