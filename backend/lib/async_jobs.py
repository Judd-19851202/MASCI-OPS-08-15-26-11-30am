from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from lib.runtime_cache import get_runtime_cache

JOB_META_TTL_SECONDS = 60 * 60

_BINARY_RESULTS: Dict[str, Dict[str, Any]] = {}
_BINARY_LOCK = asyncio.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at_iso(ttl_seconds: int = JOB_META_TTL_SECONDS) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(60, int(ttl_seconds)))).isoformat()


def _job_meta_key(job_id: str) -> str:
    return f"async-job:{job_id}:meta"


async def create_async_job(
    kind: str,
    *,
    result_type: str = "json",
    message: str = "Queued",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cache = get_runtime_cache()
    job_id = str(uuid.uuid4())
    result_token = uuid.uuid4().hex
    meta = {
        "job_id": job_id,
        "kind": kind,
        "status": "queued",
        "result_type": result_type,
        "message": message,
        "details": dict(details or {}),
        "error": None,
        "result": None,
        "result_token": result_token,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "expires_at": _expires_at_iso(),
        "cache_backend": cache.meta(),
    }
    await cache.set_json(_job_meta_key(job_id), meta, ttl_seconds=JOB_META_TTL_SECONDS)
    return meta


async def get_async_job(job_id: str) -> Optional[Dict[str, Any]]:
    cache = get_runtime_cache()
    meta = await cache.get_json(_job_meta_key(job_id))
    if not isinstance(meta, dict):
        return None
    return meta


async def _save_job_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    cache = get_runtime_cache()
    meta["updated_at"] = _now_iso()
    meta["expires_at"] = _expires_at_iso()
    await cache.set_json(_job_meta_key(str(meta.get("job_id"))), meta, ttl_seconds=JOB_META_TTL_SECONDS)
    return meta


async def patch_async_job(job_id: str, **updates: Any) -> Optional[Dict[str, Any]]:
    meta = await get_async_job(job_id)
    if not meta:
        return None
    for key, value in updates.items():
        if key == "details" and isinstance(value, dict):
            merged = dict(meta.get("details") or {})
            merged.update(value)
            meta["details"] = merged
            continue
        meta[key] = value
    return await _save_job_meta(meta)


async def mark_async_job_processing(
    job_id: str,
    *,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    updates: Dict[str, Any] = {"status": "processing"}
    if message is not None:
        updates["message"] = message
    if details is not None:
        updates["details"] = details
    return await patch_async_job(job_id, **updates)


async def complete_async_job_json(
    job_id: str,
    result: Dict[str, Any],
    *,
    message: str = "Completed",
) -> Optional[Dict[str, Any]]:
    return await patch_async_job(
        job_id,
        status="completed",
        message=message,
        result=result,
        error=None,
    )


async def complete_async_job_binary(
    job_id: str,
    *,
    content: bytes,
    media_type: str,
    filename: str,
    message: str = "Completed",
    result_meta: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    meta = await get_async_job(job_id)
    if not meta:
        return None
    token = str(meta.get("result_token") or "")
    async with _BINARY_LOCK:
        _BINARY_RESULTS[job_id] = {
            "content": content,
            "media_type": media_type,
            "filename": filename,
            "token": token,
            "meta": dict(result_meta or {}),
            "expires_at": _expires_at_iso(),
        }
    result_payload = {
        "filename": filename,
        "media_type": media_type,
        "download_url": f"/api/jobs/{job_id}/result?token={token}",
        **dict(result_meta or {}),
    }
    return await patch_async_job(
        job_id,
        status="completed",
        message=message,
        result=result_payload,
        error=None,
    )


async def fail_async_job(
    job_id: str,
    *,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    return await patch_async_job(
        job_id,
        status="failed",
        message=message,
        error={"code": error_code, "message": message},
        details=details or {},
    )


async def get_async_job_binary_result(job_id: str, token: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    meta = await get_async_job(job_id)
    if not meta or str(meta.get("status")) != "completed":
        return None
    async with _BINARY_LOCK:
        stored = _BINARY_RESULTS.get(job_id)
    if not stored or str(stored.get("token") or "") != str(token or ""):
        return None
    return meta, stored


def serialize_async_job_status(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ok": True,
        "job_id": meta.get("job_id"),
        "kind": meta.get("kind"),
        "status": meta.get("status"),
        "message": meta.get("message"),
        "details": meta.get("details") or {},
        "error": meta.get("error"),
        "result": meta.get("result") if str(meta.get("status")) == "completed" else None,
        "created_at": meta.get("created_at"),
        "updated_at": meta.get("updated_at"),
        "expires_at": meta.get("expires_at"),
        "poll_after_ms": 1400 if str(meta.get("status")) in {"queued", "processing"} else 0,
        "cache_backend": meta.get("cache_backend") or {},
    }


__all__ = [
    "complete_async_job_binary",
    "complete_async_job_json",
    "create_async_job",
    "fail_async_job",
    "get_async_job",
    "get_async_job_binary_result",
    "mark_async_job_processing",
    "patch_async_job",
    "serialize_async_job_status",
]