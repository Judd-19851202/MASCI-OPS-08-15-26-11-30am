"""
routes/pm_routes.py · iter377 · Phase 4D · PM Portal read-only routes.

EXTRACTED FROM server.py L2423-L2612 (≈190 lines).

Scope:
  • /pm/check                   — token validity probe.
  • /pm/crew/training-records   — PM scoped training records (180-day crew).
  • /pm/crew/ppe                — PM scoped PPE issuance.
  • /pm/crew/capas              — PM scoped CAPA visibility (read-only).
  • /pm/crew/summary            — PM crew compliance roll-up.
  • /pm/me                      — currently signed-in PM record.

Why these 6 only:
  Zero state mutation. Zero lockout coupling. Zero directory-fallback
  logic. All consume the existing `require_admin` / `require_admin_async`
  dependencies that were already factored. Login/forgot/reset/change/logout
  remain in server.py for a future iteration — they have IP-lockout,
  directory-fallback, and session-activity coupling that need to move
  together when extracted.

Behavior contract (locked by tests/test_iter377_pm_routes_extraction.py):
  Identical request/response shape to the original handlers in server.py.
  No auth drift. No visibility drift. No route renaming.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from pm_auth import public_pm_view


async def _pm_crew_employee_names(
    db, actor: Any, days: int = 180,
) -> Optional[List[str]]:
    """Return the set of employee NAMES on PM's assigned projects'
    daily reports within the last `days`. For admin/legacy callers
    (actor is True), return None to signal "no scope restriction".

    IDENTICAL behavior to server.py:_pm_crew_employee_names (iter353e).
    """
    # Admin or legacy PM bypass → no scope restriction
    if actor is True or not isinstance(actor, dict):
        return None
    pm_email = (actor.get("email") or "").lower()
    if not pm_email:
        return []
    proj_names: List[str] = []
    async for p in db.projects.find(
        {"$or": [
            {"project_manager_email": {"$regex": f"^{re.escape(pm_email)}$", "$options": "i"}},
            {"project_managers": {"$regex": f"^{re.escape(pm_email)}$", "$options": "i"}},
        ]},
        {"_id": 0, "name": 1, "project_name": 1},
    ):
        proj_names.append(p.get("name") or p.get("project_name") or "")
    proj_names = [p for p in proj_names if p]
    if not proj_names:
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()[:10]
    names: set[str] = set()
    async for r in db.daily_reports.find(
        {"project_name": {"$in": proj_names},
         "report_date": {"$gte": cutoff}},
        {"_id": 0, "crew_members": 1, "employees": 1, "personnel": 1},
    ).limit(2000):
        for fld in ("crew_members", "employees", "personnel"):
            v = r.get(fld) or []
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, str):
                        names.add(entry.strip())
                    elif isinstance(entry, dict):
                        nm = (entry.get("name") or entry.get("employee_name") or "").strip()
                        if nm:
                            names.add(nm)
    return sorted(names)


def build_pm_router(
    db,
    require_admin_dep: Callable,
    require_admin_async_dep: Callable,
) -> APIRouter:
    """Build the PM read-only routes router.

    Args:
      db: motor database handle.
      require_admin_dep: server.py `require_admin` dependency.
      require_admin_async_dep: server.py `require_admin_async` dependency.
    """
    router = APIRouter(prefix="/api", tags=["pm"])

    @router.get("/pm/check")
    async def pm_check(_: bool = Depends(require_admin_dep)):
        """Verify a stored PM (or Admin) token is still valid."""
        return {"ok": True}

    @router.get("/pm/crew/training-records")
    async def pm_crew_training_records(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped training records for crew on PM's projects."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"$or": [{"employee_name": {"$in": names}},
                         {"employee_email": {"$in": names}}]}
        items = []
        async for r in db.safety_training_records.find(
            q,
            {"_id": 0, "id": 1, "employee_id": 1, "employee_name": 1,
             "training_name": 1, "certification_type": 1,
             "completed_date": 1, "expiration_date": 1, "notes": 1,
             "created_by_role": 1},
        ).sort("completed_date", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/ppe")
    async def pm_crew_ppe(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped PPE issuance records for crew."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"employee_name": {"$in": names}}
        items = []
        async for r in db.safety_equipment_issuances.find(
            q,
            {"_id": 0, "id": 1, "employee_name": 1, "equipment_type": 1,
             "issued_date": 1, "size": 1, "condition": 1},
        ).sort("issued_date", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/capas")
    async def pm_crew_capas(
        actor=Depends(require_admin_async_dep),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """iter353e · PM scoped CAPA visibility for incidents involving
        crew. Read-only — PM does NOT have CAPA closeout authority."""
        names = await _pm_crew_employee_names(db, actor)
        q: Dict[str, Any] = {}
        if names is not None:
            if not names:
                return {"ok": True, "items": [], "count": 0,
                        "scope": "pm_crew_180d", "crew_size": 0}
            q = {"$or": [{"linked_employee_name": {"$in": names}},
                         {"employee_name": {"$in": names}}]}
        items = []
        async for r in db.corrective_actions.find(
            q,
            {"_id": 0},
        ).sort("created_at", -1).limit(limit):
            items.append(r)
        return {"ok": True, "items": items, "count": len(items),
                "scope": "pm_crew_180d" if names is not None else "admin_all",
                "crew_size": len(names) if names is not None else None}

    @router.get("/pm/crew/summary")
    async def pm_crew_summary(actor=Depends(require_admin_async_dep)):
        """iter353e · PM crew compliance roll-up: crew size, expiring
        training in 30d, expired training, PPE missing, open CAPAs."""
        names = await _pm_crew_employee_names(db, actor)
        if names is None:
            return {"ok": True, "scope": "admin_all", "crew_size": None,
                    "expiring_30d": 0, "expired": 0, "open_capas": 0,
                    "ppe_records": 0}
        today = datetime.now(timezone.utc).isoformat()[:10]
        cutoff_30d = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        if not names:
            return {"ok": True, "scope": "pm_crew_180d", "crew_size": 0,
                    "expiring_30d": 0, "expired": 0, "open_capas": 0,
                    "ppe_records": 0}
        expiring = await db.safety_training_records.count_documents({
            "$or": [{"employee_name": {"$in": names}}],
            "expiration_date": {"$gte": today, "$lte": cutoff_30d},
        })
        expired = await db.safety_training_records.count_documents({
            "$or": [{"employee_name": {"$in": names}}],
            "expiration_date": {"$gt": "", "$lt": today},
        })
        open_capas = await db.corrective_actions.count_documents({
            "$or": [{"linked_employee_name": {"$in": names}},
                    {"employee_name": {"$in": names}}],
            "status": {"$nin": ["closed", "completed", "verified"]},
        })
        ppe_records = await db.safety_equipment_issuances.count_documents({
            "employee_name": {"$in": names},
        })
        return {"ok": True, "scope": "pm_crew_180d", "crew_size": len(names),
                "expiring_30d": expiring, "expired": expired,
                "open_capas": open_capas, "ppe_records": ppe_records}

    @router.get("/pm/me")
    async def pm_me(actor=Depends(require_admin_async_dep)):
        """Return the currently signed-in PM's record (sans password_hash).
        Returns ``{is_admin: true, pm: null}`` when an Admin token is being
        used or when the legacy shared-PM bypass is active."""
        if actor is True:
            return {"is_admin_or_legacy": True, "pm": None}
        return {"is_admin_or_legacy": False, "pm": public_pm_view(actor)}

    return router


__all__ = ["build_pm_router"]
