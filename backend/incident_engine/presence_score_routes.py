"""Track 19.37 · Presence Score routes.

Additive · read-only. One endpoint:

    GET /api/incident-cases/{case_id}/presence-score

Returns the deterministic Passive Incident-Presence Score object.
Same Safety/Admin/PM gate as every other /api/incident-cases/* endpoint.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from . import case_service
from . import workspace as ws
from .evidence import list_evidence
from .corrective_actions import list_actions
from .presence_score import compute_presence_score


def register_presence_score_routes(
    api_router: APIRouter, db, *, require_actor,
) -> None:
    @api_router.get("/incident-cases/{case_id}/presence-score")
    async def presence_score_route(
        case_id: str, actor=Depends(require_actor),
    ):
        case = await case_service.get_case(db, case_id)
        if not case:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "detail": f"case {case_id!r} not found"},
            )
        evidence = await list_evidence(db, case_id=case_id, include_withdrawn=False)
        capa = await list_actions(db, consumer_kind="incident_case",
                                  consumer_id=case_id)
        medical = await ws.list_medical(db, case_id=case_id)
        agency = await ws.list_agency(db, case_id=case_id)
        tasks = await ws.list_tasks(db, case_id=case_id)
        return compute_presence_score(
            case,
            evidence=evidence,
            capa=capa,
            medical=medical,
            agency=agency,
            tasks=tasks,
        )


__all__ = ["register_presence_score_routes"]
