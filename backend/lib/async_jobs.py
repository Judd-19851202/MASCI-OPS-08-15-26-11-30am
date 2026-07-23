from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient

from lib.runtime_cache import get_runtime_cache

JOB_META_TTL_SECONDS = 60 * 60
MAX_JSON_RESULT_BYTES = 256 * 1024
MAX_BINARY_RESULT_BYTES = 10 * 1024 * 1024
TERMINAL_STATUSES = {"completed", "failed", "expired"}

_BINARY_RESULTS: Dict[str, Dict[str, Any]] = {}
_BINARY_LOCK = asyncio.Lock()
_MONGO_CLIENT: Optional[AsyncIOMotorClient] = None
_MONGO_META_COLLECTION = None
_MONGO_BINARY_COLLECTION = None
_MONGO_LOCK = asyncio.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at_iso(ttl_seconds: int = JOB_META_TTL_SECONDS) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(60, int(ttl_seconds)))).isoformat()


def _job_meta_key(job_id: str) -> str:
    return f"async-job:{job_id}:meta"


def _mongo_expiry_dt(meta: Dict[str, Any]) -> datetime:
    raw = str(meta.get("expires_at") or "").strip()
    if raw:
        try:
            dt = datetime.fromisoformat(raw)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:  # noqa: BLE001
            pass
    return datetime.now(timezone.utc) + timedelta(seconds=JOB_META_TTL_SECONDS)


def _is_expired_meta(meta: Dict[str, Any]) -> bool:
    raw = str(meta.get("expires_at") or "").strip()
    if not raw:
        return False
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt <= datetime.now(timezone.utc)
    except Exception:  # noqa: BLE001
        return False


def _json_size_bytes(value: Any) -> int:
    return len(json.dumps(value, default=str, ensure_ascii=False).encode("utf-8"))


def _is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(value, ensure_ascii=False)
        return True
    except Exception:  # noqa: BLE001
        return False


def _validate_meta(meta: Dict[str, Any]) -> bool:
    if not isinstance(meta, dict):
        return False
    if not str(meta.get("job_id") or "").strip():
        return False
    status = str(meta.get("status") or "").strip().lower()
    if status not in {"queued", "processing", "completed", "failed", "expired"}:
        return False
    result_type = str(meta.get("result_type") or "json").strip().lower()
    if result_type not in {"json", "binary"}:
        return False
    try:
        if result_type == "json" and meta.get("result") is not None:
            if not _is_json_serializable(meta.get("result")):
                return False
            if _json_size_bytes(meta.get("result")) > MAX_JSON_RESULT_BYTES:
                return False
        if result_type == "binary" and meta.get("result") is not None:
            result = meta.get("result") or {}
            if not isinstance(result, dict):
                return False
            if result.get("download_url") and not str(result.get("download_url")).startswith("/api/jobs/"):
                return False
    except Exception:  # noqa: BLE001
        return False
    return True


async def _delete_persisted_job(job_id: str) -> None:
    coll = await _get_job_meta_collection()
    if coll is not None:
        try:
            await coll.delete_one({"job_id": job_id})
        except Exception:  # noqa: BLE001
            pass
    bcoll = await _get_job_binary_collection()
    if bcoll is not None:
        try:
            await bcoll.delete_one({"job_id": job_id})
        except Exception:  # noqa: BLE001
            pass


async def _ensure_mongo_collections():
    global _MONGO_CLIENT, _MONGO_META_COLLECTION, _MONGO_BINARY_COLLECTION
    if _MONGO_META_COLLECTION is not None and _MONGO_BINARY_COLLECTION is not None:
        return _MONGO_META_COLLECTION, _MONGO_BINARY_COLLECTION
    mongo_url = (os.environ.get("MONGO_URL") or "").strip()
    db_name = (os.environ.get("DB_NAME") or "").strip()
    if not mongo_url or not db_name:
        return None, None
    async with _MONGO_LOCK:
        if _MONGO_META_COLLECTION is None or _MONGO_BINARY_COLLECTION is None:
            if _MONGO_CLIENT is None:
                _MONGO_CLIENT = AsyncIOMotorClient(mongo_url, tz_aware=True)
            database = _MONGO_CLIENT[db_name]
            _MONGO_META_COLLECTION = database["async_job_meta"]
            _MONGO_BINARY_COLLECTION = database["async_job_binary"]
            try:
                await _MONGO_META_COLLECTION.create_index("job_id", unique=True)
                await _MONGO_META_COLLECTION.create_index("expires_at_dt", expireAfterSeconds=0)
                await _MONGO_BINARY_COLLECTION.create_index("job_id", unique=True)
                await _MONGO_BINARY_COLLECTION.create_index("expires_at_dt", expireAfterSeconds=0)
            except Exception:  # noqa: BLE001
                pass
    return _MONGO_META_COLLECTION, _MONGO_BINARY_COLLECTION


async def _get_job_meta_collection():
    coll, _ = await _ensure_mongo_collections()
    return coll


async def _get_job_binary_collection():
    _, coll = await _ensure_mongo_collections()
    return coll


def _meta_doc(meta: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(meta)
    doc["expires_at_dt"] = _mongo_expiry_dt(meta)
    return doc


async def _persist_job_meta(meta: Dict[str, Any]) -> None:
    coll = await _get_job_meta_collection()
    if coll is None:
        return
    doc = _meta_doc(meta)
    await coll.replace_one({"job_id": str(meta.get("job_id"))}, doc, upsert=True)


async def _load_persisted_job_meta(job_id: str) -> Optional[Dict[str, Any]]:
    coll = await _get_job_meta_collection()
    if coll is None:
        return None
    doc = await coll.find_one({"job_id": job_id}, {"_id": 0, "expires_at_dt": 0})
    if not isinstance(doc, dict):
        return None
    if not _validate_meta(doc):
        return None
    return doc


async def _persist_binary_result(job_id: str, stored: Dict[str, Any]) -> None:
    coll = await _get_job_binary_collection()
    if coll is None:
        return
    expires_at = str(stored.get("expires_at") or "").strip()
    try:
        expires_dt = datetime.fromisoformat(expires_at) if expires_at else datetime.now(timezone.utc) + timedelta(seconds=JOB_META_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        expires_dt = datetime.now(timezone.utc) + timedelta(seconds=JOB_META_TTL_SECONDS)
    if expires_dt.tzinfo is None:
        expires_dt = expires_dt.replace(tzinfo=timezone.utc)
    doc = {**stored, "job_id": job_id, "expires_at_dt": expires_dt}
    await coll.replace_one({"job_id": job_id}, doc, upsert=True)


async def _load_persisted_binary_result(job_id: str) -> Optional[Dict[str, Any]]:
    coll = await _get_job_binary_collection()
    if coll is None:
        return None
    doc = await coll.find_one({"job_id": job_id}, {"_id": 0, "expires_at_dt": 0, "job_id": 0})
    if not isinstance(doc, dict):
        return None
    if not isinstance(doc.get("content"), (bytes, bytearray)):
        return None
    if len(doc.get("content") or b"") > MAX_BINARY_RESULT_BYTES:
        return None
    if not str(doc.get("token") or "").strip():
        return None
    return doc


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
    try:
        await _persist_job_meta(meta)
    except Exception:  # noqa: BLE001
        pass
    return meta


async def get_async_job(job_id: str) -> Optional[Dict[str, Any]]:
    cache = get_runtime_cache()
    meta = await cache.get_json(_job_meta_key(job_id))
    if isinstance(meta, dict):
        if not _validate_meta(meta):
            try:
                await cache.delete(_job_meta_key(job_id))
            except Exception:  # noqa: BLE001
                pass
            meta = None
        elif _is_expired_meta(meta):
            try:
                await cache.delete(_job_meta_key(job_id))
            except Exception:  # noqa: BLE001
                pass
            await _delete_persisted_job(job_id)
            return None
        else:
            return meta
    if isinstance(meta, dict):
        return meta
    try:
        persisted = await _load_persisted_job_meta(job_id)
    except Exception:  # noqa: BLE001
        persisted = None
    if not isinstance(persisted, dict):
        return None
    if _is_expired_meta(persisted):
        await _delete_persisted_job(job_id)
        return None
    try:
        await cache.set_json(_job_meta_key(job_id), persisted, ttl_seconds=JOB_META_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        pass
    return persisted


async def _save_job_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    cache = get_runtime_cache()
    meta["updated_at"] = _now_iso()
    meta["expires_at"] = _expires_at_iso()
    await cache.set_json(_job_meta_key(str(meta.get("job_id"))), meta, ttl_seconds=JOB_META_TTL_SECONDS)
    try:
        await _persist_job_meta(meta)
    except Exception:  # noqa: BLE001
        pass
    return meta


async def patch_async_job(job_id: str, **updates: Any) -> Optional[Dict[str, Any]]:
    meta = await get_async_job(job_id)
    if not meta:
        return None
    if str(meta.get("status") or "") in TERMINAL_STATUSES:
        next_status = str(updates.get("status") or meta.get("status") or "")
        if next_status != str(meta.get("status") or ""):
            return meta
        if "result" in updates and updates.get("result") != meta.get("result"):
            return meta
        if "error" in updates and updates.get("error") != meta.get("error"):
            return meta
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
    if _json_size_bytes(result) > MAX_JSON_RESULT_BYTES:
        return await fail_async_job(
            job_id,
            error_code="result_too_large",
            message="Async job result exceeded JSON size limit",
            details={"max_bytes": MAX_JSON_RESULT_BYTES, "actual_bytes": _json_size_bytes(result)},
        )
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
    content_bytes = bytes(content or b"")
    if len(content_bytes) > MAX_BINARY_RESULT_BYTES:
        return await fail_async_job(
            job_id,
            error_code="binary_result_too_large",
            message="Async job binary exceeded size limit",
            details={"max_bytes": MAX_BINARY_RESULT_BYTES, "actual_bytes": len(content_bytes)},
        )
    meta = await get_async_job(job_id)
    if not meta:
        return None
    token = str(meta.get("result_token") or "")
    async with _BINARY_LOCK:
        _BINARY_RESULTS[job_id] = {
            "content": content_bytes,
            "media_type": media_type,
            "filename": filename,
            "token": token,
            "meta": dict(result_meta or {}),
            "expires_at": _expires_at_iso(),
        }
        stored = dict(_BINARY_RESULTS[job_id])
    try:
        await _persist_binary_result(job_id, stored)
    except Exception:  # noqa: BLE001
        pass
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
    if not stored:
        try:
            stored = await _load_persisted_binary_result(job_id)
        except Exception:  # noqa: BLE001
            stored = None
    if not stored or str(stored.get("token") or "") != str(token or ""):
        return None
    if not isinstance(stored.get("content"), (bytes, bytearray)):
        return None
    if len(stored.get("content") or b"") > MAX_BINARY_RESULT_BYTES:
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
    "MAX_BINARY_RESULT_BYTES",
    "MAX_JSON_RESULT_BYTES",
    "mark_async_job_processing",
    "patch_async_job",
    "serialize_async_job_status",
]