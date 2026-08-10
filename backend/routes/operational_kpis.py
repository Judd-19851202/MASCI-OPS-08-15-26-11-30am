"""routes/operational_kpis.py — TRACK 23.7 + TRACK 23.8 wrappers.

Route wrappers over the shared
`services.operational_kpis.aggregator.aggregate_project_kpis` spine.

    * PM       →  GET /api/pm/projects/{project_number}/operational-kpis
                  (require_admin — Admin or per-PM token; enforces
                  PmScope so PMs only see assigned projects)
    * Safety   →  GET /api/safety/projects/{project_number}/safety-kpis
                  (require_safety_or_admin — Safety-role or Admin;
                  never blocked by PM assignment)
    * Safety   →  GET /api/safety/company/safety-kpis
                  (TRACK 23.8 · company-wide safety posture across
                  active projects; require_safety_or_admin)

ABSOLUTE RULE: NO money, NO cost, NO rates, NO dollars, NO budget.
Runtime `_assert_no_cost` guard belts + braces the aggregator.
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from lib.enterprise_governance import governance_project_scope_allows

from services.operational_kpis.aggregator import (
    aggregate_project_kpis,
    _resolve_window,
)


_BANNED_EXACT_KEYS = {
    "cost", "labor_cost", "labor_spend", "spend", "dollars", "usd",
    "rate", "hourly_rate", "billing_rate", "budget", "variance_usd",
    "amount_usd", "total_cost", "unit_cost", "material_cost",
    "equipment_cost", "burden", "burdened_rate", "burden_rate",
    "payroll_cost", "cost_variance", "budget_variance",
}


def _assert_no_cost(payload: Any, path: str = "") -> None:
    """Belt-and-braces runtime guard. Refuses to ship any dollar,
    cost, rate, or budget key from either endpoint."""
    if isinstance(payload, dict):
        for k, v in payload.items():
            kl = str(k).lower()
            if kl in _BANNED_EXACT_KEYS:
                raise HTTPException(
                    status_code=500,
                    detail=f"[TRACK 23.7/23.8 CONTRACT VIOLATION] cost key {path}.{k}",
                )
            _assert_no_cost(v, f"{path}.{k}")
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            _assert_no_cost(v, f"{path}[{i}]")


def register_operational_kpis_routes(
    api_router: APIRouter,
    db,
    require_admin_dep: Callable[..., Awaitable[Any]],
    require_safety_or_admin_dep: Callable[..., Awaitable[Any]],
) -> None:

    # ---- PM (per-project, PM assignment scoped) ---------------------
    @api_router.get("/pm/projects/{project_number}/operational-kpis")
    async def pm_project_operational_kpis(
        project_number: str,
        actor=Depends(require_admin_dep),
        window: str = Query(
            default="7d",
            description="Time window: 7d · 30d · mtd · ptd",
        ),
    ) -> Dict[str, Any]:
        """PM operational KPIs — labor, equipment, materials, production,
        delays, safety, intelligence, scheduling_readiness,
        safety_sources. PMs only see assigned projects (PmScope).
        Admins see any project. NO cost data ever.
        """
        # Governance-scoped project enforcement — the canonical actor
        # context owns whether this caller is global or project-bound.
        try:
            if not await governance_project_scope_allows(db, actor, project_number):
                raise HTTPException(
                    status_code=403,
                    detail="PM is not assigned to this project",
                )
        except HTTPException:
            raise
        except Exception:
            # Scope resolution failures stay backward-compatible for
            # legacy admin sentinels while convergence continues.
            pass

        payload = await aggregate_project_kpis(
            db=db, project_number=project_number, window=window,
        )
        payload["kpi_metadata"] = _build_pm_project_kpi_metadata(
            project_number=project_number,
            window=payload["window"],
            date_from=payload.get("date_from"),
            date_to=payload.get("date_to"),
        )
        _assert_no_cost(payload)
        return payload

    # ---- Safety per-project (never blocked by PM assignment) --------
    @api_router.get("/safety/projects/{project_number}/safety-kpis")
    async def safety_project_kpis(
        project_number: str,
        actor=Depends(require_safety_or_admin_dep),
        window: str = Query(
            default="30d",
            description="Time window: 7d · 30d · mtd · ptd (Safety default 30d)",
        ),
    ) -> Dict[str, Any]:
        """Safety Portal per-project subset. Read-only. Safety-role or
        admin — never PM-assignment restricted."""
        full = await aggregate_project_kpis(
            db=db, project_number=project_number, window=window,
        )
        subset = _safety_subset(full)
        subset["kpi_metadata"] = _build_safety_project_kpi_metadata(
            project_number=project_number,
            window=subset["window"],
            date_from=subset.get("date_from"),
            date_to=subset.get("date_to"),
        )
        _assert_no_cost(subset)
        return subset

    # ---- Safety company-wide (TRACK 23.8 P0) ------------------------
    @api_router.get("/safety/company/safety-kpis")
    async def safety_company_kpis(
        actor=Depends(require_safety_or_admin_dep),
        window: str = Query(
            default="30d",
            description="Time window: 7d · 30d · mtd · ptd",
        ),
        limit_projects: int = Query(default=50, ge=1, le=200),
    ) -> Dict[str, Any]:
        """Company-wide safety posture. Aggregates the shared spine
        across every active project (jobs_master.active == True) and
        returns:

            * company totals (safety events, incidents, meetings,
              JHAs, inspections, escalation gaps, evidence count)
            * top projects by attention (safety_event_count +
              escalation_gap_count desc)
            * per-project safety subset for drilldown
            * source-classification aggregate

        NO PM-assignment restriction. Safety-role or admin only.
        No cost data. No double-counting (each source counted once
        per project; per-project totals never overlap).
        """
        date_from, date_to, canonical_window = _resolve_window(window)

        # Active projects — canonical is jobs_master.active == True.
        # Fall back to projects that have facts in the window when no
        # jobs_master row exists (legacy data path).
        active_projects: List[str] = []
        async for j in db.jobs_master.find(
            {"active": True},
            {"_id": 0, "project_number": 1, "project_name": 1},
        ):
            pn = (j.get("project_number") or "").strip()
            if pn:
                active_projects.append(pn)

        # Deduplicate + preserve alphabetical order for stable output.
        active_projects = sorted(set(active_projects))

        # Also fold in any project_number that has recorded facts in
        # the window (so a job that hasn't been added to jobs_master
        # yet still surfaces).
        q_facts: Dict[str, Any] = {"tenant_id": "masci", "is_current": True}
        if date_from or date_to:
            d: Dict[str, Any] = {}
            if date_from:
                d["$gte"] = date_from
            if date_to:
                d["$lte"] = date_to
            q_facts["date"] = d
        fact_projects = await db.operational_facts.distinct("project_id", q_facts)
        for pn in fact_projects:
            if pn and pn not in active_projects:
                active_projects.append(pn)

        # Cap the fan-out so a runaway roster can't stall the request.
        active_projects = active_projects[:limit_projects]

        # Parallel per-project rollups (safety subset only).
        rollups = await asyncio.gather(*[
            aggregate_project_kpis(db=db, project_number=pn, window=window)
            for pn in active_projects
        ]) if active_projects else []

        # Roll up company totals + per-project safety subsets.
        totals = {
            "safety_event_count": 0,
            "daily_report_safety_events": 0,
            "incident_count": 0,
            "accident_count": 0,
            "near_miss_count": 0,
            "utility_strike_count": 0,
            "injuries_reported": 0,
            "safety_contacted_yes": 0,
            "safety_contacted_no": 0,
            "escalation_gap_count": 0,
            "open_incidents": 0,
            "safety_meetings_count": 0,
            "jha_count": 0,
            "safety_inspection_count": 0,
            "trench_inspection_count": 0,
            "safety_photo_count": 0,
        }
        projects_out: List[Dict[str, Any]] = []
        source_status_counter: Dict[str, Dict[str, int]] = {}

        for pn, full in zip(active_projects, rollups):
            s = full["safety"]
            for k in totals:
                totals[k] += int(s.get(k) or 0)
            attention_score = int(
                s["safety_event_count"] + s["escalation_gap_count"]
            )
            projects_out.append({
                "project_number": pn,
                "project_name": full.get("project_name") or "",
                "safety_event_count": s["safety_event_count"],
                "incident_count": s["incident_count"],
                "near_miss_count": s["near_miss_count"],
                "escalation_gap_count": s["escalation_gap_count"],
                "safety_meetings_count": s["safety_meetings_count"],
                "jha_count": s["jha_count"],
                "safety_inspection_count": s["safety_inspection_count"],
                "trench_inspection_count": s["trench_inspection_count"],
                "safety_photo_count": s["safety_photo_count"],
                "attention_score": attention_score,
                "safety_sources": {
                    k: v["status"] for k, v in full["safety_sources"].items()
                },
                # Cross-signal (no money) so the safety row can show
                # "how much activity generated these events".
                "total_man_hours": full["labor"]["total_man_hours"],
            })
            # Aggregate source statuses so we can honestly present
            # "5 projects LIVE, 12 PARTIAL, 3 MISSING · FUTURE" per
            # source across the whole company.
            for src, meta in full["safety_sources"].items():
                bucket = source_status_counter.setdefault(
                    src, {"LIVE": 0, "PARTIAL": 0, "MISSING · FUTURE": 0},
                )
                bucket[meta["status"]] = bucket.get(meta["status"], 0) + 1

        # Top projects by attention_score desc, then safety_event_count.
        top_projects = sorted(
            projects_out,
            key=lambda r: (-r["attention_score"], -r["safety_event_count"], r["project_number"]),
        )

        # Overall status band — calm colours only when data warrants.
        if totals["escalation_gap_count"] > 0 or totals["injuries_reported"] > 0:
            company_band = "red"
        elif totals["incident_count"] > 0 or totals["near_miss_count"] > 0:
            company_band = "amber"
        else:
            company_band = "green"

        payload = {
            "window": canonical_window,
            "date_from": date_from,
            "date_to": date_to,
            "generated_at": _generated_at(),
            "contract_version": "23.8",
            "active_project_count": len(active_projects),
            "projects_with_safety_signal": sum(
                1 for r in projects_out if r["safety_event_count"] > 0
                or r["safety_meetings_count"] > 0
                or r["jha_count"] > 0
                or r["safety_inspection_count"] > 0
            ),
            "totals": totals,
            "status_band": company_band,
            "top_projects": top_projects,
            "projects": projects_out,
            "source_status_summary": source_status_counter,
            "kpi_metadata": _build_safety_company_kpi_metadata(
                window=canonical_window,
                date_from=date_from,
                date_to=date_to,
            ),
        }
        _assert_no_cost(payload)
        return payload


def _safety_subset(full: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project_number": full["project_number"],
        "project_name": full["project_name"],
        "window": full["window"],
        "date_from": full["date_from"],
        "date_to": full["date_to"],
        "generated_at": full["generated_at"],
        "contract_version": full["contract_version"],
        "safety": full["safety"],
        "safety_sources": full["safety_sources"],
        "activity_context": {
            "total_man_hours": full["labor"]["total_man_hours"],
            "unique_employee_count": full["labor"]["unique_employee_count"],
            "delay_hours_impact": full["delays"]["total_hours_impact"],
        },
    }


def _generated_at() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _build_safety_company_kpi_metadata(*, window: str, date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    return {
        "page": {
            "kpi_name": "Company Safety Posture",
            "business_definition": "Company-wide safety posture aggregated from the shared operational KPI spine across active projects.",
            "source_of_truth": ["operational_facts", "incidents", "meetings", "jhas", "inspections", "trench_excavations"],
            "api_endpoint": "/api/safety/company/safety-kpis",
            "formula": {
                "window": window,
                "date_from": date_from,
                "date_to": date_to,
                "active_projects": "jobs_master.active == True plus project_ids present in operational_facts for the same window",
            },
            "confidence": "HIGH",
            "status_reason": "The company view is a rollup of the shared per-project safety spine, not a separate calculation.",
            "drilldown_source": "/safety-portal",
            "owner": "safety-truth",
            "freshness": "Generated on request.",
        },
        "status_band": {
            "kpi_name": "Company Band",
            "business_definition": "Deterministic color band for company safety posture.",
            "formula": [
                "RED if escalation_gap_count > 0 or injuries_reported > 0",
                "AMBER if incident_count > 0 or near_miss_count > 0 and red rule not met",
                "GREEN otherwise",
            ],
        },
        "totals": {
            "safety_event_count": {
                "kpi_name": "Safety Events",
                "business_definition": "Daily-report safety events plus incident records within the selected window.",
                "formula": "daily_report_safety_events + incident_count",
            },
            "open_incidents": {
                "kpi_name": "Open Incidents",
                "business_definition": "Open incidents from the shared safety spine for the selected projects/window.",
                "formula": "Sum of per-project safety.open_incidents values from aggregate_project_kpis()",
            },
            "escalation_gap_count": {
                "kpi_name": "Escalation Gaps",
                "business_definition": "Safety events with missing safety-contact confirmation.",
                "formula": "Sum of per-project safety_contacted_no counts",
            },
        },
        "cards": {
            "injuries_accidents": {
                "kpi_name": "Injuries / Accidents",
                "business_definition": "Grouped injury, accident, and utility-strike counts from the shared safety spine.",
                "formula": "Display card shows injuries_reported / accident_count with utility_strike_count as supporting context",
            },
            "near_miss_open_incidents": {
                "kpi_name": "Near-miss / Open Incidents",
                "business_definition": "Near-miss activity shown alongside the current open-incident count for the same company rollup.",
                "formula": "Display card shows near_miss_count with open_incidents as supporting context",
            },
            "meetings_jhas_inspections": {
                "kpi_name": "Meetings / JHAs / Inspections",
                "business_definition": "Grouped operational safety activity counts for meetings, JHAs, inspections, trench inspections, and safety photos.",
                "formula": "Display card shows safety_meetings_count / jha_count / safety_inspection_count with trench_inspection_count and safety_photo_count as supporting context",
            },
        },
    }


def _build_pm_project_kpi_metadata(*, project_number: str, window: str, date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    return {
        "page": {
            "kpi_name": f"Project Operational KPIs · {project_number}",
            "business_definition": "Per-project PM operational KPI rollup from the shared operational KPI spine.",
            "source_of_truth": [
                "aggregate_project_kpis()",
                "operational_facts",
                "incidents",
                "meetings",
                "jhas",
                "inspections",
                "trench_excavations",
            ],
            "api_endpoint": f"/api/pm/projects/{project_number}/operational-kpis",
            "formula": {
                "window": window,
                "date_from": date_from,
                "date_to": date_to,
                "shared_spine": "aggregate_project_kpis()",
            },
            "confidence": "HIGH",
            "status_reason": "PM project KPIs reuse the same governed aggregation spine consumed by Safety drilldowns; no PM-only duplicate calculation is allowed.",
            "drilldown_source": f"/pm/project/{project_number}",
            "owner": "operations-control",
            "freshness": "Generated on request.",
        },
        "sections": {
            "labor": {
                "kpi_name": "Labor activity",
                "business_definition": "Crew-hour and staffing activity from governed operational facts for the selected project/window.",
            },
            "equipment": {
                "kpi_name": "Equipment activity",
                "business_definition": "Run/idle/utilization posture from governed equipment facts for the selected project/window.",
            },
            "materials": {
                "kpi_name": "Material flow",
                "business_definition": "Inbound/outbound material movement for the selected project/window from governed operational facts.",
            },
            "production": {
                "kpi_name": "Production signal",
                "business_definition": "Production units and completed work captured in the shared operational facts spine.",
            },
            "delays": {
                "kpi_name": "Delay impact",
                "business_definition": "Delay counts and hours impact from the shared operational facts spine.",
            },
            "safety": {
                "kpi_name": "Safety subset",
                "business_definition": "Project safety posture derived from the same shared spine exposed to Safety Portal consumers.",
            },
            "intelligence": {
                "kpi_name": "Operational intelligence",
                "business_definition": "Contextual signals and summaries emitted by the shared operational KPI spine.",
            },
            "scheduling_readiness": {
                "kpi_name": "Scheduling readiness",
                "business_definition": "Readiness posture bridging operational facts to schedule-oriented downstream consumers.",
            },
            "safety_sources": {
                "kpi_name": "Safety source coverage",
                "business_definition": "LIVE / PARTIAL / MISSING coverage for each project safety source used by the shared spine.",
            },
        },
    }


def _build_safety_project_kpi_metadata(*, project_number: str, window: str, date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
    return {
        "page": {
            "kpi_name": f"Project Safety KPIs · {project_number}",
            "business_definition": "Per-project safety subset from the shared operational KPI spine.",
            "source_of_truth": ["aggregate_project_kpis()", "incidents", "meetings", "jhas", "inspections", "trench_excavations"],
            "api_endpoint": f"/api/safety/projects/{project_number}/safety-kpis",
            "formula": {
                "window": window,
                "date_from": date_from,
                "date_to": date_to,
            },
            "confidence": "HIGH",
            "status_reason": "This project drilldown is the safety subset of the same shared spine used by the company rollup.",
            "drilldown_source": "/safety-portal",
            "owner": "safety-truth",
            "freshness": "Generated on request.",
        },
    }


__all__ = ["register_operational_kpis_routes"]
