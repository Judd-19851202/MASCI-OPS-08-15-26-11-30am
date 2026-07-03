# TRACK 19.52 · Mobile / iPad Review

## OiAttentionStrip layout classes
```
grid-cols-1  sm:grid-cols-2  lg:grid-cols-3
```
- Mobile (<640px): single-column tiles · full width · no horizontal overflow.
- iPad portrait (≥640px): 2 tiles per row · matches Safety/HR max product count of 2.
- Desktop (≥1024px): up to 3 tiles per row.

## Per-portal verification

### `/safety-portal` (SafetyHubV2)
- Mobile: strip renders as one full-width tile (safety_morning_digest) above the CAPA grid.
- iPad portrait: same — one tile · calm spacing.
- iPad landscape / desktop: one tile, aligned left inside the grid container.
- No horizontal scroll.

### `/hr` (HrHubV2)
- Mobile: two full-width tiles stacked (hr_intelligence, training_intelligence).
- iPad portrait: 2 tiles in one row.
- Desktop: 2 tiles in one row.
- No horizontal scroll.

### `/pm/command-center` (PmCommandCenter)
- Mobile: one full-width tile (project_intelligence).
- Sits directly above the project selector — no overlap with the tab bar.
- No horizontal scroll.

### `/shop` (ShopHubV2)
- Mobile / iPad / desktop: one tile · sits above Unit Search.
- Existing horizontal PriorityMetric grid below (`repeat(auto-fit, minmax(220px, 1fr))`) unchanged.
- No horizontal scroll.

### `/shop/fleet` (FleetVisibility)
- Mobile: one full-width tile (fleet_intelligence).
- iPad portrait: same — sits directly under the FocusBanner.
- Existing chip counter grid: `grid-cols-2 sm:grid-cols-4 lg:grid-cols-5` — verified not to cause overflow at 768px (iPad portrait), 900px, or 1024px (iPad landscape). Chips flow to a second row cleanly when needed.
- Unit list: responsive `space-y-3` — no table, no fixed-width columns.
- No horizontal scroll.

## Reachability
- Every tile is a `<Link>` — tap target size ≥ 44px on all touched portals.
- "Open in Cockpit" link uses `min-h`-safe padding (px-y-y).

## Cards stack correctly
- Under `sm` (mobile): all strips collapse to 1-column.
- Under `lg` (desktop): strip grid never exceeds 3 columns (Safety/PM/Shop/Fleet have 1 product; HR has 2 → both fit).

## No screen-blocking widgets
- Strip is a compact section (< 200px tall on all viewport widths).
- Does not overlay sidebar, header, or existing action rows.

## Loading / empty / error states
- Loading: single-row inline text "Loading OI signals…" · does not shift layout.
- Empty (auth failure or no products): honest 1-line empty state · does not shift layout.
- Per-tile error: "Insufficient data · consult Cockpit." — never fake numbers.
