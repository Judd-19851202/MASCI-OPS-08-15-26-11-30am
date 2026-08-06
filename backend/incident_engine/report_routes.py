"""Track 19.16 · Phase E · Report Intelligence Engine routes.

Additive read-only report renderer. Consumes Phase A/B/C/D data.
Never mutates anything. Zero-Drift preserved.

Routes registered:
  GET /api/incident-reports/types
  GET /api/incident-cases/{case_id}/reports/{report_type}
  GET /api/incident-cases/{case_id}/reports/{report_type}.pdf
  GET /api/incident-intelligence/digest/weekly
  GET /api/incident-intelligence/digest/weekly.pdf

TRACK 19.16 · UX Hardening Batch 1 (additive, read-only):
  GET /api/incident-intelligence/weather?lat=&lng=
  GET /api/incident-intelligence/project-context/{project_number}
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from . import reports
from .report_render import render_report_html, render_digest_html, html_to_pdf_bytes
from .weather import fetch_current_weather
from .fleet_crosslink import list_incidents_by_unit


def register_report_routes(api_router: APIRouter, db, *, require_actor, require_field_actor=None) -> None:

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

    # ── UX Hardening Batch 1 · Weather auto-fetch ────────────────────
    @api_router.get("/incident-intelligence/weather")
    async def weather_lookup(
        lat: float = Query(..., ge=-90, le=90),
        lng: float = Query(..., ge=-180, le=180),
    ):
        try:
            return await fetch_current_weather(lat, lng)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail={"code": "weather_unavailable",
                        "detail": str(e)[:200]},
            )

    # ── UX Hardening Batch 1 · Project auto-fill ─────────────────────
    @api_router.get("/incident-intelligence/project-context/{project_number}")
    async def project_context(
        project_number: str,
    ):
        """Read the canonical `jobs_master` row + last-known super
        for a project so the incident form can auto-fill without asking
        the crew to type anything."""
        pn = (project_number or "").strip()
        if not pn:
            raise HTTPException(422, detail={"code": "project_number_required"})
        row = await db.jobs_master.find_one({"project_number": pn}, {"_id": 0})
        if not row:
            raise HTTPException(404, detail={"code": "project_not_found",
                                             "project_number": pn})
        # Optional: last DR-known superintendent as fallback.
        super_name = ""
        try:
            latest = await db.daily_reports.find_one(
                {"project_number": pn,
                 "superintendent": {"$nin": ["", None]}},
                {"_id": 0, "superintendent": 1},
                sort=[("created_at", -1)],
            )
            if latest:
                super_name = latest.get("superintendent") or ""
        except Exception:
            pass
        return {
            "project_number":    row.get("project_number") or pn,
            "project_name":      row.get("project_name") or "",
            "location":          row.get("location") or "",
            "client":            row.get("client") or "",
            "project_manager":   row.get("project_manager") or "",
            "pm_email":          row.get("pm_email") or "",
            "co_pm_emails":      row.get("co_pm_emails") or [],
            "superintendent":    super_name,
            "active":            bool(row.get("active", True)),
        }

    # ── Closeout · Fleet / Equipment cross-link (read-only) ──────────
    @api_router.get("/equipment-status-board/incidents-by-unit")
    async def incidents_by_unit(
        unit: Optional[str] = Query(default=None,
                                    description="Comma-separated unit_numbers."),
        actor=Depends(require_actor),
    ):
        unit_numbers = None
        if unit:
            unit_numbers = [u.strip() for u in unit.split(",") if u.strip()]
        data = await list_incidents_by_unit(db, unit_numbers=unit_numbers)
        return {"by_unit": data, "unit_count": len(data)}


__all__ = ["register_report_routes"]
