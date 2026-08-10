"""
promo_assets storage — iter347 (Promo Asset Library)

A small helper layer on top of the existing photo_storage R2 client so the
admin promo-asset workflow can:

  • upload arbitrary media (mp4/mov/webm/jpg/png) to a dedicated key prefix
  • mint long-TTL presigned URLs for browser playback + download
  • delete objects when an asset is removed from the admin library

This is NOT a replacement for `photo_storage`. It deliberately reuses the
same boto3 client + R2 credentials so we don't add new env vars or a
second SDK surface.
"""
from __future__ import annotations
import asyncio
import logging
import re
import uuid
from typing import Optional, Tuple

import photo_storage  # reuse R2 client + bucket helpers
from lib.storage_ownership import build_env_owned_key, current_app_env, current_env_owns_key

logger = logging.getLogger(__name__)

PROMO_KEY_PREFIX = "promo-assets"

# `promo://<bucket>/<key>` — keeps the same reference grammar as
# `photo://` so admins can scan logs / mongo dumps and instantly tell
# what they're looking at.
_PROMO_REF_RE = re.compile(r"^promo://([^/]+)/(.+)$")


def is_configured() -> bool:
    return photo_storage.is_configured()


def _slug(value: str) -> str:
    """Filename-safe lowercase slug. Spaces → '-', non [a-z0-9-_] stripped."""
    s = (value or "").strip().lower()
    s = re.sub(r"[^a-z0-9\-_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def build_key(category: str, name_hint: str, ext: str) -> str:
    """Deterministic key shape: `promo-assets/<category-slug>/<uuid>-<name>.<ext>`."""
    cat = _slug(category)
    name = _slug(name_hint)[:60]
    ext_clean = (ext or "bin").lstrip(".").lower()
    return build_env_owned_key(PROMO_KEY_PREFIX, f"{cat}/{uuid.uuid4().hex[:10]}-{name}.{ext_clean}")


def is_promo_ref(ref: Optional[str]) -> bool:
    if not ref or not isinstance(ref, str):
        return False
    return bool(_PROMO_REF_RE.match(ref))


def parse_ref(ref: str) -> Tuple[str, str]:
    m = _PROMO_REF_RE.match(ref)
    if not m:
        raise ValueError(f"Not a valid promo:// reference: {ref[:80]}")
    return m.group(1), m.group(2)


def build_ref(key: str) -> str:
    return f"promo://{photo_storage._bucket()}/{key}"  # noqa: SLF001


async def upload_bytes(
    data: bytes,
    *,
    category: str,
    name_hint: str,
    ext: str,
    content_type: Optional[str] = None,
) -> Tuple[str, str]:
    """Upload `data` to R2 under the promo-assets prefix. Returns
    (promo_ref, raw_key). Raises RuntimeError if storage isn't configured.
    """
    if not is_configured():
        raise RuntimeError("promo_assets storage not configured (missing S3_* env vars)")
    c = photo_storage._client()  # noqa: SLF001
    if c is None:
        raise RuntimeError("promo_assets storage client failed to initialize")
    key = build_key(category, name_hint, ext)
    ct = content_type or _guess_content_type(ext)
    # CacheControl: longer for promo (1 day default) — admins are NOT
    # editing these every hour. Browser caching is fine.
    await asyncio.to_thread(
        c.put_object,
        Bucket=photo_storage._bucket(),  # noqa: SLF001
        Key=key,
        Body=data,
        ContentType=ct,
        CacheControl="public, max-age=86400",
    )
    ref = build_ref(key)
    logger.info(
        f"[promo-assets] uploaded {len(data) / (1024 * 1024):.1f} MB → {ref}"
    )
    return ref, key


def _guess_content_type(ext: str) -> str:
    e = (ext or "").lstrip(".").lower()
    return {
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "webm": "video/webm",
        "m4v": "video/x-m4v",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "pdf": "application/pdf",
        "json": "application/json",
    }.get(e, "application/octet-stream")


async def presigned_url(ref: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    """Mint a presigned GET URL for direct browser playback / download.
    Default TTL = 7 days (R2 maximum). Admin can re-mint anytime."""
    _bucket, key = parse_ref(ref)
    return await photo_storage.presigned_get_url_for_key(key, ttl_seconds=ttl_seconds)


async def delete_ref(ref: str) -> None:
    """Best-effort delete from R2. Swallows errors so a stale-key cleanup
    can't 500 the admin DELETE call — the mongo row goes away regardless."""
    try:
        _bucket, key = parse_ref(ref)
        if not current_env_owns_key(key):
            logger.info(
                "[promo-assets] delete skipped for non-owned key=%s current_env=%s",
                key,
                current_app_env(),
            )
            return
        c = photo_storage._client()  # noqa: SLF001
        if c is None:
            return
        await asyncio.to_thread(
            c.delete_object,
            Bucket=photo_storage._bucket(),  # noqa: SLF001
            Key=key,
        )
        logger.info(f"[promo-assets] deleted {ref}")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[promo-assets] delete failed for {ref}: {e}")
