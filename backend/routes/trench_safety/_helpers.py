"""Shared helpers for trench-safety: audit, equipment_master mirror, status moves."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from ._models import OPERATIONAL_STATUSES, CONDITIONS


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def actor_label(actor: Optional[Dict[str, Any]]) -> str:
    """Render an actor dict (from require_* deps) to a short audit string."""
    if not actor:
        return "system"
    role = actor.get("_actor") or actor.get("role") or "unknown"
    name = (
        actor.get("name")
        or actor.get("email")
        or actor.get("display_name")
        or role
    )
    return f"{role}:{name}"


async def write_audit(
    db,
    *,
    kind: str,
    asset_id: str,
    actor: Optional[Dict[str, Any]] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a single audit event. Uses the existing db.audit_events
    collection so the trench-safety surface joins the global timeline.
    """
    doc = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "kind": kind,
        "asset_id": asset_id,
        "actor": actor_label(actor),
        "actor_email": (actor or {}).get("email"),
        "detail": detail or {},
    }
    await db.audit_events.insert_one(doc)


async def upsert_equipment_master_mirror(
    db,
    asset: Dict[str, Any],
) -> None:
    """Keep db.equipment_master in lockstep with the trench_safety_assets row.

    Single-direction mirror: trench_safety_assets is the source of truth.
    equipment_master is a thin shadow so the asset participates in global
    search, supervisor pickers, and existing asset_transfers movement.

    Idempotent: safe to call on every create/update.
    """
    asset_id = asset["asset_id"]
    payload = {
        "id": asset["id"],                       # primary key shared
        "asset_id": asset_id,                    # MASCI tag
        "category": "Trench Safety",
        "type": asset.get("asset_type") or "Trench Box",
        "label": _label_for(asset),
        "manufacturer": asset.get("manufacturer") or "",
        "model": asset.get("model") or "",
        "serial_number": asset.get("serial_number") or "",
        "size": asset.get("size") or "",
        "color": asset.get("color") or "",
        "condition": asset.get("condition") or "",
        "status": asset.get("operational_status") or "Available",
        "location": asset.get("current_location") or asset.get("yard_location") or "",
        "current_project_id": asset.get("current_project_id"),
        "current_project_name": asset.get("current_project_name"),
        "is_active": bool(asset.get("is_active", True)),
        "retired_at": asset.get("retired_at"),
        "linked_collection": "trench_safety_assets",
        "updated_at": now_iso(),
    }
    # If first time, set created_at
    existing = await db.equipment_master.find_one(
        {"id": asset["id"]}, {"_id": 0, "created_at": 1}
    )
    if existing and existing.get("created_at"):
        payload["created_at"] = existing["created_at"]
    else:
        payload["created_at"] = asset.get("created_at") or now_iso()

    await db.equipment_master.update_one(
        {"id": asset["id"]},
        {"$set": payload},
        upsert=True,
    )


def _label_for(asset: Dict[str, Any]) -> str:
    tag = asset.get("asset_id") or ""
    size = asset.get("size") or ""
    color = asset.get("color") or ""
    t = asset.get("asset_type") or "Trench Box"
    bits = [tag]
    if size:
        bits.append(size)
    if color:
        bits.append(color)
    bits.append(t)
    return " · ".join([b for b in bits if b])


def validate_status_transition(current: str, target: str) -> Optional[str]:
    """Return None if the transition is allowed, else an error string.

    Rules:
      - Retired is terminal (only admin can un-retire via explicit edit).
      - Cannot leave Inspection Hold or Repair into Available without
        going through inspect/repair endpoints (server enforces the gate).
      - Available ↔ Assigned ↔ In Transport are free moves.
    """
    if target not in OPERATIONAL_STATUSES:
        return f"unknown status: {target}"
    if current == target:
        return None
    if current == "Retired":
        return "asset is retired — re-activation requires admin edit"
    if current in {"Inspection Hold", "Repair"} and target == "Available":
        return (
            f"cannot move from {current} to Available directly — "
            "submit a clearing inspection or close the repair first"
        )
    return None


def public_view(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Field-safe public projection used by the QR landing endpoint.

    Excludes: cost, purchase_date, audit detail, assigned_to_*, raw
    photo refs (presigned URLs are handled at fetch time). Keeps the
    information a crew member needs to verify the box is safe to use.
    """
    keep = {
        "asset_id",
        "asset_type",
        "manufacturer",
        "model",
        "size",
        "rated_depth_ft",
        "rated_soil_type",
        "color",
        "condition",
        "operational_status",
        "current_location",
        "current_project_name",
        "last_inspection_at",
        "next_inspection_due",
        "certification_expires_at",
        "tabulated_data_missing",
        "missing_serial_number",
        "needs_review",
        "qr_url",
    }
    return {k: asset.get(k) for k in keep}


async def latest_inspection(db, asset_id: str) -> Optional[Dict[str, Any]]:
    doc = await db.trench_safety_inspections.find_one(
        {"asset_id": asset_id},
        {"_id": 0},
        sort=[("submitted_at", -1)],
    )
    return doc


async def has_open_repair(db, asset_id: str) -> bool:
    doc = await db.trench_safety_repairs.find_one(
        {"asset_id": asset_id, "status": {"$in": ["Open", "In Progress"]}},
        {"_id": 0, "id": 1},
    )
    return bool(doc)


async def has_inspection_hold(db, asset_id: str) -> bool:
    asset = await db.trench_safety_assets.find_one(
        {"asset_id": asset_id},
        {"_id": 0, "operational_status": 1},
    )
    return bool(asset and asset.get("operational_status") == "Inspection Hold")
