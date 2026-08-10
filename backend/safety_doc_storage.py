"""
safety_doc_storage.py — R2/S3 object-storage helper for Safety Portal
document library.

Mirrors `photo_storage.py` but uses the ``safety-docs/<YYYY>/<MM>/...``
key prefix and a ``doc://<bucket>/<key>`` reference scheme so document
records can be distinguished at-a-glance from photo records in the DB.

Hybrid storage contract: callers should fall back to inline base64
(``data:...``) when ``is_configured()`` returns False — keeps tests +
unconfigured dev environments functional without surprise.
"""
from __future__ import annotations

import asyncio
import base64
import datetime as _dt
import io
import logging
import os
import re
import uuid
from typing import Optional, Tuple

from lib.storage_ownership import (
    build_env_owned_key,
    build_storage_ref,
    current_app_env,
    current_env_owns_key,
    describe_key_ownership,
)

logger = logging.getLogger(__name__)

# ── Lazily-initialised boto3 client (shared module-level singleton) ──
_client_singleton = None


def _env(key: str) -> str:
    return (os.environ.get(key) or "").strip()


def is_configured() -> bool:
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
    global _client_singleton
    if _client_singleton is not None:
        return _client_singleton
    if not is_configured():
        return None
    try:
        import boto3  # noqa: PLC0415
        from botocore.config import Config  # noqa: PLC0415
        _client_singleton = boto3.client(
            "s3",
            endpoint_url=_env("S3_ENDPOINT_URL"),
            aws_access_key_id=_env("S3_ACCESS_KEY"),
            aws_secret_access_key=_env("S3_SECRET_KEY"),
            region_name=_env("S3_REGION") or "auto",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        logger.info(f"[safety-doc-storage] boto3 client initialized · bucket={_bucket()}")
        return _client_singleton
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[safety-doc-storage] client init failed: {e}")
        return None


# ── Reference scheme: doc://<bucket>/<key> ─────────────────────────────
_DOC_REF_RE = re.compile(r"^doc://([^/]+)/(.+)$")


def is_storage_ref(ref: Optional[str]) -> bool:
    if not ref or not isinstance(ref, str):
        return False
    return bool(_DOC_REF_RE.match(ref))


def _parse_ref(ref: str) -> Tuple[str, str]:
    m = _DOC_REF_RE.match(ref)
    if not m:
        raise ValueError(f"Not a valid doc:// reference: {ref[:80]}")
    return m.group(1), m.group(2)


def _build_key(doc_id: str, filename: str) -> str:
    """``safety-docs/<YYYY>/<MM>/<doc_id>/<uuid>-<safe-filename>``"""
    today = _dt.datetime.now(_dt.timezone.utc)
    safe_doc = "".join(c if c.isalnum() or c in "-_." else "_" for c in (doc_id or "unknown"))[:48]
    safe_fn = "".join(c if c.isalnum() or c in "-_." else "_" for c in (filename or "file"))[:80]
    return build_env_owned_key("safety-docs", f"{today:%Y/%m}/{safe_doc}/{uuid.uuid4().hex[:8]}-{safe_fn}")


def build_ref_for_key(key: str) -> str:
    return build_storage_ref("doc", _bucket(), key)


def _is_not_found_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None) or {}
    error = response.get("Error") or {}
    code = str(error.get("Code") or response.get("ResponseMetadata", {}).get("HTTPStatusCode") or "").strip().lower()
    return code in {"404", "nosuchkey", "notfound", "nosuchbucket"}


def _object_exists_sync(bucket: str, key: str) -> bool:
    c = _client()
    if c is None:
        raise RuntimeError("safety_doc_storage client unavailable")
    try:
        c.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as exc:  # noqa: BLE001
        if _is_not_found_error(exc):
            return False
        raise


async def _guard_explicit_key_write(key: str) -> None:
    ownership = describe_key_ownership(key)
    env = current_app_env()
    if ownership.namespaced and ownership.owner_env != env:
        raise PermissionError(
            f"refusing to write {ownership.family} object owned by {ownership.owner_env} from {env}",
        )
    if ownership.is_legacy and await asyncio.to_thread(_object_exists_sync, _bucket(), ownership.key):
        raise PermissionError(
            f"refusing to overwrite legacy unowned object key {ownership.key}",
        )


async def upload_doc_bytes(
    data: bytes,
    *,
    doc_id: str,
    filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload raw doc bytes to R2 and return the ``doc://`` reference.
    Raises RuntimeError if storage isn't configured — caller should
    catch and fall back to inline base64 so unconfigured envs still
    work end-to-end."""
    if not is_configured():
        raise RuntimeError("safety_doc_storage not configured (missing R2 env vars)")
    c = _client()
    if c is None:
        raise RuntimeError("safety_doc_storage client failed to initialize")
    key = _build_key(doc_id, filename)
    await asyncio.to_thread(
        c.put_object,
        Bucket=_bucket(),
        Key=key,
        Body=data,
        ContentType=content_type,
        # Docs are private — admin/safety/HR pull via the FastAPI download
        # endpoint which serves them through the app's own auth gate.
        # CacheControl conservative so cross-portal updates aren't stuck.
        CacheControl="private, max-age=300",
    )
    ref = build_ref_for_key(key)
    logger.info(f"[safety-doc-storage] uploaded {len(data)/1024:.1f} KB → {ref}")
    return ref


async def upload_bytes(data: bytes, *, key: str, content_type: str = "application/octet-stream") -> str:
    """Upload raw bytes to an explicit key and return the matching doc:// ref.

    Used by restore paths that need to rehydrate archived document objects back
    into object storage without inventing new keys that would break persisted
    document references.
    """
    if not is_configured():
        raise RuntimeError("safety_doc_storage not configured (missing R2 env vars)")
    c = _client()
    if c is None:
        raise RuntimeError("safety_doc_storage client failed to initialize")
    await _guard_explicit_key_write(key)
    await asyncio.to_thread(
        c.put_object,
        Bucket=_bucket(),
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="private, max-age=300",
    )
    return build_ref_for_key(key)


async def read_doc_bytes(ref: str) -> bytes:
    """Read doc bytes from a ``doc://`` reference OR a base64
    ``data:`` URL (backward compatibility with pre-R2 records)."""
    if not ref or not isinstance(ref, str):
        raise ValueError("empty doc reference")
    if ref.startswith("data:"):
        try:
            _head, b64 = ref.split(",", 1)
            pad = (-len(b64)) % 4
            if pad:
                b64 = b64 + ("=" * pad)
            return base64.b64decode(b64, validate=False)
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"corrupt base64 data URL: {e}") from e
    if not is_storage_ref(ref):
        raise ValueError(f"unrecognized doc ref scheme: {ref[:40]}")
    bucket, key = _parse_ref(ref)
    c = _client()
    if c is None:
        raise RuntimeError("safety_doc_storage client unavailable but ref requires it")
    obj = await asyncio.to_thread(c.get_object, Bucket=bucket, Key=key)
    body = obj["Body"]
    buf = io.BytesIO()
    while True:
        chunk = await asyncio.to_thread(body.read, 1024 * 256)
        if not chunk:
            break
        buf.write(chunk)
    return buf.getvalue()


async def delete_doc(ref: Optional[str]) -> bool:
    """Best-effort delete from R2. Returns True on success, False if
    nothing was deleted (unconfigured, malformed ref, base64-only, etc.).
    Callers should NOT fail their request just because R2 delete failed —
    the DB record removal is the authoritative cleanup signal."""
    if not ref or not isinstance(ref, str):
        return False
    if ref.startswith("data:"):
        return False  # base64 lives in the DB only — DB delete is enough
    if not is_storage_ref(ref):
        return False
    bucket, key = _parse_ref(ref)
    if not current_env_owns_key(key):
        logger.info(
            "[safety-doc-storage] delete skipped for non-owned key=%s current_env=%s",
            key,
            current_app_env(),
        )
        return False
    c = _client()
    if c is None:
        return False
    try:
        await asyncio.to_thread(c.delete_object, Bucket=bucket, Key=key)
        logger.info(f"[safety-doc-storage] deleted {ref}")
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[safety-doc-storage] delete failed for {ref}: {e}")
        return False
