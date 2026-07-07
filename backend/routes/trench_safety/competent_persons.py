"""FV-7.2 · Competent Person designation registry.

A Competent Person (OSHA 29 CFR 1926.32(f)) is not "any active employee."
The platform must track who has been formally designated, by whom,
when, and whether the designation is still current.

This module owns the CP-designation surface on top of the existing
`db.employees` collection. NO new collection. NO new auth model.
Just structured fields written under `competent_person_designated`,
`cp_approved_by`, `cp_approval_date`, `cp_active`, `cp_training_date`,
`cp_expiration_date`, `cp_notes` on the existing employee document.

Public consumers (the Excavation public form) pull the filtered list
from `GET /api/employees/competent-persons` so the EmployeePicker
shows only currently-designated CPs in normal selection lists.

Audit: every designation change writes a `cp_designation_changed`
event into `audit_events` and a journal entry into
`employee.cp_designation_history`.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from ._helpers import now_iso, write_audit

logger = logging.getLogger(__name__)


class CPDesignation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    competent_person_designated: bool = False
    cp_approved_by: str = ""
    cp_approval_date: str = ""        # YYYY-MM-DD
    cp_active: bool = True
    cp_training_date: str = ""        # future-ready
    cp_expiration_date: str = ""      # future-ready
    cp_notes: str = ""                # future-ready
    reason: str = ""                  # free-text reason for this change


def _is_expired(emp: Dict[str, Any]) -> bool:
    exp = (emp.get("cp_expiration_date") or "").strip()
    if not exp:
        return False
    # ISO date string lexical comparison works here because dates are
    # always YYYY-MM-DD.
    return exp < now_iso().split("T")[0]


def register_competent_person_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin,
    require_safety_or_admin,
) -> None:
    """Register CP-designation endpoints under /api."""

    # ── Public list — DELEGATED to the Qualifications Engine (23.10-B)
    #   Single source of truth = `db.safety_training_records` +
    #   `services/certifications/qualification_registry.py`. The
    #   legacy `competent_person_designated` flag on `db.employees`
    #   is now vestigial — backfilled by the 23.10-B migration and
    #   read no more.
    @api_router.get("/employees/competent-persons")
    async def list_competent_persons():
        """Consumer-facing list of currently-active Competent Persons.

        Reads from the Qualifications Engine registry. Only rows with
        `verification_status="active"` AND non-expired
        `expiration_date` AND no suspension/revocation appear here.

        Response contract preserved for backwards compatibility with
        the trench safety CP picker (shape: {items:[...], count:N}
        where each item carries id, name, employee_id, crew,
        role, trade, cp_approval_date, cp_expiration_date,
        cp_approved_by).
        """
        from services.certifications.qualification_registry import (
            list_active_qualifications,
        )
        rows = await list_active_qualifications(
            db, qualification_type="COMPETENT_PERSON", warning_days=30,
        )
        items = [{
            "id": r.get("employee_id") or "",
            "employee_id": r.get("employee_id") or "",
            "name": r.get("employee_name") or "",
            "crew": r.get("employee_crew") or "",
            "role": r.get("employee_trade") or "",
            "trade": r.get("employee_trade") or "",
            "cp_approval_date": r.get("issued_at") or "",
            "cp_expiration_date": r.get("expires_at") or "",
            "cp_approved_by": r.get("issuing_organization") or "",
            # Engine surface — new consumers should prefer these.
            "qualification_id": r.get("qualification_id"),
            "qualification_type": r.get("qualification_type"),
            "expires_in_days": r.get("expires_in_days"),
            "warning": r.get("warning"),
        } for r in rows]
        # Sort by employee name for stable UI order (matches legacy).
        items.sort(key=lambda x: (x.get("name") or "").lower())
        return {"items": items, "count": len(items)}


    # ── Admin · set / update CP designation ────────────────────────
    @api_router.put("/admin/employees/{employee_id}/cp-designation")
    async def set_cp_designation(
        employee_id: str,
        body: CPDesignation,
        actor: Dict[str, Any] = Depends(require_admin),
    ):
        emp = await db.employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id}]},
            {"_id": 0},
        )
        if not emp:
            raise HTTPException(404, "Employee not found")

        prev_designated = bool(emp.get("competent_person_designated") or emp.get("cp_designated"))

        actor_dict = actor if isinstance(actor, dict) else {}
        actor_label = actor_dict.get("email") or actor_dict.get("name") or "admin"
        history = list(emp.get("cp_designation_history") or [])
        history.append({
            "at": now_iso(),
            "by": actor_label,
            "from_designated": prev_designated,
            "to_designated": body.competent_person_designated,
            "cp_active": body.cp_active,
            "approved_by": body.cp_approved_by,
            "approval_date": body.cp_approval_date,
            "training_date": body.cp_training_date,
            "expiration_date": body.cp_expiration_date,
            "reason": body.reason,
        })

        upd = {
            "competent_person_designated": bool(body.competent_person_designated),
            "cp_designated": bool(body.competent_person_designated),  # mirror for back-compat
            "cp_approved_by": body.cp_approved_by,
            "cp_approval_date": body.cp_approval_date,
            "cp_active": bool(body.cp_active),
            "cp_training_date": body.cp_training_date,
            "cp_expiration_date": body.cp_expiration_date,
            "cp_notes": body.cp_notes,
            "cp_designation_history": history,
            "cp_designation_updated_at": now_iso(),
            "cp_designation_updated_by": actor_label,
            "updated_at": now_iso(),
        }
        await db.employees.update_one({"id": emp["id"]}, {"$set": upd})

        await write_audit(
            db, kind="cp_designation_changed",
            asset_id=emp["id"], actor=actor_dict,
            detail={
                "from_designated": prev_designated,
                "to_designated": body.competent_person_designated,
                "cp_active": body.cp_active,
                "approval_date": body.cp_approval_date,
                "expiration_date": body.cp_expiration_date,
                "reason": body.reason,
            },
        )
        out = await db.employees.find_one({"id": emp["id"]}, {"_id": 0})
        return out

    # ── Safety/Admin · read single employee CP record ─────────────
    @api_router.get("/admin/employees/{employee_id}/cp-designation")
    async def get_cp_designation(
        employee_id: str,
        _actor: Dict[str, Any] = Depends(require_safety_or_admin),
    ):
        emp = await db.employees.find_one(
            {"$or": [{"id": employee_id}, {"employee_id": employee_id}]},
            {"_id": 0, "id": 1, "name": 1, "employee_id": 1,
             "competent_person_designated": 1, "cp_designated": 1,
             "cp_approved_by": 1, "cp_approval_date": 1,
             "cp_active": 1, "cp_training_date": 1,
             "cp_expiration_date": 1, "cp_notes": 1,
             "cp_designation_history": 1,
             "cp_designation_updated_at": 1, "cp_designation_updated_by": 1},
        )
        if not emp:
            raise HTTPException(404, "Employee not found")
        emp["expired"] = _is_expired(emp)
        return emp
