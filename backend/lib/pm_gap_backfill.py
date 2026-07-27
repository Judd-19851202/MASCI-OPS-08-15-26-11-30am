from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


PROJECT_PM_RECOMMENDATIONS = {
    "22-08": {
        "email": "davidjewett@mascigc.com",
        "name": "David Jewett",
        "reason": "FDOT project; nearest verified PM coverage in active FDOT portfolio.",
    },
    "24-08": {
        "email": "davidjewett@mascigc.com",
        "name": "David Jewett",
        "reason": "FDOT project; nearest verified PM coverage in active FDOT portfolio.",
    },
    "26-04": {
        "email": "ramonrodriguez@mascigc.com",
        "name": "Ramon Rodriguez",
        "reason": "Closest active SR-5 PM coverage found in live job portfolio.",
    },
    "26-07": {
        "email": "ramonrodriguez@mascigc.com",
        "name": "Ramon Rodriguez",
        "reason": "Nearest active Volusia/Orange-area PM coverage with live route history.",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def preview_pm_gap_backfill(db: Any) -> Dict[str, Any]:
    plan: List[Dict[str, Any]] = []
    for project_number, rec in PROJECT_PM_RECOMMENDATIONS.items():
        job = await db.jobs_master.find_one(
            {
                "project_number": project_number,
                "active": True,
                "deleted_at": {"$in": [None, ""]},
                "forensic_fixture": {"$ne": True},
            },
            {"_id": 0},
        )
        if not job:
            continue
        existing = await db.project_team_assignments.find_one(
            {
                "project_number": project_number,
                "assignment_role": "pm",
                "active": True,
            },
            {"_id": 0},
        )
        if existing:
            continue
        pm_user = await db.user_directory.find_one(
            {"email": rec["email"], "disabled": {"$ne": True}},
            {"_id": 0, "id": 1, "email": 1, "name": 1, "employee_id": 1},
        )
        if not pm_user:
            continue
        plan.append(
            {
                "project_number": project_number,
                "project_name": job.get("project_name"),
                "pm_email": rec["email"],
                "pm_name": rec["name"],
                "reason": rec["reason"],
                "user_id": pm_user.get("id"),
                "employee_id": pm_user.get("employee_id") or None,
            }
        )
    return {"ok": True, "plan": plan, "count": len(plan)}


async def apply_pm_gap_backfill(db: Any) -> Dict[str, Any]:
    preview = await preview_pm_gap_backfill(db)
    applied = 0
    for row in preview["plan"]:
        ts = _now_iso()
        await db.project_team_assignments.update_one(
            {
                "project_number": row["project_number"],
                "assignment_role": "pm",
                "user_id": row["user_id"],
                "active": True,
            },
            {
                "$setOnInsert": {
                    "id": str(uuid4()),
                    "project_number": row["project_number"],
                    "user_id": row["user_id"],
                    "employee_id": row.get("employee_id"),
                    "email": row["pm_email"],
                    "display_name": row["pm_name"],
                    "assignment_role": "pm",
                    "assignment_scope": "full",
                    "is_primary": True,
                    "is_backup": False,
                    "active": True,
                    "notes": f"Auto-backfilled from pm_missing_route gap. {row['reason']}",
                    "created_at": ts,
                    "updated_at": ts,
                }
            },
            upsert=True,
        )
        await db.jobs_master.update_one(
            {"project_number": row["project_number"]},
            {
                "$set": {
                    "pm_email": row["pm_email"],
                    "project_manager": row["pm_name"],
                    "updated_at": ts,
                }
            },
        )
        applied += 1
    return {"ok": True, "count": applied, "plan": preview["plan"]}


__all__ = ["preview_pm_gap_backfill", "apply_pm_gap_backfill"]