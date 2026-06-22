# TRACK 15.61 — Haul Data Forensics (Phase 5)

**Sample:** all 154 production Daily Reports in the 60-day window.

## Headline numbers

| Metric | Value |
|---|---|
| Reports in window | 154 |
| Reports with **any** outbound material row | **4** (2.6 %) |
| Reports with zero outbound material rows | **150** (97.4 %) |
| Total outbound rows across all reports | **4** |
| Reports with **any** incoming material row | 36 (23.4 %) |
| `production[]` non-empty | 5 (3.2 %) |

## Material types seen (outbound)

| Material | Outbound rows |
|---|---|
| Dirt | 4 |

**That is the entire outbound material vocabulary in 60 days of production:** the word "Dirt", four times. Aggregate quantity across the four rows: **50 loads**.

## Haulers seen (outbound)

| Hauler | Outbound rows |
|---|---|
| Masci | 2 |
| MASCI | 2 |

Same identity, two casings — same problem as the `prepared_by` field (Phase 1). Zero third-party haulers recorded.

## Units seen (outbound)

| Unit | Outbound rows |
|---|---|
| Loads | 4 |

No "tons", "cubic yards", "trips", "tickets" appearing as units. Operators ARE using a consistent vocabulary, but the unit is always "Loads".

## Trace · field → DB → API → dashboard → executive → reporting

### Where the haul data IS captured

- The Daily Report form has an "outbound_materials" / "Trucking & Materials" section (`/daily/new`).
- Schema captures: `material`, `quantity`, `unit`, `hauler`, `destination`, `ticket_or_manifest`, `notes`.
- Persisted to `db.daily_reports.outbound_materials` (verified by direct API read).

### Where it appears

| Destination | Result | Evidence |
|---|---|---|
| **DB** | ✅ persists | `GET /api/daily-reports/{id}` returns the array verbatim |
| **API** | ✅ identical to DB | same |
| **PDF render** | ✅ rendered as "Loads / Material / Hauler / Destination" table | extracted text from `DR-2026-00348.pdf` contains "Loads Dirt" |
| **PM Project Detail** (`/pm/projects/{number}`) | ✅ surfaced | `GET /api/material-movement/daily/26-07/2026-06-19` returns the 11-load row under `outgoing[]` with `dr_id` back-reference |
| **PM Command Center / Hauls tab** | **❌ EMPTY** | `GET /api/pm/command-center/hauls` returns `rows: []` even though the production data has 4 outbound rows |
| **PM Command Center overview counts** | **❌ ZERO** | `counts.materials_out_today=0`, `loads_today=0`, `active_hauls=0` |
| **Executive dashboard** | n/a — no dedicated executive endpoint exists; readers must use Admin Command Center / Ops Center | not surfacing in any roll-up |
| **Motive integration** | ❌ no linkage | the haul row has no `motive_event_id` / `motive_load_id` / vehicle reference; no Motive event in `motive_events` cross-references the daily report; see `TRACK_15_61_MOTIVE_FORENSICS.md` |

### Field-by-field traceability matrix

| Field on form | Captured | Stored | Aggregated to PM project | Aggregated to PM command center | Aggregated to exec | Linked to Motive |
|---|---|---|---|---|---|---|
| `outbound_materials[i].material` | ✅ | ✅ | ✅ via `material-movement.outgoing` | ❌ | ❌ | ❌ |
| `outbound_materials[i].quantity` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `outbound_materials[i].unit` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `outbound_materials[i].hauler` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `outbound_materials[i].destination` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `outbound_materials[i].ticket_or_manifest` | ✅ | ✅ (always blank in observed corpus) | n/a | n/a | n/a | ❌ |

## Conclusion

The MASCI haul dataset has TWO independent problems:

1. **Capture is essentially zero.** 2.6 % of reports recorded outbound material. 50 total loads in 60 days. Either crews are not hauling (false — see the dispatch + Motive event volume of 50 events / 5 returned which IS active), OR they are hauling and not recording it in the Daily Report.
2. **Even when captured, the data does not roll up to the PM Command Center top-line counters.** The hauls tab returns an empty rows array. The `loads_today` counter reads 0. This is an aggregation-logic gap between Daily Reports and the Command Center, NOT a data-loss gap on the project-detail page (which DOES surface the row).

Recommendation rank: **R-HAUL** (high impact) in `TRACK_15_61_RECOMMENDATIONS.md`.
