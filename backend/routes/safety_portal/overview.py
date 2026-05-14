"""
Safety Portal · overview.py — KPI roll-up endpoints.

Two endpoints with the same shape so /admin/safety/overview and the
Safety-side /safety/overview can feed the same dashboard component on
both portals.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends


async def _build_overview_payload(db) -> dict:
    now = datetime.now(timezone.utc)
    today = now.isoformat()[:10]
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    thirty_days_out = (now + timedelta(days=30)).isoformat()[:10]
    return {
        "incidents_total": await db.incidents.count_documents({}),
        "incidents_last_7d": await db.incidents.count_documents({"created_at": {"$gte": seven_days_ago}}),
        "meetings_last_7d": await db.safety_meetings.count_documents({"created_at": {"$gte": seven_days_ago}}),
        "inspections_last_30d": await db.inspections.count_documents({"created_at": {"$gte": thirty_days_ago}}),
        "corrective_actions_open": await db.corrective_actions.count_documents(
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]}}
        ),
        "corrective_actions_overdue": await db.corrective_actions.count_documents(
            {"status": {"$in": ["Open", "In Progress", "Pending Review"]},
             "due_date": {"$ne": None, "$lt": today}}
        ),
        "training_deficiencies_total": await db.field_leadership_records.count_documents(
            {"kind": "training_deficiency"}
        ),
        "safety_equipment_issuances_total": await db.field_leadership_records.count_documents(
            {"kind": "safety_equipment_issuance"}
        ),
        "fire_extinguishers_total": await db.fire_extinguishers.count_documents({}),
        "fire_extinguishers_overdue": await db.fire_extinguishers.count_documents(
            {"next_due_date": {"$ne": None, "$lt": today}}
        ),
        "training_records_total": await db.safety_training_records.count_documents({}),
        "training_expiring_30d": await db.safety_training_records.count_documents(
            {"expiration_date": {"$ne": None, "$gte": today, "$lte": thirty_days_out}}
        ),
        "training_expired": await db.safety_training_records.count_documents(
            {"expiration_date": {"$ne": None, "$lt": today}}
        ),
        "safety_documents_total": await db.safety_documents.count_documents({}),
        "generated_at": now.isoformat(),
    }


def register_overview_routes(
    api_router: APIRouter, db, require_admin, require_safety_token,
) -> None:
    @api_router.get("/safety/overview")
    async def safety_overview(_: dict = Depends(require_safety_token)):
        return await _build_overview_payload(db)

    @api_router.get("/admin/safety/overview", dependencies=[Depends(require_admin)])
    async def admin_safety_overview():
        return await _build_overview_payload(db)


__all__ = ["register_overview_routes"]
