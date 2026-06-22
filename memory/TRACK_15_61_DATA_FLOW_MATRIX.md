# TRACK 15.61 — Data Flow Matrix (Phase 10)

**Method:** for every field on the Daily Report schema, compute (a) its non-empty rate across the 60-day production corpus, (b) whether it reaches the PDF, (c) whether it reaches the PM dashboard, (d) whether it reaches an executive surface, (e) whether it links to Motive.

## Master matrix

Legend: `■` = surfaced · `□` = present but not surfaced · `–` = not applicable

| Field | DB non-empty % | PDF | PM Project Detail | PM Command Center | Executive | Motive linkage |
|---|---|---|---|---|---|---|
| `activities[]` | 26.0 % | ■ | □ | □ | □ | – |
| `outbound_materials[]` | **2.6 %** | ■ | ■ | **□** (empty hauls tab) | □ | – (no link) |
| `materials[]` (incoming) | 23.4 % | ■ | ■ | □ (no overview surface) | □ | – |
| `production[]` | **3.2 %** | ■ | □ | □ | □ | – |
| `constraints[]` | 6.5 % | ■ | □ | □ | □ | – |
| `general_notes` | 40.3 % | ■ | □ | □ | □ | – |
| `schedule_delays_notes` | **0.0 %** | (n/a — empty) | – | – | – | – |
| `weather_impact_notes` | **0.0 %** | (n/a — empty) | – | – | – | – |
| `masci_crews[]` | 96.8 % | ■ | □ | □ (no crew-roster surface) | □ | – |
| `subcontractors[]` | 31.8 % | ■ | □ | □ | □ | – |
| `visitors[]` | 24.7 % | ■ | □ | □ | □ | – |
| `equipment[]` | 43.5 % | ■ | □ | □ (overview shows 0 trucks) | □ | □ via `asset_mappings` but NOT consumed |
| `photos[]` | 97.4 % | ■ | – | – | – | – |
| `linked_excavation_ids[]` | **0.0 %** | (n/a) | – | – | – | – |
| `weather_summary` | 52.6 % | ■ | – | – | – | – |
| `weather_snapshots` | 51.9 % | ■ | – | – | – | – |
| `safety_incidents_today` | 100.0 % | ■ | – | □ | □ | – |
| `incident_notes` | 10.4 % | ■ | – | □ | □ | – |
| `prepared_by_signature` | 97.4 % | ■ | – | – | – | – |
| `superintendent_signature` | **39.0 %** | ■ | – | – | – | – |
| `gps_lat` / `gps_lng` | 51.9 % | ■ | – | – | – | – |

## Dead fields (0 % non-empty in production)

- `schedule_delays_notes` — operators never use this. The yes/no `schedule_delays` flag is also rarely used.
- `weather_impact_notes` — same.
- `linked_excavation_ids` — excavation linkage is never set.

These should be either removed from the form, hidden behind progressive disclosure, or replaced with a single more general "What slowed you down today?" prompt.

## Hidden / orphaned fields

- `production[]` — operators don't use it (3.2 %), no dashboard surfaces it.
- `constraints[]` — same (6.5 %, no surface).
- `equipment[]` — 43.5 % populated but the PM Command Center overview shows `equipment_assigned=0`. There IS data, the dashboard just doesn't read it.

## Lost fields

- **`outbound_materials[]` is the canonical "lost" field.** 4 reports captured 50 loads of dirt. The DB has it. The PDF prints it. The PM Project Detail surface shows it. But the PM Command Center hauls tab returns `rows: []` and the overview's `loads_today` counter is 0. The roll-up never happens.

## Fields that work end-to-end

- Photos: form → DB → PDF, all three healthy.
- Crews: 96.8 % populated, rendered on PDF, but not surfaced on PM dashboards as a daily-roll-up.
- Safety incidents: 100 % populated (the form gates on this), surfaced in safety dashboards.

## Recommendation rank derived from this matrix

| Rank | Where to focus | Reason |
|---|---|---|
| 1 | Activity Log + `general_notes` consolidation | Half of all reports have no narrative anywhere. |
| 2 | PM Command Center hauls / loads aggregation | Data exists but the dashboard says 0. |
| 3 | Remove the three dead-field surfaces | They confuse the operator without producing data. |
| 4 | Wire `equipment[]` into PM dashboard | 43 % populated, 0 surfaced. |
| 5 | Motive ↔ Daily Report cross-walk | Mappings exist; use them in the picker and in the hauls roll-up. |

See `TRACK_15_61_RECOMMENDATIONS.md` for prioritised list with effort and impact scoring.
