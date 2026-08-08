"""
Safety Portal · training.py — Phase 4 training records + per-employee
safety profile.

Training is tied to ``db.employees`` (single source of truth — no
duplicate employee list). Reads accept Safety/HR/Admin tokens; writes
require Safety.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
from lib.synthetic_flr_filter import apply_synthetic_flr_exclusion

from ._models import TrainingRecordCreate, TrainingRecordUpdate


def register_training_routes(
    api_router: APIRouter, db, require_safety_token, require_safety_or_hr_or_admin,
) -> None:

    # iter353a · Shared HR+Safety+Admin write gate for accountability
    # records. Keeps Safety + Admin authority intact while letting HR
    # operationally manage employee accountability (per operator
    # policy). DELETE remains gated by `require_safety_token` —
    # operator rule: HR has NO hard-delete authority. Soft state
    # changes (mark inactive / supersede) are achieved via PATCH.
    _gate_write = require_safety_or_hr_or_admin

    @api_router.get("/safety/training-records")
    async def list_training_records(
        employee_id: Optional[str] = None,
        expiring_within_days: Optional[int] = None,
        _: dict = Depends(require_safety_or_hr_or_admin),
    ):
        q: dict = {}
        if employee_id:
            q["employee_id"] = employee_id
        if expiring_within_days is not None and expiring_within_days >= 0:
            cutoff = (datetime.now(timezone.utc) + timedelta(days=expiring_within_days)).isoformat()[:10]
            q["expiration_date"] = {"$ne": None, "$lte": cutoff}
        return await db.safety_training_records.find(q, {"_id": 0}).sort("expiration_date", 1).to_list(5000)

    @api_router.post("/safety/training-records")
    async def create_training_record(
        body: TrainingRecordCreate, user: dict = Depends(_gate_write),
    ):
        emp_name = (body.employee_name or "").strip()
        if not emp_name:
            emp = await db.employees.find_one({"id": body.employee_id}, {"_id": 0, "name": 1})
            emp_name = (emp or {}).get("name") or ""
        now = datetime.now(timezone.utc).isoformat()
        # iter353a · canonical actor-audit fields. Both legacy
        # `created_by_name` (preserved for back-compat) and the new
        # role-attributed fields land on every write.
        actor_role = (user.get("_actor") or user.get("role") or "safety").lower()
        actor_email = user.get("email") or ""
        actor_name = user.get("name") or actor_email or ""
        doc = {
            "id": str(uuid.uuid4()),
            "employee_id": body.employee_id,
            "employee_name": emp_name,
            "training_name": body.training_name.strip(),
            "certification_type": (body.certification_type or "").strip(),
            "completed_date": body.completed_date,
            "expiration_date": body.expiration_date,
            "issued_by": (body.issued_by or "").strip(),
            "notes": (body.notes or "").strip(),
            "certificate_file_id": body.certificate_file_id,
            # iter138 — bind to employees master collection
            "employee_master_id": (body.employee_master_id or body.employee_id or "").strip(),
            # Legacy fields (preserved)
            "created_by_name": actor_name,
            # iter353a · canonical actor_audit attribution
            "created_by": actor_email,
            "created_by_role": actor_role,
            "originating_portal": actor_role,
            "updated_by": actor_email,
            "updated_by_role": actor_role,
            "created_at": now,
            "updated_at": now,
            # TRACK 15.50 · incident-trigger traceability fields
            "source_incident_id": (body.source_incident_id or "").strip() or None,
            "source_incident_doc_id": (body.source_incident_doc_id or "").strip() or None,
            "topic_keys": body.topic_keys or [],
            # TRACK 15.50 AMENDMENT
            "status": (body.status or ("Completed" if body.completed_date else "Assigned")),
            "trigger_classification": body.trigger_classification or [],
            "due_date": body.due_date or None,
            "verified_by": body.verified_by or None,
            "verified_at": body.verified_at or None,
            "waived_by": body.waived_by or None,
            "waived_at": body.waived_at or None,
            "waiver_reason": body.waiver_reason or None,
        }
        await db.safety_training_records.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch("/safety/training-records/{rec_id}")
    async def update_training_record(
        rec_id: str, body: TrainingRecordUpdate, user: dict = Depends(_gate_write),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not update:
            raise HTTPException(400, "No changes")
        # iter353a · attribute every edit to {actor, role}
        actor_role = (user.get("_actor") or user.get("role") or "safety").lower()
        actor_email = user.get("email") or ""
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        update["updated_by"] = actor_email
        update["updated_by_role"] = actor_role
        res = await db.safety_training_records.update_one({"id": rec_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.safety_training_records.find_one({"id": rec_id}, {"_id": 0})

    @api_router.delete("/safety/training-records/{rec_id}")
    async def delete_training_record(
        rec_id: str, _: dict = Depends(require_safety_token),
    ):
        # iter353a NOTE: DELETE remains Safety+Admin only.
        # Operator policy explicitly excluded HR from hard-delete authority.
        # HR should archive/supersede via PATCH instead.
        res = await db.safety_training_records.delete_one({"id": rec_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}

    @api_router.get("/safety/employee-profile/{employee_id}")
    async def employee_safety_profile(
        employee_id: str, _: dict = Depends(require_safety_or_hr_or_admin),
    ):
        employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
        if not employee:
            raise HTTPException(404, "Employee not found")
        name = employee.get("name", "")
        trainings = await db.safety_training_records.find(
            {"employee_id": employee_id}, {"_id": 0}
        ).sort("expiration_date", 1).to_list(500)
        meetings_attended = await db.safety_meetings.count_documents(
            {"attendees": {"$elemMatch": {"name": name}}}
        ) if name else 0
        incident_involvements = 0
        if name:
            incident_involvements = await db.incidents.count_documents({
                "$or": [
                    {"injured_party_name": name},
                    {"employees_involved": {"$elemMatch": {"name": name}}},
                ]
            })
        ppe_issuance = 0
        if name:
            ppe_issuance = await db.field_leadership_records.count_documents(apply_synthetic_flr_exclusion({
                "kind": "safety_equipment_issuance",
                "employee_name": name,
            }))
        open_cas = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion({
                "assigned_to_name": name,
                "status": {"$in": ["Open", "In Progress", "Pending Review"]},
            })
        ) if name else 0
        today = datetime.now(timezone.utc).isoformat()[:10]
        thirty_out = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()[:10]
        expiring_30 = [
            t for t in trainings
            if t.get("expiration_date") and today <= t["expiration_date"] <= thirty_out
        ]
        expired = [
            t for t in trainings
            if t.get("expiration_date") and t["expiration_date"] < today
        ]
        return {
            "employee": employee,
            "trainings": trainings,
            "training_summary": {
                "total": len(trainings),
                "expiring_within_30_days": len(expiring_30),
                "expired": len(expired),
            },
            "meetings_attended": meetings_attended,
            "incident_involvements": incident_involvements,
            "ppe_issuance_count": ppe_issuance,
            "open_corrective_actions": open_cas,
        }


__all__ = ["register_training_routes"]
