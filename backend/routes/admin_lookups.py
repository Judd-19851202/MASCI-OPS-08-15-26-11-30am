"""
routes/admin_lookups.py · iter381 · Phase 4D · Admin shared lookup services.

EXTRACTED FROM server.py L10539-L10593 (≈55 lines).

Single endpoint:
  • GET /api/admin/find-by-doc-id  — resolves a human-readable doc ID
    (e.g. DR-001234, JHA-2024-99) to the underlying record across 10
    collections and returns the frontend route the admin UI should
    navigate to.

This is the "global search" lookup powering the admin homepage search
bar. Pure read; no mutation; admin-gated.

Why this is a clean iter381 candidate:
  • Single endpoint, ≈55 LOC.
  • Zero coupling to module-level helpers in server.py.
  • Delegates to `doc_ids.find_record_by_doc_id` for the lookup.
  • Route map (collection → frontend path) is the only business logic.

Behavior contract (locked by tests/test_iter381_admin_lookups_extraction.py):
  Identical request/response shape to the original handler. The
  collection → route map MUST be byte-identical — it mirrors the
  frontend routes in /app/frontend/src/App.js.
"""
from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends


# The collection → admin route map. MUST mirror /app/frontend/src/App.js.
# If you add a new doc-ID-bearing collection, add it BOTH here AND in
# the frontend's route table (iter54 caught a real regression where these
# drifted).
_COLLECTION_ROUTES: dict = {
    "field_leadership_records": "/admin/leadership/records/{id}",
    "daily_reports": "/admin/daily/{id}",
    "equipment_inspections": "/admin/equipment/{id}",
    "qaqc_inspections": "/admin/qaqc/{id}",
    "inspections": "/admin/inspections/{id}",
    "meetings": "/admin/meetings/{id}",
    "incidents": "/admin/incidents/{id}",
    "safety_equipment_issuances": "/admin/safety/issuance/{id}",
    "safety_equipment_trainings": "/admin/safety/training/{id}",
    # JHAs use a focus query (not path) — the admin dashboard auto-opens.
    "jhas": "/admin/jha-plans?focus={id}",
}


def _route_for(collection: str, rid: str, doc_id: str) -> str:
    template = _COLLECTION_ROUTES.get(collection)
    if template:
        return template.format(id=rid)
    return f"/admin?doc_id={doc_id}"


def build_admin_lookups_router(db, require_admin_dep: Callable) -> APIRouter:
    """Build the admin shared-lookup router.

    Args:
      db: motor database handle.
      require_admin_dep: server.py `require_admin` dependency.
    """
    router = APIRouter(prefix="/api", tags=["admin-lookups"])

    @router.get("/admin/find-by-doc-id",
                dependencies=[Depends(require_admin_dep)])
    async def admin_find_by_doc_id(doc_id: str):
        """Resolve a human-readable doc ID to the underlying record.

        Returns ``{found, collection, id, doc_id, route}`` where ``route``
        is the frontend path the admin UI should navigate to. Missing IDs
        return ``{found: false}``.
        """
        from doc_ids import find_record_by_doc_id  # noqa: PLC0415
        rec = await find_record_by_doc_id(db, doc_id)
        if not rec:
            return {"found": False}
        coll = rec.get("collection") or ""
        rid = rec.get("id") or ""
        return {
            "found": True,
            "collection": coll,
            "id": rid,
            "doc_id": rec.get("doc_id"),
            "kind": rec.get("kind") or "",
            "project_number": rec.get("project_number"),
            "project_name": rec.get("project_name"),
            "route": _route_for(coll, rid, rec.get("doc_id") or ""),
        }

    return router


__all__ = ["build_admin_lookups_router"]
