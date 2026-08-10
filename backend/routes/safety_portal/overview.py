"""
Safety Portal · overview.py — KPI roll-up endpoints.

Two endpoints with the same shape so /admin/safety/overview and the
Safety-side /safety/overview can feed the same dashboard component on
both portals.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from lib.corrective_action_truth import (
    open_corrective_action_query,
    overdue_corrective_action_query,
)
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
from lib.synthetic_flr_filter import apply_synthetic_flr_exclusion


def _overview_card_metadata() -> dict:
    base_source = [
        "incidents",
        "corrective_actions",
        "safety_meetings",
        "inspections",
        "field_leadership_records",
        "fire_extinguishers",
        "safety_training_records",
        "safety_documents",
    ]
    return {
        "page": {
            "kpi_name": "Safety Operations Snapshot",
            "business_definition": "Live operational snapshot for the Safety portals and leadership attention surfaces.",
            "source_of_truth": base_source,
            "api_endpoint": "/api/safety/overview",
            "formula": "Direct Mongo counts over live Safety source records; no client-side KPI remapping is allowed.",
            "confidence": "HIGH",
            "status_reason": "The same endpoint feeds Safety portal and leadership attention consumers, so every visible count must trace back to shared Safety source records.",
            "drilldown_source": "/safety-portal",
            "owner": "safety-truth",
            "freshness": "Generated on request.",
        },
        "sections": {
            "corrective_actions": {
                "kpi_name": "Safety Corrective Actions Attention",
                "business_definition": "Open and overdue corrective actions that still require Safety follow-up.",
                "source_of_truth": "corrective_actions",
                "formula": {
                    "open": "count of operator-visible corrective actions not in terminal status",
                    "overdue": "subset of open corrective actions with a non-blank due date before today",
                },
                "freshness": "Generated on request.",
                "status_reason": "These counts drive Safety prioritization and leadership escalation review.",
            },
            "compliance": {
                "kpi_name": "Safety Compliance Snapshot",
                "business_definition": "Counts of overdue extinguisher inspections and expired or soon-expiring training records.",
                "source_of_truth": ["fire_extinguishers", "safety_training_records"],
                "formula": {
                    "fire_extinguishers_overdue": "next_due_date before today",
                    "training_expired": "expiration_date before today",
                    "training_expiring_30d": "expiration_date between today and 30 days out",
                },
                "freshness": "Generated on request.",
                "status_reason": "These counts surface compliance gaps before they become field or audit failures.",
            },
            "incidents": {
                "kpi_name": "Safety Incident Activity",
                "business_definition": "Recent incident and inspection activity used to guide the next Safety follow-up.",
                "source_of_truth": ["incidents", "safety_meetings", "inspections", "safety_documents"],
                "formula": {
                    "incidents_last_7d": "incidents created in the last 7 days",
                    "meetings_last_7d": "safety meetings created in the last 7 days",
                    "inspections_last_30d": "inspections created in the last 30 days",
                    "safety_documents_total": "total safety documents on file",
                },
                "freshness": "Generated on request.",
                "status_reason": "These counts show whether the field is producing the records Safety expects to review.",
            },
            "classic_hub": {
                "kpi_name": "Safety Hub Snapshot",
                "business_definition": "The Safety Hub dashboard tiles reuse the same live Safety snapshot endpoint.",
                "source_of_truth": base_source,
                "formula": "Each dashboard tile maps directly to a field in /api/safety/overview.",
                "freshness": "Generated on request.",
                "status_reason": "The classic Safety hub must explain the same governed counts shown in the newer hub and leadership read surfaces.",
            },
        },
    }


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
            apply_synthetic_corrective_action_exclusion(open_corrective_action_query())
        ),
        "corrective_actions_overdue": await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=today))
        ),
        "training_deficiencies_total": await db.field_leadership_records.count_documents(
            apply_synthetic_flr_exclusion({"kind": "training_deficiency"})
        ),
        "safety_equipment_issuances_total": await db.field_leadership_records.count_documents(
            apply_synthetic_flr_exclusion({"kind": "safety_equipment_issuance"})
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
        "kpi_metadata": _overview_card_metadata(),
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
