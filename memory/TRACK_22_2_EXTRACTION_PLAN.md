# TRACK 22.2 · Extraction Plan

**Date:** 2026-02-04
**Executor:** Next session (fresh context).

## Target directory structure

```
frontend/src/app/
├── App.jsx                     # NEW — orchestration shell (~60 lines)
│                                 - <BrandingProvider>
│                                 - chrome components in exact order
│                                 - <BrowserRouter key={authTick}>
│                                 - <React.Suspense>{<AppRoutes/>}
├── routing/
│   ├── AppRoutes.jsx           # <Routes> assembly; imports all feature-routes
│   └── index.js
├── providers/
│   ├── AppProviders.jsx        # composed provider stack (currently just BrandingProvider)
│   └── index.js
├── layouts/                    # placeholder — no layouts extracted currently
├── guards/
│   ├── aliases.jsx             # A, TX, AP, APS, P, S, H, FL, SF, DP, D + Require* re-exports
│   └── index.js
├── boot/
│   ├── useAppBootEffects.js    # validateStoredTokens + usageTracker + purgeStaleDrafts
│   └── index.js
├── feature-routes/
│   ├── public.jsx              # /, /revise/:token
│   ├── safety.jsx              # 55 routes
│   ├── admin.jsx               # 99 routes
│   ├── pm.jsx                  # 44 routes
│   ├── hr.jsx                  # 31 routes
│   ├── shop.jsx                # 26 routes
│   ├── dispatch.jsx            # 14 routes
│   ├── field-leadership.jsx    # 13 routes
│   ├── trench-safety.jsx       # 7 routes
│   ├── incidents.jsx           # 6 routes
│   ├── fleet.jsx               # 6 routes
│   ├── odr.jsx                 # 5 routes
│   ├── dev.jsx                 # 5-7 routes (D-guarded + dev misc)
│   ├── qaqc.jsx                # 4 routes
│   ├── meetings.jsx            # 4 routes
│   ├── daily.jsx               # 4 routes
│   ├── training.jsx            # 4 routes
│   ├── operations.jsx          # 4 routes
│   ├── constraints.jsx         # 3 routes
│   ├── jha.jsx                 # 3 routes
│   ├── equipment.jsx           # 3 routes
│   ├── guidance.jsx            # 3 routes
│   ├── field.jsx               # 2 routes
│   ├── transportation.jsx      # 2 public + 1 TX-guarded shell = 3 routes
│   ├── driver.jsx              # 2 + 1 driver-public = 3 routes
│   ├── ops-training.jsx        # 2 routes
│   ├── legal.jsx               # 2 routes
│   ├── misc.jsx                # remaining ~24 single-route buckets + /* catch-all
│   └── index.js                # re-exports all *routes arrays
└── index.js                    # re-exports <App/> for src/index.js
```

Total: **28 files** under `frontend/src/app/` (target), replacing the current single 1,283-line `App.js`.

## Extraction order (safe, one PR at a time — but all in one execution window)

1. **Bootstrap** — create empty scaffolding + `guards/aliases.jsx` re-exporting the 11 alias factories.
2. **Boot effects** — extract useEffect body → `boot/useAppBootEffects.js`.
3. **Providers** — wrap `<BrandingProvider>` in `AppProviders`.
4. **Chrome + routes shell** — extract chrome + `<BrowserRouter>` scaffolding into `App.jsx`.
5. **Public routes first** — extract `feature-routes/public.jsx` (2 routes) and prove parity harness green.
6. **Safety / Admin / PM / HR / Shop / Dispatch / FL** — extract in order of route count.
7. **Small groups** — remaining <10-route buckets.
8. **Catch-all** — `/*` at the very end of the routes array (preserve current ordering — no route re-ordering allowed).
9. **Delete old `App.js`**; update `src/index.js` to `import App from "@/app"`.
10. **Re-run parity harness** — JSON diff MUST be empty.
11. **Playwright** — per-portal auth-gated smoke.
12. **Bundle report** — `yarn build` before/after; chunk count + total size ≤ before.

## Parity harness protocol

```bash
# Pre-refactor snapshot (this session)
python3 /app/memory/track_22_2/extract_app_js_inventory.py
cp /app/memory/track_22_2/APP_JS_INVENTORY.json \
   /app/memory/track_22_2/APP_JS_INVENTORY.before.json

# Post-refactor: extractor points at the new tree
# (modify extractor to walk feature-routes/*.jsx via the same regex,
#  OR make it aggregate every <Route> across all *.jsx files under src/app)
python3 /app/memory/track_22_2/extract_app_js_inventory.py --tree src/app
diff /app/memory/track_22_2/APP_JS_INVENTORY.before.json \
     /app/memory/track_22_2/APP_JS_INVENTORY.after.json
# Expected: empty diff (or only line-number deltas, which the harness normalizes)
```

The harness must normalize `line` fields (extraction from a different file structure will change line numbers). Comparison is on `(path, guard_alias, guard_component, target_component, load)` tuples set-equality, and on ordered `path` list (route ordering matters for `<Routes>` first-match semantics).

## Playwright coverage matrix

| Portal | Auth-gated entry | Deep link | Back/forward | Refresh | Layout | Providers | Console-clean | Network-clean |
|---|---|---|---|---|---|---|---|---|
| Public / (Hub) | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Login (admin) | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin | `A` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PM | `P` / `AP` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HR | `H` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safety | `SF` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dispatch | `DP` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Shop | `S` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Training/Academy | *(public)* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Operations | *(public)* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Field Leadership | `FL` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Transportation-Ops | `TX` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Public field forms | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Bundle report

Run `yarn build` before and after; capture:
- Total gzipped size
- Chunk count
- Largest chunk name + size
- Suspense boundary triggering (verify lazy chunks still load on route hit)

**Acceptance:** `after ≤ before` on every metric. Zero regression.

## STOP triggers during Phase B execution

Abort and hand off (again) if any of the following occurs mid-extraction:
- Parity harness `after` diff not empty
- Playwright any single portal fails smoke
- `yarn build` errors or bundle size regresses
- Any Require* guard rewrites its logic
- Any lazy target's chunk name changes (potential CDN cache invalidation)
- Any console error appears on portal entry
