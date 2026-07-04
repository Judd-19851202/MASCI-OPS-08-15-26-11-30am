# TRACK 22.2 · Provider + Chrome Graph

**Date:** 2026-02-04

## Provider mounts (App() render tree)
| Order | Component | Line | Source |
|---:|---|---:|---|
| 1 | `<BrandingProvider>` | 457 | `@/lib/BrandingProvider` |

## Chrome components (mounted between `<BrandingProvider>` and `<BrowserRouter>`)
Order preserved from App.js lines 458–482.

| Order | Component | Purpose |
|---:|---|---|
| 1 | `<SplashOverlay />` | Splash-until-ready overlay |
| 2 | `<Toaster ... />` | Sonner toast root |
| 3 | `<QueueStatusPill />` | Global queue visibility pill (R-BL-3) |
| 4 | `<OfflineBanner />` | Track 14.0-RC1 D3 · offline trust ribbon |
| 5 | `<GlobalKeepalive />` | Global keepalive ping |
| 6 | `<BackendStatusBanner />` | Backend reachability banner |
| 7 | `<ClusterCapacityBanner />` | Cluster capacity banner |
| 8 | `<EnvBanner />` | Environment banner (preview/prod) |
| 9 | `<BannerStrip />` | Banner strip host |

## Router-scoped children (mounted INSIDE `<BrowserRouter>`)
| Order | Component | Line | Purpose |
|---:|---|---:|---|
| 1 | `<ScrollToTop />` | 474 | Scroll restoration |
| 2 | `<EnforcePortalScope />` | 475 | Portal scope enforcement |
| 3 | `<MultiPortalHydrator />` | 476 | Multi-portal state hydration |
| 4 | `<IdleTimeout />` | 477 | Session idle timeout |
| 5 | `<SessionStatusOverlay />` | 481 | TRUST-DIAGNOSTICS-001 global overlay |

## Constitutional invariant
The new architecture MUST preserve:
- **Provider order:** `BrandingProvider` remains the outermost provider (or is composed via `<AppProviders>` with identical outer→inner order).
- **Chrome mount order:** exact top-to-bottom sequence above.
- **Router-scoped children:** must remain siblings of `<Routes>` inside `<BrowserRouter>`, in the exact order above.
- **`key={authTick}`** on `<BrowserRouter>` — token-validation remount pattern MUST be preserved.
- **`<React.Suspense fallback={null}>`** boundary around `<Routes>` MUST be preserved.

## Boot effects (App() useEffect body — lines 436–453)
| Effect | Trigger | Behavior |
|---|---|---|
| `validateStoredTokens()` | mount | Ping 4× `/check` endpoints; clear rejected tokens; bump `authTick` |
| `import("@/lib/usageTracker")` | mount | Fire-and-forget usage analytics binder |
| `import("@/lib/resiliency").purgeStaleDrafts()` | mount | Fire-and-forget IndexedDB draft purge (>14d) |

All three MUST fire in the same order on the new shell. Recommended placement: `app/boot/index.js` re-exporting a `useAppBootEffects()` hook consumed once by the App shell.
