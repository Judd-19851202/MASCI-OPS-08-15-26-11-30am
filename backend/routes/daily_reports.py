"""Daily Job Reports routes.

Extracted from server.py 2026-04-28 (P1 refactor batch 3).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field


class DailyReportCreate(BaseModel):
    """Daily site activity log (replaces Fieldwire daily reports)."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    report_date: str  # YYYY-MM-DD
    report_number: Optional[str] = ""
    prepared_by: str
    superintendent: Optional[str] = ""

    weather_summary: Optional[str] = ""
    weather_snapshots: List[Dict[str, Any]] = Field(default_factory=list)

    schedule_delays: Optional[str] = "No"
    schedule_delays_notes: Optional[str] = ""
    weather_impact: Optional[str] = "No"
    weather_impact_notes: Optional[str] = ""
    safety_incidents_today: Optional[str] = "No"
    injuries_reported: Optional[str] = "No"
    incident_notes: Optional[str] = ""
    safety_notified: Optional[str] = ""
    safety_contact_person: Optional[str] = ""
    safety_contact_time: Optional[str] = ""
    incident_report_filled: Optional[str] = ""
    incident_report_time: Optional[str] = ""
    general_notes: Optional[str] = ""

    masci_crews: List[Dict[str, Any]] = Field(default_factory=list)
    subcontractors: List[Dict[str, Any]] = Field(default_factory=list)
    visitors: List[Dict[str, Any]] = Field(default_factory=list)
    equipment: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    photos: List[str] = Field(default_factory=list)

    prepared_by_signature: Optional[str] = ""
    superintendent_signature: Optional[str] = ""
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


class DailyReport(DailyReportCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DailyReportSummary(BaseModel):
    id: str
    project_name: str
    project_number: str
    location: str
    report_date: str
    prepared_by: str
    weather_summary: str
    photo_count: int
    crew_count: int
    sub_count: int
    visitor_count: int
    created_at: str


def register_daily_reports_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email):
    """Attach Daily Report endpoints to the shared router."""

    @api_router.post("/daily-reports", response_model=DailyReport, dependencies=[Depends(rate_limit_public_post)])
    async def create_daily_report(payload: DailyReportCreate):
        report = DailyReport(**payload.model_dump())
        doc = report.model_dump()
        await db.daily_reports.insert_one(doc)
        doc.pop("_id", None)
        schedule_auto_email("daily-report", doc)
        return report

    @api_router.get("/daily-reports", response_model=List[DailyReportSummary])
    async def list_daily_reports(_: bool = Depends(require_admin)):
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 1000},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "report_date": 1, "prepared_by": 1,
                "weather_summary": 1, "created_at": 1,
                "photo_count":   {"$size": {"$ifNull": ["$photos", []]}},
                "crew_count":    {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":     {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count": {"$size": {"$ifNull": ["$visitors", []]}},
            }},
        ]
        docs = await db.daily_reports.aggregate(pipeline).to_list(1000)
        return [
            DailyReportSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                project_number=d.get("project_number", ""),
                location=d.get("location", ""),
                report_date=d.get("report_date", ""),
                prepared_by=d.get("prepared_by", ""),
                weather_summary=d.get("weather_summary", ""),
                photo_count=d.get("photo_count", 0) or 0,
                crew_count=d.get("crew_count", 0) or 0,
                sub_count=d.get("sub_count", 0) or 0,
                visitor_count=d.get("visitor_count", 0) or 0,
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ]

    @api_router.get("/daily-reports/next-number")
    async def next_daily_report_number(date: Optional[str] = None):
        """Return the next available DR-YYYYMMDD-NNN for the given (or today's) date."""
        d = (date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).replace("-", "")
        prefix = f"DR-{d}-"
        n = await db.daily_reports.count_documents({"report_number": {"$regex": f"^{prefix}"}})
        return {"report_number": f"{prefix}{n + 1:03d}", "prefix": prefix}

    @api_router.get("/daily-reports/{report_id}")
    async def get_daily_report(report_id: str, _: bool = Depends(require_admin)):
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Daily report not found")
        return doc

    @api_router.delete("/daily-reports/{report_id}")
    async def delete_daily_report(report_id: str, _: bool = Depends(require_admin)):
        result = await db.daily_reports.delete_one({"id": report_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Daily report not found")
        return {"deleted": True, "id": report_id}
