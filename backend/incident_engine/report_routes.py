"""Track 19.16 · Phase E · Report Intelligence Engine routes.

Additive read-only report renderer. Consumes Phase A/B/C/D data.
Never mutates anything. Zero-Drift preserved.

Routes registered:
  GET /api/incident-reports/types
  GET /api/incident-cases/{case_id}/reports/{report_type}
  GET /api/incident-cases/{case_id}/reports/{report_type}.pdf
  GET /api/incident-intelligence/digest/weekly
  GET /api/incident-intelligence/digest/weekly.pdf
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from . import reports
from .report_render import render_report_html, render_digest_html, html_to_pdf_bytes


def register_report_routes(api_router: APIRouter, db, *, require_actor) -> None:

    @api_router.get("/incident-reports/types")
    async def list_types(actor=Depends(require_actor)):
        return {
            "types": [
                {"code": k, "title": v["title"], "audience": v["audience"],
                 "sections": v["sections"],
                 "medical_privacy": v.get("medical_privacy", "hidden"),
                 "customer_facing": bool(v.get("customer_facing", False)),
                 "internal_notes": bool(v.get("internal_notes", False))}
                for k, v in reports.REPORT_DEFINITIONS.items()
            ],
        }

    @api_router.get("/incident-cases/{case_id}/reports/{report_type}.pdf")
    async def render_pdf_route(case_id: str, report_type: str,
                               actor=Depends(require_actor)):
        try:
            payload = await reports.render_report(
                db, case_id=case_id, report_type=report_type,
            )
        except LookupError as e:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": str(e)})
        except ValueError as e:
            raise HTTPException(422, detail={"code": "invalid_report_type",
                                             "detail": str(e)})
        html = render_report_html(payload)
        pdf = html_to_pdf_bytes(html)
        filename = (
            f"incident-{payload.get('case_number') or case_id}"
            f"-{report_type}.pdf"
        )
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @api_router.get("/incident-cases/{case_id}/reports/{report_type}")
    async def render_route(case_id: str, report_type: str,
                           actor=Depends(require_actor)):
        # Guard against `.pdf` routing collision — the pdf route above
        # is registered first, but path patterns can still allow this.
        if report_type.endswith(".pdf"):
            raise HTTPException(404, detail={"code": "not_found"})
        try:
            return await reports.render_report(
                db, case_id=case_id, report_type=report_type,
            )
        except LookupError as e:
            raise HTTPException(404, detail={"code": "not_found",
                                             "detail": str(e)})
        except ValueError as e:
            raise HTTPException(422, detail={"code": "invalid_report_type",
                                             "detail": str(e)})

    @api_router.get("/incident-intelligence/digest/weekly")
    async def weekly_digest(actor=Depends(require_actor)):
        return await reports.render_weekly_digest(db)

    @api_router.get("/incident-intelligence/digest/weekly.pdf")
    async def weekly_digest_pdf(actor=Depends(require_actor)):
        payload = await reports.render_weekly_digest(db)
        html = render_digest_html(payload)
        pdf = html_to_pdf_bytes(html)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="weekly-digest.pdf"',
                "X-Content-Type-Options": "nosniff",
            },
        )


__all__ = ["register_report_routes"]
