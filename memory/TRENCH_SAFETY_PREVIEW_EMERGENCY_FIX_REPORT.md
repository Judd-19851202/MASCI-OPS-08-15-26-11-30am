# TRENCH SAFETY · PREVIEW EMERGENCY FIX REPORT

**Mode:** Emergency surgical fix · zero new features
**Date:** 2026-02
**Trigger:** Preview compile blocked. Public Safety Tile still labelled "Trench Box Tabulated Data".

## Issue 1 — Preview compile failure

### Root cause
During Phase 5 I added two `// eslint-disable-next-line react-hooks/set-state-in-effect ...` comments to `src/pages/AssetTransfers.jsx` at lines 92 and 365 to silence what I believed were pre-existing lint errors from the lint MCP tool.

The MCP lint tool uses its own ESLint configuration with the React-Compiler plugin enabled (`react-hooks/set-state-in-effect` rule is part of `eslint-plugin-react-hooks` >=5.x). However, **Create React App's compile-time ESLint configuration does NOT include this rule**. When the CRA dev server's webpack-eslint integration encountered my disable comments, it failed with:

```
src/pages/AssetTransfers.jsx
  Line 92:5:   Definition for rule 'react-hooks/set-state-in-effect' was not found
  Line 365:5:  Definition for rule 'react-hooks/set-state-in-effect' was not found
webpack compiled with 1 error
```

Net effect: the CRA preview overlay showed the compile error and the page never rendered past the loading splash.

### Fix
Removed both `eslint-disable-next-line` comments from `AssetTransfers.jsx`. No functional code changed. No dispatch / transfer behavior altered.

### Verification
```
[supervisor] frontend.out.log:
  Compiling...
  Compiled successfully!
  webpack compiled successfully
```

Visual confirmation via Playwright screenshot of `/safety`: page renders fully (no overlay). The Safety Section tile grid loads with all 7 tiles visible.

## Issue 2 — Public Safety Tile mislabelled

### Root cause
`pages/SafetySection.jsx` (the public Safety entry point) hosted a tile labelled `"Trench Box Tabulated Data"` pointing to the legacy `/trench-boxes` library route. The directive requires the **public** Safety Tile to surface the full Trench Safety field portal (asset lookup, QR scan, tabulated data, reporting), with title "Trench Safety".

### Fix
Edited `pages/SafetySection.jsx::SafetyTile` for the trench entry only:
- `to`: `/trench-boxes` → `/trench-safety` (the public Trench Safety landing page).
- `title`: `Trench Box Tabulated Data` → `Trench Safety`.
- `desc`: rewritten to describe the full public field surface.
- `ctaLabel`: `OPEN LIBRARY` → `OPEN TRENCH SAFETY`.
- `testId`: kept as `safety-tile-trench` (no test break).

Spanish translations added for the two new strings (`OPEN TRENCH SAFETY` and the new desc).

### Verification
Playwright DOM inspection of `[data-testid='safety-tile-trench']`:
- href: `/trench-safety` ✅
- text: `Trench Safety` · Field-facing entry point for the MASCI Trench Safety system — asset lookup, QR scan landing, tabulated data, safety reference, and damage / unsafe / missing-pin / missing-label reporting. Bilingual. · `OPEN TRENCH SAFETY →` ✅

## Preserved
- Tabulated data library (`/trench-boxes` → `pages/TrenchBoxes.jsx`) still exists and serves its PDFs. The Trench Safety landing page (`/trench-safety` → `PublicTrenchSafetyDashboard`) **already includes a tile linking into the tabulated data view** (Phase 3.5 implementation).
- No admin functions exposed publicly.
- AssetTransfers behavior unchanged (no functional edit, only removal of bogus disable comments).
- Phase 5 backend tests: 10/10 PASS.

## Validation matrix (10/10)
| # | Item | Result |
|---|------|--------|
| 1 | Preview compiles without overlay | ✅ |
| 2 | AssetTransfers.jsx no longer references missing eslint rule | ✅ |
| 3 | Public Safety Tile shows "Trench Safety" | ✅ |
| 4 | Public Safety Tile no longer says only "Trench Box Tabulated Data" | ✅ |
| 5 | CTA routes to `/trench-safety` (public Trench Safety landing) | ✅ |
| 6 | Existing tabulated data library still works | ✅ (`/trench-boxes` HTTP 200) |
| 7 | No admin actions exposed publicly | ✅ (route unchanged, public-only surfaces) |
| 8 | Dispatch/Asset Transfers still loads | ✅ (compile clean, no functional change) |
| 9 | Phase 5 tests remain green | ✅ (10/10 PASS, 53.24s) |
| 10 | No deployment performed | ✅ |
