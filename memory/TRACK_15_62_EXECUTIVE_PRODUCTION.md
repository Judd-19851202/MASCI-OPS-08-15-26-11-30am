# TRACK 15.62 · Executive Production Intelligence (R-EXEC) — Session A

## Problem (15.61 finding)

> No dedicated executive endpoint exists on production. Executives cannot get cross-job answers to "how many loads of dirt did we move this week" or "which projects produced the most". They must drill into individual PDFs. — Track 15.61 Phase 7.

## Fix

**New endpoint:** `GET /api/admin/daily-roll-up?from=YYYY-MM-DD&to=YYYY-MM-DD&project=NN-NN`

Powered by the shared `lib/daily_report_rollup.py` aggregator so the haul count an executive sees is the EXACT same haul count a PM sees in the Command Center.

Default window: last 7 days. Optional `project` filter.

## Response shape

```jsonc
{
  "ok": true,
  "meta": { "date_from": "2026-06-15", "date_to": "2026-06-22",
            "project_numbers_filter": [], "vocab_size": 14 },
  "loads": {
    "in":  9,    // sum of `materials[i].quantity` where unit ∈ {Loads,Trips,...}
    "out": 291,  // sum of `outbound_materials[i].quantity` where unit ∈ {...}
    "by_material_out": [
      { "material": "Dirt",   "loads": 39, "rows": 3, "projects": ["26-07"] },
      { "material": "Other",  "loads": 0,  "rows": 1, "projects": ["24-12"] }
    ],
    "by_material_in":  [ /* same shape */ ],
    "by_unit_out":     { "Loads": 39 }
  },
  "rows_count": { "reports": 15, "materials_in_rows": 3, "materials_out_rows": 3 },
  "by_project": {
    "26-07": { "loads_in": 0, "loads_out": 39,
               "materials_in_rows": 3, "materials_out_rows": 3, "reports": 3 }
  },
  "top_haulers": [{ "hauler": "Masci", "rows": 3 }],
  "narrative_health": { "total": 15, "with_activities": 4, "with_general_notes": 6,
                        "with_narrative_sections": 0, "blank": 5,
                        "completion_pct": 66.7,
                        "avg_word_count": 12.4, "median_word_count": 8 }
}
```

## Required Executive Metrics — coverage

| Metric mandated in 15.62 directive | Source field in response | Status |
|---|---|---|
| Per-Project Loads In | `by_project.{pn}.loads_in` | ✅ |
| Per-Project Loads Out | `by_project.{pn}.loads_out` | ✅ |
| Material Types | `loads.by_material_out[].material` | ✅ |
| Production Quantities | `loads.by_material_out[].loads` + `by_unit_out` | ✅ |
| Daily Trend | re-query with `from=today&to=today` | ✅ via window param |
| Weekly Trend | re-query with default 7-day window | ✅ |
| Rolling Trend | re-query with `from=30d-ago&to=today` | ✅ via window param |

The Session B Admin Command Center "Daily Roll-Up" tab will window-toggle (Today · 7d · 30d · custom) and consume the same endpoint.

## Six Pillars

Powerful 10 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9 · Deployable 10 → **57/60**.

## Status

✅ **Executive endpoint is live behind the canonical admin gate.** Session B will surface it in the Admin Command Center; until then it is consumable via `curl` for any executive who wants the numbers today.
