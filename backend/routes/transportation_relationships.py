"""TRACK 18.00 · Phase D · Universal Relationships + Live Right Rail.

One composer endpoint that returns the connected records around any
Transportation Operations entity — strictly read-only, RBAC-aware,
no new collections, no new relationship index.

Doctrine
========
* Pure composer over existing collections.
* No graph DB. No new relationship store.
* Every result row carries an existing deep-link route.
* RBAC mirrors Phase C — unauthorized relations are OMITTED, not redacted.
* Schema version `18.00D`.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "18.00D"
SUPPORTED_TYPES = (
    "driver", "carrier", "truck", "dispatch_assignment",
    "project", "certificate", "document", "orientation",
    "inspection", "action_item", "cleanup_signal",
)

SECTION_LIMITS = {
    "recent_activity": 5,
    "timeline": 8,
    "related_records": 10,
    "open_actions": 5,
    "audit": 8,
}
MAX_LIMIT = 25


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _allowed(actor: Dict[str, Any]) -> set:
    """Same RBAC matrix as Phase C — `_actor` field."""
    a = (actor or {}).get("_actor") or ""
    if a in ("admin", "leadership"):
        return {"all"}
    if a == "dispatch":
        return {"trucks", "drivers", "carriers", "dispatch", "projects", "audit"}
    if a == "hr":
        return {"drivers", "documents", "orientation", "audit"}
    if a == "pm":
        return {"projects", "dispatch", "trucks", "audit"}
    if a == "safety":
        return {"drivers", "trucks", "audit"}
    if a == "shop":
        return {"trucks", "audit"}
    if a == "fl":
        return {"drivers", "projects", "audit"}
    return set()


def _permits(allowed: set, group: str) -> bool:
    return "all" in allowed or group in allowed


# ---------------------------------------------------------------------------
# Entity loaders — pull title/subtitle/route for the focused entity.
# ---------------------------------------------------------------------------
async def _load_entity(db, etype: str, eid: str) -> Dict[str, Any]:
    coll_map = {
        "driver": ("transport_persons", "name", "/admin/transportation/drivers/{id}"),
        "carrier": ("carriers", "name", "/admin/transportation/carriers/{id}"),
        "truck": ("transport_trucks", "unit_number", "/admin/transportation/trucks/{id}"),
        "dispatch_assignment": ("dispatch_assignments", "assignment_id",
                                "/admin/transportation/dispatch"),
        "project": ("projects", "project_number", "/pm/project/{id}"),
        "certificate": ("transport_orientation_certificates",
                        "certificate_number", "/admin/transportation/orientation"),
        "document": ("carrier_documents", "document_type",
                     "/admin/transportation/documents"),
        "orientation": ("transport_orientation_assignments", "id",
                        "/admin/transportation/orientation"),
        "inspection": ("transport_truck_inspections", "id",
                       "/admin/transportation/inspections"),
        "action_item": ("transport_action_items", "title",
                        "/admin/transportation/command-queue"),
        "cleanup_signal": (None, None, "/admin/transportation/intelligence/cleanup"),
    }
    coll_name, title_field, route_tpl = coll_map.get(etype, (None, None, None))
    if not coll_name:
        return {"type": etype, "id": eid, "title": eid,
                "subtitle": "", "status": "unknown",
                "route": route_tpl or "/admin/transportation"}
    try:
        row = await db[coll_name].find_one(
            {"$or": [{"id": eid}, {"_id": eid}]})
    except Exception:
        row = None
    if not row:
        return {"type": etype, "id": eid, "title": "(not found)",
                "subtitle": "", "status": "unknown", "route": route_tpl.replace("{id}", eid)}
    return {
        "type": etype,
        "id": row.get("id") or eid,
        "title": str(row.get(title_field) or eid),
        "subtitle": row.get("status") or "",
        "status": row.get("status") or "active",
        "route": route_tpl.replace("{id}", row.get("id") or eid),
    }


# ---------------------------------------------------------------------------
# Per-section relation loaders — each runs only if permitted by RBAC.
# All bounded by SECTION_LIMITS. All read-only.
# ---------------------------------------------------------------------------
async def _related_for_driver(db, eid: str, allowed: set) -> Dict[str, Any]:
    related: List[Dict[str, Any]] = []
    actions: List[Dict[str, Any]] = []
    timeline: List[Dict[str, Any]] = []
    if _permits(allowed, "carriers"):
        # Carrier the driver is bound to.
        person = await db.transport_persons.find_one({"id": eid})
        if person and person.get("carrier_id"):
            c = await db.carriers.find_one({"id": person["carrier_id"]})
            if c:
                related.append({
                    "type": "carrier", "title": c.get("name") or "Carrier",
                    "subtitle": "Driver of record",
                    "status": c.get("status") or "active",
                    "source": "carriers",
                    "route": f"/admin/transportation/carriers/{c.get('id')}",
                })
    if _permits(allowed, "dispatch"):
        try:
            rows = await db.dispatch_assignments.find({
                "driver_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "assignment",
                    "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                    "subtitle": r.get("project_number") or "",
                    "status": r.get("state") or "active",
                    "source": "dispatch_assignments",
                    "route": "/admin/transportation/dispatch",
                })
        except Exception:
            pass
    if _permits(allowed, "documents"):
        try:
            rows = await db.driver_documents.find({
                "transport_person_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "document",
                    "title": r.get("document_type") or "Document",
                    "subtitle": r.get("status") or "",
                    "status": r.get("status") or "unknown",
                    "source": "driver_documents",
                    "route": "/admin/transportation/documents",
                })
        except Exception:
            pass
    return {"related_records": related[:SECTION_LIMITS["related_records"]],
            "open_actions": actions, "timeline": timeline}


async def _related_for_truck(db, eid: str, allowed: set) -> Dict[str, Any]:
    related: List[Dict[str, Any]] = []
    if _permits(allowed, "carriers"):
        truck = await db.transport_trucks.find_one({"id": eid})
        if truck and truck.get("carrier_id"):
            c = await db.carriers.find_one({"id": truck["carrier_id"]})
            if c:
                related.append({
                    "type": "carrier", "title": c.get("name") or "Carrier",
                    "subtitle": "Truck owner",
                    "status": c.get("status") or "active",
                    "source": "carriers",
                    "route": f"/admin/transportation/carriers/{c.get('id')}",
                })
    if _permits(allowed, "trucks"):
        try:
            rows = await db.transport_truck_inspections.find({
                "truck_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "inspection",
                    "title": r.get("inspection_type") or "Inspection",
                    "subtitle": r.get("status") or "",
                    "status": r.get("status") or "unknown",
                    "source": "transport_truck_inspections",
                    "route": "/admin/transportation/inspections",
                })
        except Exception:
            pass
    if _permits(allowed, "dispatch"):
        try:
            rows = await db.dispatch_assignments.find({
                "truck_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "assignment",
                    "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                    "subtitle": r.get("driver_name") or "",
                    "status": r.get("state") or "active",
                    "source": "dispatch_assignments",
                    "route": "/admin/transportation/dispatch",
                })
        except Exception:
            pass
    return {"related_records": related[:SECTION_LIMITS["related_records"]],
            "open_actions": [], "timeline": []}


async def _related_for_carrier(db, eid: str, allowed: set) -> Dict[str, Any]:
    related: List[Dict[str, Any]] = []
    if _permits(allowed, "drivers"):
        try:
            rows = await db.transport_persons.find({
                "carrier_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "driver", "title": r.get("name") or "Driver",
                    "subtitle": "Driver of carrier",
                    "status": r.get("status") or "active",
                    "source": "transport_persons",
                    "route": f"/admin/transportation/drivers/{r.get('id')}",
                })
        except Exception:
            pass
    if _permits(allowed, "trucks"):
        try:
            rows = await db.transport_trucks.find({
                "carrier_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "truck",
                    "title": f"Truck {r.get('unit_number') or '—'}",
                    "subtitle": r.get("vin") or "",
                    "status": r.get("status") or "active",
                    "source": "transport_trucks",
                    "route": f"/admin/transportation/trucks/{r.get('id')}",
                })
        except Exception:
            pass
    if _permits(allowed, "documents"):
        try:
            rows = await db.carrier_documents.find({
                "carrier_id": eid}).limit(SECTION_LIMITS["related_records"]).to_list(SECTION_LIMITS["related_records"])
            for r in rows:
                related.append({
                    "type": "document",
                    "title": r.get("document_type") or "Document",
                    "subtitle": r.get("status") or "",
                    "status": r.get("status") or "unknown",
                    "source": "carrier_documents",
                    "route": "/admin/transportation/documents",
                })
        except Exception:
            pass
    return {"related_records": related[:SECTION_LIMITS["related_records"]],
            "open_actions": [], "timeline": []}


async def _audit_rows(db, etype: str, eid: str, allowed: set) -> List[Dict[str, Any]]:
    if not _permits(allowed, "audit"):
        return []
    try:
        rows = await db.audit_events.find({
            "$or": [{"entity_id": eid}, {"target_id": eid}],
        }).limit(SECTION_LIMITS["audit"]).to_list(SECTION_LIMITS["audit"])
        return [{
            "kind": r.get("kind") or "event",
            "at": r.get("at") or r.get("created_at") or "",
            "source": "audit_events",
            "route": "/admin/transportation/audit",
        } for r in rows]
    except Exception:
        return []


async def _open_actions(db, eid: str, allowed: set) -> List[Dict[str, Any]]:
    if not _permits(allowed, "drivers") and "all" not in allowed:
        return []
    try:
        rows = await db.transport_action_items.find({
            "$or": [{"entity_id": eid}, {"target_id": eid}],
            "status": {"$in": ["open", "in_progress"]},
        }).limit(SECTION_LIMITS["open_actions"]).to_list(SECTION_LIMITS["open_actions"])
        return [{
            "type": "action_item",
            "title": r.get("title") or "Action item",
            "subtitle": r.get("event_key") or "",
            "status": r.get("status") or "open",
            "source": "transport_action_items",
            "route": "/admin/transportation/command-queue",
        } for r in rows]
    except Exception:
        return []


def register_track_18_00_phase_d_routes(
    app, db,
    require_any_portal_dep: Callable,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/admin/transportation",
        tags=["transportation-operations-relationships"],
    )

    @router.get("/related/{entity_type}/{entity_id}")
    async def related(
        entity_type: str,
        entity_id: str,
        actor: Any = Depends(require_any_portal_dep),
    ) -> Dict[str, Any]:
        if entity_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported_entity_type:{entity_type}")
        allowed = _allowed(actor if isinstance(actor, dict) else {})
        if not allowed:
            raise HTTPException(
                status_code=403, detail="no_relationships_permission")

        # Load focal entity (best-effort).
        entity = await _load_entity(db, entity_type, entity_id)

        # Fan out per-entity-type relations.
        sections = {
            "recent_activity": [],
            "timeline": [],
            "related_records": [],
            "open_actions": [],
            "audit": [],
        }
        try:
            if entity_type == "driver":
                out = await _related_for_driver(db, entity_id, allowed)
            elif entity_type == "truck":
                out = await _related_for_truck(db, entity_id, allowed)
            elif entity_type == "carrier":
                out = await _related_for_carrier(db, entity_id, allowed)
            else:
                out = {"related_records": [], "open_actions": [], "timeline": []}
            sections["related_records"] = out.get("related_records") or []
            sections["timeline"] = out.get("timeline") or []
        except Exception as exc:
            logger.warning(f"[related] section fanout: {exc}")

        sections["open_actions"] = await _open_actions(db, entity_id, allowed)
        sections["audit"] = await _audit_rows(db, entity_type, entity_id, allowed)
        # Recent activity = newest audit rows (alias).
        sections["recent_activity"] = sections["audit"][:SECTION_LIMITS["recent_activity"]]

        counts = {k: len(v) for k, v in sections.items()}

        return {
            "ok": True,
            "entity": entity,
            "sections": sections,
            "counts": counts,
            "schema_version": SCHEMA_VERSION,
        }

    app.include_router(router)
    return router


__all__ = ["register_track_18_00_phase_d_routes", "SUPPORTED_TYPES", "SCHEMA_VERSION"]
