from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency scaffold
    import redis.asyncio as redis_asyncio
except Exception:  # noqa: BLE001
    redis_asyncio = None


def _now_epoch() -> float:
    return time.time()


class BaseRuntimeCache:
    backend_name = "memory"
    redis_requested = False
    redis_active = False

    async def get_json(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    def meta(self) -> Dict[str, Any]:
        return {
            "backend": self.backend_name,
            "redis_requested": self.redis_requested,
            "redis_active": self.redis_active,
        }


class InMemoryRuntimeCache(BaseRuntimeCache):
    backend_name = "memory"

    def __init__(self, *, redis_requested: bool = False) -> None:
        self.redis_requested = redis_requested
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_json(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at = float(entry.get("expires_at") or 0)
            if expires_at and expires_at <= _now_epoch():
                self._store.pop(key, None)
                return None
            return entry.get("value")

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        ttl = max(1, int(ttl_seconds or 1))
        async with self._lock:
            self._store[key] = {
                "value": value,
                "expires_at": _now_epoch() + ttl,
            }

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)


class RedisRuntimeCache(BaseRuntimeCache):
    backend_name = "redis"
    redis_requested = True
    redis_active = True

    def __init__(self, redis_url: str, *, namespace: str = "masci:runtime-cache") -> None:
        self._namespace = namespace
        self._client = redis_asyncio.from_url(redis_url, decode_responses=True)

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self._client.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        ttl = max(1, int(ttl_seconds or 1))
        await self._client.set(self._key(key), json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(self._key(key))


_CACHE_SINGLETON: Optional[BaseRuntimeCache] = None


def redis_requested() -> bool:
    return (os.environ.get("REDIS_ENABLED") or "").strip().lower() in {"1", "true", "yes", "on"}


def get_runtime_cache() -> BaseRuntimeCache:
    global _CACHE_SINGLETON
    if _CACHE_SINGLETON is not None:
        return _CACHE_SINGLETON

    requested = redis_requested()
    redis_url = (os.environ.get("REDIS_URL") or "").strip()
    if requested and redis_url and redis_asyncio is not None:
        _CACHE_SINGLETON = RedisRuntimeCache(redis_url)
        return _CACHE_SINGLETON

    _CACHE_SINGLETON = InMemoryRuntimeCache(redis_requested=requested)
    return _CACHE_SINGLETON


async def get_or_set_runtime_json(
    key: str,
    *,
    ttl_seconds: int,
    builder,
) -> Any:
    cache = get_runtime_cache()
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    built = await builder()
    try:
        await cache.set_json(key, built, ttl_seconds=ttl_seconds)
    except Exception:  # noqa: BLE001
        pass
    return built


__all__ = [
    "BaseRuntimeCache",
    "InMemoryRuntimeCache",
    "RedisRuntimeCache",
    "get_runtime_cache",
    "get_or_set_runtime_json",
    "redis_requested",
]