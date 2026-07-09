"""
routes/dispatch_exports.py · iter395 · Phase 11.4 · DLS Operational
Intelligence Exports.

Three CSV endpoints. Each is a thin, paginated read over an existing
iter392 collection. No analytics. No charts. Foundations for future
estimating + change-order + cycle-time work, NOT a dashboard system.

Endpoints (prefix /api/dispatch/exports):
  • assignments.csv   — current dispatch_assignments snapshot
  • state-events.csv  — append-only transition log
  • haul-cycles.csv   — derived per-cycle summaries

Doctrine:
  • Tenant-scoped (X-Tenant-Id; default `masci`).
  • Dispatch + Admin only (write-grade gate; exports leak operational truth).
  • Date range optional via `?since` / `?until` (ISO 8601).
  • Hard limit per export to prevent unbounded streaming pulls.
"""
from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Query, Response

from routes.dispatch_lifecycle import DEFAULT_TENANT_ID

# TRACK 27.03 · Phase 2 · Filename stamp uses local calendar time so
# dispatchers see the same wall clock in downloaded CSVs.
from lib.platform_time import resolve_tz

logger = logging.getLogger("dispatch_exports_routes")

MAX_ROWS = 5000


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _now_stamp() -> str:
    return datetime.now(resolve_tz()).strftime("%Y%m%dT%H%M%S")


def _csv_response(rows: List[List[Any]], header: List[str], filename: str) -> Response:
    """Build a CSV HTTP response with the platform's standard headers
    (UTF-8, BOM for Excel friendliness, attachment)."""
    buf = io.StringIO()
    buf.write("\ufeff")                                # BOM for Excel
    writer = csv.writer(buf)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    body = buf.getvalue()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


def _bounded(value: Optional[str], maxlen: int = 240) -> str:
    if value is None:
        return ""
    s = str(value)
    return s if len(s) <= maxlen else s[:maxlen - 1] + "…"


def build_dispatch_exports_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch/exports", tags=["dispatch-exports"])

    def _date_query(since: Optional[str], until: Optional[str], field: str) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if since:
            q["$gte"] = since
        if until:
            q["$lte"] = until
        return {field: q} if q else {}

    # ─────────────────────────────────────────────────────────────────
    # assignments.csv
    # ─────────────────────────────────────────────────────────────────
    @router.get("/assignments.csv")
    async def export_assignments(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        since: Optional[str] = Query(None, description="ISO 8601 lower bound on assigned_at"),
        until: Optional[str] = Query(None, description="ISO 8601 upper bound on assigned_at"),
        include_completed: bool = Query(True),
        limit: int = Query(MAX_ROWS, ge=1, le=MAX_ROWS),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        query.update(_date_query(since, until, "assigned_at"))
        if not include_completed:
            query["current_state"] = {"$nin": ["COMPLETE", "OFF_SHIFT"]}
            query["cancelled_at"] = None
        cursor = (
            db.dispatch_assignments
            .find(query, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        rows_in = await cursor.to_list(length=limit)
        header = [
            "assignment_id", "tenant_id", "truck_id",
            "driver_id", "driver_name",
            "project_number", "project_name", "material",
            "source_location", "destination",
            "current_state", "current_wait_reason",
            "assigned_at", "last_transition_at", "completed_at",
            "cancelled_at", "cancel_reason",
            "transitions_count", "non_standard_count",
        ]
        out_rows: List[List[Any]] = []
        for a in rows_in:
            hist = a.get("state_history") or []
            non_std = sum(1 for h in hist if not h.get("standard", True))
            out_rows.append([
                a.get("id"), a.get("tenant_id"), a.get("truck_id"),
                a.get("driver_id"), _bounded(a.get("driver_name")),
                a.get("project_number"), _bounded(a.get("project_name")),
                _bounded(a.get("material")),
                _bounded(a.get("source_location")),
                _bounded(a.get("destination")),
                a.get("current_state"), a.get("current_wait_reason") or "",
                a.get("assigned_at"), a.get("last_transition_at"),
                a.get("completed_at") or "", a.get("cancelled_at") or "",
                _bounded(a.get("cancel_reason") or ""),
                len(hist), non_std,
            ])
        return _csv_response(
            out_rows, header,
            f"dispatch_assignments_{tenant_id}_{_now_stamp()}.csv",
        )

    # ─────────────────────────────────────────────────────────────────
    # state-events.csv
    # ─────────────────────────────────────────────────────────────────
    @router.get("/state-events.csv")
    async def export_state_events(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        since: Optional[str] = Query(None),
        until: Optional[str] = Query(None),
        non_standard_only: bool = Query(False),
        assignment_id: Optional[str] = Query(None),
        limit: int = Query(MAX_ROWS, ge=1, le=MAX_ROWS),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        query.update(_date_query(since, until, "at"))
        if non_standard_only:
            query["standard"] = False
        if assignment_id:
            query["assignment_id"] = assignment_id
        cursor = (
            db.dispatch_state_events
            .find(query, {"_id": 0})
            .sort("at", -1)
            .limit(limit)
        )
        rows_in = await cursor.to_list(length=limit)
        header = [
            "event_id", "tenant_id", "assignment_id",
            "truck_id", "driver_id", "driver_name", "project_number",
            "from_state", "to_state", "standard", "warning_tag",
            "at", "by_name", "by_role",
            "wait_reason", "note", "correction_reason",
        ]
        out_rows: List[List[Any]] = [
            [
                e.get("id"), e.get("tenant_id"), e.get("assignment_id"),
                e.get("truck_id"), e.get("driver_id"), _bounded(e.get("driver_name")),
                e.get("project_number"),
                e.get("from_state") or "", e.get("to_state") or "",
                "true" if e.get("standard") else "false",
                e.get("warning_tag") or "",
                e.get("at"), _bounded(e.get("by_name") or ""), e.get("by_role") or "",
                e.get("wait_reason") or "",
                _bounded(e.get("note") or ""),
                _bounded(e.get("correction_reason") or ""),
            ]
            for e in rows_in
        ]
        return _csv_response(
            out_rows, header,
            f"dispatch_state_events_{tenant_id}_{_now_stamp()}.csv",
        )

    # ─────────────────────────────────────────────────────────────────
    # haul-cycles.csv
    # ─────────────────────────────────────────────────────────────────
    @router.get("/haul-cycles.csv")
    async def export_haul_cycles(
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        since: Optional[str] = Query(None),
        until: Optional[str] = Query(None),
        truck_id: Optional[str] = Query(None),
        project_number: Optional[str] = Query(None),
        limit: int = Query(MAX_ROWS, ge=1, le=MAX_ROWS),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        query.update(_date_query(since, until, "completed_at"))
        if truck_id:
            query["truck_id"] = truck_id
        if project_number:
            query["project_number"] = project_number
        cursor = (
            db.haul_cycles
            .find(query, {"_id": 0})
            .sort("completed_at", -1)
            .limit(limit)
        )
        rows_in = await cursor.to_list(length=limit)
        header = [
            "cycle_id", "tenant_id", "assignment_id",
            "truck_id", "driver_id", "driver_name",
            "project_number", "project_name", "material",
            "source_location", "destination",
            "started_at", "completed_at",
            "total_seconds", "wait_seconds", "operating_seconds",
            "transitions", "non_standard_transitions",
        ]
        out_rows: List[List[Any]] = [
            [
                c.get("id"), c.get("tenant_id"), c.get("assignment_id"),
                c.get("truck_id"), c.get("driver_id"), _bounded(c.get("driver_name")),
                c.get("project_number"), _bounded(c.get("project_name")),
                _bounded(c.get("material")),
                _bounded(c.get("source_location")),
                _bounded(c.get("destination")),
                c.get("started_at"), c.get("completed_at"),
                c.get("total_seconds"),
                c.get("wait_seconds"),
                c.get("operating_seconds"),
                c.get("transitions"),
                c.get("non_standard_transitions"),
            ]
            for c in rows_in
        ]
        return _csv_response(
            out_rows, header,
            f"dispatch_haul_cycles_{tenant_id}_{_now_stamp()}.csv",
        )

    return router


__all__ = ["build_dispatch_exports_router"]
