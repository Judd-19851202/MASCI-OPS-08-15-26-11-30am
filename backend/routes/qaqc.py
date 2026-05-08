"""QA/QC inspection routes — concrete-form, rebar, subcontractor-work.

All three inspection types share an identical envelope (job info, photos,
signatures, sign-off) and differ only in:
  - the `inspection_kind` discriminator field
  - the per-kind checklist items the field user filled out

That structural overlap is why the 3 inspections share one Mongo
collection (`qaqc_inspections`) and one route table — same shape as how
the Site Inspection / Daily Report / Equipment Pre-Op routes are split.
"""
from __future__ import annotations

import csv as _csv
import io
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from pm_auth import compute_pm_scope


_ALLOWED_KINDS = {"concrete_form", "rebar", "subcontractor_work"}

_KIND_LABELS = {
    "concrete_form": "Concrete Form Inspection",
    "rebar": "Rebar Inspection",
    "subcontractor_work": "Subcontractor Work Inspection",
}


class QaqcChecklistItem(BaseModel):
    """One row of the checklist. `result` ∈ {pass, fail, na}."""
    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    result: str = "na"
    note: str = ""


class QaqcInspectionCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    inspection_kind: str  # concrete_form | rebar | subcontractor_work

    # Job / project info
    project_name: str
    project_number: Optional[str] = ""
    location: str
    client: Optional[str] = ""
    pm_name: Optional[str] = ""

    # Subcontractor / crew
    subcontractor_name: Optional[str] = ""
    crew_company: Optional[str] = ""

    # PM email (auto-filled from JobPicker.pm_email so the auto-email
    # pipeline can dispatch directly without re-resolving the PM)
    pm_email: Optional[str] = ""

    # Inspection
    inspection_date: str  # YYYY-MM-DD
    inspection_time: str  # HH:MM
    inspector_name: str
    inspection_type: Optional[str] = ""
    work_area: str  # required
    weather_conditions: Optional[str] = ""
    work_activity: Optional[str] = ""

    # Concrete-Form-only placement controls (validated client-side)
    mix_design: Optional[str] = ""
    yards_ordered: Optional[str] = ""
    concrete_vendor: Optional[str] = ""

    # Body
    checklist: List[QaqcChecklistItem] = Field(default_factory=list)
    inspection_notes: str = ""
    deficiencies: str = ""
    corrective_actions: str = ""

    # Photos (data-URL strings — same as other forms)
    photos: List[str] = Field(default_factory=list)
    photo_captions: List[str] = Field(default_factory=list)

    # Sign-off
    inspector_signature: str = ""
    sub_rep_name: Optional[str] = ""
    sub_rep_signature: Optional[str] = ""

    # Counts (computed on submit by the frontend; recomputed if missing)
    pass_count: Optional[int] = 0
    fail_count: Optional[int] = 0
    na_count: Optional[int] = 0


class QaqcInspection(QaqcInspectionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # QC-YYYY-NNNNN
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QaqcInspectionSummary(BaseModel):
    id: str
    inspection_kind: str
    inspection_label: str
    project_name: str
    project_number: str
    location: str
    inspection_date: str
    inspector_name: str
    subcontractor_name: str
    pm_name: str = ""
    pm_email: str = ""
    pass_count: int
    fail_count: int
    na_count: int
    photo_count: int
    created_at: str


def _label_for(kind: str) -> str:
    return _KIND_LABELS.get(kind, "QA/QC Inspection")


def _summary_from_doc(d: dict) -> QaqcInspectionSummary:
    return QaqcInspectionSummary(
        id=d.get("id", ""),
        inspection_kind=d.get("inspection_kind", ""),
        inspection_label=_label_for(d.get("inspection_kind", "")),
        project_name=d.get("project_name", ""),
        project_number=d.get("project_number", "") or "",
        location=d.get("location", ""),
        inspection_date=d.get("inspection_date", ""),
        inspector_name=d.get("inspector_name", ""),
        subcontractor_name=d.get("subcontractor_name", "") or d.get("crew_company", "") or "",
        pm_name=d.get("pm_name", "") or "",
        pm_email=(d.get("pm_email", "") or "").lower(),
        pass_count=int(d.get("pass_count") or 0),
        fail_count=int(d.get("fail_count") or 0),
        na_count=int(d.get("na_count") or 0),
        photo_count=len(d.get("photos") or []),
        created_at=d.get("created_at", ""),
    )


def register_qaqc_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email):
    """Attach the 4 QA/QC routes (POST/GET-list/GET-by-id/DELETE) plus
    admin stats + CSV export."""

    @api_router.post(
        "/qaqc-inspections",
        response_model=QaqcInspection,
        dependencies=[Depends(rate_limit_public_post)],
    )
    async def create_qaqc(payload: QaqcInspectionCreate):
        if payload.inspection_kind not in _ALLOWED_KINDS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown inspection_kind '{payload.inspection_kind}'",
            )
        # Recompute pass/fail/na counts server-side so admin trust the values
        items = payload.checklist or []
        ps = sum(1 for i in items if i.result == "pass")
        fs = sum(1 for i in items if i.result == "fail")
        na = sum(1 for i in items if i.result == "na")
        body = payload.model_dump()

        # Server-side PM backfill from jobs_master if the form didn't carry
        # one (e.g. crews on an old build, or a custom job typed in by hand).
        pn = (body.get("project_number") or "").strip()
        if pn and (not body.get("pm_email") or not body.get("pm_name")):
            try:
                job = await db.jobs_master.find_one(
                    {"project_number": pn}, {"_id": 0}
                )
                if job:
                    if not body.get("pm_name"):
                        body["pm_name"] = job.get("project_manager") or ""
                    if not body.get("pm_email"):
                        body["pm_email"] = (job.get("pm_email") or "").lower()
            except Exception:
                pass

        rec = QaqcInspection(
            **{
                **body,
                "pass_count": ps,
                "fail_count": fs,
                "na_count": na,
            }
        )
        doc = rec.model_dump()
        from doc_ids import ensure_doc_id
        await ensure_doc_id(db, doc, "QC", when=doc.get("inspection_date") or doc.get("created_at"))
        await db.qaqc_inspections.insert_one(doc)
        doc.pop("_id", None)
        # Mirror photos into the Job Photos library (Phase 1 read-only).
        try:
            from routes.job_photos import index_record_photos
            await index_record_photos(db, "qaqc", doc)
        except Exception:
            pass
        # Route to assigned PM via the existing auto-email pipeline.
        # The kind passed downstream is "qaqc" — pdf_render maps it to a
        # generic QA/QC PDF and the email subject already reads
        # "[MASCI] QA/QC … · Project … · PM: …".
        schedule_auto_email("qaqc", doc)
        return rec

    @api_router.get("/qaqc-inspections", response_model=List[QaqcInspectionSummary])
    async def list_qaqc(actor=Depends(require_admin)):
        scope = await compute_pm_scope(db, actor)
        cursor = db.qaqc_inspections.find(scope.filter({}), {"_id": 0}).sort("created_at", -1).limit(2000)
        out: List[QaqcInspectionSummary] = []
        async for d in cursor:
            out.append(_summary_from_doc(d))
        return out

    @api_router.get(
        "/pm/qaqc-inspections",
        response_model=List[QaqcInspectionSummary],
    )
    async def list_qaqc_for_pm(
        pm: str = "",
        _: bool = Depends(require_admin),
    ):
        """PM portal scoped list. Filtered to records whose
        `pm_email` (preferred) or `pm_name` matches the requested PM
        identifier. PMs share a single password (env PM_PASSWORD), so the actual
        identity is selected client-side from the active PM roster — the
        UI passes ?pm=<email-or-name>. Empty `pm` returns an empty list
        instead of all records, so the field MUST be set to see anything.
        """
        pm_q = (pm or "").strip()
        if not pm_q:
            return []
        is_email = "@" in pm_q
        if is_email:
            mongo_query = {"pm_email": pm_q.lower()}
        else:
            mongo_query = {"pm_name": pm_q}
        cursor = (
            db.qaqc_inspections.find(mongo_query, {"_id": 0})
            .sort("created_at", -1)
            .limit(2000)
        )
        out: List[QaqcInspectionSummary] = []
        async for d in cursor:
            out.append(_summary_from_doc(d))
        return out

    @api_router.get("/qaqc-inspections/{inspection_id}")
    async def get_qaqc(inspection_id: str, actor=Depends(require_admin)):
        doc = await db.qaqc_inspections.find_one({"id": inspection_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")
        return doc

    @api_router.delete("/qaqc-inspections/{inspection_id}")
    async def delete_qaqc(inspection_id: str, _: bool = Depends(require_admin)):
        result = await db.qaqc_inspections.delete_one({"id": inspection_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="QA/QC inspection not found")
        return {"deleted": True, "id": inspection_id}

    @api_router.get("/admin/qaqc-inspections/stats")
    async def qaqc_stats(actor=Depends(require_admin)):
        scope = await compute_pm_scope(db, actor)
        base = scope.filter({})
        total = await db.qaqc_inspections.count_documents(base)
        rows = []
        for k in ("concrete_form", "rebar", "subcontractor_work"):
            c = await db.qaqc_inspections.count_documents({**base, "inspection_kind": k})
            rows.append({"kind": k, "label": _label_for(k), "count": c})
        last = await db.qaqc_inspections.find_one(
            base,
            {"_id": 0, "id": 1, "inspection_kind": 1, "project_name": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        return {"total": total, "by_kind": rows, "last": last}

    @api_router.get("/admin/qaqc-inspections/export.csv")
    async def qaqc_export(actor=Depends(require_admin)):
        scope = await compute_pm_scope(db, actor)
        buf = io.StringIO()
        w = _csv.writer(buf)
        w.writerow([
            "Created At (UTC)", "Inspection", "Project Number", "Project Name",
            "Location", "Inspector", "Subcontractor", "Pass", "Fail", "N/A",
            "Photos", "Deficiencies",
        ])
        cursor = db.qaqc_inspections.find(scope.filter({}), {"_id": 0}).sort("created_at", -1)
        async for d in cursor:
            w.writerow([
                d.get("created_at", ""),
                _label_for(d.get("inspection_kind", "")),
                d.get("project_number", "") or "",
                d.get("project_name", ""),
                d.get("location", ""),
                d.get("inspector_name", ""),
                d.get("subcontractor_name", "") or d.get("crew_company", ""),
                d.get("pass_count") or 0,
                d.get("fail_count") or 0,
                d.get("na_count") or 0,
                len(d.get("photos") or []),
                (d.get("deficiencies") or "").replace("\n", " "),
            ])
        buf.seek(0)
        return Response(
            content=buf.read(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="masci-qaqc-inspections.csv"'},
        )
