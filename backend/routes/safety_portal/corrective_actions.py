"""
Safety Portal · corrective_actions.py — Phase 2 corrective-action CRUD.

Status pipeline: Open → In Progress → Pending Review → Closed.
Closing a CA auto-stamps completed_at + closed_by_name.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ._models import CorrectiveActionCreate, CorrectiveActionUpdate


def register_corrective_action_routes(
    api_router: APIRouter, db, require_safety_token,
) -> None:
    @api_router.get("/safety/corrective-actions")
    async def list_corrective_actions(
        status: Optional[str] = None, _: dict = Depends(require_safety_token),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        return await db.corrective_actions.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)

    @api_router.post("/safety/corrective-actions")
    async def create_corrective_action(
        body: CorrectiveActionCreate, user: dict = Depends(require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "title": body.title.strip(),
            "description": (body.description or "").strip(),
            "source_kind": body.source_kind.strip(),
            "source_id": body.source_id,
            "project_number": (body.project_number or "").strip(),
            "assigned_to_name": (body.assigned_to_name or "").strip(),
            "assigned_to_email": (body.assigned_to_email or "").strip().lower(),
            "priority": body.priority or "Medium",
            "due_date": body.due_date,
            "status": "Open",
            "notes": (body.notes or "").strip(),
            "completion_notes": "",
            "completed_at": None,
            "closed_by_name": "",
            "created_by_name": user.get("name") or "",
            "created_by_email": user.get("email") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.corrective_actions.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.get("/safety/corrective-actions/{ca_id}")
    async def get_corrective_action(ca_id: str, _: dict = Depends(require_safety_token)):
        doc = await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Not found")
        return doc

    @api_router.patch("/safety/corrective-actions/{ca_id}")
    async def update_corrective_action(
        ca_id: str, body: CorrectiveActionUpdate, user: dict = Depends(require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        update = {"updated_at": now}
        for k, v in body.dict(exclude_none=True).items():
            update[k] = v
        if update.get("status") == "Closed":
            update["completed_at"] = now
            update["closed_by_name"] = user.get("name") or ""
        res = await db.corrective_actions.update_one({"id": ca_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})

    @api_router.delete("/safety/corrective-actions/{ca_id}")
    async def delete_corrective_action(ca_id: str, _: dict = Depends(require_safety_token)):
        res = await db.corrective_actions.delete_one({"id": ca_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_corrective_action_routes"]
