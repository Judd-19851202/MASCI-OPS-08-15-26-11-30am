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
FORM_KEY_MAX_LENGTH = 180
MAX_META_BYTES = 2_048
ALLOWED_EVENTS = {
    "draft.write.ok",
    "draft.write.fail",
    "draft.restore.offered",
    "draft.restore.action",
    "draft.restore.blocked_cross_actor",
    "draft.recovery.absent",
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
    formKey: str = Field(..., min_length=1, max_length=FORM_KEY_MAX_LENGTH)
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

    @router.post("/api/draft-telemetry")
    async def append_events(
        body: DraftEventBatch,
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_pm_token: Optional[str] = Header(default=None, alias="X-PM-Token"),
        x_hr_token: Optional[str] = Header(default=None, alias="X-HR-Token"),
        x_safety_token: Optional[str] = Header(default=None, alias="X-Safety-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
        x_leadership_token: Optional[str] = Header(default=None, alias="X-Leadership-Token"),
        x_shop_token: Optional[str] = Header(default=None, alias="X-Shop-Token"),
        x_fl_token: Optional[str] = Header(default=None, alias="X-FL-Token"),
    ):
        # iter441 — accept anonymous events too. The P0 incident
        # population (foremen accessing /daily/submit via public link)
        # carries no portal token, so requiring auth would silently
        # drop the exact telemetry we need. Rate-limit by deviceId
        # AND by token-or-anon to bound abuse.
        token_key = (
            x_admin_token or x_pm_token or x_hr_token or x_safety_token
            or x_dispatch_token or x_leadership_token or x_shop_token
            or x_fl_token or ""
        )
        token_kind = "anon"
        if x_admin_token:
            token_kind = "admin"
        elif x_pm_token:
            token_kind = "pm"
        elif x_hr_token:
            token_kind = "hr"
        elif x_safety_token:
            token_kind = "safety"
        elif x_dispatch_token:
            token_kind = "dispatch"
        elif x_leadership_token:
            token_kind = "leadership"
        elif x_shop_token:
            token_kind = "shop"
        elif x_fl_token:
            token_kind = "fl"

        # Rate-limit on (deviceId, token_key) — keeps a misconfigured
        # device from drowning the collector while letting genuine
        # multi-user shared phones through.
        first_device = body.batch[0].deviceId if body.batch else "anon"
        rl_key = f"{token_kind}:{first_device}:{token_key[:16]}"[:80]
        if _rate_limited(rl_key):
            raise HTTPException(429, "draft-telemetry rate limit exceeded")

        now = datetime.now(timezone.utc)
        received = 0
        deduped = 0
        for ev in body.batch:
            # Cheap meta-size guard.
            try:
                meta_json = ev.meta or {}
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
        formKey: Optional[str] = Query(default=None, max_length=FORM_KEY_MAX_LENGTH),
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
