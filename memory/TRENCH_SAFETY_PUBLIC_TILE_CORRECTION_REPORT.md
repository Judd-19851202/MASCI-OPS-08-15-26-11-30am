# PUBLIC TILE CORRECTION REPORT

**Component:** `frontend/src/pages/SafetySection.jsx` (public Safety entry surface, not admin)
**Tile testId:** `safety-tile-trench`

## Before → After

| Field | Before | After |
|-------|--------|-------|
| `to` | `/trench-boxes` | `/trench-safety` |
| `title` | "Trench Box Tabulated Data" | "Trench Safety" |
| `desc` | "Learn what tabulated data is, why it keeps you alive, and pull the exact manufacturer data sheet for every shield in the MASCI fleet — bilingual." | "Field-facing entry point for the MASCI Trench Safety system — asset lookup, QR scan landing, tabulated data, safety reference, and damage / unsafe / missing-pin / missing-label reporting. Bilingual." |
| `ctaLabel` | "OPEN LIBRARY" | "OPEN TRENCH SAFETY" |
| `accent` | slate | slate (unchanged) |
| `icon` | Box | Box (unchanged) |

## Routing target

`/trench-safety` → `pages/trench_safety/PublicTrenchSafetyDashboard.jsx` (registered in `App.js` line 359, public — no auth).

The public landing page offers:
- Anonymous fleet overview counts (no asset IDs leaked).
- Asset lookup by ID.
- QR scan deep-link routing → `/trench-safety/assets/:assetId` (public field-safe projection).
- Tabulated data tab (reuses existing `/trench-boxes` PDFs — they remain available).
- Damage / unsafe / missing-pin / missing-label reporting via the public damage-report endpoint.

## Architecture compliance

| Surface | Role | Touched? |
|---------|------|----------|
| Public Safety Tile | Field reference + reporting | ✅ Corrected |
| Safety Portal (`/safety/trench-safety/*`) | Admin / management | Not touched |
| Operations Integration (`/api/trench-safety/by-project`, asset_transfers) | Assignment / movement | Not touched |

No admin actions added to the public tile. No portal/operations behavior modified.

## Spanish parity

Two new strings added to `lib/i18n.js`:
- `"OPEN TRENCH SAFETY"` → `"ABRIR SEGURIDAD DE ZANJA"`
- New `desc` string translated faithfully.

## Verification (Playwright)

```
data-testid="safety-tile-trench"
  href:  /trench-safety
  text:  Trench Safety
         Field-facing entry point for the MASCI Trench Safety system —
         asset lookup, QR scan landing, tabulated data, safety reference,
         and damage / unsafe / missing-pin / missing-label reporting. Bilingual.
         OPEN TRENCH SAFETY →
```

Screenshot saved at `/tmp/safety_tile_check.png` shows the full Safety page with the corrected tile in the grid position 5 (between Job Hazard Plans and Field Safety Cards).

## Preserved
- Tabulated data library page (`/trench-boxes`) still renders and serves PDFs.
- Existing admin path (`/admin/trench-boxes`) untouched.
- Existing Safety Portal trench routes (`/safety/trench-safety/*`) untouched.
