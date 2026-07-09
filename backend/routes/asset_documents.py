"""routes/asset_documents.py · Track 13.31B-D3+D4.

Asset Documents · Renewal Surfaces · CSV Exports · MASCI Profile PDF.

The collection `operational_attachments` is reused — same R2 path, same
schema. We add:
  • host_kind = "asset"  (in addition to the existing "assignment")
  • 13 asset-document types (registration / insurance / title / etc.)
  • effective_date · expiration_date metadata
  • photo_kind subtype (primary / serial_plate / vin_plate / etc.)
  • Asset-Admin RBAC + sensitive-type gate (Insurance Policy · Title ·
    Purchase Document — Admin + Asset Admin only)
  • PDF support (max 25 MB · application/pdf)
  • Image support (max 10 MB · same MIME list as the assignment lane)

Endpoints (under /api/asset-spine/):
  POST   /assets/{id}/documents/upload          (admin · asset_admin)
  GET    /assets/{id}/documents                 (admin · asset_admin)
  GET    /assets/{id}/documents/{att_id}/file   (admin · asset_admin)
  PATCH  /assets/{id}/documents/{att_id}        (admin · asset_admin)
  DELETE /assets/{id}/documents/{att_id}        (admin)
  GET    /assets/{id}/required-documents        (any portal — info only)
  GET    /assets/{id}/missing-photos            (any portal — info only)
  GET    /assets/{id}/profile.pdf               (admin · asset_admin)
  GET    /dashboard/missing-documents           (admin · asset_admin)
  GET    /dashboard/missing-documents/{doc_type}(admin · asset_admin)
  GET    /dashboard/renewals                    (admin · asset_admin)
  GET    /dashboard/recent-uploads              (admin · asset_admin)
  GET    /dashboard/required-documents-config   (admin · asset_admin)
  GET    /exports/assets.csv                    (admin · asset_admin)
  GET    /exports/renewals.csv                  (admin · asset_admin)
  GET    /exports/missing-documents.csv         (admin · asset_admin)

No new collection. No new storage backend. No new workflow.
"""
from __future__ import annotations

import asyncio
import base64
import csv
import hashlib
import io
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

# TRACK 27.03 · Phase 2b · Asset profile PDF "Generated" stamp uses the
# canonical local formatter.
from lib.platform_time import format_platform_stamp

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

import photo_storage
from services.required_documents import (
    ASSET_DOC_TYPES,
    DOC_ASSET_PHOTO,
    PHOTO_SUBTYPES,
    SENSITIVE_DOC_TYPES,
    doc_label,
    is_sensitive,
    renewal_mirror_field,
    required_documents_for,
    all_required_map,
)

logger = logging.getLogger("asset_documents")

DEFAULT_TENANT_ID = "masci"
ASSET_HOST_KIND = "asset"

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB image cap
MAX_PDF_BYTES   = 25 * 1024 * 1024  # 25 MB PDF cap
MAX_PER_ASSET   = 200                # generous cap, asset records are long-lived

ALLOWED_IMAGE_MIMES = {
    "image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif",
    "image/webp", "image/gif",
}
ALLOWED_PDF_MIMES = {"application/pdf"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_iso_date(s: str | None) -> bool:
    if not s:
        return False
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def _actor_role(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "admin"
    return (actor.get("portal") or actor.get("role") or "admin").lower()


def _actor_label(actor: Dict[str, Any]) -> str:
    if isinstance(actor, dict):
        return str(actor.get("name") or actor.get("email") or actor.get("username") or "admin")
    return "admin"


def _is_admin_or_asset_admin(actor: Any) -> bool:
    # require_admin returns `True` for admin tokens (no dict). Honor that.
    if actor is True:
        return True
    if not isinstance(actor, dict):
        return False
    if actor.get("admin"):
        return True
    role = _actor_role(actor)
    if role == "admin":
        return True
    if actor.get("is_asset_admin") or actor.get("asset_admin"):
        return True
    # iter D2 added `roles` array on user_directory
    roles = actor.get("roles") or []
    if isinstance(roles, list) and "asset_admin" in [str(r).lower() for r in roles]:
        return True
    return False


def _public_doc(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": d.get("id"),
        "asset_id": d.get("host_id"),
        "document_type": d.get("type"),
        "document_label": doc_label(d.get("type") or ""),
        "photo_kind": d.get("photo_kind"),
        "filename": d.get("filename"),
        "content_type": d.get("content_type"),
        "size_bytes": d.get("size_bytes"),
        "uploaded_by": d.get("uploaded_by"),
        "uploaded_at": d.get("uploaded_at"),
        "operational_note": d.get("operational_note") or "",
        "effective_date": d.get("effective_date"),
        "expiration_date": d.get("expiration_date"),
        "is_sensitive": is_sensitive(d.get("type") or ""),
    }


def _filter_sensitive(docs: List[Dict[str, Any]], allow_sensitive: bool) -> List[Dict[str, Any]]:
    if allow_sensitive:
        return docs
    return [d for d in docs if not d.get("is_sensitive")]


class DocumentMetaPatch(BaseModel):
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    operational_note: Optional[str] = None
    photo_kind: Optional[str] = None


def _days_to(date_iso: str | None) -> Optional[int]:
    if not date_iso:
        return None
    try:
        d = datetime.fromisoformat(date_iso.replace("Z", "+00:00")).date()
        return (d - date.today()).days
    except Exception:
        return None


def register_asset_documents_routes(
    app_or_router,
    db,
    require_admin_dep: Callable,
    require_any_portal_dep: Callable,
    require_admin_or_asset_admin_dep: Optional[Callable] = None,
) -> APIRouter:
    """Mount asset-document routes under `/api/asset-spine/`.

    TRACK 15.13E — `require_admin_or_asset_admin_dep` (optional) is
    used on the 4 read-only Asset Care dashboard endpoints so that
    Shop-portal Asset Administrators can view them. When not provided,
    falls back to `_require_asset_admin` (admin/PM only) — preserves
    the legacy behavior for any test/regression harness that mounts
    this router without the extra dep.
    """
    parent_has_prefix = hasattr(app_or_router, "prefix") and getattr(app_or_router, "prefix", "") == "/api"
    router_prefix = "/asset-spine" if parent_has_prefix else "/api/asset-spine"
    router = APIRouter(prefix=router_prefix, tags=["asset-documents"])

    async def _require_asset_admin(actor=Depends(require_admin_dep)):
        # Admin always satisfies the asset-admin gate; once the platform
        # exposes a non-admin asset_admin role, _is_admin_or_asset_admin
        # will accept it transparently.
        if not _is_admin_or_asset_admin(actor):
            raise HTTPException(status_code=403, detail="Asset Administrator access required.")
        return actor

    # TRACK 15.13E — read dep for the 4 dashboard endpoints. Defaults
    # to the legacy gate when the new dep isn't supplied.
    _dashboard_read_dep = require_admin_or_asset_admin_dep or _require_asset_admin

    async def _get_asset_or_404(asset_id: str) -> Dict[str, Any]:
        doc = await db.equipment_master.find_one({"id": asset_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Asset not found")
        return doc

    # ── UPLOAD ─────────────────────────────────────────────────────
    @router.post("/assets/{asset_id}/documents/upload")
    async def upload_asset_document(
        asset_id: str = Path(..., min_length=1),
        document_type: str = Form(...),
        photo_kind: Optional[str] = Form(default=None),
        effective_date: Optional[str] = Form(default=None),
        expiration_date: Optional[str] = Form(default=None),
        operational_note: str = Form(default=""),
        file: UploadFile = File(...),
        actor: Dict[str, Any] = Depends(_require_asset_admin),
    ):
        if document_type not in ASSET_DOC_TYPES:
            raise HTTPException(status_code=400, detail=f"Unknown document type: {document_type}")
        if photo_kind and photo_kind not in PHOTO_SUBTYPES:
            raise HTTPException(status_code=400, detail=f"Unknown photo type: {photo_kind}")
        if document_type != DOC_ASSET_PHOTO and photo_kind:
            raise HTTPException(status_code=400, detail="photo_kind only valid for asset_photo")

        if effective_date and not _is_iso_date(effective_date):
            raise HTTPException(status_code=400, detail="effective_date must be ISO yyyy-mm-dd")
        if expiration_date and not _is_iso_date(expiration_date):
            raise HTTPException(status_code=400, detail="expiration_date must be ISO yyyy-mm-dd")

        await _get_asset_or_404(asset_id)

        # Cap per-asset
        existing = await db.operational_attachments.count_documents(
            {"host_kind": ASSET_HOST_KIND, "host_id": asset_id, "tenant_id": DEFAULT_TENANT_ID}
        )
        if existing >= MAX_PER_ASSET:
            raise HTTPException(
                status_code=400,
                detail=f"This asset already has {MAX_PER_ASSET} documents on file.",
            )

        content_type = (file.content_type or "").lower()
        is_image = content_type in ALLOWED_IMAGE_MIMES
        is_pdf = content_type in ALLOWED_PDF_MIMES
        if not (is_image or is_pdf):
            raise HTTPException(
                status_code=400,
                detail="Supported file types: image (jpg/png/webp/heic/gif) or PDF.",
            )
        raw = await file.read()
        size = len(raw)
        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
        if is_image and size > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="Image is over the 10 MB limit.")
        if is_pdf and size > MAX_PDF_BYTES:
            raise HTTPException(status_code=400, detail="PDF is over the 25 MB limit.")

        note = (operational_note or "").strip()[:500]
        att_id = str(uuid.uuid4())
        sha256_hex = hashlib.sha256(raw).hexdigest()

        ext = (content_type.split("/", 1)[-1] or "bin").replace("jpeg", "jpg")
        r2_key: Optional[str] = None
        storage_backend = "inline_b64"
        if photo_storage.is_configured():
            try:
                ref = await photo_storage.upload_photo_bytes(
                    raw,
                    ext=ext,
                    source_id=f"asset/{asset_id}/{document_type}/{att_id}",
                    content_type=content_type,
                )
                if ref.startswith("photo://"):
                    _, _, rest = ref.partition("photo://")
                    _, _, key_part = rest.partition("/")
                    r2_key = key_part or None
                if r2_key:
                    storage_backend = "r2"
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[asset-documents] R2 upload failed · inline fallback: {exc}")

        doc: Dict[str, Any] = {
            "id": att_id,
            "tenant_id": DEFAULT_TENANT_ID,
            "host_kind": ASSET_HOST_KIND,
            "host_id": asset_id,
            "type": document_type,
            "uploaded_by": _actor_label(actor),
            "uploaded_role": _actor_role(actor),
            "uploaded_at": _now_iso(),
            "operational_note": note,
            "filename": (file.filename or "document").strip()[:255],
            "content_type": content_type,
            "size_bytes": size,
            "sha256": sha256_hex,
            "storage_backend": storage_backend,
        }
        if photo_kind:
            doc["photo_kind"] = photo_kind
        if effective_date:
            doc["effective_date"] = effective_date
        if expiration_date:
            doc["expiration_date"] = expiration_date
        if storage_backend == "r2":
            doc["r2_key"] = r2_key
        else:
            doc["data_b64"] = base64.b64encode(raw).decode("ascii")

        await db.operational_attachments.insert_one(doc)

        # Mirror expiration onto equipment_master for fast dashboard reads.
        mirror_field = renewal_mirror_field(document_type)
        if mirror_field and expiration_date:
            await db.equipment_master.update_one(
                {"id": asset_id},
                {"$set": {mirror_field: expiration_date,
                          f"{mirror_field}_source_doc_id": att_id,
                          "updated_at": _now_iso()}},
            )

        return _public_doc(doc)

    # ── LIST ───────────────────────────────────────────────────────
    @router.get("/assets/{asset_id}/documents")
    async def list_asset_documents(
        asset_id: str = Path(...),
        document_type: Optional[str] = Query(default=None),
        actor: Dict[str, Any] = Depends(_require_asset_admin),
    ):
        await _get_asset_or_404(asset_id)
        q: Dict[str, Any] = {
            "host_kind": ASSET_HOST_KIND,
            "host_id": asset_id,
            "tenant_id": DEFAULT_TENANT_ID,
        }
        if document_type:
            if document_type not in ASSET_DOC_TYPES:
                raise HTTPException(status_code=400, detail="Unknown document type")
            q["type"] = document_type
        cur = db.operational_attachments.find(q, {"_id": 0, "data_b64": 0, "r2_key": 0}).sort("uploaded_at", -1)
        items = [_public_doc(d) async for d in cur]
        # Filter sensitive types for non-admin/asset-admin (already gated, but defensive)
        items = _filter_sensitive(items, _is_admin_or_asset_admin(actor))
        return {"count": len(items), "items": items}

    # ── FETCH BINARY ───────────────────────────────────────────────
    @router.get("/assets/{asset_id}/documents/{attachment_id}/file")
    async def get_asset_document_file(
        asset_id: str = Path(...),
        attachment_id: str = Path(...),
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "host_id": asset_id, "host_kind": ASSET_HOST_KIND,
             "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        backend = doc.get("storage_backend") or ("r2" if doc.get("r2_key") else "inline_b64")
        if backend == "r2" and doc.get("r2_key"):
            try:
                ref = f"photo://{photo_storage._env('S3_BUCKET')}/{doc['r2_key']}"  # noqa: SLF001
                raw = await photo_storage.read_photo_bytes(ref)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[asset-documents] R2 read failed: {exc}")
                if doc.get("data_b64"):
                    raw = base64.b64decode(doc["data_b64"])
                else:
                    raise HTTPException(status_code=502, detail="Document storage temporarily unavailable")
        else:
            raw = base64.b64decode(doc.get("data_b64") or "")
        return Response(
            content=raw,
            media_type=doc.get("content_type") or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{doc.get("filename","document")}"',
                "Cache-Control": "private, max-age=300",
                "X-Content-Type-Options": "nosniff",
            },
        )

    # ── PATCH META (effective / expiration / note) ────────────────
    @router.patch("/assets/{asset_id}/documents/{attachment_id}")
    async def patch_asset_document_meta(
        asset_id: str,
        attachment_id: str,
        body: DocumentMetaPatch,
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "host_id": asset_id, "host_kind": ASSET_HOST_KIND,
             "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        update: Dict[str, Any] = {}
        if body.effective_date is not None:
            if body.effective_date and not _is_iso_date(body.effective_date):
                raise HTTPException(status_code=400, detail="effective_date must be ISO yyyy-mm-dd")
            update["effective_date"] = body.effective_date or None
        if body.expiration_date is not None:
            if body.expiration_date and not _is_iso_date(body.expiration_date):
                raise HTTPException(status_code=400, detail="expiration_date must be ISO yyyy-mm-dd")
            update["expiration_date"] = body.expiration_date or None
        if body.operational_note is not None:
            update["operational_note"] = (body.operational_note or "")[:500]
        if body.photo_kind is not None:
            if body.photo_kind and body.photo_kind not in PHOTO_SUBTYPES:
                raise HTTPException(status_code=400, detail="Unknown photo type")
            update["photo_kind"] = body.photo_kind or None
        if not update:
            return _public_doc(doc)
        await db.operational_attachments.update_one(
            {"id": attachment_id, "tenant_id": DEFAULT_TENANT_ID},
            {"$set": update},
        )
        # Mirror expiration date onto equipment_master if applicable.
        if "expiration_date" in update:
            mirror_field = renewal_mirror_field(doc.get("type") or "")
            if mirror_field:
                await db.equipment_master.update_one(
                    {"id": asset_id},
                    {"$set": {mirror_field: update["expiration_date"],
                              f"{mirror_field}_source_doc_id": attachment_id,
                              "updated_at": _now_iso()}},
                )
        merged = {**doc, **update}
        return _public_doc(merged)

    # ── DELETE ─────────────────────────────────────────────────────
    @router.delete("/assets/{asset_id}/documents/{attachment_id}")
    async def delete_asset_document(
        asset_id: str,
        attachment_id: str,
        actor: Dict[str, Any] = Depends(require_admin_dep),  # admin only for delete
    ):
        doc = await db.operational_attachments.find_one(
            {"id": attachment_id, "host_id": asset_id, "host_kind": ASSET_HOST_KIND,
             "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0, "storage_backend": 1, "r2_key": 1, "type": 1},
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        await db.operational_attachments.delete_one(
            {"id": attachment_id, "tenant_id": DEFAULT_TENANT_ID}
        )
        if doc.get("storage_backend") == "r2" and doc.get("r2_key"):
            try:
                ref = f"photo://{photo_storage._env('S3_BUCKET')}/{doc['r2_key']}"  # noqa: SLF001
                await photo_storage.delete_photo(ref)
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[asset-documents] R2 delete best-effort failed: {exc}")
        # If this doc was the renewal source, clear the mirror.
        mirror_field = renewal_mirror_field(doc.get("type") or "")
        if mirror_field:
            await db.equipment_master.update_one(
                {"id": asset_id, f"{mirror_field}_source_doc_id": attachment_id},
                {"$unset": {mirror_field: "", f"{mirror_field}_source_doc_id": ""}},
            )
        return {"ok": True, "id": attachment_id}

    # ── REQUIRED DOCS (per asset) ─────────────────────────────────
    @router.get("/assets/{asset_id}/required-documents")
    async def required_docs_for_asset(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        asset = await _get_asset_or_404(asset_id)
        asset_type = asset.get("asset_type")
        behavior: Dict[str, Any] = {}
        try:
            from services.asset_taxonomy import behavior_for
            behavior = behavior_for(asset_type) if asset_type else {}
        except Exception:
            behavior = {}
        base = required_documents_for(asset_type, behavior)
        # Apply D7 admin overrides
        required: List[str] = list(base)
        if asset_type:
            ov_row = await db.asset_required_doc_overrides.find_one(
                {"asset_type": asset_type}, {"_id": 0, "levels": 1},
            )
            levels = (ov_row or {}).get("levels") or {}
            # Promote any doc_type set to "required" that isn't already in base
            for d, lvl in levels.items():
                if lvl == "required" and d in ASSET_DOC_TYPES and d not in required:
                    required.append(d)
            # Demote any base doc_type that's been moved off "required"
            required = [
                d for d in required
                if levels.get(d, "required") == "required"
            ]
        # Determine which required docs are already on file.
        present_cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "host_id": asset_id, "tenant_id": DEFAULT_TENANT_ID,
             "type": {"$in": required}},
            {"_id": 0, "type": 1, "expiration_date": 1},
        )
        present_types: set = set()
        async for d in present_cursor:
            present_types.add(d.get("type"))
        missing = [t for t in required if t not in present_types]
        return {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "required_documents": [{"document_type": t, "label": doc_label(t),
                                     "uploaded": t in present_types} for t in required],
            "missing_count": len(missing),
        }

    @router.get("/assets/{asset_id}/missing-photos")
    async def missing_photos_for_asset(
        asset_id: str = Path(...),
        _: Any = Depends(require_any_portal_dep),
    ):
        await _get_asset_or_404(asset_id)
        present_cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "host_id": asset_id, "tenant_id": DEFAULT_TENANT_ID,
             "type": DOC_ASSET_PHOTO},
            {"_id": 0, "photo_kind": 1},
        )
        present_kinds: set = set()
        async for d in present_cursor:
            pk = d.get("photo_kind")
            if pk:
                present_kinds.add(pk)
        return {
            "asset_id": asset_id,
            "photo_kinds": [
                {"photo_kind": k, "label": k.replace("_", " ").title(),
                 "uploaded": k in present_kinds}
                for k in PHOTO_SUBTYPES
            ],
        }

    # ── DASHBOARD: MISSING DOCUMENTS ──────────────────────────────
    @router.get("/dashboard/missing-documents")
    async def dashboard_missing_documents(
        actor: Dict[str, Any] = Depends(_dashboard_read_dep),  # noqa: ARG001
    ):
        """Platform-wide counts of active assets missing the required
        documents for their canonical asset_type. Read-only · informational.
        """
        # Pull active assets; ignore retired/disposed.
        active_cursor = db.equipment_master.find(
            {"$or": [{"is_active": True}, {"active": True},
                     {"status": {"$nin": ["retired", "disposed", "sold"]}}]},
            {"_id": 0, "id": 1, "asset_type": 1, "unit_number": 1, "display_label": 1},
        )
        assets: List[Dict[str, Any]] = [a async for a in active_cursor]
        # Pull all asset-doc rows in one shot, group by host_id.
        docs_cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0, "host_id": 1, "type": 1},
        )
        present_by_asset: Dict[str, set] = {}
        async for d in docs_cursor:
            present_by_asset.setdefault(d.get("host_id"), set()).add(d.get("type"))

        # Compute per-doc-type missing counts + per-asset summaries
        try:
            from services.asset_taxonomy import behavior_for
        except Exception:
            behavior_for = lambda _: {}  # noqa: E731

        per_type_missing: Dict[str, int] = {}
        per_asset_missing: List[Dict[str, Any]] = []
        for a in assets:
            asset_type = a.get("asset_type")
            req = required_documents_for(asset_type, behavior_for(asset_type) if asset_type else {})
            present = present_by_asset.get(a.get("id"), set())
            missing = [r for r in req if r not in present]
            for m in missing:
                per_type_missing[m] = per_type_missing.get(m, 0) + 1
            if missing:
                per_asset_missing.append({
                    "asset_id": a.get("id"),
                    "asset_type": asset_type,
                    "unit_number": a.get("unit_number") or a.get("display_label") or a.get("id"),
                    "missing_documents": missing,
                    "missing_count": len(missing),
                })

        per_type = [
            {"document_type": t, "label": doc_label(t), "count": c}
            for t, c in sorted(per_type_missing.items(), key=lambda x: -x[1])
        ]
        per_asset_missing.sort(key=lambda x: -x["missing_count"])
        return {
            "total_active_assets": len(assets),
            "assets_with_missing_documents": len(per_asset_missing),
            "per_document_type": per_type,
            "assets": per_asset_missing[:500],  # cap dashboard payload
        }

    # ── DASHBOARD: RENEWALS ───────────────────────────────────────
    @router.get("/dashboard/renewals")
    async def dashboard_renewals(
        bucket: str = Query("all", pattern="^(all|expired|30|60|90)$"),
        actor: Dict[str, Any] = Depends(_dashboard_read_dep),  # noqa: ARG001
    ):
        """Renewals by bucket: expired · 30d · 60d · 90d · all.

        Reads `operational_attachments` rows (host_kind=asset) that
        carry expiration_date. Joins to `equipment_master` to surface
        unit_number + asset_type.
        """
        # Pull all asset attachments with expiration dates
        cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "tenant_id": DEFAULT_TENANT_ID,
             "expiration_date": {"$nin": [None, ""]}},
            {"_id": 0, "data_b64": 0, "r2_key": 0},
        )
        rows: List[Dict[str, Any]] = []
        asset_ids: set = set()
        async for d in cursor:
            asset_ids.add(d.get("host_id"))
            rows.append(d)
        # Hydrate asset display data
        assets_map: Dict[str, Dict[str, Any]] = {}
        if asset_ids:
            ac = db.equipment_master.find(
                {"id": {"$in": list(asset_ids)}},
                {"_id": 0, "id": 1, "unit_number": 1, "display_label": 1, "asset_type": 1, "asset_class": 1},
            )
            async for a in ac:
                assets_map[a["id"]] = a

        out: List[Dict[str, Any]] = []
        for r in rows:
            days = _days_to(r.get("expiration_date"))
            asset = assets_map.get(r.get("host_id"), {})
            # Bucket
            if bucket == "expired" and (days is None or days >= 0):
                continue
            if bucket == "30" and (days is None or days < 0 or days > 30):
                continue
            if bucket == "60" and (days is None or days < 0 or days > 60):
                continue
            if bucket == "90" and (days is None or days < 0 or days > 90):
                continue
            out.append({
                "attachment_id": r.get("id"),
                "asset_id": r.get("host_id"),
                "unit_number": asset.get("unit_number") or asset.get("display_label") or r.get("host_id"),
                "asset_type": asset.get("asset_type"),
                "document_type": r.get("type"),
                "document_label": doc_label(r.get("type") or ""),
                "expiration_date": r.get("expiration_date"),
                "effective_date": r.get("effective_date"),
                "days_remaining": days,
            })
        # Bucket counters (always returned)
        counters = {"expired": 0, "30": 0, "60": 0, "90": 0, "total_tracked": len(rows)}
        for r in rows:
            d = _days_to(r.get("expiration_date"))
            if d is None:
                continue
            if d < 0:
                counters["expired"] += 1
            elif d <= 30:
                counters["30"] += 1
            elif d <= 60:
                counters["60"] += 1
            elif d <= 90:
                counters["90"] += 1
        out.sort(key=lambda x: (x.get("days_remaining") is None, x.get("days_remaining") or 0))
        return {"bucket": bucket, "counters": counters, "items": out[:500]}

    # ── DASHBOARD: RECENT UPLOADS ─────────────────────────────────
    @router.get("/dashboard/recent-uploads")
    async def dashboard_recent_uploads(
        limit: int = Query(20, ge=1, le=100),
        actor: Dict[str, Any] = Depends(_dashboard_read_dep),  # noqa: ARG001
    ):
        cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0, "data_b64": 0, "r2_key": 0},
        ).sort("uploaded_at", -1).limit(limit)
        rows = [d async for d in cursor]
        asset_ids = {r.get("host_id") for r in rows if r.get("host_id")}
        amap: Dict[str, Dict[str, Any]] = {}
        if asset_ids:
            ac = db.equipment_master.find(
                {"id": {"$in": list(asset_ids)}},
                {"_id": 0, "id": 1, "unit_number": 1, "display_label": 1, "asset_type": 1},
            )
            async for a in ac:
                amap[a["id"]] = a
        out = []
        for r in rows:
            a = amap.get(r.get("host_id"), {})
            out.append({
                **_public_doc(r),
                "unit_number": a.get("unit_number") or a.get("display_label") or r.get("host_id"),
                "asset_type": a.get("asset_type"),
            })
        return {"count": len(out), "items": out}

    # ── DASHBOARD: REQUIRED-DOCS CONFIG (read-only this round) ───
    @router.get("/dashboard/required-documents-config")
    async def required_documents_config(
        actor: Dict[str, Any] = Depends(_dashboard_read_dep),  # noqa: ARG001
    ):
        m = all_required_map()
        return {
            "count": len(m),
            "items": [
                {"asset_type": at, "required": [
                    {"document_type": t, "label": doc_label(t)} for t in docs
                ]}
                for at, docs in sorted(m.items())
            ],
        }

    # ── CSV EXPORTS ───────────────────────────────────────────────
    def _csv_response(rows: List[List[str]], filename: str) -> StreamingResponse:
        buf = io.StringIO()
        w = csv.writer(buf)
        for row in rows:
            w.writerow(row)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @router.get("/exports/assets.csv")
    async def export_assets_csv(
        active_only: bool = Query(True),
        asset_type: Optional[str] = Query(None),
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        q: Dict[str, Any] = {}
        if active_only:
            q["$or"] = [{"is_active": True}, {"active": True},
                        {"status": {"$nin": ["retired", "disposed", "sold"]}}]
        if asset_type:
            q["asset_type"] = asset_type
        cur = db.equipment_master.find(q, {
            "_id": 0, "id": 1, "unit_number": 1, "display_label": 1,
            "asset_class": 1, "asset_type": 1, "taxonomy_verified": 1,
            "make": 1, "model": 1, "year": 1, "serial_number": 1, "vin": 1,
            "license_plate": 1, "registration_state": 1,
            "registration_expiration": 1, "insurance_expiration": 1,
            "dot_expiration": 1, "calibration_expiration": 1,
            "warranty_expiration": 1, "lifecycle_status": 1,
            "ownership": 1, "division": 1,
        })
        headers = [
            "Unit Number", "Display Label", "Asset Class", "Asset Type",
            "Verified", "Make", "Model", "Year", "Serial", "VIN", "Plate",
            "State", "Registration Expires", "Insurance Expires",
            "DOT Expires", "Calibration Expires", "Warranty Expires",
            "Lifecycle", "Ownership", "Division",
        ]
        rows = [headers]
        async for a in cur:
            rows.append([
                a.get("unit_number") or a.get("display_label") or "",
                a.get("display_label") or "",
                a.get("asset_class") or "",
                a.get("asset_type") or "",
                "Yes" if a.get("taxonomy_verified") else "Needs Review",
                a.get("make") or "", a.get("model") or "",
                str(a.get("year") or ""), a.get("serial_number") or "",
                a.get("vin") or "", a.get("license_plate") or "",
                a.get("registration_state") or "",
                a.get("registration_expiration") or "",
                a.get("insurance_expiration") or "",
                a.get("dot_expiration") or "",
                a.get("calibration_expiration") or "",
                a.get("warranty_expiration") or "",
                a.get("lifecycle_status") or "",
                a.get("ownership") or "",
                a.get("division") or "",
            ])
        return _csv_response(rows, "masci-asset-inventory.csv")

    @router.get("/exports/renewals.csv")
    async def export_renewals_csv(
        bucket: str = Query("all", pattern="^(all|expired|30|60|90)$"),
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        # Reuse the renewals computation
        cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "tenant_id": DEFAULT_TENANT_ID,
             "expiration_date": {"$nin": [None, ""]}},
            {"_id": 0, "data_b64": 0, "r2_key": 0},
        )
        rows = [d async for d in cursor]
        asset_ids = {r.get("host_id") for r in rows if r.get("host_id")}
        amap: Dict[str, Dict[str, Any]] = {}
        if asset_ids:
            ac = db.equipment_master.find(
                {"id": {"$in": list(asset_ids)}},
                {"_id": 0, "id": 1, "unit_number": 1, "display_label": 1, "asset_type": 1},
            )
            async for a in ac:
                amap[a["id"]] = a
        out_rows = [["Unit Number", "Asset Type", "Document", "Expiration Date",
                     "Days Remaining", "Status"]]
        for r in rows:
            days = _days_to(r.get("expiration_date"))
            if bucket == "expired" and (days is None or days >= 0):
                continue
            if bucket == "30" and (days is None or days < 0 or days > 30):
                continue
            if bucket == "60" and (days is None or days < 0 or days > 60):
                continue
            if bucket == "90" and (days is None or days < 0 or days > 90):
                continue
            a = amap.get(r.get("host_id"), {})
            status = "Current"
            if days is None:
                status = "Pending Update"
            elif days < 0:
                status = "Expired"
            elif days <= 30:
                status = "Expiring Soon · 30 Days"
            elif days <= 60:
                status = "Expiring Soon · 60 Days"
            elif days <= 90:
                status = "Expiring Soon · 90 Days"
            out_rows.append([
                a.get("unit_number") or a.get("display_label") or r.get("host_id") or "",
                a.get("asset_type") or "",
                doc_label(r.get("type") or ""),
                r.get("expiration_date") or "",
                str(days) if days is not None else "",
                status,
            ])
        return _csv_response(out_rows, "masci-asset-renewals.csv")

    @router.get("/exports/missing-documents.csv")
    async def export_missing_documents_csv(
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        # Recompute missing-documents directly (no __wrapped__ on FastAPI endpoints)
        active_cursor = db.equipment_master.find(
            {"$or": [{"is_active": True}, {"active": True},
                     {"status": {"$nin": ["retired", "disposed", "sold"]}}]},
            {"_id": 0, "id": 1, "asset_type": 1, "unit_number": 1, "display_label": 1},
        )
        assets = [a async for a in active_cursor]
        docs_cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0, "host_id": 1, "type": 1},
        )
        present_by_asset: Dict[str, set] = {}
        async for d in docs_cursor:
            present_by_asset.setdefault(d.get("host_id"), set()).add(d.get("type"))
        try:
            from services.asset_taxonomy import behavior_for
        except Exception:
            behavior_for = lambda _: {}  # noqa: E731
        rows = [["Unit Number", "Asset Type", "Missing Document"]]
        for a in assets:
            asset_type = a.get("asset_type")
            req = required_documents_for(asset_type, behavior_for(asset_type) if asset_type else {})
            present = present_by_asset.get(a.get("id"), set())
            for r in req:
                if r not in present:
                    rows.append([
                        a.get("unit_number") or a.get("display_label") or "",
                        asset_type or "",
                        doc_label(r),
                    ])
        return _csv_response(rows, "masci-missing-documents.csv")

    # ── ASSET PROFILE PDF ─────────────────────────────────────────
    @router.get("/assets/{asset_id}/profile.pdf")
    async def asset_profile_pdf(
        asset_id: str = Path(...),
        actor: Dict[str, Any] = Depends(_require_asset_admin),  # noqa: ARG001
    ):
        asset = await _get_asset_or_404(asset_id)
        # Gather docs (without binaries)
        docs_cursor = db.operational_attachments.find(
            {"host_kind": ASSET_HOST_KIND, "host_id": asset_id, "tenant_id": DEFAULT_TENANT_ID},
            {"_id": 0, "data_b64": 0, "r2_key": 0},
        )
        docs = [d async for d in docs_cursor]
        # Recent inspections (last 5)
        insp_cursor = db.equipment_inspections.find(
            {"$or": [{"equipment_unit": asset.get("unit_number")},
                     {"truck_unit_number": asset.get("unit_number")},
                     {"asset_id": asset_id}]},
            {"_id": 0, "id": 1, "inspection_date": 1, "fail_count": 1,
             "pass_count": 1, "kind": 1, "out_of_service": 1},
        ).sort("inspection_date", -1).limit(5)
        recent_inspections = [d async for d in insp_cursor]

        pdf_bytes = await asyncio.to_thread(_render_asset_profile_pdf, asset, docs, recent_inspections)
        unit = asset.get("unit_number") or asset.get("display_label") or asset_id
        safe_unit = "".join(ch if ch.isalnum() else "_" for ch in str(unit))
        fname = f"MASCI_Asset_Profile_{safe_unit}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{fname}"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    # Decide mount strategy.
    if hasattr(app_or_router, "include_router") and not isinstance(app_or_router, APIRouter):
        # FastAPI app
        app_or_router.include_router(router)
    else:
        app_or_router.include_router(router)
    return router


# ──────────────────────────────────────────────────────────────────
# MASCI Asset Profile PDF renderer · reuses safety_forms style.
# ──────────────────────────────────────────────────────────────────


def _render_asset_profile_pdf(
    asset: Dict[str, Any],
    docs: List[Dict[str, Any]],
    inspections: List[Dict[str, Any]],
) -> bytes:
    """Synchronous PDF render (called via asyncio.to_thread)."""
    from weasyprint import HTML  # local import keeps router importable in tests
    from routes.safety_forms import _BASE_CSS, _logo_data_uri, _safe  # noqa: PLC2701

    unit = asset.get("unit_number") or asset.get("display_label") or asset.get("id") or ""
    asset_class = asset.get("asset_class") or ""
    asset_type = asset.get("asset_type") or ""
    make = asset.get("make") or ""
    model = asset.get("model") or ""
    year = asset.get("year") or ""
    vin = asset.get("vin") or ""
    serial = asset.get("serial_number") or ""
    plate = asset.get("license_plate") or ""
    ownership = asset.get("ownership") or ""
    division = asset.get("division") or ""
    region = asset.get("region") or ""

    def _row(k: str, v: Any) -> str:
        return f"<div class='k'>{_safe(k)}</div><div class='v'>{_safe(v or '—')}</div>"

    classification_html = (
        "<div class='section'><h2>Classification</h2><div class='kv'>"
        + _row("Asset Class", asset_class)
        + _row("Asset Type", asset_type)
        + _row("Verified", "Yes" if asset.get("taxonomy_verified") else "Needs Review")
        + _row("Lifecycle", asset.get("lifecycle_status"))
        + "</div></div>"
    )
    ident_html = (
        "<div class='section'><h2>Identifiers</h2><div class='kv'>"
        + _row("Make", make)
        + _row("Model", model)
        + _row("Year", year)
        + _row("Serial", serial)
        + _row("VIN", vin)
        + _row("Plate", plate)
        + _row("State", asset.get("registration_state"))
        + "</div></div>"
    )
    ownership_html = (
        "<div class='section'><h2>Ownership &amp; Organization</h2><div class='kv'>"
        + _row("Ownership", ownership)
        + _row("Division", division)
        + _row("Region", region)
        + _row("Department", asset.get("department"))
        + "</div></div>"
    )
    renewals_html = (
        "<div class='section'><h2>Renewals</h2><div class='kv'>"
        + _row("Registration Expires", asset.get("registration_expiration"))
        + _row("Insurance Expires", asset.get("insurance_expiration"))
        + _row("DOT Expires", asset.get("dot_expiration"))
        + _row("Calibration Expires", asset.get("calibration_expiration"))
        + _row("Warranty Expires", asset.get("warranty_expiration"))
        + "</div></div>"
    )

    # Documents table — non-sensitive by default in the PDF (since PDF
    # is downloadable). Sensitive types are listed by label only,
    # without filenames or counts beyond "On File".
    doc_rows = []
    for d in docs:
        t = d.get("type") or ""
        label = doc_label(t)
        if is_sensitive(t):
            doc_rows.append(
                f"<tr><td>{_safe(label)}</td><td>On File · Restricted Access</td>"
                f"<td>{_safe(d.get('expiration_date') or '—')}</td></tr>"
            )
        else:
            doc_rows.append(
                f"<tr><td>{_safe(label)}</td>"
                f"<td>{_safe(d.get('filename') or '—')}</td>"
                f"<td>{_safe(d.get('expiration_date') or '—')}</td></tr>"
            )
    docs_body = "".join(doc_rows) or (
        "<tr><td colspan=3 style='text-align:center;color:#94a3b8'>"
        "No documents on file</td></tr>"
    )
    docs_html = (
        "<div class='section'><h2>Documents</h2><table>"
        "<thead><tr><th>Document</th><th>Filename</th><th>Expires</th></tr></thead>"
        f"<tbody>{docs_body}</tbody>"
        "</table></div>"
    )

    insp_rows = []
    for i in inspections:
        insp_rows.append(
            f"<tr><td>{_safe(i.get('kind') or 'Inspection')}</td>"
            f"<td>{_safe(i.get('inspection_date') or '—')}</td>"
            f"<td>{int(i.get('pass_count') or 0)}</td>"
            f"<td>{int(i.get('fail_count') or 0)}</td>"
            f"<td>{_safe(i.get('out_of_service') or '—')}</td></tr>"
        )
    insp_body = "".join(insp_rows) or (
        "<tr><td colspan=5 style='text-align:center;color:#94a3b8'>"
        "No recent inspections</td></tr>"
    )
    insp_html = (
        "<div class='section'><h2>Recent Inspections</h2><table>"
        "<thead><tr><th>Type</th><th>Date</th><th>Pass</th><th>Fail</th><th>OOS</th></tr></thead>"
        f"<tbody>{insp_body}</tbody>"
        "</table></div>"
    )

    generated = format_platform_stamp(datetime.now(timezone.utc))
    html_doc = f"""<!doctype html><html><head><meta charset='utf-8'><style>{_BASE_CSS}</style></head>
    <body>
      <div class='head'>
        <div>
          <div class='eyebrow'>MASCI · Asset Administration</div>
          <h1>{_safe(unit)} &middot; Asset Profile</h1>
          <p class='sub'>{_safe(asset_class)} &middot; {_safe(asset_type)}</p>
        </div>
        <div style='text-align:right'>
          <div class='logo'><img src='{_logo_data_uri()}' /></div>
        </div>
      </div>
      {classification_html}
      {ident_html}
      {ownership_html}
      {renewals_html}
      {docs_html}
      {insp_html}
      <div class='foot'>MASCI General Contractors Inc. &middot; Generated {generated} &middot; Confidential</div>
      {_t1541_asset_audit_block(asset)}
    </body></html>"""
    return HTML(string=html_doc).write_pdf()


def _t1541_asset_audit_block(asset) -> str:
    """TRACK 15.42 · additive foundation audit block for asset profile PDFs."""
    try:
        from pdf_branding import build_audit_block_html
        a = asset if isinstance(asset, dict) else {}
        return build_audit_block_html(
            record_id=(a.get("unit_number") or a.get("id") or "—"),
            source_module="assets.profile",
            project=(a.get("project_name") or a.get("assigned_project") or None),
            generated_by="system",
        )
    except Exception:
        return ""
