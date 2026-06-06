"""Phase 5 — Trench-aware sync into the existing asset-transfer state machine.

This module is the SINGLE integration point between the canonical
`routes/asset_transfers.py` lifecycle and the `trench_safety_assets`
source-of-truth. It is invoked by asset_transfers.py on:

  - in-transit  → mark asset In Transport (hold-preserving)
  - receive     → update location + project + status (hold-preserving)
  - cancel      → restore (hold-preserving)

NO new transport endpoints. NO new collections. The trench mirror
into equipment_master remains the single ledger; trench_safety_assets
remains the authority on operational_status. All writes route through
the existing hold engine (resolve_operational_status) so safety,
certification, maintenance, and inspection holds are never silently
cleared by movement.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .trench_safety._helpers import (
    apply_resolved_status,
    list_open_holds,
    now_iso,
    upsert_equipment_master_mirror,
    write_audit,
)


def _is_trench_asset(eq_master_row: Optional[Dict[str, Any]]) -> bool:
    return bool(eq_master_row and eq_master_row.get("category") == "Trench Safety")


async def _load_trench_asset_by_master_id(db, equipment_id: str) -> Optional[Dict[str, Any]]:
    """The Phase 4A mirror reuses the same `id` between equipment_master
    and trench_safety_assets — look up by `id` first, fall back to
    `asset_id` if needed.
    """
    a = await db.trench_safety_assets.find_one({"id": equipment_id}, {"_id": 0})
    if a:
        return a
    return await db.trench_safety_assets.find_one(
        {"asset_id": equipment_id}, {"_id": 0}
    )


async def on_transfer_in_transit(
    db,
    *,
    transfer: Dict[str, Any],
    actor_label: str,
) -> None:
    """Called when an asset_transfer enters 'In Transit'."""
    eq = await db.equipment_master.find_one(
        {"id": transfer.get("equipment_id")}, {"_id": 0}
    )
    if not _is_trench_asset(eq):
        return
    asset = await _load_trench_asset_by_master_id(db, transfer["equipment_id"])
    if not asset:
        return

    # Retired is terminal — never allow movement to flip the status.
    if asset.get("operational_status") == "Retired":
        await write_audit(
            db, kind="trench_safety_transport_blocked_retired",
            asset_id=asset["asset_id"],
            actor={"_actor": "dispatch", "email": actor_label},
            detail={
                "transfer_id": transfer["id"],
                "from": transfer.get("from_location_label"),
                "to": transfer.get("to_location_label"),
            },
        )
        return

    open_holds = await list_open_holds(db, asset["asset_id"])
    has_hold = bool(open_holds)

    # Mark In Transport ONLY if the resolver would otherwise return
    # Assigned / Available — i.e., the asset has NO blocking hold.
    # The hold resolver preserves the highest-priority hold; "In Transport"
    # has lower priority (20) than every hold. We persist the move
    # bookkeeping fields regardless, but never silently lift a hold.
    update = {
        "current_location": "In Transit",
        "active_transfer_id": transfer["id"],
        "transport_from_location": transfer.get("from_location_label"),
        "transport_to_location": transfer.get("to_location_label"),
        "transport_to_project_number": transfer.get("to_project_number"),
        "transport_started_at": now_iso(),
        "transport_moved_by": actor_label,
        "updated_at": now_iso(),
        "updated_by": actor_label,
    }
    if not has_hold:
        update["operational_status"] = "In Transport"

    await db.trench_safety_assets.update_one(
        {"id": asset["id"]}, {"$set": update}
    )
    # Recompute via hold engine (idempotent — preserves the hold).
    await apply_resolved_status(db, asset["asset_id"], actor_label)

    await write_audit(
        db, kind="trench_safety_transport_started",
        asset_id=asset["asset_id"],
        actor={"_actor": "dispatch", "email": actor_label},
        detail={
            "transfer_id": transfer["id"],
            "from": transfer.get("from_location_label"),
            "to": transfer.get("to_location_label"),
            "hold_preserved": has_hold,
            "to_project_number": transfer.get("to_project_number"),
        },
    )


async def on_transfer_received(
    db,
    *,
    transfer: Dict[str, Any],
    actor_label: str,
) -> None:
    """Called when an asset_transfer is Received at destination."""
    eq = await db.equipment_master.find_one(
        {"id": transfer.get("equipment_id")}, {"_id": 0}
    )
    if not _is_trench_asset(eq):
        return
    asset = await _load_trench_asset_by_master_id(db, transfer["equipment_id"])
    if not asset:
        return
    if asset.get("operational_status") == "Retired":
        return  # Retired never returns to service via transport.

    open_holds = await list_open_holds(db, asset["asset_id"])
    has_hold = bool(open_holds)

    to_project_number = transfer.get("to_project_number")
    to_project_name = transfer.get("to_project_name") or transfer.get("to_location_label")
    to_loc_label = transfer.get("to_location_label") or to_project_name or to_project_number or "MASCI Yard"
    # Yard destinations: detect by sentinel project_number or by location label.
    YARD_SENTINELS = {"YARD", "YARD-RETURN", "MASCI-YARD", "RETURN"}
    label_lower = (to_loc_label or "").strip().lower()
    is_yard_destination = (
        (to_project_number or "").upper() in YARD_SENTINELS
        or "yard" in label_lower
        or "shop" in label_lower
    )
    is_project_destination = bool(to_project_number) and not is_yard_destination

    update: Dict[str, Any] = {
        "current_location": to_loc_label,
        "active_transfer_id": None,
        "transport_from_location": None,
        "transport_to_location": None,
        "transport_to_project_number": None,
        "transport_received_at": now_iso(),
        "updated_at": now_iso(),
        "updated_by": actor_label,
    }
    if is_project_destination:
        update["current_project_id"] = to_project_number
        update["current_project_name"] = to_project_name
        update["current_project_number"] = to_project_number
        if not has_hold:
            update["operational_status"] = "Assigned"
    else:
        # Yard destination → clear project + (if no hold) mark Available
        update["current_project_id"] = None
        update["current_project_name"] = None
        update["current_project_number"] = None
        update["current_superintendent"] = None
        update["current_foreman"] = None
        if not has_hold:
            update["operational_status"] = "Available"

    await db.trench_safety_assets.update_one(
        {"id": asset["id"]}, {"$set": update}
    )
    # Open a closing deployment record if destination is a project — keeps
    # the Phase 4A deployments timeline in sync without duplicating data.
    if is_project_destination:
        import uuid as _uuid
        # Close any open deployment first
        await db.trench_safety_deployments.update_many(
            {"asset_id": asset["asset_id"], "returned_at": None},
            {"$set": {
                "returned_at": now_iso(),
                "returned_by": actor_label,
                "auto_returned": True,
            }},
        )
        dep = {
            "id": str(_uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "project_id": to_project_number,
            "project_name": to_project_name,
            "project_number": to_project_number,
            "superintendent": None,
            "foreman": None,
            "assigned_by": actor_label,
            "assigned_at": now_iso(),
            "returned_by": None,
            "returned_at": None,
            "condition_at_assign": asset.get("condition"),
            "condition_at_return": None,
            "source": "Dispatch / Transport Log",
            "notes": f"Auto-assigned on asset transfer receive ({transfer['id']})",
        }
        await db.trench_safety_deployments.insert_one(dep)
    else:
        # Yard → close any open deployment
        await db.trench_safety_deployments.update_many(
            {"asset_id": asset["asset_id"], "returned_at": None},
            {"$set": {
                "returned_at": now_iso(),
                "returned_by": actor_label,
                "auto_returned": True,
            }},
        )

    await apply_resolved_status(db, asset["asset_id"], actor_label)

    await write_audit(
        db, kind="trench_safety_transport_completed",
        asset_id=asset["asset_id"],
        actor={"_actor": "dispatch", "email": actor_label},
        detail={
            "transfer_id": transfer["id"],
            "to": to_loc_label,
            "to_project_number": to_project_number,
            "hold_preserved": has_hold,
        },
    )


async def on_transfer_cancelled(
    db,
    *,
    transfer: Dict[str, Any],
    actor_label: str,
) -> None:
    """Called when a transfer is cancelled / rejected.

    Restores the asset's current_location to the from-location and lets
    the hold engine recompute the operational_status (so In Transport
    is naturally lifted if there are no holds, holds are preserved).
    """
    eq = await db.equipment_master.find_one(
        {"id": transfer.get("equipment_id")}, {"_id": 0}
    )
    if not _is_trench_asset(eq):
        return
    asset = await _load_trench_asset_by_master_id(db, transfer["equipment_id"])
    if not asset:
        return

    update = {
        "current_location": asset.get("transport_from_location") or asset.get("current_location") or "MASCI Yard",
        "active_transfer_id": None,
        "transport_from_location": None,
        "transport_to_location": None,
        "transport_to_project_number": None,
        "updated_at": now_iso(),
        "updated_by": actor_label,
    }
    # If asset was parked at In Transport status without a hold, return it
    if asset.get("operational_status") == "In Transport":
        update["operational_status"] = "Available"

    await db.trench_safety_assets.update_one(
        {"id": asset["id"]}, {"$set": update}
    )
    await apply_resolved_status(db, asset["asset_id"], actor_label)

    await write_audit(
        db, kind="trench_safety_transport_cancelled",
        asset_id=asset["asset_id"],
        actor={"_actor": "dispatch", "email": actor_label},
        detail={"transfer_id": transfer["id"]},
    )
