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
        status: Optional[str] = None,
        equipment_master_id: Optional[str] = None,  # iter139 filter
        employee_master_id: Optional[str] = None,   # iter139 filter
        _: dict = Depends(require_safety_token),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        if equipment_master_id:
            q["equipment_master_id"] = equipment_master_id
        if employee_master_id:
            q["employee_master_id"] = employee_master_id
        return await db.corrective_actions.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)

    @api_router.post("/safety/corrective-actions")
    async def create_corrective_action(
        body: CorrectiveActionCreate, user: dict = Depends(require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        related = [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in (body.related_entities or [])]
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
            "related_entities": related,
            # iter138 — SOT bindings (optional)
            "equipment_master_id": (body.equipment_master_id or "").strip(),
            "employee_master_id": (body.employee_master_id or "").strip(),
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
        update: dict = {"updated_at": now}
        for k, v in body.model_dump(exclude_none=True).items():
            if k == "related_entities" and v is not None:
                # Normalize: each item may be Pydantic or dict
                update[k] = [dict(x) for x in v]
            else:
                update[k] = v
        if update.get("status") == "Closed":
            update["completed_at"] = now
            update["closed_by_name"] = user.get("name") or ""
        res = await db.corrective_actions.update_one({"id": ca_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})

    # ── Related-entity link management ─────────────────────────────
    # Used by the UI's link-picker. POST appends, DELETE removes by composite
    # (kind, id) so the front-end doesn't need to track per-link UUIDs.
    @api_router.post("/safety/corrective-actions/{ca_id}/links")
    async def add_ca_link(
        ca_id: str, body: dict, _: dict = Depends(require_safety_token),
    ):
        kind = (body.get("kind") or "").strip()
        link_id = str(body.get("id") or "").strip()
        if not kind or not link_id:
            raise HTTPException(400, "kind and id are required")
        label = (body.get("label") or "").strip()[:240]
        url = (body.get("url") or "").strip()[:400]
        entry = {"kind": kind, "id": link_id, "label": label, "url": url}
        # Pull existing (composite-key) then push fresh — keeps it idempotent
        await db.corrective_actions.update_one(
            {"id": ca_id},
            {"$pull": {"related_entities": {"kind": kind, "id": link_id}}},
        )
        res = await db.corrective_actions.update_one(
            {"id": ca_id},
            {
                "$push": {"related_entities": entry},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            },
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Corrective action not found")
        return entry

    @api_router.delete("/safety/corrective-actions/{ca_id}/links")
    async def remove_ca_link(
        ca_id: str, kind: str, id: str,  # noqa: A002 (`id` is a query param)
        _: dict = Depends(require_safety_token),
    ):
        res = await db.corrective_actions.update_one(
            {"id": ca_id},
            {
                "$pull": {"related_entities": {"kind": kind, "id": id}},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            },
        )
        if res.matched_count == 0:
            raise HTTPException(404, "Corrective action not found")
        return {"ok": True}

    @api_router.get("/safety/corrective-actions/{ca_id}/related-resolved")
    async def resolve_ca_links(ca_id: str, _: dict = Depends(require_safety_token)):
        """Resolve each related entity against its source collection so
        the UI can display fresh labels even if the underlying record
        was renamed. Missing records get `exists=false` so the UI can
        show a 'this link is broken' marker."""
        ca = await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0, "related_entities": 1})
        if not ca:
            raise HTTPException(404, "Corrective action not found")
        out: list = []
        for r in (ca.get("related_entities") or []):
            kind = r.get("kind")
            rid = r.get("id")
            resolved = {**r, "exists": False, "summary": ""}
            coll_map = {
                "incident": ("incidents", "incident_type"),
                "equipment_inspection": ("equipment_inspections", "equipment_unit"),
                "equipment_master": ("equipment_master", "unit_number"),
                "training_record": ("safety_training_records", "training_name"),
                "audit": ("inspections", "project_name"),
                "safety_document": ("safety_documents", "title"),
                "fire_ext": ("fire_extinguishers", "unit_id"),
            }
            target = coll_map.get(kind)
            if target:
                coll_name, summary_field = target
                doc = await db[coll_name].find_one({"id": rid}, {"_id": 0, summary_field: 1})
                if doc:
                    resolved["exists"] = True
                    resolved["summary"] = str(doc.get(summary_field) or "")
            out.append(resolved)
        return {"ca_id": ca_id, "related": out}

    @api_router.delete("/safety/corrective-actions/{ca_id}")
    async def delete_corrective_action(ca_id: str, _: dict = Depends(require_safety_token)):
        res = await db.corrective_actions.delete_one({"id": ca_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_corrective_action_routes"]
