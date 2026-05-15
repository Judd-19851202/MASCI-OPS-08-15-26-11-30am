"""
Safety Portal · documents.py — Phase 3 document library.

Read access: Safety + HR + Admin (via the multi-role gate).
Write access: Safety only.

Storage: HYBRID. When R2/S3 is configured (`safety_doc_storage.is_configured()`
returns True) uploaded bytes go to object storage and `file_data` holds
a ``doc://bucket/key`` reference. Otherwise the file is inlined as a
``data:...;base64,...`` URL (legacy / unconfigured-env behaviour).

Read path (`/download`) handles both schemes transparently via
``safety_doc_storage.read_doc_bytes``, so existing records uploaded
under the inline-only scheme keep working without migration.
"""
from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

import safety_doc_storage
from ._models import SafetyDocumentUpdate

logger = logging.getLogger(__name__)

MAX_DOC_BYTES = 15 * 1024 * 1024  # 15 MB


def register_document_routes(
    api_router: APIRouter, db, require_safety_token, require_safety_or_hr_or_admin,
) -> None:

    @api_router.get("/safety/documents")
    async def list_safety_documents(
        category: Optional[str] = None,
        _: dict = Depends(require_safety_or_hr_or_admin),
    ):
        q: dict = {}
        if category:
            q["category"] = category
        # Always project file_data OUT — list view is metadata only.
        cursor = db.safety_documents.find(q, {"_id": 0, "file_data": 0}).sort("uploaded_at", -1)
        return await cursor.to_list(2000)

    @api_router.post("/safety/documents")
    async def upload_safety_document(
        file: UploadFile = File(...),
        title: str = Form(""),
        category: str = Form("General"),
        description: str = Form(""),
        tags: str = Form(""),
        user: dict = Depends(require_safety_token),
    ):
        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty file")
        if len(raw) > MAX_DOC_BYTES:
            raise HTTPException(413, f"File too large. Max {MAX_DOC_BYTES // (1024 * 1024)} MB.")
        content_type = file.content_type or "application/octet-stream"
        filename = (file.filename or "document").strip()
        doc_id = str(uuid.uuid4())

        # Hybrid storage: prefer R2 when configured, fall back to inline base64.
        storage_backend = "inline"
        if safety_doc_storage.is_configured():
            try:
                ref = await safety_doc_storage.upload_doc_bytes(
                    raw, doc_id=doc_id, filename=filename, content_type=content_type,
                )
                file_data = ref
                storage_backend = "r2"
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[safety-doc] R2 upload failed, falling back to inline: {e}")
                # Log degraded-storage event (iter133 — surfaces in System Health)
                # NOTE: store `at` as BSON datetime (not ISO string) so the
                # System Health 24h-window query stays correct regardless of
                # downstream logger swaps.
                try:
                    await db.r2_degraded_events.insert_one({
                        "at": datetime.now(timezone.utc),
                        "module": "safety_documents",
                        "doc_id": doc_id,
                        "filename": filename,
                        "size_bytes": len(raw),
                        "error": str(e)[:240],
                    })
                except Exception:  # noqa: BLE001
                    pass
                b64 = base64.b64encode(raw).decode("ascii")
                file_data = f"data:{content_type};base64,{b64}"
        else:
            b64 = base64.b64encode(raw).decode("ascii")
            file_data = f"data:{content_type};base64,{b64}"

        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": doc_id,
            "title": (title or filename or "Untitled").strip(),
            "filename": filename,
            "category": (category or "General").strip(),
            "description": (description or "").strip(),
            "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
            "content_type": content_type,
            "file_size": len(raw),
            "file_data": file_data,
            "storage_backend": storage_backend,
            "uploaded_by_name": user.get("name") or "",
            "uploaded_by_email": user.get("email") or "",
            "uploaded_at": now,
        }
        await db.safety_documents.insert_one(doc)
        # Return summary (no file_data — that can be huge for inline records)
        doc.pop("_id", None)
        doc.pop("file_data", None)
        return doc

    @api_router.patch("/safety/documents/{doc_id}")
    async def update_safety_document(
        doc_id: str, body: SafetyDocumentUpdate, _: dict = Depends(require_safety_token),
    ):
        update = {k: v for k, v in body.dict(exclude_none=True).items()}
        if not update:
            raise HTTPException(400, "No changes")
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = await db.safety_documents.update_one({"id": doc_id}, {"$set": update})
        if res.matched_count == 0:
            raise HTTPException(404, "Not found")
        return await db.safety_documents.find_one(
            {"id": doc_id}, {"_id": 0, "file_data": 0},
        )

    @api_router.get("/safety/documents/{doc_id}/download")
    async def download_safety_document(
        doc_id: str, _: dict = Depends(require_safety_or_hr_or_admin),
    ):
        doc = await db.safety_documents.find_one({"id": doc_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Not found")
        ref = doc.get("file_data") or ""
        try:
            raw = await safety_doc_storage.read_doc_bytes(ref)
        except (ValueError, RuntimeError) as e:
            logger.exception(f"[safety-doc] download read failed for doc_id={doc_id}: {e}")
            raise HTTPException(500, "Stored file is unreadable")
        ct = doc.get("content_type", "application/octet-stream")
        fname = doc.get("filename", "document")
        return Response(
            content=raw,
            media_type=ct,
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "Cache-Control": "no-store",
            },
        )

    @api_router.delete("/safety/documents/{doc_id}")
    async def delete_safety_document(
        doc_id: str, _: dict = Depends(require_safety_token),
    ):
        # Best-effort R2 cleanup BEFORE the DB delete — if R2 errors we
        # still want the record gone. Inline base64 records skip R2.
        doc = await db.safety_documents.find_one({"id": doc_id}, {"_id": 0, "file_data": 1})
        if doc and doc.get("file_data"):
            try:
                await safety_doc_storage.delete_doc(doc["file_data"])
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[safety-doc] R2 delete failed for {doc_id}: {e}")
        res = await db.safety_documents.delete_one({"id": doc_id})
        if res.deleted_count == 0:
            raise HTTPException(404, "Not found")
        return {"ok": True}


__all__ = ["register_document_routes"]
