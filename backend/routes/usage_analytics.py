"""
usage_analytics.py — Iter146 (Phase 2.5). Operational usage telemetry.

Goal: track HOW the platform is used in the wild so future iters can
target real friction — NOT employee surveillance, not productivity
scoring, not behavioral analytics. Strict guardrails:

  * Admin-only read access (no PII leaked to any portal).
  * No raw user IDs — every actor is HMAC-hashed with a per-deploy
    secret so the same person produces stable but unlinkable buckets.
  * No request bodies, no employee names, no project numbers, no
    free-text. Only route, status, latency, viewport, portal_kind.
  * TTL = 90 days. Long-tail retention is for trend lines, not audits.
  * Writes are fire-and-forget. A failed insert NEVER blocks the
    actual user request.

Event kinds (capped to a closed enum so storage costs are predictable):
    page_view        — frontend route change
    form_submit      — frontend form submission (success or fail)
    export           — CSV/PDF download
    upload_failure   — file upload aborted with error
    api_call         — backend route timing (middleware)

Endpoints:
    POST /api/usage/track            (public — JWT optional, no schema-leak)
    GET  /api/admin/analytics/summary (admin)
    GET  /api/admin/analytics/routes  (admin)
    GET  /api/admin/analytics/portals (admin)
    GET  /api/admin/analytics/health  (admin)
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Closed set so storage / dashboards stay predictable.
ALLOWED_KINDS = {"page_view", "form_submit", "export",
                 "upload_failure", "api_call"}

# Skip these API path prefixes — telemetry on telemetry is noise.
SKIP_PATH_PREFIXES = (
    "/api/usage/",
    "/api/health",
    "/api/admin/analytics/",
    "/static/",
    "/favicon",
)

# Bound the in-memory queue so a runaway can't OOM the pod.
MAX_QUEUE_DEPTH = 5000


# ──────────────────────────────────────────────────────────────────
# Privacy helpers
# ──────────────────────────────────────────────────────────────────
def _hash_actor(value: Optional[str]) -> Optional[str]:
    """HMAC-hash an identifier so analytics buckets are stable but
    not reversible without the per-deploy secret. Anonymous if no
    secret is configured (defaults to a fresh key each pod start)."""
    if not value:
        return None
    secret = os.environ.get("ANALYTICS_HMAC_SECRET", "")
    if not secret:
        # Fall back to ADMIN_HMAC_SECRET so prod deploys don't need a
        # second secret; never use a literal in-code default.
        secret = os.environ.get("ADMIN_HMAC_SECRET", "")
    if not secret:
        # Last-resort process-local salt — restart rotates the buckets,
        # which is fine for an anonymous deploy.
        secret = str(os.getpid())
    digest = hmac.new(secret.encode("utf-8"), value.encode("utf-8"),
                      hashlib.sha256).hexdigest()
    return digest[:16]


def _strip_query(path: str) -> str:
    """Drop ?query and trailing /numeric/ id segments so analytics
    cluster by route, not by record."""
    if not path:
        return "/"
    head = path.split("?", 1)[0]
    parts = head.split("/")
    cleaned = []
    for p in parts:
        # Heuristic — long-ish hex/UUID-ish path segments get collapsed
        # to `:id`. Keeps `/admin/equipment/:id/history` as one bucket.
        if (len(p) >= 8 and all(c in "0123456789abcdef-" for c in p)) or p.isdigit():
            cleaned.append(":id")
        else:
            cleaned.append(p)
    return "/".join(cleaned)


# ──────────────────────────────────────────────────────────────────
# Async event sink
# ──────────────────────────────────────────────────────────────────
class UsageEventSink:
    """Bounded async queue → background flusher. Writes batches of
    up to 50 events at a time so the DB doesn't see one insert per
    page-view. `enqueue` is non-blocking and silently drops if the
    queue is full — protecting the user's request path is more
    important than perfect telemetry capture."""

    def __init__(self, db) -> None:
        self.db = db
        self.queue: deque[Dict[str, Any]] = deque(maxlen=MAX_QUEUE_DEPTH)
        self._task: Optional[asyncio.Task] = None
        self._stop = False

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop = True
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=2.0)
            except asyncio.TimeoutError:
                self._task.cancel()

    def enqueue(self, event: Dict[str, Any]) -> None:
        if event.get("kind") not in ALLOWED_KINDS:
            return
        # `deque(maxlen=…)` silently drops the OLDEST entry when full,
        # which is what we want — telemetry must never push back.
        self.queue.append(event)

    async def _run(self) -> None:
        while not self._stop:
            try:
                batch: List[Dict[str, Any]] = []
                while self.queue and len(batch) < 50:
                    batch.append(self.queue.popleft())
                if batch:
                    try:
                        await self.db.usage_events.insert_many(batch, ordered=False)
                    except Exception as e:  # noqa: BLE001
                        logger.debug(f"[usage] flush failed: {e}")
                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[usage] sink loop crashed: {e}")
                await asyncio.sleep(5.0)


SINK: Optional[UsageEventSink] = None


def get_sink() -> Optional[UsageEventSink]:
    return SINK


async def ensure_usage_indexes(db) -> None:
    """TTL = 90 days. Plus the two indexes the dashboards actually
    use (kind/at and portal/at). All idempotent."""
    try:
        await db.usage_events.create_index([("at", 1)],
                                           expireAfterSeconds=60 * 60 * 24 * 90)
        await db.usage_events.create_index([("kind", 1), ("at", -1)])
        await db.usage_events.create_index([("portal", 1), ("at", -1)])
        await db.usage_events.create_index([("route", 1), ("at", -1)])
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[usage_events] index ensure failed: {e}")


def start_sink(db) -> None:
    global SINK
    if SINK is None:
        SINK = UsageEventSink(db)
    SINK.start()


# ──────────────────────────────────────────────────────────────────
# HTTP middleware — fire-and-forget API timing capture
# ──────────────────────────────────────────────────────────────────
async def usage_tracking_middleware(request: Request, call_next):
    """Times every API request. Skips heartbeat / static / its-own
    endpoints so we don't have a feedback loop. NEVER raises — the
    request must succeed (or fail) on its own merits."""
    path = request.url.path
    if any(path.startswith(p) for p in SKIP_PATH_PREFIXES):
        return await call_next(request)

    t0 = time.monotonic()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        try:
            sink = get_sink()
            if sink is not None:
                portal = (
                    request.headers.get("X-Admin-Token") and "admin"
                    or request.headers.get("X-Safety-Token") and "safety"
                    or request.headers.get("X-HR-Token") and "hr"
                    or request.headers.get("X-PM-Token") and "pm"
                    or request.headers.get("X-Shop-Token") and "shop"
                    or request.headers.get("X-Dispatch-Token") and "dispatch"
                    or request.headers.get("X-Leadership-Token") and "leadership"
                    or "anon"
                )
                sink.enqueue({
                    "kind": "api_call",
                    "at": datetime.now(timezone.utc),
                    "route": _strip_query(path),
                    "method": request.method,
                    "status": status,
                    "latency_ms": int((time.monotonic() - t0) * 1000),
                    "portal": portal,
                    "viewport": None,
                    "actor": None,  # never derive identity from headers here
                })
        except Exception:  # noqa: BLE001
            pass  # NEVER let analytics break a real response


# ──────────────────────────────────────────────────────────────────
# Public ingest endpoint — frontend page_view / form_submit / export
# ──────────────────────────────────────────────────────────────────
class TrackEvent(BaseModel):
    kind: str
    route: Optional[str] = None
    portal: Optional[str] = None
    viewport: Optional[str] = None  # "mobile" | "tablet" | "desktop"
    status: Optional[str] = None    # "success" | "error"
    label: Optional[str] = None     # form id, export type, etc. — bounded
    latency_ms: Optional[int] = None
    error_code: Optional[str] = None


class TrackBatch(BaseModel):
    events: List[TrackEvent] = Field(default_factory=list)


def build_usage_routes(db, require_admin):
    router = APIRouter(tags=["usage-analytics"])

    @router.post("/api/usage/track")
    async def ingest(batch: TrackBatch,
                     x_actor_hint: Optional[str] = Header(default=None)):
        """No auth required by design — frontends fire-and-forget. We
        validate the kind is in our closed set, normalize the route,
        truncate label, and drop anything else. Returns immediately."""
        sink = get_sink()
        if sink is None:
            return {"ok": False, "queued": 0}
        accepted = 0
        actor_hash = _hash_actor(x_actor_hint) if x_actor_hint else None
        for ev in batch.events[:50]:  # cap per request
            if ev.kind not in ALLOWED_KINDS:
                continue
            sink.enqueue({
                "kind": ev.kind,
                "at": datetime.now(timezone.utc),
                "route": _strip_query(ev.route or ""),
                "portal": (ev.portal or "anon")[:24],
                "viewport": (ev.viewport or "")[:12] or None,
                "status": (ev.status or "")[:12] or None,
                "label": (ev.label or "")[:48] or None,
                "latency_ms": ev.latency_ms,
                "error_code": (ev.error_code or "")[:48] or None,
                "actor": actor_hash,
            })
            accepted += 1
        return {"ok": True, "queued": accepted}

    # ── Admin dashboards ──────────────────────────────────────────
    @router.get("/api/admin/analytics/summary",
                dependencies=[Depends(require_admin)])
    async def summary(window_hours: int = 24):
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        cur = db.usage_events.aggregate([
            {"$match": {"at": {"$gte": since}}},
            {"$group": {
                "_id": "$kind",
                "count": {"$sum": 1},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            }},
        ])
        kinds = []
        async for d in cur:
            kinds.append({"kind": d["_id"], "count": d["count"],
                          "errors": d["errors"]})
        viewport_cur = db.usage_events.aggregate([
            {"$match": {"at": {"$gte": since}, "viewport": {"$ne": None}}},
            {"$group": {"_id": "$viewport", "count": {"$sum": 1}}},
        ])
        viewports = []
        async for d in viewport_cur:
            viewports.append({"viewport": d["_id"], "count": d["count"]})
        return {
            "window_hours": window_hours,
            "since": since.isoformat(),
            "kinds": kinds,
            "viewports": viewports,
            "queue_depth": len(get_sink().queue) if get_sink() else 0,
        }

    @router.get("/api/admin/analytics/routes",
                dependencies=[Depends(require_admin)])
    async def by_route(window_hours: int = 24, limit: int = 30):
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        cur = db.usage_events.aggregate([
            {"$match": {"at": {"$gte": since}, "route": {"$ne": ""},
                        "kind": "api_call"}},
            {"$group": {
                "_id": "$route",
                "count": {"$sum": 1},
                "p95":   {"$max": "$latency_ms"},
                "avg_ms":{"$avg": "$latency_ms"},
                "errors":{"$sum": {"$cond": [
                    {"$gte": [{"$ifNull": ["$status", 0]}, 400]}, 1, 0,
                ]}},
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ])
        rows = []
        async for d in cur:
            rows.append({
                "route": d["_id"],
                "count": d["count"],
                "p95_ms": d.get("p95") or 0,
                "avg_ms": int(d.get("avg_ms") or 0),
                "errors": d.get("errors") or 0,
            })
        return {"window_hours": window_hours, "rows": rows}

    @router.get("/api/admin/analytics/portals",
                dependencies=[Depends(require_admin)])
    async def by_portal(window_hours: int = 24):
        since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        cur = db.usage_events.aggregate([
            {"$match": {"at": {"$gte": since}}},
            {"$group": {
                "_id": "$portal",
                "count": {"$sum": 1},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}},
            }},
            {"$sort": {"count": -1}},
        ])
        rows = []
        async for d in cur:
            rows.append({"portal": d["_id"] or "anon", "count": d["count"],
                         "errors": d.get("errors") or 0})
        return {"window_hours": window_hours, "rows": rows}

    @router.get("/api/admin/analytics/health",
                dependencies=[Depends(require_admin)])
    async def health():
        sink = get_sink()
        total = await db.usage_events.count_documents({})
        return {
            "sink_running": bool(sink and sink._task and not sink._task.done()),  # noqa: SLF001
            "queue_depth": len(sink.queue) if sink else 0,
            "total_stored_events": total,
            "retention_days": 90,
        }

    return router


__all__ = [
    "build_usage_routes",
    "ensure_usage_indexes",
    "start_sink",
    "usage_tracking_middleware",
]
