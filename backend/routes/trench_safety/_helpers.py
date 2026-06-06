"""Shared helpers for trench-safety: audit, equipment_master mirror, status moves."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from ._models import (
    OPERATIONAL_STATUSES,
    CONDITIONS,
    HOLD_PRIORITY,
    HOLD_KINDS,
)


# ────────────────────────────────────────────────────────────────────────
# Phase 4B — Hold engine helpers
# ────────────────────────────────────────────────────────────────────────

async def list_open_holds(db, asset_id: str) -> list:
    return await db.trench_safety_holds.find(
        {"asset_id": asset_id, "is_active": True},
        {"_id": 0},
    ).to_list(50)


def resolve_operational_status(asset: dict, open_holds: list) -> str:
    """Single source of truth for the asset's operational state.

    Inputs:
      - asset.operational_status: current persisted value (the resolver
        respects Assigned / In Transport / Retired as the non-hold base).
      - open_holds: list of {kind, ...} rows from trench_safety_holds where
        is_active=True.

    Returns the highest-priority status. Retired is terminal — if asset is
    Retired, the resolver returns Retired regardless of holds (a retired
    asset is removed from service entirely).
    """
    base = asset.get("operational_status") or "Available"
    if base == "Retired":
        return "Retired"

    hold_kinds = [h.get("kind") for h in (open_holds or [])]
    hold_kinds = [k for k in hold_kinds if k in HOLD_KINDS]
    if hold_kinds:
        return max(hold_kinds, key=lambda k: HOLD_PRIORITY.get(k, 0))

    # No active holds — preserve Assigned / In Transport / Available
    if base in ("Assigned", "In Transport", "Available"):
        return base
    # Any legacy non-Operational base without an open hold normalises back
    # to Available (this is what fires after the last hold is cleared on
    # an asset that was previously parked in a hold state).
    return "Available"


async def apply_resolved_status(db, asset_id: str, actor_email: str = "system") -> dict:
    """Recompute and persist operational_status for an asset based on its
    open holds. Mirrors to equipment_master. Returns the fresh asset doc.
    """
    asset = await db.trench_safety_assets.find_one(
        {"asset_id": asset_id}, {"_id": 0}
    )
    if not asset:
        return None
    open_holds = await list_open_holds(db, asset_id)
    new_status = resolve_operational_status(asset, open_holds)
    if new_status != asset.get("operational_status"):
        await db.trench_safety_assets.update_one(
            {"id": asset["id"]},
            {"$set": {
                "operational_status": new_status,
                "updated_at": now_iso(),
                "updated_by": actor_email,
            }},
        )
        asset = await db.trench_safety_assets.find_one(
            {"id": asset["id"]}, {"_id": 0}
        )
    await upsert_equipment_master_mirror(db, asset)
    return asset


async def open_hold(
    db,
    *,
    asset_id: str,
    kind: str,
    reason: str,
    source: str,
    source_ref: Optional[str] = None,
    opened_by: str = "system",
) -> dict:
    """Idempotent open. If an active hold of (asset_id, kind) already
    exists, return it without duplicating. Recomputes operational_status.
    """
    if kind not in HOLD_KINDS:
        raise ValueError(f"unknown hold kind: {kind}")
    existing = await db.trench_safety_holds.find_one(
        {"asset_id": asset_id, "kind": kind, "is_active": True},
        {"_id": 0},
    )
    if existing:
        # Update reason / source if changed (latest-write-wins)
        await db.trench_safety_holds.update_one(
            {"id": existing["id"]},
            {"$set": {
                "reason": reason or existing.get("reason"),
                "source": source or existing.get("source"),
                "source_ref": source_ref or existing.get("source_ref"),
            }},
        )
        await apply_resolved_status(db, asset_id, opened_by)
        return await db.trench_safety_holds.find_one({"id": existing["id"]}, {"_id": 0})

    doc = {
        "id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "kind": kind,
        "reason": reason,
        "source": source,
        "source_ref": source_ref,
        "opened_at": now_iso(),
        "opened_by": opened_by,
        "cleared_at": None,
        "cleared_by": None,
        "clear_reason": None,
        "clear_source": None,
        "is_active": True,
    }
    await db.trench_safety_holds.insert_one(doc)
    doc.pop("_id", None)
    await apply_resolved_status(db, asset_id, opened_by)
    await write_audit(
        db, kind="trench_asset_hold_opened", asset_id=asset_id,
        actor={"_actor": "system", "email": opened_by},
        detail={"hold_id": doc["id"], "hold_kind": kind, "source": source},
    )
    return doc


async def clear_hold(
    db,
    *,
    asset_id: str,
    kind: str,
    clear_reason: str,
    clear_source: str = "manual",
    cleared_by: str = "system",
) -> Optional[dict]:
    """Close any active hold of (asset_id, kind). Recomputes status."""
    existing = await db.trench_safety_holds.find_one(
        {"asset_id": asset_id, "kind": kind, "is_active": True},
        {"_id": 0},
    )
    if not existing:
        return None
    await db.trench_safety_holds.update_one(
        {"id": existing["id"]},
        {"$set": {
            "is_active": False,
            "cleared_at": now_iso(),
            "cleared_by": cleared_by,
            "clear_reason": clear_reason,
            "clear_source": clear_source,
        }},
    )
    await apply_resolved_status(db, asset_id, cleared_by)
    await write_audit(
        db, kind="trench_asset_hold_cleared", asset_id=asset_id,
        actor={"_actor": "system", "email": cleared_by},
        detail={"hold_id": existing["id"], "hold_kind": kind, "clear_source": clear_source},
    )
    return await db.trench_safety_holds.find_one({"id": existing["id"]}, {"_id": 0})


# ────────────────────────────────────────────────────────────────────────
# Phase 4B — Certification status helpers
# ────────────────────────────────────────────────────────────────────────

def certification_status_for(
    requires_cert: bool,
    active_certs: list,
    now_dt: Optional[datetime] = None,
) -> str:
    """Returns one of: Not Required | Missing | Expired | Due Soon | OK.

    active_certs: rows from trench_safety_certifications with status in
    {Active}. Caller is responsible for filtering out Revoked/Superseded.
    """
    if not requires_cert:
        return "Not Required"
    if not active_certs:
        return "Missing"
    now_dt = now_dt or datetime.now(timezone.utc)
    expirations = []
    for c in active_certs:
        exp = c.get("expires_at")
        if not exp:
            continue
        try:
            # Accept either YYYY-MM-DD or ISO datetime
            if len(exp) == 10:
                dt = datetime.strptime(exp, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            continue
        expirations.append(dt)
    if not expirations:
        return "Missing"
    soonest = min(expirations)
    if soonest < now_dt:
        return "Expired"
    days_left = (soonest - now_dt).days
    if days_left <= 90:
        return "Due Soon"
    return "OK"


async def recompute_certification_hold(db, asset_id: str, actor_email: str = "system") -> None:
    """Open or clear the Certification Hold for an asset based on the
    current state of its certifications + the requires_certification flag.

    Auto-marks any expired Active cert rows as status=Expired so the
    derived status calculation is correct.
    """
    asset = await db.trench_safety_assets.find_one(
        {"asset_id": asset_id}, {"_id": 0}
    )
    if not asset:
        return
    if not asset.get("requires_certification"):
        await clear_hold(
            db, asset_id=asset_id, kind="Certification Hold",
            clear_reason="requires_certification flag cleared",
            clear_source="manual", cleared_by=actor_email,
        )
        return

    # First — sweep Active certs and flip past-due to Expired so the
    # derived status calculation reflects reality.
    now_dt = datetime.now(timezone.utc)
    active = await db.trench_safety_certifications.find(
        {"asset_id": asset_id, "status": "Active"}, {"_id": 0}
    ).to_list(200)
    for c in active:
        exp = c.get("expires_at") or ""
        try:
            if len(exp) == 10:
                dt = datetime.strptime(exp, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            continue
        if dt < now_dt:
            await db.trench_safety_certifications.update_one(
                {"id": c["id"]}, {"$set": {"status": "Expired", "updated_at": now_iso()}}
            )

    # Re-read after the sweep
    active_certs = await db.trench_safety_certifications.find(
        {"asset_id": asset_id, "status": "Active"}, {"_id": 0}
    ).to_list(200)
    status = certification_status_for(True, active_certs, now_dt)
    if status in ("Missing", "Expired"):
        await open_hold(
            db, asset_id=asset_id, kind="Certification Hold",
            reason=f"Certification status: {status}",
            source="certification", source_ref=None, opened_by=actor_email,
        )
    else:
        await clear_hold(
            db, asset_id=asset_id, kind="Certification Hold",
            clear_reason=f"Certification status now: {status}",
            clear_source="cert_added", cleared_by=actor_email,
        )


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
    # Phase 4B — enrich the mirror with hold + certification snapshots so
    # Dispatch / Project / Search consumers see the same state.
    try:
        open_holds = await db.trench_safety_holds.find(
            {"asset_id": asset_id, "is_active": True},
            {"_id": 0, "kind": 1, "opened_at": 1, "source": 1},
        ).to_list(20)
    except Exception:  # noqa: BLE001 — collection may not exist on first boot
        open_holds = []
    try:
        active_certs = await db.trench_safety_certifications.find(
            {"asset_id": asset_id, "status": "Active"},
            {"_id": 0, "expires_at": 1},
        ).to_list(50)
    except Exception:  # noqa: BLE001
        active_certs = []
    cert_status = certification_status_for(
        bool(asset.get("requires_certification")), active_certs
    )
    mfr = asset.get("manufacturer") or ""
    mdl = asset.get("model") or ""
    make_model = " ".join([s for s in [mfr, mdl] if s]).strip() or asset.get("asset_type") or "Trench Safety"
    year = asset.get("year_manufactured")
    display_label = _label_for(asset)
    payload = {
        "id": asset["id"],                       # primary key shared
        "asset_id": asset_id,                    # MASCI tag
        "category": "Trench Safety",
        "type": asset.get("asset_type") or "Trench Box",
        "label": display_label,
        # Phase 4A — populate the canonical equipment_master columns so the
        # existing Fleet table (Unit # · Year · Make · Model · Pre-Op Type)
        # renders trench safety assets identically to fleet vehicles.
        "unit_number": asset_id,
        "year": str(year) if year else "",
        "make": mfr,
        "model": mdl,
        "make_model": make_model,
        "display_label": display_label,
        "vin_serial_number": asset.get("serial_number") or "",
        "preop_equipment_type": "Other",
        "company": asset.get("owner") or "MASCI",
        "comments": asset.get("notes") or "",
        # Trench-specific extras kept for safety/dispatch consumers
        "manufacturer": mfr,
        "serial_number": asset.get("serial_number") or "",
        "size": asset.get("size") or "",
        "color": asset.get("color") or "",
        "condition": asset.get("condition") or "",
        "status": asset.get("operational_status") or "Available",
        "operational_status": asset.get("operational_status") or "Available",
        "location": asset.get("current_location") or asset.get("yard_location") or "",
        "current_location": asset.get("current_location") or asset.get("yard_location") or "",
        "current_project_id": asset.get("current_project_id"),
        "current_project_name": asset.get("current_project_name"),
        "current_project_number": asset.get("current_project_number"),
        "last_inspection_at": asset.get("last_inspection_at"),
        "next_inspection_due": asset.get("next_inspection_due"),
        # Phase 4B fields
        "requires_certification": bool(asset.get("requires_certification")),
        "certification_status": cert_status,
        "active_holds": open_holds,
        "last_inspection_result": asset.get("last_inspection_result"),
        "last_inspection_severity": asset.get("last_inspection_severity"),
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

    Phase 4B — extended for new hold kinds.
    Rules:
      - Retired is terminal (only admin can un-retire via explicit edit).
      - Cannot leave Inspection / Maintenance / Safety / Certification Hold
        directly to Available — must clear the hold through the proper path.
      - Available ↔ Assigned ↔ In Transport are free moves.
    """
    HOLD_STATUSES = {
        "Inspection Hold", "Maintenance Hold",
        "Safety Hold", "Certification Hold",
    }
    if target not in OPERATIONAL_STATUSES:
        return f"unknown status: {target}"
    if current == target:
        return None
    if current == "Retired":
        return "asset is retired — re-activation requires admin edit"
    if current in HOLD_STATUSES and target == "Available":
        return (
            f"cannot move from {current} to Available directly — "
            "clear the hold through the proper workflow"
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
