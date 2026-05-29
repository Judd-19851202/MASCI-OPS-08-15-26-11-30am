"""
routes/odr/observation.py — Phase V.1 · M0.3 · ODR Adoption Observation.

Doctrine:
  /app/memory/ODR_ADOPTION_OBSERVATION_PLAN.md

PURPOSE
=======
Track field-adoption signals — NOT performance scoring, NOT individual
foreman surveillance.

The observation layer answers ONE question:

  "Are foremen / superintendents / PMs / owners actually using
   the ODR system the way it was designed to be used?"

Aggregates only. Per-foreman attribution is intentionally avoided in
exposed APIs (the underlying log has the uid for debugging support,
but it never surfaces in dashboards).

ENDPOINTS
=========
  POST /api/odr/observation/event       any portal · log one signal
  GET  /api/odr/observation/summary     admin · aggregates over a window

EVENT SHAPE
===========
  surface : "foreman" | "fl_center" | "pm_panel" | "public_viewer"
  kind    : free-string · e.g. "session_start" | "section_visited" |
            "submit_success" | "amendment_routed" | "pdf_rendered" |
            "language_toggled" | "coaching_expanded" |
            "trust_banner_dismissed" | "photo_added"
  context : optional {section, lang, crew_type, duration_ms, …}

NEVER LOGGED
============
- Free-text body of any ODR field
- Coaching content actually read
- Foreman names (only uid hash for support)
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


ALLOWED_SURFACES = {"foreman", "fl_center", "pm_panel", "public_viewer"}
# Closed enum of telemetry signals — adding a new kind requires updating this
# set + adding it to the corresponding doctrine table in
# ODR_ADOPTION_OBSERVATION_PLAN.md.
ALLOWED_KINDS = {
    # foreman entry
    "session_start", "section_visited", "section_completed",
    "language_toggled", "photo_added", "voice_caption_used",
    "autosave_triggered", "submit_success", "submit_blocked",
    "abandoned", "coaching_expanded", "draft_resumed",
    # fl center
    "fl_inbox_opened", "fl_record_opened",
    "amendment_routed", "amendment_approved",
    "constraint_link_visited", "chronology_opened",
    "readiness_signal_clicked",
    # pm panel
    "pm_panel_opened", "pm_project_opened",
    "pm_blocker_opened", "pm_trend_inspected",
    "pm_pdf_downloaded",
    # public viewer
    "public_viewer_opened", "public_pdf_downloaded",
    # system
    "pdf_rendered", "trust_banner_dismissed", "trust_banner_shown",
    "device_kind_detected",
}


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _actor_uid(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("id")
        or actor.get("user_id")
        or actor.get("uid")
        or actor.get("email")
        or "unknown"
    )


def _hash_uid(uid: str) -> str:
    """Stable short hash for uid — preserves cardinality for unique
    counts without exposing the actual uid in aggregate responses."""
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:16]


class ObservationEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    surface: str = Field(..., max_length=24)
    kind: str = Field(..., max_length=48)
    odr_id: Optional[str] = None
    doc_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    device_kind: Optional[str] = Field(default=None, max_length=16)  # phone | tablet | desktop
    lang: Optional[str] = Field(default=None, max_length=8)


async def ensure_observation_indexes(db) -> None:
    await db.odr_observation_events.create_index("event_id", unique=True)
    await db.odr_observation_events.create_index([("at_utc", -1)])
    await db.odr_observation_events.create_index([("surface", 1), ("at_utc", -1)])
    await db.odr_observation_events.create_index([("kind", 1), ("at_utc", -1)])
    await db.odr_observation_events.create_index([("odr_id", 1), ("at_utc", -1)])
    logger.info("ODR observation indexes ensured.")


def build_odr_observation_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
    require_admin: Callable[..., Awaitable[Any]],
) -> APIRouter:

    router = APIRouter(prefix="/api/odr/observation", tags=["odr-observation"])

    @router.post("/event")
    async def post_event(
        body: ObservationEvent,
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> Dict[str, Any]:
        if body.surface not in ALLOWED_SURFACES:
            raise HTTPException(422, f"surface must be one of {ALLOWED_SURFACES}")
        if body.kind not in ALLOWED_KINDS:
            raise HTTPException(
                422,
                f"kind '{body.kind}' not in closed enum. "
                "Add to ALLOWED_KINDS + doctrine before logging.",
            )
        uid = _actor_uid(actor)
        row = {
            "event_id": str(uuid.uuid4()),
            "surface": body.surface,
            "kind": body.kind,
            "odr_id": body.odr_id,
            "doc_id": body.doc_id,
            "context": body.context or {},
            "device_kind": body.device_kind,
            "lang": body.lang,
            "actor_portal": (actor.get("_actor") or "unknown"),
            "actor_uid_hash": _hash_uid(uid),
            "at_utc": _utc_iso(),
        }
        await db.odr_observation_events.insert_one(row)
        row.pop("_id", None)
        # Never return uid_hash on the public response — trim.
        row.pop("actor_uid_hash", None)
        return row

    @router.get("/summary")
    async def get_summary(
        days: int = Query(default=7, ge=1, le=365),
        _admin: Any = Depends(require_admin),
    ) -> Dict[str, Any]:
        """Aggregate counts only — NEVER per-foreman attribution."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - days * 86400
        cutoff_iso = (
            datetime.fromtimestamp(cutoff, tz=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )
        cur = db.odr_observation_events.find(
            {"at_utc": {"$gte": cutoff_iso}},
            {"_id": 0},
        )
        events: List[Dict[str, Any]] = await cur.to_list(length=50000)

        by_surface: Dict[str, int] = {}
        by_kind: Dict[str, int] = {}
        by_device: Dict[str, int] = {}
        by_lang: Dict[str, int] = {}
        unique_authors: set[str] = set()
        durations: List[float] = []
        photo_counts: List[int] = []
        coaching_engagements = 0
        amendment_routes = 0
        public_pdfs = 0
        amendments_volume = 0
        pdf_renders = 0

        for ev in events:
            by_surface[ev["surface"]] = by_surface.get(ev["surface"], 0) + 1
            by_kind[ev["kind"]] = by_kind.get(ev["kind"], 0) + 1
            if ev.get("device_kind"):
                by_device[ev["device_kind"]] = by_device.get(ev["device_kind"], 0) + 1
            if ev.get("lang"):
                by_lang[ev["lang"]] = by_lang.get(ev["lang"], 0) + 1
            ctx = ev.get("context") or {}
            if ev["surface"] == "foreman" and ev.get("actor_uid_hash"):
                unique_authors.add(ev["actor_uid_hash"])
            if ev["kind"] == "submit_success" and isinstance(ctx.get("duration_ms"), (int, float)):
                durations.append(float(ctx["duration_ms"]))
            if ev["kind"] == "photo_added":
                photo_counts.append(1)
            if ev["kind"] == "coaching_expanded":
                coaching_engagements += 1
            if ev["kind"] == "amendment_routed":
                amendment_routes += 1
            if ev["kind"] == "public_pdf_downloaded":
                public_pdfs += 1
            if ev["kind"] in ("amendment_routed", "amendment_approved"):
                amendments_volume += 1
            if ev["kind"] == "pdf_rendered":
                pdf_renders += 1

        avg_duration_s = round(sum(durations) / len(durations) / 1000.0, 1) if durations else None
        return {
            "window_days": days,
            "total_events": len(events),
            "unique_foreman_sessions": len(unique_authors),
            "by_surface": by_surface,
            "by_kind": by_kind,
            "by_device": by_device,
            "by_language": by_lang,
            "average_submit_duration_s": avg_duration_s,
            "photos_added_count": len(photo_counts),
            "coaching_engagement_count": coaching_engagements,
            "amendment_volume": amendments_volume,
            "public_pdf_downloads": public_pdfs,
            "pdf_render_count": pdf_renders,
        }

    return router


__all__ = [
    "build_odr_observation_router",
    "ensure_observation_indexes",
    "ALLOWED_KINDS",
    "ALLOWED_SURFACES",
]
