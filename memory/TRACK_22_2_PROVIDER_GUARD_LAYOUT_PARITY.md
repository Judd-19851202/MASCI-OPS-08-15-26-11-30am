# Track 22.2 Phase B · Provider · Guard · Layout Parity

**Date:** 2026-02-05
🟢 **All three surfaces preserved verbatim.**

## Provider parity

| Provider | Baseline location | Post-refactor location | Δ |
|---|---|---|---:|
| `BrandingProvider` (from `@/lib/BrandingProvider`) | Outermost in `App() return` | Outermost in `App() return` | 0 |

Provider scope is unchanged. `BrandingProvider` wraps the entire chrome + BrowserRouter + `<AppRoutes/>` subtree, exactly as before.

## Guard parity

| Alias | Component | Baseline usages | Post usages | Δ |
|---|---|---:|---:|---:|
| A | RequireAdmin | 65 | 65 | 0 |
| TX | RequireTransportationPortal | 1 | 1 | 0 |
| AP | RequireAdminOrPm | 45 | 45 | 0 |
| APS | RequireAdminPmOrSafety | 3 | 3 | 0 |
| P | RequirePm | 22 | 22 | 0 |
| S | RequireShop | 25 | 25 | 0 |
| H | RequireHr | 28 | 28 | 0 |
| FL | RequireFl | 4 | 4 | 0 |
| SF | RequireSafety | 33 | 33 | 0 |
| DP | RequireDispatch | 10 | 10 | 0 |
| D | RequireDev | 6 | 6 | 0 |

All 11 guard aliases moved verbatim to `AppRoutes.jsx`. Each is still a single-arg lambda wrapping its element in the corresponding `RequireX` component. Zero logic edits. Zero permission surface change.

## Layout parity

The App.js chrome layer (mounted between `BrandingProvider` and `<BrowserRouter>`) is preserved in the exact top-to-bottom order:

1. `<SplashOverlay />`
2. `<Toaster … />`
3. `<QueueStatusPill />`
4. `<OfflineBanner />`
5. `<GlobalKeepalive />`
6. `<BackendStatusBanner />`
7. `<ClusterCapacityBanner />`
8. `<EnvBanner />`
9. `<BannerStrip />`

Router-scoped chrome (inside `<BrowserRouter key={authTick}>`, sibling of `<AppRoutes>`):

1. `<ScrollToTop />`
2. `<EnforcePortalScope />`
3. `<MultiPortalHydrator />`
4. `<IdleTimeout />`
5. `<SessionStatusOverlay />`

Post-`<AppRoutes/>` chrome:

1. `<GlobalFooter />`

**Every mount order preserved byte-identically.** The Suspense boundary that previously wrapped `<Routes>` in App.js now wraps `<Routes>` inside `AppRoutes.jsx` — same semantics, same fallback (`null`).

## Boot effect parity

The App.js `useEffect` at mount time still runs in the exact same order:
1. `validateStoredTokens()` — clears rejected tokens, bumps `authTick`
2. `import("@/lib/usageTracker").then(({ bindRouteChangeTracker }) => bindRouteChangeTracker())` — fire-and-forget analytics
3. `import("@/lib/resiliency").then(({ purgeStaleDrafts }) => purgeStaleDrafts())` — fire-and-forget IndexedDB draft purge

The `authTick` state + `<BrowserRouter key={authTick}>` remount pattern is preserved verbatim.

## `<Suspense fallback={null}>` parity

Baseline: `<React.Suspense fallback={null}><Routes>…</Routes></React.Suspense>` in App.js.
Post-refactor: identical `<React.Suspense fallback={null}><Routes>…</Routes></React.Suspense>` inside `AppRoutes.jsx`.

Fallback semantics unchanged. Lazy-loaded route chunks still show no fallback UI during code-split resolution (this is intentional — the chrome + splash cover the transition window).

## Deep-link + browser history parity

- **Deep links:** verified via Playwright on `/`, `/sign-in`, `/signin` (404 fallback), `/admin/login` — all resolve identically.
- **404 fallback:** `<Route path="*" element={<NotFound />} />` remains the LAST route in AppRoutes.jsx.
- **Browser history:** BrowserRouter with same `key={authTick}` prop; no history API touched.

## Attestation

🟢 **Provider · Guard · Layout parity: 100%.** No user-visible change. No permission change. No layout drift.
