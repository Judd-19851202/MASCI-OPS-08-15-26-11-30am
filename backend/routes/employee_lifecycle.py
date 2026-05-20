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

# iter285 · employment separation taxonomy.
ALLOWED_SEPARATION_TYPES = {"voluntary", "involuntary", "layoff"}

# iter285 · lifecycle date field names · used by write-once enforcement
# and status-transition auto-population helpers below.
_LIFECYCLE_DATE_FIELDS = (
    "original_hire_date",
    "last_day_worked",
    "termination_date",
    "leave_start_date",
    "expected_return_date",
)
# Once `original_hire_date` is set to a non-empty string on an employee
# document, no subsequent PATCH may change it. Audit (iter284 · §2.2 +
# §6 risk #1) flagged unprotected hire-date overwrite as the highest
# structural risk in the employee schema.
_WRITE_ONCE_FIELDS = ("original_hire_date",)


def _is_date_string(v: Any) -> bool:
    """Light validation: ISO-style YYYY-MM-DD prefix.

    Mongo stores dates as ISO strings in this collection per existing
    convention. We don't enforce calendar correctness here — that's
    the frontend date picker's job; this just keeps obviously bad
    values out.
    """
    if v is None or v == "":
        return True  # empty / null is fine; caller decides if required
    if not isinstance(v, str):
        return False
    if len(v) < 10:
        return False
    head = v[:10]
    return head[4] == "-" and head[7] == "-" and head.replace("-", "").isdigit()


def _tenure_days(employee: Dict[str, Any]) -> Optional[int]:
    """Derive tenure in days from `original_hire_date` (preferred) or
    legacy `hire_date`. Returns None when neither is set.

    Strictly read-time — NEVER stored. Single source of truth is the
    authoritative date field itself.
    """
    from datetime import datetime, date
    raw = (employee.get("original_hire_date") or employee.get("hire_date") or "").strip()
    if not raw or len(raw) < 10:
        return None
    try:
        hire = datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    # If terminated/resigned/retired, freeze tenure at termination date
    # when available, otherwise last_day_worked, otherwise today.
    end_raw = (
        employee.get("termination_date")
        or employee.get("last_day_worked")
        or ""
    ).strip()
    if end_raw and employee.get("lifecycle_status") in _OFFBOARDING_STATUSES:
        try:
            end = datetime.strptime(end_raw[:10], "%Y-%m-%d").date()
            return max(0, (end - hire).days)
        except ValueError:
            pass
    today = date.today()
    return max(0, (today - hire).days)


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

    # iter285 · lifecycle date structure
    original_hire_date: Optional[str] = None
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError(f"lifecycle_status must be one of {sorted(ALLOWED_LIFECYCLE_STATUSES)}")
        return v

    @field_validator(
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
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

    # iter285 · lifecycle date structure (mirror of create-time fields)
    original_hire_date: Optional[str] = None
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    @field_validator(
        "original_hire_date", "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
        return v


class StatusChange(BaseModel):
    lifecycle_status: str
    reason: Optional[str] = Field(default=None, max_length=2000)

    # iter285 · dates that may accompany a status transition. The route
    # also accepts these via PATCH, but allowing them on the dedicated
    # status-change endpoint keeps the lifecycle event atomic.
    last_day_worked: Optional[str] = None
    termination_date: Optional[str] = None
    leave_start_date: Optional[str] = None
    expected_return_date: Optional[str] = None
    separation_type: Optional[str] = None

    @field_validator("lifecycle_status")
    @classmethod
    def _v_status(cls, v: str) -> str:
        if v not in ALLOWED_LIFECYCLE_STATUSES:
            raise ValueError("invalid status")
        return v

    @field_validator(
        "last_day_worked", "termination_date",
        "leave_start_date", "expected_return_date",
    )
    @classmethod
    def _v_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if not _is_date_string(v):
            raise ValueError("date must be YYYY-MM-DD")
        return v

    @field_validator("separation_type")
    @classmethod
    def _v_sep(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        if v not in ALLOWED_SEPARATION_TYPES:
            raise ValueError(f"separation_type must be one of {sorted(ALLOWED_SEPARATION_TYPES)}")
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
        items = []
        async for d in cur:
            d = _strip_id(d) or {}
            d["tenure_days"] = _tenure_days(d)
            items.append(d)
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
            # iter285 · lifecycle date structure
            "original_hire_date": (body.original_hire_date or None),
            "last_day_worked": (body.last_day_worked or None),
            "termination_date": (body.termination_date or None),
            "leave_start_date": (body.leave_start_date or None),
            "expected_return_date": (body.expected_return_date or None),
            "separation_type": (body.separation_type or None),
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
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return out

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
        incoming = body.model_dump(exclude_none=True)

        # iter285 · write-once enforcement for original_hire_date (and
        # any future write-once fields enumerated in _WRITE_ONCE_FIELDS).
        # Audit iter284 §2.2 / §6 risk #1: hire-date overwrite was the
        # highest structural risk in the schema. Once persisted as a
        # non-empty value, the field cannot be re-set to a different
        # value via PATCH. Re-sending the same value is a no-op (so
        # idempotent UI re-saves don't error).
        for fname in _WRITE_ONCE_FIELDS:
            cur = (existing.get(fname) or "").strip() if isinstance(existing.get(fname), str) else existing.get(fname)
            incoming_v = (incoming.get(fname) or "").strip() if isinstance(incoming.get(fname), str) else incoming.get(fname)
            if cur and incoming_v and cur != incoming_v:
                raise HTTPException(
                    409,
                    f"{fname} is write-once and is already set to {cur!r}; "
                    f"refusing to overwrite with {incoming_v!r}. Rehire "
                    f"flows are not supported in this surface.",
                )

        update: Dict[str, Any] = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        for k, v in incoming.items():
            update[k] = v
        await db.employees.update_one({"id": employee_id}, {"$set": update})
        doc = await db.employees.find_one(
            {"id": employee_id}, {"_id": 0})
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return out

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

        # iter285 · status transitions that require / auto-populate
        # lifecycle dates. The route accepts these in the request body
        # (preferred) and back-fills sensible defaults from "today"
        # (date-only) when omitted. Separation type is REQUIRED for any
        # offboarding transition so the historical record can be
        # filtered/audited later without parsing free-text reasons.
        from datetime import date
        today_iso = date.today().isoformat()
        date_updates: Dict[str, Any] = {}
        is_offboarding = (
            body.lifecycle_status in _OFFBOARDING_STATUSES
            and prev_status not in _OFFBOARDING_STATUSES
        )
        is_going_on_leave = (
            body.lifecycle_status == "Leave of Absence"
            and prev_status != "Leave of Absence"
        )
        if is_offboarding:
            # Separation type is operationally required to keep
            # downstream reporting honest. Reject the transition
            # if the existing record + the request together don't
            # supply one. (Accept either the request body OR a
            # value already present on the employee.)
            existing_sep = (existing.get("separation_type") or "").strip()
            incoming_sep = (body.separation_type or "").strip()
            if not (existing_sep or incoming_sep):
                raise HTTPException(
                    400,
                    "separation_type is required when transitioning to "
                    f"{body.lifecycle_status} "
                    "(one of: voluntary, involuntary, layoff)",
                )
            if incoming_sep:
                date_updates["separation_type"] = incoming_sep
            # Termination date + last day worked default to today if
            # not provided. Both are stored so reporting can use
            # whichever makes sense; HR can edit either via PATCH
            # after the transition.
            date_updates["termination_date"] = (
                body.termination_date or existing.get("termination_date") or today_iso
            )
            date_updates["last_day_worked"] = (
                body.last_day_worked or existing.get("last_day_worked") or today_iso
            )
        if is_going_on_leave:
            # Leave of Absence without a leave_start_date is the
            # iter284 §6 risk #6 anti-pattern. Default to today;
            # accept an explicit value when provided. Expected
            # return is optional but kept structured when present.
            date_updates["leave_start_date"] = (
                body.leave_start_date or existing.get("leave_start_date") or today_iso
            )
            if body.expected_return_date:
                date_updates["expected_return_date"] = body.expected_return_date

        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "at": now,
            "by": actor.get("name") or actor.get("email") or "hr",
            "from": prev_status,
            "to": body.lifecycle_status,
            "reason": body.reason,
        }
        set_block: Dict[str, Any] = {
            "lifecycle_status": body.lifecycle_status,
            "is_active": _is_active_for_status(body.lifecycle_status),
            "updated_at": now,
        }
        set_block.update(date_updates)
        await db.employees.update_one(
            {"id": employee_id},
            {
                "$set": set_block,
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
        out = _strip_id(doc) or {}
        out["tenure_days"] = _tenure_days(out)
        return {
            "ok": True,
            "employee": out,
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
    "ALLOWED_SEPARATION_TYPES",
]
