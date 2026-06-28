"""TRACK 18.00 · Phase C · RBAC-aware Universal Search.

One thin composer endpoint that fans out across EXISTING
transportation collections, filters results per the calling
portal token's RBAC, and returns grouped + deep-linked results.

Doctrine
========
* Pure composer. Owns nothing.
* No new collection. No new index. No new business logic.
* Audit-only writes (single ``audit_events`` row per query).
* Every result carries an existing deep link or is omitted.
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "18.00C"
SAFE_MAX_LIMIT = 50
DEFAULT_LIMIT = 20
MAX_QUERY = 80
RX_FLAGS = re.IGNORECASE

# Result groups every result MUST tag itself into.
GROUPS = (
    "drivers", "carriers", "trucks", "dispatch", "projects",
    "documents", "orientation", "actions", "intelligence", "timeline",
)


def _safe_regex(q: str) -> Dict[str, Any]:
    """Bounded, escaped regex projection. Bounded to first 80 chars."""
    safe = re.escape((q or "")[:MAX_QUERY].strip())
    if not safe:
        return {}
    return {"$regex": safe, "$options": "i"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Per-portal RBAC. Returns the set of result-types the actor may see.
# ---------------------------------------------------------------------------
def _types_for_role(actor: Dict[str, Any]) -> set:
    """Return the set of result groups the actor is allowed to see.

    Driven off the ``_actor`` field set by
    ``make_require_any_portal_token`` (admin / safety / hr / shop / pm
    / dispatch / leadership / fl).
    """
    a = (actor or {}).get("_actor") or (actor or {}).get("portal") or ""
    if a in ("admin", "leadership"):
        return set(GROUPS)
    if a == "dispatch":
        return {"trucks", "drivers", "carriers", "dispatch", "projects"}
    if a == "hr":
        return {"drivers", "documents", "orientation"}
    if a == "pm":
        return {"projects", "dispatch", "trucks"}
    if a == "safety":
        return {"drivers", "trucks"}
    if a == "shop":
        return {"trucks"}
    if a == "fl":
        return {"drivers", "projects"}
    return set()


# ---------------------------------------------------------------------------
# Per-collection fanout. Each returns a list of result dicts (capped).
# ---------------------------------------------------------------------------
async def _hit_drivers(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    cur = db.transport_persons.find({
        "$or": [{"name": rx}, {"employee_id": rx}],
    }).limit(lim)
    out = []
    for r in await cur.to_list(lim):
        rid = r.get("id") or str(r.get("_id"))
        out.append({
            "type": "driver", "group": "drivers",
            "title": r.get("name") or "(unnamed driver)",
            "subtitle": (r.get("employee_id") or "").strip()
                        or "Driver record",
            "status": r.get("status") or "active",
            "source": "transport_persons",
            "route": f"/admin/transportation/drivers/{rid}",
            "reason": "Matched name or employee id",
            "metadata": {"id": rid},
        })
    return out


async def _hit_carriers(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    cur = db.carriers.find({
        "$or": [{"name": rx}, {"dot_number": rx},
                {"mc_number": rx}, {"contact_name": rx}],
    }).limit(lim)
    out = []
    for r in await cur.to_list(lim):
        rid = r.get("id") or str(r.get("_id"))
        out.append({
            "type": "carrier", "group": "carriers",
            "title": r.get("name") or "(unnamed carrier)",
            "subtitle": " · ".join([
                x for x in [r.get("dot_number"), r.get("mc_number")] if x]) or "Carrier record",
            "status": r.get("status") or "unknown",
            "source": "carriers",
            "route": f"/admin/transportation/carriers/{rid}",
            "reason": "Matched name / DOT / MC / contact",
            "metadata": {"id": rid},
        })
    return out


async def _hit_trucks(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    cur = db.transport_trucks.find({
        "$or": [{"unit_number": rx}, {"vin": rx},
                {"plate": rx}, {"truck_number": rx}],
    }).limit(lim)
    out = []
    for r in await cur.to_list(lim):
        rid = r.get("id") or str(r.get("_id"))
        unit = r.get("unit_number") or r.get("truck_number") or "—"
        out.append({
            "type": "truck", "group": "trucks",
            "title": f"Truck {unit}",
            "subtitle": (r.get("vin") or "")[-6:] or "Truck record",
            "status": r.get("status") or "active",
            "source": "transport_trucks",
            "route": f"/admin/transportation/trucks/{rid}",
            "reason": "Matched unit / VIN / plate",
            "metadata": {"id": rid, "unit": unit},
        })
    return out


async def _hit_dispatch(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    try:
        cur = db.dispatch_assignments.find({
            "$or": [{"assignment_id": rx}, {"project_number": rx},
                    {"driver_name": rx}, {"unit_number": rx},
                    {"carrier_name": rx}],
        }).limit(lim)
        rows = await cur.to_list(lim)
    except Exception as exc:
        logger.warning(f"[search] dispatch fanout: {exc}")
        return []
    out = []
    for r in rows:
        aid = r.get("assignment_id") or r.get("id") or str(r.get("_id"))
        out.append({
            "type": "assignment", "group": "dispatch",
            "title": f"Assignment {aid}",
            "subtitle": " · ".join([
                x for x in [r.get("project_number"), r.get("driver_name"),
                            r.get("unit_number")] if x]) or "Dispatch row",
            "status": r.get("state") or r.get("status") or "active",
            "source": "dispatch_assignments",
            "route": "/admin/transportation/dispatch",
            "reason": "Matched assignment / project / driver / unit",
            "metadata": {"assignment_id": aid},
        })
    return out


async def _hit_projects(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    try:
        cur = db.projects.find({
            "$or": [{"project_number": rx}, {"name": rx},
                    {"customer": rx}, {"location": rx}],
        }).limit(lim)
        rows = await cur.to_list(lim)
    except Exception as exc:
        logger.warning(f"[search] projects fanout: {exc}")
        return []
    out = []
    for r in rows:
        pn = r.get("project_number") or r.get("id") or ""
        out.append({
            "type": "project", "group": "projects",
            "title": r.get("name") or f"Project {pn}",
            "subtitle": pn or r.get("customer") or "Project record",
            "status": r.get("status") or "active",
            "source": "projects",
            "route": f"/pm/project/{pn}" if pn else "/admin/transportation/live-operations",
            "reason": "Matched project number / name / customer",
            "metadata": {"project_number": pn},
        })
    return out


async def _hit_documents(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    out: List[Dict[str, Any]] = []
    for coll, route_kind in (
        ("carrier_documents", "carriers"),
        ("driver_documents", "drivers"),
    ):
        try:
            cur = db[coll].find({
                "$or": [{"document_type": rx}, {"status": rx},
                        {"file_name": rx}],
            }).limit(lim)
            for r in await cur.to_list(lim):
                rid = r.get("id") or str(r.get("_id"))
                out.append({
                    "type": "document", "group": "documents",
                    "title": r.get("document_type") or "Document",
                    "subtitle": f"{coll} · {r.get('status', 'unknown')}",
                    "status": r.get("status") or "unknown",
                    "source": coll,
                    "route": "/admin/transportation/documents",
                    "reason": "Matched document type / status / file name",
                    "metadata": {"id": rid, "kind": route_kind},
                })
        except Exception as exc:
            logger.warning(f"[search] {coll} fanout: {exc}")
    return out[:lim]


async def _hit_orientation(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    out: List[Dict[str, Any]] = []
    try:
        cur = db.transport_orientation_modules.find({
            "$or": [{"key": rx}, {"title": rx}],
        }).limit(lim)
        for r in await cur.to_list(lim):
            mid = r.get("id") or str(r.get("_id"))
            out.append({
                "type": "orientation_module", "group": "orientation",
                "title": r.get("title") or r.get("key") or "Module",
                "subtitle": "Orientation module",
                "status": "active",
                "source": "transport_orientation_modules",
                "route": "/admin/transportation/orientation",
                "reason": "Matched module key / title",
                "metadata": {"id": mid},
            })
    except Exception as exc:
        logger.warning(f"[search] orientation modules fanout: {exc}")
    try:
        cur = db.transport_orientation_certificates.find({
            "$or": [{"certificate_number": rx}, {"person_name": rx}],
        }).limit(lim)
        for r in await cur.to_list(lim):
            cid = r.get("id") or str(r.get("_id"))
            cnum = r.get("certificate_number") or ""
            out.append({
                "type": "orientation_certificate", "group": "orientation",
                "title": f"Certificate {cnum}",
                "subtitle": r.get("person_name") or "Orientation certificate",
                "status": r.get("status") or "issued",
                "source": "transport_orientation_certificates",
                "route": "/admin/transportation/orientation",
                "reason": "Matched certificate number / person",
                "metadata": {"id": cid, "cnum": cnum},
            })
    except Exception as exc:
        logger.warning(f"[search] orientation certs fanout: {exc}")
    return out[:lim]


async def _hit_actions(db, q: str, lim: int) -> List[Dict[str, Any]]:
    rx = _safe_regex(q)
    if not rx:
        return []
    try:
        cur = db.transport_action_items.find({
            "$or": [{"title": rx}, {"status": rx}, {"event_key": rx}],
        }).limit(lim)
        rows = await cur.to_list(lim)
    except Exception as exc:
        logger.warning(f"[search] actions fanout: {exc}")
        return []
    out = []
    for r in rows:
        aid = r.get("id") or str(r.get("_id"))
        out.append({
            "type": "action_item", "group": "actions",
            "title": r.get("title") or "Action item",
            "subtitle": r.get("event_key") or r.get("status") or "Action",
            "status": r.get("status") or "open",
            "source": "transport_action_items",
            "route": "/admin/transportation/command-queue",
            "reason": "Matched title / status / event key",
            "metadata": {"id": aid},
        })
    return out


GROUP_FANOUTS = {
    "drivers":      _hit_drivers,
    "carriers":     _hit_carriers,
    "trucks":       _hit_trucks,
    "dispatch":     _hit_dispatch,
    "projects":     _hit_projects,
    "documents":    _hit_documents,
    "orientation":  _hit_orientation,
    "actions":      _hit_actions,
}


def register_track_18_00_phase_c_routes(
    app, db,
    require_any_portal_dep: Callable,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/admin/transportation",
        tags=["transportation-operations-search"],
    )

    @router.get("/search")
    async def search(
        q: str = Query(..., min_length=1, max_length=MAX_QUERY),
        limit: int = Query(DEFAULT_LIMIT, ge=1, le=SAFE_MAX_LIMIT),
        types: Optional[str] = Query(None),
        actor: Any = Depends(require_any_portal_dep),
    ) -> Dict[str, Any]:
        q = (q or "").strip()
        if not q:
            raise HTTPException(status_code=400, detail="q is required")

        allowed = _types_for_role(actor if isinstance(actor, dict) else {})
        if not allowed:
            raise HTTPException(status_code=403, detail="no_search_permission")

        # Optional caller-side `types` filter narrows further within
        # the allowed set.
        if types:
            wanted = {t.strip() for t in types.split(",") if t.strip()}
            allowed = allowed & wanted

        # Fan out in parallel across permitted groups.
        per_group = max(3, limit // max(len(allowed), 1))
        coros = []
        labels = []
        for g in GROUPS:
            if g not in allowed or g not in GROUP_FANOUTS:
                continue
            coros.append(GROUP_FANOUTS[g](db, q, per_group))
            labels.append(g)
        try:
            buckets = await asyncio.wait_for(
                asyncio.gather(*coros, return_exceptions=True),
                timeout=4.0,
            )
        except asyncio.TimeoutError:
            buckets = [[] for _ in coros]

        results: List[Dict[str, Any]] = []
        counts: Dict[str, int] = {}
        for label, rows in zip(labels, buckets):
            if isinstance(rows, Exception):
                rows = []
            counts[label] = len(rows)
            results.extend(rows)

        # Bound to overall limit.
        results = results[:limit]

        # Lightweight audit row (no PII — store query LENGTH and the
        # first 3 characters as a safety probe, not the full query).
        try:
            await db.audit_events.insert_one({
                "kind": "transportation_search_performed",
                "at": _now_iso(),
                "actor": (actor or {}).get("id") if isinstance(actor, dict) else None,
                "portal": (actor or {}).get("_actor") if isinstance(actor, dict) else None,
                "role": (actor or {}).get("role") if isinstance(actor, dict) else None,
                "query_length": len(q),
                "query_prefix": q[:3],
                "result_count": len(results),
                "counts": counts,
            })
        except Exception as exc:
            logger.warning(f"[search] audit write: {exc}")

        return {
            "ok": True,
            "query": q,
            "results": results,
            "counts": counts,
            "schema_version": SCHEMA_VERSION,
        }

    app.include_router(router)
    return router


__all__ = ["register_track_18_00_phase_c_routes"]
