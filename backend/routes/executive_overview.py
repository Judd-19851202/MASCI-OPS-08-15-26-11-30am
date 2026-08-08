"""TRACK 15.44 · Executive Overview — read-only aggregator.

Aggregates existing certified collections into 6 tiles:
  1. Jobs Requiring Attention
  2. Overdue Operational Items
  3. Staffing Issues
  4. Equipment Issues
  5. Safety Attention Items
  6. Activity Snapshot ("Is the company operating today?")

HARD RULES (per directive):
* No new collections
* No new schemas
* No new background jobs
* No analytics engines
* No forecasting
* No AI summaries
* No data warehouses

Single endpoint: GET /api/admin/executive/overview
Admin-only (uses the existing require_admin_dep).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request

from lib.corrective_action_truth import open_corrective_action_query, overdue_corrective_action_query
from lib.enterprise_governance import require_governed_action
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion

from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

logger = logging.getLogger(__name__)

_CLOSED_INCIDENT_RESOLUTION = "Closed"
def _open_incident_query(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    query: Dict[str, Any] = {"resolution_status": {"$ne": _CLOSED_INCIDENT_RESOLUTION}}
    if extra:
        query.update(extra)
    return query


def _tile_metadata(
    *,
    name: str,
    definition: str,
    sources: List[str],
    formula: Dict[str, Any],
    drilldown: str,
    owner: str,
) -> Dict[str, Any]:
    return {
        "kpi_name": name,
        "business_definition": definition,
        "source_of_truth": sources,
        "api_endpoint": "/api/admin/executive/overview",
        "formula": formula,
        "confidence": "HIGH",
        "status_reason": "Executive Overview now reuses canonical open-incident and open-corrective-action semantics used by other operational dashboards.",
        "drilldown_source": drilldown,
        "owner": owner,
        "freshness": "Point-in-time snapshot generated on request.",
    }


def _overview_metadata() -> Dict[str, Any]:
    return {
        "page": {
            "kpi_name": "Executive Overview",
            "business_definition": "Read-only executive attention surface composed from existing certified operational sources.",
            "source_of_truth": [
                "daily_reports",
                "incidents",
                "corrective_actions",
                "project_team_assignments",
                "fleet_status",
                "fleet_defects",
                "asset_holds",
            ],
            "api_endpoint": "/api/admin/executive/overview",
            "formula": {
                "tile_count": 6,
                "verdict_policy": "RED if any deterministic executive red-threshold is breached; YELLOW if only attention thresholds are breached; GREEN otherwise.",
            },
            "confidence": "HIGH",
            "status_reason": "Every tile exposes its own metadata so executives can trace the displayed value back to the source and formula.",
            "drilldown_source": "/admin/executive-overview",
            "owner": "executive-truth",
            "freshness": "Generated when the route is requested.",
        },
        "verdict": {
            "kpi_name": "Executive Verdict",
            "business_definition": "Deterministic rollup of the six executive tiles using explicit thresholds and surfaced reasons.",
            "source_of_truth": "Derived from the Executive Overview tiles",
            "api_endpoint": "/api/admin/executive/overview",
            "formula": {
                "red_thresholds": [
                    "out_of_service_units > 5",
                    "unresolved_incidents > 10",
                    "overdue_corrective_actions > 5",
                    "workplace_violence_incidents_90d > 0",
                    "training_overdue > 0",
                ],
                "yellow_thresholds": [
                    "stale_projects_no_dr_in_3d > 3",
                    "active_high_severity_asset_holds > 0",
                    "unresolved_corrective_actions > 3",
                    "public_interaction_incidents_30d > 2",
                ],
            },
            "confidence": "HIGH",
            "status_reason": "Reasons are emitted directly beside the verdict so no color is unexplained.",
            "drilldown_source": "/admin/executive-overview",
            "owner": "executive-truth",
            "freshness": "Evaluated on every request.",
        },
    }


def register(app, *, db=None, require_admin_dep=None):
    router = APIRouter()

    if db is None:
        db = getattr(app.state, "db", None)
    if db is None:
        raise RuntimeError("Executive overview requires canonical runtime database injection")

    @router.get("/api/admin/executive/overview")
    async def executive_overview(request: Request, actor=Depends(require_admin_dep)):  # noqa: ARG001
        await require_governed_action(
            db,
            actor=actor,
            action_key="executive.view",
            resource_type="executive_overview",
            resource={"id": "executive-overview", "project_number": "enterprise"},
            requested_context={"scope": "enterprise"},
            request=request,
        )
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        today_iso = now.date().isoformat()
        yesterday_iso = (now.date() - timedelta(days=1)).isoformat()
        cutoff_3d = (now - timedelta(days=3)).isoformat()
        cutoff_7d = (now - timedelta(days=7)).isoformat()

        # ───────────── Tile 6 — Activity Snapshot ─────────────
        # Source modules: daily_reports.report_date, meetings.created_at,
        # jhas.created_at, incidents.created_at, equipment_inspections.created_at
        # TRACK 28.02B · exclude synthetic/certification DRs from every
        # count/distinct on daily_reports (the executive overview is a
        # user-facing operational surface — synthetic rows would inflate
        # `daily_reports_today` and pollute `stale_projects`).
        dr_today = await db.daily_reports.count_documents(
            apply_synthetic_dr_exclusion({"report_date": today_iso})
        )
        dr_yesterday = await db.daily_reports.count_documents(
            apply_synthetic_dr_exclusion({"report_date": yesterday_iso})
        )
        meetings_today = await db.meetings.count_documents(
            {"created_at": {"$gte": today_iso}}
        )
        jhas_today = await db.jhas.count_documents(
            {"created_at": {"$gte": today_iso}}
        )
        inspections_today = await db.equipment_inspections.count_documents(
            {"created_at": {"$gte": today_iso}}
        )

        activity = {
            "daily_reports_today": dr_today,
            "daily_reports_yesterday": dr_yesterday,
            "safety_meetings_today": meetings_today,
            "jhas_today": jhas_today,
            "equipment_inspections_today": inspections_today,
            "source_modules": [
                "daily_reports", "safety.meeting", "safety.jha",
                "equipment.preop",
            ],
            "kpi_metadata": _tile_metadata(
                name="Activity Snapshot (Today)",
                definition="Same-day operational activity snapshot across daily reports, safety meetings, JHAs, and equipment inspections.",
                sources=["daily_reports", "meetings", "jhas", "equipment_inspections"],
                formula={
                    "report_day": today_iso,
                    "synthetic_daily_reports_excluded": True,
                    "activity_sum": [
                        "daily_reports_today",
                        "safety_meetings_today",
                        "jhas_today",
                        "equipment_inspections_today",
                    ],
                },
                drilldown="/daily-reports",
                owner="operations-activity",
            ),
        }

        # ───────────── Tile 2 — Overdue Operational Items ─────────────
        # Corrective actions due before now, still open
        overdue_capa = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=today_iso))
        )
        # Daily Reports cadence: projects with no DR in the last 3 days
        # (signal only — not authoritative "missing", just "needs attention")
        recent_project_set = await db.daily_reports.distinct(
            "project_number",
            apply_synthetic_dr_exclusion({"report_date": {"$gte": cutoff_3d}}),
        )
        all_active_project_set = await db.daily_reports.distinct(
            "project_number",
            apply_synthetic_dr_exclusion({"report_date": {"$gte": cutoff_7d}}),
        )
        stale_projects = sorted(
            set(p for p in all_active_project_set if p)
            - set(p for p in recent_project_set if p)
        )

        overdue = {
            "overdue_corrective_actions": overdue_capa,
            "stale_projects_no_dr_in_3d": len(stale_projects),
            "stale_projects_sample": stale_projects[:5],
            "source_modules": ["corrective_actions", "daily_reports"],
            "kpi_metadata": _tile_metadata(
                name="Overdue Operational Items",
                definition="Counts open corrective actions that are past due plus projects that have gone 3+ days without a daily report while still active in the last 7 days.",
                sources=["corrective_actions", "daily_reports"],
                formula={
                    "overdue_corrective_actions": {
                        "match": apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=today_iso)),
                    },
                    "stale_daily_reports": "active project_number in last 7 days but absent from last 3 days",
                },
                drilldown="/admin/qaqc",
                owner="executive-operations",
            ),
        }

        # ───────────── Tile 1 — Jobs Requiring Attention ─────────────
        # Compose from existing signals:
        #   - stale DR cadence (above)
        #   - active asset_holds tied to that project
        #   - open incidents in that project
        attention_jobs: Dict[str, Dict[str, Any]] = {}
        for pn in stale_projects:
            attention_jobs.setdefault(pn, {"project_number": pn, "reasons": []})
            attention_jobs[pn]["reasons"].append("No Daily Report in 3+ days")

        # Open incidents per project
        async for row in db.incidents.aggregate([
            {"$match": _open_incident_query()},
            {"$group": {"_id": "$project_number", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 25},
        ]):
            pn = row.get("_id") or ""
            if not pn:
                continue
            attention_jobs.setdefault(pn, {"project_number": pn, "reasons": []})
            attention_jobs[pn]["reasons"].append(
                f"{row.get('count')} open incident(s)"
            )

        # Active asset_holds → project rollup (via team_assignments → equipment_master if possible).
        # Cheap path: count holds in last 7d and surface top projects via daily_reports linkage.
        active_holds = await db.asset_holds.count_documents({"active": True})

        jobs = {
            "total_attention_jobs": len(attention_jobs),
            "active_asset_holds": active_holds,
            "top_jobs": list(attention_jobs.values())[:10],
            "source_modules": ["daily_reports", "safety.incidents", "asset_holds"],
            "kpi_metadata": _tile_metadata(
                name="Jobs Requiring Attention",
                definition="Distinct projects with at least one executive attention trigger from stale daily-report cadence or canonical open incidents.",
                sources=["daily_reports", "incidents", "asset_holds"],
                formula={
                    "attention_triggers": [
                        "no daily report in last 3 days for projects active in last 7 days",
                        "open incidents where resolution_status != Closed",
                    ],
                    "counted_entity": "distinct project_number",
                },
                drilldown="/admin/jobs",
                owner="executive-operations",
            ),
        }

        # ───────────── Tile 3 — Staffing Issues ─────────────
        # Active assignments without an assignee, or projects with active
        # DRs in the last 7 days that lack a primary PM/foreman.
        roles_seen_by_project: Dict[str, set] = {}
        async for row in db.project_team_assignments.aggregate([
            {"$match": {"active": True}},
            {"$group": {"_id": {"pn": "$project_number", "role": "$assignment_role"}}},
        ]):
            pn = row["_id"].get("pn") or ""
            role = row["_id"].get("role") or ""
            roles_seen_by_project.setdefault(pn, set()).add(role)

        active_projects = [p for p in all_active_project_set if p]
        missing_pm = []
        missing_foreman = []
        for pn in active_projects:
            roles = roles_seen_by_project.get(pn, set())
            if not any(r in roles for r in ("pm", "co_pm")):
                missing_pm.append(pn)
            if "foreman" not in roles:
                missing_foreman.append(pn)

        staffing = {
            "active_projects_count": len(active_projects),
            "projects_missing_pm": len(missing_pm),
            "projects_missing_pm_sample": missing_pm[:5],
            "projects_missing_foreman": len(missing_foreman),
            "projects_missing_foreman_sample": missing_foreman[:5],
            "source_modules": ["project_team_assignments", "daily_reports"],
            "kpi_metadata": _tile_metadata(
                name="Staffing Issues",
                definition="Active projects with recent daily-report activity that do not have a canonical PM/co-PM or Foreman assignment.",
                sources=["project_team_assignments", "daily_reports"],
                formula={
                    "active_project_window_days": 7,
                    "pm_roles": ["pm", "co_pm"],
                    "foreman_role": "foreman",
                },
                drilldown="/admin/jobs",
                owner="staffing-integrity",
            ),
        }

        # ───────────── Tile 4 — Equipment Issues ─────────────
        # Sources: fleet_status.status, asset_holds.active, fleet_defects open
        oos_units = await db.fleet_status.count_documents({"status": "oos"})
        monitor_units = await db.fleet_status.count_documents({"status": "monitor"})
        open_defects = await db.fleet_defects.count_documents({"status": {"$in": ["open", "Open", "in_progress"]}})
        active_asset_holds_severe = await db.asset_holds.count_documents({
            "active": True, "severity": {"$in": ["high", "critical"]},
        })

        equipment = {
            "out_of_service_units": oos_units,
            "monitor_units": monitor_units,
            "open_defects": open_defects,
            "active_high_severity_holds": active_asset_holds_severe,
            "active_asset_holds_total": active_holds,
            "source_modules": [
                "fleet_status", "fleet_defects", "asset_holds",
            ],
            "kpi_metadata": _tile_metadata(
                name="Equipment Issues",
                definition="Company-wide equipment friction combining out-of-service fleet status, open fleet defects, and high-severity asset holds.",
                sources=["fleet_status", "fleet_defects", "asset_holds"],
                formula={
                    "out_of_service_units": {"fleet_status.status": "oos"},
                    "monitor_units": {"fleet_status.status": "monitor"},
                    "open_defects": {"fleet_defects.status": ["open", "Open", "in_progress"]},
                    "active_high_severity_holds": {"asset_holds.active": True, "asset_holds.severity": ["high", "critical"]},
                },
                drilldown="/equipment",
                owner="fleet-operations",
            ),
        }

        # ───────────── Tile 5 — Safety Attention Items ─────────────
        unresolved_incidents = await db.incidents.count_documents(_open_incident_query())
        unresolved_capa = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion(open_corrective_action_query())
        )
        trench_holds_active = 0
        try:
            trench_holds_active = await db.trench_safety_holds.count_documents({
                "active": True,
            })
        except Exception:
            trench_holds_active = 0

        # TRACK 15.48 · G6 follow-up · Workplace-violence + Public-
        # Interaction visibility for leadership. Smallest additive
        # solution: TWO extra counts on the existing safety tile.
        # No new tile, no new endpoint, no new collection. Uses the
        # Track 15.47 `classifications` field on incidents — written
        # to existing `db.incidents` collection.
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        ninety_days_ago = (now - timedelta(days=90)).isoformat()
        wv_incidents_90d = 0
        public_interaction_30d = 0
        try:
            wv_incidents_90d = await db.incidents.count_documents({
                "created_at": {"$gte": ninety_days_ago},
                "$or": [
                    {"classifications": {"$in": [
                        "Workplace Violence", "Physical Assault",
                        "Weapon Displayed", "Weapon Used",
                    ]}},
                    {"physical_assault": True},
                    {"weapon_displayed": True},
                    {"weapon_used": True},
                ],
            })
            public_interaction_30d = await db.incidents.count_documents({
                "created_at": {"$gte": thirty_days_ago},
                "$or": [
                    {"classifications": {"$in": [
                        "Public Interaction", "Verbal Confrontation",
                        "Threat", "Harassment", "Physical Contact",
                    ]}},
                    {"threat_made": True},
                    {"physical_contact": True},
                ],
            })
        except Exception:
            pass

        # TRACK 15.50 · Training requalification compliance metrics.
        # Smallest additive solution: surface 3 numbers on the existing
        # safety tile — required / completed / overdue.
        training_required = 0
        training_completed = 0
        training_overdue = 0
        try:
            training_required = await db.safety_training_records.count_documents(
                {"source_incident_id": {"$nin": [None, ""]}}
            )
            training_completed = await db.safety_training_records.count_documents(
                {"source_incident_id": {"$nin": [None, ""]},
                 "status": {"$in": ["Completed", "Verified"]}}
            )
            # Tasks where the aftercare training task is past-due and
            # unfinished — proxy for incident-driven training overdue.
            training_overdue = await db.tasks.count_documents({
                "task_key": "incident.aftercare.training_14d",
                "status": {"$nin": ["Closed", "Completed"]},
                "due_at": {"$lt": now.isoformat()},
            })
        except Exception:
            pass

        safety = {
            "unresolved_incidents": unresolved_incidents,
            "unresolved_corrective_actions": unresolved_capa,
            "active_trench_safety_holds": trench_holds_active,
            "wv_incidents_90d": wv_incidents_90d,
            "public_interaction_30d": public_interaction_30d,
            "training_required": training_required,
            "training_completed": training_completed,
            "training_overdue": training_overdue,
            "source_modules": [
                "safety.incidents", "corrective_actions",
                "trench_safety.holds", "safety_training_records",
            ],
            "kpi_metadata": _tile_metadata(
                name="Safety Attention Items",
                definition="Canonical unresolved safety load across incidents, corrective actions, trench holds, workplace-violence visibility, and overdue retraining.",
                sources=["incidents", "corrective_actions", "trench_safety_holds", "safety_training_records", "tasks"],
                formula={
                    "unresolved_incidents": _open_incident_query(),
                    "unresolved_corrective_actions": apply_synthetic_corrective_action_exclusion(open_corrective_action_query()),
                    "workplace_violence_window_days": 90,
                    "public_interaction_window_days": 30,
                    "training_overdue_task_key": "incident.aftercare.training_14d",
                },
                drilldown="/safety",
                owner="safety-truth",
            ),
        }

        # ───────────── Overall health verdict ─────────────
        # Simple deterministic rollup — NO AI, NO weights model.
        # TRACK 15.46 · FR-02 · "Why RED?" — surface the deterministic
        # reasons driving the verdict so operators don't have to scan
        # all six tiles to understand the color.
        verdict_reasons: List[str] = []
        if oos_units > 5:
            verdict_reasons.append(
                f"{oos_units} units out of service (threshold > 5)",
            )
        if unresolved_incidents > 10:
            verdict_reasons.append(
                f"{unresolved_incidents} unresolved incidents (threshold > 10)",
            )
        if overdue_capa > 5:
            verdict_reasons.append(
                f"{overdue_capa} overdue corrective actions (threshold > 5)",
            )
        if len(stale_projects) > 3:
            verdict_reasons.append(
                f"{len(stale_projects)} projects with no DR in 3+ days (threshold > 3)",
            )
        if active_asset_holds_severe > 0:
            verdict_reasons.append(
                f"{active_asset_holds_severe} high-severity active asset hold(s)",
            )
        if unresolved_capa > 3 and overdue_capa <= 5:
            verdict_reasons.append(
                f"{unresolved_capa} open corrective actions (threshold > 3)",
            )
        # TRACK 15.48 · WV is always RED-grade. Any workplace-violence
        # incident in the last 90 days surfaces immediately on the
        # verdict reasons block so the executive sees it without
        # having to scan tiles.
        if wv_incidents_90d > 0:
            verdict_reasons.append(
                f"{wv_incidents_90d} workplace-violence incident(s) in last 90 days",
            )
        if public_interaction_30d > 2:
            verdict_reasons.append(
                f"{public_interaction_30d} public-interaction incidents in last 30 days (threshold > 2)",
            )
        # TRACK 15.50 · Training overdue = RED-grade. Recurrence-
        # prevention isn't done if the 14-day training is past due.
        if training_overdue > 0:
            verdict_reasons.append(
                f"{training_overdue} incident-triggered training assignment(s) overdue",
            )
        red = (
            (oos_units > 5)
            or (unresolved_incidents > 10)
            or (overdue_capa > 5)
            or (wv_incidents_90d > 0)
            or (training_overdue > 0)
        )
        amber = (
            (len(stale_projects) > 3)
            or (active_asset_holds_severe > 0)
            or (unresolved_capa > 3)
            or (public_interaction_30d > 2)
        )
        verdict = "RED" if red else ("YELLOW" if amber else "GREEN")

        return {
            "generated_at": now.isoformat(),
            "verdict": verdict,
            "verdict_reasons": verdict_reasons,
            "kpi_metadata": _overview_metadata(),
            "tiles": {
                "jobs": jobs,
                "overdue": overdue,
                "staffing": staffing,
                "equipment": equipment,
                "safety": safety,
                "activity": activity,
            },
            "foundation_version": "15.50.1",
        }

    app.include_router(router)
