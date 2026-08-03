# WP18C1 Operator Experience Evidence

Date: 2026-08-03

## UI result

WP-18C1 added only the minimum governed admin experience required to manage and verify the hierarchy foundation.

## New governed surface

Route:

- `/admin/governance/organization`

Surface includes:

- summary cards
- current structure list
- detail panel
- review queue panel
- resource assignment panel
- scope preview panel
- add / edit / activate / deactivate / archive flows

## Preserved experience rules

- existing MASCI navy / frosted admin shell preserved
- existing portal structure preserved
- existing WP-17 design primitives reused
- operator-safe language used instead of internal engineering terminology

## EN / ES evidence

Testing agent verified Spanish labels including:

- `Estructura organizativa`
- `Actualizar`
- `Buscar`

## Responsive certification evidence

Testing agent verified no major horizontal overflow at:

- `390`
- `430`
- `768`
- `1024`
- `1440`

## Verified data-testids

- `hierarchy-foundation-page`
- `hierarchy-refresh-button`
- `hierarchy-backfill-button`
- `hierarchy-add-button`
- `hierarchy-search-input`
- `hierarchy-type-filter`
- `hierarchy-nodes-table`
- `hierarchy-node-row-*`
- `hierarchy-detail-panel`
- `hierarchy-review-queue-panel`
- `hierarchy-assignment-panel`
- `hierarchy-scope-panel`
- `hierarchy-item-dialog`
- `hierarchy-form-cancel-button`

## Result

WP-18C1 met the operator/admin experience requirement without introducing a new shell, a new visual language, or route-level duplication.