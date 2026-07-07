"""TRACK 23.10-B · Qualifications Engine HTTP surface.

Read endpoints (any authenticated portal token):
  * GET  /api/employees/qualifications                 active list
  * GET  /api/employees/qualifications/summary         counts per type
  * GET  /api/employees/{employee_id}/qualifications   employee detail
  * GET  /api/employees/competent-persons              legacy alias (COMPETENT_PERSON)

Write endpoints (HR / Safety-Training-admin / Admin):
  * POST   /api/hr/qualifications                      create
  * PATCH  /api/hr/qualifications/{id}                 update
  * POST   /api/hr/qualifications/{id}/suspend         { reason }
  * POST   /api/hr/qualifications/{id}/revoke          { reason }
  * POST   /api/hr/qualifications/{id}/reinstate       { reason }
  * POST   /api/hr/qualifications/{id}/renew           { expiration_date, ... }

All writes:
  * Require the HR / Safety-Training-admin / Admin gate.
  * Append to `verification_status_history[]` on the row.
  * Emit `qualification_certification_fact` via ODS spine.
  * Write an audit entry to `db.hr_audit`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from services.certifications.qualification_registry import (
    COLL,
    list_active_qualifications,
    resolve_active_for_employee,
    get_qualification_snapshot,
    list_employee_qualifications,
    qualification_summary,
    is_active,
)
from services.certifications.qualification_types import (
    QUALIFICATION_ENGINE_TYPES,
    QUALIFICATION_STATUS,
    is_engine_type,
    validate_type_metadata,
    validate_status,
    TYPE_METADATA_SPEC,
)
from services.certifications.qualification_facts import (
    emit_qualification_certification_fact,
)


# ─── Pydantic bodies ────────────────────────────────────────────────
class QualificationCreate(BaseModel):
    employee_id: str = Field(..., min_length=1)
    employee_master_id: Optional[str] = None
    employee_name: Optional[str] = ""
    qualification_type: str = Field(..., min_length=1)
    completed_date: str = Field(..., min_length=10, max_length=10)
    expiration_date: Optional[str] = None
    issuing_organization: Optional[str] = ""
    issued_by: Optional[str] = ""
    instructor: Optional[str] = ""
    instructor_company: Optional[str] = ""
    training_hours: Optional[float] = None
    training_standard: Optional[str] = ""
    jurisdiction: Optional[str] = ""
    certificate_number: Optional[str] = ""
    certificate_file_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = ""
    type_metadata: Optional[Dict[str, Any]] = None
    training_name: Optional[str] = None


class QualificationUpdate(BaseModel):
    expiration_date: Optional[str] = None
    issuing_organization: Optional[str] = None
    issued_by: Optional[str] = None
    instructor: Optional[str] = None
    instructor_company: Optional[str] = None
    training_hours: Optional[float] = None
    training_standard: Optional[str] = None
    jurisdiction: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_file_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    type_metadata: Optional[Dict[str, Any]] = None
    training_name: Optional[str] = None


class QualificationReasonBody(BaseModel):
    reason: str = Field(..., min_length=2)


class QualificationRenewBody(BaseModel):
    expiration_date: str = Field(..., min_length=10, max_length=10)
    completed_date: Optional[str] = None
    certificate_number: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    reason: Optional[str] = "renewal"


class QualificationAttachmentBody(BaseModel):
    """Track 24.2 · P1 attachment upload contract.

    * `filename`     — original filename, preserved verbatim on the
      metadata (never used as a disk path).
    * `content_type` — MIME. Only ALLOWED_CT below is accepted.
    * `data_base64`  — base64-encoded bytes. Enforced ≤ 15 MB before
      decode + magic-byte validation after.
    * `document_kind`— caller-supplied taxonomy (certificate, wallet_card,
      sign_in_sheet, transcript, roster, practical_evaluation, other).
    * `notes`        — free-text operator note.
    """
    filename: str = Field(..., min_length=1, max_length=200)
    content_type: str = Field(..., min_length=3, max_length=200)
    data_base64: str = Field(..., min_length=4)
    document_kind: Optional[str] = "certificate"
    notes: Optional[str] = ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_tuple(user: Dict[str, Any]) -> Dict[str, str]:
    return {
        "actor_id": user.get("id") or user.get("email") or "",
        "actor_email": user.get("email") or "",
        "actor_name": user.get("name") or user.get("email") or "",
        "actor_role": (user.get("_actor") or user.get("role") or "hr").lower(),
    }


async def _write_audit(db, row: Dict[str, Any], action: str, before: Optional[Dict[str, Any]], after: Dict[str, Any], user: Dict[str, Any]):
    actor = _actor_tuple(user)
    await db.hr_audit.insert_one({
        "id": str(uuid.uuid4()),
        "kind": "qualification",
        "action": action,
        "qualification_id": row.get("id"),
        "qualification_type": row.get("qualification_type") or row.get("certification_type"),
        "employee_id": row.get("employee_id"),
        "before": before,
        "after": after,
        "at": _now(),
        **actor,
    })


def _append_history(row: Dict[str, Any], status: str, user: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    hist = list(row.get("verification_status_history") or [])
    actor = _actor_tuple(user)
    hist.append({
        "status": status,
        "at": _now(),
        "actor_id": actor["actor_id"],
        "actor_role": actor["actor_role"],
        "reason": reason or "",
    })
    return {"verification_status_history": hist}


# ─── Router builder ─────────────────────────────────────────────────
def build_qualifications_router(
    db,
    require_read_dep,
    require_write_dep,
) -> APIRouter:
    """Build the qualifications router.

    * `require_read_dep`  — resolves ANY authenticated portal token
      (multi-portal). Registry reads are enterprise-wide readable.
    * `require_write_dep` — HR / Safety (Training admin) / Admin gate.
      Field / PM / Trench / DR / Scheduling tokens are REJECTED.
    """
    r = APIRouter(prefix="/api", tags=["qualifications"])

    # ── Types metadata (public read) ───────────────────────────────
    @r.get("/employees/qualifications/types")
    async def list_types(_: dict = Depends(require_read_dep)):
        return {
            "types": list(QUALIFICATION_ENGINE_TYPES),
            "statuses": list(QUALIFICATION_STATUS),
            "type_metadata_spec": {
                k: {"required": list(v.get("required") or ()),
                    "optional": list(v.get("optional") or ())}
                for k, v in TYPE_METADATA_SPEC.items()
            },
        }

    # ── Active registry list ───────────────────────────────────────
    @r.get("/employees/qualifications")
    async def get_qualifications(
        type: str,                                              # noqa: A002
        active: bool = True,
        warning_days: int = 30,
        _: dict = Depends(require_read_dep),
    ):
        if not is_engine_type(type):
            raise HTTPException(400, f"unknown qualification_type: {type}")
        if not active:
            # `active=false` = admin-only listing of ALL rows for the
            # type. Field consumers must never see non-active rows.
            raise HTTPException(
                403,
                "Non-active qualification listings are HR / admin only.",
            )
        rows = await list_active_qualifications(
            db, qualification_type=type, warning_days=warning_days,
        )
        return {"type": type, "warning_days": warning_days,
                "count": len(rows), "items": rows}

    # ── Legacy alias (Competent Person) ────────────────────────────
    # Track 24.1 · P0-2: this is now the ONE-AND-ONLY handler for
    # `/api/employees/competent-persons`. The duplicate registration
    # in `routes.trench_safety.competent_persons` was removed so the
    # auth gate below actually fires. The response items include BOTH
    # the raw registry keys (for the DR V3 CompetentPersonCombo) AND
    # the legacy trench_safety shape (for the trench EmployeePicker)
    # so downstream consumers keep working unchanged.
    @r.get("/employees/competent-persons")
    async def get_competent_persons(
        active: bool = True,
        warning_days: int = 30,
        _: dict = Depends(require_read_dep),
    ):
        if not active:
            raise HTTPException(403, "HR / admin only.")
        rows = await list_active_qualifications(
            db, qualification_type="COMPETENT_PERSON",
            warning_days=warning_days,
        )
        # Emit the strict superset of both consumer shapes.  New code
        # should read qualification_id / employee_name / employee_trade
        # / employee_crew / expires_at; legacy trench code reads
        # id / name / role / trade / crew / cp_approval_date /
        # cp_expiration_date / cp_approved_by.
        items = []
        for r_ in rows:
            items.append({
                # ── Raw registry shape (Track 23.10-B / DR V3 combo) ──
                "qualification_id": r_.get("qualification_id"),
                "qualification_type": r_.get("qualification_type"),
                "employee_id": r_.get("employee_id") or "",
                "employee_name": r_.get("employee_name") or "",
                "employee_trade": r_.get("employee_trade") or "",
                "employee_crew": r_.get("employee_crew") or "",
                "verification_status": r_.get("verification_status"),
                "issued_at": r_.get("issued_at") or "",
                "expires_at": r_.get("expires_at") or "",
                "issuing_organization": r_.get("issuing_organization") or "",
                "expires_in_days": r_.get("expires_in_days"),
                "warning": r_.get("warning"),
                # ── Legacy trench_safety shape (EmployeePicker) ─────
                "id": r_.get("employee_id") or "",
                "name": r_.get("employee_name") or "",
                "role": r_.get("employee_trade") or "",
                "trade": r_.get("employee_trade") or "",
                "crew": r_.get("employee_crew") or "",
                "cp_approval_date": r_.get("issued_at") or "",
                "cp_expiration_date": r_.get("expires_at") or "",
                "cp_approved_by": r_.get("issuing_organization") or "",
            })
        items.sort(key=lambda x: (x.get("employee_name") or "").lower())
        return {"type": "COMPETENT_PERSON",
                "warning_days": warning_days,
                "count": len(items), "items": items}

    # ── TRACK 24.9 · Public-safe Competent Person projection ───────
    # Anonymous DR V3 (`/daily/new`) needs to load the active CP
    # registry so foremen can complete the excavation section. The
    # authenticated endpoints above 401 for anonymous users. This
    # public projection returns ONLY the fields required for
    # selection safety — no PII, no email, no phone, no address.
    # Lock test enforces the allowed key set.
    _CP_PUBLIC_ALLOWED_KEYS = frozenset({
        "qualification_id", "qualification_type",
        "employee_name", "employee_trade", "employee_crew",
        "verification_status", "expires_at", "warning",
    })

    @r.get("/employees/competent-persons/public")
    async def get_competent_persons_public(warning_days: int = 30):
        """Public-safe Competent Person registry for anonymous DR V3.

        Returns ONLY active CPs. Whitelisted projection. No PII.
        """
        rows = await list_active_qualifications(
            db, qualification_type="COMPETENT_PERSON",
            warning_days=max(0, min(int(warning_days or 30), 90)),
        )
        items: List[Dict[str, Any]] = []
        for r_ in rows:
            row = {
                "qualification_id": r_.get("qualification_id") or "",
                "qualification_type": r_.get("qualification_type") or "COMPETENT_PERSON",
                "employee_name": r_.get("employee_name") or "",
                "employee_trade": r_.get("employee_trade") or "",
                "employee_crew": r_.get("employee_crew") or "",
                "verification_status": r_.get("verification_status") or "",
                "expires_at": r_.get("expires_at") or "",
                "warning": bool(r_.get("warning")),
            }
            # Enforce whitelist at emit-time (defense-in-depth).
            filtered = {k: v for k, v in row.items() if k in _CP_PUBLIC_ALLOWED_KEYS}
            items.append(filtered)
        items.sort(key=lambda x: (x.get("employee_name") or "").lower())
        return {
            "type": "COMPETENT_PERSON",
            "warning_days": warning_days,
            "count": len(items),
            "items": items,
            "contract_version": "24.9-public",
            "public": True,
        }

    # ── Summary (dashboards) ───────────────────────────────────────
    @r.get("/employees/qualifications/summary")
    async def get_summary(
        type: str,                                              # noqa: A002
        warning_days: int = 30,
        _: dict = Depends(require_read_dep),
    ):
        if not is_engine_type(type):
            raise HTTPException(400, f"unknown qualification_type: {type}")
        return await qualification_summary(
            db, qualification_type=type, warning_days=warning_days,
        )

    # ── Per-employee list ──────────────────────────────────────────
    @r.get("/employees/{employee_id}/qualifications")
    async def get_employee_qualifications(
        employee_id: str,
        type: Optional[str] = None,                             # noqa: A002
        include_history: bool = False,
        _: dict = Depends(require_read_dep),
    ):
        if type and not is_engine_type(type):
            raise HTTPException(400, f"unknown qualification_type: {type}")
        rows = await list_employee_qualifications(
            db, employee_id=employee_id,
            include_history=include_history,
            qualification_type=type,
        )
        return {"employee_id": employee_id, "count": len(rows),
                "items": rows}

    # ── Snapshot (historical embedding) ────────────────────────────
    @r.get("/hr/qualifications/{qualification_id}/snapshot")
    async def get_snapshot(
        qualification_id: str,
        _: dict = Depends(require_read_dep),
    ):
        snap = await get_qualification_snapshot(db, qualification_id)
        if not snap:
            raise HTTPException(404, "qualification not found")
        return snap

    # ── Create ─────────────────────────────────────────────────────
    @r.post("/hr/qualifications")
    async def create_qualification(
        body: QualificationCreate,
        user: dict = Depends(require_write_dep),
    ):
        qtype = body.qualification_type
        if not is_engine_type(qtype):
            raise HTTPException(400, f"unknown qualification_type: {qtype}")
        err = validate_type_metadata(qtype, body.type_metadata)
        if err:
            raise HTTPException(400, err)
        # Resolve employee.
        emp = await db.employees.find_one(
            {"$or": [{"id": body.employee_id},
                     {"employee_id": body.employee_id}]},
            {"_id": 0},
        )
        if not emp:
            raise HTTPException(404, "employee not found")
        actor = _actor_tuple(user)
        now = _now()
        qid = str(uuid.uuid4())
        row = {
            "id": qid,
            "employee_id": body.employee_id,
            "employee_master_id": body.employee_master_id
                or emp.get("id") or body.employee_id,
            "employee_name": body.employee_name
                or emp.get("name") or "",
            # qualification-engine fields
            "qualification_type": qtype,
            "certification_type": qtype,      # kept in sync for legacy readers
            "training_name": body.training_name or qtype.replace("_", " ").title(),
            "completed_date": body.completed_date,
            "expiration_date": body.expiration_date,
            "issuing_organization": (body.issuing_organization or "").strip(),
            "issued_by": (body.issued_by or body.issuing_organization or "").strip(),
            "instructor": (body.instructor or "").strip(),
            "instructor_company": (body.instructor_company or "").strip(),
            "training_hours": body.training_hours,
            "training_standard": (body.training_standard or "").strip(),
            "jurisdiction": (body.jurisdiction or "").strip(),
            "certificate_number": (body.certificate_number or "").strip(),
            "certificate_file_id": body.certificate_file_id,
            "attachments": body.attachments or [],
            "notes": (body.notes or "").strip(),
            "type_metadata": body.type_metadata or {},
            # lifecycle
            "verification_status": "active",
            "verification_status_history": [{
                "status": "active", "at": now,
                "actor_id": actor["actor_id"],
                "actor_role": actor["actor_role"],
                "reason": "created",
            }],
            "suspended_at": None,
            "revoked_at": None,
            # audit
            "created_at": now, "updated_at": now,
            "created_by": actor["actor_email"],
            "created_by_role": actor["actor_role"],
            "created_by_name": actor["actor_name"],
            "updated_by": actor["actor_email"],
            "updated_by_role": actor["actor_role"],
            "originating_portal": actor["actor_role"],
            "status": "Completed",
        }
        await db[COLL].insert_one(row)
        row.pop("_id", None)
        await _write_audit(db, row, "create", None, row, user)
        try:
            await emit_qualification_certification_fact(
                db, row,
                actor=actor["actor_email"] or "system",
                trigger="qualifications.create",
                submitted_by=actor["actor_name"],
            )
        except Exception:                                  # noqa: BLE001
            # Never fail the write on an ODS emit error — the fact
            # can be re-emitted from the row via the migration script.
            pass
        return row

    # ── Update ─────────────────────────────────────────────────────
    @r.patch("/hr/qualifications/{qid}")
    async def update_qualification(
        qid: str, body: QualificationUpdate,
        user: dict = Depends(require_write_dep),
    ):
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        if not row:
            raise HTTPException(404, "qualification not found")
        payload = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not payload:
            raise HTTPException(400, "no changes")
        # Type-metadata validation if the caller changed it.
        if "type_metadata" in payload:
            err = validate_type_metadata(
                row.get("qualification_type"), payload["type_metadata"],
            )
            if err:
                raise HTTPException(400, err)
        before = {k: row.get(k) for k in payload.keys()}
        actor = _actor_tuple(user)
        payload["updated_at"] = _now()
        payload["updated_by"] = actor["actor_email"]
        payload["updated_by_role"] = actor["actor_role"]
        await db[COLL].update_one({"id": qid}, {"$set": payload})
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        await _write_audit(db, row, "update", before, payload, user)
        try:
            await emit_qualification_certification_fact(
                db, row, actor=actor["actor_email"] or "system",
                trigger="qualifications.update",
                submitted_by=actor["actor_name"],
            )
        except Exception:                                  # noqa: BLE001
            pass
        return row

    # ── Lifecycle transitions ──────────────────────────────────────
    async def _transition(
        qid: str, target: str, reason: str, user: Dict[str, Any],
        *, clear_terminal: bool = False,
    ) -> Dict[str, Any]:
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        if not row:
            raise HTTPException(404, "qualification not found")
        actor = _actor_tuple(user)
        # Revoked is terminal — only an explicit "reinstate" from a
        # non-active status can clear `revoked_at`. Suspend can be
        # reinstated too.
        now = _now()
        patch: Dict[str, Any] = {
            "verification_status": target,
            "updated_at": now,
            "updated_by": actor["actor_email"],
            "updated_by_role": actor["actor_role"],
            **_append_history(row, target, user, reason=reason),
        }
        if target == "suspended":
            patch["suspended_at"] = now
        elif target == "revoked":
            patch["revoked_at"] = now
        elif target == "active" and clear_terminal:
            patch["suspended_at"] = None
            patch["revoked_at"] = None
        await db[COLL].update_one({"id": qid}, {"$set": patch})
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        await _write_audit(db, row, f"lifecycle.{target}", None, patch, user)
        try:
            await emit_qualification_certification_fact(
                db, row, actor=actor["actor_email"] or "system",
                trigger=f"qualifications.{target}",
                submitted_by=actor["actor_name"],
            )
        except Exception:                                  # noqa: BLE001
            pass
        return row

    @r.post("/hr/qualifications/{qid}/suspend")
    async def suspend_qualification(
        qid: str, body: QualificationReasonBody,
        user: dict = Depends(require_write_dep),
    ):
        return await _transition(qid, "suspended", body.reason, user)

    @r.post("/hr/qualifications/{qid}/revoke")
    async def revoke_qualification(
        qid: str, body: QualificationReasonBody,
        user: dict = Depends(require_write_dep),
    ):
        return await _transition(qid, "revoked", body.reason, user)

    @r.post("/hr/qualifications/{qid}/reinstate")
    async def reinstate_qualification(
        qid: str, body: QualificationReasonBody,
        user: dict = Depends(require_write_dep),
    ):
        return await _transition(
            qid, "active", body.reason, user, clear_terminal=True,
        )

    @r.post("/hr/qualifications/{qid}/renew")
    async def renew_qualification(
        qid: str, body: QualificationRenewBody,
        user: dict = Depends(require_write_dep),
    ):
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        if not row:
            raise HTTPException(404, "qualification not found")
        actor = _actor_tuple(user)
        now = _now()
        patch = {
            "expiration_date": body.expiration_date,
            "verification_status": "active",
            "suspended_at": None,
            "updated_at": now,
            "updated_by": actor["actor_email"],
            "updated_by_role": actor["actor_role"],
            **_append_history(row, "active", user, reason=body.reason or "renewal"),
        }
        if body.completed_date:
            patch["completed_date"] = body.completed_date
        if body.certificate_number:
            patch["certificate_number"] = body.certificate_number
        if body.attachments:
            patch["attachments"] = list(row.get("attachments") or []) + list(body.attachments)
        # Renew does NOT clear revoked_at automatically — a revoked
        # qualification must be reinstated first (HR policy).
        await db[COLL].update_one({"id": qid}, {"$set": patch})
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        await _write_audit(db, row, "renew", None, patch, user)
        try:
            await emit_qualification_certification_fact(
                db, row, actor=actor["actor_email"] or "system",
                trigger="qualifications.renew",
                submitted_by=actor["actor_name"],
            )
        except Exception:                                  # noqa: BLE001
            pass
        return row

    # ── Attachment · UPLOAD ────────────────────────────────────────
    #
    # Track 24.2 · Phase 1 · Qualifications finalization.
    # Every qualification row already carries an `attachments: []`
    # array. This endpoint accepts a base64-encoded document (PDF /
    # wallet card / sign-in sheet / transcript / photo) and appends a
    # metadata record to that array. Bytes themselves are stored in
    # `db.qualification_attachments` for GridFS-free downloadability.
    # No overwrite: a later re-upload of the same filename creates a
    # new version with `version = last + 1`. Every upload is audit-
    # logged. Downloads are auth-gated (any portal token can read;
    # only HR/Safety/Training/Admin can upload — same as write dep).
    _ALLOWED_CT = {
        "application/pdf",
        "image/jpeg", "image/jpg", "image/png", "image/webp",
    }
    _MAX_BYTES = 15 * 1024 * 1024                          # 15 MB

    @r.post("/hr/qualifications/{qid}/attachments")
    async def upload_qualification_attachment(
        qid: str, body: QualificationAttachmentBody,
        user: dict = Depends(require_write_dep),
    ):
        row = await db[COLL].find_one({"id": qid}, {"_id": 0})
        if not row:
            raise HTTPException(404, "qualification not found")
        if body.content_type not in _ALLOWED_CT:
            raise HTTPException(400, {
                "error": "unsupported_content_type",
                "allowed": sorted(_ALLOWED_CT),
                "received": body.content_type,
            })
        import base64
        try:
            raw = base64.b64decode(body.data_base64, validate=True)
        except Exception:                                  # noqa: BLE001
            raise HTTPException(400, {"error": "invalid_base64"})
        if len(raw) == 0:
            raise HTTPException(400, {"error": "empty_file"})
        if len(raw) > _MAX_BYTES:
            raise HTTPException(413, {
                "error": "file_too_large",
                "max_bytes": _MAX_BYTES, "received_bytes": len(raw),
            })
        # Magic-byte validation.
        if body.content_type == "application/pdf" and not raw.startswith(b"%PDF"):
            raise HTTPException(400, {"error": "invalid_pdf_magic_bytes"})
        if body.content_type.startswith("image/"):
            ok = (raw.startswith(b"\xff\xd8\xff")            # JPEG
                  or raw.startswith(b"\x89PNG\r\n\x1a\n")   # PNG
                  or raw[:4] == b"RIFF" and raw[8:12] == b"WEBP")
            if not ok:
                raise HTTPException(400, {"error": "invalid_image_magic_bytes"})
        # RFC 6266 filename quote — strip control chars & path
        # separators before storing.
        import re as _re
        safe_name = _re.sub(r"[\\/\r\n\t]+", "_", body.filename).strip()[:200]
        # Determine version (append-only).
        existing = list(row.get("attachments") or [])
        matching = [a for a in existing if (a.get("filename") == safe_name)]
        version = (max((a.get("version") or 1) for a in matching) + 1) if matching else 1

        attachment_id = str(uuid.uuid4())
        actor = _actor_tuple(user)
        now = _now()
        meta = {
            "attachment_id": attachment_id,
            "qualification_id": qid,
            "employee_id": row.get("employee_id"),
            "filename": safe_name,
            "content_type": body.content_type,
            "size_bytes": len(raw),
            "document_kind": (body.document_kind or "certificate").strip().lower(),
            "notes": (body.notes or "").strip(),
            "version": version,
            "uploaded_by": actor["actor_email"],
            "uploaded_by_name": actor["actor_name"],
            "uploaded_by_role": actor["actor_role"],
            "uploaded_at": now,
        }
        # Store bytes separately so the qualification doc stays small.
        await db.qualification_attachments.insert_one({
            **meta,
            "data_base64": body.data_base64,
        })
        # Append metadata onto the qualification row.
        updated = list(existing) + [meta]
        await db[COLL].update_one(
            {"id": qid},
            {"$set": {"attachments": updated, "updated_at": now,
                      "updated_by": actor["actor_email"],
                      "updated_by_role": actor["actor_role"]}},
        )
        await _write_audit(
            db, row, "attachment_upload",
            before={"attachment_count": len(existing)},
            after={"attachment_count": len(updated),
                   "attachment_id": attachment_id,
                   "filename": safe_name, "version": version,
                   "size_bytes": len(raw)},
            user=user,
        )
        return {"ok": True, "attachment": meta}

    # ── Attachment · LIST metadata ─────────────────────────────────
    @r.get("/hr/qualifications/{qid}/attachments")
    async def list_qualification_attachments(
        qid: str, _: dict = Depends(require_read_dep),
    ):
        row = await db[COLL].find_one({"id": qid}, {"_id": 0, "attachments": 1})
        if not row:
            raise HTTPException(404, "qualification not found")
        return {"attachments": row.get("attachments") or [], "count": len(row.get("attachments") or [])}

    # ── Attachment · DOWNLOAD ──────────────────────────────────────
    @r.get("/hr/qualifications/{qid}/attachments/{attachment_id}")
    async def download_qualification_attachment(
        qid: str, attachment_id: str,
        _: dict = Depends(require_read_dep),
    ):
        blob = await db.qualification_attachments.find_one(
            {"qualification_id": qid, "attachment_id": attachment_id},
            {"_id": 0},
        )
        if not blob:
            raise HTTPException(404, "attachment not found")
        import base64
        from fastapi.responses import Response
        try:
            payload = base64.b64decode(blob["data_base64"])
        except Exception:                                  # noqa: BLE001
            raise HTTPException(500, "attachment corrupted")
        # RFC 6266 filename-quoted disposition, safe fallback for
        # non-ASCII filenames using UTF-8 percent-encoding.
        import urllib.parse
        fname = blob.get("filename") or f"{attachment_id}.bin"
        ascii_safe = fname.encode("ascii", "ignore").decode() or "attachment.bin"
        utf8_quoted = urllib.parse.quote(fname)
        disposition = (f'attachment; filename="{ascii_safe}"; '
                       f"filename*=UTF-8''{utf8_quoted}")
        return Response(
            content=payload,
            media_type=blob.get("content_type") or "application/octet-stream",
            headers={"Content-Disposition": disposition,
                     "Cache-Control": "private, no-store"},
        )

    # ── Migration · AUDIT REPORT ───────────────────────────────────
    #
    # Read-only enumeration of every `safety_training_records` row and
    # its coverage against the Qualifications Engine registry.
    # Answers: (a) how many total training rows exist, (b) how many
    # are already recognized as engine qualification types, (c) how
    # many are ambiguous / legacy (`certification_type` not in engine
    # canonical types), (d) counts per engine type, (e) rows with
    # attachments. Idempotent: this endpoint is a read.  Track 24.2.
    @r.get("/hr/qualifications/migration-audit")
    async def qualifications_migration_audit(
        _: dict = Depends(require_write_dep),  # HR/Safety/Admin only
    ):
        from services.certifications.qualification_types import (
            QUALIFICATION_ENGINE_TYPES,
        )
        canonical = set(QUALIFICATION_ENGINE_TYPES)
        total = 0
        recognized = 0
        ambiguous_rows: List[Dict[str, Any]] = []
        per_type: Dict[str, int] = {}
        rows_with_attachments = 0
        rows_with_certificate_number = 0
        active_count = 0
        cursor = db[COLL].find(
            {},
            {"_id": 0, "id": 1, "qualification_type": 1,
             "certification_type": 1, "training_name": 1,
             "employee_id": 1, "verification_status": 1,
             "attachments": 1, "certificate_number": 1,
             "completed_date": 1, "expiration_date": 1},
        )
        async for r_ in cursor:
            total += 1
            t = r_.get("qualification_type") or r_.get("certification_type") or ""
            if t in canonical:
                recognized += 1
                per_type[t] = per_type.get(t, 0) + 1
            else:
                if len(ambiguous_rows) < 50:
                    ambiguous_rows.append({
                        "id": r_.get("id"),
                        "employee_id": r_.get("employee_id"),
                        "type_seen": t,
                        "training_name": r_.get("training_name"),
                    })
            if r_.get("attachments"):
                rows_with_attachments += 1
            if (r_.get("certificate_number") or "").strip():
                rows_with_certificate_number += 1
            if (r_.get("verification_status") or "").lower() == "active":
                active_count += 1
        return {
            "generated_at": _now(),
            "source_collection": COLL,
            "canonical_engine_types": sorted(canonical),
            "totals": {
                "total_rows": total,
                "recognized_engine_type": recognized,
                "ambiguous_or_legacy_type": total - recognized,
                "active_rows": active_count,
                "rows_with_attachments": rows_with_attachments,
                "rows_with_certificate_number": rows_with_certificate_number,
            },
            "recognized_per_type": per_type,
            "ambiguous_sample": ambiguous_rows,
            "notes": [
                "This report is READ-ONLY. It never mutates records.",
                "Ambiguous rows are legacy training-records whose "
                "`certification_type` string does not map to a "
                "canonical engine type. They remain readable via "
                "the qualifications endpoints and are not orphaned; "
                "they simply do not surface in engine-typed listings "
                "until relabelled to a canonical type.",
                "The Qualifications Engine is idempotent by design — "
                "there is NO import job. Existing safety_training_records "
                "are the native store; the engine is a lens over it.",
            ],
        }

    return r


__all__ = ["build_qualifications_router"]
