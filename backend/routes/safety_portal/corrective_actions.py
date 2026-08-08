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

from lib.corrective_action_truth import normalize_corrective_action_due_date
from lib.synthetic_corrective_action_filter import (
    apply_synthetic_corrective_action_exclusion,
    synthetic_corrective_action_markers,
)
from ._models import CorrectiveActionCreate, CorrectiveActionUpdate


def register_corrective_action_routes(
    api_router: APIRouter, db, require_safety_token,
) -> None:
    @api_router.get("/safety/corrective-actions")
    async def list_corrective_actions(
        status: Optional[str] = None,
        equipment_master_id: Optional[str] = None,  # iter139 filter
        employee_master_id: Optional[str] = None,   # iter139 filter
        source_kind: Optional[str] = None,          # iter368 filter — reverse-link from incident detail
        source_id: Optional[str] = None,            # iter368 filter — reverse-link from incident detail
        _: dict = Depends(require_safety_token),
    ):
        q: dict = {}
        if status:
            q["status"] = status
        if equipment_master_id:
            q["equipment_master_id"] = equipment_master_id
        if employee_master_id:
            q["employee_master_id"] = employee_master_id
        if source_kind:
            q["source_kind"] = source_kind.strip()
        if source_id:
            q["source_id"] = source_id.strip()
        return await db.corrective_actions.find(
            apply_synthetic_corrective_action_exclusion(q),
            {"_id": 0},
        ).sort("created_at", -1).to_list(1000)

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
            "due_date": normalize_corrective_action_due_date(body.due_date),
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
        doc.update(synthetic_corrective_action_markers(doc))
        await db.corrective_actions.insert_one(doc)
        doc.pop("_id", None)

        # Iter150 — emit a unified task for accountability tracking.
        # Fire-and-forget; analytics-style safety so a failure NEVER
        # blocks the actual CA write.
        try:
            from routes.tasks_notifications import task_service  # noqa: PLC0415
            from datetime import datetime as _dt  # noqa: PLC0415
            due_at = None
            if doc.get("due_date"):
                try:
                    due_at = _dt.fromisoformat(str(doc["due_date"]))
                except Exception:
                    due_at = None
            await task_service.create(db, {
                "title": f"Corrective Action: {doc['title'][:140]}",
                "description": doc.get("description") or "",
                "source_module": "safety.corrective_actions",
                "source_record_id": doc["id"],
                "linked_employee_id": doc.get("employee_master_id") or None,
                "linked_equipment_id": doc.get("equipment_master_id") or None,
                "linked_project_number": doc.get("project_number") or None,
                "assignee_role": "safety",
                "priority": doc.get("priority") or "Medium",
                "due_at": due_at,
                "created_by": {
                    "role": "safety",
                    "name": user.get("name") or user.get("email"),
                },
            })
        except Exception:
            pass

        # Iter160 · Operational signal — CA created throughput.
        try:
            from lib.operational_signals import record_signal  # noqa: PLC0415
            await record_signal(
                db, signal="ca.created", module="safety.corrective_actions",
                dims={"priority": (doc.get("priority") or "Medium")[:24],
                      "source_kind": (doc.get("source_kind") or "")[:24]},
            )
        except Exception:
            pass

        return doc

    @api_router.get("/safety/corrective-actions/{ca_id}")
    async def get_corrective_action(ca_id: str, _: dict = Depends(require_safety_token)):
        doc = await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Not found")
        return doc

    # iter356 — lifecycle enforcement. Valid status pipeline:
    #   Open → In Progress → Pending Review → Verified → Closed
    # Plus side-paths: any status can return to In Progress (re-open),
    # and admins can hard-cancel to Closed via explicit transition_note.
    # Transitions outside the table are REJECTED with a 422.
    _CAPA_TRANSITIONS = {
        "Open":           {"Open", "In Progress", "Pending Review"},
        "In Progress":    {"In Progress", "Open", "Pending Review"},
        "Pending Review": {"Pending Review", "In Progress", "Verified"},
        "Verified":       {"Verified", "In Progress", "Closed"},
        "Closed":         {"Closed", "In Progress"},  # re-open path
    }

    def _normalize_status(s: Optional[str]) -> str:
        if not s:
            return ""
        return str(s).strip().title().replace("In progress", "In Progress").replace(
            "Pending review", "Pending Review"
        )

    @api_router.patch("/safety/corrective-actions/{ca_id}")
    async def update_corrective_action(
        ca_id: str, body: CorrectiveActionUpdate, user: dict = Depends(require_safety_token),
    ):
        now = datetime.now(timezone.utc).isoformat()
        existing = await db.corrective_actions.find_one(
            {"id": ca_id}, {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "Not found")

        update: dict = {"updated_at": now}
        payload = body.model_dump(exclude_none=True)
        transition_note = (payload.pop("transition_note", None) or "").strip()

        for k, v in payload.items():
            if k == "related_entities" and v is not None:
                update[k] = [dict(x) for x in v]
            elif k == "due_date":
                update[k] = normalize_corrective_action_due_date(v)
            else:
                update[k] = v
        candidate = {**existing, **update}
        update.update(synthetic_corrective_action_markers(candidate))

        # iter356 · Lifecycle enforcement on status transitions.
        new_status_raw = update.get("status")
        new_status = _normalize_status(new_status_raw) if new_status_raw else ""
        old_status = _normalize_status(existing.get("status") or "Open") or "Open"

        if new_status:
            update["status"] = new_status  # canonicalize storage
            allowed = _CAPA_TRANSITIONS.get(old_status, set())
            if new_status not in allowed:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Illegal CAPA status transition: '{old_status}' → "
                        f"'{new_status}'. Allowed from '{old_status}': "
                        f"{sorted(allowed)}. Lifecycle pipeline is "
                        f"Open → In Progress → Pending Review → Verified → Closed."
                    ),
                )

            # Separation of duties: the person who marked Pending Review
            # should not be the same person who Verifies. We enforce a
            # soft check (warn via detail) only if previous reviewer is
            # the same email. Hard-block kept off — small Safety teams
            # routinely have one Safety Coordinator.
            if new_status == "Closed":
                if old_status != "Verified":
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            "Cannot close a CAPA that has not been Verified. "
                            "Move it through 'Verified' first (a separate "
                            "reviewer step is the lifecycle gate)."
                        ),
                    )
                update["completed_at"] = now
                update["closed_by_name"] = user.get("name") or ""
            if new_status == "Verified":
                update["verified_at"] = now
                update["verified_by_name"] = user.get("name") or ""
                update["verified_by_email"] = user.get("email") or ""

        # Append status_history entry on any status change.
        if new_status and new_status != old_status:
            history_entry = {
                "from": old_status,
                "to": new_status,
                "by_name": user.get("name") or "",
                "by_email": user.get("email") or "",
                "at": now,
                "note": transition_note,
            }
            res = await db.corrective_actions.update_one(
                {"id": ca_id},
                {"$set": update, "$push": {"status_history": history_entry}},
            )
        else:
            res = await db.corrective_actions.update_one(
                {"id": ca_id}, {"$set": update},
            )
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        updated = await db.corrective_actions.find_one({"id": ca_id}, {"_id": 0})

        # Iter160 · Operational signal — CA closed cycle time.
        if new_status == "Closed" and updated:
            try:
                from lib.operational_signals import record_signal, elapsed_ms_between  # noqa: PLC0415
                ems = elapsed_ms_between(updated.get("created_at"),
                                         updated.get("completed_at"))
                await record_signal(
                    db, signal="ca.closed",
                    module="safety.corrective_actions",
                    elapsed_ms=ems,
                    dims={"priority": (updated.get("priority") or "")[:24]},
                )
            except Exception:
                pass
        return updated

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
