"""
job_photos.py — Job Photos Library (Phase 1, read-only aggregator)
================================================================

Mirrors photos that crews already submit on **Daily Reports**, **Site
Inspections**, and **QA/QC inspections** into a flat per-photo index so the
Admin / PM portal can:

  • Browse photos grouped by Job → Week
  • Lightbox / zoom any photo
  • Multi-select + download a ZIP packet
  • Email a packet to a recipient

Photos are NOT removed from their source records — this is a denormalised
read view. The source record stays the system of record.

Why a separate collection (not a Mongo aggregation)?
----------------------------------------------------
Aggregating 100K daily-report photos every time the page loads would be
slow and would balloon the response payload. We pre-compute a tiny
metadata row per photo so the list query stays cheap. Thumbnails are
NOT stored in this collection — we point back at the original photo
on each render so we never duplicate the actual image bytes.

Indexer behaviour
-----------------
Runs in three modes:
  1. Inline on form submit (server.py calls ``index_record_photos``)
  2. Background catch-up loop every 30 minutes (boot-time + periodic)
  3. Manual rebuild via POST /api/admin/job-photos/reindex

Idempotent — running it twice never duplicates entries (PK = source_id +
photo_index).

PM scoping
----------
Every list / download / email endpoint passes through ``compute_pm_scope``
so a PM only sees photos from the jobs they're assigned to.
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import re
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pm_auth import compute_pm_scope

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/job-photos", tags=["job-photos"])

# Sources we mirror photos FROM. Pre-Op (`equipment_inspections`) is
# intentionally excluded for this Phase 1 per user direction — Pre-Op fail
# photos are diagnostic, not job-progress documentation.
SOURCE_COLLECTIONS = {
    "daily_report":  {
        "collection": "daily_reports",
        "date_field": "report_date",
        "submitter_field": "prepared_by",
    },
    "inspection": {
        "collection": "inspections",
        "date_field": "inspection_date",
        "submitter_field": "inspector_name",
    },
    "qaqc": {
        "collection": "qaqc_inspections",
        "date_field": "inspection_date",
        "submitter_field": "inspector_name",
    },
}

SOURCE_LABEL_EN = {
    "daily_report": "Daily Report",
    "inspection": "Site Inspection",
    "qaqc": "QA/QC",
}

# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────
def _week_of(date_str: str) -> str:
    """Return ISO 'YYYY-Www' week tag for a date string (YYYY-MM-DD)."""
    if not date_str:
        return "unknown-week"
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        iso_year, iso_week, _ = d.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    except Exception:
        return "unknown-week"


def _safe_filename(s: str, fallback: str = "photo") -> str:
    """Strip a string down to a filesystem-safe slug."""
    if not s:
        return fallback
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", s)[:60] or fallback


def _decode_data_url(data_url: str) -> Optional[tuple[bytes, str]]:
    """Return (raw_bytes, ext) from a `data:image/...;base64,...` URL."""
    if not isinstance(data_url, str) or not data_url.startswith("data:"):
        return None
    try:
        header, b64 = data_url.split(",", 1)
        mime = header.split(";")[0].split(":")[1]  # e.g. "image/jpeg"
        ext = mime.split("/")[-1].lower().replace("jpeg", "jpg")
        if ext not in ("jpg", "png", "webp", "gif", "heic", "heif"):
            ext = "jpg"
        return base64.b64decode(b64), ext
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────
# Indexer
# ─────────────────────────────────────────────────────────────────────────
async def index_record_photos(db, source: str, record: Dict[str, Any]) -> int:
    """Mirror a single source record's photos into the job_photos collection.

    Idempotent — uses (source, source_id, photo_index) as the natural key
    so re-indexing the same record overwrites rather than duplicating.

    Returns the number of photo rows upserted.
    """
    if source not in SOURCE_COLLECTIONS:
        return 0
    cfg = SOURCE_COLLECTIONS[source]
    src_id = record.get("id")
    if not src_id:
        return 0
    photos = record.get("photos") or []
    if not isinstance(photos, list):
        return 0

    project_number = (record.get("project_number") or "").strip()
    project_name = (record.get("project_name") or "").strip()
    submitter = (record.get(cfg["submitter_field"]) or "").strip()
    record_date = (record.get(cfg["date_field"]) or "")[:10]
    week = _week_of(record_date)

    # Wipe out any old rows for this record so removed photos don't linger.
    await db.job_photos.delete_many({"source": source, "source_id": src_id})

    rows = []
    for idx, p in enumerate(photos):
        if not isinstance(p, str) or not p.startswith("data:"):
            continue
        rows.append({
            "id": f"{source}:{src_id}:{idx}",
            "source": source,
            "source_id": src_id,
            "photo_index": idx,
            "project_number": project_number,
            "project_name": project_name,
            "submitter": submitter,
            "record_date": record_date,
            "week_of": week,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })
    if rows:
        await db.job_photos.insert_many(rows)
    return len(rows)


async def reindex_all(db) -> Dict[str, int]:
    """Wipe and rebuild the entire `job_photos` collection from source.

    Run on boot (lazy) or manually from /admin. Safe at any size — uses
    streaming cursors so even 50K records doesn't pin RAM."""
    await db.job_photos.delete_many({})
    counts: Dict[str, int] = {}
    for source, cfg in SOURCE_COLLECTIONS.items():
        n = 0
        async for rec in db[cfg["collection"]].find(
            {"photos.0": {"$exists": True}},
            # Pull only the fields we need — photos are big.
            {"_id": 0, "id": 1, "photos": 1, "project_number": 1,
             "project_name": 1, cfg["date_field"]: 1, cfg["submitter_field"]: 1},
        ):
            n += await index_record_photos(db, source, rec)
            await asyncio.sleep(0)  # yield so we don't block the loop
        counts[source] = n

    # Helpful indexes (idempotent)
    await db.job_photos.create_index("project_number")
    await db.job_photos.create_index([("project_number", 1), ("week_of", -1)])
    await db.job_photos.create_index([("source", 1), ("source_id", 1)])
    counts["total"] = sum(counts.values())
    logger.info(f"[job-photos] reindex complete: {counts}")
    return counts


async def background_indexer_loop(db) -> None:
    """Periodic catch-up. Runs every 30 minutes. On startup, only reindexes
    if the collection is empty — first deploy / fresh database scenario."""
    try:
        existing = await db.job_photos.count_documents({})
        if existing == 0:
            logger.info("[job-photos] empty collection — running first index pass")
            await reindex_all(db)
    except Exception as e:
        logger.exception(f"[job-photos] startup index failed: {e}")

    while True:
        try:
            await asyncio.sleep(1800)  # 30 minutes
            # Light catch-up: only re-index records modified in last 2h
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            for source, cfg in SOURCE_COLLECTIONS.items():
                async for rec in db[cfg["collection"]].find(
                    {"photos.0": {"$exists": True}, "updated_at": {"$gte": cutoff}},
                    {"_id": 0, "id": 1, "photos": 1, "project_number": 1,
                     "project_name": 1, cfg["date_field"]: 1, cfg["submitter_field"]: 1},
                ):
                    await index_record_photos(db, source, rec)
                    await asyncio.sleep(0)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"[job-photos] catch-up indexer error: {e}")


# ─────────────────────────────────────────────────────────────────────────
# Photo loader — lazy fetch the actual image bytes when needed
# ─────────────────────────────────────────────────────────────────────────
async def _load_photo(db, source: str, source_id: str, idx: int) -> Optional[str]:
    """Return the full data URL for a single photo by re-fetching the
    source record. We never duplicate photo bytes into job_photos."""
    cfg = SOURCE_COLLECTIONS.get(source)
    if not cfg:
        return None
    rec = await db[cfg["collection"]].find_one(
        {"id": source_id}, {"_id": 0, "photos": 1}
    )
    if not rec:
        return None
    photos = rec.get("photos") or []
    if 0 <= idx < len(photos) and isinstance(photos[idx], str):
        return photos[idx]
    return None


# ─────────────────────────────────────────────────────────────────────────
# Pydantic models for endpoints
# ─────────────────────────────────────────────────────────────────────────
class BulkSelection(BaseModel):
    photo_ids: List[str]


class BulkEmail(BaseModel):
    photo_ids: List[str]
    to: str
    subject: Optional[str] = None
    note: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────
# Endpoints — wired into server.py via include_router
# ─────────────────────────────────────────────────────────────────────────
def attach_routes(app, db, require_caller, send_email_fn) -> None:
    """Wire endpoints to a running FastAPI app.

    Args:
        app: the FastAPI instance to mount on
        db: the live Motor database handle (passed directly, not via Depends —
            matches the pattern used by other routers in this codebase)
        require_caller: existing FastAPI dependency that returns the current
            PM/admin actor (we re-use ``require_admin`` from server.py since
            that already accepts both admin tokens and per-PM tokens)
        send_email_fn: async callable ``(to, subject, text, attachments)``
            that wraps Resend — passed in so we share the same retry +
            logging behaviour as other system emails.
    """

    @router.get("")
    async def list_photos(
        actor=Depends(require_caller),
        source: Optional[str] = Query(None, description="Filter to one source"),
        project_number: Optional[str] = Query(None),
        week_of: Optional[str] = Query(None, description="ISO 'YYYY-Www'"),
        date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
        date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
        submitter: Optional[str] = Query(None),
    ):
        """Return the metadata index (no photo bytes). Frontend then asks
        for individual photo bytes only when rendering a thumbnail / zoom."""
        scope = await compute_pm_scope(db, actor)
        q: Dict[str, Any] = {}
        if source: q["source"] = source
        if project_number: q["project_number"] = project_number
        if week_of: q["week_of"] = week_of
        if submitter: q["submitter"] = submitter
        if date_from or date_to:
            rng: Dict[str, str] = {}
            if date_from: rng["$gte"] = date_from
            if date_to: rng["$lte"] = date_to
            q["record_date"] = rng
        q = scope.filter(q)
        cursor = db.job_photos.find(q, {"_id": 0}).sort("record_date", -1).limit(5000)
        items = await cursor.to_list(length=5000)
        return {"items": items, "count": len(items)}

    @router.get("/{photo_id}/raw")
    async def get_photo_raw(
        photo_id: str,
        actor=Depends(require_caller),
    ):
        """Return the actual data URL for a single photo (used for
        lightbox + thumbnail rendering). PM-scoped."""
        scope = await compute_pm_scope(db, actor)
        meta = await db.job_photos.find_one({"id": photo_id}, {"_id": 0})
        if not meta:
            raise HTTPException(404, "photo not found")
        if not scope.allows(meta.get("project_number")):
            raise HTTPException(403, "not in scope")
        url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
        if not url:
            raise HTTPException(404, "source photo missing")
        return {"data_url": url, "meta": meta}

    @router.get("/{photo_id}/thumb")
    async def get_photo_thumb(
        photo_id: str,
        actor=Depends(require_caller),
    ):
        """Return a small (≤ 360px on the long edge, JPEG q60) thumbnail
        of a photo. ~5–20 KB per response vs. 200 KB–2 MB for /raw — the
        difference is the difference between a snappy gallery and 'super
        slow'. Cached for 24h (immutable: photo_id never changes content)."""
        scope = await compute_pm_scope(db, actor)
        meta = await db.job_photos.find_one({"id": photo_id}, {"_id": 0})
        if not meta:
            raise HTTPException(404, "photo not found")
        if not scope.allows(meta.get("project_number")):
            raise HTTPException(403, "not in scope")
        url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
        decoded = _decode_data_url(url) if url else None
        if not decoded:
            raise HTTPException(404, "source photo missing")
        raw, _ext = decoded
        try:
            from PIL import Image as _PILImage  # type: ignore  # noqa: WPS433
            with _PILImage.open(io.BytesIO(raw)) as im:
                im.thumbnail((360, 360), _PILImage.LANCZOS)
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGB")
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=60, optimize=True)
                jpeg = buf.getvalue()
        except Exception:
            # If Pillow choked (heic/heif/corrupt), fall back to original
            jpeg = raw
        from fastapi.responses import Response  # local import to avoid clash
        return Response(
            content=jpeg,
            media_type="image/jpeg",
            headers={"Cache-Control": "private, max-age=86400, immutable"},
        )

    @router.post("/raw-batch")
    async def get_photo_raw_batch(
        body: BulkSelection,
        actor=Depends(require_caller),
    ):
        """Bulk fetch up to 50 full-resolution photos in a single round-trip.
        Used by the lightbox preloader and downstream tooling that needs
        original bytes (e.g. ZIP). For gallery thumbnails, use /thumb."""
        ids = (body.photo_ids or [])[:50]
        if not ids:
            return {"items": []}
        scope = await compute_pm_scope(db, actor)
        metas = await db.job_photos.find(
            {"id": {"$in": ids}}, {"_id": 0}
        ).to_list(length=len(ids))
        out: List[Dict[str, Any]] = []
        for meta in metas:
            if not scope.allows(meta.get("project_number")):
                continue
            url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
            if not url:
                continue
            out.append({"id": meta["id"], "data_url": url})
        return {"items": out}

    @router.post("/zip")
    async def download_zip(
        body: BulkSelection,
        actor=Depends(require_caller),
    ):
        """Stream a ZIP of selected photos. Files are organized by
        ``<job_number>__<job_name>/<week>/<source>__<date>__N.<ext>`` so
        the recipient can drop the zip into their file system and get a
        sane structure right away."""
        scope = await compute_pm_scope(db, actor)
        ids = body.photo_ids[:1000]  # safety: cap to 1000 per zip
        if not ids:
            raise HTTPException(400, "no photos selected")
        metas = await db.job_photos.find(
            {"id": {"$in": ids}}, {"_id": 0}
        ).to_list(length=len(ids))
        metas = [m for m in metas if scope.allows(m.get("project_number"))]
        if not metas:
            raise HTTPException(403, "no accessible photos in selection")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for m in metas:
                url = await _load_photo(db, m["source"], m["source_id"], m["photo_index"])
                if not url:
                    continue
                decoded = _decode_data_url(url)
                if not decoded:
                    continue
                raw, ext = decoded
                folder = (
                    f"{_safe_filename(m.get('project_number') or 'no-job')}__"
                    f"{_safe_filename(m.get('project_name') or 'unnamed')}/"
                    f"{m.get('week_of') or 'unknown-week'}"
                )
                fname = (
                    f"{m['source']}__"
                    f"{_safe_filename(m.get('record_date') or 'no-date')}__"
                    f"{m['photo_index']:03d}.{ext}"
                )
                zf.writestr(f"{folder}/{fname}", raw)
                await asyncio.sleep(0)
        buf.seek(0)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        zip_name = f"masci-photos-{ts}-{len(metas)}photos.zip"
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
        )

    @router.post("/email")
    async def email_zip(
        body: BulkEmail,
        actor=Depends(require_caller),
    ):
        """Email the selected photos as a single ZIP attachment (capped at
        ~25 MB — anything larger should be downloaded directly via /zip)."""
        scope = await compute_pm_scope(db, actor)
        if not body.to or "@" not in body.to:
            raise HTTPException(400, "invalid email")
        ids = body.photo_ids[:200]  # email cap
        if not ids:
            raise HTTPException(400, "no photos selected")
        metas = await db.job_photos.find({"id": {"$in": ids}}, {"_id": 0}).to_list(length=len(ids))
        metas = [m for m in metas if scope.allows(m.get("project_number"))]
        if not metas:
            raise HTTPException(403, "no accessible photos")

        buf = io.BytesIO()
        total_bytes = 0
        included = 0
        MAX_BYTES = 25 * 1024 * 1024
        skipped_for_size = 0
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for m in metas:
                url = await _load_photo(db, m["source"], m["source_id"], m["photo_index"])
                decoded = _decode_data_url(url) if url else None
                if not decoded:
                    continue
                raw, ext = decoded
                if total_bytes + len(raw) > MAX_BYTES:
                    skipped_for_size += 1
                    continue
                fname = (
                    f"{_safe_filename(m.get('project_number') or 'no-job')}/"
                    f"{m['source']}__{m.get('record_date','')}__"
                    f"{m['photo_index']:03d}.{ext}"
                )
                zf.writestr(fname, raw)
                total_bytes += len(raw)
                included += 1
                await asyncio.sleep(0)
        buf.seek(0)

        subject = body.subject or f"MASCI Photos — {included} photo(s)"
        body_text = (body.note or "") + (
            f"\n\n— {included} photos attached ({total_bytes/1024/1024:.1f} MB). "
            f"{skipped_for_size} skipped for size. Sent from MASCI HUB."
        )
        try:
            await send_email_fn(
                to=body.to,
                subject=subject,
                text=body_text,
                attachments=[{
                    "filename": "masci-photos.zip",
                    "content": buf.getvalue(),
                    "content_type": "application/zip",
                }],
            )
        except Exception as e:
            raise HTTPException(500, f"email send failed: {e}") from e
        return {"ok": True, "included": included, "skipped_for_size": skipped_for_size, "bytes": total_bytes}

    @router.post("/admin/reindex")
    async def admin_reindex(
        actor=Depends(require_caller),
    ):
        """Admin-only: wipe and rebuild the photo index from scratch."""
        scope = await compute_pm_scope(db, actor)
        if not scope.is_admin:
            raise HTTPException(403, "admin only")
        result = await reindex_all(db)
        return {"ok": True, **result}

    app.include_router(router)
