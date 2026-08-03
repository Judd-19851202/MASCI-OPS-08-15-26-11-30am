# WP18C1 API and Model Evidence

Date: 2026-08-03

## Additive model result

WP-18C1 implemented an additive hierarchy foundation with references and bindings instead of replacing authoritative records.

## Canonical hierarchy registry fields implemented

Each governed hierarchy object supports, as applicable:

- stable internal ID
- code
- name
- description
- type
- subtype
- parent ID
- ancestry path / ancestor IDs
- company scope
- effective start / end
- active status
- archive status
- owner / steward
- source provenance
- external source identifier
- created / updated metadata
- audit metadata
- version
- metadata extension

## New / extended API capabilities

- `GET /api/admin/governance/hierarchy/overview`
- `POST /api/admin/governance/hierarchy/backfill/run`
- `GET /api/admin/governance/hierarchy/backfill/latest`
- `GET /api/admin/governance/hierarchy/nodes`
- `GET /api/admin/governance/hierarchy/nodes/{node_id}`
- `GET /api/admin/governance/hierarchy/nodes/{node_id}/children`
- `GET /api/admin/governance/hierarchy/nodes/{node_id}/ancestry`
- `POST /api/admin/governance/hierarchy/nodes`
- `PATCH /api/admin/governance/hierarchy/nodes/{node_id}`
- `POST /api/admin/governance/hierarchy/nodes/{node_id}/activate`
- `POST /api/admin/governance/hierarchy/nodes/{node_id}/deactivate`
- `POST /api/admin/governance/hierarchy/nodes/{node_id}/archive`
- `GET /api/admin/governance/hierarchy/bindings`
- `POST /api/admin/governance/hierarchy/bindings`
- `GET /api/admin/governance/hierarchy/review-queue`
- `GET /api/admin/governance/hierarchy/resource-assignments`
- `GET /api/admin/governance/hierarchy/scope`
- `GET /api/admin/governance/organization` now reflects the governed hierarchy foundation

## Validation rules implemented

- valid parent-type enforcement
- facility subtype enforcement (`plant`, `yard`, `shop`)
- immutable code / type after creation
- no silent destructive deletion path
- archive / deactivate instead of destructive remove
- circular-parent prevention
- duplicate-code handling
- idempotent backfill and binding behavior

## Existing authoritative systems preserved

- `jobs_master`
- `project_team_assignments`
- `cost_code_registry`
- Asset Spine / `equipment_master`
- current employee identity / projections
- `operational_locations`
- current Daily Reports and existing operator workflows

## Result

The WP-18C1 API and model foundation is complete, additive, backward-compatible, and ready for WP-18C2 to build on without replacing protected systems.