"""OMEGA · FOCP Release 2 · TR-0001 · JHP Acknowledgement Ledger.

Additive ledger layer ON TOP OF the existing JHP/JHA infrastructure
(``db.job_hazard_files`` + ``/api/job-hazard-files/*`` + ``/jha``
public page). This module does NOT replace any existing JHP code.

What it adds:
    * ``db.jha_acknowledgements`` collection (employee-by-employee
      acknowledgement rows, keyed by employee + project + jha_file_id).
    * POST  /api/jha-acknowledgements
    * GET   /api/jha-acknowledgements/by-project/{project_number}
    * GET   /api/jha-acknowledgements/by-employee/{employee_id}
    * GET   /api/jha-acknowledgements/me  (public — for showing acked-state)
    * GET   /api/jha-acknowledgements/compliance  (admin — cross-project)

Each row schema::

    {
        "id":               "<uuid4>",
        "project_number":   "...",
        "jha_file_id":      "...",          # specific file version
        "jha_filename":     "...",          # snapshot for audit
        "employee_id":      "...",
        "employee_name":    "...",          # snapshot
        "employee_email":   "...",          # snapshot (lowercased)
        "signature":        "Typed full name",
        "locale":           "en"|"es",
        "acknowledged_at":  ISO-UTC,
        "ip":               "X-Forwarded-For first hop",
        "user_agent":       "<=240 chars",
    }

Audit twin: every ack ALSO writes a ``workflow_state_events`` row with
``workflow="jha_ack"`` (the workflow_state_events module already
declares jha_ack in its schema docstring) so the unified recovery
audit stream surfaces JHP acknowledgements alongside the 5 other
lifecycle workflows. No new audit collection is introduced.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from lib.workflow_state_events import write_state_event

logger = logging.getLogger(__name__)

JHA_ACK_COLLECTION = "jha_acknowledgements"
WORKFLOW = "jha_ack"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class JhaAcknowledgementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_number: str
    jha_file_id: str
    employee_email: Optional[str] = ""
    employee_id: Optional[str] = ""
    signature: str
    locale: Optional[str] = "en"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_meta(request: Optional[Request]) -> Dict[str, str]:
    if request is None:
        return {"ip": "", "user_agent": ""}
    try:
        ip = (
            (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
            or (request.client.host if request.client else "")
        )
    except Exception:
        ip = ""
    ua = (request.headers.get("user-agent") or "")[:240]
    return {"ip": ip, "user_agent": ua}


def _clean_locale(v: Optional[str]) -> str:
    s = (v or "").strip().lower()
    return s if s in ("en", "es") else "en"


async def _resolve_employee(db, payload: JhaAcknowledgementRequest) -> Dict[str, Any]:
    """Look up the employee by id OR email. Returns the directory doc.

    Raises HTTPException(404) when no match. The directory is the
    source of truth — we never invent an employee row here."""
    eid = (payload.employee_id or "").strip()
    email = (payload.employee_email or "").strip().lower()
    if eid:
        doc = await db.employees.find_one({"id": eid}, {"_id": 0})
        if doc:
            return doc
    if email:
        if not _EMAIL_RE.match(email):
            raise HTTPException(status_code=422, detail={"code": "employee_email_invalid"})
        doc = await db.employees.find_one(
            {"email": {"$regex": f"^{re.escape(email)}$", "$options": "i"}},
            {"_id": 0},
        )
        if doc:
            return doc
    raise HTTPException(
        status_code=404,
        detail={"code": "employee_not_found",
                "message": "No employee on file matches that id or email."},
    )


async def _resolve_jha_file(db, project_number: str, jha_file_id: str) -> Dict[str, Any]:
    """Look up the JHP file row (job_hazard_files collection). The file
    must exist AND belong to the given project_number. Returns the row
    minus _id. Raises 404 when not found / mismatched."""
    pn = (project_number or "").strip()
    fid = (jha_file_id or "").strip()
    if not pn or not fid:
        raise HTTPException(status_code=422, detail={"code": "project_or_file_missing"})
    doc = await db.job_hazard_files.find_one(
        {"id": fid}, {"_id": 0, "file_data": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "jha_file_not_found"})
    if str(doc.get("project_number") or "") != pn:
        raise HTTPException(
            status_code=422,
            detail={"code": "jha_file_project_mismatch",
                    "expected": doc.get("project_number"),
                    "received": pn},
        )
    return doc


async def ensure_indexes(db) -> None:
    """Create the index battery. Idempotent. Failures are logged but
    never block boot."""
    try:
        await db[JHA_ACK_COLLECTION].create_index("id", unique=True)
        await db[JHA_ACK_COLLECTION].create_index(
            [("project_number", 1), ("acknowledged_at", -1)],
            name="jha_ack_project_at",
        )
        await db[JHA_ACK_COLLECTION].create_index(
            [("employee_id", 1), ("acknowledged_at", -1)],
            name="jha_ack_employee_at",
        )
        await db[JHA_ACK_COLLECTION].create_index(
            [("jha_file_id", 1), ("employee_id", 1)],
            unique=True,
            name="jha_ack_file_employee_unique",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"jha_acknowledgements index: {e}")


def register_jha_acknowledgement_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin_dep,
):
    """Attach the TR-0001 acknowledgement endpoints.

    ``require_admin_dep`` is the existing admin dependency from
    server.py (Admin token only — PM tokens are NOT accepted for
    cross-project compliance reads)."""

    @api_router.post("/jha-acknowledgements")
    async def acknowledge_jha(
        request: Request,
        payload: JhaAcknowledgementRequest = Body(...),
    ) -> Dict[str, Any]:
        """Public — an employee acknowledges a specific JHP file.

        Identity proof: the request must carry either the employee_id
        or the employee_email of a directory row. We DO NOT mint new
        employees from this endpoint. Signature (typed full name) is
        required and is stored verbatim on the row."""
        sig = (payload.signature or "").strip()
        if len(sig) < 3:
            raise HTTPException(status_code=422, detail={"code": "signature_required_min3"})

        emp = await _resolve_employee(db, payload)
        jha = await _resolve_jha_file(db, payload.project_number, payload.jha_file_id)

        emp_id = str(emp.get("id") or "")
        emp_name = str(emp.get("name") or "").strip() or "Unknown"
        emp_email = str(emp.get("email") or "").strip().lower()
        existing = await db[JHA_ACK_COLLECTION].find_one(
            {"jha_file_id": str(jha.get("id") or "").strip(), "employee_id": emp_id},
            projection={"_id": 0},
        )
        if existing:
            return {
                "ok": True,
                "duplicate_prevented": True,
                "acknowledgement": existing,
            }

        meta = _request_meta(request)
        ack_id = str(uuid.uuid4())
        now = _now_iso()

        doc = {
            "id": ack_id,
            "project_number": str(jha.get("project_number") or "").strip(),
            "jha_file_id": str(jha.get("id") or "").strip(),
            "jha_filename": str(jha.get("filename") or "").strip(),
            "jha_uploaded_at": str(jha.get("uploaded_at") or "").strip(),
            "employee_id": emp_id,
            "employee_name": emp_name,
            "employee_email": emp_email,
            "signature": sig[:200],
            "locale": _clean_locale(payload.locale),
            "acknowledged_at": now,
            "ip": meta["ip"],
            "user_agent": meta["user_agent"],
        }
        from doc_ids import ensure_doc_id
        await ensure_doc_id(db, doc, "JAA", when=doc.get("acknowledged_at"))

        try:
            await db[JHA_ACK_COLLECTION].insert_one(doc.copy())
        except Exception as e:  # noqa: BLE001
            logger.error(f"jha_acknowledgements upsert failed: {e}")
            raise HTTPException(status_code=500, detail={"code": "ack_persistence_failed"})

        # Append-only audit row in workflow_state_events. Best-effort.
        await write_state_event(
            db,
            workflow=WORKFLOW,
            record_id=ack_id,
            record_doc_id=doc["jha_file_id"],
            from_state=None,
            to_state="ACKNOWLEDGED",
            actor={
                "_actor": "employee",
                "_actor_kind": "employee",
                "id": emp_id,
                "name": emp_name,
                "email": emp_email,
            },
            reason="",
            evidence={
                "project_number": doc["project_number"],
                "jha_filename": doc["jha_filename"],
                "jha_file_id": doc["jha_file_id"],
                "signature": sig[:200],
                "locale": doc["locale"],
            },
            request=request,
        )

        return {"ok": True, "acknowledgement": doc}

    @api_router.get("/jha-acknowledgements/by-doc/{doc_id}")
    async def jha_ack_by_doc_id(
        doc_id: str,
        _: Any = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        clean = (doc_id or "").strip().upper()
        if not clean:
            raise HTTPException(status_code=422, detail="doc_id required")
        ack = await db[JHA_ACK_COLLECTION].find_one(
            {"doc_id": clean},
            projection={"_id": 0},
        )
        if not ack:
            raise HTTPException(status_code=404, detail="Acknowledgement not found")
        return {"item": ack}

    @api_router.get("/jha-acknowledgements/me")
    async def my_acknowledgements(
        employee_email: Optional[str] = None,
        employee_id: Optional[str] = None,
        project_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Public — read your own acknowledgement state.

        Used by the /jha public page to render a ✓ next to plans the
        signed-in (by-email) employee has already acknowledged. Email
        is treated case-insensitively. Optional project_number narrows
        the response."""
        email = (employee_email or "").strip().lower()
        eid = (employee_id or "").strip()
        if not email and not eid:
            return {"items": [], "count": 0}

        q: Dict[str, Any] = {}
        if eid:
            q["employee_id"] = eid
        elif email:
            q["employee_email"] = email
        if project_number:
            q["project_number"] = project_number.strip()

        cursor = db[JHA_ACK_COLLECTION].find(q, {"_id": 0, "ip": 0, "user_agent": 0}).sort(
            "acknowledged_at", -1
        )
        rows = await cursor.to_list(500)
        return {"items": rows, "count": len(rows)}

    @api_router.get("/jha-acknowledgements/by-project/{project_number}")
    async def by_project(
        project_number: str,
        _: bool = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """Admin — per-project roster vs acknowledgement matrix.

        Returns every file uploaded for the project + every employee
        who has acknowledged each file. Supervisor visibility surface
        per TR-0001 directive."""
        pn = (project_number or "").strip()
        if not pn:
            raise HTTPException(status_code=422, detail={"code": "project_number_required"})

        files_cursor = db.job_hazard_files.find(
            {"project_number": pn},
            {"_id": 0, "file_data": 0},
        ).sort("uploaded_at", -1)
        files = await files_cursor.to_list(500)

        acks_cursor = db[JHA_ACK_COLLECTION].find(
            {"project_number": pn},
            {"_id": 0, "ip": 0, "user_agent": 0},
        ).sort("acknowledged_at", -1)
        acks = await acks_cursor.to_list(5000)

        # Group acknowledgements by file
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for a in acks:
            by_file.setdefault(str(a.get("jha_file_id") or ""), []).append(a)

        files_with_acks = []
        for f in files:
            fid = str(f.get("id") or "")
            files_with_acks.append({
                "file": f,
                "acknowledgements": by_file.get(fid, []),
                "ack_count": len(by_file.get(fid, [])),
            })

        return {
            "project_number": pn,
            "files": files_with_acks,
            "total_acknowledgements": len(acks),
            "total_files": len(files),
        }

    @api_router.get("/jha-acknowledgements/by-employee/{employee_id}")
    async def by_employee(
        employee_id: str,
        _: bool = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """Admin — every JHP an employee has acknowledged, newest first.

        Used by HR / Safety to verify training-equivalent attestation
        history for a single employee."""
        eid = (employee_id or "").strip()
        if not eid:
            raise HTTPException(status_code=422, detail={"code": "employee_id_required"})

        emp = await db.employees.find_one({"id": eid}, {"_id": 0})
        if not emp:
            raise HTTPException(status_code=404, detail={"code": "employee_not_found"})

        cursor = db[JHA_ACK_COLLECTION].find(
            {"employee_id": eid}, {"_id": 0, "ip": 0, "user_agent": 0}
        ).sort("acknowledged_at", -1)
        acks = await cursor.to_list(2000)
        return {
            "employee": {
                "id": emp.get("id"),
                "name": emp.get("name"),
                "email": emp.get("email"),
            },
            "acknowledgements": acks,
            "count": len(acks),
        }

    @api_router.get("/jha-acknowledgements/compliance")
    async def compliance_summary(
        _: bool = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """Admin — cross-project compliance roll-up.

        Returns one row per project_number with:
            * total uploaded JHP files
            * distinct employees who have acknowledged ANY file
            * total acknowledgement rows
            * most-recent acknowledgement timestamp
        Used by the Compliance Reporting surface per TR-0001."""
        # Files grouped by project
        files = await db.job_hazard_files.find(
            {}, {"_id": 0, "id": 1, "project_number": 1, "uploaded_at": 1}
        ).to_list(20000)
        files_by_pn: Dict[str, int] = {}
        for f in files:
            pn = str(f.get("project_number") or "")
            if pn:
                files_by_pn[pn] = files_by_pn.get(pn, 0) + 1

        # Acks grouped by project
        acks = await db[JHA_ACK_COLLECTION].find(
            {},
            {"_id": 0, "project_number": 1, "employee_id": 1, "acknowledged_at": 1},
        ).to_list(50000)
        ack_count: Dict[str, int] = {}
        ack_employees: Dict[str, set] = {}
        ack_latest: Dict[str, str] = {}
        for a in acks:
            pn = str(a.get("project_number") or "")
            if not pn:
                continue
            ack_count[pn] = ack_count.get(pn, 0) + 1
            ack_employees.setdefault(pn, set()).add(str(a.get("employee_id") or ""))
            at = str(a.get("acknowledged_at") or "")
            if at and at > ack_latest.get(pn, ""):
                ack_latest[pn] = at

        all_projects = sorted(set(files_by_pn.keys()) | set(ack_count.keys()))
        rows = [
            {
                "project_number": pn,
                "files_uploaded": files_by_pn.get(pn, 0),
                "acknowledgements": ack_count.get(pn, 0),
                "distinct_employees": len(ack_employees.get(pn, set())),
                "latest_acknowledged_at": ack_latest.get(pn, ""),
            }
            for pn in all_projects
        ]
        return {
            "projects": rows,
            "totals": {
                "projects": len(all_projects),
                "files": sum(files_by_pn.values()),
                "acknowledgements": sum(ack_count.values()),
            },
            "computed_at": _now_iso(),
        }


__all__ = [
    "register_jha_acknowledgement_routes",
    "ensure_indexes",
    "JHA_ACK_COLLECTION",
    "WORKFLOW",
]
