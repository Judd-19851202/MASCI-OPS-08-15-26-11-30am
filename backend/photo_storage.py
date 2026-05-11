"""
photo_storage.py — S3-compatible photo storage abstraction
==========================================================

Why this module exists
----------------------
Until iter64, every photo submitted to MASCI Hub was base64-encoded and
embedded straight into the source record's ``photos`` array in MongoDB.
That choice was simple and worked great at low volume, but at ~600 MB
of photos in the database it had crossed three thresholds:

  1. Backup ZIPs ballooned to 887 MB → OOM-killing the worker (iter62/63
     installed a watermark + watchdog as defense-in-depth, but the only
     real cure is to get the bytes out of Mongo)
  2. Full-record fetches were carrying megabytes of base64 the caller
     usually didn't need (slow API responses)
  3. Restore-from-backup operations had to deserialize huge JSON
     documents, occasionally tripping Mongo's 16MB document size limit
     on the verge of submitting

This module provides a provider-agnostic storage layer that uploads
photo bytes to any S3-compatible bucket (Cloudflare R2 recommended,
also tested with AWS S3, Backblaze B2, DigitalOcean Spaces) and stores
only a lightweight ``photo://`` URL pointer back into the document.

Config (all from env vars, all required to enable cloud storage)
----------------------------------------------------------------
    S3_ENDPOINT_URL    The full HTTPS endpoint. For R2 it looks like
                       https://<account-id>.r2.cloudflarestorage.com
    S3_BUCKET          Bucket name (e.g. "masci-hub")
    S3_ACCESS_KEY      Access key ID
    S3_SECRET_KEY      Secret access key
    S3_REGION          AWS-style region (R2 uses "auto", AWS uses
                       us-east-1, B2 uses your region, DO uses your region)

If any of these are missing, ``is_configured()`` returns False and the
rest of the platform falls back to base64-in-Mongo storage with no
behavior change — letting us roll out the migration safely.

Public surface
--------------
    is_configured() -> bool
    upload_photo_bytes(data, ext, source_id) -> str   (returns photo:// URL)
    read_photo_bytes(ref) -> bytes                    (handles BOTH photo:// + base64)
    delete_photo(ref) -> bool
    is_storage_ref(ref) -> bool                       (True if ref starts with photo://)
    presigned_get_url(ref, ttl_seconds=900) -> str   (for direct browser delivery)
    health_check() -> dict                            (admin sanity)

URL format
----------
``photo://<bucket>/<key>`` where key looks like
``photos/2026/05/<source_id>/<uuid>.<ext>``. The double-slash distinguishes
our pointer scheme from a plain S3 URL (which would be exposing credentials
or bucket policy if leaked); we mint a fresh presigned GET URL whenever
the photo needs to be served to a browser.
"""
from __future__ import annotations

import base64
import datetime as _dt
import io
import logging
import os
import re
import uuid
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ── Config & lazy client ──────────────────────────────────────────────
_CLIENT = None
_CLIENT_FAILED = False  # cache failed init so we don't retry per-request


def _env(key: str) -> str:
    return (os.environ.get(key) or "").strip()


def is_configured() -> bool:
    """Return True only when every env var needed for S3 access is set.
    Used as a feature flag — read paths fall back to base64 storage when
    this returns False, so deploys without R2 credentials behave exactly
    like the pre-iter64 platform."""
    return all(
        _env(k)
        for k in (
            "S3_ENDPOINT_URL",
            "S3_BUCKET",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
        )
    )


def _bucket() -> str:
    return _env("S3_BUCKET")


def _client():
    """Lazy-init the boto3 S3 client. Cached at module scope after first
    success. R2's region is ``"auto"`` per Cloudflare docs; we default
    to that and let users override via S3_REGION for AWS/B2/DO."""
    global _CLIENT, _CLIENT_FAILED
    if _CLIENT is not None:
        return _CLIENT
    if _CLIENT_FAILED:
        return None
    if not is_configured():
        return None
    try:
        import boto3
        from botocore.config import Config as _BotoConfig
        # R2 requires path-style addressing and SigV4. AWS S3 supports both
        # but virtual-host-style is the default; setting "path" here is
        # safe for both — slightly slower DNS resolution on AWS, but no
        # functional difference.
        _CLIENT = boto3.client(
            "s3",
            endpoint_url=_env("S3_ENDPOINT_URL"),
            aws_access_key_id=_env("S3_ACCESS_KEY"),
            aws_secret_access_key=_env("S3_SECRET_KEY"),
            region_name=_env("S3_REGION") or "auto",
            config=_BotoConfig(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
                connect_timeout=10,
                read_timeout=30,
            ),
        )
        logger.info(
            f"[photo-storage] boto3 client initialized · "
            f"endpoint={_env('S3_ENDPOINT_URL')[:60]}… bucket={_bucket()}"
        )
        return _CLIENT
    except Exception as e:  # noqa: BLE001
        logger.exception(f"[photo-storage] client init failed: {e}")
        _CLIENT_FAILED = True
        return None


# ── Reference scheme: photo://<bucket>/<key> ──────────────────────────
_PHOTO_REF_RE = re.compile(r"^photo://([^/]+)/(.+)$")


def is_storage_ref(ref: Optional[str]) -> bool:
    """True if ``ref`` is one of our ``photo://`` pointers (i.e. lives in
    cloud storage). False for plain base64 ``data:`` URLs or empty/None.

    Validates the bucket+key structure, not just the prefix — a bare
    ``photo://`` (no bucket, no key) is rejected so downstream parsing
    can rely on the format being well-formed."""
    if not ref or not isinstance(ref, str):
        return False
    if not ref.startswith("photo://"):
        return False
    return bool(_PHOTO_REF_RE.match(ref))


def _parse_ref(ref: str) -> Tuple[str, str]:
    """Return (bucket, key) tuple from a ``photo://bucket/key`` URL.
    Raises ValueError on malformed refs so callers can decide whether to
    fall back to base64 or surface the error."""
    m = _PHOTO_REF_RE.match(ref)
    if not m:
        raise ValueError(f"Not a valid photo:// reference: {ref[:80]}")
    return m.group(1), m.group(2)


def _build_ref(key: str) -> str:
    return f"photo://{_bucket()}/{key}"


def _ext_from_data_url(data_url: str) -> str:
    """Pull a sensible extension out of a base64 data URL header. Falls
    back to ``jpg`` for unknown mime types (safest for downstream PDF
    embedding — every image renderer handles JPEG)."""
    try:
        head = data_url.split(",", 1)[0]
        mime = head.split(":", 1)[1].split(";", 1)[0].strip().lower()
        mapping = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/avif": "avif",
            "image/heic": "heic",
            "image/heif": "heif",
            "image/gif": "gif",
        }
        return mapping.get(mime, "jpg")
    except Exception:
        return "jpg"


def _build_key(source_id: str, ext: str) -> str:
    """Build the object key. Layout: ``photos/<YYYY>/<MM>/<source>/<uuid>.<ext>``
    so the bucket can be browsed by year/month in the R2 dashboard and the
    source ID is preserved for forensics. UUID prevents collisions."""
    today = _dt.datetime.now(_dt.timezone.utc)
    safe_src = "".join(c if c.isalnum() or c in "-_." else "_" for c in (source_id or "unknown"))
    return f"photos/{today:%Y/%m}/{safe_src}/{uuid.uuid4().hex}.{ext}"


# ── Public API ────────────────────────────────────────────────────────
async def upload_photo_bytes(
    data: bytes,
    *,
    ext: str = "jpg",
    source_id: str = "unknown",
    content_type: Optional[str] = None,
) -> str:
    """Upload raw bytes to S3 and return the ``photo://`` reference.

    Raises RuntimeError if storage isn't configured — caller should
    catch and fall back to base64 storage so unconfigured deploys
    continue to work.
    """
    import asyncio
    if not is_configured():
        raise RuntimeError("photo_storage not configured (missing env vars)")
    c = _client()
    if c is None:
        raise RuntimeError("photo_storage client failed to initialize")
    key = _build_key(source_id, ext)
    ct = content_type or {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "avif": "image/avif",
        "heic": "image/heic",
        "heif": "image/heif",
        "gif": "image/gif",
    }.get(ext.lower(), "application/octet-stream")
    # boto3 PUT is synchronous — wrap with to_thread so the event loop isn't blocked
    await asyncio.to_thread(
        c.put_object,
        Bucket=_bucket(),
        Key=key,
        Body=data,
        ContentType=ct,
        CacheControl="public, max-age=31536000, immutable",
    )
    ref = _build_ref(key)
    logger.info(f"[photo-storage] uploaded {len(data)/1024:.1f} KB → {ref}")
    return ref


async def upload_data_url(data_url: str, source_id: str = "unknown") -> str:
    """Upload a base64 ``data:image/...`` URL (the format every existing
    record uses) directly to S3. Returns a ``photo://`` reference."""
    try:
        head, b64 = data_url.split(",", 1)
    except ValueError as e:
        raise ValueError("Not a valid base64 data URL") from e
    raw = base64.b64decode(b64)
    ext = _ext_from_data_url(data_url)
    content_type = None
    try:
        content_type = head.split(":", 1)[1].split(";", 1)[0].strip().lower()
    except Exception:
        pass
    return await upload_photo_bytes(
        raw, ext=ext, source_id=source_id, content_type=content_type
    )


async def read_photo_bytes(ref: str) -> bytes:
    """Read photo bytes from EITHER a ``photo://`` reference OR a base64
    ``data:`` URL. This is the unifying read API every caller should use
    so legacy + migrated records work identically.

    Raises ValueError on malformed refs.
    """
    import asyncio
    if not ref or not isinstance(ref, str):
        raise ValueError("empty photo reference")
    if ref.startswith("data:"):
        try:
            _head, b64 = ref.split(",", 1)
            return base64.b64decode(b64)
        except Exception as e:
            raise ValueError(f"corrupt base64 data URL: {e}") from e
    if not is_storage_ref(ref):
        raise ValueError(f"unrecognized photo ref scheme: {ref[:40]}")
    bucket, key = _parse_ref(ref)
    c = _client()
    if c is None:
        raise RuntimeError("photo_storage client unavailable but ref requires it")
    obj = await asyncio.to_thread(c.get_object, Bucket=bucket, Key=key)
    body = obj["Body"]
    buf = io.BytesIO()
    while True:
        chunk = await asyncio.to_thread(body.read, 1024 * 256)
        if not chunk:
            break
        buf.write(chunk)
    return buf.getvalue()


def read_photo_bytes_sync(ref: str) -> bytes:
    """Synchronous variant of read_photo_bytes — used by sync PDF render
    paths (weasyprint) that can't await. Safe to call from inside an
    ``asyncio.to_thread`` wrapper. Same dual-read contract: handles both
    base64 ``data:`` URLs and ``photo://`` refs."""
    if not ref or not isinstance(ref, str):
        raise ValueError("empty photo reference")
    if ref.startswith("data:"):
        try:
            _head, b64 = ref.split(",", 1)
            return base64.b64decode(b64)
        except Exception as e:
            raise ValueError(f"corrupt base64 data URL: {e}") from e
    if not is_storage_ref(ref):
        raise ValueError(f"unrecognized photo ref scheme: {ref[:40]}")
    bucket, key = _parse_ref(ref)
    c = _client()
    if c is None:
        raise RuntimeError("photo_storage client unavailable but ref requires it")
    obj = c.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()


def resolve_to_data_url_sync(ref: str) -> str:
    """Sync helper: take ANY photo ref (data: or photo://) and return a
    base64 ``data:image/...`` URL suitable for embedding in HTML/PDF.
    Returns the input unchanged when it's already a data: URL. Returns
    empty string on failure (caller should treat as "no photo")."""
    if not ref or not isinstance(ref, str):
        return ""
    if ref.startswith("data:"):
        return ref
    if not is_storage_ref(ref):
        return ""
    try:
        raw = read_photo_bytes_sync(ref)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[photo-storage] resolve_to_data_url_sync failed for {ref[:80]}: {e}")
        return ""
    # Pick a sensible content-type from the key extension.
    ext = (ref.rsplit(".", 1)[-1] or "jpg").lower()
    ct = {
        "png": "image/png", "webp": "image/webp", "avif": "image/avif",
        "heic": "image/heic", "heif": "image/heif", "gif": "image/gif",
    }.get(ext, "image/jpeg")
    return f"data:{ct};base64,{base64.b64encode(raw).decode('ascii')}"


async def presigned_get_url(ref: str, ttl_seconds: int = 900) -> str:
    """Mint a presigned GET URL the browser can fetch directly. Use this
    when serving full-resolution photos to the gallery lightbox so we
    don't proxy the bytes through FastAPI. TTL defaults to 15 min."""
    import asyncio
    if not is_storage_ref(ref):
        raise ValueError(f"not a cloud photo ref: {ref[:40]}")
    bucket, key = _parse_ref(ref)
    c = _client()
    if c is None:
        raise RuntimeError("photo_storage client unavailable")
    url = await asyncio.to_thread(
        c.generate_presigned_url,
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=ttl_seconds,
    )
    return url


async def delete_photo(ref: str) -> bool:
    """Best-effort delete. Returns True on success, False otherwise.
    Never raises — orphaned photos in R2 are cheap; we don't want a
    transient network failure to block the user from deleting a
    record."""
    import asyncio
    if not is_storage_ref(ref):
        return False
    try:
        bucket, key = _parse_ref(ref)
        c = _client()
        if c is None:
            return False
        await asyncio.to_thread(c.delete_object, Bucket=bucket, Key=key)
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[photo-storage] delete failed for {ref}: {e}")
        return False


async def health_check() -> dict:
    """Lightweight admin sanity check. Verifies the client can
    head-bucket. Used by /api/admin/photo-storage/health."""
    import asyncio
    if not is_configured():
        return {"configured": False, "ok": False, "reason": "env vars missing"}
    c = _client()
    if c is None:
        return {"configured": True, "ok": False, "reason": "client init failed"}
    try:
        await asyncio.to_thread(c.head_bucket, Bucket=_bucket())
        return {
            "configured": True,
            "ok": True,
            "bucket": _bucket(),
            "endpoint": _env("S3_ENDPOINT_URL"),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "configured": True,
            "ok": False,
            "bucket": _bucket(),
            "reason": f"head_bucket failed: {e}",
        }
