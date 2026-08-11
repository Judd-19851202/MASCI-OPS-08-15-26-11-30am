"""TRACK 15.76A · Master-Data Trust.

Continuously verify the integrity of the canonical sources that
drive operational workflows. Detects drift, missing identities,
unresolvable routes, and orphaned references **without mutating
any data** — read-only.

Returns a list of findings, each shaped::

    {
      "code":   "pm_missing_email",
      "band":   "red" | "amber",
      "count":  int,
      "summary": str,                 # operator-readable headline
      "remediation": str,             # exactly what to do
      "samples": [first 5 affected ids],
    }

Band logic:

* **RED**  — directly impacts an active workflow today (e.g. a PM
              assigned to an active job has no resolvable email,
              meaning every Daily Report on that job will fail).
* **AMBER** — drift exists but the system is guarded by a fallback
              (e.g. equipment unit_number missing on 247 inactive
              rows; dead-letter is configured).
"""
from __future__ import annotations

from typing import Any, Dict, List

from lib.synthetic_hr_filter import is_synthetic_hr


async def collect_findings(db) -> List[Dict[str, Any]]:
    """Run every drift check; return a flat list of findings."""
    findings: List[Dict[str, Any]] = []

    findings.extend(await _pm_assignment_findings(db))
    findings.extend(await _equipment_findings(db))
    findings.extend(await _employee_findings(db))
    findings.extend(await _route_findings(db))

    return findings


async def _pm_assignment_findings(db) -> List[Dict[str, Any]]:
    """PM/Co-PM resolvability against project_team_assignments
    + jobs_master fallback. RED if an *active* job has no
    resolvable email anywhere.

    TRACK 22.5A-RESTART · truth-source reconciliation:
    Uses the SAME filter as the canonical ``jobs_master.list_jobs``
    helper (see ``/app/backend/jobs_master.py::list_jobs``) so this
    audit reads exactly the same set of "active jobs" that the UI
    Admin Jobs page, ``/api/jobs``, and ``/api/admin/pm-email-coverage``
    all read. Previously this used ``is_active != False`` — a field
    that does not exist on any jobs_master row, and which failed to
    honor the ``deleted_at`` soft-delete flag, so soft-deleted test
    rows were falsely reported as production jobs missing a PM.
    """
    out: List[Dict[str, Any]] = []
    try:
        active_jobs: List[Dict[str, Any]] = []
        async for j in db.jobs_master.find(
            {
                "active": True,
                "deleted_at": {"$in": [None, ""]},
                "forensic_fixture": {"$ne": True},
            },
            {"_id": 0, "project_number": 1, "pm_email": 1},
            limit=2000,
        ):
            active_jobs.append(j)
    except Exception:
        active_jobs = []

    missing: List[str] = []
    for j in active_jobs:
        project_number = j.get("project_number")
        if not project_number:
            continue
        # Check project_team_assignments first (canonical), fall back
        # to legacy jobs_master.pm_email.
        try:
            pm_assigned = await db.project_team_assignments.count_documents({
                "project_number": project_number,
                "assignment_role": {"$in": ["pm", "co_pm"]},
                "active": True,
                "$or": [
                    {"email": {"$nin": [None, ""]}},
                    {"user_id": {"$nin": [None, ""]}},
                    {"employee_id": {"$nin": [None, ""]}},
                ],
            })
        except Exception:
            pm_assigned = 0
        if pm_assigned > 0:
            continue
        if (j.get("pm_email") or "").strip():
            continue
        missing.append(project_number)

    if missing:
        out.append({
            "code": "pm_missing_route",
            "band": "red",
            "severity": "critical",
            "count": len(missing),
            "summary": (
                f"{len(missing)} active project(s) have no resolvable "
                "PM or Co-PM email — every notification on these "
                "projects will dead-letter."
            ),
            "remediation": (
                "Open Admin → People & Access → Multi-Portal Directory "
                "and assign a PM in project_team_assignments for each "
                "project listed below. (Legacy fallback: set pm_email "
                "on the jobs_master row.)"
            ),
            "remediation_link": "/admin/people-and-access",
            "samples": missing[:10],
            "estimated_remediation_seconds": 30 * len(missing),
            "impact": (
                "Restores Daily Reports, Safety Meetings, Incidents, "
                "QA/QC, JHA, Pre-Op, and DVIR notifications for these "
                "projects."
            ),
        })
    return out


async def _equipment_findings(db) -> List[Dict[str, Any]]:
    """Equipment master integrity. AMBER if rows are missing
    unit_number (display label drift / identity risk)."""
    out: List[Dict[str, Any]] = []
    try:
        missing_un: List[str] = []
        async for e in db.equipment_master.find(
            {"$or": [{"unit_number": None}, {"unit_number": ""}]},
            {"_id": 0, "id": 1},
            limit=500,
        ):
            missing_un.append(str(e.get("id") or "")[:8])
        if missing_un:
            out.append({
                "code": "equipment_missing_unit_number",
                "band": "amber",
                "severity": "cleanup",
                "count": len(missing_un),
                "summary": (
                    f"{len(missing_un)} equipment row(s) missing canonical "
                    "unit_number — display label is being used as identity."
                ),
                "remediation": (
                    "Go to Admin → Equipment & Suppliers → Status Board "
                    "and assign a unit_number to each piece of equipment, "
                    "or remove inactive rows via the Asset Administration "
                    "→ Canonical Taxonomy review queue."
                ),
                "remediation_link": "/admin/equipment-suppliers",
                "samples": missing_un[:10],
                "estimated_remediation_seconds": 15 * min(len(missing_un), 200),
                "impact": (
                    "Data hygiene only — no live workflow is currently "
                    "blocked by this drift."
                ),
            })
    except Exception:
        pass
    return out


async def _employee_findings(db) -> List[Dict[str, Any]]:
    """Employee identity integrity. AMBER if any active employee row
    is missing the canonical employee_id field."""
    out: List[Dict[str, Any]] = []
    try:
        missing_live: List[str] = []
        missing_technical: List[str] = []
        async for e in db.employees.find(
            {"$and": [
                {
                    "$or": [
                        {"active": True},
                        {"is_active": True},
                        {
                            "$and": [
                                {"active": {"$exists": False}},
                                {"is_active": {"$exists": False}},
                            ]
                        },
                    ]
                },
                {"$or": [
                    {"employee_id": None},
                    {"employee_id": ""},
                    {"employee_id": {"$exists": False}},
                ]},
            ]},
            {
                "_id": 0,
                "id": 1,
                "name": 1,
                "preferred_name": 1,
                "email": 1,
                "employee_id": 1,
                "synthetic_record": 1,
                "hidden_from_operations": 1,
                "technical_record_classification": 1,
                "truth_visibility_scope": 1,
                "track_23_5_cert_seed": 1,
            },
            limit=200,
        ):
            label = str(e.get("name") or e.get("id") or "")[:40]
            if is_synthetic_hr(e):
                missing_technical.append(label)
            else:
                missing_live.append(label)
        missing_total = len(missing_live) + len(missing_technical)
        if missing_total:
            live_only = len(missing_live) > 0
            summary = (
                f"{len(missing_live)} active employee(s) saved without a "
                "canonical employee_id."
                if live_only
                else f"{len(missing_technical)} technical / synthetic employee row(s) are missing canonical employee_id."
            )
            if live_only and missing_technical:
                summary += f" {len(missing_technical)} technical / synthetic row(s) are also present in the audit lane."

            remediation = (
                "Open Admin → People & Access → Employee Master and assign the canonical employee_id to each live employee row below."
                if live_only
                else "No live-operations remediation required. Keep these rows in the technical audit lane, or assign a canonical employee_id only if you intend to promote them into live employee records."
            )
            remediation_link = "/admin/people-and-access" if live_only else "/admin/governance/legacy-health"
            impact = (
                "Data hygiene — no live workflow is blocked, but employee identity is at risk of drift."
                if live_only
                else "Technical-audit hygiene only — no live workflow is blocked and no operator roster is incomplete."
            )
            out.append({
                "code": "employee_missing_id",
                "band": "amber",
                "severity": "cleanup",
                "count": missing_total,
                "summary": summary,
                "remediation": remediation,
                "remediation_link": remediation_link,
                "samples": (missing_live + missing_technical)[:10],
                "estimated_remediation_seconds": 20 * min(missing_total, 100),
                "impact": impact,
                "live_count": len(missing_live),
                "technical_count": len(missing_technical),
            })
    except Exception:
        pass
    return out


async def _route_findings(db) -> List[Dict[str, Any]]:
    """Critical-route presence. RED if a critical email role has
    nowhere to send. Reads from the canonical ``email_routes``
    collection (Track 15.65 — admin-managed route catalog)."""
    out: List[Dict[str, Any]] = []
    try:
        critical_keys = {
            "COMPLIANCE_ALWAYS_CC": "Compliance Always-CC catch-all",
            "SAFETY_FORMS_TO": "Safety Forms inbox",
            "PRE_OP_FAIL_FALLBACK": "Pre-Op / DVIR fail fallback (shop manager)",
        }
        missing: List[str] = []
        for key, label in critical_keys.items():
            row = await db.email_routes.find_one(
                {"route_key": key, "enabled": True}, {"_id": 0, "to": 1}
            )
            to_list = (row or {}).get("to") or []
            if not [a for a in to_list if (a or "").strip()]:
                missing.append(label)
        # Dead-letter must be configured via env (Resend cannot route
        # to nowhere); flag separately if missing.
        import os as _os  # noqa: PLC0415
        if not (_os.environ.get("ADMIN_DEAD_LETTER_EMAIL")
                or _os.environ.get("ADMIN_DEAD_LETTER_TO")):
            missing.append("Dead-letter address (ADMIN_DEAD_LETTER_EMAIL env)")
        if missing:
            out.append({
                "code": "critical_route_missing",
                "band": "red",
                "severity": "critical",
                "count": len(missing),
                "summary": (
                    f"{len(missing)} critical email route(s) are not "
                    "configured — failures cannot be routed safely."
                ),
                "remediation": (
                    "Open Admin → Email & Routing → Auto-Routing Rules "
                    "and configure: " + "; ".join(missing) + "."
                ),
                "remediation_link": "/admin/email",
                "samples": missing,
                "estimated_remediation_seconds": 60 * len(missing),
                "impact": (
                    "Without these routes, dispatch/safety/dead-letter "
                    "failures will not reach any inbox."
                ),
            })
    except Exception:
        pass
    return out


def overall_band(findings: List[Dict[str, Any]]) -> str:
    """Roll-up: RED if any RED finding; AMBER if any AMBER; else GREEN."""
    if any(f.get("band") == "red" for f in findings):
        return "red"
    if any(f.get("band") == "amber" for f in findings):
        return "amber"
    return "green"
