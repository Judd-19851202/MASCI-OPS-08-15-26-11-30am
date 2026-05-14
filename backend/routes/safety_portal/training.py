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

from ._models import TrainingRecordCreate, TrainingRecordUpdate


def register_training_routes(
    api_router: APIRouter, db, require_safety_token, require_safety_or_hr_or_admin,
) -> None:

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
        body: TrainingRecordCreate, user: dict = Depends(require_safety_token),
    ):
        emp_name = (body.employee_name or "").strip()
        if not emp_name:
            emp = await db.employees.find_one({"id": body.employee_id}, {"_id": 0, "name": 1})
            emp_name = (emp or {}).get("name") or ""
        now = datetime.now(timezone.utc).isoformat()
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
            "created_by_name": user.get("name") or "",
            "created_at": now,
            "updated_at": now,
        }
        await db.safety_training_records.insert_one(doc)
        doc.pop("_id", None)
        return doc

    @api_router.patch("/safety/training-records/{rec_id}")
    async def update_training_record(
        rec_id: str, body: TrainingRecordUpdate, _: dict = Depends(require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not update:
            raise HTTPException(400, "No changes")
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.safety_training_records.update_one({"id": rec_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.safety_training_records.find_one({"id": rec_id}, {"_id": 0})

    @api_router.delete("/safety/training-records/{rec_id}")
    async def delete_training_record(
        rec_id: str, _: dict = Depends(require_safety_token),
    ):
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
            ppe_issuance = await db.field_leadership_records.count_documents({
                "kind": "safety_equipment_issuance",
                "employee_name": name,
            })
        open_cas = await db.corrective_actions.count_documents({
            "assigned_to_name": name,
            "status": {"$in": ["Open", "In Progress", "Pending Review"]},
        }) if name else 0
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
