"""TRACK 15.73Q · Admin PM-Email Coverage Observability.

Admin-gated, read-only endpoint that exposes the same audit shape as the
`scripts/track_15_73q_pm_email_audit.py` regression script, but live and
production-safe. Surfaces:

  * total active projects
  * projects with valid pm_email
  * projects missing pm_email
  * projects with malformed pm_email
  * projects with PM name but no email
  * projects with only co_pm_emails
  * detailed list of impacted projects sorted by recent DR count

The operator can hit this from the Routing Status Panel and immediately
see which projects need a PM email backfill. No DB access required.

No production writes. No mutation of any record. Pure read-aggregate.
"""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def make_router(db, require_admin_only_dep) -> APIRouter:
    router = APIRouter()

    @router.get("/api/admin/pm-email-coverage")
    async def pm_email_coverage(_: Any = Depends(require_admin_only_dep)):
        """Track 15.73Q · PM/Co-PM email coverage on active jobs_master rows.

        Operator-facing observability for the Daily Report PM-notification
        gap. Returns per-project status flags + summary counters.

        Read-only · admin-gated · no production writes."""
        # ---------- recent DR project counts ----------
        dr_counts: dict[str, int] = {}
        dr_latest: dict[str, str] = {}
        async for d in db.daily_reports.find({}, {"_id": 0, "project_number": 1, "report_date": 1}):
            pn = (d.get("project_number") or "").strip()
            if not pn:
                continue
            dr_counts[pn] = dr_counts.get(pn, 0) + 1
            rd = (d.get("report_date") or "").strip()
            if rd > dr_latest.get(pn, ""):
                dr_latest[pn] = rd

        # ---------- jobs_master active projects ----------
        rows: list[dict[str, Any]] = []
        counters = {
            "active_total": 0,
            "active_with_pm_email": 0,
            "active_missing_pm_email": 0,
            "active_with_pm_name_no_email": 0,
            "active_with_co_pm_email_only": 0,
            "active_total_no_pm_no_copm": 0,
            "active_malformed_pm_email": 0,
        }

        async for r in db.jobs_master.find(
            {"$or": [{"active": True}, {"active": {"$exists": False}}]},
            {"_id": 0, "project_number": 1, "project_name": 1,
             "project_manager": 1, "pm_email": 1, "co_pm_emails": 1,
             "active": 1},
        ):
            counters["active_total"] += 1
            pn = (r.get("project_number") or "").strip()
            pm_email = (r.get("pm_email") or "").strip()
            pm_name = (r.get("project_manager") or "").strip()
            co_emails = [e for e in (r.get("co_pm_emails") or []) if e and isinstance(e, str)]
            status: list[str] = []

            if pm_email and EMAIL_RE.match(pm_email):
                counters["active_with_pm_email"] += 1
                status.append("pm_email_ok")
            elif pm_email:
                counters["active_malformed_pm_email"] += 1
                status.append("pm_email_malformed")
            else:
                counters["active_missing_pm_email"] += 1
                status.append("pm_email_blank")
                if pm_name:
                    counters["active_with_pm_name_no_email"] += 1
                if co_emails:
                    counters["active_with_co_pm_email_only"] += 1
                else:
                    counters["active_total_no_pm_no_copm"] += 1

            rows.append({
                "project_number": pn,
                "project_name": r.get("project_name") or "",
                "pm_name": pm_name,
                "pm_email": pm_email,
                "co_pm_emails": co_emails,
                "recent_dr_count": dr_counts.get(pn, 0),
                "last_dr_date": dr_latest.get(pn, ""),
                "status": status,
            })

        # Sort missing-PM rows by DR impact (most active first).
        missing_rows = sorted(
            (r for r in rows if "pm_email_ok" not in r["status"]),
            key=lambda r: (-r["recent_dr_count"], r["project_number"]),
        )

        return {
            "track": "15.73Q",
            "summary": counters,
            "active_projects_total": counters["active_total"],
            "active_projects_missing_pm_email": (
                counters["active_missing_pm_email"] + counters["active_malformed_pm_email"]
            ),
            "active_projects_with_recent_drs_and_no_pm_email": sum(
                1 for r in missing_rows if r["recent_dr_count"] > 0
            ),
            "missing_rows_top_25": missing_rows[:25],
            "remediation_note": (
                "For each row in missing_rows_top_25, the operator should set "
                "jobs_master.pm_email to the authoritative PM email. The PM "
                "directory at /admin → 'Project Managers' is the source. "
                "Until backfilled, those projects' Daily Report notifications "
                "fall through to ADMIN_DEAD_LETTER_TO (no silent failure)."
            ),
        }

    return router
