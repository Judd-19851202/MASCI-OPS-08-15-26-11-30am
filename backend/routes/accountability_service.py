"""routes/accountability_service.py — Pillar 1 · Phase 1A-3.

Read-only Accountability service surface. Exposes the certified
projection layer from ``lib/accountability_projection.py`` via three
admin-strict endpoints:

    GET /api/admin/accountability/sources
        — list of supported source_module ids · static metadata

    GET /api/admin/accountability/item?source_module=...&source_record_id=...
        — single projection for one source row · pulls the live row
          from the source collection · returns the canonical 24-field
          shape

    GET /api/admin/accountability/snapshot[?per_source=50]
        — bulk projection across all six certified sources · capped per
          source · 15-second in-memory cache mirroring command_center
          pattern

This module:
    - Imports the certified projection library.
    - Performs ZERO writes to any collection.
    - Does NOT touch source workflows.
    - Does NOT touch Command Center routes.
    - Emits no notifications, tasks, or events.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.accountability_projection import (
    CANONICAL_STATUSES,
    project_corrective_action,
    project_fleet_defect,
    project_incident,
    project_po_request,
    project_task,
    project_virtual_signal,
)


# ─── In-memory cache (mirrors command_center & recovery_dashboard) ──
_CACHE: Dict[str, Any] = {"computed_at": 0.0, "snapshot": None,
                          "per_source": None}
_CACHE_TTL_SECONDS = 15.0


# ─── Supported source descriptors ───────────────────────────────────
_SOURCE_DESCRIPTORS: List[Dict[str, Any]] = [
    {"source_module": "tasks",
     "collection": "tasks",
     "kind": "first_class",
     "is_async_projection": False,
     "description": "Unified task / action items (db.tasks)"},
    {"source_module": "safety.corrective_actions",
     "collection": "corrective_actions",
     "kind": "domain_workflow",
     "is_async_projection": False,
     "description": "Safety corrective actions (db.corrective_actions)"},
    {"source_module": "po.requests",
     "collection": "po_requests",
     "kind": "domain_workflow",
     "is_async_projection": False,
     "description": "PO approval requests (db.po_requests)"},
    {"source_module": "equipment.dvir",
     "collection": "fleet_defects",
     "kind": "domain_workflow",
     "is_async_projection": False,
     "description": "Fleet DVIR defects (db.fleet_defects)"},
    {"source_module": "safety.incidents",
     "collection": "incidents",
     "kind": "domain_workflow",
     "is_async_projection": True,
     "description": "Safety incidents (db.incidents · async · CA-aware)"},
    {"source_module": "virtual.signals",
     "collection": "<virtual>",
     "kind": "virtual",
     "is_async_projection": False,
     "description": "Signals not backed by a per-row collection "
                    "(e.g. JOBS-DR-MISSING aggregate). Read-only; "
                    "populated by Command Center signal payloads."},
]


# ─── Per-source bulk projection helpers ─────────────────────────────
async def _project_tasks_page(db: Any, limit: int) -> List[Dict[str, Any]]:
    cursor = db.tasks.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    return [project_task(r) for r in rows]


async def _project_cas_page(db: Any, limit: int) -> List[Dict[str, Any]]:
    cursor = db.corrective_actions.find({}, {"_id": 0}).sort(
        "created_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    return [project_corrective_action(r) for r in rows]


async def _project_pos_page(db: Any, limit: int) -> List[Dict[str, Any]]:
    cursor = db.po_requests.find({}, {"_id": 0}).sort(
        "created_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    return [project_po_request(r) for r in rows]


async def _project_defects_page(db: Any, limit: int) -> List[Dict[str, Any]]:
    cursor = db.fleet_defects.find({}, {"_id": 0}).sort(
        "reported_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    return [project_fleet_defect(r) for r in rows]


async def _project_incidents_page(db: Any, limit: int) -> List[Dict[str, Any]]:
    cursor = db.incidents.find({}, {"_id": 0}).sort(
        "created_at", -1).limit(limit)
    rows = await cursor.to_list(length=limit)
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(await project_incident(db, r))
    return out


def _empty_virtual_section() -> List[Dict[str, Any]]:
    """Virtual signals don't have a backing collection; the snapshot
    returns an empty list. Callers that want a specific signal
    projected should POST it to the dedicated `item` endpoint with
    the payload."""
    return []


# ─── Aggregate helpers ──────────────────────────────────────────────
def _counts_from_projections(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_status: Dict[str, int] = {s: 0 for s in CANONICAL_STATUSES}
    overdue = 0
    for p in items:
        s = p.get("status") or "open"
        if s in by_status:
            by_status[s] += 1
        if p.get("overdue"):
            overdue += 1
    return {"total": len(items), "by_status": by_status, "overdue": overdue}


# ─── Router factory ─────────────────────────────────────────────────
def build_accountability_router(db: Any, require_admin_strict_dep: Any
                                  ) -> APIRouter:
    router = APIRouter()

    @router.get("/admin/accountability/sources")
    async def get_sources(_: bool = Depends(require_admin_strict_dep)
                          ) -> Dict[str, Any]:
        return {
            "canonical_statuses": list(CANONICAL_STATUSES),
            "sources": _SOURCE_DESCRIPTORS,
        }

    @router.get("/admin/accountability/item")
    async def get_item(
        source_module: str = Query(..., min_length=2, max_length=64),
        source_record_id: str = Query(..., min_length=1, max_length=200),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        sm = source_module.strip()

        if sm == "tasks":
            row = await db.tasks.find_one({"id": source_record_id},
                                           {"_id": 0})
            if not row:
                raise HTTPException(404, f"task {source_record_id!r} not found")
            return project_task(row)

        if sm == "safety.corrective_actions":
            row = await db.corrective_actions.find_one(
                {"id": source_record_id}, {"_id": 0})
            if not row:
                raise HTTPException(404, f"corrective_action {source_record_id!r} not found")
            return project_corrective_action(row)

        if sm == "po.requests":
            row = await db.po_requests.find_one({"id": source_record_id},
                                                  {"_id": 0})
            if not row:
                raise HTTPException(404, f"po_request {source_record_id!r} not found")
            return project_po_request(row)

        if sm == "equipment.dvir":
            row = await db.fleet_defects.find_one({"id": source_record_id},
                                                    {"_id": 0})
            if not row:
                raise HTTPException(404, f"fleet_defect {source_record_id!r} not found")
            return project_fleet_defect(row)

        if sm == "safety.incidents":
            row = await db.incidents.find_one({"id": source_record_id},
                                                {"_id": 0})
            if not row:
                raise HTTPException(404, f"incident {source_record_id!r} not found")
            return await project_incident(db, row)

        if sm.startswith("virtual."):
            # Virtual signals have no backing row; the caller can
            # supply a payload via the snapshot bulk endpoint. The
            # /item endpoint cannot fabricate one — return 404.
            raise HTTPException(
                404,
                f"virtual signals have no backing row · use /snapshot "
                f"or supply payload separately (got {sm})")

        raise HTTPException(400, f"unsupported source_module {sm!r}")

    @router.get("/admin/accountability/snapshot")
    async def get_snapshot(
        per_source: int = Query(50, ge=1, le=500),
        _: bool = Depends(require_admin_strict_dep),
    ) -> Dict[str, Any]:
        now_wall = time.time()
        if (_CACHE["snapshot"] is not None
                and _CACHE["per_source"] == per_source
                and (now_wall - _CACHE["computed_at"]) < _CACHE_TTL_SECONDS):
            cached = dict(_CACHE["snapshot"])
            cached["cached"] = True
            return cached

        t_start = time.perf_counter()

        tasks_proj = await _project_tasks_page(db, per_source)
        t_tasks = time.perf_counter()

        cas_proj = await _project_cas_page(db, per_source)
        t_cas = time.perf_counter()

        pos_proj = await _project_pos_page(db, per_source)
        t_pos = time.perf_counter()

        defects_proj = await _project_defects_page(db, per_source)
        t_def = time.perf_counter()

        incidents_proj = await _project_incidents_page(db, per_source)
        t_inc = time.perf_counter()

        virtual_proj = _empty_virtual_section()
        t_end = time.perf_counter()

        sections = {
            "tasks": {
                "items": tasks_proj,
                "counts": _counts_from_projections(tasks_proj),
            },
            "safety.corrective_actions": {
                "items": cas_proj,
                "counts": _counts_from_projections(cas_proj),
            },
            "po.requests": {
                "items": pos_proj,
                "counts": _counts_from_projections(pos_proj),
            },
            "equipment.dvir": {
                "items": defects_proj,
                "counts": _counts_from_projections(defects_proj),
            },
            "safety.incidents": {
                "items": incidents_proj,
                "counts": _counts_from_projections(incidents_proj),
            },
            "virtual.signals": {
                "items": virtual_proj,
                "counts": _counts_from_projections(virtual_proj),
            },
        }

        # Roll-up totals
        total_items = sum(s["counts"]["total"] for s in sections.values())
        total_overdue = sum(s["counts"]["overdue"] for s in sections.values())
        rollup_by_status: Dict[str, int] = {s: 0 for s in CANONICAL_STATUSES}
        for sec in sections.values():
            for k, v in sec["counts"]["by_status"].items():
                rollup_by_status[k] = rollup_by_status.get(k, 0) + v

        snapshot_doc = {
            "phase": "1A-3",
            "per_source": per_source,
            "sections": sections,
            "rollup": {
                "total_items": total_items,
                "overdue_items": total_overdue,
                "by_status": rollup_by_status,
            },
            "timing_ms": {
                "tasks": round((t_tasks - t_start) * 1000.0, 2),
                "corrective_actions": round((t_cas - t_tasks) * 1000.0, 2),
                "po_requests": round((t_pos - t_cas) * 1000.0, 2),
                "fleet_defects": round((t_def - t_pos) * 1000.0, 2),
                "incidents": round((t_inc - t_def) * 1000.0, 2),
                "virtual": round((t_end - t_inc) * 1000.0, 2),
                "total": round((t_end - t_start) * 1000.0, 2),
            },
            "cached": False,
        }

        _CACHE["snapshot"] = snapshot_doc
        _CACHE["per_source"] = per_source
        _CACHE["computed_at"] = now_wall
        return snapshot_doc

    return router
