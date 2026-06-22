# TRACK 15.61 — Motive Integration Forensics (Phase 8)

**Method:** probe `/api/integrations/health` and `/api/integrations/motive/events` on production; inspect `motive_events` and asset/employee mapping counts; map intended-vs-actual linkage with Daily Reports.

## Live production integration health

```
GET /api/integrations/health
→ motive:
    id: 9d721d37-34c3-408a-ad71-83a2eca18c53
    provider: motive
    status: Connected
    enabled: true
    demo_mode: false
    test_mode: false
    api_key_present: true
    api_key_masked: •••••••
  counts:
    asset_mappings_total: 190
    asset_mappings_mapped: 190
    employee_mappings_total: 65
    employee_mappings_mapped: 65
```

✅ Motive IS connected and mapping data is current. 190 trucks + 65 employees are linked.

## What data comes FROM Motive

`GET /api/integrations/motive/events?limit=5` returns vehicle GPS / event_family=`vehicle_gps` rows. Sample event keys:

```
provider, event_signature, bearing, city, event_at, event_family, event_kind,
id, lat, lon, raw, received_at, source, speed_kph, state, vehicle_id,
event_type, event_type_label, severity, priority, driver_name, unit_number,
masci_equipment_id, speed_mph, location, coaching_required, notify, summary
```

These power the **Operations Map**, **DriverCommandProfile**, **MotiveDriverIntelPanel**, **MotiveOpsIntelPanel** — all real-time fleet operational views.

## What data goes TO Motive

**Nothing direct.** The codebase has no outbound Motive writes other than webhook acknowledgements. The integration is pull-only (Motive → MASCI).

## What Daily Report data links to Motive

**None.** Direct grep across the codebase:

- `db.daily_reports.outbound_materials[i]` has no `motive_event_id` / `motive_load_id` / `vehicle_id` / `unit_number` field.
- `db.daily_reports.equipment[i]` does have an `asset_id` but it is the MASCI internal asset ID, not the Motive truck id (the cross-walk via `db.asset_mappings` exists but is not consulted at Daily Report submit time).
- The Daily Report PDF does NOT show Motive driver-hours, mileage, or GPS coverage for the day.

## What trucking information SHOULD link but does not

| Should link | Today? | Why-not |
|---|---|---|
| `outbound_materials[i].hauler="Masci"` row → the specific Motive truck (unit_number, VIN, driver) that ran the loads | ❌ no field on the form for unit_number; no auto-resolution | The form expects free-text, not a truck picker |
| Daily-Report `equipment[i]` (truck/equipment ID) → Motive `motive_truck_id` via `db.asset_mappings` | ❌ not displayed back to the form | Mapping exists in the DB but is not surfaced |
| Daily-Report `prepared_by` (foreman) → Motive employee mapping (`employee_mappings`) | ❌ no cross-walk | `prepared_by` is free-text; 65 employee mappings exist but are not consulted |

## Integration map

```
┌─────────────────┐                  ┌─────────────────────┐
│  Motive Cloud   │ ──── webhook ──►│ /api/integrations/  │
│  (telemetry)    │                  │ motive/webhook      │
└─────────────────┘                  └──────────┬──────────┘
                                                │
                                                ▼
                                      ┌─────────────────┐
                                      │ motive_events   │
                                      │ (stored events) │
                                      └────────┬────────┘
                                               │
                       ┌───────────────────────┼─────────────────────┐
                       ▼                       ▼                     ▼
              ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
              │ Operations Map  │    │ Driver Profile  │    │ Ops Intel Panel │
              └─────────────────┘    └─────────────────┘    └─────────────────┘

                       ┌─────────────────┐
                       │ daily_reports   │      NO LINKAGE
                       │ (outbound,      │ ◄────────────────── motive_events
                       │  equipment)     │      NO LINKAGE
                       └─────────────────┘

                       ┌─────────────────┐
                       │ asset_mappings  │   ◄── 190 rows mapped
                       │ employee_       │   ◄── 65 rows mapped
                       │ mappings        │       BUT NOT CONSULTED AT
                       └─────────────────┘       DAILY REPORT SUBMIT TIME
```

## Verdict

Motive is **fully integrated for telemetry ingest** and **fully unmapped to Daily Reports**. The mappings (`asset_mappings`, `employee_mappings`) exist as durable database links, but the Daily Report form does NOT pick truck identities from a Motive-aware picker, does NOT link outbound rows to actual Motive vehicle_ids, and does NOT consume Motive load events to auto-populate `loads_today` for the PM dashboard.

The fix is NOT new Motive credentials or a new webhook. The fix is wiring the existing mappings into the Daily Report form (an asset picker that pulls from `asset_mappings`) and into the PM Command Center hauls roll-up (cross-join `motive_events` by `motive_truck_id` to active project assignments).

See `TRACK_15_61_RECOMMENDATIONS.md` item R-MOTIVE.
