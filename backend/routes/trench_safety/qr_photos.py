"""Trench Safety · Phase 7 — QR labels + Photo management.

Two clean read/write surfaces appended to the existing /api/trench-safety
namespace. No new collections beyond `trench_safety_photos`. No external
storage system — photos are stored as base64 inside the document (matches
the existing `safety_documents` pattern). Bounded to 8 MB per photo.

QR labels are rendered server-side as PNG via the `qrcode` library. The
QR target is the stable, never-changing `/trench-safety/assets/{asset_id}`
public URL — no new IDs are minted; existing asset_id is the QR value.
"""
from __future__ import annotations

import base64
import io
import re
import uuid
from typing import Any, Dict, List, Optional

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from ._helpers import now_iso, write_audit


PHOTO_CATEGORIES = (
    "Front", "Rear", "Side", "Serial Number", "Manufacturer Plate",
    "QR Label", "Inspection Photo", "Damage Photo", "Repair Photo",
    "Deployment Photo", "Other",
)
PHOTO_VISIBILITIES = ("internal", "field_safe")
PHOTO_SOURCES = ("Asset Detail", "Inspection", "Repair", "Damage Report", "QR Field Report")

# 8 MB hard cap per photo (matches existing safety_documents inline pattern).
_MAX_PHOTO_BYTES = 8 * 1024 * 1024
_DATA_URL_RE = re.compile(r"^data:image/(png|jpeg|jpg|webp|heic);base64,(.+)$", re.I)


class PhotoUploadBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    image_data_url: str = Field(min_length=32)   # data:image/<fmt>;base64,...
    category: str = Field(min_length=1)
    caption: Optional[str] = Field(default="", max_length=500)
    source: str = "Asset Detail"
    linked_record_id: Optional[str] = None
    visibility: str = "internal"


def _decode_data_url(data_url: str) -> bytes:
    m = _DATA_URL_RE.match(data_url.strip())
    if not m:
        raise HTTPException(422, "image_data_url must be a base64 data URL (png/jpeg/webp/heic)")
    try:
        raw = base64.b64decode(m.group(2), validate=True)
    except Exception:  # noqa: BLE001
        raise HTTPException(422, "image_data_url base64 payload is invalid")
    if len(raw) > _MAX_PHOTO_BYTES:
        raise HTTPException(413, f"image exceeds {_MAX_PHOTO_BYTES // (1024*1024)} MB limit")
    return raw


def _photo_public_view(photo: Dict[str, Any]) -> Dict[str, Any]:
    """Field-safe projection — strips uploader email / source IDs / linked records."""
    return {
        "id": photo["id"],
        "asset_id": photo["asset_id"],
        "category": photo["category"],
        "caption": photo.get("caption") or "",
        "image_data_url": photo.get("image_data_url"),
        "uploaded_at": photo.get("uploaded_at"),
    }


def register_qr_and_photo_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
    require_any_portal,
    require_shop_or_admin,
) -> None:

    # ────────────────────────────────────────────────────────────────
    # § QR label generation
    # ────────────────────────────────────────────────────────────────

    @api_router.get("/trench-safety/assets/{ident}/qr-label.png")
    async def qr_label_png(
        ident: str,
        size: int = Query(default=10, ge=4, le=20),
        actor: dict = Depends(require_safety_or_admin),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]}, {"_id": 0}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        target = f"/trench-safety/assets/{asset['asset_id']}"
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=4,
        )
        qr.add_data(target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        png_bytes = buf.getvalue()

        await write_audit(
            db, kind="trench_asset_qr_generated", asset_id=asset["asset_id"],
            actor=actor, detail={"target": target, "size": size, "bytes": len(png_bytes)},
        )
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f'inline; filename="trench-safety-{asset["asset_id"]}-qr.png"',
                "X-Trench-Asset-Id": asset["asset_id"],
                "X-Trench-QR-Target": target,
            },
        )

    @api_router.get("/trench-safety/assets/{ident}/qr-label")
    async def qr_label_meta(
        ident: str,
        size: int = Query(default=10, ge=4, le=20),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]}, {"_id": 0}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        size_str = (asset.get("size") or "").strip()
        type_str = (asset.get("asset_type") or "Trench Box").strip()
        label_lines = [
            "MASCI TRENCH SAFETY",
            asset["asset_id"],
            (f"{type_str} · {size_str}" if size_str else type_str).strip(" · "),
            "SCAN FOR TABULATED DATA + INSPECTION",
        ]
        # TRENCH-ASSET-ASSIGNMENT-QR-FIX · Phase 5: embed the QR PNG
        # as a base64 data URL so the frontend `<img src=…>` renders
        # without a follow-up authenticated request (the PNG endpoint
        # requires a token that browsers can't attach via <img>, which
        # was producing the broken-image icon in production).
        import base64  # noqa: PLC0415
        target = f"/trench-safety/assets/{asset['asset_id']}"
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=4,
        )
        qr.add_data(target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return {
            "asset_id": asset["asset_id"],
            "target_url": target,
            "png_url": f"/api/trench-safety/assets/{asset['asset_id']}/qr-label.png",
            "png_data_url": f"data:image/png;base64,{png_b64}",
            "label_lines": label_lines,
        }

    @api_router.post("/trench-safety/assets/{ident}/qr-label/audit")
    async def qr_label_action_audit(
        ident: str,
        body: Dict[str, str],
        actor: dict = Depends(require_safety_or_admin),
    ):
        action = (body.get("action") or "").strip()
        if action not in {"downloaded", "printed", "reprinted"}:
            raise HTTPException(422, "action must be downloaded|printed|reprinted")
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]}, {"_id": 0, "asset_id": 1}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        kind = {
            "downloaded": "trench_asset_qr_label_downloaded",
            "printed":    "trench_asset_qr_label_printed",
            "reprinted":  "trench_asset_qr_reprinted",
        }[action]
        await write_audit(db, kind=kind, asset_id=asset["asset_id"], actor=actor, detail={})
        return {"ok": True, "kind": kind}

    # ────────────────────────────────────────────────────────────────
    # § Photo management
    # ────────────────────────────────────────────────────────────────

    @api_router.get("/trench-safety/assets/{ident}/photos")
    async def list_photos(
        ident: str,
        category: Optional[str] = Query(default=None),
        visibility: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
        _actor: dict = Depends(require_any_portal),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]}, {"_id": 0, "asset_id": 1}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        q: Dict[str, Any] = {"asset_id": asset["asset_id"]}
        if category:
            q["category"] = category
        if visibility:
            q["visibility"] = visibility
        items = await db.trench_safety_photos.find(q, {"_id": 0}).sort("uploaded_at", -1).limit(limit).to_list(limit)
        return {"items": items, "count": len(items)}

    @api_router.post("/trench-safety/assets/{ident}/photos")
    async def upload_photo(
        ident: str,
        payload: PhotoUploadBody,
        actor: dict = Depends(require_safety_or_admin),
    ):
        if payload.category not in PHOTO_CATEGORIES:
            raise HTTPException(422, f"category must be one of {list(PHOTO_CATEGORIES)}")
        if payload.visibility not in PHOTO_VISIBILITIES:
            raise HTTPException(422, f"visibility must be one of {list(PHOTO_VISIBILITIES)}")
        if payload.source not in PHOTO_SOURCES:
            raise HTTPException(422, f"source must be one of {list(PHOTO_SOURCES)}")
        # Decode for size check; we still persist the data URL form for direct <img src>
        _decode_data_url(payload.image_data_url)

        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}]}, {"_id": 0, "asset_id": 1, "id": 1}
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")

        actor_email = "unknown"
        if isinstance(actor, dict):
            actor_email = actor.get("email") or actor.get("_actor") or "unknown"
        actor_for_audit = actor if isinstance(actor, dict) else {"_actor": "shop_or_admin", "email": actor_email}
        doc = {
            "id": str(uuid.uuid4()),
            "asset_id": asset["asset_id"],
            "asset_uuid": asset["id"],
            "category": payload.category,
            "caption": payload.caption or "",
            "image_data_url": payload.image_data_url,
            "source": payload.source,
            "linked_record_id": payload.linked_record_id,
            "visibility": payload.visibility,
            "uploaded_by": actor_email,
            "uploaded_at": now_iso(),
        }
        await db.trench_safety_photos.insert_one(doc)
        doc.pop("_id", None)
        await write_audit(
            db, kind="trench_asset_photo_uploaded", asset_id=asset["asset_id"],
            actor=actor_for_audit, detail={
                "photo_id": doc["id"], "category": doc["category"],
                "visibility": doc["visibility"], "source": doc["source"],
                "linked_record_id": doc.get("linked_record_id"),
            },
        )
        return doc

    @api_router.delete("/trench-safety/photos/{photo_id}")
    async def delete_photo(
        photo_id: str,
        actor: dict = Depends(require_safety_or_admin),
    ):
        existing = await db.trench_safety_photos.find_one({"id": photo_id}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Photo not found")
        await db.trench_safety_photos.delete_one({"id": photo_id})
        await write_audit(
            db, kind="trench_asset_photo_deleted",
            asset_id=existing["asset_id"], actor=actor,
            detail={"photo_id": photo_id, "category": existing.get("category")},
        )
        return {"ok": True, "deleted_id": photo_id}

    # ────────────────────────────────────────────────────────────────
    # § Public — field-safe photos only (no auth)
    # ────────────────────────────────────────────────────────────────

    @api_router.get("/trench-safety/public/assets/{ident}/photos")
    async def public_photos(
        ident: str,
        limit: int = Query(default=50, ge=1, le=200),
    ):
        asset = await db.trench_safety_assets.find_one(
            {"$or": [{"asset_id": ident}, {"id": ident}], "is_active": True},
            {"_id": 0, "asset_id": 1},
        )
        if not asset:
            raise HTTPException(404, "Trench safety asset not found")
        items = await db.trench_safety_photos.find(
            {"asset_id": asset["asset_id"], "visibility": "field_safe"},
            {"_id": 0},
        ).sort("uploaded_at", -1).limit(limit).to_list(limit)
        return {
            "items": [_photo_public_view(p) for p in items],
            "count": len(items),
        }
