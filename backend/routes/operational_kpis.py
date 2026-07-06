"""routes/operational_kpis.py — TRACK 23.7 route wrappers.

Two thin wrappers over the shared
`services.operational_kpis.aggregator.aggregate_project_kpis` spine:

    * PM      →  GET /api/pm/projects/{project_number}/operational-kpis
    * Safety  →  GET /api/safety/projects/{project_number}/safety-kpis
    * Scheduling (future) → will consume the same aggregator directly.

ABSOLUTE RULE (Track 23.7): NO money, NO cost, NO rates, NO dollars,
NO budget. Both routes are read-only and return operational
production intelligence only.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from services.operational_kpis.aggregator import aggregate_project_kpis


# Sanity guard — refuses to serve a payload containing any cost/rate
# key even by accident. Belt-and-braces (the aggregator never emits
# these keys, but this guard means any future contributor who tries
# to sneak one through is caught at the boundary).
_BANNED_COST_KEYS = {
    "cost", "labor_cost", "labor_spend", "spend", "dollars", "usd",
    "rate", "hourly_rate", "billing_rate", "budget", "variance_usd",
    "amount_usd", "total_cost", "unit_cost", "material_cost",
    "equipment_cost", "burden", "burdened_rate",
}


def _assert_no_cost(payload: Any, path: str = "") -> None:
    if isinstance(payload, dict):
        for k, v in payload.items():
            if isinstance(k, str) and k.lower() in _BANNED_COST_KEYS:
                raise HTTPException(
                    status_code=500,
                    detail=f"[TRACK 23.7 CONTRACT VIOLATION] cost field {path}.{k} in response",
                )
            _assert_no_cost(v, f"{path}.{k}")
    elif isinstance(payload, list):
        for i, v in enumerate(payload):
            _assert_no_cost(v, f"{path}[{i}]")


def register_operational_kpis_routes(api_router: APIRouter, db) -> None:

    # ---- PM ---------------------------------------------------------
    @api_router.get("/pm/projects/{project_number}/operational-kpis")
    async def pm_project_operational_kpis(
        project_number: str,
        window: str = Query(
            default="7d",
            description="Time window: 7d · 30d · mtd · ptd",
        ),
    ) -> Dict[str, Any]:
        """PM operational KPIs — labor, equipment, materials, production,
        delays, safety, intelligence, scheduling_readiness,
        safety_sources. Uses the shared aggregator so Safety Portal
        and future Scheduling see the same numbers.

        No cost. No dollars. No rates. Ever.
        """
        payload = await aggregate_project_kpis(
            db=db, project_number=project_number, window=window,
        )
        _assert_no_cost(payload)
        return payload

    # ---- Safety Portal ---------------------------------------------
    @api_router.get("/safety/projects/{project_number}/safety-kpis")
    async def safety_project_kpis(
        project_number: str,
        window: str = Query(
            default="30d",
            description="Time window: 7d · 30d · mtd · ptd (Safety default 30d)",
        ),
    ) -> Dict[str, Any]:
        """Safety Portal subset of the shared aggregator — only the
        safety, safety_sources, and lightweight project metadata.
        Prevents Safety Portal from re-deriving different numbers."""
        full = await aggregate_project_kpis(
            db=db, project_number=project_number, window=window,
        )
        subset = {
            "project_number": full["project_number"],
            "project_name": full["project_name"],
            "window": full["window"],
            "date_from": full["date_from"],
            "date_to": full["date_to"],
            "generated_at": full["generated_at"],
            "contract_version": full["contract_version"],
            "safety": full["safety"],
            "safety_sources": full["safety_sources"],
            # Cross-signal: safety pros want to know how much
            # activity generated these safety events. Man-hours +
            # delay-impact are the only two non-safety numbers
            # exposed here, and neither is a cost.
            "activity_context": {
                "total_man_hours": full["labor"]["total_man_hours"],
                "unique_employee_count": full["labor"]["unique_employee_count"],
                "delay_hours_impact": full["delays"]["total_hours_impact"],
            },
        }
        _assert_no_cost(subset)
        return subset


__all__ = ["register_operational_kpis_routes"]
