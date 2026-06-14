"""
routes/project_team_assignments.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION
Phase 1.

Editable per-project team roster. One row per (project_number, user_id,
assignment_role, active) tuple. Soft-delete via `active=false`. Every
mutation mirrors to the existing `audit_events` collection so the
admin Recent Activity timeline carries roster history alongside other
platform events.

Companion helper exposes a project→roster resolver used by Phase-2
producer rewrites; this phase does not rewrite producers, only
prepares the resolver.

Hard locks honoured: this file adds a new collection and new endpoints.
It does NOT touch `pm_email` / `co_pm_emails` on `jobs_master` — the
existing PM cascade in `pm_admin.py` continues to be the source of
truth for PM/Co-PM email routing. Backfill copies that data into the
roster idempotently for forward use.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── Closed-set role registry ─────────────────────────────────────────
# Internal keys are stable snake_case. UI labels are operator-friendly.
ROLE_REGISTRY: Dict[str, str] = {
    "pm": "Project Manager",
    "co_pm": "Co-PM",
    "assistant_pm": "Assistant PM",
    "superintendent": "Superintendent",
    "foreman": "Foreman",
    "safety_lead": "Safety Lead",
    "project_engineer": "Project Engineer",
    "asset_admin": "Asset Admin",
    "locate_coordinator": "811 Locate Coordinator",
    "dispatcher_contact": "Dispatcher Contact",
    "shop_contact": "Shop Contact",
    "executive_oversight": "Executive Oversight",
    "read_only_stakeholder": "Read-only Stakeholder",
}
ALL_ROLES: Set[str] = set(ROLE_REGISTRY.keys())

# PM / Co-PM are admin-managed only. PM cannot assign / remove these.
ADMIN_ONLY_ROLES: Set[str] = {"pm", "co_pm", "executive_oversight"}
PM_ASSIGNABLE_ROLES: Set[str] = ALL_ROLES - ADMIN_ONLY_ROLES


# ── Pydantic IO models ───────────────────────────────────────────────
class AssignmentIn(BaseModel):
    user_id: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    assignment_role: str
    assignment_scope: str = Field(default="full")  # "full" | "read_only"
    is_primary: bool = False
    is_backup: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


class AssignmentPatch(BaseModel):
    assignment_scope: Optional[str] = None
    is_primary: Optional[bool] = None
    is_backup: Optional[bool] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


# ── Helpers ──────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in row.items() if k != "_id"}
    out["role_label"] = ROLE_REGISTRY.get(out.get("assignment_role"), out.get("assignment_role"))
    return out


def _coerce_actor(actor: Any) -> Dict[str, Any]:
    """`require_admin` returns `True` for admin tokens and a PM doc for
    PM tokens. Coerce both shapes into the dict the route bodies expect.
    `_require_any_portal_token` already returns a dict."""
    if actor is True:
        return {"_actor": "admin", "name": "Admin", "id": "admin"}
    if isinstance(actor, dict):
        # If a PM doc was supplied from require_admin, tag it explicitly
        # so downstream gates know it's a PM (not a generic admin).
        if "_actor" not in actor:
            return {**actor, "_actor": "pm"}
        return actor
    return {"_actor": "unknown"}


def _actor_signature(actor: Dict[str, Any]) -> Dict[str, str]:
    return {
        "actor_user_id": actor.get("id") or actor.get("user_id") or "",
        "actor_role": actor.get("_actor") or "",
        "actor_email": (actor.get("email") or "").lower(),
        "actor_name": actor.get("name") or actor.get("display_name") or "",
    }


async def _project_exists(db, project_number: str) -> bool:
    return bool(await db.jobs_master.find_one(
        {"project_number": project_number, "deleted_at": {"$in": [None, ""]}},
        {"_id": 1},
    ))


async def _is_pm_on_project(db, actor_email: str, project_number: str) -> Tuple[bool, bool]:
    """Return (is_primary_pm, is_co_pm)."""
    if not actor_email:
        return (False, False)
    job = await db.jobs_master.find_one(
        {"project_number": project_number},
        {"_id": 0, "pm_email": 1, "co_pm_emails": 1},
    )
    if not job:
        return (False, False)
    return (
        (job.get("pm_email") or "").lower() == actor_email,
        actor_email in {e.lower() for e in (job.get("co_pm_emails") or [])},
    )


async def _resolve_user(
    db,
    payload: AssignmentIn,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (user_id, employee_id, email, display_name) by resolving
    against `user_directory` (primary) and `employees` (secondary).

    Resolution priority: explicit `user_id` > `email` > `employee_id`.
    """
    user_id = (payload.user_id or "").strip() or None
    employee_id = (payload.employee_id or "").strip() or None
    email = (payload.email or "").strip().lower() or None
    name = (payload.display_name or "").strip() or None

    # Try user_directory by id.
    if user_id:
        row = await db.user_directory.find_one(
            {"id": user_id}, {"_id": 0, "id": 1, "email": 1, "name": 1, "employee_id": 1},
        )
        if row:
            return (
                row["id"],
                row.get("employee_id") or employee_id,
                (row.get("email") or email or "").lower(),
                row.get("name") or name,
            )

    # Try user_directory by email.
    if email:
        row = await db.user_directory.find_one(
            {"email": email}, {"_id": 0, "id": 1, "email": 1, "name": 1, "employee_id": 1},
        )
        if row:
            return (
                row["id"],
                row.get("employee_id") or employee_id,
                row.get("email").lower(),
                row.get("name") or name,
            )

    # Try employees collection (will leave user_id None — caller MUST
    # treat that as an unmatched assignment).
    if employee_id:
        emp = await db.employees.find_one(
            {"id": employee_id},
            {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1},
        )
        if emp:
            disp = " ".join(filter(None, [emp.get("first_name"), emp.get("last_name")])) or name
            return (
                None,
                emp["id"],
                (emp.get("email") or email or "").lower() or None,
                disp,
            )

    # Could not resolve to any identity; return whatever was supplied.
    return (user_id, employee_id, email, name)


async def _audit(
    db,
    *,
    action: str,
    project_number: str,
    assignment_role: str,
    target_user_id: Optional[str],
    target_email: Optional[str],
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
    actor: Dict[str, Any],
    notes: Optional[str] = None,
) -> None:
    """Append one audit row to the existing `audit_events` collection."""
    sig = _actor_signature(actor)
    doc = {
        "id": str(uuid.uuid4()),
        "at": _now_iso(),
        "category": "project_team_roster",
        "action": action,
        "project_number": project_number,
        "assignment_role": assignment_role,
        "target_user_id": target_user_id,
        "target_email": target_email,
        "before": before,
        "after": after,
        "notes": notes,
        **sig,
    }
    try:
        await db.audit_events.insert_one(doc)
    except Exception as exc:
        logger.warning("[team-roster] audit insert failed: %s", exc)


# ── Resolver helpers (used by Phase-2 producer rewrites) ─────────────
async def resolve_team_for_project(
    db, project_number: str, *, active_only: bool = True,
) -> List[Dict[str, Any]]:
    q = {"project_number": project_number}
    if active_only:
        q["active"] = True
    rows: List[Dict[str, Any]] = []
    async for r in db.project_team_assignments.find(q, {"_id": 0}):
        rows.append(_public(r))
    return rows


async def resolve_users_for_project_role(
    db, project_number: str, role: str,
) -> List[str]:
    """Return active user_ids assigned to (project, role). Empty list →
    no one rostered; caller should fall back to role-bucket routing."""
    if role not in ALL_ROLES:
        return []
    out: List[str] = []
    cur = db.project_team_assignments.find(
        {"project_number": project_number, "assignment_role": role, "active": True,
         "user_id": {"$nin": [None, ""]}},
        {"_id": 0, "user_id": 1},
    )
    async for r in cur:
        if r.get("user_id"):
            out.append(r["user_id"])
    return out


# ── Backfill ─────────────────────────────────────────────────────────
async def backfill_pm_and_co_pm(db) -> Dict[str, Any]:
    """Idempotent: for each active job, ensure a PM row exists if
    `pm_email` resolves to a directory user, and a `co_pm` row exists
    per `co_pm_emails`. Re-runs are safe — the unique partial index
    ``(project_number, user_id, assignment_role) where active=true``
    plus the `existing` lookup prevent duplicates.
    """
    now = _now_iso()
    summary: Dict[str, Any] = {
        "jobs_scanned": 0,
        "pm_assignments_created": 0,
        "co_pm_assignments_created": 0,
        "unmatched": [],
        "ran_at": now,
    }
    async for j in db.jobs_master.find(
        {"deleted_at": {"$in": [None, ""]}},
        {"_id": 0, "project_number": 1, "pm_email": 1, "co_pm_emails": 1},
    ):
        summary["jobs_scanned"] += 1
        pn = (j.get("project_number") or "").strip()
        if not pn:
            continue
        # Primary PM
        pm_email = (j.get("pm_email") or "").strip().lower()
        if pm_email:
            ud = await db.user_directory.find_one(
                {"email": pm_email}, {"_id": 0, "id": 1, "email": 1, "name": 1},
            )
            if ud:
                # Idempotency: skip if active row already exists.
                exists = await db.project_team_assignments.find_one({
                    "project_number": pn,
                    "user_id": ud["id"],
                    "assignment_role": "pm",
                    "active": True,
                })
                if not exists:
                    await db.project_team_assignments.insert_one({
                        "id": str(uuid.uuid4()),
                        "project_number": pn,
                        "user_id": ud["id"],
                        "employee_id": None,
                        "email": pm_email,
                        "display_name": ud.get("name") or pm_email,
                        "assignment_role": "pm",
                        "assignment_scope": "full",
                        "is_primary": True,
                        "is_backup": False,
                        "active": True,
                        "start_date": now[:10],
                        "end_date": None,
                        "assigned_by": "system-backfill",
                        "assigned_by_role": "system",
                        "assigned_at": now,
                        "updated_by": None,
                        "updated_at": None,
                        "removed_by": None,
                        "removed_at": None,
                        "remove_reason": None,
                        "source": "backfill_pm_email",
                        "notes": None,
                    })
                    summary["pm_assignments_created"] += 1
            else:
                summary["unmatched"].append({"project_number": pn, "role": "pm", "email": pm_email})
        # Co-PMs
        for ce in (j.get("co_pm_emails") or []):
            ce_norm = (ce or "").strip().lower()
            if not ce_norm:
                continue
            ud = await db.user_directory.find_one(
                {"email": ce_norm}, {"_id": 0, "id": 1, "email": 1, "name": 1},
            )
            if ud:
                exists = await db.project_team_assignments.find_one({
                    "project_number": pn,
                    "user_id": ud["id"],
                    "assignment_role": "co_pm",
                    "active": True,
                })
                if not exists:
                    await db.project_team_assignments.insert_one({
                        "id": str(uuid.uuid4()),
                        "project_number": pn,
                        "user_id": ud["id"],
                        "employee_id": None,
                        "email": ce_norm,
                        "display_name": ud.get("name") or ce_norm,
                        "assignment_role": "co_pm",
                        "assignment_scope": "full",
                        "is_primary": False,
                        "is_backup": False,
                        "active": True,
                        "start_date": now[:10],
                        "end_date": None,
                        "assigned_by": "system-backfill",
                        "assigned_by_role": "system",
                        "assigned_at": now,
                        "updated_by": None,
                        "updated_at": None,
                        "removed_by": None,
                        "removed_at": None,
                        "remove_reason": None,
                        "source": "backfill_co_pm_emails",
                        "notes": None,
                    })
                    summary["co_pm_assignments_created"] += 1
            else:
                summary["unmatched"].append({"project_number": pn, "role": "co_pm", "email": ce_norm})
    return summary


# ── Permission gates ─────────────────────────────────────────────────
async def _can_manage_project_team(
    db, actor: Dict[str, Any], project_number: str, target_role: str,
) -> Tuple[bool, str]:
    """Return (allowed, reason). Permission rules:
      - admin actor → always allowed.
      - PM (primary on this project) → may assign PM_ASSIGNABLE_ROLES.
      - Co-PM (in co_pm_emails) → may assign PM_ASSIGNABLE_ROLES.
      - other actors → forbidden.
    """
    actor_kind = (actor.get("_actor") or "").lower()
    if actor_kind == "admin":
        return (True, "admin")
    if target_role not in ALL_ROLES:
        return (False, "unknown role")
    if target_role in ADMIN_ONLY_ROLES:
        return (False, f"role {target_role!r} is admin-only")
    if actor_kind == "pm":
        email = (actor.get("email") or "").lower()
        is_primary, is_co = await _is_pm_on_project(db, email, project_number)
        if is_primary or is_co:
            return (True, "pm or co-pm on project")
        return (False, "PM not assigned to this project")
    return (False, f"actor kind {actor_kind!r} cannot manage team")


# ── Router registration ─────────────────────────────────────────────
def register_project_team_assignments(
    app, db, require_admin_dep: Callable, require_any_portal_token: Callable,
) -> APIRouter:
    router = APIRouter(tags=["project-team-roster"])

    @router.get("/api/team-roster/role-registry")
    async def role_registry(
        actor=Depends(require_any_portal_token),  # noqa: ARG001
    ):
        return {
            "roles": [
                {"key": k, "label": v,
                 "admin_only": k in ADMIN_ONLY_ROLES,
                 "pm_assignable": k in PM_ASSIGNABLE_ROLES}
                for k, v in ROLE_REGISTRY.items()
            ]
        }

    @router.get("/api/admin/jobs/{project_number}/team")
    async def admin_list_team(
        project_number: str,
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        actor = _coerce_actor(actor)
        if not await _project_exists(db, project_number):
            raise HTTPException(404, "project not found")
        items = await resolve_team_for_project(db, project_number, active_only=False)
        return {"project_number": project_number, "items": items, "count": len(items)}

    @router.get("/api/admin/jobs/{project_number}/team/audit")
    async def admin_team_audit(
        project_number: str,
        limit: int = Query(default=100, ge=1, le=500),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        actor = _coerce_actor(actor)
        rows: List[Dict[str, Any]] = []
        cur = db.audit_events.find(
            {"category": "project_team_roster", "project_number": project_number},
            {"_id": 0},
        ).sort("at", -1).limit(limit)
        async for r in cur:
            rows.append(r)
        return {"items": rows, "count": len(rows)}

    @router.post("/api/admin/jobs/{project_number}/team")
    async def admin_add_team_member(
        project_number: str,
        payload: AssignmentIn = Body(...),
        actor=Depends(require_admin_dep),
    ):
        actor = _coerce_actor(actor)
        if not await _project_exists(db, project_number):
            raise HTTPException(404, "project not found")
        if payload.assignment_role not in ALL_ROLES:
            raise HTTPException(400, f"unknown role: {payload.assignment_role}")
        user_id, employee_id, email, name = await _resolve_user(db, payload)
        if not (user_id or email or employee_id):
            raise HTTPException(400, "must supply user_id, email, or employee_id")
        # Prevent duplicate active rows for the same (project,user,role).
        if user_id:
            dup = await db.project_team_assignments.find_one({
                "project_number": project_number,
                "user_id": user_id,
                "assignment_role": payload.assignment_role,
                "active": True,
            })
            if dup:
                raise HTTPException(409, "active assignment already exists for this user+role on this project")
        now = _now_iso()
        row = {
            "id": str(uuid.uuid4()),
            "project_number": project_number,
            "user_id": user_id,
            "employee_id": employee_id,
            "email": email,
            "display_name": name,
            "assignment_role": payload.assignment_role,
            "assignment_scope": payload.assignment_scope or "full",
            "is_primary": bool(payload.is_primary),
            "is_backup": bool(payload.is_backup),
            "active": True,
            "start_date": payload.start_date or now[:10],
            "end_date": payload.end_date,
            "assigned_by": (actor.get("id") or actor.get("name") or "admin"),
            "assigned_by_role": actor.get("_actor") or "admin",
            "assigned_at": now,
            "updated_by": None,
            "updated_at": None,
            "removed_by": None,
            "removed_at": None,
            "remove_reason": None,
            "source": "admin_ui",
            "notes": payload.notes,
        }
        await db.project_team_assignments.insert_one(row)
        await _audit(
            db, action="assign", project_number=project_number,
            assignment_role=payload.assignment_role, target_user_id=user_id,
            target_email=email, before=None, after=_public(row), actor=actor,
            notes=payload.notes,
        )
        return {"ok": True, "assignment": _public(row),
                "user_link_warning": user_id is None}

    @router.patch("/api/admin/jobs/{project_number}/team/{assignment_id}")
    async def admin_update_team_member(
        project_number: str,
        assignment_id: str,
        patch: AssignmentPatch = Body(...),
        actor=Depends(require_admin_dep),
    ):
        actor = _coerce_actor(actor)
        existing = await db.project_team_assignments.find_one(
            {"id": assignment_id, "project_number": project_number}, {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "assignment not found")
        updates: Dict[str, Any] = {"updated_at": _now_iso(),
                                   "updated_by": actor.get("id") or "admin"}
        for field in ("assignment_scope", "is_primary", "is_backup",
                      "end_date", "notes"):
            v = getattr(patch, field, None)
            if v is not None:
                updates[field] = v
        await db.project_team_assignments.update_one(
            {"id": assignment_id}, {"$set": updates},
        )
        after = await db.project_team_assignments.find_one(
            {"id": assignment_id}, {"_id": 0},
        )
        await _audit(
            db, action="update", project_number=project_number,
            assignment_role=existing["assignment_role"],
            target_user_id=existing.get("user_id"),
            target_email=existing.get("email"),
            before=_public(existing), after=_public(after), actor=actor,
        )
        return {"ok": True, "assignment": _public(after)}

    @router.delete("/api/admin/jobs/{project_number}/team/{assignment_id}")
    async def admin_remove_team_member(
        project_number: str,
        assignment_id: str,
        reason: Optional[str] = Query(default=None),
        actor=Depends(require_admin_dep),
    ):
        actor = _coerce_actor(actor)
        existing = await db.project_team_assignments.find_one(
            {"id": assignment_id, "project_number": project_number,
             "active": True}, {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "active assignment not found")
        now = _now_iso()
        await db.project_team_assignments.update_one(
            {"id": assignment_id},
            {"$set": {
                "active": False,
                "removed_by": actor.get("id") or "admin",
                "removed_at": now,
                "remove_reason": reason,
                "end_date": (existing.get("end_date") or now[:10]),
            }},
        )
        after = await db.project_team_assignments.find_one(
            {"id": assignment_id}, {"_id": 0},
        )
        await _audit(
            db, action="remove", project_number=project_number,
            assignment_role=existing["assignment_role"],
            target_user_id=existing.get("user_id"),
            target_email=existing.get("email"),
            before=_public(existing), after=_public(after), actor=actor,
            notes=reason,
        )
        return {"ok": True}

    @router.post("/api/admin/team-roster/backfill")
    async def admin_backfill(
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await backfill_pm_and_co_pm(db)

    # ── PM-scoped read/write ─────────────────────────────────────────
    @router.get("/api/pm/job/{project_number}/team")
    async def pm_list_team(
        project_number: str,
        actor=Depends(require_any_portal_token),
    ):
        allowed, _ = await _can_manage_project_team(
            db, actor, project_number, "foreman",  # use a representative
        )
        # PM read-access also permitted on any project they own (even
        # when the per-row action is admin-only; they get to LOOK).
        if not allowed and (actor.get("_actor") or "") != "admin":
            is_p, is_c = await _is_pm_on_project(
                db, (actor.get("email") or "").lower(), project_number,
            )
            if not (is_p or is_c):
                raise HTTPException(403, "not authorized for this project's roster")
        items = await resolve_team_for_project(db, project_number, active_only=False)
        return {"project_number": project_number, "items": items, "count": len(items)}

    @router.post("/api/pm/job/{project_number}/team")
    async def pm_add_team_member(
        project_number: str,
        payload: AssignmentIn = Body(...),
        actor=Depends(require_any_portal_token),
    ):
        allowed, why = await _can_manage_project_team(
            db, actor, project_number, payload.assignment_role,
        )
        if not allowed:
            raise HTTPException(403, why)
        if not await _project_exists(db, project_number):
            raise HTTPException(404, "project not found")
        user_id, employee_id, email, name = await _resolve_user(db, payload)
        if not (user_id or email or employee_id):
            raise HTTPException(400, "must supply user_id, email, or employee_id")
        if user_id:
            dup = await db.project_team_assignments.find_one({
                "project_number": project_number, "user_id": user_id,
                "assignment_role": payload.assignment_role, "active": True,
            })
            if dup:
                raise HTTPException(409, "active assignment exists")
        now = _now_iso()
        row = {
            "id": str(uuid.uuid4()),
            "project_number": project_number,
            "user_id": user_id, "employee_id": employee_id,
            "email": email, "display_name": name,
            "assignment_role": payload.assignment_role,
            "assignment_scope": payload.assignment_scope or "full",
            "is_primary": bool(payload.is_primary),
            "is_backup": bool(payload.is_backup),
            "active": True,
            "start_date": payload.start_date or now[:10],
            "end_date": payload.end_date,
            "assigned_by": actor.get("id") or actor.get("name") or "pm",
            "assigned_by_role": actor.get("_actor") or "pm",
            "assigned_at": now,
            "updated_by": None, "updated_at": None,
            "removed_by": None, "removed_at": None,
            "remove_reason": None, "source": "pm_ui",
            "notes": payload.notes,
        }
        await db.project_team_assignments.insert_one(row)
        await _audit(
            db, action="assign", project_number=project_number,
            assignment_role=payload.assignment_role, target_user_id=user_id,
            target_email=email, before=None, after=_public(row), actor=actor,
            notes=payload.notes,
        )
        return {"ok": True, "assignment": _public(row),
                "user_link_warning": user_id is None}

    @router.delete("/api/pm/job/{project_number}/team/{assignment_id}")
    async def pm_remove_team_member(
        project_number: str,
        assignment_id: str,
        reason: Optional[str] = Query(default=None),
        actor=Depends(require_any_portal_token),
    ):
        existing = await db.project_team_assignments.find_one(
            {"id": assignment_id, "project_number": project_number,
             "active": True}, {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "active assignment not found")
        allowed, why = await _can_manage_project_team(
            db, actor, project_number, existing["assignment_role"],
        )
        if not allowed:
            raise HTTPException(403, why)
        now = _now_iso()
        await db.project_team_assignments.update_one(
            {"id": assignment_id},
            {"$set": {"active": False, "removed_by": actor.get("id") or "pm",
                      "removed_at": now, "remove_reason": reason,
                      "end_date": (existing.get("end_date") or now[:10])}},
        )
        after = await db.project_team_assignments.find_one(
            {"id": assignment_id}, {"_id": 0},
        )
        await _audit(
            db, action="remove", project_number=project_number,
            assignment_role=existing["assignment_role"],
            target_user_id=existing.get("user_id"),
            target_email=existing.get("email"),
            before=_public(existing), after=_public(after), actor=actor,
            notes=reason,
        )
        return {"ok": True}

    # ── Field Leadership / Asset Admin / Dispatch — read-only ────────
    @router.get("/api/jobs/{project_number}/team")
    async def public_list_team(
        project_number: str,
        actor=Depends(require_any_portal_token),
    ):
        """Read-only roster for the project. Any authenticated portal
        token may read so Foremen, Superintendents, Asset Admins, and
        Dispatchers know who their teammates are on a given job. PII is
        already minimal (name + email + role); private HR records are
        not surfaced anywhere on this row."""
        if not await _project_exists(db, project_number):
            raise HTTPException(404, "project not found")
        items = await resolve_team_for_project(db, project_number, active_only=True)
        return {"project_number": project_number, "items": items,
                "count": len(items)}

    @router.get("/api/users/me/projects")
    async def my_rostered_projects(
        actor=Depends(require_any_portal_token),
    ):
        """Reverse lookup — every project the actor is rostered on
        (active rows only). Used by Field Leadership portal to show
        "My Jobs" without exposing other crews' projects."""
        uid = actor.get("id") or actor.get("user_id")
        email = (actor.get("email") or "").lower()
        q: Dict[str, Any] = {"active": True, "$or": []}
        if uid:
            q["$or"].append({"user_id": uid})
        if email:
            q["$or"].append({"email": email})
        if not q["$or"]:
            return {"items": [], "count": 0}
        items: List[Dict[str, Any]] = []
        async for r in db.project_team_assignments.find(q, {"_id": 0}):
            items.append(_public(r))
        return {"items": items, "count": len(items)}

    app.include_router(router)
    return router


__all__ = [
    "register_project_team_assignments",
    "resolve_team_for_project",
    "resolve_users_for_project_role",
    "backfill_pm_and_co_pm",
    "ROLE_REGISTRY",
    "ALL_ROLES",
    "ADMIN_ONLY_ROLES",
    "PM_ASSIGNABLE_ROLES",
]
