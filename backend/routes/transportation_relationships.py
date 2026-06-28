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

import logging
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

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


# ---------------------------------------------------------------------------
# RBAC matrix — mirrors Phase C `_actor` doctrine.
# Unknown / anonymous returns an empty set → endpoint responds 403.
# ---------------------------------------------------------------------------
def _allowed(actor: Optional[Dict[str, Any]]) -> set:
    """Return permission tags for the actor's portal role.

    `all` is the admin/leadership wildcard. Otherwise the set lists
    the relation groups the actor may see. Unauthorized relations
    are OMITTED entirely (never redacted) so the existence of a
    relationship is never leaked.
    """
    a = (actor or {}).get("_actor") or (actor or {}).get("portal") or ""
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


def _bounded(limit: Optional[int], section: str) -> int:
    base = SECTION_LIMITS[section]
    if not limit:
        return base
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return base
    return max(1, min(n, MAX_LIMIT))


# ---------------------------------------------------------------------------
# Entity loader — best-effort title/subtitle/status/route for the focal record.
# Returns a normalized envelope even when the record cannot be located, so
# the right rail can still render an "(not found)" entity banner.
# ---------------------------------------------------------------------------
_ENTITY_MAP = {
    "driver": ("transport_persons", "name", "/admin/transportation/drivers/{id}"),
    "carrier": ("carriers", "name", "/admin/transportation/carriers/{id}"),
    "truck": ("transport_trucks", "unit_number", "/admin/transportation/trucks/{id}"),
    "dispatch_assignment": (
        "dispatch_assignments", "assignment_id",
        "/admin/transportation/dispatch"),
    "project": ("projects", "project_number", "/pm/project/{id}"),
    "certificate": (
        "transport_orientation_certificates", "certificate_number",
        "/admin/transportation/orientation"),
    "document": (
        "carrier_documents", "document_type",
        "/admin/transportation/documents"),
    "orientation": (
        "transport_orientation_assignments", "id",
        "/admin/transportation/orientation"),
    "inspection": (
        "transport_truck_inspections", "id",
        "/admin/transportation/inspections"),
    "action_item": (
        "transport_action_items", "title",
        "/admin/transportation/command-queue"),
    "cleanup_signal": (
        None, None,
        "/admin/transportation/intelligence/cleanup"),
}


async def _load_entity(db, etype: str, eid: str) -> Dict[str, Any]:
    coll_name, title_field, route_tpl = _ENTITY_MAP.get(
        etype, (None, None, "/admin/transportation"))
    if not coll_name:
        return {
            "type": etype, "id": eid, "title": eid,
            "subtitle": "", "status": "unknown",
            "route": route_tpl,
        }
    try:
        row = await db[coll_name].find_one({"id": eid})
    except Exception:
        row = None
    if not row:
        return {
            "type": etype, "id": eid, "title": "(not found)",
            "subtitle": "", "status": "unknown",
            "route": route_tpl.replace("{id}", eid),
        }
    return {
        "type": etype,
        "id": row.get("id") or eid,
        "title": str(row.get(title_field) or eid),
        "subtitle": str(row.get("status") or ""),
        "status": str(row.get("status") or "active"),
        "route": route_tpl.replace("{id}", row.get("id") or eid),
    }


# ---------------------------------------------------------------------------
# Per-entity relation loaders. Each runs only if RBAC permits the
# relation group. All bounded by SECTION_LIMITS. All read-only.
# Bare except blocks isolate per-collection failures so a missing
# collection never blanks the whole rail (graceful partial results).
# ---------------------------------------------------------------------------
async def _safe_find(coll, query: Dict[str, Any], lim: int) -> List[Dict[str, Any]]:
    try:
        cur = coll.find(query)
        if hasattr(cur, "limit"):
            cur = cur.limit(lim)
        rows = await cur.to_list(lim)
        return list(rows or [])
    except Exception as exc:
        logger.debug(f"[related] safe_find {query!r}: {exc}")
        return []


async def _related_for_driver(db, eid: str, allowed: set,
                              lim: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if _permits(allowed, "carriers"):
        person = await db.transport_persons.find_one({"id": eid})
        if person and person.get("carrier_id"):
            c = await db.carriers.find_one({"id": person["carrier_id"]})
            if c:
                out.append({
                    "type": "carrier", "id": c.get("id"),
                    "title": c.get("name") or "Carrier",
                    "subtitle": "Driver of record",
                    "status": c.get("status") or "active",
                    "source": "carriers",
                    "route": f"/admin/transportation/carriers/{c.get('id')}",
                })
    if _permits(allowed, "dispatch"):
        for r in await _safe_find(db.dispatch_assignments, {"driver_id": eid}, lim):
            out.append({
                "type": "dispatch_assignment", "id": r.get("id"),
                "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                "subtitle": r.get("project_number") or "",
                "status": r.get("state") or "active",
                "source": "dispatch_assignments",
                "route": "/admin/transportation/dispatch",
            })
    if _permits(allowed, "documents"):
        for r in await _safe_find(db.driver_documents,
                                   {"transport_person_id": eid}, lim):
            out.append({
                "type": "document", "id": r.get("id"),
                "title": r.get("document_type") or "Document",
                "subtitle": r.get("status") or "",
                "status": r.get("status") or "unknown",
                "source": "driver_documents",
                "route": "/admin/transportation/documents",
            })
    if _permits(allowed, "orientation"):
        for r in await _safe_find(db.transport_orientation_assignments,
                                   {"transport_person_id": eid}, lim):
            out.append({
                "type": "orientation", "id": r.get("id"),
                "title": r.get("module_key") or "Orientation",
                "subtitle": r.get("status") or "",
                "status": r.get("status") or "unknown",
                "source": "transport_orientation_assignments",
                "route": "/admin/transportation/orientation",
            })
    return out[:lim]


async def _related_for_truck(db, eid: str, allowed: set,
                             lim: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if _permits(allowed, "carriers"):
        truck = await db.transport_trucks.find_one({"id": eid})
        if truck and truck.get("carrier_id"):
            c = await db.carriers.find_one({"id": truck["carrier_id"]})
            if c:
                out.append({
                    "type": "carrier", "id": c.get("id"),
                    "title": c.get("name") or "Carrier",
                    "subtitle": "Truck owner",
                    "status": c.get("status") or "active",
                    "source": "carriers",
                    "route": f"/admin/transportation/carriers/{c.get('id')}",
                })
    if _permits(allowed, "trucks"):
        for r in await _safe_find(db.transport_truck_inspections,
                                   {"truck_id": eid}, lim):
            out.append({
                "type": "inspection", "id": r.get("id"),
                "title": r.get("inspection_type") or "Inspection",
                "subtitle": r.get("result") or r.get("status") or "",
                "status": r.get("status") or "unknown",
                "source": "transport_truck_inspections",
                "route": "/admin/transportation/inspections",
            })
    if _permits(allowed, "dispatch"):
        for r in await _safe_find(db.dispatch_assignments, {"truck_id": eid}, lim):
            out.append({
                "type": "dispatch_assignment", "id": r.get("id"),
                "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                "subtitle": r.get("driver_name") or "",
                "status": r.get("state") or "active",
                "source": "dispatch_assignments",
                "route": "/admin/transportation/dispatch",
            })
    return out[:lim]


async def _related_for_carrier(db, eid: str, allowed: set,
                               lim: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if _permits(allowed, "drivers"):
        for r in await _safe_find(db.transport_persons, {"carrier_id": eid}, lim):
            out.append({
                "type": "driver", "id": r.get("id"),
                "title": r.get("name") or "Driver",
                "subtitle": "Driver of carrier",
                "status": r.get("status") or "active",
                "source": "transport_persons",
                "route": f"/admin/transportation/drivers/{r.get('id')}",
            })
    if _permits(allowed, "trucks"):
        for r in await _safe_find(db.transport_trucks, {"carrier_id": eid}, lim):
            out.append({
                "type": "truck", "id": r.get("id"),
                "title": f"Truck {r.get('unit_number') or '—'}",
                "subtitle": r.get("vin") or "",
                "status": r.get("status") or "active",
                "source": "transport_trucks",
                "route": f"/admin/transportation/trucks/{r.get('id')}",
            })
    if _permits(allowed, "documents"):
        for r in await _safe_find(db.carrier_documents, {"carrier_id": eid}, lim):
            out.append({
                "type": "document", "id": r.get("id"),
                "title": r.get("document_type") or "Document",
                "subtitle": r.get("status") or "",
                "status": r.get("status") or "unknown",
                "source": "carrier_documents",
                "route": "/admin/transportation/documents",
            })
    if _permits(allowed, "dispatch"):
        for r in await _safe_find(db.dispatch_assignments,
                                   {"carrier_id": eid}, lim):
            out.append({
                "type": "dispatch_assignment", "id": r.get("id"),
                "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                "subtitle": r.get("driver_name") or "",
                "status": r.get("state") or "active",
                "source": "dispatch_assignments",
                "route": "/admin/transportation/dispatch",
            })
    return out[:lim]


async def _related_for_project(db, eid: str, allowed: set,
                               lim: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if _permits(allowed, "dispatch"):
        for r in await _safe_find(db.dispatch_assignments,
                                   {"project_number": eid}, lim):
            out.append({
                "type": "dispatch_assignment", "id": r.get("id"),
                "title": f"Assignment {r.get('assignment_id') or r.get('id')}",
                "subtitle": r.get("driver_name") or "",
                "status": r.get("state") or "active",
                "source": "dispatch_assignments",
                "route": "/admin/transportation/dispatch",
            })
    return out[:lim]


async def _related_for_dispatch_assignment(db, eid: str, allowed: set,
                                           lim: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    asg = await db.dispatch_assignments.find_one({"id": eid})
    if not asg:
        return out
    if _permits(allowed, "drivers") and asg.get("driver_id"):
        d = await db.transport_persons.find_one({"id": asg["driver_id"]})
        if d:
            out.append({
                "type": "driver", "id": d.get("id"),
                "title": d.get("name") or "Driver",
                "subtitle": "Assigned driver",
                "status": d.get("status") or "active",
                "source": "transport_persons",
                "route": f"/admin/transportation/drivers/{d.get('id')}",
            })
    if _permits(allowed, "trucks") and asg.get("truck_id"):
        t = await db.transport_trucks.find_one({"id": asg["truck_id"]})
        if t:
            out.append({
                "type": "truck", "id": t.get("id"),
                "title": f"Truck {t.get('unit_number') or '—'}",
                "subtitle": "Assigned truck",
                "status": t.get("status") or "active",
                "source": "transport_trucks",
                "route": f"/admin/transportation/trucks/{t.get('id')}",
            })
    if _permits(allowed, "carriers") and asg.get("carrier_id"):
        c = await db.carriers.find_one({"id": asg["carrier_id"]})
        if c:
            out.append({
                "type": "carrier", "id": c.get("id"),
                "title": c.get("name") or "Carrier",
                "subtitle": "Hauling carrier",
                "status": c.get("status") or "active",
                "source": "carriers",
                "route": f"/admin/transportation/carriers/{c.get('id')}",
            })
    if _permits(allowed, "projects") and asg.get("project_number"):
        out.append({
            "type": "project", "id": asg["project_number"],
            "title": f"Project {asg['project_number']}",
            "subtitle": "Dispatch project",
            "status": "active",
            "source": "projects",
            "route": f"/pm/project/{asg['project_number']}",
        })
    return out[:lim]


async def _related_for_document(db, eid: str, allowed: set,
                                lim: int) -> List[Dict[str, Any]]:
    """A document row binds to either a carrier or a driver — surface both."""
    if not _permits(allowed, "documents") and "all" not in allowed:
        return []
    out: List[Dict[str, Any]] = []
    doc = await db.carrier_documents.find_one({"id": eid})
    if doc and doc.get("carrier_id"):
        c = await db.carriers.find_one({"id": doc["carrier_id"]})
        if c:
            out.append({
                "type": "carrier", "id": c.get("id"),
                "title": c.get("name") or "Carrier",
                "subtitle": "Document owner",
                "status": c.get("status") or "active",
                "source": "carriers",
                "route": f"/admin/transportation/carriers/{c.get('id')}",
            })
    return out[:lim]


async def _related_for_certificate(db, eid: str, allowed: set,
                                   lim: int) -> List[Dict[str, Any]]:
    if not _permits(allowed, "orientation") and "all" not in allowed:
        return []
    out: List[Dict[str, Any]] = []
    cert = await db.transport_orientation_certificates.find_one({"id": eid})
    if cert and cert.get("transport_person_id"):
        d = await db.transport_persons.find_one(
            {"id": cert["transport_person_id"]})
        if d and _permits(allowed, "drivers"):
            out.append({
                "type": "driver", "id": d.get("id"),
                "title": d.get("name") or "Driver",
                "subtitle": "Certificate holder",
                "status": d.get("status") or "active",
                "source": "transport_persons",
                "route": f"/admin/transportation/drivers/{d.get('id')}",
            })
    return out[:lim]


async def _related_for_inspection(db, eid: str, allowed: set,
                                  lim: int) -> List[Dict[str, Any]]:
    if not _permits(allowed, "trucks") and "all" not in allowed:
        return []
    out: List[Dict[str, Any]] = []
    insp = await db.transport_truck_inspections.find_one({"id": eid})
    if insp and insp.get("truck_id"):
        t = await db.transport_trucks.find_one({"id": insp["truck_id"]})
        if t:
            out.append({
                "type": "truck", "id": t.get("id"),
                "title": f"Truck {t.get('unit_number') or '—'}",
                "subtitle": "Inspected unit",
                "status": t.get("status") or "active",
                "source": "transport_trucks",
                "route": f"/admin/transportation/trucks/{t.get('id')}",
            })
    return out[:lim]


# ---------------------------------------------------------------------------
# Cross-cutting sections — audit, open_actions, timeline.
# ---------------------------------------------------------------------------
async def _audit_rows(db, eid: str, allowed: set,
                      lim: int) -> List[Dict[str, Any]]:
    if not _permits(allowed, "audit"):
        return []
    try:
        cur = db.audit_events.find(
            {"$or": [{"entity_id": eid}, {"target_id": eid}]})
        if hasattr(cur, "sort"):
            try:
                cur = cur.sort("at", -1)
            except Exception:
                pass
        if hasattr(cur, "limit"):
            cur = cur.limit(lim)
        rows = await cur.to_list(lim)
    except Exception:
        rows = []
    return [{
        "kind": r.get("kind") or "event",
        "at": r.get("at") or r.get("created_at") or "",
        "actor": r.get("actor") or "",
        "source": "audit_events",
        "route": "/admin/transportation/administration/audit",
    } for r in (rows or [])][:lim]


async def _open_actions(db, eid: str, allowed: set,
                       lim: int) -> List[Dict[str, Any]]:
    """Open transport action items linked to this entity.

    Visible to any role that has at least one non-audit permission.
    The action_item collection already carries scope tags so this is
    a safe read for every authenticated portal role.
    """
    if not allowed or allowed == {"audit"}:
        return []
    rows = await _safe_find(
        db.transport_action_items,
        {"$or": [{"entity_id": eid}, {"target_id": eid}],
         "status": {"$in": ["open", "in_progress"]}},
        lim,
    )
    return [{
        "type": "action_item", "id": r.get("id"),
        "title": r.get("title") or "Action item",
        "subtitle": r.get("event_key") or r.get("severity") or "",
        "status": r.get("status") or "open",
        "source": "transport_action_items",
        "route": "/admin/transportation/command-queue",
    } for r in rows][:lim]


# ---------------------------------------------------------------------------
# Router registration.
# ---------------------------------------------------------------------------
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
        limit: Optional[int] = Query(default=None, ge=1, le=MAX_LIMIT),
        actor: Any = Depends(require_any_portal_dep),
    ) -> Dict[str, Any]:
        if entity_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported_entity_type:{entity_type}")
        actor_d = actor if isinstance(actor, dict) else {}
        allowed = _allowed(actor_d)
        if not allowed:
            raise HTTPException(
                status_code=403, detail="no_relationships_permission")

        rel_lim = _bounded(limit, "related_records")
        act_lim = _bounded(limit, "open_actions")
        aud_lim = _bounded(limit, "audit")

        # Focal entity envelope (best-effort).
        entity = await _load_entity(db, entity_type, entity_id)

        # Per-entity-type relation fan-out (graceful per-section).
        related_records: List[Dict[str, Any]] = []
        try:
            if entity_type == "driver":
                related_records = await _related_for_driver(db, entity_id, allowed, rel_lim)
            elif entity_type == "truck":
                related_records = await _related_for_truck(db, entity_id, allowed, rel_lim)
            elif entity_type == "carrier":
                related_records = await _related_for_carrier(db, entity_id, allowed, rel_lim)
            elif entity_type == "project":
                related_records = await _related_for_project(db, entity_id, allowed, rel_lim)
            elif entity_type == "dispatch_assignment":
                related_records = await _related_for_dispatch_assignment(
                    db, entity_id, allowed, rel_lim)
            elif entity_type == "document":
                related_records = await _related_for_document(db, entity_id, allowed, rel_lim)
            elif entity_type == "certificate":
                related_records = await _related_for_certificate(db, entity_id, allowed, rel_lim)
            elif entity_type == "inspection":
                related_records = await _related_for_inspection(db, entity_id, allowed, rel_lim)
            # action_item / orientation / cleanup_signal currently have no
            # outbound relations beyond their own audit trail.
        except Exception as exc:
            logger.warning(f"[related] section fanout: {exc}")

        open_actions = await _open_actions(db, entity_id, allowed, act_lim)
        audit_rows = await _audit_rows(db, entity_id, allowed, aud_lim)

        sections = {
            # Recent Activity is the newest slice of the audit feed.
            "recent_activity": audit_rows[:SECTION_LIMITS["recent_activity"]],
            "timeline": audit_rows[:SECTION_LIMITS["timeline"]],
            "related_records": related_records,
            "open_actions": open_actions,
            "audit": audit_rows,
        }
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


__all__ = [
    "register_track_18_00_phase_d_routes",
    "SUPPORTED_TYPES",
    "SCHEMA_VERSION",
    "SECTION_LIMITS",
    "MAX_LIMIT",
]
