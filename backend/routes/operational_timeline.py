"""
routes/operational_timeline.py — Phase V-Prelude · Wave 1 · Substrate.

Read-only chronology aggregator over `operational_links` +
`operational_constraints`. See
`/app/memory/OPERATIONAL_TIMELINE_FOUNDATION.md` for the doctrine —
specifically: single project per call, text-only response, no
gantt / no chart, ≤200 items, sorted by `at`.

This endpoint is forward-compatible: when V.1 RFI lands its rows
will appear in the timeline automatically through the
`operational_links` substrate.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

MAX_ITEMS = 200


class TimelineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    id: str
    at: str
    title: str
    subtitle: str = ""
    relationship: Optional[str] = None
    project_id: str
    linked_to: List[Dict[str, str]] = []


class TimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_id: str
    generated_at: str
    truncated: bool
    items: List[TimelineItem]


def _utc_iso(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now(timezone.utc)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{d.microsecond // 1000:03d}Z"


def _within_range(at: str, from_iso: Optional[str], to_iso: Optional[str]) -> bool:
    if not from_iso and not to_iso:
        return True
    try:
        ts = at.replace("Z", "+00:00") if at.endswith("Z") else at
        d = datetime.fromisoformat(ts)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
    except Exception:
        return True
    if from_iso:
        try:
            f = datetime.fromisoformat(from_iso.replace("Z", "+00:00"))
            if f.tzinfo is None:
                f = f.replace(tzinfo=timezone.utc)
            if d < f:
                return False
        except Exception:
            pass
    if to_iso:
        try:
            t = datetime.fromisoformat(to_iso.replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if d > t:
                return False
        except Exception:
            pass
    return True


def build_operational_timeline_router(
    db,
    require_actor: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    router = APIRouter(prefix="/api/timeline", tags=["operational-timeline"])

    @router.get("", response_model=TimelineResponse)
    async def get_timeline(
        project_id: str = Query(..., min_length=1),
        from_: Optional[str] = Query(default=None, alias="from"),
        to: Optional[str] = Query(default=None),
        actor: Dict[str, Any] = Depends(require_actor),
    ) -> TimelineResponse:
        items: List[Dict[str, Any]] = []
        is_admin = actor.get("_actor") == "admin"

        # 1. Constraints opened / resolved on this project.
        cur = db.operational_constraints.find(
            {"project_id": project_id},
            {"_id": 0},
        ).sort("created_at", -1).limit(MAX_ITEMS)
        constraints = await cur.to_list(length=MAX_ITEMS)
        for c in constraints:
            if _within_range(c["created_at"], from_, to):
                items.append({
                    "kind": "operational_constraint",
                    "id": c["id"],
                    "at": c["created_at"],
                    "title": c.get("title", ""),
                    "subtitle": f"{c.get('discipline', '')} · {c.get('severity', '')}",
                    "relationship": None,
                    "project_id": project_id,
                    "linked_to": [],
                })
            # Chronology events (resolved, owner contacted, etc.) show
            # as additional rows tied to the constraint.
            for ev in c.get("chronology", [])[1:]:  # skip "created"
                if _within_range(ev.get("at", ""), from_, to):
                    items.append({
                        "kind": "operational_constraint",
                        "id": c["id"],
                        "at": ev.get("at", ""),
                        "title": c.get("title", ""),
                        "subtitle": f"{ev.get('action', '')} · {ev.get('note', '')[:80]}",
                        "relationship": ev.get("action"),
                        "project_id": project_id,
                        "linked_to": [],
                    })

        # 2. Operational links touching this project (excluding voided
        #    & audit-only for non-admins).
        link_q: Dict[str, Any] = {"project_id": project_id}
        if not is_admin:
            link_q["visibility"] = {"$ne": "audit-only"}
        link_q["status"] = {"$ne": "voided"}
        cur = db.operational_links.find(link_q, {"_id": 0}).sort(
            "created_at", -1
        ).limit(MAX_ITEMS)
        links = await cur.to_list(length=MAX_ITEMS)
        for ln in links:
            if not _within_range(ln["created_at"], from_, to):
                continue
            items.append({
                "kind": ln["source_type"],
                "id": ln["source_id"],
                "at": ln["created_at"],
                "title": ln.get("reason", "") or f"{ln['source_type']} → {ln['target_type']}",
                "subtitle": ln["relationship"],
                "relationship": ln["relationship"],
                "project_id": project_id,
                "linked_to": [{
                    "kind": ln["target_type"],
                    "id": ln["target_id"],
                }],
            })

        # 3. Sort newest first; cap at MAX_ITEMS.
        items.sort(key=lambda r: (r["at"], r["id"]), reverse=True)
        truncated = len(items) > MAX_ITEMS
        items = items[:MAX_ITEMS]

        return TimelineResponse(
            project_id=project_id,
            generated_at=_utc_iso(),
            truncated=truncated,
            items=[TimelineItem(**i) for i in items],
        )

    return router


__all__ = ["build_operational_timeline_router"]
