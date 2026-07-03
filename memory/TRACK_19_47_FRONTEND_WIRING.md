# TRACK 19.47 · Frontend Wiring

## Files touched
| File | Change |
|---|---|
| `/app/frontend/src/pages/admin/AdminOperationalIntelligence.jsx` | NEW — Cockpit page (~500 lines). |
| `/app/frontend/src/App.js` | Additive route `/admin/operational-intelligence` + lazy import. |
| `/app/frontend/src/components/AdminShell.jsx` | Additive nav entry (`operational-intelligence` section). |

## Route registration
```js
const AdminOperationalIntelligence = React.lazy(() =>
  import("@/pages/admin/AdminOperationalIntelligence"));

<Route path="/admin/operational-intelligence"
       element={A(<AdminOperationalIntelligence />)} />
```

The `A(...)` wrapper is the shared admin auth gate — Cockpit inherits
the identical protection every other `/admin/*` page uses.

## Nav entry
```
{ key: "operational-intelligence", to: "/admin/operational-intelligence",
  icon: Activity, label: "Operational Intelligence",
  desc: "Scores · previews · history · audit for all 11 intelligence products" }
```

Added directly below `Weekly Digest` for discoverability.

## State model
Local React state only. No new client-side stores, no new context, no
new hooks. The page holds:
- `summary` — one-shot payload from `/summary`.
- `previewProduct` / `previewHtml` / `previewError` — preview drawer.
- `dryRunProduct` / `dryRunResult` — dry-run drawer.
- `historyProduct` / `historyRows` / `historyLoading` — history drawer.
- `auditProduct` / `auditRows` / `auditLoading` — audit drawer.

## Component structure
- `AttentionChip` — colour-coded LOW/MEDIUM/HIGH/CRITICAL.
- `ScoreChip` — score + trend arrow + optional %.
- `TopStrip` — 6-column KPI strip with worst/best + failures.
- `ProductCard` — one card per product.
- `DrawerShell` — right-side slide-over used by all four drawers.
- `PreviewBody` — sandboxed iframe rendering backend HTML.
- `TablePanel` — reusable table for history + audit drawers.

## API wiring (single axios instance)
Every request goes through the shared `@/lib/api` axios client, which
already attaches the admin token, handles session-expiry, and honours
`REACT_APP_BACKEND_URL`.

## Test-ID contract
The page exposes `data-testid` on every interactive element:
`admin-operational-intelligence`, `oi-cockpit-top-strip`,
`oi-product-grid`, `oi-product-card-{product_id}`,
`oi-preview-btn-{product_id}`, `oi-dryrun-btn-{product_id}`,
`oi-history-btn-{product_id}`, `oi-audit-btn-{product_id}`,
`oi-refresh-btn`, `oi-recipient-governance-entry`,
`oi-{preview|dryrun|history|audit}-drawer`, and drawer-body
identifiers for iframe / result / tables.
