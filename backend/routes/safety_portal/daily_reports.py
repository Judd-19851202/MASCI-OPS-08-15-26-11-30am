"""
Safety Portal · daily_reports.py — Phase 5 · W3 closeout.

Read-only Safety surface into the Daily Report stream. Closes the Safety
visibility gap identified in FINAL_OPERATIONAL_COMMUNICATION_VERIFICATION.md
(workflow W3) without granting Safety any write/edit authority over
daily reports.

Safety needs to see daily reports that:
  • flag a safety incident today (`safety_incidents_today` == 'Yes')
  • report injuries (`injuries_reported` == 'Yes')
  • have non-empty `incident_notes` / `safety_notified` / `incident_report_filled`

Projection deliberately omits labor/cost fields (none of Safety's business)
and trims the deep nested crew/material arrays to summary counts.

No POST · PATCH · DELETE peers. Source of truth remains in
`routes/daily_reports.py`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion


def register_daily_report_routes(
    api_router: APIRouter, db, require_safety_token,
) -> None:
    @api_router.get("/safety/daily-reports")
    async def list_safety_daily_reports(
        only_flagged: bool = Query(
            default=True,
            description="When true (default), return only reports that flagged a safety incident, injury, or filed an incident report.",
        ),
        limit: int = Query(default=100, ge=1, le=500),
        _: dict = Depends(require_safety_token),
    ):
        """Phase 5 · W3 · Safety read-only daily-report visibility.
        Defaults to flagged-only — Safety doesn't need every routine
        clean-day report, just the ones that touch their domain."""
        q: dict = {}
        if only_flagged:
            q = {"$or": [
                {"safety_incidents_today": {"$regex": "^yes$", "$options": "i"}},
                {"injuries_reported": {"$regex": "^yes$", "$options": "i"}},
                {"incident_notes": {"$exists": True, "$nin": ["", None]}},
                {"incident_report_filled": {"$exists": True, "$nin": ["", None]}},
            ]}
        pipeline = [
            {"$match": apply_synthetic_dr_exclusion(q)},
            {"$sort": {"report_date": -1, "created_at": -1}},
            {"$limit": limit},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "report_date": 1, "prepared_by": 1,
                "superintendent": 1, "weather_summary": 1,
                "safety_incidents_today": 1, "injuries_reported": 1,
                "incident_notes": 1, "safety_notified": 1,
                "safety_contact_person": 1, "safety_contact_time": 1,
                "incident_report_filled": 1, "incident_report_time": 1,
                "created_at": 1,
                "crew_count":   {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":    {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count":{"$size": {"$ifNull": ["$visitors", []]}},
            }},
        ]
        items = await db.daily_reports.aggregate(pipeline).to_list(limit)
        return {
            "ok": True,
            "items": items,
            "count": len(items),
            "filter": "flagged_only" if only_flagged else "all",
            "viewer_role": "safety",
        }
