# TRACK 19.62 · Parent Asset Surfacing

**Requirement:** If a fire extinguisher is linked to Unit 2648,
Excavator 37, or another parent asset, that parent's thread MUST surface
the linked extinguisher (identity + type + inspection status + due date
+ deep-link into extinguisher thread).

## Implementation
`frontend/src/pages/fleet/FleetUnitThread.jsx` (the pilot; every Asset
Thread route resolves through this shell for Fleet lens):

1. On mount, in addition to the existing `/api/assets/<unit>/timeline`
   and OI summary fetches, issue a third parallel request:
   `GET /api/safety/fire-extinguishers?assigned_target_ref=<unit>`.
2. The Safety endpoint returns 0..N extinguishers matched via
   `assigned_target_ref` OR (backward compat) `equipment_master_id`
   OR `assigned_unit_number`.
3. Each returned extinguisher is added:
   - **As a relationship edge** with `kind="fire_ext"`,
     `label="Fire Ext <unit_id>"`,
     `sublabel="<type> · next due <date> [· OVERDUE]"`,
     `deep_link=/admin/assets/<unit_id>/thread`.
   - **As an attention item** (HIGH · "Fire extinguisher <unit_id>
     overdue") when `next_due_date < today`.

## Zero-Drift accounting
- No new storage on the parent asset.
- No duplicate extinguisher fields on `equipment_master`.
- The relationship is a RENDER, not a persisted linkage on the parent.
- The Safety endpoint gains query params only; the schema is unchanged.

## Bi-directional linking (already provided)
- **Parent → Extinguisher:** shown here.
- **Extinguisher → Parent:** shown on the AdminAssetThread Fire branch
  via the `parent_asset` relationship edge.

## Consumers who will benefit immediately
- **Shop Manager** opening Unit 2648 — sees mounted extinguisher, its
  type, and its next-due date.
- **Fleet Manager** — same.
- **Dispatch** — same, for OTR trucks.
- **Superintendent** — sees extinguisher status while reviewing a
  project vehicle.
- **Executive** — via the shared shell.

## What was NOT built
- No wholesale rewrite of any Fleet page.
- No new "Fleet Fire Roster" table.
- No new backend endpoint (the safety endpoint was extended additively).
