"""routes/legacy_imports.py · iter430 · Phase 28.2 · Phase 4D extraction.

Legacy Operational Records Import — full Phase A + Phase B route surface.

Doctrine
--------
This module is a ZERO-BEHAVIOR-CHANGE extraction of the legacy-imports
endpoints from server.py. Every route path, response shape, status
code, dependency signature, and audit-write contract is preserved
verbatim from the inline implementation at server.py:9211-9702
(pre-iter430).

Architectural notes:
  • Routes that were previously declared on the global `app` with
    `@app.post(...)` are now declared on a single `APIRouter()`
    factory and mounted with `app.include_router(router)` from
    server.py. FastAPI's path resolution is identical either way.
  • Shared helpers `_li_require_uploader` and `_li_scope_filter`
    moved into this module — they were only ever used by these
    routes.
  • Startup hooks (`_li_ensure_indexes`, `_li_start_worker`) and
    the global `_li_worker_task` REMAIN in server.py to keep the
    application's startup lifecycle untouched.
  • All external symbols this module needs are passed in through
    the `build_legacy_imports_router` factory: `db`, the admin
    token validator, the admin-strict dep, the existing `legacy_imports`
    business-logic module (`_li`), and the `photo_storage` helper
    (`_ps`). This keeps server.py the single owner of those globals.

Routes (paths · matching the iter238/iter248/iter249 contract):

    POST   /api/legacy-imports/upload
    GET    /api/legacy-imports/_meta
    GET    /api/legacy-imports
    GET    /api/legacy-imports/{import_id}
    GET    /api/legacy-imports/{import_id}/file
    PATCH  /api/legacy-imports/{import_id}
    POST   /api/legacy-imports/{import_id}/approve
    POST   /api/legacy-imports/{import_id}/reject
    POST   /api/legacy-imports/{import_id}/retry-ocr
    GET    /api/admin/legacy-imports/audit
    GET    /api/admin/legacy-imports/pilot-debrief
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from pydantic import BaseModel

logger = logging.getLogger("legacy_imports_routes")


# ─── Pydantic bodies · preserved verbatim from server.py ──────────
class _LiCorrections(BaseModel):
    extracted_fields: Optional[Dict[str, Any]] = None
    matches: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class _LiApprove(BaseModel):
    corrections: Optional[Dict[str, Any]] = None
    notes: str = ""
    admin_override_self_approval: bool = False


class _LiReject(BaseModel):
    reason: str
    notes: str = ""


def build_legacy_imports_router(
    *,
    db,
    li_module,                              # legacy_imports module (_li)
    photo_storage_module,                   # photo_storage module (_ps)
    is_valid_admin_token: Callable[[str], bool],
    require_admin_strict: Callable[..., Awaitable[Any]],
    is_valid_admin_token_async: Optional[Callable[[str], Awaitable[bool]]] = None,
) -> APIRouter:
    """Build the legacy-imports router with all 11 routes attached.

    Parameters mirror the implicit dependencies the inline server.py
    code had on global symbols.

    TRACK 28.03E · accepts optional ``is_valid_admin_token_async`` so
    per-user admin tokens unlock the uploader.
    """
    _li = li_module
    _ps = photo_storage_module
    router = APIRouter(tags=["legacy-imports"])

    # ─── Uploader auth dep · HR / Safety / Admin only ─────────────
    async def _li_require_uploader(
        request: Request,  # noqa: ARG001
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
    ) -> Dict[str, Any]:
        """HR · Safety · Admin only. Returns `{actor_role, actor_id, actor_name, upload_portal}`."""
        if x_admin_token:
            admin_ok = is_valid_admin_token(x_admin_token)
            if not admin_ok and is_valid_admin_token_async:
                admin_ok = bool(await is_valid_admin_token_async(x_admin_token))
            if admin_ok:
                return {
                    "actor_role": "admin",
                    "actor_id": "admin-break-glass",
                    "actor_name": "Admin",
                    "upload_portal": "admin",
                }
        if x_hr_token:
            from hr_users import is_valid_hr_user_token_async  # noqa: PLC0415
            u = await is_valid_hr_user_token_async(db, x_hr_token)
            if u:
                return {
                    "actor_role": "hr_user",
                    "actor_id": u.get("id") or "",
                    "actor_name": u.get("name") or u.get("email") or "HR User",
                    "upload_portal": "hr",
                }
        if x_safety_token:
            from safety_users import is_valid_safety_user_token  # noqa: PLC0415
            u = await is_valid_safety_user_token(db, x_safety_token)
            if u:
                return {
                    "actor_role": "safety_user",
                    "actor_id": u.get("id") or "",
                    "actor_name": u.get("name") or u.get("email") or "Safety User",
                    "upload_portal": "safety",
                }
        raise HTTPException(401, "HR, Safety, or Admin authentication required")

    def _li_scope_filter(actor: Dict[str, Any]) -> Dict[str, Any]:
        """Admins see everything · HR sees HR-uploaded · Safety sees Safety-uploaded."""
        if actor["actor_role"] == "admin":
            return {}
        return {"upload_portal": actor["upload_portal"]}

    # ─── POST /api/legacy-imports/upload ──────────────────────────
    @router.post("/api/legacy-imports/upload")
    async def li_upload(
        request: Request,
        file: UploadFile = File(...),
        document_type: str = Form("unknown"),
        batch_id: Optional[str] = Form(None),
        actor=Depends(_li_require_uploader),
    ):
        """Upload one file. Multi-file uploads send N parallel requests
        sharing the same `batch_id`. Phase A returns the legacy_imports
        row; OCR worker picks it up in the background."""
        if document_type not in _li.DOCUMENT_TYPES:
            raise HTTPException(400, f"unknown document_type · valid: {_li.DOCUMENT_TYPES}")
        if not _li.upload_allowed(actor["upload_portal"], document_type):
            raise HTTPException(
                403,
                f"{actor['upload_portal']} portal cannot upload document_type={document_type!r}",
            )

        # Phase B · pilot cap on equipment_checkout (50 by default ·
        # env LEGACY_IMPORT_PILOT_CAP). Goal: learn operational
        # friction at small scale before scaling up — operator rule.
        if document_type == "equipment_checkout":
            try:
                import legacy_imports_equipment_checkout as _li_ec  # noqa: PLC0415
                remaining = await _li_ec.equipment_checkout_pilot_remaining(db)
            except Exception:
                remaining = 9999
            if remaining <= 0:
                raise HTTPException(
                    429,
                    "equipment_checkout pilot cap reached "
                    "(LEGACY_IMPORT_PILOT_CAP). Operator must lift before "
                    "more uploads can be staged.",
                )

        data = await file.read()
        if not data:
            raise HTTPException(400, "empty file")
        if len(data) > 25 * 1024 * 1024:  # 25 MB hard cap
            raise HTTPException(400, "file too large (max 25 MB)")

        sha = _li.sha256_bytes(data)
        existing = await _li.find_by_sha256(db, sha)
        if existing:
            return {
                "duplicate_of": existing.get("id"),
                "message": "this file was already uploaded · returning existing import row",
                "row": existing,
            }

        # Upload to R2 (private bucket · same lib as photo_storage)
        if not _ps.is_configured():
            raise HTTPException(503, "object storage not configured")

        ext = (file.filename or "upload").rsplit(".", 1)[-1].lower() or "bin"
        today = _dt.datetime.now(_dt.timezone.utc)
        safe_src = "".join(
            c if c.isalnum() or c in "-_." else "_"
            for c in (actor["actor_id"] or "unknown")
        )
        key = (
            f"legacy-imports/{today:%Y/%m}/{batch_id or 'solo'}/"
            f"{safe_src}/{uuid.uuid4().hex}.{ext}"
        )
        client = _ps._client()  # internal but stable
        if client is None:
            raise HTTPException(503, "object storage client init failed")
        await asyncio.to_thread(
            client.put_object,
            Bucket=_ps._bucket(),
            Key=key,
            Body=data,
            ContentType=file.content_type or "application/octet-stream",
        )

        now = datetime.now(timezone.utc).isoformat()
        import_id = uuid.uuid4().hex
        row = {
            "id": import_id,
            "document_type": document_type,
            "status": "uploaded",
            "source_files": [{
                "r2_key": key,
                "original_name": file.filename or "upload",
                "mime": file.content_type or "application/octet-stream",
                "size_bytes": len(data),
                "sha256": sha,
                "uploaded_by_id": actor["actor_id"],
                "uploaded_by_name": actor["actor_name"],
                "uploaded_at": now,
            }],
            "upload_portal": actor["upload_portal"],
            "batch_id": batch_id,
            "ocr": {
                "provider": "pending",
                "completed_at": None, "raw_text": "", "extracted_fields": {},
                "confidence": 0.0, "field_confidences": {},
                "classifier_score": 0.0, "error": None,
            },
            "matches": {
                "employee": {"suggested_id": None, "suggested_name": None,
                             "confidence": 0.0, "alternatives": []},
                "equipment": {"suggested_id": None, "suggested_name": None,
                              "confidence": 0.0, "alternatives": []},
                "project": {"suggested_id": None, "suggested_name": None,
                            "confidence": 0.0, "alternatives": []},
                "duplicate_of": None,
            },
            "review": {
                "reviewer_user_id": None, "reviewer_name": None,
                "reviewed_at": None, "decision": None,
                "corrections": {}, "reject_reason": None, "notes": "",
            },
            "promotion": {
                "promoted": False, "promoted_to_collection": None,
                "promoted_record_id": None, "promoted_at": None,
            },
            "created_at": now,
            "updated_at": now,
        }
        await db.legacy_imports.insert_one(row)
        row.pop("_id", None)
        await _li.audit_log(
            db,
            import_id=import_id,
            batch_id=batch_id,
            actor_user_id=actor["actor_id"],
            actor_name=actor["actor_name"],
            actor_role=actor["actor_role"],
            action="uploaded",
            after={"document_type": document_type, "size_bytes": len(data), "sha256": sha},
            ip=(request.client.host if request.client else ""),
            user_agent=request.headers.get("user-agent", "")[:240],
        )
        return {"ok": True, "row": row}

    # ─── GET /api/legacy-imports/_meta ────────────────────────────
    @router.get("/api/legacy-imports/_meta")
    async def li_meta(actor=Depends(_li_require_uploader)):
        """Static meta for the reconciliation UI — document types this
        portal can upload + active promoters. Registered ABOVE
        /{import_id} so FastAPI's path-matching doesn't capture `_meta`
        as an ID."""
        portal = actor["upload_portal"]
        allowed = sorted(_li.UPLOAD_PORTAL_MATRIX.get(portal, set()))
        pilot_remaining = None
        pilot_cap_v = None
        try:
            import legacy_imports_equipment_checkout as _li_ec  # noqa: PLC0415
            if "equipment_checkout" in _li.ACTIVE_PROMOTERS:
                pilot_remaining = await _li_ec.equipment_checkout_pilot_remaining(db)
                pilot_cap_v = _li_ec.pilot_cap()
        except Exception:
            pass
        return {
            "upload_portal": portal,
            "actor_role": actor["actor_role"],
            "actor_id": actor["actor_id"],
            "allowed_document_types": allowed,
            "active_promoters": sorted(_li.ACTIVE_PROMOTERS.keys()),
            "phase": ("B" if "equipment_checkout" in _li.ACTIVE_PROMOTERS else "A"),
            "equipment_checkout_pilot_cap": pilot_cap_v,
            "equipment_checkout_pilot_remaining": pilot_remaining,
        }

    # ─── GET /api/legacy-imports ──────────────────────────────────
    @router.get("/api/legacy-imports")
    async def li_list(
        status: Optional[str] = None,
        document_type: Optional[str] = None,
        batch_id: Optional[str] = None,
        limit: int = 100,
        actor=Depends(_li_require_uploader),
    ):
        q = _li_scope_filter(actor)
        if status:
            q["status"] = status
        if document_type:
            q["document_type"] = document_type
        if batch_id:
            q["batch_id"] = batch_id
        cursor = (db.legacy_imports
                  .find(q, {"_id": 0})
                  .sort("created_at", -1)
                  .limit(max(1, min(500, limit))))
        items = await cursor.to_list(None)
        return {"count": len(items), "items": items}

    # ─── GET /api/legacy-imports/{import_id} ──────────────────────
    @router.get("/api/legacy-imports/{import_id}")
    async def li_detail(import_id: str, actor=Depends(_li_require_uploader)):
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        return doc

    # ─── GET /api/legacy-imports/{import_id}/file ─────────────────
    @router.get("/api/legacy-imports/{import_id}/file")
    async def li_signed_url(
        request: Request,
        import_id: str,
        file_index: int = 0,
        actor=Depends(_li_require_uploader),
    ):
        """Returns a 5-minute signed URL for the original scan + writes
        an audit row (so HR/legal can prove who accessed the evidence)."""
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        files = doc.get("source_files") or []
        if file_index < 0 or file_index >= len(files):
            raise HTTPException(400, "file_index out of range")
        key = files[file_index]["r2_key"]
        url = await _ps.presigned_get_url_for_key(key, ttl_seconds=300)
        await _li.audit_log(
            db,
            import_id=import_id,
            batch_id=doc.get("batch_id"),
            actor_user_id=actor["actor_id"],
            actor_name=actor["actor_name"],
            actor_role=actor["actor_role"],
            action="evidence_accessed",
            after={"file_index": file_index, "r2_key": key},
            ip=(request.client.host if request.client else ""),
            user_agent=request.headers.get("user-agent", "")[:240],
        )
        return {"url": url, "expires_in_seconds": 300}

    # ─── PATCH /api/legacy-imports/{import_id} ────────────────────
    @router.patch("/api/legacy-imports/{import_id}")
    async def li_correct(
        import_id: str,
        body: _LiCorrections,
        request: Request,  # noqa: ARG001  (preserved for audit-shape parity)
        actor=Depends(_li_require_uploader),
    ):
        """Reviewer corrections / suggested-match overrides. Does NOT
        change `status`. Reviewer commits via /approve."""
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        updates: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if body.extracted_fields is not None:
            updates["ocr.extracted_fields"] = body.extracted_fields
        if body.matches is not None:
            for k, v in body.matches.items():
                if k in ("employee", "equipment", "project", "duplicate_of"):
                    updates[f"matches.{k}"] = v
        if body.notes is not None:
            updates["review.notes"] = body.notes
        await db.legacy_imports.update_one({"id": import_id}, {"$set": updates})
        await _li.audit_log(
            db,
            import_id=import_id,
            batch_id=doc.get("batch_id"),
            actor_user_id=actor["actor_id"],
            actor_name=actor["actor_name"],
            actor_role=actor["actor_role"],
            action="metadata_corrected",
            after=body.model_dump(exclude_none=True),
        )
        return await db.legacy_imports.find_one({"id": import_id}, {"_id": 0})

    # ─── POST /api/legacy-imports/{import_id}/approve ─────────────
    @router.post("/api/legacy-imports/{import_id}/approve")
    async def li_approve(
        import_id: str,
        body: _LiApprove,
        request: Request,  # noqa: ARG001  (preserved for audit-shape parity)
        actor=Depends(_li_require_uploader),
    ):
        """Human approval — the only path to operational activation.
        Phase A: marks `status=approved` (no doc type has an active
        promoter yet · operator activates them in Phase B+)."""
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        try:
            out = await _li.approve_import(
                db,
                import_id=import_id,
                approver_id=actor["actor_id"],
                approver_name=actor["actor_name"],
                approver_role=actor["actor_role"],
                corrections=body.corrections,
                notes=body.notes,
                admin_override_self_approval=body.admin_override_self_approval,
            )
            return {"ok": True, "row": out}
        except _li.ApprovalError as e:
            raise HTTPException(400, str(e))

    # ─── POST /api/legacy-imports/{import_id}/reject ──────────────
    @router.post("/api/legacy-imports/{import_id}/reject")
    async def li_reject(
        import_id: str,
        body: _LiReject,
        actor=Depends(_li_require_uploader),
    ):
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        try:
            out = await _li.reject_import(
                db,
                import_id=import_id,
                reviewer_id=actor["actor_id"],
                reviewer_name=actor["actor_name"],
                reviewer_role=actor["actor_role"],
                reason=body.reason,
                notes=body.notes,
            )
            return {"ok": True, "row": out}
        except _li.ApprovalError as e:
            raise HTTPException(400, str(e))

    # ─── POST /api/legacy-imports/{import_id}/retry-ocr ───────────
    @router.post("/api/legacy-imports/{import_id}/retry-ocr")
    async def li_retry_ocr(
        import_id: str,
        actor=Depends(_li_require_uploader),
    ):
        """Re-enqueue an `ocr_failed` row for the worker. Only OCR-failed
        rows can be retried (state-machine guard prevents resetting an
        approved/promoted row by accident)."""
        q = {"id": import_id, **_li_scope_filter(actor)}
        doc = await db.legacy_imports.find_one(q, {"_id": 0})
        if not doc:
            raise HTTPException(404, "import not found")
        if doc.get("status") != "ocr_failed":
            raise HTTPException(
                400,
                f"can only retry from status=ocr_failed (current={doc.get('status')!r})",
            )
        await db.legacy_imports.update_one(
            {"id": import_id},
            {"$set": {
                "status": "uploaded",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        await _li.audit_log(
            db,
            import_id=import_id,
            batch_id=doc.get("batch_id"),
            actor_user_id=actor["actor_id"],
            actor_name=actor["actor_name"],
            actor_role=actor["actor_role"],
            action="ocr_retry_requested",
        )
        return {"ok": True}

    # ─── GET /api/admin/legacy-imports/audit ──────────────────────
    @router.get("/api/admin/legacy-imports/audit")
    async def li_admin_audit(
        import_id: Optional[str] = None,
        limit: int = 200,
        _: bool = Depends(require_admin_strict),
    ):
        q: Dict[str, Any] = {}
        if import_id:
            q["import_id"] = import_id
        cursor = (db.legacy_import_audit
                  .find(q, {"_id": 0})
                  .sort("timestamp", -1)
                  .limit(max(1, min(1000, limit))))
        items = await cursor.to_list(None)
        return {"count": len(items), "items": items}

    # ─── GET /api/admin/legacy-imports/pilot-debrief ──────────────
    @router.get("/api/admin/legacy-imports/pilot-debrief")
    async def li_admin_pilot_debrief(
        document_type: str = "equipment_checkout",
        _: bool = Depends(require_admin_strict),
    ):
        """iter249 Phase B · Read-only operator verification tool for
        the Equipment Checkout legacy-import pilot. Admin-strict ·
        returns structured JSON · NOT a dashboard · NOT a feature
        surface.

        Aggregates: status counts · OCR confidence stats · reviewer
        corrections summary + diff examples · failed-extraction list ·
        unmatched employee/equipment rows · duplicate-suspicion count ·
        evidence-access audit count · accountability round-trip
        verification · termination-flag verification · readiness
        verdict (READY / NEEDS_TUNING / NOT_READY).

        Operator approval scope: document_type=equipment_checkout only.
        """
        if document_type != "equipment_checkout":
            raise HTTPException(
                400,
                "Pilot debrief is currently scoped to "
                "document_type=equipment_checkout only (operator-approved "
                "Phase B scope · other doc types not yet activated).",
            )
        try:
            import legacy_imports_equipment_checkout as _li_ec  # noqa: PLC0415
            return await _li_ec.compute_pilot_debrief(
                db, document_type=document_type
            )
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[legacy-imports] pilot-debrief failed: {e}")
            raise HTTPException(500, f"pilot debrief failed: {str(e)[:200]}")

    return router
