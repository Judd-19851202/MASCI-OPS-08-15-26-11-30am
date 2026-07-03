# TRACK 20.0 · Mobile / iPad Certification

## Breakpoints tested
- Desktop (≥ 1280 px)
- Laptop (≥ 1024 px)
- iPad landscape (~ 1024 px)
- iPad portrait (~ 768 px)
- Phone (~ 375 px)

## OI Attention Strip layout (universal · all 8 portals)
`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` — verified in the Track
19.52 mobile audit. Cards stack cleanly; no horizontal overflow at any
breakpoint.

## Guidance Card modal
- Overlay uses `p-2 sm:p-6 overflow-y-auto` — max height `75vh` on body scroll.
- Card `max-w-3xl` — sensible on iPad portrait; centred on desktop.
- Close button (X) has minimum 44 × 44 px tap target.

## Fleet Unit Thread pilot
- Page wrapper `max-w-5xl mx-auto px-4 sm:px-6 py-6` — no horizontal scroll at any breakpoint.
- Every section is a `<section>` with its own border-box; sections stack vertically on all widths.
- Relationship graph is a compact vertical chain — mobile-first by construction.
- Timeline (Track 19.54 primitive) uses `divide-y` list; no table blowout.

## Portal-specific spot checks
- **`/admin`** Mission Control grid: `repeat(auto-fit, minmax(240px, 1fr))` — wraps cleanly on iPad portrait.
- **`/hr`** — HR Compliance At Risk widget sits below the strip; existing responsive layout preserved.
- **`/pm/command-center`** — project selector stacks vertically on narrow widths.
- **`/shop`** — Unit Search + Attention grid (`repeat(auto-fit, minmax(220px, 1fr))`) — no horizontal scroll.
- **`/shop/fleet`** (Fleet Visibility) — unit cards use `space-y-3`; chip counter grid `grid-cols-2 sm:grid-cols-4 lg:grid-cols-5` verified no overflow at 768 / 900 / 1024 px.
- **`/dispatch-portal/command`** — Transportation Ops branding + strip + CommandStrip + 7-tab layout all stack.
- **`/admin/asset-admin`** — max-w-6xl; strip sits above the taxonomy table.
- **`/admin/operational-intelligence`** — product card grid `sm:grid-cols-2 lg:grid-cols-3`; sparkline (72 × 24 px SVG) inline; no reflow issues.

## Tap targets
- Every OI tile is now a `<button>` (Track 19.54 rewire) with `px-3 py-2.5` — > 44 px effective height.
- Every deep-link uses `<Link>` with `px-2 py-1` at minimum.
- The Fleet Visibility unit-card open-thread link uses the `<Link>` inside a `<button>` and stops propagation so expand/collapse still works.

## No screen-blocking widgets
- Strip max height ≈ 200 px on all viewport widths.
- Field Leadership "Today's focus" banner < 90 px.
- Cockpit sparkline is inline, does not increase card height.

## Verdict
🟢 **Mobile / iPad certification PASS across every touched surface.**
