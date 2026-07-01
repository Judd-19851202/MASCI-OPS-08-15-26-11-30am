"""Phase E · Report Engine routes."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from . import reports


def register_report_routes(api_router: APIRouter, db, *, require_actor) -> None:

    @api_router.get("/incident-reports/types")
    async def list_types(actor=Depends(require_actor)):
        return {"types": [{"code": k, "title": v["title"], "audience": v["audience"]}
                          for k, v in reports.REPORT_DEFINITIONS.items()]}

    @api_router.get("/incident-cases/{case_id}/reports/{report_type}")
    async def render_route(case_id: str, report_type: str, actor=Depends(require_actor)):
        try:
            return await reports.render_report(db, case_id=case_id, report_type=report_type)
        except LookupError as e:
            raise HTTPException(404, detail={"code": "not_found", "detail": str(e)})
        except ValueError as e:
            raise HTTPException(422, detail={"code": "invalid", "detail": str(e)})

    @api_router.get("/incident-intelligence/digest/weekly")
    async def weekly_digest(actor=Depends(require_actor)):
        return await reports.render_weekly_digest(db)


__all__ = ["register_report_routes"]
