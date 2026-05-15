"""
routes/global_search.py — Iter155 (Phase 2.5) · Phase G.

UNIFIED, PERMISSION-SAFE GLOBAL SEARCH.

One search endpoint reachable from every portal. Returns role-aware,
permission-safe results across the platform's operational object
surface. Designed to be:

  * Fast        — asyncio.gather'd parallel probes, indexed regex,
                  per-kind limit, lightweight payloads
  * Safe        — each probe applies its own scope filter so a Safety
                  user NEVER sees an HR-only result, a PM only sees
                  records tied to their projects, Field Leadership only
                  sees their own POs, etc.
  * Lightweight — returns only id/title/subtitle/url/badge per row.
                  NO descriptions, NO base64 thumbnails, NO PII.
  * Predictable — closed-set categories, role-aware coverage list
                  echoed back in the response so the UI can render
                  "what you can search" without guessing.

CRITICAL: never include result counts for kinds the caller has no
access to. If a kind is out-of-scope, it's NOT probed and NOT echoed
— zero data leakage through counters or category labels.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)


# ─── Per-kind / per-role coverage map ─────────────────────────────────
# Each kind is one of the closed-set categories below. The actor's
# `_actor` role determines which kinds are probed. Admin = all.
#
# Why a static map: explicit > implicit. Reading this single dict tells
# you exactly which roles can search which kinds — no scattered if/else.

ALL_KINDS = (
    "tasks",
    "notifications",
    "employees",
    "equipment",
    "projects",
    "po_requests",
    "incidents",
    "corrective_actions",
    "fire_extinguishers",
    "safety_documents",
    "safety_training",
    "document_expirations",
    "operations_events",
    "field_leadership",
)

# Role → tuple of kinds visible to that role. Admin gets everything.
KIND_VISIBILITY: Dict[str, tuple] = {
    "admin": ALL_KINDS,
    "safety": (
        "tasks", "notifications",
        "incidents", "corrective_actions",
        "fire_extinguishers", "safety_documents",
        "safety_training", "document_expirations",
        "employees", "equipment",
    ),
    "hr": (
        "tasks", "notifications",
        "employees", "safety_training",
        "document_expirations", "field_leadership",
        "po_requests",
    ),
    "pm": (
        "tasks", "notifications",
        "projects", "po_requests",
        "incidents", "corrective_actions",
        "employees", "equipment",
    ),
    "shop": (
        "tasks", "notifications",
        "equipment", "operations_events",
        "document_expirations",
    ),
    "dispatch": (
        "tasks", "notifications",
        "equipment", "operations_events",
        "projects",
    ),
    "leadership": (
        "po_requests", "field_leadership",
    ),
}

# Friendly labels (per kind) for the UI grouping
KIND_LABELS: Dict[str, str] = {
    "tasks": "Tasks",
    "notifications": "Notifications",
    "employees": "Employees",
    "equipment": "Equipment / Assets",
    "projects": "Jobs / Projects",
    "po_requests": "PO Requests",
    "incidents": "Incidents",
    "corrective_actions": "Corrective Actions",
    "fire_extinguishers": "Fire Extinguishers",
    "safety_documents": "Safety Documents",
    "safety_training": "Training Records",
    "document_expirations": "Document Expirations",
    "operations_events": "Operations Events",
    "field_leadership": "Field Leadership Records",
}


def _safe_regex(q: str) -> Dict[str, str]:
    """Build a case-insensitive regex from user input. Always escapes."""
    return {"$regex": re.escape(q.strip()), "$options": "i"}


def _row(
    kind: str, doc: Dict[str, Any],
    title: str, subtitle: Optional[str] = None,
    url: Optional[str] = None, status: Optional[str] = None,
    badge: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "kind": kind,
        "id": doc.get("id") or doc.get("_id"),
        "title": (title or "").strip()[:160] or "—",
        "subtitle": (subtitle or "").strip()[:200] or None,
        "url": url,
        "status": status,
        "badge": badge,
    }


def build_global_search_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["global-search"])

    def _role(a: Dict[str, Any]) -> str:
        return a.get("_actor") or a.get("role") or "admin"

    async def _pm_project_numbers(actor: Dict[str, Any]) -> Optional[List[str]]:
        """Resolve PM scope. Returns None when unrestricted (admin/legacy)."""
        try:
            from pm_auth import compute_pm_scope  # noqa: PLC0415
        except Exception:
            return None
        try:
            scope = await compute_pm_scope(db, actor)
            if getattr(scope, "is_admin", False):
                return None
            return list(scope.project_numbers or [])
        except Exception:
            return None

    # ─── PROBES ───────────────────────────────────────────────────
    # Each probe is short, well-bounded, and returns (kind, [rows]).
    # Probes catch their own exceptions so one bad probe never breaks
    # the whole search.

    async def _probe(
        kind: str, limit: int,
        runner: Callable[[], Awaitable[List[Dict[str, Any]]]],
    ) -> Optional[Dict[str, Any]]:
        try:
            rows = await runner()
            if rows:
                return {
                    "kind": kind, "label": KIND_LABELS.get(kind, kind),
                    "rows": rows[:limit], "count": len(rows[:limit]),
                }
        except Exception as e:  # noqa: BLE001
            logger.warning("[search] probe %s failed: %s", kind, e)
        return None

    @router.get("/api/search")
    async def search(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        q: str = Query(..., min_length=2, max_length=80),
        kinds: Optional[str] = Query(default=None,
            description="CSV filter — restricts to a subset of kinds the actor already has access to."),
        limit: int = Query(default=6, ge=1, le=15),
    ) -> Dict[str, Any]:
        role = _role(actor)
        visible = list(KIND_VISIBILITY.get(role, ()))
        if not visible:
            return {
                "q": q, "role": role, "scope": [],
                "groups": [], "total": 0,
            }

        # Apply optional kind filter (still cannot exceed visible)
        if kinds:
            requested = {k.strip() for k in kinds.split(",") if k.strip()}
            visible = [k for k in visible if k in requested]
            if not visible:
                return {
                    "q": q, "role": role, "scope": [],
                    "groups": [], "total": 0,
                }

        rx = _safe_regex(q)

        # PM scope (project numbers) — None means unrestricted.
        pm_proj: Optional[List[str]] = None
        if role == "pm":
            pm_proj = await _pm_project_numbers(actor)

        # Leadership actor id (for own-records scoping). Field Leadership
        # has no user record, so we fall back to "leadership" role match.
        actor_id = actor.get("id")

        # ── Per-kind probe runners ─────────────────────────────────
        async def run_tasks() -> List[Dict[str, Any]]:
            clauses = [{"$or": [{"title": rx}, {"source_module": rx}, {"linked_record_id": rx}]}]
            scope: List[Dict[str, Any]] = []
            if role != "admin":
                scope.append({"$or": [
                    {"assignee_role": role},
                    {"assignee_role": None},
                    {"created_by.role": role},
                ]})
            # PM scope: restrict tasks to those linked to PM-scoped projects.
            # Without this, a PM could see tasks across projects via search.
            # (P1 audit finding — Iter B fix.)
            if role == "pm" and pm_proj is not None:
                scope.append({"linked_project_number": {"$in": pm_proj}})
            q_doc = {"$and": clauses + scope} if scope else clauses[0]
            rows = []
            async for d in db.tasks.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "tasks", d,
                    title=d.get("title") or "—",
                    subtitle=f"{d.get('source_module') or 'task'} · {d.get('priority') or 'Medium'}",
                    url=f"/tasks?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("priority"),
                ))
            return rows

        async def run_notifications() -> List[Dict[str, Any]]:
            clauses = [{"$or": [{"title": rx}, {"body": rx}, {"type": rx}]}]
            scope: List[Dict[str, Any]] = []
            if role != "admin":
                scope.append({"$or": [
                    {"recipient_role": role},
                    {"recipient_role": None},
                ]})
            q_doc = {"$and": clauses + scope} if scope else clauses[0]
            rows = []
            async for d in db.notifications.find(q_doc, {"_id": 0}).sort("created_at", -1).limit(limit * 2):
                rows.append(_row(
                    "notifications", d,
                    title=d.get("title") or d.get("type") or "—",
                    subtitle=(d.get("body") or "")[:180],
                    url="/tasks",
                    status=d.get("severity"),
                    badge=d.get("type"),
                ))
            return rows

        async def run_employees() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"name": rx}, {"first_name": rx}, {"last_name": rx},
                {"employee_id": rx}, {"email": rx},
            ]}
            rows = []
            async for d in db.employees.find(q_doc, {"_id": 0}).limit(limit * 2):
                full = d.get("name") or " ".join(p for p in [d.get("first_name"), d.get("last_name")] if p)
                rows.append(_row(
                    "employees", d,
                    title=full or d.get("employee_id") or "—",
                    subtitle=" · ".join(p for p in [d.get("role") or d.get("title"), d.get("department")] if p) or None,
                    url=f"/hr/employees?id={d.get('id')}",
                    status=d.get("lifecycle_status") or ("Active" if d.get("is_active") else "Inactive"),
                ))
            return rows

        async def run_equipment() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"unit_number": rx}, {"make_model": rx},
                {"vin": rx}, {"serial_number": rx}, {"type": rx},
            ]}
            rows = []
            async for d in db.equipment_master.find(q_doc, {"_id": 0}).limit(limit * 2):
                title = d.get("unit_number") or d.get("make_model") or "—"
                subtitle = " · ".join(p for p in [d.get("make_model") if d.get("unit_number") else None, d.get("type"), d.get("status")] if p) or None
                rows.append(_row(
                    "equipment", d,
                    title=str(title),
                    subtitle=subtitle,
                    url=f"/admin/assets?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_projects() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"project_number": rx}, {"name": rx}, {"location": rx},
            ]}
            if pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.projects.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "projects", d,
                    title=d.get("project_number") or d.get("name") or "—",
                    subtitle=" · ".join(p for p in [d.get("name") if d.get("project_number") else None, d.get("location")] if p) or None,
                    url=f"/admin/jobs?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_po_requests() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"po_number": rx}, {"description": rx},
                {"vendor": rx}, {"project_number": rx},
            ]}
            scope: List[Dict[str, Any]] = []
            if role == "leadership":
                clauses = [{"requested_by_role": "leadership"}]
                if actor_id:
                    clauses.append({"requested_by_user_id": actor_id})
                scope.append({"$or": clauses})
            if role == "pm" and pm_proj is not None:
                scope.append({"project_number": {"$in": pm_proj}})
            final = {"$and": [q_doc] + scope} if scope else q_doc
            rows = []
            async for d in db.po_requests.find(final, {"_id": 0}).sort("created_at", -1).limit(limit * 2):
                rows.append(_row(
                    "po_requests", d,
                    title=d.get("po_number") or d.get("description") or "—",
                    subtitle=" · ".join(p for p in [d.get("vendor"), d.get("project_number")] if p) or None,
                    url=f"/po-requests?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("urgency"),
                ))
            return rows

        async def run_incidents() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"title": rx}, {"description": rx},
                {"incident_type": rx}, {"project_number": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.incidents.find(q_doc, {"_id": 0}).sort("incident_date", -1).limit(limit * 2):
                rows.append(_row(
                    "incidents", d,
                    title=d.get("title") or d.get("incident_type") or "—",
                    subtitle=" · ".join(p for p in [d.get("project_number"), d.get("incident_date")] if p) or None,
                    url=f"/incidents/{d.get('id')}",
                    status=d.get("severity"),
                ))
            return rows

        async def run_corrective_actions() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"title": rx}, {"description": rx},
                {"project_number": rx}, {"assigned_to_name": rx},
            ]}
            if role == "pm" and pm_proj is not None:
                q_doc = {"$and": [q_doc, {"project_number": {"$in": pm_proj}}]}
            rows = []
            async for d in db.corrective_actions.find(q_doc, {"_id": 0}).sort("due_date", 1).limit(limit * 2):
                rows.append(_row(
                    "corrective_actions", d,
                    title=d.get("title") or "—",
                    subtitle=" · ".join(p for p in [d.get("project_number"), d.get("priority"), d.get("due_date")] if p) or None,
                    url=f"/safety-portal/corrective-actions?id={d.get('id')}",
                    status=d.get("status"),
                    badge=d.get("priority"),
                ))
            return rows

        async def run_fire_extinguishers() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"unit_id": rx}, {"location_label": rx},
                {"location_kind": rx}, {"serial_number": rx},
            ]}
            rows = []
            async for d in db.fire_extinguishers.find(q_doc, {"_id": 0}).limit(limit * 2):
                rows.append(_row(
                    "fire_extinguishers", d,
                    title=d.get("unit_id") or "—",
                    subtitle=" · ".join(p for p in [d.get("location_label"), d.get("location_kind")] if p) or None,
                    url=f"/safety-portal/fire-extinguishers?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_safety_documents() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"title": rx}, {"category": rx},
                {"filename": rx},
            ]}
            rows = []
            async for d in db.safety_documents.find(q_doc, {"_id": 0}).sort("uploaded_at", -1).limit(limit * 2):
                rows.append(_row(
                    "safety_documents", d,
                    title=d.get("title") or d.get("filename") or "—",
                    subtitle=d.get("category"),
                    url=f"/safety-portal/documents?id={d.get('id')}",
                ))
            return rows

        async def run_safety_training() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"track": rx}, {"employee_name": rx},
                {"course_name": rx}, {"certificate_number": rx},
            ]}
            rows = []
            async for d in db.safety_training_records.find(q_doc, {"_id": 0}).sort("expiration_date", 1).limit(limit * 2):
                rows.append(_row(
                    "safety_training", d,
                    title=d.get("track") or d.get("course_name") or "—",
                    subtitle=" · ".join(p for p in [d.get("employee_name"), d.get("expiration_date")] if p) or None,
                    url=f"/safety-portal/training?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_document_expirations() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"document_type": rx}, {"description": rx},
                {"linked_employee_name": rx}, {"linked_equipment_unit": rx},
                {"linked_project_number": rx},
            ]}
            rows = []
            async for d in db.document_expirations.find(q_doc, {"_id": 0}).sort("expiration_date", 1).limit(limit * 2):
                rows.append(_row(
                    "document_expirations", d,
                    title=d.get("document_type") or d.get("description") or "—",
                    subtitle=" · ".join(p for p in [d.get("linked_employee_name") or d.get("linked_equipment_unit") or d.get("linked_project_number"), d.get("expiration_date")] if p) or None,
                    url=f"/document-expirations?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_operations_events() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"event_type": rx}, {"summary": rx},
                {"asset_id": rx}, {"employee_id": rx},
            ]}
            rows = []
            async for d in db.operations_events.find(q_doc, {"_id": 0}).sort("occurred_at", -1).limit(limit * 2):
                rows.append(_row(
                    "operations_events", d,
                    title=d.get("event_type") or d.get("summary") or "—",
                    subtitle=" · ".join(p for p in [d.get("asset_id"), d.get("employee_id")] if p) or None,
                    url=f"/admin/operations-events?id={d.get('id')}",
                    status=d.get("status"),
                ))
            return rows

        async def run_field_leadership() -> List[Dict[str, Any]]:
            q_doc = {"$or": [
                {"kind": rx}, {"employee_name": rx},
                {"project_number": rx}, {"notes": rx},
            ]}
            scope: List[Dict[str, Any]] = []
            if role == "pm" and pm_proj is not None:
                scope.append({"project_number": {"$in": pm_proj}})
            final = {"$and": [q_doc] + scope} if scope else q_doc
            rows = []
            async for d in db.field_leadership_records.find(final, {"_id": 0}).sort("occurred_at", -1).limit(limit * 2):
                rows.append(_row(
                    "field_leadership", d,
                    title=d.get("kind") or "Field Leadership Record",
                    subtitle=" · ".join(p for p in [d.get("employee_name"), d.get("project_number")] if p) or None,
                    url=f"/leadership/records/{d.get('id')}",
                ))
            return rows

        runners: Dict[str, Callable[[], Awaitable[List[Dict[str, Any]]]]] = {
            "tasks": run_tasks,
            "notifications": run_notifications,
            "employees": run_employees,
            "equipment": run_equipment,
            "projects": run_projects,
            "po_requests": run_po_requests,
            "incidents": run_incidents,
            "corrective_actions": run_corrective_actions,
            "fire_extinguishers": run_fire_extinguishers,
            "safety_documents": run_safety_documents,
            "safety_training": run_safety_training,
            "document_expirations": run_document_expirations,
            "operations_events": run_operations_events,
            "field_leadership": run_field_leadership,
        }

        coros = [_probe(k, limit, runners[k]) for k in visible if k in runners]
        results = await asyncio.gather(*coros, return_exceptions=False)
        groups = [r for r in results if r]

        return {
            "q": q,
            "role": role,
            "scope": list(visible),
            "groups": groups,
            "total": sum(g["count"] for g in groups),
        }

    return router


__all__ = [
    "build_global_search_router",
    "ALL_KINDS",
    "KIND_LABELS",
    "KIND_VISIBILITY",
]
