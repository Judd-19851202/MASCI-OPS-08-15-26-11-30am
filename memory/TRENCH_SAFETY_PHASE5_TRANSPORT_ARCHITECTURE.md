# TRENCH SAFETY · PHASE 5 — TRANSPORT ARCHITECTURE

**Phase:** 5 — Transport / Dispatch Integration
**Date:** 2026-02
**Status:** Architecture certified · built · tested.

## 1. Mandate (operator-locked)

> Use the existing `/api/asset-transfers` state machine as the transport authority. Do NOT create a duplicate trench-only transport system.

## 2. State machine

Unchanged. The canonical lifecycle in `routes/asset_transfers.py` remains:
```
Draft → Requested → Approved → In Transit → Received → Closed
                                 │
                                 └── Cancelled | Rejected
```

## 3. Integration model — Bridge pattern

`routes/trench_transport_bridge.py` is the single integration point. It is **invoked by** the existing `asset_transfers` handlers via three callsites (no transport routes added):

| Existing handler | Hook added | Bridge function |
|------------------|------------|-----------------|
| `POST /api/asset-transfers/{id}/in-transit` | inside the `if did:` block (after `_fan`) | `on_transfer_in_transit` |
| `POST /api/asset-transfers/{id}/receive`    | inside the `if did:` block (after `_fan`) | `on_transfer_received` |
| `POST /api/asset-transfers/{id}/cancel`     | inside the `if _did:` block               | `on_transfer_cancelled` |

Each bridge function:
1. Looks up the `equipment_master` row by `transfer.equipment_id`.
2. Returns immediately if `category != "Trench Safety"` (zero impact on yellow iron / fleet).
3. Loads the `trench_safety_assets` row (mirrors share the same primary `id`).
4. Mutates the asset; routes status through the **hold engine** (`apply_resolved_status`) so holds cannot be silently cleared.
5. Emits an audit event into the shared `audit_events` collection.

## 4. Field additions to `trench_safety_assets`

| Field | Set when |
|-------|----------|
| `active_transfer_id` | in-transit · cleared on receive/cancel |
| `transport_from_location` | in-transit |
| `transport_to_location` | in-transit |
| `transport_to_project_number` | in-transit |
| `transport_started_at` | in-transit |
| `transport_received_at` | receive |
| `transport_moved_by` | in-transit |

`operational_status` and `current_*` continue to be authoritative — holds always win.

## 5. Yard vs project destination resolution

Asset Transfers requires a non-empty `to_project_number`. The bridge treats these as **yard destinations**:
- `to_project_number` ∈ `{"YARD", "YARD-RETURN", "MASCI-YARD", "RETURN"}`, OR
- `to_location_label` contains `"yard"` or `"shop"` (case-insensitive).

Project destinations: any other non-empty `to_project_number`.

## 6. Audit event kinds

| Event | Emitted by |
|-------|------------|
| `trench_safety_transport_started`  | `on_transfer_in_transit` |
| `trench_safety_transport_completed` | `on_transfer_received` |
| `trench_safety_transport_cancelled` | `on_transfer_cancelled` |
| `trench_safety_transport_blocked_retired` | bridge guard on Retired |

## 7. Hold preservation — proof points

- The bridge never writes `operational_status` directly if the asset has any active hold.
- After every mutation it calls `apply_resolved_status(asset_id, actor)` which re-runs the Phase 4B priority resolver. Safety / Certification / Maintenance / Inspection holds always win over `In Transport` / `Assigned` / `Available`.

## 8. UI integration

| Surface | Change |
|---------|--------|
| `asset_transfers` create payload | now snapshots `equipment_category` + `equipment_type` |
| `pages/AssetTransfers.jsx` | adds a `Trench Safety` badge next to the unit ID on every trench row (data-testid `transfer-trench-badge`) |
| `pages/trench_safety/TrenchSafetyQrLanding.jsx` | already covers `In Transport` via the Phase 4B `STATUS_STYLE` table |
| `lib/i18n.js` | Spanish entries: In Transport, From, To, Delivered, Received, Transfer Cancelled, Hold Preserved + the four coaching strings |

## 9. Non-duplication guarantees

| Rule | Compliance |
|------|------------|
| No new transport collection | ✅ |
| No new transport endpoints | ✅ |
| No new transfer state machine | ✅ |
| Single audit stream | ✅ |
| Single mirror direction | ✅ |
| Holds remain authoritative | ✅ |
