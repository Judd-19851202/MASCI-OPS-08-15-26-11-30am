"""
Safety Portal · fire_extinguishers.py — Phase 3 FE register.

One record per physical unit. `/inspect` POST is the monthly-inspection
hook: it stamps last_inspection_date / last_status / next_due_date on
the unit AND pushes an entry into its embedded `inspections[]` history.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ._models import (
    FireExtinguisherCreate,
    FireExtinguisherInspection,
    FireExtinguisherUpdate,
)


def register_fire_extinguisher_routes(
    api_router: APIRouter, db, require_safety_token,
) -> None:
    @api_router.get("/safety/fire-extinguishers")
    async def list_fire_extinguishers(
        status: Optional[str] = None,
        overdue_only: bool = False,
        _: dict = Depends(require_safety_token),
    ):
        q: dict = {}
        if status:
            q["last_status"] = status
        if overdue_only:
            today = datetime.now(timezone.utc).isoformat()[:10]
            q["next_due_date"] = {"$ne": None, "$lt": today}
        return await db.fire_extinguishers.find(q, {"_id": 0}).sort("unit_id", 1).to_list(2000)

    @api_router.post("/safety/fire-extinguishers")
    async def create_fire_extinguisher(
        body: FireExtinguisherCreate, user: dict = Depends(require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "unit_id": body.unit_id.strip(),
            "location_kind": body.location_kind.strip(),
            "location_value": (body.location_value or "").strip(),
            "type": (body.type or "ABC").strip(),
            "size": (body.size or "").strip(),
            "last_inspection_date": body.last_inspection_date,
            "next_due_date": body.next_due_date,
            "last_status": body.last_status or "Pass",
            "last_inspector_name": "",
            "notes": (body.notes or "").strip(),
            # iter138 — link to equipment_master if specified (truck mount)
            "equipment_master_id": (body.equipment_master_id or "").strip(),
            "inspections": [],
            "created_by_name": user.get("name") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.fire_extinguishers.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch("/safety/fire-extinguishers/{fe_id}")
    async def update_fire_extinguisher(
        fe_id: str, body: FireExtinguisherUpdate, _: dict = Depends(require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.fire_extinguishers.update_one({"id": fe_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})

    @api_router.post("/safety/fire-extinguishers/{fe_id}/inspect")
    async def inspect_fire_extinguisher(
        fe_id: str, body: FireExtinguisherInspection,
        user: dict = Depends(require_safety_token),
    ):
        existing = await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        next_due = body.next_due_date
        if not next_due:
            try:
                base = datetime.fromisoformat(body.inspection_date)
            except ValueError:
                base = datetime.now(timezone.utc)
            next_due = (base + timedelta(days=30)).isoformat()[:10]
        entry = {
            "inspection_date": body.inspection_date,
            "status": body.status,
            "inspector_name": (body.inspector_name or user.get("name") or "").strip(),
            "notes": (body.notes or "").strip(),
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.fire_extinguishers.update_one(
            {"id": fe_id},
            {
                "$set": {
                    "last_inspection_date": body.inspection_date,
                    "next_due_date": next_due,
                    "last_status": body.status,
                    "last_inspector_name": entry["inspector_name"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                "$push": {"inspections": entry},
            },
        )

        # Phase E · Cross-system fan-out — failed/needs-service
        # inspections trigger a safety corrective task + notification.
        # Pass status is silent. Fire-and-forget.
        try:
            status_lc = (body.status or "").lower()
            is_fail = status_lc in ("fail", "needs service", "needs_service",
                                    "tag missing", "missing", "damaged")
            if is_fail:
                from lib.event_fanout import emit_task_and_notification  # noqa: PLC0415
                title = (f"Fire extinguisher {existing.get('unit_id') or fe_id} "
                         f"flagged {body.status}")
                await emit_task_and_notification(
                    db,
                    task={
                        "title": title[:200],
                        "description": (f"Location: "
                                        f"{existing.get('location_label') or existing.get('location_kind') or '—'} · "
                                        f"Inspector: {entry['inspector_name'] or '—'} · "
                                        f"Notes: {entry.get('notes') or '—'}")[:4000],
                        "source_module": "safety.fire_extinguishers",
                        "source_record_id": fe_id,
                        "assignee_role": "safety",
                        "priority": "High",
                        "created_by": {"role": "system", "via": "fire-ext-inspection"},
                    },
                    notification={
                        "type": "fire_ext.deficiency",
                        "title": title[:200],
                        "message": (f"{existing.get('unit_id') or fe_id} · "
                                    f"{body.status}")[:200],
                        "severity": "Warning",
                        "recipient_role": "safety",
                        "linked_source_module": "safety.fire_extinguishers",
                        "linked_source_record_id": fe_id,
                    },
                )
            # Iter160 · Operational signal — record pass AND fail outcomes.
            try:
                from lib.operational_signals import record_signal  # noqa: PLC0415
                sig = "fire_ext.fail" if is_fail else "fire_ext.pass"
                await record_signal(
                    db, signal=sig, module="safety.fire_extinguishers",
                    dims={"status": (body.status or "")[:24]},
                )
            except Exception:
                pass
        except Exception as e:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("[fire-ext-fanout] failed: %s", e)

        return await db.fire_extinguishers.find_one({"id": fe_id}, {"_id": 0})

    @api_router.delete("/safety/fire-extinguishers/{fe_id}")
    async def delete_fire_extinguisher(fe_id: str, _: dict = Depends(require_safety_token)):
        res = await db.fire_extinguishers.delete_one({"id": fe_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_fire_extinguisher_routes"]
