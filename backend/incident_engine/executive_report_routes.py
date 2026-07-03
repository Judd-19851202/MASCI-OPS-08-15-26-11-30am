"""Track 19.36 · Executive Intelligence + Executive Report PDF routes.

Additive · read-only. Wired from server.py.

Endpoints
---------
GET /api/incident-cases/{case_id}/executive-intelligence
    Returns the unified Executive Intelligence Model (JSON).

GET /api/incident-cases/{case_id}/executive-report.pdf
    Returns a boardroom-grade PDF rendered from the same model.

Both routes read-only. They never mutate any collection. Existing
executive PDF endpoint (``/api/incident-cases/{id}/reports/{type}.pdf``,
Track 19.16 Phase E) is preserved untouched.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from .executive_intelligence import assemble_executive_intelligence
from .executive_report_render import render_executive_report_html
from .report_render import html_to_pdf_bytes


def register_executive_report_routes(
    api_router: APIRouter, db, *, require_actor,
) -> None:
    @api_router.get("/incident-cases/{case_id}/executive-intelligence")
    async def executive_intelligence_route(
        case_id: str, actor=Depends(require_actor),
    ):
        try:
            return await assemble_executive_intelligence(db, case_id=case_id)
        except LookupError as e:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "detail": str(e)},
            )

    @api_router.get("/incident-cases/{case_id}/executive-report.pdf")
    async def executive_report_pdf_route(
        case_id: str, actor=Depends(require_actor),
    ):
        try:
            model = await assemble_executive_intelligence(db, case_id=case_id)
        except LookupError as e:
            raise HTTPException(
                status_code=404,
                detail={"code": "not_found", "detail": str(e)},
            )
        html = render_executive_report_html(model)
        pdf = html_to_pdf_bytes(html)
        case_number = (model.get("case_ref") or {}).get("case_number") or case_id
        filename = f"executive-report-{case_number}.pdf"
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )


__all__ = ["register_executive_report_routes"]
