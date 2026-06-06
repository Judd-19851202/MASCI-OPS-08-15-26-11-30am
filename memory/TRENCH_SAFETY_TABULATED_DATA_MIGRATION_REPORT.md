# TRENCH SAFETY PHASE 3 — TABULATED DATA MIGRATION REPORT

**Phase:** 3 of 11
**Mode:** Re-host existing content under new IA — no file moves, no schema changes, no PDF re-uploads.

---

## 1. What "migration" means here

The directive says:

> The existing Trench Box Tabulated Data page must be preserved and moved into:
> Safety → Trench Safety → Tabulated Data

There are TWO valid interpretations:

| Interpretation | Pros | Cons |
|---|---|---|
| **A. Hard move** — delete `/trench-boxes`, redirect to `/safety/trench-safety/tabulated-data` | Single canonical URL | Breaks every printed QR poster and bookmark in the field |
| **B. Soft co-host** — keep `/trench-boxes` working AND add `/safety/trench-safety/tabulated-data` as the canonical home | Field continuity preserved; zero risk of bricked QR posters | Two routes serve the same content |

Phase 3 chose **B**. Field-printed QR posters are deployed; breaking them silently is a regression. Both routes serve the identical content (same primer + library components), so there is no drift.

---

## 2. Files and routes preserved (unchanged)

| Surface | Path | Status |
|---|---|---|
| Public field-reference page | `/trench-boxes` (`TrenchBoxes.jsx`) | UNTOUCHED |
| Safety legacy redirect | `/safety/trench-boxes` → `/trench-boxes` | UNTOUCHED |
| Admin CRUD | `/admin/trench-boxes` (`TrenchBoxesAdmin.jsx`) | UNTOUCHED |
| Admin QR Poster | `/admin/trench-boxes/poster` (`TrenchBoxPoster.jsx`) | UNTOUCHED |
| PM alias | `/pm/trench-boxes` | UNTOUCHED |
| PDF storage scope | `scope="trench_box"` (db `trench_box_files`) | UNTOUCHED |
| Manufacturer reference rows | `db.trench_boxes` (Speed Shore et al.) | UNTOUCHED |
| Tabulated Data Primer (EN+ES) | `TabulatedDataPrimer.jsx` + `lib/tabulatedDataPrimer.js` (351 lines) | UNTOUCHED |
| Library component | `TrenchBoxTabulatedLibrary.jsx` (345 lines) | UNTOUCHED |
| All existing PDFs uploaded to `trench_box_files` | Live storage | UNTOUCHED |

## 3. New route — what's actually new

```
/safety/trench-safety/tabulated-data  →  TrenchSafetyTabulatedData (wrapper)
```

`TrenchSafetyTabulatedData.jsx` is a 25-line wrapper that:

1. Wraps the existing `TabulatedDataPrimer` component verbatim.
2. Wraps the existing `TrenchBoxTabulatedLibrary` component with `adminMode={false}` (same as the legacy `/trench-boxes` page).
3. Renders both inside the Safety portal's `TrenchSafetyShell` (gives the tab strip + back link + cyan accent).

That's it. **No PDF was moved. No upload was re-keyed. No filename changed.**

## 4. PDF/library functional parity verification

| Functionality | Legacy `/trench-boxes` | New `/safety/trench-safety/tabulated-data` |
|---|---|---|
| Primer card (EN) | YES | YES (same component) |
| Primer card (ES) — toggle | YES | YES (same component) |
| Library: per-box folders | YES | YES (same component) |
| Library: "General / Educational" folder | YES | YES (same component) |
| Search filter | YES | YES (same component) |
| PDF inline open | YES | YES (same component) |
| PDF download | YES | YES (same component) |
| File counts | YES | YES (same component) |
| Admin uploader UI | NO (separate at `/admin/trench-boxes`) | NO (intentional — uploader stays admin-only) |

**Zero functional drift.**

## 5. Spanish behaviour preservation

The legacy primer uses `lib/tabulatedDataPrimer.js` (351-line EN+ES content table) — that file is UNTOUCHED. Phase 3 added ~120 new keys to `lib/i18n.js` for the NEW Trench Safety chrome (hub, list, detail, QR landing), but did not touch any existing trench-box keys. Spanish parity of the primer is therefore unchanged.

## 6. Discoverability — how users find the new home

1. **Safety Hub tile** — `safety-tile-trench-safety` now appears in the Safety landing page Operational Output group. Click → Hub.
2. **Hub quicklink** — `ql-tabdata` quicklink on the Hub routes to the new tabulated-data page.
3. **Asset Detail link** — every asset detail page exposes a "Browse Tabulated Data Library" tile.
4. **QR Landing CTA** — public QR landing has a big cyan-700 "Open Tabulated Data" button.

Old `/trench-boxes` URL still works for anyone with a stale QR or bookmark.

## 7. Verdict

✅ **MIGRATION COMPLETE — ZERO FILE LOSS, ZERO BROKEN ROUTES.**

The new path co-exists with the legacy path. Field QR posters continue to resolve. All Spanish content is preserved. Admin uploader is unchanged. No PDF was moved or re-uploaded.
