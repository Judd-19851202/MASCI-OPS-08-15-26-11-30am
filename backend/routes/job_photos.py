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
import hashlib
import hmac
import io
import logging
import os
import re
import time
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from lib.enterprise_governance import governance_project_scope_allows, governance_project_scope_filter

# Register HEIF/HEIC opener once at import. Without this, iPhone photos
# (default HEIC format) cannot be decoded by Pillow and end up rendered
# as broken thumbnails for every job-photo gallery view. pillow-heif is a
# hard dependency of this module — falling back silently would mask a
# very real and recurring user-facing bug.
try:
    from pillow_heif import register_heif_opener  # type: ignore
    register_heif_opener()
except Exception as _heif_err:  # noqa: BLE001
    logging.getLogger(__name__).warning(
        f"[job-photos] pillow-heif failed to register: {_heif_err}. "
        "iPhone HEIC thumbnails will fall back to broken-image placeholders."
    )

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/job-photos", tags=["job-photos"])

# ─────────────────────────────────────────────────────────────────────────
# Iter64 hotfix — Photo Bytes resolver (sibling router, no prefix collision)
# ─────────────────────────────────────────────────────────────────────────
# Direct img-src endpoint for ``photo://`` refs that ended up rendered in
# record-detail views (ViewDailyReport, ViewMeeting, ViewInspection,
# ViewIncident, ViewQaqcInspection, ViewEquipmentInspection,
# ViewSafetyForm, FieldLeadershipView, PhotoUpload preview). These pages
# render the raw `record.photos[i]` string straight into <img src=...>.
# Before iter64 phase 2 the string was a base64 data: URL that browsers
# could load natively. After migration the string became
# ``photo://masci-hub/...`` which browsers can't fetch → blank squares.
# This endpoint resolves the ref to actual image bytes on the server
# and returns them as a normal HTTP image response so browsers display
# them transparently.
#
# Auth: deliberately public. The threat model is identical to having
# the photos embedded as base64 inside the record JSON — if you can
# fetch the record, you can see the photos. Refs are unguessable
# (UUID-keyed paths) and we cache aggressively to keep this cheap.
photo_bytes_router = APIRouter(prefix="/api", tags=["photo-bytes"])


@photo_bytes_router.get("/photo-bytes")
async def photo_bytes_resolve(ref: str = Query(..., min_length=10, max_length=512)):
    """Return raw image bytes for any photo ref. Accepts both legacy
    base64 ``data:`` URLs (in which case we just unbox the base64) and
    ``photo://`` storage refs (in which case we fetch from R2). Sets
    aggressive cache headers — these URLs are content-addressable so
    a 1-year cache is correct.

    Frontend usage:
        <img src={`${API}/photo-bytes?ref=${encodeURIComponent(p)}`} />
    """
    from fastapi.responses import Response
    if not ref or not isinstance(ref, str):
        raise HTTPException(400, "ref required")
    # Reject obvious garbage early so we don't burn an R2 call.
    if not (ref.startswith("data:") or ref.startswith("photo://")):
        raise HTTPException(400, "unsupported photo ref scheme")

    result = await _load_photo_bytes(ref)
    if not result:
        raise HTTPException(404, "photo not available")
    raw, ext = result
    content_type = {
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "heic": "image/heic",
        "heif": "image/heif",
        "avif": "image/avif",
    }.get(ext, "image/jpeg")
    return Response(
        content=raw,
        media_type=content_type,
        headers={
            # Aggressive cache — refs are immutable so the bytes never change.
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        },
    )


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
    """Return (raw_bytes, ext) from a `data:image/...;base64,...` URL.

    Pre-iter64 only handled base64 data URLs. For S3-migrated photos,
    callers should use ``_load_photo_bytes`` which transparently handles
    both schemes. This sync helper is retained for legacy code paths
    that haven't been updated yet and for the unit tests."""
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


async def _load_photo_bytes(ref: Optional[str]) -> Optional[tuple[bytes, str]]:
    """Unified async reader: returns (raw_bytes, ext) for ANY photo ref —
    a base64 ``data:`` URL (legacy in-Mongo storage) OR a ``photo://``
    pointer (S3-migrated). Returns None on any failure so callers can
    serve a graceful 404 instead of crashing.

    This is the unifying read API every thumb/raw/preview/PDF path
    should call. Once iter64 migration completes, the base64 branch
    will only fire for records the migrator hasn't reached yet.
    """
    if not ref or not isinstance(ref, str):
        return None
    # Legacy base64 fast path — no async work needed.
    if ref.startswith("data:"):
        return _decode_data_url(ref)
    # S3-backed pointer
    try:
        from photo_storage import is_storage_ref, read_photo_bytes
    except Exception:
        return None
    if not is_storage_ref(ref):
        return None
    try:
        raw = await read_photo_bytes(ref)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[job-photos] S3 fetch failed for {ref[:60]}: {e}")
        return None
    # Pull extension out of the ref's URL key for the downstream PDF embed.
    ext = "jpg"
    try:
        ext = ref.rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "webp", "gif", "heic", "heif", "avif"):
            ext = "jpg"
        if ext == "jpeg":
            ext = "jpg"
    except Exception:
        pass
    return raw, ext


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
        # Accept BOTH legacy base64 (data:) AND migrated cloud refs (photo://).
        # Skipping photo:// refs here would un-index every photo after R2 migration.
        if not isinstance(p, str) or not (p.startswith("data:") or p.startswith("photo://")):
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


async def _warm_missing_thumbs(db, batch_limit: int = 200) -> Dict[str, int]:
    """Pre-render thumbs for any indexed photo that doesn't yet have a
    JPEG cache entry. Honors the same render concurrency cap as the
    on-demand path so we never blow up the worker. Cap batch size so a
    single tick never runs longer than the next tick interval.

    TRACK 26.07 refactor: previously loaded EVERY warm photo_id in the
    cache into a Python set per tick (O(N) memory + full-collection read
    of `job_photo_thumb_cache` filtering only by `fmt`). Now walks
    `job_photos` in a bounded batch and issues ONE `$in` lookup against
    the compound `{fmt: 1, photo_id: 1}` index to identify warm ones —
    bounded query, index-backed, zero unbounded scans.

    Returns ``{warmed, failed}`` for log surfacing.
    """
    warmed = 0
    failed = 0
    skipped_recent_failures = 0
    retry_after = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()

    # Walk the index in a bounded batch. Over-fetch a bit since most rows
    # will already be warm, but hard-cap so a single tick never scans the
    # full collection.
    candidates: List[Dict[str, Any]] = []
    scan_cap = max(batch_limit * 5, 100)
    async for meta in db.job_photos.find(
        {
            "$or": [
                {"thumb_warm_last_failed_at": {"$exists": False}},
                {"thumb_warm_last_failed_at": None},
                {"thumb_warm_last_failed_at": {"$lt": retry_after}},
            ]
        },
        {
            "_id": 0,
            "id": 1,
            "source": 1,
            "source_id": 1,
            "photo_index": 1,
            "thumb_warm_fail_count": 1,
            "thumb_warm_last_failed_at": 1,
        }
    ).limit(scan_cap):
        candidates.append(meta)

    if not candidates:
        return {"warmed": 0, "failed": 0}

    # Single index-backed lookup: which of this batch already have a JPEG
    # cache entry? Uses the compound `{fmt: 1, photo_id: 1}` index added
    # in `_ensure_thumb_cache_indexes` (TRACK 26.07). The `$in` size is
    # bounded to `scan_cap`, so the query planner can serve this entirely
    # from the index without touching document payloads.
    batch_ids = [c["id"] for c in candidates if c.get("id")]
    warm_ids: set[str] = set()
    if batch_ids:
        async for d in db.job_photo_thumb_cache.find(
            {"fmt": "jpeg", "photo_id": {"$in": batch_ids}},
            {"_id": 0, "photo_id": 1},
        ):
            pid = d.get("photo_id")
            if pid:
                warm_ids.add(pid)

    for meta in candidates:
        if meta["id"] in warm_ids:
            continue
        if warmed + failed >= batch_limit:
            break
        last_failed_at = str(meta.get("thumb_warm_last_failed_at") or "").strip()
        if last_failed_at and last_failed_at >= retry_after:
            skipped_recent_failures += 1
            continue
        try:
            url = await _load_photo(
                db, meta["source"], meta["source_id"], meta["photo_index"]
            )
            decoded = await _load_photo_bytes(url) if url else None
            if not decoded:
                await db.job_photos.update_one(
                    {"id": meta["id"]},
                    {"$set": {"thumb_warm_last_failed_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"thumb_warm_fail_count": 1}},
                )
                failed += 1
                continue
            raw, _ext = decoded
            async with _render_sema():
                rendered = await asyncio.to_thread(_render_all_formats, raw)
            for fmt_key, payload_bytes in rendered.items():
                await _write_thumb_cache(db, meta["id"], fmt_key, payload_bytes)
            if rendered:
                await db.job_photos.update_one(
                    {"id": meta["id"]},
                    {"$unset": {"thumb_warm_last_failed_at": ""}, "$set": {"thumb_warm_fail_count": 0}},
                )
                warmed += 1
            else:
                await db.job_photos.update_one(
                    {"id": meta["id"]},
                    {"$set": {"thumb_warm_last_failed_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"thumb_warm_fail_count": 1}},
                )
                failed += 1
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[job-photos] auto-warm failed for {meta['id']}: {e}")
            await db.job_photos.update_one(
                {"id": meta["id"]},
                {"$set": {"thumb_warm_last_failed_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"thumb_warm_fail_count": 1}},
            )
            failed += 1
    return {"warmed": warmed, "failed": failed, "skipped_recent_failures": skipped_recent_failures}


async def background_indexer_loop(db) -> None:
    """Periodic catch-up. Runs every 10 minutes. On startup, only reindexes
    if the collection is empty — first deploy / fresh database scenario.

    Each tick also auto-warms up to 200 thumbs that haven't been rendered
    yet, so the first viewer of any newly-submitted daily report's
    photos gets instant load instead of paying the Pillow decode cost.
    """
    try:
        existing = await db.job_photos.count_documents({})
        if existing == 0:
            logger.info("[job-photos] empty collection — running first index pass")
            await reindex_all(db)
    except Exception as e:
        logger.exception(f"[job-photos] startup index failed: {e}")

    while True:
        try:
            await asyncio.sleep(600)  # 10 minutes
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
            # Auto-warm any thumbs that haven't been rendered yet.
            warm_result = await _warm_missing_thumbs(db, batch_limit=200)
            if warm_result["warmed"] or warm_result["failed"] or warm_result.get("skipped_recent_failures"):
                logger.info(
                    f"[job-photos] auto-warm tick: {warm_result['warmed']} warmed, "
                    f"{warm_result['failed']} failed, "
                    f"{warm_result.get('skipped_recent_failures', 0)} skipped-recent-failures"
                )
            # Auto-vacuum: when R2 storage is configured, sweep any
            # base64 photos still in MongoDB out to R2 in small batches.
            # This is the steady-state companion to the one-shot
            # admin migration endpoint — keeps DB size flat as new
            # uploads come in. Bounded to 25 docs/collection/tick so we
            # never hammer R2 or block the loop. Idempotent — already
            # migrated photo:// refs are skipped.
            try:
                from photo_storage import is_configured as _ps_configured
                if _ps_configured():
                    from photo_migration import migrate_all
                    vacuum = await migrate_all(
                        db, dry_run=False,
                        limit_per_collection=25, resume=True,
                    )
                    v = vacuum.get("totals") or {}
                    if v.get("photos_migrated") or v.get("photos_failed"):
                        logger.info(
                            f"[job-photos] R2 vacuum tick: "
                            f"{v.get('photos_migrated', 0)} migrated, "
                            f"{v.get('photos_failed', 0)} failed, "
                            f"{v.get('bytes_migrated', 0)} bytes"
                        )
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[job-photos] R2 vacuum failed: {e}")
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
# Server-side thumbnail cache (Mongo) + signed-URL helpers
# ─────────────────────────────────────────────────────────────────────────
# Why a Mongo cache instead of disk?
# 1. Disk on the Emergent container is ephemeral — survives a single boot
#    but vanishes on every redeploy. A 156-photo gallery would re-render
#    every photo through Pillow on every deploy → user sees the slow load
#    again every time.
# 2. Multi-worker uvicorn would need a shared volume to share the disk
#    cache anyway — Mongo is already there and shared.
# 3. Each AVIF thumb is ~5-15 KB so even 50K photos × 3 formats = ~3 GB
#    which is well within the Atlas plan we're on. We bound it with a
#    7-day TTL so cold photos drop out automatically.
#
# Schema (db.job_photo_thumb_cache):
#   _id               composite "<photo_id>:<fmt>" — e.g. "daily:abc123:0:avif"
#   photo_id          str — the job_photos id
#   fmt               "avif" | "webp" | "jpeg"
#   bytes             binary blob
#   created_at        datetime UTC (TTL index)
_THUMB_TTL_DAYS = 7


def _thumb_cache_key(photo_id: str, fmt: str) -> str:
    return f"{photo_id}:{fmt.lower()}"


async def _ensure_thumb_cache_indexes(db) -> None:
    try:
        await db.job_photo_thumb_cache.create_index(
            "created_at", expireAfterSeconds=_THUMB_TTL_DAYS * 86400
        )
        await db.job_photo_thumb_cache.create_index("photo_id")
        # TRACK 26.07: compound index covering the per-tick warm lookup
        # (`{fmt: "jpeg", photo_id: {$in: [...]}}`) used by
        # `_warm_missing_thumbs`. Prior to this index, that filter fell back
        # to the `photo_id_1` index and re-scanned every candidate to filter
        # by fmt, triggering Atlas query targeting when the cache grew.
        await db.job_photo_thumb_cache.create_index(
            [("fmt", 1), ("photo_id", 1)],
            name="fmt_1_photo_id_1",
        )
        await db.job_photos.create_index(
            [("thumb_warm_last_failed_at", 1)],
            name="ix_job_photos_thumb_warm_last_failed_at",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[job-photos] thumb cache index create failed: {e}")


async def _read_thumb_cache(db, photo_id: str, fmt: str) -> Optional[bytes]:
    doc = await db.job_photo_thumb_cache.find_one(
        {"_id": _thumb_cache_key(photo_id, fmt)}, {"bytes": 1}
    )
    if not doc:
        return None
    payload = doc.get("bytes")
    # PyMongo returns binary as `bytes` directly. Defensive against
    # legacy {"$binary": ...} payloads.
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    return None


async def _write_thumb_cache(db, photo_id: str, fmt: str, payload: bytes) -> None:
    try:
        await db.job_photo_thumb_cache.update_one(
            {"_id": _thumb_cache_key(photo_id, fmt)},
            {"$set": {
                "_id": _thumb_cache_key(photo_id, fmt),
                "photo_id": photo_id,
                "fmt": fmt,
                "bytes": payload,
                "created_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[job-photos] thumb cache write failed: {e}")


def _thumb_secret() -> bytes:
    """HMAC secret for signed thumbnail URLs. Re-uses the same admin
    HMAC secret as the rest of the auth system so rotation invalidates
    every signed URL too."""
    s = (os.environ.get("ADMIN_HMAC_SECRET") or "").strip()
    if not s:
        # Fall back to a per-process random — survives the worker
        # lifetime, which is fine for cached <img src> tokens.
        s = hashlib.sha256(os.urandom(32)).hexdigest()
    return s.encode()


def make_thumb_token(photo_id: str, ttl_seconds: int = 3600) -> str:
    """`<exp_unix>.<hmac>` — signed-URL token for <img src>.

    The token grants thumbnail access for a single photo for the next
    ``ttl_seconds`` (default 1h). It does NOT grant access to /raw or
    any other endpoint. Browser-cacheable, SW-cacheable, no axios round-
    trip needed. Renew by re-listing /job-photos which mints fresh ones.
    """
    exp = int(time.time()) + max(60, ttl_seconds)
    msg = f"thumb|exp={exp}|photo:{photo_id}".encode()
    sig = hmac.new(_thumb_secret(), msg, hashlib.sha256).hexdigest()[:32]
    return f"{exp}.{sig}"


def verify_thumb_token(photo_id: str, token: str) -> bool:
    if not token or "." not in token:
        return False
    exp_str, sig = token.split(".", 1)
    try:
        exp = int(exp_str)
    except ValueError:
        return False
    if exp < int(time.time()):
        return False
    msg = f"thumb|exp={exp}|photo:{photo_id}".encode()
    expected = hmac.new(_thumb_secret(), msg, hashlib.sha256).hexdigest()[:32]
    return hmac.compare_digest(sig, expected)


def _render_all_formats(raw: bytes) -> Dict[str, bytes]:
    """Pillow-render a thumbnail in EVERY format we serve, in a single
    decode pass. Returns a dict keyed by ``"avif"`` / ``"webp"`` / ``"jpeg"``
    with the encoded bytes, omitting any format Pillow refuses to encode.

    Why render all three at once? On the first miss we always pay the
    full HEIC/JPEG decode cost (the expensive part). Encoding three
    output formats from the already-loaded Image is nearly free
    compared to the decode. Caching all three at once means a Chrome
    request and a Safari request for the same photo never both trigger
    a re-decode of the source — second visitor wins by hitting the
    Mongo cache regardless of which Accept header they carry.

    JPEG is always present — it's the universal fallback if AVIF/WebP
    encoding fails on this Pillow build.
    """
    out: Dict[str, bytes] = {}
    try:
        from PIL import Image as _PILImage  # type: ignore  # noqa: WPS433
        with _PILImage.open(io.BytesIO(raw)) as im:
            im.thumbnail((360, 360), _PILImage.LANCZOS)
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            # JPEG (always — universal fallback)
            try:
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=60, optimize=True)
                out["jpeg"] = buf.getvalue()
            except Exception as e:
                logger.warning(f"[job-photos] JPEG encode failed: {e}")
            # WebP (Chrome/Edge/Firefox/Safari14+)
            try:
                buf = io.BytesIO()
                im.save(buf, format="WebP", quality=60, method=4)
                out["webp"] = buf.getvalue()
            except Exception as e:
                logger.debug(f"[job-photos] WebP encode skipped: {e}")
            # AVIF (Chrome/Edge — best compression). pillow-avif-plugin
            # may not be present; fall through silently.
            try:
                buf = io.BytesIO()
                im.save(buf, format="AVIF", quality=45)
                out["avif"] = buf.getvalue()
            except Exception as e:
                logger.debug(f"[job-photos] AVIF encode skipped: {e}")
    except Exception as e:
        logger.debug(f"[job-photos] Pillow decode failed, using raw bytes as JPEG: {e}")
        out["jpeg"] = raw
    return out


# Concurrency cap on Pillow rendering. Without this, 30+ simultaneous
# /thumb-signed requests (gallery first-load on a busy job) all hit
# asyncio.to_thread at once, the default ThreadPoolExecutor explodes
# to 32 workers, each holding a decompressed image in RAM, and the
# FastAPI worker gets OOM-killed by Cloudflare → HTTP 520 storm to
# the user. Serializing render+encode to ~2 in-flight CPU jobs keeps
# memory bounded; cache hits skip the lock entirely so the second
# visit to a job is instant.
_RENDER_SEMA: Optional[asyncio.Semaphore] = None
_RENDER_CONCURRENCY = max(
    1, int(os.environ.get("JOB_PHOTO_RENDER_CONCURRENCY", "2"))
)


def _render_sema() -> asyncio.Semaphore:
    """Lazy semaphore so we attach to the running event loop, not the
    import-time loop (FastAPI's startup event loop is created after
    module import)."""
    global _RENDER_SEMA
    if _RENDER_SEMA is None:
        _RENDER_SEMA = asyncio.Semaphore(_RENDER_CONCURRENCY)
    return _RENDER_SEMA


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
async def _serve_thumb(db, photo_id: str, meta: dict, accept: str) -> Response:
    """Shared cache-or-render path for both /thumb and /thumb-signed.

    Resolves the requested format from the Accept header, hits the
    Mongo cache, and renders through Pillow only on miss. All paths
    return a Response with appropriate Cache-Control + Vary headers
    so the browser, the service worker, and any intermediate proxy
    cache the bytes correctly across visits.
    """
    accept_l = (accept or "").lower()
    if "image/avif" in accept_l:
        fmt_pref = "avif"
    elif "image/webp" in accept_l:
        fmt_pref = "webp"
    else:
        fmt_pref = "jpeg"

    cached = await _read_thumb_cache(db, photo_id, fmt_pref)
    if cached:
        return Response(
            content=cached,
            media_type=f"image/{fmt_pref if fmt_pref != 'jpeg' else 'jpeg'}",
            headers={
                # End-user (browser) directive — note that the Emergent /
                # Cloudflare ingress can rewrite this to no-store on the
                # preview environment, so we ALSO send CDN-Cache-Control
                # and Surrogate-Control which Cloudflare honors separately.
                # Net effect: even when the browser cache is defeated by
                # the ingress, the CDN edge keeps a copy and the on-device
                # service worker (sw-thumbs.js) does the rest.
                "Cache-Control": "public, max-age=604800, immutable",
                "CDN-Cache-Control": "public, max-age=604800, immutable",
                "Surrogate-Control": "max-age=604800",
                "Vary": "Accept",
                "X-Thumb-Cache": "hit",
            },
        )

    url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
    decoded = await _load_photo_bytes(url) if url else None
    if not decoded:
        raise HTTPException(404, "source photo missing")
    raw, _ext = decoded

    # Serialize Pillow render to bound CPU + memory. Without this cap,
    # 30+ concurrent gallery requests would each spawn a thread holding
    # a decompressed iPhone HEIC in RAM (~30-60 MB resident each), the
    # worker would OOM, and Cloudflare would paint HTTP 520 across the
    # gallery — exactly the bug reported on 2026-05-08.
    async with _render_sema():
        # Re-check cache after acquiring the lock — another concurrent
        # request for the same photo may have just rendered it while
        # we were waiting in line.
        cached_again = await _read_thumb_cache(db, photo_id, fmt_pref)
        if cached_again:
            return Response(
                content=cached_again,
                media_type=f"image/{fmt_pref}",
                headers={
                    "Cache-Control": "public, max-age=604800, immutable",
                    "CDN-Cache-Control": "public, max-age=604800, immutable",
                    "Surrogate-Control": "max-age=604800",
                    "Vary": "Accept",
                    "X-Thumb-Cache": "hit-after-wait",
                },
            )

        # Render every format we can in a single decode pass, then
        # cache them all. Means a Chrome visit and a Safari visit for
        # the same photo never re-decode the source.
        rendered = await asyncio.to_thread(_render_all_formats, raw)

    # Persist all formats (best-effort) outside the render lock so the
    # next request through doesn't have to wait on Mongo writes.
    for fmt_key, payload_bytes in rendered.items():
        await _write_thumb_cache(db, photo_id, fmt_key, payload_bytes)

    payload = rendered.get(fmt_pref) or rendered.get("jpeg") or raw
    mime = f"image/{fmt_pref}" if fmt_pref in rendered else "image/jpeg"

    return Response(
        content=payload,
        media_type=mime,
        headers={
            "Cache-Control": "public, max-age=604800, immutable",
            "CDN-Cache-Control": "public, max-age=604800, immutable",
            "Surrogate-Control": "max-age=604800",
            "Vary": "Accept",
            "X-Thumb-Cache": "miss",
        },
    )


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
        for individual photo bytes only when rendering a thumbnail / zoom.

        Each item also carries a ``thumb_token`` — a 1h HMAC-signed URL
        token the frontend uses as ``<img src=".../thumb-signed?t=...">``.
        That lets the browser cache + service worker cache do their job
        WITHOUT a per-thumb axios round-trip, and is the single biggest
        wire-time speedup vs. iter44's blob-via-axios approach.
        """
        q: Dict[str, Any] = {}
        if source:
            q["source"] = source
        if project_number:
            q["project_number"] = project_number
        if week_of:
            q["week_of"] = week_of
        if submitter:
            q["submitter"] = submitter
        if date_from or date_to:
            rng: Dict[str, str] = {}
            if date_from:
                rng["$gte"] = date_from
            if date_to:
                rng["$lte"] = date_to
            q["record_date"] = rng
        scope_query = await governance_project_scope_filter(db, actor, base_filter=q)
        if scope_query is None:
            return {"items": [], "count": 0}
        cursor = db.job_photos.find(scope_query, {"_id": 0}).sort("record_date", -1).limit(5000)
        items = await cursor.to_list(length=5000)
        # Mint a 1h thumb token per item so the gallery can render via
        # plain <img src> with no axios overhead.
        for it in items:
            it["thumb_token"] = make_thumb_token(it["id"], ttl_seconds=3600)
        return {"items": items, "count": len(items),
                "total": await db.job_photos.count_documents(scope_query)}

    @router.get("/{photo_id}/raw")
    async def get_photo_raw(
        photo_id: str,
        response: Response,
        actor=Depends(require_caller),
    ):
        """Return the actual data URL for a single photo (used for
        lightbox + thumbnail rendering). PM-scoped.

        iter437 P0-incident fix · 2026-02:
          Response carries inline base64 image data. It is auth-scoped
          and user-specific. It MUST NOT be cached by browsers/edges
          (during the 2026-02 production outage, Cloudflare's 520 HTML
          error page was cached by iOS Safari against this URL with
          `immutable` for 7 days, persistently poisoning the mobile
          photo viewer even after origin recovered). Forcing
          `no-store` here prevents any future poisoning regardless of
          intermediate proxy behaviour.
        """
        meta = await db.job_photos.find_one({"id": photo_id}, {"_id": 0})
        if not meta:
            raise HTTPException(404, "photo not found")
        if not await governance_project_scope_allows(db, actor, meta.get("project_number")):
            raise HTTPException(403, "not in scope")
        url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
        if not url:
            raise HTTPException(404, "source photo missing")
        # iter445 · 2026-02 — When the source record stores an
        # R2-backed pointer (``photo://bucket/key``) instead of a
        # legacy inline base64 data URL, mint a short-lived presigned
        # HTTPS URL so the browser can fetch the bytes directly from
        # R2. The frontend lightbox's renderable check accepts strings
        # starting with ``data:image/``, ``blob:``, or ``http``; the
        # raw ``photo://`` scheme was rejected as "Photo data
        # unavailable or corrupt" even though the photo was perfectly
        # intact in storage. Legacy base64 records (pre-iter64
        # migration) continue to pass through unchanged.
        if isinstance(url, str) and url.startswith("photo://"):
            try:
                from photo_storage import presigned_get_url
                url = await presigned_get_url(url, ttl_seconds=900)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[job-photos] presign failed for {meta.get('id')}: {e}")
                raise HTTPException(500, "photo presign failed")
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        return {"data_url": url, "meta": meta}

    @router.get("/{photo_id}/thumb")
    async def get_photo_thumb(
        photo_id: str,
        request: Request,
        actor=Depends(require_caller),
    ):
        """Auth-header thumbnail endpoint. Kept for backward compat with
        existing clients (lightbox preview, mobile native shells). New
        gallery uses the signed-URL ``/thumb-signed`` path instead so
        the browser cache + service worker can do their job without an
        axios interceptor in the way.

        Hits the Mongo cache first; only renders through Pillow on miss.
        """
        meta = await db.job_photos.find_one({"id": photo_id}, {"_id": 0})
        if not meta:
            raise HTTPException(404, "photo not found")
        if not await governance_project_scope_allows(db, actor, meta.get("project_number")):
            raise HTTPException(403, "not in scope")
        return await _serve_thumb(db, photo_id, meta, request.headers.get("accept", ""))

    @router.get("/{photo_id}/thumb-signed")
    async def get_photo_thumb_signed(
        photo_id: str,
        request: Request,
        t: str = Query(..., description="HMAC signed token from /api/job-photos"),
    ):
        """Browser-friendly signed-URL thumbnail. No auth header required —
        the ``t`` query parameter carries a 1h HMAC token minted in the
        list endpoint and bound to this single ``photo_id``. Does NOT
        grant access to /raw or any other endpoint.

        Why this exists: <img src=...> can't carry custom headers, so
        the original /thumb endpoint forced us to fetch via axios → blob
        → object URL, which kills both the browser cache AND the service
        worker cache. With a signed query param, the browser caches by
        URL, the SW caches by URL, and the second visit to a job is
        effectively instant.
        """
        if not verify_thumb_token(photo_id, t):
            raise HTTPException(403, "thumb token invalid or expired")
        meta = await db.job_photos.find_one({"id": photo_id}, {"_id": 0})
        if not meta:
            raise HTTPException(404, "photo not found")
        # Note: PM scope was already enforced at list-time when the token
        # was minted. The token+expiry binding makes lateral leakage to
        # other photos impossible (signature is photo_id-specific).
        return await _serve_thumb(db, photo_id, meta, request.headers.get("accept", ""))

    @router.post("/raw-batch")
    async def get_photo_raw_batch(
        body: BulkSelection,
        response: Response,
        actor=Depends(require_caller),
    ):
        """Bulk fetch up to 50 full-resolution photos in a single round-trip.
        Used by the lightbox preloader and downstream tooling that needs
        original bytes (e.g. ZIP). For gallery thumbnails, use /thumb.

        iter437 P0 · same `no-store` doctrine as /raw above — see note there.
        """
        ids = (body.photo_ids or [])[:50]
        if not ids:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            return {"items": []}
        metas = await db.job_photos.find(
            {"id": {"$in": ids}}, {"_id": 0}
        ).to_list(length=len(ids))
        out: List[Dict[str, Any]] = []
        # iter445 · same R2-pointer presign fix as /raw above. Loop
        # body intentionally swallows per-photo presign failures so a
        # single bad ref doesn't fail the whole batch fetch — the
        # lightbox preloader can still render the others.
        try:
            from photo_storage import presigned_get_url
        except Exception:
            presigned_get_url = None  # type: ignore[assignment]
        for meta in metas:
            if not await governance_project_scope_allows(db, actor, meta.get("project_number")):
                continue
            url = await _load_photo(db, meta["source"], meta["source_id"], meta["photo_index"])
            if not url:
                continue
            if isinstance(url, str) and url.startswith("photo://"):
                if presigned_get_url is None:
                    continue
                try:
                    url = await presigned_get_url(url, ttl_seconds=900)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"[job-photos] batch presign failed for {meta.get('id')}: {e}")
                    continue
            out.append({"id": meta["id"], "data_url": url})
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
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
        ids = body.photo_ids[:1000]  # safety: cap to 1000 per zip
        if not ids:
            raise HTTPException(400, "no photos selected")
        metas = await db.job_photos.find(
            {"id": {"$in": ids}}, {"_id": 0}
        ).to_list(length=len(ids))
        metas = [m for m in metas if await governance_project_scope_allows(db, actor, m.get("project_number"))]
        if not metas:
            raise HTTPException(403, "no accessible photos in selection")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for m in metas:
                url = await _load_photo(db, m["source"], m["source_id"], m["photo_index"])
                if not url:
                    continue
                decoded = await _load_photo_bytes(url)
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
        if not body.to or "@" not in body.to:
            raise HTTPException(400, "invalid email")
        ids = body.photo_ids[:200]  # email cap
        if not ids:
            raise HTTPException(400, "no photos selected")
        metas = await db.job_photos.find({"id": {"$in": ids}}, {"_id": 0}).to_list(length=len(ids))
        metas = [m for m in metas if await governance_project_scope_allows(db, actor, m.get("project_number"))]
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
                decoded = await _load_photo_bytes(url) if url else None
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
            f"{skipped_for_size} skipped for size. Sent from MASCI Operations Platform."
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
        """Admin-only: wipe and rebuild the photo index from scratch.

        Also wipes the thumbnail cache so the next gallery load picks
        up any photos that were previously failing (e.g. iPhone HEIC
        before pillow-heif was installed).
        """
        if await governance_project_scope_filter(db, actor, base_filter={}) != {}:
            raise HTTPException(403, "admin only")
        try:
            await db.job_photo_thumb_cache.delete_many({})
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[job-photos] thumb cache wipe failed: {e}")
        result = await reindex_all(db)
        return {"ok": True, **result}

    @router.post("/admin/warm-cache")
    async def admin_warm_cache(
        actor=Depends(require_caller),
        project_number: Optional[str] = Query(None),
        limit: int = Query(2000, ge=1, le=20000),
    ):
        """Admin-only: pre-render every thumbnail in the index into the
        Mongo cache so the first viewer of a job page gets instant
        photos instead of paying the Pillow decode cost on every tile.

        Honors the same render concurrency cap as the on-demand path,
        so we never blow up the worker even when warming 1000+ photos.
        Skips photos that already have a cached JPEG (we treat JPEG as
        the "warmed" sentinel since it always renders if any format
        does).

        Returns ``{warmed, skipped, failed, elapsed_seconds}``.
        """
        if await governance_project_scope_filter(db, actor, base_filter={}) != {}:
            raise HTTPException(403, "admin only")

        q: Dict[str, Any] = {}
        if project_number:
            q["project_number"] = project_number

        t0 = time.time()
        warmed = 0
        skipped = 0
        failed = 0

        async def _warm_one(meta: Dict[str, Any]) -> None:
            nonlocal warmed, skipped, failed
            pid = meta["id"]
            # Skip if already cached as JPEG (universal format).
            existing = await db.job_photo_thumb_cache.find_one(
                {"_id": _thumb_cache_key(pid, "jpeg")}, {"_id": 1}
            )
            if existing:
                skipped += 1
                return
            try:
                url = await _load_photo(
                    db, meta["source"], meta["source_id"], meta["photo_index"]
                )
                decoded = await _load_photo_bytes(url) if url else None
                if not decoded:
                    failed += 1
                    return
                raw, _ext = decoded
                async with _render_sema():
                    rendered = await asyncio.to_thread(_render_all_formats, raw)
                for fmt_key, payload_bytes in rendered.items():
                    await _write_thumb_cache(db, pid, fmt_key, payload_bytes)
                if rendered:
                    warmed += 1
                else:
                    failed += 1
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[job-photos] warm-cache failed for {pid}: {e}")
                failed += 1

        # Stream the index — never load 20K rows into RAM at once.
        cursor = db.job_photos.find(q, {"_id": 0}).limit(limit)
        async for meta in cursor:
            await _warm_one(meta)

        return {
            "ok": True,
            "warmed": warmed,
            "skipped": skipped,
            "failed": failed,
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    # Track 22.1K · Orphan-task audit F2 · Was previously:
    #   asyncio.get_event_loop().create_task(_ensure_thumb_cache_indexes(db))
    # That fire-and-forget scheduled during module import produced
    # `Task was destroyed but it is pending` warnings under pytest because
    # the coroutine was created BEFORE the event loop was running.
    # Fix: register a proper LIFECYCLE_STEP so index creation is awaited
    # inside the startup lifespan phase-1 (still idempotent, still safe).
    try:
        from lib.lifespan_bootstrap import LIFECYCLE_STEPS, LifecycleStep  # noqa: PLC0415

        async def _job_photos_ensure_thumb_cache_indexes():
            try:
                await _ensure_thumb_cache_indexes(db)
            except Exception:  # noqa: BLE001
                pass  # best-effort, matches pre-migration silent semantics
        LIFECYCLE_STEPS.append(LifecycleStep(
            group="misc-bootstrap",
            name="_job_photos_ensure_thumb_cache_indexes",
            fn=_job_photos_ensure_thumb_cache_indexes,
            source_module=__name__,
        ))
    except Exception:
        pass

    app.include_router(router)
