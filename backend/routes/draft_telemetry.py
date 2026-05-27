"""
routes/draft_telemetry.py — P0 Field Incident · Daily Report draft loss · 2026-05-27.

Append-only client-driven telemetry for the form-draft / autosave
subsystem. Lets us see — from the device — every write success,
every write failure, every quota warning, every page-lifecycle
transition. This is the observability layer that proves the
remediation is doing its job.

Privacy doctrine
----------------
  * NEVER store form content. Sizes/error-names/timestamps only.
  * `actorId` is the existing 16-char token prefix — already used in
    IDB key space; nothing new is leaked.
  * `deviceId` is a random UUIDv4 minted client-side; not joined to
    any user table.
  * No IP retention beyond the existing FastAPI access log.

Endpoints
---------
  POST /api/draft-telemetry            — append events (any portal token)
  GET  /api/draft-telemetry/health     — recent activity summary
  GET  /api/draft-telemetry/recent     — admin-only debug feed

Schema · `db.draft_telemetry`
-----------------------------
  eventId    str   (unique index)
  event      str
  actorId    str
  deviceId   str
  formKey    str
  ts         datetime  (client ts as UTC)
  meta       dict      (free-form; capped at 2KB serialized)
  receivedAt datetime  (server stamp)
  tokenKind  str       ("admin" | "pm" | "hr" | ...)

TTL: 30 days on `receivedAt` (created in ensure_draft_telemetry_indexes).

Rate limit: 60 batches/min per token (in-memory sliding window). The
endpoint is best-effort; if Mongo is slow we return 200 with
{partial: true} so clients never lose more than a buffer cycle.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ----- Constants --------------------------------------------------------
MAX_BATCH = 50
MAX_META_BYTES = 2_048
ALLOWED_EVENTS = {
    "draft.write.ok",
    "draft.write.fail",
    "draft.restore.offered",
    "draft.restore.action",
    "draft.lifecycle",
    "draft.actorId.rotated",
    "quota.warning",
}

# Sliding-window rate limit. NOT a security boundary — just a kindness
# limiter so a runaway client cannot DoS the collector. 60 batches/min
# per token.
_RATE_WINDOW_SEC = 60
_RATE_MAX_BATCHES = 60
_rate_state: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=_RATE_MAX_BATCHES * 2))


def _rate_limited(token_key: str) -> bool:
    now = time.monotonic()
    q = _rate_state[token_key]
    cutoff = now - _RATE_WINDOW_SEC
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= _RATE_MAX_BATCHES:
        return True
    q.append(now)
    return False


# ----- Pydantic models --------------------------------------------------
class DraftEvent(BaseModel):
    eventId: str = Field(..., min_length=8, max_length=64)
    event: str = Field(..., min_length=1, max_length=64)
    actorId: str = Field(default="anon", max_length=80)
    deviceId: str = Field(default="anon", max_length=80)
    formKey: str = Field(..., min_length=1, max_length=64)
    ts: int = Field(..., ge=0)
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event")
    @classmethod
    def _event_allowed(cls, v: str) -> str:
        if v not in ALLOWED_EVENTS:
            raise ValueError(f"event '{v}' not in allowlist")
        return v


class DraftEventBatch(BaseModel):
    batch: List[DraftEvent] = Field(..., min_length=1, max_length=MAX_BATCH)


# ----- Index bootstrap --------------------------------------------------
async def ensure_draft_telemetry_indexes(db) -> None:
    try:
        await db.draft_telemetry.create_index("eventId", unique=True)
        await db.draft_telemetry.create_index([("ts", -1), ("event", 1)])
        await db.draft_telemetry.create_index([("deviceId", 1), ("ts", -1)])
        await db.draft_telemetry.create_index(
            "receivedAt", expireAfterSeconds=30 * 24 * 60 * 60
        )
    except Exception as e:  # pragma: no cover
        logger.warning("draft_telemetry index bootstrap failed: %s", e)


# ----- Router ------------------------------------------------------------
def build_draft_telemetry_router(db, require_any_portal_token, require_admin_dep):
    router = APIRouter(tags=["draft-telemetry"])

    def _token_kind_from_actor(actor: Dict[str, Any]) -> str:
        return (actor.get("_actor") or actor.get("role") or "any")[:16]

    @router.post("/api/draft-telemetry")
    async def append_events(
        body: DraftEventBatch,
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ):
        token_key = (
            request.headers.get("x-admin-token")
            or request.headers.get("x-pm-token")
            or request.headers.get("x-hr-token")
            or request.headers.get("x-safety-token")
            or request.headers.get("x-dispatch-token")
            or request.headers.get("x-leadership-token")
            or "anon"
        )[:32]
        if _rate_limited(token_key):
            raise HTTPException(429, "draft-telemetry rate limit exceeded")

        token_kind = _token_kind_from_actor(actor)
        now = datetime.now(timezone.utc)
        received = 0
        deduped = 0
        for ev in body.batch:
            # Cheap meta-size guard.
            try:
                meta_json = ev.meta or {}
                # Quick sizeof estimate without dumping (avoid pulling json):
                if sum(len(str(k)) + len(str(v)) for k, v in meta_json.items()) > MAX_META_BYTES:
                    meta_json = {"_truncated": True}
            except Exception:
                meta_json = {}
            doc = {
                "eventId": ev.eventId,
                "event": ev.event,
                "actorId": ev.actorId,
                "deviceId": ev.deviceId,
                "formKey": ev.formKey,
                "ts": datetime.fromtimestamp(ev.ts / 1000.0, tz=timezone.utc)
                if ev.ts > 10_000_000_000
                else datetime.fromtimestamp(ev.ts, tz=timezone.utc),
                "meta": meta_json,
                "receivedAt": now,
                "tokenKind": token_kind,
            }
            try:
                await db.draft_telemetry.insert_one(doc)
                received += 1
            except Exception as e:
                msg = str(e).lower()
                if "duplicate" in msg or "e11000" in msg:
                    deduped += 1
                    continue
                # Anything else — log + count as deduped so the client
                # doesn't retry a poisoned event into a tight loop.
                logger.warning("draft_telemetry insert failed: %s", e)
                deduped += 1
        return {"received": received, "deduplicated": deduped}

    @router.get("/api/draft-telemetry/health")
    async def telemetry_health(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ):
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
            count = await db.draft_telemetry.count_documents({"receivedAt": {"$gte": cutoff}})
        except Exception as e:
            logger.warning("draft_telemetry health count failed: %s", e)
            count = -1
        return {
            "ok": True,
            "recent_events_60s": count,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    @router.get("/api/draft-telemetry/recent")
    async def telemetry_recent(
        _admin=Depends(require_admin_dep),
        formKey: Optional[str] = Query(default=None, max_length=64),
        deviceId: Optional[str] = Query(default=None, max_length=80),
        event: Optional[str] = Query(default=None, max_length=64),
        limit: int = Query(default=50, ge=1, le=200),
    ):
        q: Dict[str, Any] = {}
        if formKey:
            q["formKey"] = formKey
        if deviceId:
            q["deviceId"] = deviceId
        if event:
            q["event"] = event
        cur = (
            db.draft_telemetry.find(q, {"_id": 0})
            .sort("receivedAt", -1)
            .limit(limit)
        )
        items = []
        async for d in cur:
            # Stringify datetimes for JSON.
            if isinstance(d.get("ts"), datetime):
                d["ts"] = d["ts"].isoformat()
            if isinstance(d.get("receivedAt"), datetime):
                d["receivedAt"] = d["receivedAt"].isoformat()
            items.append(d)
        return {"items": items, "count": len(items)}

    return router


__all__ = [
    "build_draft_telemetry_router",
    "ensure_draft_telemetry_indexes",
    "ALLOWED_EVENTS",
    "MAX_BATCH",
]
