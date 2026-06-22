# TRACK 15.61 — PM Dashboard Trace (Phase 6)

**Method:** for every Daily-Report metric that should reach the PM dashboard, probe the live production API surface and compare the answer to the underlying DB data.

## Surfaces audited

| Surface | URL | Endpoint(s) probed | Live result (2026-06-22) |
|---|---|---|---|
| PM Command Center · Overview | `/pm/command-center` | `GET /api/pm/command-center/overview` | 200 — see counts below |
| PM Command Center · Hauls tab | same | `GET /api/pm/command-center/hauls` | 200, `rows: []` |
| PM Command Center · Materials tab | same | `GET /api/pm/command-center/materials` | 200, `rows: [8 entries]` |
| PM Project Detail · Material Movement | `/pm/projects/{n}` | `GET /api/material-movement/daily/{n}/{date}` | 200, surfaces dr_id-linked rows |

## Command Center overview counts (live)

```
materials_in_today  : 0
materials_out_today : 0
active_hauls        : 0
loads_today         : 0
trucks_assigned     : 0
drivers_assigned    : 0
equipment_assigned  : 0
defects_open        : 0
incidents_open      : 0
capas_open          : 0
```

**Every counter except "scoped_projects" is zero.** Yet the 60-day corpus contains:
- 4 reports with 50 loads of outbound material
- 36 reports with incoming material (~140+ delivery rows)
- 154 reports submitted with crews + photos
- ~96 reports with equipment rows

The Command Center is reporting "0 of everything today" because it scopes to "today" only AND the data path it consults does not include `db.daily_reports.outbound_materials` / `materials` rows. Even rolling the window across all 60 days, the hauls tab returns `rows: []`.

## What IS surfacing on PM

| Daily Report metric | PM Project Detail | PM Command Center |
|---|---|---|
| Labor (`masci_crews`, `subcontractors`, `visitors`) | not the canonical scope of material-movement; surfaces elsewhere if at all | ❌ overview shows `drivers_assigned=0` |
| Equipment (`equipment[]`) | not in material-movement; needs separate surface | ❌ overview shows `equipment_assigned=0` |
| Materials IN (`materials[]`) | ✅ shown in `incoming[]` of `/api/material-movement/daily/{n}/{date}` | partial — `materials` tab returns 8 rows window-wide |
| Trucking (outbound) (`outbound_materials[]`) | ✅ shown in `outgoing[]` | ❌ — overview counter is 0; hauls tab is empty |
| Hauls (linked to Motive) | ❌ no linkage exists | ❌ |
| Quantities (`production[]`) | ❌ no surfacing observed | ❌ |
| Production (per activity row `% done`) | ❌ buried inside activities row; not extracted | ❌ |

## What IS being collected but NOT surfaced

These fields exist in the database with non-zero data, but no PM dashboard renders them:

| Field | DB non-empty % | Surfaced on PM dashboard? |
|---|---|---|
| `production[]` | 3.2 % | ❌ |
| `equipment[]` | 43.5 % | ❌ (the count counter shows 0) |
| `subcontractors[]` | 31.8 % | ❌ (overview shows 0 contractors) |
| `visitors[]` | 24.7 % | ❌ |
| `general_notes` | 40.3 % | ❌ (no Notes feed on any PM dashboard) |
| `constraints[]` | 6.5 % | ❌ (no "Open constraints" panel) |
| `weather_impact_notes` | 0 % | n/a |

## Conclusion

The PM **Project Detail** page (the page operators land on when they tap a specific job) does correctly surface incoming + outgoing material rows from Daily Reports — that route is healthy.

The PM **Command Center** overview + hauls + materials tabs are largely empty because:
1. The counters look at "today" only — they are reset every midnight.
2. The hauls tab queries a different collection (`haul_cycles` / `dispatch_assignments`) that does not currently include Daily-Report outbound rows.
3. The materials tab reads 8 rows — likely from `dispatch_assignments`, not from the 36 reports with incoming material.
4. There is no aggregation layer that rolls Daily Reports forward into PM Command Center counts beyond the immediate calendar day.

This is a real, fix-able **integration / aggregation gap**, NOT a PDF or DB bug. See `TRACK_15_61_DATA_FLOW_MATRIX.md` for the per-field map and `TRACK_15_61_RECOMMENDATIONS.md` items R-PMCC and R-AGG.
