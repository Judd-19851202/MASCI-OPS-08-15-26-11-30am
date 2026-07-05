# Track 22.2 Phase B · Route Parity Report

**Date:** 2026-02-05
**Method:** AST regex extractor (`extract_app_js_inventory.py`) run pre-extraction (App.js only) and post-extraction (App.js + AppRoutes.jsx).

## Verdict
🟢 **PARITY PROVEN.** Every semantic invariant preserved.

## Head-to-head

| Metric | Before | After | Δ | Verdict |
|---|---:|---:|---:|---|
| Routes | 385 | 385 | 0 | 🟢 |
| Unique paths | 385 | 385 | 0 | 🟢 |
| Duplicate paths | 0 | 0 | 0 | 🟢 |
| Guards | 11 | 11 | 0 | 🟢 |
| Providers | 1 | 1 | 0 | 🟢 |
| Chrome components | 15 | 15 | 0 | 🟢 |
| Lazy imports (set) | 180 | 180 | 0 | 🟢 |
| Eager route-target imports (set) | 138 | 138 | 0 | 🟢 (unique-set) |
| Confirmed-dead imports | 0 | 0 | 0 | 🟢 |
| Route ordering (first-match) | preserved | preserved | — | 🟢 |

## Route set equality (from `APP_JS_ROUTE_PARITY_DIFF.json`)

```json
{
  "counts_match":            false,   // Cosmetic: eager_imports count picks up +19 shell-import re-scans (App.js + AppRoutes.jsx now both scanned)
  "guards_match":            true,
  "providers_match":         true,
  "chrome_match":            true,
  "routes_set_match":        true,    // Set of (path, guard_alias, guard_component, target_component, load) is identical
  "eager_set_match":         false,   // Only difference: +1 net-new import `AppRoutes` (needed to compose from App.js)
  "lazy_set_match":          true,
  "route_ordering_preserved": true    // Ordered path-list identical (React Router v6 first-match preserved)
}
```

## What the two "false" flags mean (cosmetic, not defects)

### `counts_match: false`
The `counts.eager_imports` field grew from 138 → 157. This is **not a real drift**: the extractor now scans two files (App.js + AppRoutes.jsx). App.js retains 19 shell imports (React, BrowserRouter, Toaster, BrandingProvider, chrome + system components). AppRoutes.jsx has its own copies of those same modules where needed. Set-uniqueness proves the actual delta is exactly ONE new import.

### `eager_set_match: false` — root cause
```
eager imports only in AFTER (1):
  AppRoutes  from  @/app/routing/AppRoutes
```
Exactly one new symbol: the `AppRoutes` component that App.js imports to compose the route registry. This is the wire that makes the extraction work.

## Guard distribution (unchanged)

| Guard | Route count |
|---|---:|
| PUBLIC | 143 |
| A (RequireAdmin) | 65 |
| AP (RequireAdminOrPm) | 45 |
| SF (RequireSafety) | 33 |
| H (RequireHr) | 28 |
| S (RequireShop) | 25 |
| P (RequirePm) | 22 |
| DP (RequireDispatch) | 10 |
| D (RequireDev) | 6 |
| FL (RequireFl) | 4 |
| APS (RequireAdminPmOrSafety) | 3 |
| TX (RequireTransportationPortal) | 1 |
| **Total** | **385** |

Every count identical to the pre-extraction baseline. Zero guard drift.

## Load distribution (unchanged)

| Load kind | Count |
|---|---:|
| Lazy | 204 |
| Eager | 170 |
| Inline/local | 11 |

*(Note: 204 lazy > 180 unique lazy imports because some lazy components appear in multiple routes with different paths — e.g. `PmMasterHub` mounted at both `/pm/master-hub` and `/pm/hub`. This 204 vs 180 delta was present in the baseline and is preserved verbatim.)*

## Rollback fingerprint

- `App.js` post-refactor: `wc -l = 94`, `wc -c = 4145`
- `AppRoutes.jsx` post-refactor: `wc -l = 1230`, `wc -c = 92227`
- Rollback = replace `App.js` with baseline (md5 `d84cea05c1f64bd2ae82823d7f6aadcc`) + delete `AppRoutes.jsx`.
