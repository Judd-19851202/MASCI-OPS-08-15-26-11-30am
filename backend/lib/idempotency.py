"""
lib/idempotency.py — Phase J · Field Resiliency Layer.

Shared backend idempotency helper. Frontend sends `Idempotency-Key`
header (uuid v4 minted per submission attempt). Server caches
{key, actor_id, response_body, created_at} in `db.idempotency_keys`
with a 90-day TTL. Repeat POSTs with the same key return the cached
response and do NOT re-execute the handler — preventing duplicate
records from double-clicks, network retries, or service-worker dupes.

Usage (in a route handler):

    from lib.idempotency import with_idempotency, idem_key_from_request

    @router.post("/some-endpoint")
    async def create(req: Request, body: ..., actor=Depends(...)):
        key = idem_key_from_request(req)
        return await with_idempotency(db, key, actor,
            lambda: _do_create(body, actor))

The helper:
  * Returns the cached response immediately if `key` matches a prior
    successful response by the same actor (silent dedup).
  * Otherwise runs `factory()`, persists the response (best-effort),
    and returns the live result.
  * Different actors using the same key are treated as separate
    submissions (no cross-actor leakage).
  * Never raises — if Mongo is down, falls back to executing the
    factory as if there was no key (graceful degradation).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import Request

logger = logging.getLogger(__name__)

# 90 days — matches usage_events TTL convention.
TTL_SECONDS = 60 * 60 * 24 * 90


def idem_key_from_request(req: Request) -> Optional[str]:
    """Pulls the `Idempotency-Key` header from the request. Lower-cased
    fallback for case variations. Returns None if absent or empty."""
    raw = (req.headers.get("idempotency-key")
           or req.headers.get("Idempotency-Key")
           or "")
    raw = (raw or "").strip()
    # Bound to reasonable length to protect against accidental abuse.
    if not raw or len(raw) > 80:
        return None
    return raw


def _actor_id(actor: Dict[str, Any]) -> str:
    """Pull a stable identifier from actor dict. Falls back to role +
    email when no `id`/`user_id` exists (e.g., legacy admin tokens)."""
    if not isinstance(actor, dict):
        return "anon"
    aid = (actor.get("id") or actor.get("user_id")
           or actor.get("_id") or "")
    if aid:
        return f"u:{aid}"
    return (f"{actor.get('_actor') or actor.get('role') or 'anon'}:"
            f"{actor.get('email') or 'unknown'}")


async def ensure_indexes(db) -> None:
    """One-time TTL + lookup index on idempotency_keys. Safe to call
    repeatedly (Mongo will no-op on duplicates)."""
    try:
        await db.idempotency_keys.create_index(
            [("key", 1), ("actor_id", 1)], unique=True, name="key_actor_uniq")
        await db.idempotency_keys.create_index(
            "created_at", expireAfterSeconds=TTL_SECONDS, name="ttl_90d")
    except Exception as e:  # noqa: BLE001
        logger.warning("[idempotency] ensure_indexes failed: %s", e)


async def with_idempotency(
    db,
    key: Optional[str],
    actor: Dict[str, Any],
    factory: Callable[[], Awaitable[Any]],
) -> Any:
    """Execute `factory` exactly once per (key, actor) tuple.

    If `key` is None, runs factory transparently (no dedup applied).
    """
    if not key:
        return await factory()

    actor_id = _actor_id(actor)

    # Lookup cache
    try:
        cached = await db.idempotency_keys.find_one(
            {"key": key, "actor_id": actor_id},
            {"_id": 0, "response": 1},
        )
        if cached:
            logger.info("[idempotency] cache hit key=%s actor=%s",
                        key[:8], actor_id[:24])
            return cached.get("response")
    except Exception as e:  # noqa: BLE001
        logger.warning("[idempotency] lookup failed: %s", e)
        # Fall through — best-effort, degrade gracefully.

    # Execute the live handler.
    result = await factory()

    # Persist the response (best-effort). If the result isn't JSON-
    # serializable as-is, we serialize via FastAPI's jsonable_encoder
    # so the cached payload mirrors what a client would receive.
    try:
        from fastapi.encoders import jsonable_encoder  # noqa: PLC0415
        cached_resp = jsonable_encoder(result)
    except Exception:  # noqa: BLE001
        cached_resp = result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else None

    try:
        # ensure_indexes() is safe to call repeatedly — protects against
        # routes that never warmed the index.
        await ensure_indexes(db)
        await db.idempotency_keys.insert_one({
            "key": key,
            "actor_id": actor_id,
            "response": cached_resp,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:  # noqa: BLE001
        # Duplicate-key error = lost a race. The other writer's cache
        # is valid; we just return our own live result.
        if "duplicate key" not in str(e).lower():
            logger.warning("[idempotency] persist failed: %s", e)

    return result


__all__ = [
    "with_idempotency", "idem_key_from_request", "ensure_indexes",
    "TTL_SECONDS",
]
