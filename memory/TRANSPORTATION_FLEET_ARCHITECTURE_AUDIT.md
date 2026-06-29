TRANSPORTATION FLEET ARCHITECTURE AUDIT (Track 19.02)
======================================================

DATE   : 2026-06-29
VERDICT: SINGLE P0 OPERATIONAL GAP IDENTIFIED.

THE PROBLEM
───────────
`/transportation-operations/trucks` queries `transport_trucks`, which
holds only **12** rows in the preview Atlas. The actual MASCI fleet
lives in `equipment_master` (705) and `equipment_units` (484).

The transport-side row contains a foreign key `equipment_id` that
already points back at `equipment_master` / `equipment_units`. The
schema is already designed for join-on-read; the join was never wired
into the Transportation Trucks page.

EVIDENCE
────────
Sample `transport_trucks` row keys:
    [carrier_id, created_at, created_by, equipment_id, id, notes,
     ownership, plate, safety_hold, status, tenant, truck_number,
     truck_type, updated_at, updated_by, vin]

`equipment_id` is present — but `vehicle_type`, `category`, `make`,
`model` are all None on the 12 transport_trucks rows.
`equipment_master` (705 rows) carries make, model, year, category.
`equipment_units` (484) carries per-instance VIN, status, location.

`fleet_audit` (979), `fleet_defects` (170), `fleet_status` (385),
`equipment_inspections` (870), and `motive_events` (468) all reference
the equipment-side identifier. The Transportation view is missing all
of them.

ROOT CAUSE
──────────
`transport_trucks` was designed as an overlay collection — it stores
Transportation-side operational state (status, safety_hold, notes)
keyed by `equipment_id`. The original Track 16.x build never shipped
the join projection, so the Trucks page only sees the 12 overlay rows
that someone manually created during testing.

RECOMMENDED ARCHITECTURE — "Fleet view, not fleet database"
───────────────────────────────────────────────────────────
`equipment_master` + `equipment_units` REMAIN the source of truth.
Transportation gets a READ-MOSTLY projection endpoint that joins:

    GET /api/admin/transportation/fleet/equipment
       ?category=transportation_capable
       &limit=...
       &q=...

Server-side join (pseudo-code):
    transport-capable categories from equipment_master / category
    join equipment_units on equipment_master_id
    left-join transport_trucks on equipment_units.id ↔ equipment_id
    project { id, unit_number, make, model, year, category,
              plate, vin, status_master, status_transport,
              safety_hold_transport, current_motive_event,
              last_inspection, current_carrier_id, current_driver_id }

The existing `POST /admin/transportation/persons/link-from-hr` pattern
(Track 19.00) is the template: read from one collection, write only
to a Transportation overlay row.

PROPOSED PHASING
────────────────
Phase A (this track if budget allows):
    · Add the `/fleet/equipment` projection endpoint.
    · Wire the existing Trucks page to read from it.
    · Show "12 transportation-managed · 484 in MASCI fleet" overlay
      counts in the header strip.

Phase B (Track 19.03 candidate):
    · Per-row "Adopt into Transportation" action that creates the
      transport_trucks overlay row if one doesn't exist.
    · Surface inspection + defect status from `equipment_inspections` /
      `fleet_defects` in the right rail.
    · Pull Motive live state from `motive_events` for the asset row.

Phase C:
    · Full Mission Control fleet utilisation widget driven by
      `fleet_status` (385 rows of real status data).

RISK
────
LOW. The join endpoint is read-only and dispatch-token-safe. The
existing 12 transport_trucks rows continue to work unchanged. No
schema migration. Operator can roll back with one endpoint removal.

NEXT ACTION
───────────
Implement Phase A. The carrier of the change is small (~80 LOC for
the join projection + minor frontend re-wiring).
