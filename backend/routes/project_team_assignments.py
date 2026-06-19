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
import re
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
    "executive_oversight": "Executive Oversight",
    "superintendent": "Superintendent",
    # Track 14.0-PM-STAFFING-RUNTIME-CERT · added per directive.
    "assistant_superintendent": "Assistant Superintendent",
    "foreman": "Foreman",
    "project_engineer": "Project Engineer",
    "project_administrator": "Project Administrator",
    "project_coordinator": "Project Coordinator",
    "safety_rep": "Safety Representative",
    "qaqc_rep": "QA/QC Representative",
    "hr_rep": "HR Representative",
    "dispatch_rep": "Dispatch Representative",
    # Track 14.0-PM-STAFFING-RUNTIME-CERT · relabels + additions.
    "equipment_manager": "Equipment Manager",
    "shop_rep": "Shop Representative",
    "survey_rep": "Survey Representative",
    "accounting_rep": "Accounting Representative",
}
# Legacy keys translated on read; POST/PATCH normalise on write.
LEGACY_ROLE_ALIASES: Dict[str, str] = {
    "safety_lead": "safety_rep",
    "dispatcher_contact": "dispatch_rep",
    "asset_admin": "equipment_manager",
    "shop_contact": "shop_rep",
    # Assistant PM rolled into Project Coordinator (operational
    # duplicate per the new roster).
    "assistant_pm": "project_coordinator",
    # 811 Locate Coordinator + Read-only Stakeholder removed from
    # the new 17-role roster; historic assignments translate to
    # closest operational role.
    "locate_coordinator": "project_coordinator",
    "read_only_stakeholder": "executive_oversight",
}
ALL_ROLES: Set[str] = set(ROLE_REGISTRY.keys())

# PM / Co-PM are admin-managed only. PM cannot assign / remove these.
ADMIN_ONLY_ROLES: Set[str] = {"pm", "co_pm", "executive_oversight"}
PM_ASSIGNABLE_ROLES: Set[str] = ALL_ROLES - ADMIN_ONLY_ROLES


# ── TRACK 14.0-OVERLOADED-CREW-VISIBILITY · Phase 2 ──────────────────
# Single source of truth for the overload threshold. A person is
# considered "overloaded" when they hold this many or more active
# assignments across active (non-deleted) projects within the actor's
# visibility scope. Configurable, regression-locked, no magic numbers
# elsewhere.
OVERLOAD_ACTIVE_PROJECT_THRESHOLD: int = 5


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
    # TRACK 15.39 — P0 · Change Role.
    # When `assignment_role` is supplied AND differs from the current
    # role, the route writes a single `role_change` audit row instead of
    # the legacy REMOVE+ADD pair.
    assignment_role: Optional[str] = None


# TRACK 15.39 — P0 · Remove Reason structured body.
# Replaces the previous `?reason=` query-string with a structured
# category + free-text body so the iPad dialog can submit operator
# intent without window.prompt().
class AssignmentRemove(BaseModel):
    # One of: reassigned, staffing_adjustment, promotion, demotion,
    # project_complete, left_company, other
    reason_category: Optional[str] = None
    reason_text: Optional[str] = None


_REMOVE_REASON_CATEGORIES: Set[str] = {
    "reassigned",
    "staffing_adjustment",
    "promotion",
    "demotion",
    "project_complete",
    "left_company",
    "other",
}


# ── Helpers ──────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_role(role: Optional[str]) -> Optional[str]:
    """Translate legacy role keys to their current canonical key so
    historic assignments keep rendering after a relabel."""
    if not role:
        return role
    return LEGACY_ROLE_ALIASES.get(role, role)


def _public(row: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: v for k, v in row.items() if k != "_id"}
    role = _canonical_role(out.get("assignment_role"))
    if role and role != out.get("assignment_role"):
        out["assignment_role"] = role
    out["role_label"] = ROLE_REGISTRY.get(role, role)
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
    """Return (is_primary_pm, is_co_pm).

    Reconciles the two sources of truth:
      1. Legacy: jobs_master.pm_email / co_pm_emails (single string + list)
      2. Track 14.0 staffing: project_team_assignments with
         assignment_role='pm' or 'co_pm' (active=True).

    A user is treated as PM/Co-PM if either source identifies them, so
    the new staffing workflow does not strand legitimate PMs out of
    their own roster (Track 14.0-PM-STAFFING-UI-DISCOVERABILITY fix)."""
    if not actor_email:
        return (False, False)
    actor_email = actor_email.lower()
    is_primary = False
    is_co = False
    job = await db.jobs_master.find_one(
        {"project_number": project_number},
        {"_id": 0, "pm_email": 1, "co_pm_emails": 1},
    )
    if job:
        if (job.get("pm_email") or "").lower() == actor_email:
            is_primary = True
        if actor_email in {e.lower() for e in (job.get("co_pm_emails") or [])}:
            is_co = True
    if not (is_primary and is_co):
        # Fall back to the staffing roster for either role.
        cur = db.project_team_assignments.find(
            {
                "project_number": project_number,
                "active": True,
                "assignment_role": {"$in": ["pm", "co_pm"]},
                "email": {"$regex": f"^{re.escape(actor_email)}$", "$options": "i"},
            },
            {"_id": 0, "assignment_role": 1},
        )
        async for r in cur:
            role = r.get("assignment_role")
            if role == "pm":
                is_primary = True
            elif role == "co_pm":
                is_co = True
    return (is_primary, is_co)


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


# Role → recipient_role mapping for bell notifications. Keeps the bell
# drawer aligned with the portal each role lives in.
_ROLE_TO_RECIPIENT_ROLE: Dict[str, str] = {
    "pm": "pm",
    "co_pm": "pm",
    "executive_oversight": "pm",
    "superintendent": "pm",
    "assistant_superintendent": "pm",
    "project_engineer": "pm",
    "project_administrator": "pm",
    "project_coordinator": "pm",
    "qaqc_rep": "pm",
    "survey_rep": "pm",
    "accounting_rep": "pm",
    "foreman": "fl",
    "safety_rep": "safety",
    "hr_rep": "hr",
    "dispatch_rep": "dispatch",
    "equipment_manager": "shop",
    "shop_rep": "shop",
}


async def _notify_assignment(
    db,
    *,
    action: str,
    project_number: str,
    role_key: str,
    role_label: str,
    target_user_id: Optional[str],
    target_email: Optional[str],
    actor_name: str,
) -> None:
    """Fan out a bell notification to the newly-assigned (or removed)
    user so they see project context the moment they log in.

    Track 14.0-PM-STAFFING-RUNTIME-PROOF · Phase 5.
    """
    try:
        from routes.tasks_notifications import notification_service
    except Exception as exc:
        logger.warning("[team-roster] notification module unavailable: %s", exc)
        return
    recipient_role = _ROLE_TO_RECIPIENT_ROLE.get(role_key, "admin")
    if action == "assign":
        title = f"You were added to project {project_number}"
        message = f"{actor_name} added you to {project_number} as {role_label}."
    elif action == "remove":
        title = f"You were removed from project {project_number}"
        message = f"{actor_name} removed you from {project_number} as {role_label}."
    else:  # update
        title = f"Your role on project {project_number} was updated"
        message = f"{actor_name} updated your assignment on {project_number} ({role_label})."
    payload = {
        "type": "project_team_assignment",
        "title": title[:200],
        "message": message[:2000],
        "severity": "Info",
        "recipient_role": recipient_role,
        "recipient_user_id": target_user_id,
        "linked_project_number": project_number,
        "link_url": f"/pm/projects/{project_number}" if recipient_role == "pm" else None,
    }
    try:
        await notification_service.fanout(db, payload)
    except Exception as exc:
        logger.warning("[team-roster] notification fanout failed: %s", exc)


# ── Resolver helpers (used by Phase-2 producer rewrites) ─────────────
# TRACK 15.10 · operational recovery — display-name fallback hierarchy
# and login-status enrichment, plus JIT lift of PM/Co-PM from
# jobs_master into the response so PMs always see known leadership.
_DISPLAY_FALLBACK_ORDER = (
    "full_name", "display_name", "name", "first_name", "email",
    "employee_id",
)


def _resolve_display_name(*sources: Dict[str, Any]) -> str:
    """Track 15.10 · canonical display-name fallback hierarchy.

    1. full_name
    2. display_name (existing roster row)
    3. name (user_directory)
    4. first_name + last_name (employees)
    5. email
    6. employee_id
    7. "Unknown person — Admin review required"

    Never returns "(unnamed)". A missing identity is operator-visible
    so PMs know the row needs Admin review.
    """
    for src in sources:
        if not isinstance(src, dict):
            continue
        full = (src.get("full_name") or "").strip()
        if full:
            return full
        disp = (src.get("display_name") or "").strip()
        if disp:
            return disp
        name = (src.get("name") or "").strip()
        if name:
            return name
        first = (src.get("first_name") or "").strip()
        last = (src.get("last_name") or "").strip()
        if first or last:
            joined = " ".join(p for p in (first, last) if p)
            if joined:
                return joined
        em = (src.get("email") or "").strip()
        if em:
            return em
        emp = (src.get("employee_id") or "").strip()
        if emp:
            return f"Employee #{emp}"
    return "Unknown person — Admin review required"


def _login_status_from_directory(ud_row: Optional[Dict[str, Any]]) -> str:
    """Track 15.10 · derive login/access status from user_directory.

    Returns one of: "active", "invite_pending", "no_login", "disabled",
    "unknown". Uses EXISTING user_directory fields — no new auth
    system, no silent account creation.
    """
    if not ud_row:
        return "no_login"
    if ud_row.get("disabled"):
        return "disabled"
    if ud_row.get("must_change_password"):
        return "invite_pending"
    if ud_row.get("password_hash") or ud_row.get("last_login_at"):
        return "active"
    # User_directory row exists but no password set and never logged in —
    # treat as invite_pending (admin must reset/issue temp pwd).
    return "invite_pending"


async def _enrich_row_with_directory(
    db, row: Dict[str, Any],
) -> Dict[str, Any]:
    """Track 15.10 · attach login_status + a resolved display_name to a
    project_team_assignments row. Read-only. Best-effort: if directory
    lookup fails, login_status falls back to "unknown".
    """
    ud_row: Optional[Dict[str, Any]] = None
    try:
        if row.get("user_id"):
            ud_row = await db.user_directory.find_one(
                {"id": row["user_id"]},
                {"_id": 0, "id": 1, "email": 1, "name": 1,
                 "employee_id": 1, "disabled": 1,
                 "must_change_password": 1, "password_hash": 1,
                 "last_login_at": 1},
            )
        if not ud_row and row.get("email"):
            ud_row = await db.user_directory.find_one(
                {"email": (row.get("email") or "").lower()},
                {"_id": 0, "id": 1, "email": 1, "name": 1,
                 "employee_id": 1, "disabled": 1,
                 "must_change_password": 1, "password_hash": 1,
                 "last_login_at": 1},
            )
    except Exception as exc:
        logger.warning("[team-roster] directory enrichment failed: %s", exc)
        row["login_status"] = "unknown"
        row["display_name"] = _resolve_display_name(row)
        return row

    emp_row: Optional[Dict[str, Any]] = None
    if not ud_row and row.get("employee_id"):
        try:
            emp_row = await db.employees.find_one(
                {"id": row["employee_id"]},
                {"_id": 0, "first_name": 1, "last_name": 1, "email": 1},
            )
        except Exception:
            emp_row = None

    row["display_name"] = _resolve_display_name(row, ud_row or {}, emp_row or {})
    row["login_status"] = (
        _login_status_from_directory(ud_row) if ud_row is not None
        else ("no_login" if not row.get("user_id") else "unknown")
    )
    # Mirror useful directory fields for the UI (read-only).
    if ud_row:
        row.setdefault("email", ud_row.get("email") or row.get("email"))
    return row


async def _jit_lift_known_leadership(
    db, project_number: str, existing_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Track 15.10 · if no active row exists for PM / Co-PM, synthesise
    read-only rows from `jobs_master.pm_email` / `co_pm_emails` so the
    Project Team page never hides leadership the platform already
    knows. These synthetic rows are marked `synthetic: True` and
    `id: "jit-..."` so the UI can render them without offering remove/
    transfer actions (operator must run the backfill to materialise).
    """
    have_pm = any(
        (r.get("active") and r.get("assignment_role") == "pm")
        for r in existing_rows
    )
    have_co_pm: Set[str] = {
        (r.get("email") or "").lower()
        for r in existing_rows
        if r.get("active") and r.get("assignment_role") == "co_pm"
    }
    try:
        job = await db.jobs_master.find_one(
            {"project_number": project_number,
             "deleted_at": {"$in": [None, ""]}},
            {"_id": 0, "pm_email": 1, "co_pm_emails": 1},
        )
    except Exception as exc:
        logger.warning("[team-roster] jit-lift jobs_master read failed: %s", exc)
        return existing_rows
    if not job:
        return existing_rows

    synth: List[Dict[str, Any]] = []
    if not have_pm:
        pm_email = (job.get("pm_email") or "").strip().lower()
        if pm_email:
            ud_row = await db.user_directory.find_one(
                {"email": pm_email},
                {"_id": 0, "id": 1, "email": 1, "name": 1,
                 "employee_id": 1, "disabled": 1,
                 "must_change_password": 1, "password_hash": 1,
                 "last_login_at": 1},
            )
            synth.append({
                "id": f"jit-pm-{pm_email}",
                "project_number": project_number,
                "user_id": (ud_row or {}).get("id"),
                "email": pm_email,
                "display_name": _resolve_display_name({"email": pm_email}, ud_row or {}),
                "assignment_role": "pm",
                "role_label": ROLE_REGISTRY["pm"],
                "active": True,
                "is_primary": True,
                "synthetic": True,
                "synthetic_source": "jobs_master.pm_email",
                "login_status": _login_status_from_directory(ud_row),
            })
    for ce in (job.get("co_pm_emails") or []):
        ce_norm = (ce or "").strip().lower()
        if not ce_norm or ce_norm in have_co_pm:
            continue
        ud_row = await db.user_directory.find_one(
            {"email": ce_norm},
            {"_id": 0, "id": 1, "email": 1, "name": 1,
             "employee_id": 1, "disabled": 1,
             "must_change_password": 1, "password_hash": 1,
             "last_login_at": 1},
        )
        synth.append({
            "id": f"jit-copm-{ce_norm}",
            "project_number": project_number,
            "user_id": (ud_row or {}).get("id"),
            "email": ce_norm,
            "display_name": _resolve_display_name({"email": ce_norm}, ud_row or {}),
            "assignment_role": "co_pm",
            "role_label": ROLE_REGISTRY["co_pm"],
            "active": True,
            "is_primary": False,
            "synthetic": True,
            "synthetic_source": "jobs_master.co_pm_emails",
            "login_status": _login_status_from_directory(ud_row),
        })
    return existing_rows + synth


async def resolve_team_for_project(
    db, project_number: str, *, active_only: bool = True,
    enrich: bool = True,
) -> List[Dict[str, Any]]:
    q = {"project_number": project_number}
    if active_only:
        q["active"] = True
    rows: List[Dict[str, Any]] = []
    async for r in db.project_team_assignments.find(q, {"_id": 0}):
        public = _public(r)
        if enrich:
            await _enrich_row_with_directory(db, public)
        rows.append(public)
    if enrich:
        rows = await _jit_lift_known_leadership(db, project_number, rows)
    return rows


async def resolve_users_for_project_role(
    db, project_number: str, role: str,
) -> List[str]:
    """Return active user_ids assigned to (project, role). Empty list →
    no one rostered; caller should fall back to role-bucket routing."""
    role = _canonical_role(role) or role
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
    target_role = _canonical_role(target_role) or target_role
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

    @router.get("/api/team-roster/feature-flags")
    async def feature_flags(
        actor=Depends(require_any_portal_token),  # noqa: ARG001
    ):
        """Surface Phase-2B feature-flag state so the frontend can show
        a "person-level routing: ON/OFF" chip in admin diagnostics."""
        from lib.team_routing import ownership_lock_enabled  # noqa: PLC0415
        return {"ownership_lock_enabled": ownership_lock_enabled()}

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
        # Accept legacy aliases (safety_lead/dispatcher_contact) on
        # write — normalised to the canonical key before persistence.
        payload.assignment_role = _canonical_role(payload.assignment_role)
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
            "assignment_status": "ACTIVE",
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
            "end_reason": None,
            "ended_at": None,
            "ended_by": None,
            "replacement_user_id": None,
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
        await _notify_assignment(
            db, action="assign", project_number=project_number,
            role_key=payload.assignment_role,
            role_label=ROLE_REGISTRY.get(payload.assignment_role, payload.assignment_role),
            target_user_id=user_id, target_email=email,
            actor_name=actor.get("name") or actor.get("email") or "Admin",
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

        # TRACK 15.39 — detect role change FIRST so we can emit the
        # correct audit action.
        new_role = _canonical_role(patch.assignment_role) if patch.assignment_role else None
        is_role_change = bool(new_role) and new_role != existing["assignment_role"]
        if new_role and new_role not in ALL_ROLES:
            raise HTTPException(400, f"unknown assignment_role: {patch.assignment_role}")
        if is_role_change:
            # No-op duplicate guard: an active row with the same
            # (project, user, new_role) would create a duplicate
            # assignment.
            dup = await db.project_team_assignments.find_one({
                "project_number": project_number,
                "user_id": existing.get("user_id"),
                "assignment_role": new_role,
                "active": True,
                "id": {"$ne": assignment_id},
            }, {"_id": 0})
            if dup:
                raise HTTPException(
                    409,
                    f"User already holds the {ROLE_REGISTRY.get(new_role, new_role)} "
                    f"role on this project. Remove the existing assignment first.",
                )

        updates: Dict[str, Any] = {"updated_at": _now_iso(),
                                   "updated_by": actor.get("id") or "admin"}
        for field in ("assignment_scope", "is_primary", "is_backup",
                      "end_date", "notes"):
            v = getattr(patch, field, None)
            if v is not None:
                updates[field] = v
        if is_role_change:
            updates["assignment_role"] = new_role
        await db.project_team_assignments.update_one(
            {"id": assignment_id}, {"$set": updates},
        )
        after = await db.project_team_assignments.find_one(
            {"id": assignment_id}, {"_id": 0},
        )

        # Single audit row, correct action label.
        audit_action = "role_change" if is_role_change else "update"
        audit_notes = None
        if is_role_change:
            audit_notes = (
                f"role: {ROLE_REGISTRY.get(existing['assignment_role'], existing['assignment_role'])}"
                f" → {ROLE_REGISTRY.get(new_role, new_role)}"
            )
        await _audit(
            db, action=audit_action, project_number=project_number,
            assignment_role=new_role if is_role_change else existing["assignment_role"],
            target_user_id=existing.get("user_id"),
            target_email=existing.get("email"),
            before=_public(existing), after=_public(after), actor=actor,
            notes=audit_notes,
        )
        return {"ok": True, "assignment": _public(after), "role_changed": is_role_change}

    @router.delete("/api/admin/jobs/{project_number}/team/{assignment_id}")
    async def admin_remove_team_member(
        project_number: str,
        assignment_id: str,
        reason: Optional[str] = Query(default=None),
        body: Optional[AssignmentRemove] = Body(default=None),
        actor=Depends(require_admin_dep),
    ):
        actor = _coerce_actor(actor)
        existing = await db.project_team_assignments.find_one(
            {"id": assignment_id, "project_number": project_number,
             "active": True}, {"_id": 0},
        )
        if not existing:
            raise HTTPException(404, "active assignment not found")

        # TRACK 15.39 — resolve structured reason. Body takes precedence
        # over the legacy `?reason=` query-string. `other` requires text.
        reason_category: Optional[str] = None
        reason_text: Optional[str] = None
        if body:
            reason_category = (body.reason_category or "").strip().lower() or None
            reason_text = (body.reason_text or "").strip() or None
            if reason_category and reason_category not in _REMOVE_REASON_CATEGORIES:
                raise HTTPException(
                    400,
                    f"unknown reason_category: {reason_category}. "
                    f"Allowed: {sorted(_REMOVE_REASON_CATEGORIES)}",
                )
            if reason_category == "other" and not reason_text:
                raise HTTPException(
                    400,
                    "reason_text is required when reason_category is 'other'.",
                )
        # Compose a single human-readable string for the legacy
        # `remove_reason` field + audit `notes`.
        composed_reason = reason
        if reason_category:
            label_map = {
                "reassigned": "Reassigned",
                "staffing_adjustment": "Staffing Adjustment",
                "promotion": "Promotion",
                "demotion": "Demotion",
                "project_complete": "Project Complete",
                "left_company": "Left Company",
                "other": "Other",
            }
            label = label_map.get(reason_category, reason_category)
            composed_reason = f"{label}: {reason_text}" if reason_text else label

        now = _now_iso()
        await db.project_team_assignments.update_one(
            {"id": assignment_id},
            {"$set": {
                "active": False,
                "removed_by": actor.get("id") or "admin",
                "removed_at": now,
                "remove_reason": composed_reason,
                "remove_reason_category": reason_category,
                "remove_reason_text": reason_text,
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
            notes=composed_reason,
        )
        await _notify_assignment(
            db, action="remove", project_number=project_number,
            role_key=existing["assignment_role"],
            role_label=ROLE_REGISTRY.get(existing["assignment_role"], existing["assignment_role"]),
            target_user_id=existing.get("user_id"),
            target_email=existing.get("email"),
            actor_name=actor.get("name") or actor.get("email") or "Admin",
        )
        return {"ok": True}

    @router.post("/api/admin/team-roster/backfill")
    async def admin_backfill(
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await backfill_pm_and_co_pm(db)

    # ── TRACK 15.10 · PM-callable directory picker ──────────────────
    # PMs were previously forced to type a raw email in the Add Member
    # flow because only Admin could call the K4 directory endpoint.
    # This route exposes a READ-ONLY, role-filtered, active-only subset
    # of `user_directory` to portal token holders so the Add Member
    # picker can be a dropdown backed by the existing source rosters
    # (Field Leadership, Shop, Safety, HR, Dispatch — all of which
    # already write to user_directory.portals). No new identity system,
    # no silent account creation. Pure read.
    @router.get("/api/pm/directory/users")
    async def pm_directory_users(
        actor=Depends(require_any_portal_token),  # noqa: ARG001
        q: Optional[str] = Query(default=None, max_length=120),
        portal: Optional[str] = Query(default=None, max_length=40),
        limit: int = Query(default=300, ge=1, le=500),
    ):
        match: Dict[str, Any] = {
            "$and": [
                {"$or": [{"disabled": {"$exists": False}},
                         {"disabled": False}]},
            ],
        }
        if q:
            needle = q.strip()
            match["$and"].append({
                "$or": [
                    {"email": {"$regex": needle, "$options": "i"}},
                    {"name": {"$regex": needle, "$options": "i"}},
                ],
            })
        if portal:
            match["$and"].append({"portals": portal.strip().lower()})
        rows: List[Dict[str, Any]] = []
        async for u in db.user_directory.find(
            match,
            {"_id": 0, "id": 1, "email": 1, "name": 1,
             "employee_id": 1, "portals": 1, "disabled": 1,
             "must_change_password": 1, "password_hash": 1,
             "last_login_at": 1},
        ).sort("email", 1).limit(limit):
            rows.append({
                "id": u.get("id"),
                "email": u.get("email"),
                "name": u.get("name") or "",
                "employee_id": u.get("employee_id"),
                "portals": sorted(set(u.get("portals") or [])),
                "login_status": _login_status_from_directory(u),
            })
        return {"ok": True, "items": rows, "count": len(rows)}

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
            "assignment_status": "ACTIVE",
            "start_date": payload.start_date or now[:10],
            "end_date": payload.end_date,
            "assigned_by": actor.get("id") or actor.get("name") or "pm",
            "assigned_by_role": actor.get("_actor") or "pm",
            "assigned_at": now,
            "updated_by": None, "updated_at": None,
            "removed_by": None, "removed_at": None,
            "remove_reason": None, "end_reason": None,
            "ended_at": None, "ended_by": None,
            "replacement_user_id": None,
            "source": "pm_ui",
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

    # ── Track 14.0-PM-STAFFING-UI-DISCOVERABILITY ────────────────────
    # Cross-project staffing summary — powers the new "Project Staffing"
    # landing tile in Admin/PM Hubs. Returns per-project active counts,
    # PM scope honored, and unassigned-role surface so operators see
    # gaps at a glance.

    @router.get("/api/project-staffing/summary")
    async def project_staffing_summary(
        actor=Depends(require_any_portal_token),
        limit: int = Query(default=200, ge=1, le=500),
    ):
        """Cross-project staffing summary. Admin sees all active projects;
        PM sees only their `compute_pm_scope` projects. Each project entry
        returns active assignment count, unassigned canonical roles,
        and a small primary-roles snapshot (PM/Super/Foreman/Safety/QC)."""
        actor = _coerce_actor(actor)
        is_admin = actor.get("_actor") == "admin"

        # Pull active projects.
        q_jobs: Dict[str, Any] = {"deleted_at": {"$in": [None, ""]}}
        if not is_admin:
            # PM scope — use existing compute_pm_scope helper.
            try:
                from pm_auth import compute_pm_scope  # noqa: PLC0415
                scope = await compute_pm_scope(db, actor)
                if not getattr(scope, "is_admin", False):
                    pns = list(getattr(scope, "project_numbers", []) or [])
                    if not pns:
                        return {"items": [], "count": 0,
                                "role_totals": {}, "role_keys": list(ROLE_REGISTRY.keys()),
                                "overloaded": [],
                                "overload_threshold": OVERLOAD_ACTIVE_PROJECT_THRESHOLD,
                                "people_count": 0,
                                "totals": {"projects": 0, "active_assignments": 0,
                                           "unassigned_role_slots": 0}}
                    q_jobs["project_number"] = {"$in": pns}
            except Exception:
                pass

        projects: List[Dict[str, Any]] = []
        async for j in db.jobs_master.find(q_jobs, {"_id": 0}).limit(limit):
            projects.append(j)

        # Build per-project roster from project_team_assignments.
        pn_set = [p.get("project_number") for p in projects if p.get("project_number")]
        roster_by_pn: Dict[str, List[Dict[str, Any]]] = {p: [] for p in pn_set}
        if pn_set:
            cur = db.project_team_assignments.find(
                {"project_number": {"$in": pn_set}, "active": True},
                {"_id": 0},
            )
            async for r in cur:
                pn = r.get("project_number")
                if pn in roster_by_pn:
                    roster_by_pn[pn].append(_public(r))

        # Role-level aggregate (how many active assignments per role
        # across the actor's scope).
        role_totals: Dict[str, int] = {k: 0 for k in ROLE_REGISTRY.keys()}
        total_active = 0
        total_unassigned_slots = 0
        items: List[Dict[str, Any]] = []

        # TRACK 14.0-OVERLOADED-CREW-VISIBILITY · Phase 1+3 — per-person
        # aggregation across the actor's scope. Keyed on email (lower),
        # falling back to user_id if email is absent. One row per person
        # carrying every active project they are on so leadership can
        # see WHO is overloaded and WHICH projects create the load.
        person_index: Dict[str, Dict[str, Any]] = {}

        # Map for project name lookup during person aggregation.
        project_name_by_pn: Dict[str, str] = {
            (j.get("project_number") or ""):
                (j.get("name") or j.get("project_name") or "")
            for j in projects
        }

        primary_role_keys = ("pm", "superintendent", "foreman",
                             "safety_rep", "qaqc_rep", "project_engineer")
        for j in projects:
            pn = j.get("project_number")
            roster = roster_by_pn.get(pn, [])
            roles_filled: Set[str] = set()
            primary_snapshot: Dict[str, Dict[str, Any]] = {}
            for r in roster:
                role = r.get("assignment_role")
                if role in ROLE_REGISTRY:
                    role_totals[role] = role_totals.get(role, 0) + 1
                    roles_filled.add(role)
                    if role in primary_role_keys and role not in primary_snapshot:
                        primary_snapshot[role] = {
                            "display_name": r.get("display_name") or r.get("email") or "—",
                            "email": r.get("email"),
                            "is_primary": bool(r.get("is_primary")),
                        }
                # Per-person index — count every active assignment row
                # toward that person's load, regardless of role.
                p_email = (r.get("email") or "").strip().lower()
                p_uid = r.get("user_id") or ""
                p_key = p_email or p_uid
                if p_key:
                    bucket = person_index.get(p_key)
                    if bucket is None:
                        bucket = {
                            "key": p_key,
                            "email": r.get("email"),
                            "user_id": p_uid or None,
                            "display_name": r.get("display_name") or r.get("email") or "—",
                            "projects": [],
                        }
                        person_index[p_key] = bucket
                    bucket["projects"].append({
                        "project_number": pn,
                        "name": project_name_by_pn.get(pn or "", ""),
                        "assignment_role": role,
                        "role_label": ROLE_REGISTRY.get(role, role or "—"),
                        "is_primary": bool(r.get("is_primary")),
                    })
            unassigned = [k for k in ROLE_REGISTRY.keys() if k not in roles_filled]
            total_active += len(roster)
            total_unassigned_slots += len(unassigned)
            items.append({
                "project_number": pn,
                "name": j.get("name") or j.get("project_name") or "",
                "status": "active" if (j.get("active") is not False) else "inactive",
                "active_assignments": len(roster),
                "unassigned_roles": unassigned,
                "primary_snapshot": primary_snapshot,
            })

        items.sort(key=lambda i: (i.get("active_assignments") or 0, i.get("project_number") or ""))

        # TRACK 14.0-OVERLOADED-CREW-VISIBILITY · Phase 1-6 — build the
        # overload roster from the in-memory person index. No new
        # queries; we already saw every active assignment row above.
        # "Active project count" is the number of UNIQUE project numbers
        # the person is rostered on (not the number of roster rows) so
        # someone holding two roles on the same job counts as 1 project.
        overloaded: List[Dict[str, Any]] = []
        people_summary: List[Dict[str, Any]] = []
        for bucket in person_index.values():
            # Group this person's roster rows by project_number.
            by_pn: Dict[str, Dict[str, Any]] = {}
            for row in bucket["projects"]:
                pn = row.get("project_number") or ""
                slot = by_pn.get(pn)
                if slot is None:
                    slot = {
                        "project_number": pn,
                        "name": row.get("name") or "",
                        "roles": [],
                        "is_primary": False,
                    }
                    by_pn[pn] = slot
                slot["roles"].append({
                    "assignment_role": row.get("assignment_role"),
                    "role_label": row.get("role_label"),
                    "is_primary": bool(row.get("is_primary")),
                })
                if row.get("is_primary"):
                    slot["is_primary"] = True
            projects_sorted = sorted(by_pn.values(), key=lambda p: p.get("project_number") or "")
            count = len(projects_sorted)
            display_name = bucket.get("display_name") or bucket.get("email") or bucket.get("user_id") or "—"
            person_row = {
                "email": bucket.get("email"),
                "user_id": bucket.get("user_id"),
                "display_name": display_name,
                "active_project_count": count,
                "is_overloaded": count >= OVERLOAD_ACTIVE_PROJECT_THRESHOLD,
                "projects": projects_sorted,
            }
            people_summary.append(person_row)
            if person_row["is_overloaded"]:
                overloaded.append(person_row)

        # Sort overloaded list: highest load first, then name.
        overloaded.sort(
            key=lambda p: (-p["active_project_count"], (p.get("display_name") or "").lower())
        )

        return {
            "items": items,
            "count": len(items),
            "role_keys": list(ROLE_REGISTRY.keys()),
            "role_totals": role_totals,
            "overloaded": overloaded,
            "overload_threshold": OVERLOAD_ACTIVE_PROJECT_THRESHOLD,
            "people_count": len(people_summary),
            "totals": {
                "projects": len(items),
                "active_assignments": total_active,
                "unassigned_role_slots": total_unassigned_slots,
            },
            "actor_scope": "admin" if is_admin else (actor.get("_actor") or "pm"),
        }

    @router.get("/api/employees/{employee_key}/project-assignments")
    async def employee_project_assignments(
        employee_key: str,
        actor=Depends(require_any_portal_token),  # noqa: ARG001
    ):
        """Reverse lookup — every active project assignment for an
        employee. `employee_key` resolves against user_id, employee_id,
        or email. Used by HR Employee Drawer and search."""
        key = (employee_key or "").strip()
        if not key:
            return {"items": [], "count": 0, "employee_key": ""}
        q = {
            "active": True,
            "$or": [
                {"user_id": key},
                {"employee_id": key},
                {"email": {"$regex": f"^{re.escape(key)}$", "$options": "i"}},
            ],
        }
        items: List[Dict[str, Any]] = []
        async for r in db.project_team_assignments.find(q, {"_id": 0}):
            items.append(_public(r))
        return {"items": items, "count": len(items), "employee_key": key}

    app.include_router(router)
    return router


__all__ = [
    "register_project_team_assignments",
    "resolve_team_for_project",
    "resolve_users_for_project_role",
    "backfill_pm_and_co_pm",
    "ROLE_REGISTRY",
    "ALL_ROLES",
    "LEGACY_ROLE_ALIASES",
    "_canonical_role",
    "ADMIN_ONLY_ROLES",
    "PM_ASSIGNABLE_ROLES",
    "OVERLOAD_ACTIVE_PROJECT_THRESHOLD",
]
