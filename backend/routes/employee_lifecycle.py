"""
routes/employee_lifecycle.py — Iter152 (Phase 2.5) · Phase C.

EMPLOYEE LIFECYCLE MANAGEMENT.

Uses existing db.employees as the single source of truth. Does NOT
create a duplicate employee collection.

Adds the `lifecycle_status` field on the existing employee documents:
  Pending Hire · Active · Inactive · Suspended · Terminated · Resigned
  · Retired · Seasonal · Leave of Absence

Active dropdown behavior:
  * Existing `is_active` boolean is kept in sync so legacy
    `/api/employees` dropdowns continue to filter Inactive folks
    out by default.
  * New `?show_inactive=true` query param exposes the full roster.

Offboarding Summary (read-only):
  Aggregates outstanding accountability for an employee:
    * Open tasks (Phase A — db.tasks)
    * Document expirations (Phase B — db.document_expirations)
    * Equipment issuances if tracked (best-effort via db.equipment)

Auto-Offboarding Playbook:
  When status transitions from {Active, Pending Hire, Seasonal, Leave of Absence}
  → {Terminated, Resigned, Retired}, the platform fan-outs a canned
  task checklist via task_service.create() (Phase A). HR can review +
  close those tasks; the platform does NOT auto-fire any operational
  changes (no auto-revoke, no auto-equipment-transfer).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

ALLOWED_LIFECYCLE_STATUSES = {
    "Pending Hire", "Active", "Inactive", "Suspended",
    "Terminated", "Resigned", "Retired", "Seasonal",
    "Leave of Absence",
}

# Statuses that count as "actively employed" for dropdown filtering.
_ACTIVE_STATUSES = {"Active", "Pending Hire", "Seasonal", "Leave of Absence"}

# Statuses that trigger the offboarding playbook.
_OFFBOARDING_STATUSES = {"Terminated", "Resigned", "Retired"}


# ──────────────────────────────────────────────────────────────────
# Canned offboarding task playbook
# ──────────────────────────────────────────────────────────────────
# Each row: (assignee_role, priority, title, description)
_OFFBOARDING_PLAYBOOK: List[Dict[str, str]] = [
    {
        "role": "hr",
        "priority": "High",
        "title": "Finalize last paycheck + benefits closeout",
        "desc": "Verify last timesheet hours, accrued PTO payout, and benefits / COBRA notice.",
    },
    {
        "role": "hr",
        "priority": "High",
        "title": "Collect company-issued documents and badges",
        "desc": "Pick up MASCI ID, site badges, OSHA wallet card, and any signed acknowledgments.",
    },
    {
        "role": "shop",
        "priority": "High",
        "title": "Recover company equipment / tools / PPE",
        "desc": "Confirm any small tools, fall protection, hard hats, PPE, fuel cards, and vehicle if applicable are returned.",
    },
    {
        "role": "shop",
        "priority": "Medium",
        "title": "Verify equipment hand-off for any active assignments",
        "desc": "Reassign or stage any equipment that was checked out to this employee.",
    },
    {
        "role": "admin",
        "priority": "High",
        "title": "Disable directory login + portal accounts",
        "desc": "Revoke admin/portal access if any directory session exists, and rotate shared credentials this person used.",
    },
    {
        "role": "admin",
        "priority": "Medium",
        "title": "Disable Motive driver profile (if applicable)",
        "desc": "Mark Motive driver Inactive so they no longer count toward fleet quotas.",
    },
    {
        "role": "safety",
        "priority": "Medium",
        "title": "Close any open safety items tied to this employee",
        "desc": "Review open incidents, corrective actions, training deficiencies, and re-assign or close.",
    },
    {
        "role": "pm",
        "priority": "Medium",
        "title": "Backfill open project assignments",
        "desc": "Identify active jobs this employee was staffed on and either reassign or note coverage plan.",
    },
]


# ──────────────────────────────────────────────────────────────────
# Pydantic
# ──────────────────────────────────────────────────────────────────
class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    trade: Optional[str] = Field(default="", max_length=80)
    role: Optional[str] = Field(default="", max_length=80)
    crew: Optional[str] = Field(default="", max_length=80)
    employee_id: Optional[str] = Field(default="", max_length=64)
    email: Optional[str] = Field(default="", max_length=160)
    phone: Optional[str] = Field(default="", max_length=40)
    supervisor: Optional[str] = Field(default="", max_length=120)
    department: Optional[str] = Field(default="", max_length=80)
    default_project_number: Optional[str] = Field(default="", max_length=64)
    lifecycle_status: str = Field(default="Active")
    hire_date: Optional[str] = None

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError(f"lifecycle_status must be one of {sorted(ALLOWED_LIFECYCLE_STATUSES)}")
        return v


class EmployeePatch(BaseModel):
    name: Optional[str] = None
    trade: Optional[str] = None
    role: Optional[str] = None
    crew: Optional[str] = None
    employee_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    supervisor: Optional[str] = None
    department: Optional[str] = None
    default_project_number: Optional[str] = None
    hire_date: Optional[str] = None


class StatusChange(BaseModel):
    lifecycle_status: str
    reason: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError("invalid status")
        return v


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def _strip_id(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not d:
        return d
    d.pop("_id", None)
    return d


def _is_active_for_status(status: str) -> bool:
    return status in _ACTIVE_STATUSES


async def _fan_out_offboarding_playbook(
    db, employee: Dict[str, Any], new_status: str, reason: Optional[str],
    actor: Dict[str, Any],
) -> List[str]:
    """Emit one task per playbook row via Phase A task_service.
    Returns the list of created task IDs."""
    from routes.tasks_notifications import task_service  # noqa: PLC0415
    created: List[str] = []
    label = f"Offboarding: {employee.get('name', '(unknown)')}"
    for row in _OFFBOARDING_PLAYBOOK:
        try:
            task_id = await task_service.create(db, {
                "title": f"{label} — {row['title']}",
                "description": (
                    f"Status: {new_status}. "
                    f"{('Reason: ' + reason) if reason else ''}\n\n"
                    f"{row['desc']}"
                ).strip(),
                "source_module": "hr.offboarding",
                "source_record_id": employee.get("id"),
                "linked_employee_id": employee.get("id"),
                "assignee_role": row["role"],
                "priority": row["priority"],
                "created_by": {
                    "role": "hr",
                    "name": actor.get("name") or actor.get("email")
                            or "HR Manager",
                },
            })
            if task_id:
                created.append(task_id)
        except Exception as e:  # pragma: no cover
            logger.warning("offboarding playbook task failed: %s", e)
    # Iter160 · Operational signal — offboarding started.
    try:
        from lib.operational_signals import record_signal  # noqa: PLC0415
        await record_signal(
            db, signal="hr.offboarding_started", module="hr.offboarding",
            dims={"new_status": (new_status or "")[:24],
                  "tasks_created": len(created)},
        )
    except Exception:
        pass
    return created


# ──────────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────────
def build_employee_lifecycle_router(db, require_hr, require_admin,
                                     require_any_portal_token):
    """Builds the HR-employee + offboarding-summary router.

    Authentication: write endpoints accept either HR or Admin tokens
    (via require_hr_or_admin); read endpoints accept any portal token.
    """
    router = APIRouter(tags=["employee-lifecycle"])

    async def require_hr_or_admin(actor: Dict[str, Any] = Depends(require_any_portal_token)) -> Dict[str, Any]:
        role = actor.get("_actor") or actor.get("role") or ""
        if role in ("hr", "admin"):
            return actor
        raise HTTPException(403, "HR or Admin only")

    # ── HR employee CRUD ──────────────────────────────────────────────
    @router.get("/api/hr/employees")
    async def list_employees(
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
        show_inactive: bool = Query(default=False),
        lifecycle_status: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None, max_length=80),
        limit: int = Query(default=500, ge=1, le=2000),
    ) -> Dict[str, Any]:
        clauses: List[Dict[str, Any]] = [{"deleted_at": None}]
        if not show_inactive:
            # Default view = only "actively employed" statuses.
            clauses.append({"$or": [
                {"lifecycle_status": {"$in": list(_ACTIVE_STATUSES)}},
                {"lifecycle_status": {"$exists": False},  # legacy rows
                 "is_active": {"$ne": False}},
            ]})
        if lifecycle_status:
            clauses.append({"lifecycle_status": lifecycle_status})
        if q:
            clauses.append({"$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"employee_id": {"$regex": q, "$options": "i"}},
                {"trade": {"$regex": q, "$options": "i"}},
            ]})
        final = {"$and": clauses}
        cur = db.employees.find(final, {"_id": 0}).sort("name", 1).limit(limit)
        items = [_strip_id(d) async for d in cur]
        return {"items": items, "count": len(items)}

    @router.post("/api/hr/employees")
    async def create_employee(
        body: EmployeeCreate,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        name = body.name.strip()
        existing = await db.employees.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"},
             "deleted_at": None},
            {"_id": 0},
        )
        if existing:
            raise HTTPException(409, f"An employee named '{name}' already exists")
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": str(uuid.uuid4()),
            "name": name,
            "trade": body.trade or "",
            "role": body.role or "",
            "crew": body.crew or "",
            "employee_id": body.employee_id or "",
            "email": body.email or "",
            "phone": body.phone or "",
            "supervisor": body.supervisor or "",
            "department": body.department or "",
            "default_project_number": body.default_project_number or "",
            "hire_date": body.hire_date or None,
            "lifecycle_status": body.lifecycle_status,
            "is_active": _is_active_for_status(body.lifecycle_status),
            "added_via": "hr-portal",
            "created_at": now,
            "updated_at": now,
            "status_history": [{
                "at": now,
                "by": actor.get("name") or actor.get("email") or "hr",
                "to": body.lifecycle_status,
                "reason": None,
            }],
            "deleted_at": None,
        }
        await db.employees.insert_one(doc)
        return _strip_id(doc)

    @router.patch("/api/hr/employees/{employee_id}")
    async def patch_employee(
        employee_id: str,
        body: EmployeePatch,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        existing = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Employee not found")
        update: Dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for k, v in body.model_dump(exclude_none=True).items():
            update[k] = v
        await db.employees.update_one({"id": employee_id}, {"$set": update})
        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        return _strip_id(doc)

    @router.post("/api/hr/employees/{employee_id}/status")
    async def change_status(
        employee_id: str,
        body: StatusChange,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        existing = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Employee not found")
        prev_status = existing.get("lifecycle_status") or (
            "Active" if existing.get("is_active") is not False else "Inactive"
        )
        if prev_status == body.lifecycle_status:
            return {"ok": True, "employee": existing, "tasks_created": 0,
                    "noop": True}
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "at": now,
            "by": actor.get("name") or actor.get("email") or "hr",
            "from": prev_status,
            "to": body.lifecycle_status,
            "reason": body.reason,
        }
        await db.employees.update_one(
            {"id": employee_id},
            {
                "$set": {
                    "lifecycle_status": body.lifecycle_status,
                    "is_active": _is_active_for_status(body.lifecycle_status),
                    "updated_at": now,
                },
                "$push": {"status_history": entry},
            },
        )
        # Auto-offboarding playbook
        tasks_created: List[str] = []
        triggers_playbook = (
            body.lifecycle_status in _OFFBOARDING_STATUSES
            and prev_status not in _OFFBOARDING_STATUSES
        )
        if triggers_playbook:
            employee = await db.employees.find_one(
                {"id": employee_id}, {"_id": 0})
            tasks_created = await _fan_out_offboarding_playbook(
                db, employee or {}, body.lifecycle_status, body.reason, actor)
        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        return {
            "ok": True,
            "employee": _strip_id(doc),
            "tasks_created": len(tasks_created),
            "task_ids": tasks_created,
            "playbook_fired": triggers_playbook,
        }

    @router.get("/api/hr/employees/{employee_id}/offboarding-summary")
    async def offboarding_summary(
        employee_id: str,
        actor: Dict[str, Any] = Depends(require_hr_or_admin),
    ) -> Dict[str, Any]:
        emp = await db.employees.find_one(
            {"id": employee_id, "deleted_at": None}, {"_id": 0})
        if not emp:
            raise HTTPException(404, "Employee not found")
        # Open tasks linked to this employee
        open_tasks_cur = db.tasks.find(
            {
                "linked_employee_id": employee_id,
                "status": {"$in": ["Open", "In Progress",
                                   "Pending Review", "Overdue"]},
            },
            {"_id": 0},
        ).sort("created_at", -1).limit(200)
        open_tasks = [d async for d in open_tasks_cur]

        # Document expirations linked to this employee
        docs_cur = db.document_expirations.find(
            {
                "linked_employee_id": employee_id,
                "status": {"$nin": ["Archived", "Not Applicable"]},
            },
            {"_id": 0},
        ).sort("expiration_date", 1).limit(200)
        # Coerce date-like fields to ISO strings for JSON safety.
        docs = []
        async for d in docs_cur:
            d.pop("_id", None)
            for k in ("issue_date", "expiration_date"):
                v = d.get(k)
                if hasattr(v, "isoformat") and not isinstance(v, str):
                    d[k] = v.isoformat()
            docs.append(d)

        # Equipment issuances — try a few common collection names.
        equipment_links: List[Dict[str, Any]] = []
        try:
            cur = db.equipment.find(
                {"assigned_to_id": employee_id}, {"_id": 0, "id": 1, "name": 1, "unit_number": 1}
            ).limit(50)
            async for d in cur:
                equipment_links.append(d)
        except Exception:
            pass

        # Outstanding corrective actions / incidents counts (Phase A
        # already creates tasks for these, but we surface raw count too).
        try:
            ca_open = await db.corrective_actions.count_documents({
                "employee_master_id": employee_id,
                "status": {"$ne": "Closed"},
            })
        except Exception:
            ca_open = 0

        # Iter153 — Final PO Reconciliation: any open POs tied to this
        # employee. Closes the loop between HR + Field Leadership at
        # exactly the moment someone leaves the company.
        open_pos: List[Dict[str, Any]] = []
        try:
            cur_pos = db.po_requests.find(
                {
                    "$or": [
                        {"requested_by_employee_id": employee_id},
                        {"requested_by_user_id": employee_id},
                    ],
                    "status": {"$in": [
                        "Submitted", "Pending Approval", "Approved",
                        "Pending Receipt", "Clarification Needed",
                        "Overdue Receipt",
                    ]},
                },
                {"_id": 0, "id": 1, "po_number": 1, "vendor": 1,
                 "status": 1, "estimated_amount": 1, "approved_amount": 1,
                 "created_at": 1},
            ).sort("created_at", -1).limit(50)
            async for p in cur_pos:
                p.pop("_id", None)
                open_pos.append(p)
        except Exception:
            pass

        # Status history excerpt
        status_history = emp.get("status_history") or []
        last_status_change = status_history[-1] if status_history else None

        return {
            "employee": _strip_id(emp),
            "open_tasks": open_tasks,
            "open_tasks_count": len(open_tasks),
            "document_expirations": docs,
            "document_expirations_count": len(docs),
            "equipment_issuances": equipment_links,
            "equipment_issuances_count": len(equipment_links),
            "open_corrective_actions": ca_open,
            "open_pos": open_pos,
            "open_pos_count": len(open_pos),
            "last_status_change": last_status_change,
            "is_active": emp.get("is_active", True),
            "lifecycle_status": emp.get("lifecycle_status") or (
                "Active" if emp.get("is_active") is not False else "Inactive"
            ),
        }

    # ── Lifecycle index bootstrap helper ─────────────────────────────
    return router


async def ensure_employee_lifecycle_indexes(db) -> None:
    try:
        await db.employees.create_index("lifecycle_status")
        await db.employees.create_index("supervisor")
        await db.employees.create_index("department")
    except Exception as e:  # pragma: no cover
        logger.warning("employee-lifecycle index bootstrap failed: %s", e)


__all__ = [
    "build_employee_lifecycle_router",
    "ensure_employee_lifecycle_indexes",
    "ALLOWED_LIFECYCLE_STATUSES",
]
