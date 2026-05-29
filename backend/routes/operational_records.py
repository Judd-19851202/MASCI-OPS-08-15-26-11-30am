"""
routes/operational_records.py — Phase V.1 · M1 · Unified Read Projector.

Doctrine:
  /app/memory/M1_OPTION_C_IMPLEMENTATION_PLAN.md
  /app/memory/UNIFIED_RECORDS_PROJECTOR_CERTIFICATION.md
  /app/memory/LEGACY_RECORD_FREEZE_CERTIFICATION.md
  /app/memory/ARCHIVE_VISUAL_TREATMENT_STANDARD.md

Mission · "The user should not need to understand legacy systems,
migrations, or record substrates. One search. One timeline. One
records dashboard."

Contract surfaces (read-only · zero mutation):
  GET /api/operational-records
       Unified list across two substrates (`odr` + frozen `daily_reports`).
       Each row carries `record_kind` ∈ {odr, legacy_daily_report}
       and `archive: bool`.

  GET /api/operational-records/resolve/{doc_id}
       doc_id router. Routes `DR-*` → legacy viewer, `ODR-*` → ODR viewer.

This module **never writes** to either collection. It is a strict
projection layer over the two underlying schemas.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ── Doc id routing ───────────────────────────────────────────────────


_ODR_DOC_ID = re.compile(r"^ODR-\d{4}-\d{5}$")
_DR_DOC_ID = re.compile(r"^DR-\d{4}-\d{5}$")


def classify_doc_id(doc_id: str) -> str:
    """Return the substrate that owns a doc_id.

    Returns one of:
      - 'odr'                   for ODR-YYYY-NNNNN
      - 'legacy_daily_report'   for DR-YYYY-NNNNN (historical archive)
      - 'unknown'               otherwise
    """
    if not isinstance(doc_id, str):
        return "unknown"
    s = doc_id.strip()
    if _ODR_DOC_ID.match(s):
        return "odr"
    if _DR_DOC_ID.match(s):
        return "legacy_daily_report"
    return "unknown"


# ── Unified envelope (subset shared by both substrates) ──────────────


class OperationalRecord(BaseModel):
    """Read-only normalized envelope for the unified records dashboard.

    The shape is the **intersection** of fields available on both
    substrates. ODR-only fields (audience projection, amendments,
    audit trail) are NEVER added to legacy rows — `archive: True`
    rows leave them null.
    """
    model_config = ConfigDict(extra="forbid")

    record_kind: str = Field(..., pattern="^(odr|legacy_daily_report)$")
    archive: bool
    id: str
    doc_id: str
    project_number: str = ""
    project_name: str = ""
    report_date: str = ""
    foreman_name: str = ""
    superintendent_name: str = ""
    photo_count: int = 0
    crew_count: int = 0
    has_foreman_signature: bool = False
    has_superintendent_signature: bool = False
    status: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    # Routing hint for the frontend (no behavioral coupling).
    viewer_route: str = ""


class OperationalRecordsList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[OperationalRecord]
    counts: Dict[str, int]


class OperationalRecordResolve(BaseModel):
    model_config = ConfigDict(extra="forbid")
    doc_id: str
    record_kind: str
    record_id: Optional[str] = None
    archive: bool
    viewer_route: str


# ── Projection helpers (zero mutation) ───────────────────────────────


def _project_legacy(row: Dict[str, Any]) -> Dict[str, Any]:
    """Project a frozen `daily_reports` row into the unified shape.
    Never mutates the input dict."""
    return {
        "record_kind": "legacy_daily_report",
        "archive": True,
        "id": row.get("id", ""),
        "doc_id": row.get("doc_id", "") or "",
        "project_number": row.get("project_number", "") or "",
        "project_name": row.get("project_name", "") or "",
        "report_date": row.get("report_date", "") or "",
        "foreman_name": row.get("prepared_by", "") or "",
        "superintendent_name": row.get("superintendent", "") or "",
        "photo_count": len(row.get("photos") or []),
        "crew_count": len(row.get("masci_crews") or []),
        "has_foreman_signature": bool(row.get("prepared_by_signature")),
        "has_superintendent_signature": bool(row.get("superintendent_signature")),
        "status": "archived",
        "submitted_at": None,
        "created_at": row.get("created_at"),
        "viewer_route": f"/daily-reports/{row.get('id', '')}",
    }


def _project_odr(row: Dict[str, Any]) -> Dict[str, Any]:
    """Project an ODR row into the unified shape. Never mutates input."""
    proj = row.get("project") or {}
    crew = row.get("crew_profile") or {}
    sig_blk = (row.get("signature") or {}).get("foreman_acknowledgement") or {}
    return {
        "record_kind": "odr",
        "archive": False,
        "id": row.get("id", ""),
        "doc_id": row.get("doc_id", "") or "",
        "project_number": proj.get("project_number", "") or "",
        "project_name": proj.get("project_name", "") or "",
        "report_date": proj.get("report_date", "") or "",
        "foreman_name": proj.get("foreman_name", "") or "",
        "superintendent_name": proj.get("superintendent_name", "") or "",
        "photo_count": len(row.get("photos") or []),
        "crew_count": 1 if crew.get("crew_id") else 0,
        "has_foreman_signature": bool(sig_blk.get("acknowledged")),
        "has_superintendent_signature": False,  # ODR is foreman-attested
        "status": row.get("status"),
        "submitted_at": row.get("submitted_at"),
        "created_at": row.get("created_at"),
        "viewer_route": f"/odr/{row.get('id', '')}",
    }


# ── Router factory ───────────────────────────────────────────────────


def build_operational_records_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:

    router = APIRouter(
        prefix="/api/operational-records",
        tags=["operational-records"],
    )

    @router.get("", response_model=OperationalRecordsList)
    async def list_records(
        project_number: Optional[str] = Query(default=None),
        report_date: Optional[str] = Query(default=None),
        kind: Optional[str] = Query(
            default=None,
            description="Filter by substrate. One of: odr, legacy_daily_report.",
        ),
        limit: int = Query(default=200, ge=1, le=1000),
        actor: Dict[str, Any] = Depends(require_actor),  # noqa: ARG001
    ) -> OperationalRecordsList:
        """Unified list across ODR + frozen Daily Reports.

        Doctrine: read-only · two-substrate projection · zero mutation.
        Each row exposes `record_kind` and `archive` so the frontend
        can render the calm "ARCHIVED DAILY REPORT" treatment per
        ARCHIVE_VISUAL_TREATMENT_STANDARD.md.
        """
        if kind and kind not in ("odr", "legacy_daily_report"):
            raise HTTPException(
                422,
                "kind must be one of: odr, legacy_daily_report",
            )

        items: List[OperationalRecord] = []

        # ── Legacy substrate ─────────────────────────────────────────
        if kind in (None, "legacy_daily_report"):
            q: Dict[str, Any] = {}
            if project_number:
                q["project_number"] = project_number
            if report_date:
                q["report_date"] = report_date
            cur = db.daily_reports.find(q, {"_id": 0}).sort(
                "report_date", -1,
            ).limit(limit)
            async for row in cur:
                projected = _project_legacy(row)
                items.append(OperationalRecord(**projected))

        # ── ODR substrate ────────────────────────────────────────────
        if kind in (None, "odr"):
            q = {}
            if project_number:
                q["project.project_number"] = project_number
            if report_date:
                q["project.report_date"] = report_date
            cur = db.odr.find(q, {"_id": 0}).sort(
                "project.report_date", -1,
            ).limit(limit)
            async for row in cur:
                projected = _project_odr(row)
                items.append(OperationalRecord(**projected))

        # Sort the merged list newest-date-first; stable secondary by
        # created_at to disambiguate same-date entries.
        items.sort(
            key=lambda r: (r.report_date or "", r.created_at or ""),
            reverse=True,
        )
        # Apply unified limit AFTER merge to preserve "newest N across
        # both substrates" semantics.
        if len(items) > limit:
            items = items[:limit]

        # Counts reflect the actual returned slice — never the
        # pre-merge totals — so the dashboard's badge math stays honest.
        odr_count = sum(1 for r in items if r.record_kind == "odr")
        legacy_count = sum(1 for r in items if r.record_kind == "legacy_daily_report")

        return OperationalRecordsList(
            items=items,
            counts={
                "total": len(items),
                "odr": odr_count,
                "legacy_daily_report": legacy_count,
            },
        )

    @router.get(
        "/resolve/{doc_id}",
        response_model=OperationalRecordResolve,
    )
    async def resolve_doc_id(
        doc_id: str,
        actor: Dict[str, Any] = Depends(require_actor),  # noqa: ARG001
    ) -> OperationalRecordResolve:
        """Route a doc_id to the correct viewer.

          DR-YYYY-NNNNN  → legacy viewer (`/daily-reports/<id>`)
          ODR-YYYY-NNNNN → ODR viewer (`/odr/<id>`)

        Users never need to know which substrate owns a record. Calm
        archive treatment is rendered downstream by the frontend.
        """
        kind = classify_doc_id(doc_id)
        if kind == "unknown":
            raise HTTPException(
                422,
                f"Unknown doc_id format: {doc_id} "
                "(expected ODR-YYYY-NNNNN or DR-YYYY-NNNNN)",
            )

        if kind == "odr":
            row = await db.odr.find_one({"doc_id": doc_id}, {"_id": 0, "id": 1})
            if not row:
                raise HTTPException(404, f"ODR not found: {doc_id}")
            return OperationalRecordResolve(
                doc_id=doc_id,
                record_kind="odr",
                record_id=row["id"],
                archive=False,
                viewer_route=f"/odr/{row['id']}",
            )

        # legacy_daily_report
        row = await db.daily_reports.find_one(
            {"doc_id": doc_id}, {"_id": 0, "id": 1}
        )
        if not row:
            raise HTTPException(404, f"Daily Report not found: {doc_id}")
        return OperationalRecordResolve(
            doc_id=doc_id,
            record_kind="legacy_daily_report",
            record_id=row["id"],
            archive=True,
            viewer_route=f"/daily-reports/{row['id']}",
        )

    return router


__all__ = ["build_operational_records_router", "classify_doc_id"]
