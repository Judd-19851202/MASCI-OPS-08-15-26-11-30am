"""
routes/promo_assets.py — iter347 (Promo Asset Library)

Admin-only management surface for the MASCI promo asset library.
Builds on the existing R2 client via `promo_assets_storage.py`.

Routes (all `/api/admin/promo-assets/*`, all admin-strict):
  GET    /              → list assets (filter by category / search / visibility)
  GET    /categories    → enum list (UI dropdown source of truth)
  GET    /manifest.json → full manifest export (downloadable JSON)
  POST   /              → upload multipart {file, name, category, ...}
  GET    /{id}          → single asset detail (with fresh presigned URLs)
  PATCH  /{id}          → edit metadata (name/category/tags/visibility/description)
  DELETE /{id}          → delete (R2 object best-effort + mongo row)
  GET    /{id}/download → 302 → presigned download URL
"""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field

import promo_assets_storage as paf

logger = logging.getLogger(__name__)

# Bounded category list — single source of truth for the UI dropdown.
# Mirrored in the frontend (`AdminPromoAssets.jsx`). Keep them aligned.
PROMO_CATEGORIES: List[str] = [
    "Home / Platform Overview",
    "HR",
    "Safety",
    "Safety Forms",
    "Field",
    "Field Leadership",
    "Dispatch",
    "Shop",
    "QA/QC",
    "Daily Reports",
    "Incidents",
    "JHAs",
    "DVIR",
    "Equipment & PPE Accountability",
    "Admin / Access Control",
    "Admin Reference Lookup",
    "Bilingual / ES",
    "PDFs / Exports",
    "Mobile",
    "Tablet",
    "Hero Loops",
    "Social Cuts",
    "Transitions / Logo",
    "Raw Screen Captures",
    "Edited Clips",
    "Final Exports",
]

PROMO_VISIBILITIES = ("internal", "public")


class PromoAssetPatch(BaseModel):
    """All fields optional — partial PATCH."""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    visibility: Optional[str] = None
    duration_seconds: Optional[float] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[str] = None
    poster_ref: Optional[str] = None  # promo:// reference to poster image


def _public_row(doc: dict) -> dict:
    """Strip mongo _id and normalize types for JSON response."""
    if not doc:
        return doc
    out = {k: v for k, v in doc.items() if k != "_id"}
    # datetime → iso string
    for fld in ("created_at", "updated_at"):
        v = out.get(fld)
        if isinstance(v, datetime):
            out[fld] = v.isoformat()
    return out


def _ext_from_filename(fn: str) -> str:
    if not fn or "." not in fn:
        return "bin"
    return fn.rsplit(".", 1)[-1].lower()


def build_promo_assets_router(
    db,
    require_admin_strict_dep: Callable,
) -> APIRouter:
    """Assemble the /api/admin/promo-assets/* router."""
    router = APIRouter(
        prefix="/api/admin/promo-assets",
        tags=["promo-assets"],
        dependencies=[Depends(require_admin_strict_dep)],
    )
    coll = db["promo_assets"]

    @router.get("/categories")
    async def list_categories():
        """Single source of truth for the UI dropdown."""
        return {"categories": PROMO_CATEGORIES, "visibilities": list(PROMO_VISIBILITIES)}

    @router.get("")
    async def list_assets(
        category: Optional[str] = Query(default=None),
        visibility: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        tag: Optional[str] = Query(default=None),
    ):
        """List assets with optional filters. Returns metadata only — call
        `/{id}` to get a fresh presigned playback URL."""
        match: dict = {}
        if category:
            match["category"] = category
        if visibility:
            match["visibility"] = visibility
        if tag:
            match["tags"] = tag
        if q:
            ql = q.strip()
            if ql:
                match["$or"] = [
                    {"name": {"$regex": ql, "$options": "i"}},
                    {"description": {"$regex": ql, "$options": "i"}},
                    {"tags": {"$regex": ql, "$options": "i"}},
                ]
        cursor = coll.find(match, {"_id": 0}).sort("created_at", -1).limit(500)
        items = [_public_row(d) async for d in cursor]
        return {
            "ok": True,
            "count": len(items),
            "items": items,
            "categories": PROMO_CATEGORIES,
        }

    @router.get("/manifest.json")
    async def manifest_json():
        """Downloadable manifest of every asset — JSON. Editors / external
        agencies can pull this to feed their pipeline."""
        cursor = coll.find({}, {"_id": 0}).sort("created_at", -1)
        items = [_public_row(d) async for d in cursor]
        return JSONResponse(
            {
                "version": 1,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "categories": PROMO_CATEGORIES,
                "count": len(items),
                "items": items,
            },
            headers={"Content-Disposition": 'attachment; filename="masci-promo-manifest.json"'},
        )

    @router.post("")
    async def upload_asset(
        file: UploadFile = File(...),
        name: str = Form(...),
        category: str = Form(...),
        description: str = Form(""),
        tags: str = Form(""),  # comma-separated
        visibility: str = Form("internal"),
        duration_seconds: Optional[float] = Form(default=None),
        resolution: Optional[str] = Form(default=None),
        aspect_ratio: Optional[str] = Form(default=None),
    ):
        """Upload a promo asset. Multipart only — file is streamed straight
        through to R2. Cap at 500 MB to stop accidental project-archive
        uploads. Anything bigger should be handed off externally."""
        # ─── validate ─────────────────────────────────────────────────
        if category not in PROMO_CATEGORIES:
            raise HTTPException(400, f"Unknown category. Allowed: {PROMO_CATEGORIES}")
        if visibility not in PROMO_VISIBILITIES:
            raise HTTPException(400, f"visibility must be one of {PROMO_VISIBILITIES}")
        if not paf.is_configured():
            raise HTTPException(503, "Object storage isn't configured on this deploy")

        raw = await file.read()
        if not raw:
            raise HTTPException(400, "Empty upload")
        size_mb = len(raw) / (1024 * 1024)
        if size_mb > 500:
            raise HTTPException(
                413,
                f"File too large ({size_mb:.0f} MB). 500 MB cap per asset — "
                "hand bigger masters off externally.",
            )

        ext = _ext_from_filename(file.filename or "")
        # ─── upload to R2 ────────────────────────────────────────────
        ref, key = await paf.upload_bytes(
            raw,
            category=category,
            name_hint=name,
            ext=ext,
            content_type=file.content_type,
        )

        # ─── persist mongo metadata row ──────────────────────────────
        tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
        now = datetime.now(timezone.utc)
        doc = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "category": category,
            "description": (description or "").strip(),
            "tags": tag_list,
            "visibility": visibility,
            "file_ref": ref,
            "file_key": key,
            "file_name": file.filename or "",
            "file_type": ext,
            "file_size_mb": round(size_mb, 2),
            "content_type": file.content_type or paf._guess_content_type(ext),  # noqa: SLF001
            "duration_seconds": duration_seconds,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "poster_ref": None,
            "created_at": now,
            "updated_at": now,
        }
        await coll.insert_one(dict(doc))  # copy so insert_one doesn't mutate ours
        return {"ok": True, "asset": _public_row(doc)}

    async def _attach_playback_url(doc: dict) -> dict:
        """Mint a fresh 7-day presigned URL for the asset's file_ref."""
        out = _public_row(doc)
        try:
            out["playback_url"] = await paf.presigned_url(doc["file_ref"])
        except Exception as e:  # noqa: BLE001
            logger.warning(f"presign failed for {doc.get('id')}: {e}")
            out["playback_url"] = None
        if doc.get("poster_ref"):
            try:
                out["poster_url"] = await paf.presigned_url(doc["poster_ref"])
            except Exception:  # noqa: BLE001
                out["poster_url"] = None
        return out

    @router.get("/{asset_id}")
    async def get_asset(asset_id: str):
        doc = await coll.find_one({"id": asset_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Asset not found")
        return {"ok": True, "asset": await _attach_playback_url(doc)}

    @router.patch("/{asset_id}")
    async def patch_asset(asset_id: str, body: PromoAssetPatch):
        doc = await coll.find_one({"id": asset_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Asset not found")
        updates = body.dict(exclude_none=True)
        if "category" in updates and updates["category"] not in PROMO_CATEGORIES:
            raise HTTPException(400, "Unknown category")
        if "visibility" in updates and updates["visibility"] not in PROMO_VISIBILITIES:
            raise HTTPException(400, "Unknown visibility")
        updates["updated_at"] = datetime.now(timezone.utc)
        await coll.update_one({"id": asset_id}, {"$set": updates})
        fresh = await coll.find_one({"id": asset_id}, {"_id": 0})
        return {"ok": True, "asset": await _attach_playback_url(fresh)}

    @router.delete("/{asset_id}")
    async def delete_asset(asset_id: str):
        doc = await coll.find_one({"id": asset_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Asset not found")
        # Best-effort R2 delete first, then mongo row.
        await paf.delete_ref(doc["file_ref"])
        if doc.get("poster_ref"):
            await paf.delete_ref(doc["poster_ref"])
        await coll.delete_one({"id": asset_id})
        return {"ok": True, "deleted": asset_id}

    @router.get("/{asset_id}/download")
    async def download_redirect(asset_id: str):
        """302 → presigned URL. Browser handles the actual file download.
        Works for both video preview (just load the URL) and explicit
        download (Content-Disposition is on the R2 object's ACL)."""
        doc = await coll.find_one({"id": asset_id}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Asset not found")
        try:
            url = await paf.presigned_url(doc["file_ref"])
        except Exception as e:  # noqa: BLE001
            raise HTTPException(503, "Could not mint download URL") from e
        return RedirectResponse(url=url, status_code=302)

    return router
