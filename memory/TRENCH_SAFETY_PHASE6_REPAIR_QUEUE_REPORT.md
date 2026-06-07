# PHASE 6 — REPAIR QUEUE REPORT

## Endpoint
`GET /api/trench-safety/shop/repairs` · auth = shop_or_admin.

## Default behavior
Returns every repair NOT in `Closed After Verification`, joined with minimal asset metadata, sorted by severity (Critical → Major → Minor → None) then `opened_at`. Counts dict gives per-status totals for the header chips.

## Filters
| Param | Values |
|-------|--------|
| `status` | any of the 6 REPAIR_STATUSES |
| `severity` | None / Minor / Major / Critical |
| `requires_reinspection` | true / false |
| `include_closed` | when true, lifts the default Closed-After-Verification exclusion |
| `limit` | 1–1000 (default 200) |

## Row shape (UI-ready, no second roundtrip required)
```jsonc
{
  "id": "<repair uuid>",
  "asset_id": "TB-04",
  "status": "Open",
  "kind": "repair_recommendation",
  "severity_at_creation": "Major",
  "issue_description": "...",
  "requires_reinspection": true,
  "source": "inspection:<id>" | "damage_report:<id>" | "shop:manual",
  "repair_vendor": "...",
  "repair_cost": 0.0,
  "photo_refs": [],
  "notes_history": [{at, by, text}, ...],
  "opened_at": "...",
  "opened_by": "...",
  "closed_at": null,
  "closed_by": null,
  "verified_at": null,
  "verified_by": null,
  // joined asset metadata
  "asset_type": "Trench Box",
  "size": "8x16",
  "serial_number": "6890902",
  "operational_status": "Maintenance Hold",
  "current_project_name": "...",
  "current_project_number": "...",
  "current_location": "..."
}
```

## Shop UI
`pages/shop/ShopTrenchSafetyRepairs.jsx`:
- Filter chips for `Open / In Progress / Waiting on Parts / Vendor Repair / Completed` plus an "All Active" pill.
- Each row shows: severity dot · asset ID + type + size · status badge · hold badge (when on hold) · reinspection-required badge · issue description · severity / source / opened_at / opened_by / vendor / project metadata.
- Each row is a `<Link>` to `/safety/trench-safety/assets/{asset_id}` for full repair detail + transitions.
- Coaching footer: "Completing a repair does not release a hold. Safety must verify before the asset returns to service."
- Header back-button to `/shop`.

## Data-testids (for QA automation)
`shop-trench-repairs-header` · `repair-queue-total` · `filter-all` · `filter-open` · `filter-in-progress` · `filter-waiting-on-parts` · `filter-vendor-repair` · `filter-completed` · `repair-queue-loading` · `repair-queue-error` · `repair-queue-empty` · `repair-queue-list` · `repair-row-{id}` · `repair-asset-id` · `severity-dot-{Critical|Major|Minor|None}` · `repair-queue-coaching`.

## Tests proving the queue behavior
- `test_shop_queue_lists_repairs_with_asset_metadata` ✅
- `test_queue_filter_by_status_and_severity` ✅
- `test_critical_inspection_creates_safety_hold` (proves auto-stub from Phase 4B feeds the queue) ✅

## Compliance
✅ Calm doctrine respected (Shop hub remains 1st-screen; trench queue is "More"-footer reachable).
✅ Read-only outside of the explicit Shop / Safety actions.
✅ No KPIs, no charts.
