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

        # TRACK 15.75A · pre-build a roster-PM index so we can reflect
        # the real PM coverage even when the legacy `jobs_master.pm_email`
        # column is blank but the Team Roster carries an active primary
        # PM. Pure additive — does not change the rules for projects
        # whose legacy column is already populated.
        roster_pm_by_pn: dict[str, str] = {}
        roster_co_pm_by_pn: dict[str, list[str]] = {}
        async for tr in db.project_team_assignments.find(
            {"assignment_role": {"$in": ["pm", "co_pm"]}, "active": True},
            {"_id": 0, "project_number": 1, "assignment_role": 1,
             "is_primary": 1, "email": 1},
        ):
            pn_tr = (tr.get("project_number") or "").strip()
            em_tr = (tr.get("email") or "").strip().lower()
            if not pn_tr or not em_tr:
                continue
            if tr.get("assignment_role") == "pm" and tr.get("is_primary"):
                roster_pm_by_pn.setdefault(pn_tr, em_tr)
            elif tr.get("assignment_role") == "co_pm":
                roster_co_pm_by_pn.setdefault(pn_tr, []).append(em_tr)

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
            roster_pm = roster_pm_by_pn.get(pn, "")
            roster_co = roster_co_pm_by_pn.get(pn, [])
            status: list[str] = []

            if pm_email and EMAIL_RE.match(pm_email):
                counters["active_with_pm_email"] += 1
                status.append("pm_email_ok")
            elif pm_email:
                counters["active_malformed_pm_email"] += 1
                status.append("pm_email_malformed")
            elif roster_pm and EMAIL_RE.match(roster_pm):
                # TRACK 15.75A · roster PM resolves the gap.
                counters["active_with_pm_email"] += 1
                status.append("pm_email_ok_via_roster")
            else:
                counters["active_missing_pm_email"] += 1
                status.append("pm_email_blank")
                if pm_name:
                    counters["active_with_pm_name_no_email"] += 1
                if co_emails or roster_co:
                    counters["active_with_co_pm_email_only"] += 1
                else:
                    counters["active_total_no_pm_no_copm"] += 1

            rows.append({
                "project_number": pn,
                "project_name": r.get("project_name") or "",
                "pm_name": pm_name,
                "pm_email": pm_email,
                "co_pm_emails": co_emails,
                "roster_pm_email": roster_pm,
                "roster_co_pm_emails": roster_co,
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
            "track": "15.75A",
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
                "TRACK 15.75A · The resolver now consults the Job Master "
                "Team Roster (project_team_assignments) when "
                "jobs_master.pm_email is blank. Projects whose roster "
                "carries an active primary PM are marked "
                "'pm_email_ok_via_roster' and route directly to that PM. "
                "Rows still listed here lack both a roster PM and a "
                "legacy pm_email — operator should assign a PM via "
                "/admin → 'Team Roster' for the project. Until "
                "backfilled, those projects' notifications fall through "
                "to ADMIN_DEAD_LETTER_TO (no silent failure)."
            ),
        }

    return router
